"""Job description parsing service."""

import re
from typing import Dict, List, Set
from dataclasses import dataclass

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class JDRequirement:
    """Job description requirement."""
    skill: str
    is_required: bool
    context: str
    confidence: float


@dataclass
class JDRequirements:
    """Parsed job description requirements."""
    required_skills: List[JDRequirement]
    preferred_skills: List[JDRequirement]
    experience_years: int
    education_level: str
    title: str
    all_skills: List[str]


def load_cue_lexicon() -> Dict[str, str]:
    """Load cue words that indicate required vs preferred skills."""
    import json
    from pathlib import Path
    
    lexicon_path = Path(__file__).parent.parent / "data" / "cue_lexicon.json"
    
    try:
        with open(lexicon_path, "r") as f:
            lexicon_data = json.load(f)
        
        # Flatten required and preferred indicators
        cues = {}
        for indicator in lexicon_data.get("required_indicators", []):
            cues[indicator] = "required"
        for indicator in lexicon_data.get("preferred_indicators", []):
            cues[indicator] = "preferred"
        
        return cues
    except Exception as e:
        logger.warning(f"Failed to load cue lexicon: {e}, using fallback")
        # Fallback to minimal lexicon
        return {
            "must": "required",
            "required": "required", 
            "mandatory": "required",
            "essential": "required",
            "preferred": "preferred",
            "nice to have": "preferred",
            "bonus": "preferred",
            "ideal": "preferred",
        }


def extract_skills_from_jd(text: str) -> List[str]:
    """Extract potential skills from job description."""
    # Load skills taxonomy
    from ats_analyzer.services.extract import load_skills_taxonomy
    skills_taxonomy = load_skills_taxonomy()
    
    found_skills = []
    text_lower = text.lower()
    
    # Look for skills in the text
    for canonical_skill, aliases in skills_taxonomy.items():
        for alias in aliases:
            if alias in text_lower:
                found_skills.append(canonical_skill)
                break
    
    # Also look for common patterns that indicate skills
    # "Experience with X", "Knowledge of Y", "Proficient in Z"
    skill_patterns = [
        r'experience\s+(?:with|in)\s+([^,\n\.]+)',
        r'knowledge\s+of\s+([^,\n\.]+)',
        r'proficient\s+(?:with|in)\s+([^,\n\.]+)',
        r'skilled\s+(?:with|in)\s+([^,\n\.]+)',
        r'familiar\s+with\s+([^,\n\.]+)',
        r'expertise\s+(?:with|in)\s+([^,\n\.]+)',
    ]
    
    for pattern in skill_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            skill_text = match.group(1).strip()
            # Check if this matches any known skill
            for canonical_skill, aliases in skills_taxonomy.items():
                for alias in aliases:
                    if alias in skill_text.lower():
                        if canonical_skill not in found_skills:
                            found_skills.append(canonical_skill)
                        break
    
    return found_skills


def classify_skill_requirements(text: str, skills: List[str]) -> List[JDRequirement]:
    """Classify skills as required or preferred based on context."""
    cue_lexicon = load_cue_lexicon()
    requirements = []
    
    text_lower = text.lower()
    
    for skill in skills:
        # Find all mentions of this skill
        skill_lower = skill.lower()
        skill_positions = []
        
        # Find positions where skill appears
        start = 0
        while True:
            pos = text_lower.find(skill_lower, start)
            if pos == -1:
                break
            skill_positions.append(pos)
            start = pos + 1
        
        # For each occurrence, analyze surrounding context
        best_classification = "preferred"  # Default
        best_confidence = 0.5
        best_context = ""
        
        for pos in skill_positions:
            # Extract context around skill (±100 characters)
            context_start = max(0, pos - 100)
            context_end = min(len(text), pos + len(skill) + 100)
            context = text[context_start:context_end]
            
            # Check for cue words in context
            context_lower = context.lower()
            for cue_word, classification in cue_lexicon.items():
                if cue_word in context_lower:
                    confidence = 0.8  # High confidence for explicit cues
                    if confidence > best_confidence:
                        best_classification = classification
                        best_confidence = confidence
                        best_context = context
                    break
        
        # Additional heuristics
        # Skills mentioned in bullet points are often required
        if re.search(rf'[•\*\-]\s*[^,\n]*{re.escape(skill_lower)}', text_lower):
            if best_confidence < 0.7:
                best_classification = "required"
                best_confidence = 0.7
        
        # Skills in "Requirements" section are required
        if re.search(rf'requirements?[^:]*:[^,\n]*{re.escape(skill_lower)}', text_lower, re.IGNORECASE):
            best_classification = "required"
            best_confidence = 0.9
        
        # Skills in "Nice to have" section are preferred
        if re.search(rf'nice\s+to\s+have[^,\n]*{re.escape(skill_lower)}', text_lower, re.IGNORECASE):
            best_classification = "preferred"
            best_confidence = 0.9
        
        requirements.append(JDRequirement(
            skill=skill,
            is_required=(best_classification == "required"),
            context=best_context,
            confidence=best_confidence,
        ))
    
    return requirements


