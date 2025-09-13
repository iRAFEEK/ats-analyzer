"""ATS compatibility linting service."""

import re
from typing import List, Tuple

import structlog

from ats_analyzer.api.dto import ATSWarnings

logger = structlog.get_logger(__name__)


def check_multi_column_layout(text: str) -> bool:
    """Detect multi-column layout that might break ATS parsing."""
    lines = text.split('\n')
    
    # Look for patterns indicating columns
    # 1. Lines with significant horizontal spacing
    # 2. Short lines followed by other short lines at similar positions
    
    suspicious_lines = 0
    total_content_lines = 0
    
    for line in lines:
        if not line.strip():
            continue
            
        total_content_lines += 1
        
        # Check for excessive spacing (might indicate columns)
        if re.search(r'\s{10,}', line):  # 10+ consecutive spaces
            suspicious_lines += 1
        
        # Check for very short lines that might be in columns
        if 10 < len(line.strip()) < 30:  # Short but not empty
            suspicious_lines += 1
    
    if total_content_lines == 0:
        return False
        
    # If more than 30% of lines look suspicious, flag as multi-column
    return (suspicious_lines / total_content_lines) > 0.3


def check_table_formatting(text: str) -> bool:
    """Detect table-like formatting that might break parsing."""
    lines = text.split('\n')
    
    # Look for table indicators
    table_indicators = 0
    
    for line in lines:
        if not line.strip():
            continue
            
        # Check for pipe characters (common in tables)
        if line.count('|') >= 2:
            table_indicators += 1
        
        # Check for tab characters
        if '\t' in line:
            table_indicators += 1
        
        # Check for repeated patterns of similar spacing
        if re.search(r'(\s{3,}[^\s]+){3,}', line):
            table_indicators += 1
    
    return table_indicators > 2


def check_image_heavy_content(text: str) -> bool:
    """Check if content might be image-heavy (low text density)."""
    # This is a proxy check - if extracted text is very short relative
    # to what we'd expect from a resume, it might be image-heavy
    
    word_count = len(text.split())
    
    # A typical resume should have at least 100-200 words
    # If we have very few words, it might be mostly images/graphics
    return word_count < 50


def check_font_readability(text: str) -> bool:
    """Check for font readability issues (basic heuristics)."""
    # Look for excessive special characters that might indicate
    # decorative fonts or encoding issues
    
    special_char_count = 0
    total_chars = len(text)
    
    if total_chars == 0:
        return False
    
    for char in text:
        if not char.isalnum() and char not in ' \n\t.,;:!?()-_[]{}"\'/':
            special_char_count += 1
    
    # If more than 5% special characters, might be font issue
    return (special_char_count / total_chars) > 0.05


