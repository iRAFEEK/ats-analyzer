"""Entity extraction service for skills, titles, companies, dates, and education."""

import re
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass

import spacy
import structlog
from rapidfuzz import fuzz

from ats_analyzer.core.errors import EntityExtractionError

logger = structlog.get_logger(__name__)


@dataclass
class ExtractedSkill:
    """Extracted skill with metadata."""
    name: str
    canonical_name: str
    confidence: float
    section: str
    context: str


@dataclass
class ExtractedExperience:
    """Extracted work experience."""
    title: str
    company: str
    start_date: Optional[str]
    end_date: Optional[str]
    duration_months: Optional[int]
    description: str
    section: str


@dataclass
class ExtractedEducation:
    """Extracted education information."""
    degree: str
    institution: str
    field: Optional[str]
    graduation_date: Optional[str]
    gpa: Optional[str]
    section: str


@dataclass
class ExtractedEntities:
    """Container for all extracted entities."""
    skills: List[ExtractedSkill]
    experience: List[ExtractedExperience]
    education: List[ExtractedEducation]
    total_experience_months: int
    most_recent_title: Optional[str]


def load_skills_taxonomy() -> Dict[str, List[str]]:
    """Load skills taxonomy with aliases."""
    import json
    from pathlib import Path
    
    taxonomy_path = Path(__file__).parent.parent / "data" / "skills_taxonomy.json"
    
    try:
        with open(taxonomy_path, "r") as f:
            taxonomy_data = json.load(f)
        
        # Flatten the nested structure
        flattened = {}
        for category, skills in taxonomy_data.items():
            for skill, aliases in skills.items():
                flattened[skill] = aliases
        
        return flattened
    except Exception as e:
        logger.warning(f"Failed to load skills taxonomy: {e}, using fallback")
        # Fallback to minimal taxonomy
        return {
            "Python": ["python", "py", "python3"],
            "JavaScript": ["javascript", "js", "node.js", "nodejs"],
            "React": ["react", "reactjs", "react.js"],
            "SQL": ["sql", "postgresql", "mysql"],
            "Docker": ["docker", "containerization"],
            "Git": ["git", "github", "version control"],
        }


def extract_skills_from_text(text: str, section: str) -> List[ExtractedSkill]:
    """Extract skills from text using fuzzy matching."""
    skills_taxonomy = load_skills_taxonomy()
    extracted_skills = []
    
    # Normalize text
    text_lower = text.lower()
    
    for canonical_skill, aliases in skills_taxonomy.items():
        best_match = None
        best_score = 0
        best_context = ""
        
        for alias in aliases:
            # Direct substring match
            if alias in text_lower:
                score = 1.0
                # Find context around the match
                start_idx = text_lower.find(alias)
                context_start = max(0, start_idx - 50)
                context_end = min(len(text), start_idx + len(alias) + 50)
                context = text[context_start:context_end].strip()
                
                if score > best_score:
                    best_match = alias
                    best_score = score
                    best_context = context
            else:
                # Fuzzy matching for partial matches
                words = text_lower.split()
                for word in words:
                    if len(word) >= 3:  # Skip very short words
                        score = fuzz.ratio(alias, word) / 100.0
                        if score >= 0.95 and score > best_score:  # Very high threshold for fuzzy
                            best_match = word
                            best_score = score
                            # Find context
                            word_idx = text_lower.find(word)
                            if word_idx != -1:
                                context_start = max(0, word_idx - 50)
                                context_end = min(len(text), word_idx + len(word) + 50)
                                best_context = text[context_start:context_end].strip()
        
        if best_match and best_score >= 0.85:  # Higher minimum confidence threshold
            extracted_skills.append(ExtractedSkill(
                name=best_match,
                canonical_name=canonical_skill,
                confidence=best_score,
                section=section,
                context=best_context,
            ))
    
    return extracted_skills


def extract_dates_from_text(text: str) -> List[Tuple[str, str]]:
    """Extract date ranges from text."""
    date_patterns = [
        r'(\d{1,2}/\d{1,2}/\d{4})\s*[-–—]\s*(\d{1,2}/\d{1,2}/\d{4})',
        r'(\d{1,2}/\d{4})\s*[-–—]\s*(\d{1,2}/\d{4})',
        r'(\w+\s+\d{4})\s*[-–—]\s*(\w+\s+\d{4})',
        r'(\d{4})\s*[-–—]\s*(\d{4})',
        r'(\w+\s+\d{4})\s*[-–—]\s*(present|current)',
    ]
    
    dates = []
    for pattern in date_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            start_date = match.group(1)
            end_date = match.group(2) if len(match.groups()) > 1 else None
            dates.append((start_date, end_date))
    
    return dates


