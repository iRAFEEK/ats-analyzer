"""Tests for scoring service."""

import pytest

from ats_analyzer.services.score import (
    calculate_coverage_score,
    calculate_experience_score,
    calculate_education_score,
    calculate_overall_score,
    calculate_scores,
)
from ats_analyzer.services.match import SkillMatch, MatchResults
from ats_analyzer.services.jd import JDRequirement, JDRequirements
from ats_analyzer.services.extract import ExtractedEntities, ExtractedSkill, ExtractedExperience, ExtractedEducation
from ats_analyzer.api.dto import MissingSkills, Evidence


class TestCoverageScore:
    """Test skill coverage scoring."""

    def test_perfect_coverage_score(self):
        # Mock perfect matches
        required_matches = [
            SkillMatch("Python", None, 0.9, True, None),
            SkillMatch("JavaScript", None, 0.85, True, None),
        ]
        preferred_matches = [
            SkillMatch("Docker", None, 0.8, False, None),
        ]
        
        matches = MatchResults(
            required_matches=required_matches,
            preferred_matches=preferred_matches,
            missing=MissingSkills(required=[], preferred=[]),
            weakly_supported=[],
            suggestions=[],
            evidence=[],
        )
        
        jd_requirements = JDRequirements(
            required_skills=[
                JDRequirement("Python", True, "", 0.9),
                JDRequirement("JavaScript", True, "", 0.9),
            ],
            preferred_skills=[
                JDRequirement("Docker", False, "", 0.8),
            ],
            experience_years=3,
            education_level="bachelor",
            title="Software Engineer",
            all_skills=["Python", "JavaScript", "Docker"],
        )
        
        score = calculate_coverage_score(matches, jd_requirements)
        assert score >= 90  # Should be very high

    def test_partial_coverage_score(self):
        # Mock partial matches
        required_matches = [
            SkillMatch("Python", None, 0.9, True, None),
            SkillMatch("JavaScript", None, 0.5, True, None),  # Below threshold
        ]
        
        matches = MatchResults(
            required_matches=required_matches,
            preferred_matches=[],
            missing=MissingSkills(required=["JavaScript"], preferred=[]),
            weakly_supported=[],
            suggestions=[],
            evidence=[],
        )
        
        jd_requirements = JDRequirements(
            required_skills=[
                JDRequirement("Python", True, "", 0.9),
                JDRequirement("JavaScript", True, "", 0.5),
            ],
            preferred_skills=[],
            experience_years=3,
            education_level="bachelor",
            title="Software Engineer",
            all_skills=["Python", "JavaScript"],
        )
        
        score = calculate_coverage_score(matches, jd_requirements)
        assert 40 <= score <= 70  # Should be moderate

    def test_no_requirements_perfect_score(self):
        matches = MatchResults(
            required_matches=[],
            preferred_matches=[],
            missing=MissingSkills(required=[], preferred=[]),
            weakly_supported=[],
            suggestions=[],
            evidence=[],
        )
        
        jd_requirements = JDRequirements(
            required_skills=[],
            preferred_skills=[],
            experience_years=0,
            education_level="unspecified",
            title="Any Position",
            all_skills=[],
        )
        
        score = calculate_coverage_score(matches, jd_requirements)
        assert score == 100


class TestExperienceScore:
    """Test experience scoring."""

    def test_meets_experience_requirement(self):
        resume_entities = ExtractedEntities(
            skills=[],
            experience=[
                ExtractedExperience(
                    title="Senior Engineer",
                    company="TechCorp",
                    start_date="2020",
                    end_date="2023",
                    duration_months=36,
                    description="Built applications",
                    section="experience",
                )
            ],
            education=[],
            total_experience_months=36,  # 3 years
            most_recent_title="Senior Engineer",
        )
        
        jd_requirements = JDRequirements(
            required_skills=[],
            preferred_skills=[],
            experience_years=3,
            education_level="bachelor",
            title="Software Engineer",
            all_skills=[],
        )
        
        matches = MatchResults(
            required_matches=[],
            preferred_matches=[],
            missing=MissingSkills(required=[], preferred=[]),
            weakly_supported=[],
            suggestions=[],
            evidence=[],
        )
        
        score = calculate_experience_score(resume_entities, jd_requirements, matches)
        assert score >= 70  # Should be good

    def test_exceeds_experience_requirement(self):
        resume_entities = ExtractedEntities(
            skills=[],
            experience=[],
            education=[],
            total_experience_months=60,  # 5 years
            most_recent_title="Senior Engineer",
        )
        
        jd_requirements = JDRequirements(
            required_skills=[],
            preferred_skills=[],
            experience_years=3,
            education_level="bachelor",
            title="Software Engineer",
            all_skills=[],
        )
        
        matches = MatchResults(
            required_matches=[],
            preferred_matches=[],
            missing=MissingSkills(required=[], preferred=[]),
            weakly_supported=[],
            suggestions=[],
            evidence=[],
        )
        
        score = calculate_experience_score(resume_entities, jd_requirements, matches)
        assert score >= 80  # Should be very good

    def test_insufficient_experience(self):
        resume_entities = ExtractedEntities(
            skills=[],
            experience=[],
            education=[],
            total_experience_months=12,  # 1 year
            most_recent_title="Junior Developer",
        )
        
        jd_requirements = JDRequirements(
            required_skills=[],
            preferred_skills=[],
            experience_years=5,
            education_level="bachelor",
            title="Senior Engineer",
            all_skills=[],
        )
        
        matches = MatchResults(
            required_matches=[],
            preferred_matches=[],
            missing=MissingSkills(required=[], preferred=[]),
            weakly_supported=[],
            suggestions=[],
            evidence=[],
        )
        
        score = calculate_experience_score(resume_entities, jd_requirements, matches)
        assert score <= 70  # Should be lower