def check_contact_info_format(text: str) -> Tuple[bool, List[str]]:
    """Check contact information formatting."""
    issues = []
    has_email = bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text))
    has_phone = bool(re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', text))
    
    if not has_email:
        issues.append("No email address found")
    
    if not has_phone:
        issues.append("No phone number found")
    
    # Check for clickable links (good practice)
    has_links = bool(re.search(r'https?://|www\.', text))
    
    return len(issues) == 0, issues


def check_section_headers(text: str) -> bool:
    """Check if section headers are clear and standard (more strict)."""
    # Count standard section headers (expanded list)
    standard_headers = [
        r'experience', r'education', r'skills', r'summary',
        r'work\s+experience', r'professional\s+experience',
        r'technical\s+skills', r'core\s+competencies',
        r'employment', r'career', r'background', r'qualifications',
        r'achievements', r'accomplishments', r'projects'
    ]
    
    found_headers = 0
    for header_pattern in standard_headers:
        if re.search(header_pattern, text, re.IGNORECASE):
            found_headers += 1
    
    # Should have at least 3 standard headers (increased requirement)
    return found_headers >= 3


def check_ats_compatibility(text: str) -> ATSWarnings:
    """Perform comprehensive ATS compatibility check (much more strict)."""
    logger.info("Starting ATS compatibility check", text_length=len(text))
    
    warnings = []
    passes = []
    
    # Check multi-column layout
    if check_multi_column_layout(text):
        warnings.append("Multi-column layout detected - may break ATS parsing")
    else:
        passes.append("Single-column layout is ATS-friendly")
    
    # Check table formatting
    if check_table_formatting(text):
        warnings.append("Table-like formatting may break parsers")
    else:
        passes.append("No complex table formatting detected")
    
    # Check image content
    if check_image_heavy_content(text):
        warnings.append("Low text density - document may be image-heavy")
    else:
        passes.append("Good text density for ATS parsing")
    
    # Check font readability
    if check_font_readability(text):
        warnings.append("Unusual characters detected - may indicate font issues")
    else:
        passes.append("Text appears cleanly formatted")
    
    # Check contact info
    contact_ok, contact_issues = check_contact_info_format(text)
    if not contact_ok:
        for issue in contact_issues:
            warnings.append(f"Contact info: {issue}")
    else:
        passes.append("Contact information is properly formatted")
    
    # Check section headers
    if not check_section_headers(text):
        warnings.append("Missing or unclear section headers - need at least 3 standard sections")
    else:
        passes.append("Clear section headers found")
    
    # More strict word count requirements
    word_count = len(text.split())
    if word_count < 300:  # Increased minimum
        warnings.append("Resume too short - needs more detailed descriptions and achievements")
    elif word_count > 800:  # Decreased maximum
        warnings.append("Resume too long - ATS may truncate or skip content")
    else:
        passes.append("Resume length is appropriate")
    
    # Check for quantified achievements (stricter)
    numbers_count = len(re.findall(r'\b\d+(?:[.,]\d+)*(?:%|\$|k|million|billion)?\b', text))
    if numbers_count < 5:
        warnings.append("Lacks sufficient quantified achievements - add more specific numbers, percentages, and metrics")
    else:
        passes.append("Good use of quantified achievements")
    
    # Check for action verbs
    action_verbs = ['achieved', 'managed', 'led', 'developed', 'created', 'improved', 
                   'increased', 'reduced', 'implemented', 'designed', 'built', 'delivered']
    action_verb_count = sum(1 for verb in action_verbs if verb in text.lower())
    if action_verb_count < 3:
        warnings.append("Few action verbs found - use strong action words to describe accomplishments")
    else:
        passes.append("Good use of action verbs")
    
    # Check for common ATS-unfriendly elements
    if re.search(r'[^\x00-\x7F]', text):  # Non-ASCII characters
        warnings.append("Non-standard characters found - may cause parsing issues")
    else:
        passes.append("Standard character encoding used")
    
    # Check for excessive formatting
    if text.count('•') > 25:  # Reduced threshold
        warnings.append("Excessive bullet points may overwhelm ATS")
    elif text.count('•') < 3:
        warnings.append("Too few bullet points - use bullets to structure content")
    else:
        passes.append("Appropriate use of bullet points")
    
    # Check for file format indicators
    if any(indicator in text.lower() for indicator in ['image', 'graphic', 'chart', 'table']):
        warnings.append("References to visual elements that ATS cannot parse")
    
    # Check for personal pronouns (should be minimal)
    pronouns = ['i ', 'me ', 'my ', 'myself']
    pronoun_count = sum(text.lower().count(pronoun) for pronoun in pronouns)
    if pronoun_count > 3:
        warnings.append("Too many personal pronouns - use action-focused language instead")
    else:
        passes.append("Appropriate use of professional language")
    
    # Check for skills section density
    skills_keywords = ['skill', 'proficient', 'experience with', 'knowledge of']
    skills_mentions = sum(1 for keyword in skills_keywords if keyword in text.lower())
    if skills_mentions < 2:
        warnings.append("Skills section appears weak - clearly list technical and professional skills")
    
    # Check for dates format
    date_patterns = [r'\d{4}\s*-\s*\d{4}', r'\d{1,2}/\d{4}', r'[A-Za-z]+\s+\d{4}']
    date_count = sum(len(re.findall(pattern, text)) for pattern in date_patterns)
    if date_count < 2:
        warnings.append("Missing or unclear date formats - use consistent MM/YYYY format")
    
    # Check for education details
    if not re.search(r'(bachelor|master|phd|degree|university|college)', text, re.IGNORECASE):
        warnings.append("Education section missing or unclear")
    
    logger.info(
        "ATS compatibility check completed",
        warnings_count=len(warnings),
        passes_count=len(passes),
    )
    
    return ATSWarnings(
        warnings=warnings,
        passes=passes,
    )