def extract_experience_from_section(text: str, section: str) -> List[ExtractedExperience]:
    """Extract work experience from text."""
    experiences = []
    
    # Split by common separators (double newlines, bullet points)
    entries = re.split(r'\n\n+|•\s*', text)
    
    for entry in entries:
        entry = entry.strip()
        if len(entry) < 50:  # Skip very short entries
            continue
        
        # Extract title (usually first line or after company)
        lines = entry.split('\n')
        first_line = lines[0].strip()
        
        # Common title patterns
        title_patterns = [
            r'^([^,\n]+?)\s*(?:at|@)\s*([^,\n]+)',  # "Software Engineer at Company"
            r'^([^,\n]+?),\s*([^,\n]+)',  # "Software Engineer, Company"
            r'^([A-Z][^,\n]+?)[\s]*$',  # Just title on first line
        ]
        
        title = ""
        company = ""
        
        for pattern in title_patterns:
            match = re.match(pattern, first_line, re.IGNORECASE)
            if match:
                if len(match.groups()) == 2:
                    title = match.group(1).strip()
                    company = match.group(2).strip()
                else:
                    title = match.group(1).strip()
                break
        
        if not title:
            # Fallback: use first line as title
            title = first_line
        
        # Extract dates
        dates = extract_dates_from_text(entry)
        start_date = dates[0][0] if dates else None
        end_date = dates[0][1] if dates and dates[0][1] else None
        
        # Calculate duration (rough estimate)
        duration_months = None
        if start_date and end_date:
            try:
                # Simple year-based calculation
                start_year = int(re.search(r'\d{4}', start_date).group())
                if end_date.lower() in ['present', 'current']:
                    end_year = datetime.now().year
                else:
                    end_year = int(re.search(r'\d{4}', end_date).group())
                duration_months = (end_year - start_year) * 12
            except:
                pass
        
        experiences.append(ExtractedExperience(
            title=title,
            company=company,
            start_date=start_date,
            end_date=end_date,
            duration_months=duration_months,
            description=entry,
            section=section,
        ))
    
    return experiences


def extract_education_from_section(text: str, section: str) -> List[ExtractedEducation]:
    """Extract education information from text."""
    educations = []
    
    # Split by common separators
    entries = re.split(r'\n\n+|•\s*', text)
    
    degree_patterns = [
        r'\b(bachelor|master|phd|doctorate|associate|b\.?s\.?|m\.?s\.?|b\.?a\.?|m\.?a\.?|ph\.?d\.?)',
        r'\b(degree|diploma|certificate)',
    ]
    
    for entry in entries:
        entry = entry.strip()
        if len(entry) < 10:
            continue
        
        # Look for degree keywords
        degree = ""
        for pattern in degree_patterns:
            match = re.search(pattern, entry, re.IGNORECASE)
            if match:
                # Extract surrounding context as degree
                lines = entry.split('\n')
                for line in lines:
                    if re.search(pattern, line, re.IGNORECASE):
                        degree = line.strip()
                        break
                break
        
        # Extract institution (often after "at" or on separate line)
        institution = ""
        institution_patterns = [
            r'(?:at|from)\s+([^,\n]+(?:university|college|institute|school)[^,\n]*)',
            r'^([^,\n]*(?:university|college|institute|school)[^,\n]*)',
        ]
        
        for pattern in institution_patterns:
            match = re.search(pattern, entry, re.IGNORECASE)
            if match:
                institution = match.group(1).strip()
                break
        
        # Extract graduation date
        dates = extract_dates_from_text(entry)
        graduation_date = dates[0][1] if dates else None
        
        # Extract GPA if present
        gpa_match = re.search(r'gpa:?\s*(\d+\.?\d*)', entry, re.IGNORECASE)
        gpa = gpa_match.group(1) if gpa_match else None
        
        if degree or institution:
            educations.append(ExtractedEducation(
                degree=degree,
                institution=institution,
                field=None,  # TODO: Extract field of study
                graduation_date=graduation_date,
                gpa=gpa,
                section=section,
            ))
    
    return educations


def extract_entities(text: str) -> ExtractedEntities:
    """Extract all entities from resume text."""
    logger.info("Starting entity extraction", text_length=len(text))
    
    try:
        # Load spaCy model
        try:
            nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not available, using basic extraction")
            nlp = None
        
        # Split into sections (basic approach - could use sectionizer)
        sections = {
            "summary": text[:500],  # First part as summary
            "experience": text,  # Use full text for now
            "education": text,
            "skills": text,
        }
        
        all_skills = []
        all_experience = []
        all_education = []
        
        # Extract from each section
        for section_name, section_text in sections.items():
            if not section_text.strip():
                continue
                
            # Extract skills
            skills = extract_skills_from_text(section_text, section_name)
            all_skills.extend(skills)
            
            # Extract experience (focus on experience section)
            if section_name in ["experience", "summary"]:
                experience = extract_experience_from_section(section_text, section_name)
                all_experience.extend(experience)
            
            # Extract education (focus on education section)
            if section_name in ["education", "summary"]:
                education = extract_education_from_section(section_text, section_name)
                all_education.extend(education)
        
        # Deduplicate skills by canonical name
        unique_skills = {}
        for skill in all_skills:
            if skill.canonical_name not in unique_skills:
                unique_skills[skill.canonical_name] = skill
            elif skill.confidence > unique_skills[skill.canonical_name].confidence:
                unique_skills[skill.canonical_name] = skill
        
        final_skills = list(unique_skills.values())
        
        # Calculate total experience
        total_months = 0
        for exp in all_experience:
            if exp.duration_months:
                total_months += exp.duration_months
        
        # Find most recent title
        most_recent_title = None
        if all_experience:
            # Sort by end date (rough approximation)
            recent_exp = sorted(all_experience, 
                              key=lambda x: x.end_date or "9999", 
                              reverse=True)
            if recent_exp:
                most_recent_title = recent_exp[0].title
        
        logger.info(
            "Entity extraction completed",
            skills_found=len(final_skills),
            experience_entries=len(all_experience),
            education_entries=len(all_education),
            total_experience_months=total_months,
        )
        
        return ExtractedEntities(
            skills=final_skills,
            experience=all_experience,
            education=all_education,
            total_experience_months=total_months,
            most_recent_title=most_recent_title,
        )
        
    except Exception as e:
        logger.error("Entity extraction failed", error=str(e))
        raise EntityExtractionError(f"Failed to extract entities: {str(e)}")