def extract_experience_requirements(text: str) -> int:
    """Extract years of experience required."""
    # Look for patterns like "3+ years", "minimum 5 years", etc.
    experience_patterns = [
        r'(\d+)\+?\s*years?\s+(?:of\s+)?experience',
        r'minimum\s+(\d+)\s+years?',
        r'at\s+least\s+(\d+)\s+years?',
        r'(\d+)\s*-\s*\d+\s+years?',
        r'(\d+)\s+to\s+\d+\s+years?',
    ]
    
    years = []
    for pattern in experience_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                year_count = int(match.group(1))
                years.append(year_count)
            except ValueError:
                continue
    
    # Return minimum required years (most conservative)
    return min(years) if years else 0


def extract_education_requirements(text: str) -> str:
    """Extract education level requirements."""
    education_patterns = [
        (r'bachelor|b\.?s\.?|b\.?a\.?', 'bachelor'),
        (r'master|m\.?s\.?|m\.?a\.?', 'master'),
        (r'phd|ph\.?d\.?|doctorate', 'phd'),
        (r'associate|a\.?s\.?', 'associate'),
        (r'high\s+school|diploma', 'high_school'),
    ]
    
    for pattern, level in education_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return level
    
    return "unspecified"


def extract_job_title(text: str) -> str:
    """Extract job title from job description."""
    # Look for common title patterns at the beginning
    lines = text.split('\n')
    
    # First few lines often contain the title
    for i, line in enumerate(lines[:5]):
        line = line.strip()
        if not line:
            continue
            
        # Skip very long lines (likely descriptions)
        if len(line) > 100:
            continue
            
        # Look for title-like patterns
        title_indicators = [
            'position', 'role', 'job', 'opportunity', 'opening',
            'engineer', 'developer', 'manager', 'analyst', 'specialist',
            'director', 'lead', 'senior', 'junior', 'intern'
        ]
        
        line_lower = line.lower()
        if any(indicator in line_lower for indicator in title_indicators):
            return line
    
    # Fallback: use first non-empty line
    for line in lines:
        line = line.strip()
        if line and len(line) < 100:
            return line
    
    return "Unknown Position"


def parse_job_description(jd_text: str) -> JDRequirements:
    """Parse job description to extract requirements."""
    logger.info("Starting job description parsing", text_length=len(jd_text))
    
    if not jd_text.strip():
        return JDRequirements(
            required_skills=[],
            preferred_skills=[],
            experience_years=0,
            education_level="unspecified",
            title="Unknown Position",
            all_skills=[],
        )
    
    try:
        # Extract job title
        title = extract_job_title(jd_text)
        
        # Extract skills
        all_skills = extract_skills_from_jd(jd_text)
        
        # Classify requirements
        requirements = classify_skill_requirements(jd_text, all_skills)
        
        # Separate required and preferred
        required_skills = [req for req in requirements if req.is_required]
        preferred_skills = [req for req in requirements if not req.is_required]
        
        # Extract experience and education requirements
        experience_years = extract_experience_requirements(jd_text)
        education_level = extract_education_requirements(jd_text)
        
        logger.info(
            "Job description parsing completed",
            title=title,
            total_skills=len(all_skills),
            required_skills=len(required_skills),
            preferred_skills=len(preferred_skills),
            experience_years=experience_years,
            education_level=education_level,
        )
        
        return JDRequirements(
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            experience_years=experience_years,
            education_level=education_level,
            title=title,
            all_skills=all_skills,
        )
        
    except Exception as e:
        logger.error("Job description parsing failed", error=str(e))
        # Return empty requirements on error
        return JDRequirements(
            required_skills=[],
            preferred_skills=[],
            experience_years=0,
            education_level="unspecified",
            title="Unknown Position",
            all_skills=[],
        )