class TestEducationScore:
    """Test education scoring."""

    def test_meets_education_requirement(self):
        resume_entities = ExtractedEntities(
            skills=[],
            experience=[],
            education=[
                ExtractedEducation(
                    degree="Bachelor of Science in Computer Science",
                    institution="Tech University",
                    field="Computer Science",
                    graduation_date="2018",
                    gpa="3.8",
                    section="education",
                )
            ],
            total_experience_months=0,
            most_recent_title=None,
        )
        
        jd_requirements = JDRequirements(
            required_skills=[],
            preferred_skills=[],
            experience_years=0,
            education_level="bachelor",
            title="Software Engineer",
            all_skills=[],
        )
        
        score = calculate_education_score(resume_entities, jd_requirements)
        assert score >= 80  # Should be high

    def test_exceeds_education_requirement(self):
        resume_entities = ExtractedEntities(
            skills=[],
            experience=[],
            education=[
                ExtractedEducation(
                    degree="Master of Science in Computer Science",
                    institution="Elite University",
                    field="Computer Science",
                    graduation_date="2020",
                    gpa="3.9",
                    section="education",
                )
            ],
            total_experience_months=0,
            most_recent_title=None,
        )
        
        jd_requirements = JDRequirements(
            required_skills=[],
            preferred_skills=[],
            experience_years=0,
            education_level="bachelor",
            title="Software Engineer",
            all_skills=[],
        )
        
        score = calculate_education_score(resume_entities, jd_requirements)
        assert score == 90  # Should be very high

    def test_no_education_requirement(self):
        resume_entities = ExtractedEntities(
            skills=[],
            experience=[],
            education=[],
            total_experience_months=0,
            most_recent_title=None,
        )
        
        jd_requirements = JDRequirements(
            required_skills=[],
            preferred_skills=[],
            experience_years=0,
            education_level="unspecified",
            title="Any Position",
            all_skills=[],
        )
        
        score = calculate_education_score(resume_entities, jd_requirements)
        assert score == 80  # Default good score


class TestOverallScore:
    """Test overall score calculation."""

    def test_overall_score_calculation(self):
        coverage_score = 80
        experience_score = 70
        education_score = 90
        
        overall = calculate_overall_score(coverage_score, experience_score, education_score)
        
        # Should be weighted average: 0.6*80 + 0.3*70 + 0.1*90 = 48 + 21 + 9 = 78
        assert overall == 78

    def test_overall_score_bounds(self):
        # Test minimum
        overall_min = calculate_overall_score(0, 0, 0)
        assert overall_min == 0
        
        # Test maximum
        overall_max = calculate_overall_score(100, 100, 100)
        assert overall_max == 100


class TestCalculateScores:
    """Test complete scores calculation."""

    def test_calculate_scores_integration(self):
        # Mock data for integration test
        matches = MatchResults(
            required_matches=[
                SkillMatch("Python", None, 0.9, True, None),
            ],
            preferred_matches=[],
            missing=MissingSkills(required=[], preferred=[]),
            weakly_supported=[],
            suggestions=[],
            evidence=[],
        )
        
        jd_requirements = JDRequirements(
            required_skills=[
                JDRequirement("Python", True, "", 0.9),
            ],
            preferred_skills=[],
            experience_years=3,
            education_level="bachelor",
            title="Python Developer",
            all_skills=["Python"],
        )
        
        resume_entities = ExtractedEntities(
            skills=[
                ExtractedSkill("python", "Python", 0.9, "skills", "Expert in Python")
            ],
            experience=[],
            education=[
                ExtractedEducation(
                    degree="BS Computer Science",
                    institution="University",
                    field="CS",
                    graduation_date="2020",
                    gpa="3.5",
                    section="education",
                )
            ],
            total_experience_months=36,
            most_recent_title="Python Developer",
        )
        
        scores = calculate_scores(matches, jd_requirements, resume_entities)
        
        assert 0 <= scores.overall <= 100
        assert 0 <= scores.coverage <= 100
        assert 0 <= scores.experience <= 100
        assert 0 <= scores.education <= 100
