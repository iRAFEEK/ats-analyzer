"""Text sectionization service."""

import re
from typing import Dict, List, Tuple

import structlog

logger = structlog.get_logger(__name__)


# Section header patterns (case-insensitive)
SECTION_PATTERNS = {
    "summary": [
        r"professional\s+summary",
        r"career\s+summary", 
        r"executive\s+summary",
        r"profile",
        r"summary",
        r"overview",
        r"objective",
        r"career\s+objective",
    ],
    "experience": [
        r"work\s+experience",
        r"professional\s+experience", 
        r"employment\s+history",
        r"career\s+history",
        r"experience",
        r"employment",
        r"work\s+history",
    ],
    "education": [
        r"education",
        r"educational\s+background",
        r"academic\s+background",
        r"qualifications",
        r"degrees?",
    ],
    "skills": [
        r"technical\s+skills",
        r"core\s+competencies",
        r"key\s+skills",
        r"skills",
        r"competencies",
        r"expertise",
        r"technologies",
        r"technical\s+expertise",
    ],
    "projects": [
        r"projects?",
        r"key\s+projects?",
        r"notable\s+projects?",
        r"selected\s+projects?",
        r"personal\s+projects?",
        r"portfolio",
    ],
    "certifications": [
        r"certifications?",
        r"certificates?",
        r"professional\s+certifications?",
        r"licenses?",
    ],
    "awards": [
        r"awards?",
        r"honors?",
        r"achievements?",
        r"recognitions?",
        r"accomplishments?",
    ],
    "languages": [
        r"languages?",
        r"language\s+skills",
        r"linguistic\s+skills",
    ],
    "publications": [
        r"publications?",
        r"papers?",
        r"research",
        r"articles?",
    ],
    "references": [
        r"references?",
        r"recommendations?",
    ],
}


def find_section_boundaries(text: str) -> List[Tuple[str, int, int]]:
    """Find section boundaries in text."""
    boundaries = []
    lines = text.split('\n')
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if not line_stripped:
            continue
            
        # Check if line looks like a section header
        # Headers are typically:
        # - All caps or title case
        # - Short (< 50 chars)
        # - Match known patterns
        # - May have decorative characters
        
        if len(line_stripped) > 50:
            continue
            
        # Remove common decorative characters
        clean_line = re.sub(r'[=\-_*•]+', '', line_stripped).strip()
        if not clean_line:
            continue
            
        # Check against patterns
        for section_name, patterns in SECTION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, clean_line, re.IGNORECASE):
                    # Calculate character position
                    char_pos = sum(len(lines[j]) + 1 for j in range(i))  # +1 for newline
                    boundaries.append((section_name, i, char_pos))
                    break
            else:
                continue
            break
    
    # Sort by line number
    boundaries.sort(key=lambda x: x[1])
    
    return boundaries


def extract_section_content(text: str, start_pos: int, end_pos: int) -> str:
    """Extract content between positions, cleaning up formatting."""
    content = text[start_pos:end_pos].strip()
    
    # Remove the header line itself (first line)
    lines = content.split('\n')
    if lines:
        lines = lines[1:]  # Skip header line
    
    # Clean up content
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if line and not re.match(r'^[=\-_*•\s]+$', line):  # Skip decorative lines
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)


def sectionize_text(text: str) -> Dict[str, str]:
    """Split text into logical sections."""
    logger.info("Starting text sectionization", text_length=len(text))
    
    if not text.strip():
        return {}
    
    # Find section boundaries
    boundaries = find_section_boundaries(text)
    
    if not boundaries:
        logger.info("No section headers found, returning text as summary")
        return {"summary": text.strip()}
    
    sections = {}
    
    # Extract content for each section
    for i, (section_name, line_num, char_pos) in enumerate(boundaries):
        # Find end position (next section or end of text)
        if i + 1 < len(boundaries):
            end_pos = boundaries[i + 1][2]
        else:
            end_pos = len(text)
        
        # Extract and clean content
        content = extract_section_content(text, char_pos, end_pos)
        
        if content:
            # If section already exists, append to it
            if section_name in sections:
                sections[section_name] += "\n\n" + content
            else:
                sections[section_name] = content
    
    # If we have leftover content at the beginning (before first section), 
    # treat it as summary
    if boundaries:
        first_section_pos = boundaries[0][2]
        if first_section_pos > 0:
            preamble = text[:first_section_pos].strip()
            if preamble and len(preamble) > 50:  # Only if substantial
                sections["summary"] = preamble
    
    # Ensure we have core sections even if empty
    core_sections = ["summary", "experience", "education", "skills"]
    for section in core_sections:
        if section not in sections:
            sections[section] = ""
    
    logger.info(
        "Text sectionization completed",
        sections_found=list(sections.keys()),
        total_sections=len(sections),
    )
    
    return sections
