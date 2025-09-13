"""Scoring service for resume analysis."""

from typing import Dict, Any
from datetime import datetime

import structlog

from ats_analyzer.api.dto import Score
from ats_analyzer.services.extract import ExtractedEntities
from ats_analyzer.services.jd import JDRequirements
from ats_analyzer.services.match import MatchResults
from ats_analyzer.core.config import get_scoring_config

logger = structlog.get_logger(__name__)


def calculate_coverage_score(matches: MatchResults, jd_requirements: JDRequirements) -> int:
    """Calculate skill coverage score (much harsher)."""
    config = get_scoring_config()
    
    total_required = len(jd_requirements.required_skills)
    total_preferred = len(jd_requirements.preferred_skills)
    
    if total_required == 0 and total_preferred == 0:
        return 80  # Lower default score
    
    # Count hits above threshold (with stricter validation)
    required_hits = sum(
        1 for match in matches.required_matches
        if match.evidence is not None  # Only count if we have evidence
    )
    
    preferred_hits = sum(
        1 for match in matches.preferred_matches
        if match.evidence is not None  # Only count if we have evidence
    )
    
    # Much harsher scoring
    if total_required > 0:
        required_score = (required_hits / total_required) * 100
        # HARSH penalty for missing required skills
        missing_required = total_required - required_hits
        if missing_required > 0:
            # Each missing required skill costs 15 points
            required_score = max(0, required_score - (missing_required * 15))
    else:
        required_score = 90  # Good score if no requirements
    
    if total_preferred > 0:
        preferred_score = (preferred_hits / total_preferred) * 100
        # Penalty for missing preferred skills (less harsh)
        missing_preferred = total_preferred - preferred_hits
        if missing_preferred > 0:
            # Each missing preferred skill costs 5 points
            preferred_score = max(0, preferred_score - (missing_preferred * 5))
    else:
        preferred_score = 80  # Decent score if no preferences
    
    # Combine with 80% weight on required, 20% on preferred (more emphasis on required)
    if total_required > 0 and total_preferred > 0:
        coverage_score = (required_score * 0.8) + (preferred_score * 0.2)
    elif total_required > 0:
        coverage_score = required_score
    else:
        coverage_score = preferred_score * 0.8  # Penalty if only preferred skills
    
    # Additional penalty for very low hit rates
    total_skills = total_required + total_preferred
    total_hits = required_hits + preferred_hits
    hit_rate = total_hits / max(total_skills, 1)
    
    if hit_rate < 0.3:  # Less than 30% hit rate
        coverage_score *= 0.7  # 30% penalty
    elif hit_rate < 0.5:  # Less than 50% hit rate
        coverage_score *= 0.85  # 15% penalty
    
    return min(100, max(0, int(coverage_score)))


def calculate_experience_score(
    resume_entities: ExtractedEntities,
    jd_requirements: JDRequirements,
    matches: MatchResults
) -> int:
    """Calculate experience relevance score (made more harsh and accurate)."""
    config = get_scoring_config()
    
    # Start with very low base score - experience must be proven
    experience_score = 10  # Much lower base score
    
    # Years of experience factor (extremely harsh for senior roles)
    actual_years = resume_entities.total_experience_months / 12
    
    # Analyze the job requirements to determine seniority level
    jd_text = str(jd_requirements).lower()
    is_senior_role = any(term in jd_text for term in [
        'senior', 'lead', 'principal', 'staff', 'founding', 'architect',
        '5+ years', '5 years', 'experienced', 'expert'
    ])
    
    # Determine minimum experience threshold based on role
    min_years_for_role = 5 if is_senior_role else 2
    
    if jd_requirements.experience_years > 0:
        required_years = max(jd_requirements.experience_years, min_years_for_role)
        
        if actual_years >= required_years:
            # Only give good scores if significantly exceeding requirement
            if actual_years >= required_years * 1.5:
                experience_score += 35  # Exceeds requirement significantly
            elif actual_years >= required_years * 1.2:
                experience_score += 25  # Comfortably meets requirement
            else:
                experience_score += 15  # Just meets requirement
        else:
            # HARSH penalty for insufficient experience
            ratio = actual_years / required_years
            if ratio >= 0.8:  # Close to requirement (80%)
                experience_score += int(10 * ratio)
            elif ratio >= 0.6:  # Somewhat close (60%)
                experience_score += int(5 * ratio)
            elif ratio >= 0.4:  # Far below (40%)
                experience_score += int(3 * ratio)
            else:  # Severely underqualified
                experience_score += int(1 * ratio)
    else:
        # If no specific requirement, infer from role type
        required_years = min_years_for_role
        if actual_years >= required_years:
            experience_score += 20
        else:
            ratio = actual_years / required_years
            experience_score += int(15 * ratio)
    
    # Recency analysis - more harsh about gaps and outdated experience
    current_year = datetime.now().year
    recency_boost_years = config.get("recency_years_boost", 2)
    
    has_recent_experience = False
    has_current_role = False
    
    for exp in resume_entities.experience:
        if exp.end_date:
            try:
                if "present" in exp.end_date.lower() or "current" in exp.end_date.lower():
                    experience_score += 15  # Current role bonus
                    has_current_role = True
                    has_recent_experience = True
                else:
                    # Extract year from end date
                    import re
                    year_match = re.search(r'\d{4}', exp.end_date)
                    if year_match:
                        end_year = int(year_match.group())
                        years_ago = current_year - end_year
                        if years_ago <= recency_boost_years:
                            experience_score += 8  # Recent experience bonus
                            has_recent_experience = True
                        elif years_ago <= 5:
                            experience_score += 3  # Somewhat recent
                        else:
                            # Penalty for very old experience
                            experience_score -= 2
            except:
                pass
    
    # Penalty for no recent experience
    if not has_recent_experience:
        experience_score -= 15
    
    # Check for employment gaps (harsh penalty)
    if len(resume_entities.experience) > 1:
        # Simple gap detection - if total months is much less than expected
        expected_months = (current_year - 2020) * 12  # Assume working since 2020
        if resume_entities.total_experience_months < expected_months * 0.6:
            experience_score -= 10  # Gap penalty
    
    # Skill-experience alignment
    section_weights = config.get("section_weights", {})
    skill_alignment_bonus = 0
    
    for match in matches.required_matches + matches.preferred_matches:
        if match.resume_skill and match.similarity >= 0.75:
            # Give bonus for skills found in experience vs just skills section
            section_weight = section_weights.get(match.resume_skill.section, 0.4)
            if section_weight >= 0.8:  # Experience or projects section
                skill_alignment_bonus += 2
    
    experience_score += min(20, skill_alignment_bonus)  # Cap the bonus
    
    return min(100, max(0, int(experience_score)))


def calculate_education_score(
    resume_entities: ExtractedEntities,
    jd_requirements: JDRequirements
) -> int:
    """Calculate education fit score (more harsh and considers graduation date)."""
    if jd_requirements.education_level == "unspecified":
        return 70  # Lower default score - education still matters
    
    education_score = 30  # Lower base score
    
    if not resume_entities.education:
        return 10  # Very low score if no education info
    
    # Education level mapping
    education_levels = {
        "high_school": 1,
        "associate": 2,
        "bachelor": 3,
        "master": 4,
        "phd": 5,
    }
    
    required_level = education_levels.get(jd_requirements.education_level, 0)
    
    # Find highest education level and check recency
    highest_level = 0
    most_recent_grad_year = 0
    current_year = datetime.now().year
    
    for edu in resume_entities.education:
        edu_text = edu.degree.lower()
        
        # Extract graduation year if available
        grad_year = 0
        if hasattr(edu, 'end_date') and edu.end_date:
            import re
            year_match = re.search(r'\d{4}', str(edu.end_date))
            if year_match:
                grad_year = int(year_match.group())
                most_recent_grad_year = max(most_recent_grad_year, grad_year)
        
        # Determine education level
        for level_name, level_value in education_levels.items():
            if level_name.replace("_", " ") in edu_text or level_name in edu_text:
                highest_level = max(highest_level, level_value)
                break
    
    # Score based on education level match
    if highest_level >= required_level:
        if highest_level > required_level:
            education_score = 85  # Exceeds requirement
        else:
            education_score = 75  # Meets requirement exactly
    elif highest_level > 0:
        # Much harsher penalty for insufficient education
        ratio = highest_level / max(required_level, 1)
        if ratio >= 0.8:  # Close to requirement
            education_score = int(30 + (35 * ratio))
        else:  # Far below requirement
            education_score = int(30 + (20 * ratio))
    
    # Factor in graduation recency (education can become outdated)
    if most_recent_grad_year > 0:
        years_since_grad = current_year - most_recent_grad_year
        if years_since_grad <= 5:
            education_score += 10  # Recent graduate bonus
        elif years_since_grad <= 10:
            education_score += 5   # Somewhat recent
        elif years_since_grad > 20:
            education_score -= 5   # Very old degree penalty
    
    # Check for relevant field of study (basic check)
    # This is a simplified check - in reality would need more sophisticated matching
    for edu in resume_entities.education:
        if hasattr(edu, 'field') and edu.field:
            field_text = edu.field.lower()
            # Look for technical fields that might be relevant
            if any(tech in field_text for tech in ['computer', 'engineering', 'science', 'technology', 'business']):
                education_score += 5
                break
    
    return min(100, max(0, int(education_score)))


def calculate_overall_score(
    coverage_score: int,
    experience_score: int,
    education_score: int
) -> int:
    """Calculate overall weighted score."""
    config = get_scoring_config()
    weights = config.get("weights", {
        "coverage": 0.6,
        "experience": 0.3,
        "education": 0.1,
    })
    
    overall = (
        coverage_score * weights["coverage"] +
        experience_score * weights["experience"] +
        education_score * weights["education"]
    )
    
    return min(100, max(0, int(overall)))


def calculate_scores(
    matches: MatchResults,
    jd_requirements: JDRequirements,
    resume_entities: ExtractedEntities
) -> Score:
    """Calculate all scores for resume analysis."""
    logger.info("Starting score calculation")
    
    # Calculate individual scores
    coverage_score = calculate_coverage_score(matches, jd_requirements)
    experience_score = calculate_experience_score(resume_entities, jd_requirements, matches)
    education_score = calculate_education_score(resume_entities, jd_requirements)
    
    # Calculate overall score (with extremely harsh reality checks)
    overall_score = calculate_overall_score(coverage_score, experience_score, education_score)
    
    # MUCH more aggressive reality checks
    penalties = []
    
    # Skill coverage penalties
    if coverage_score < 60:
        penalty = 0.7  # 30% penalty for poor skill match
        overall_score = int(overall_score * penalty)
        penalties.append(f"Poor skill coverage ({coverage_score}%)")
    elif coverage_score < 75:
        penalty = 0.85  # 15% penalty for mediocre skill match
        overall_score = int(overall_score * penalty)
        penalties.append(f"Mediocre skill coverage ({coverage_score}%)")
    
    # Experience penalties (very harsh)
    if experience_score < 30:
        penalty = 0.6  # 40% penalty for poor experience
        overall_score = int(overall_score * penalty)
        penalties.append(f"Severely underqualified experience ({experience_score}%)")
    elif experience_score < 50:
        penalty = 0.75  # 25% penalty for weak experience
        overall_score = int(overall_score * penalty)
        penalties.append(f"Insufficient experience ({experience_score}%)")
    
    # Education penalties
    if education_score < 40:
        penalty = 0.9  # 10% penalty for poor education fit
        overall_score = int(overall_score * penalty)
        penalties.append(f"Poor education fit ({education_score}%)")
    
    # Cap scores that seem unrealistic
    if overall_score > 80:
        if experience_score < 60 or coverage_score < 70:
            overall_score = min(overall_score, 65)  # Much lower cap
            penalties.append("Capped due to weak fundamentals")
    
    if overall_score > 70:
        if experience_score < 40 or coverage_score < 60:
            overall_score = min(overall_score, 50)  # Very low cap for weak candidates
            penalties.append("Capped due to major deficiencies")
    
    # Log the penalties applied
    if penalties:
        logger.info("Applied scoring penalties", penalties=penalties, final_score=overall_score)
    
    logger.info(
        "Score calculation completed",
        overall=overall_score,
        coverage=coverage_score,
        experience=experience_score,
        education=education_score,
    )
    
    return Score(
        overall=overall_score,
        coverage=coverage_score,
        experience=experience_score,
        education=education_score,
    )
