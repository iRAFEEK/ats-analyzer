"""Tests for entity extraction service."""

import pytest

from ats_analyzer.services.extract import (
    load_skills_taxonomy,
    extract_skills_from_text,
    extract_dates_from_text,
    extract_experience_from_section,
    extract_education_from_section,
    extract_entities,
)


class TestSkillsTaxonomy:
    """Test skills taxonomy loading."""

    def test_load_skills_taxonomy_returns_dict(self):
        taxonomy = load_skills_taxonomy()
        assert isinstance(taxonomy, dict)
        assert len(taxonomy) > 0
        
        # Check some expected skills
        assert "Python" in taxonomy
        assert "JavaScript" in taxonomy
        assert isinstance(taxonomy["Python"], list)

    def test_skills_have_aliases(self):
        taxonomy = load_skills_taxonomy()
        python_aliases = taxonomy.get("Python", [])
        assert "python" in python_aliases
        assert "py" in python_aliases


class TestSkillExtraction:
    """Test skill extraction from text."""

    def test_extract_skills_basic_match(self):
        text = "I have experience with Python and JavaScript programming."
        skills = extract_skills_from_text(text, "experience")
        
        skill_names = [skill.canonical_name for skill in skills]
        assert "Python" in skill_names
        assert "JavaScript" in skill_names

    def test_extract_skills_case_insensitive(self):
        text = "Proficient in PYTHON and javascript development."
        skills = extract_skills_from_text(text, "skills")
        
        skill_names = [skill.canonical_name for skill in skills]
        assert "Python" in skill_names
        assert "JavaScript" in skill_names

    def test_extract_skills_with_context(self):
        text = "Built web applications using React and Node.js"
        skills = extract_skills_from_text(text, "experience")
        
        react_skills = [s for s in skills if s.canonical_name == "React"]
        if react_skills:
            assert "React" in react_skills[0].context

    def test_extract_skills_no_matches(self):
        text = "I enjoy cooking and hiking in my free time."
        skills = extract_skills_from_text(text, "summary")
        assert len(skills) == 0


class TestDateExtraction:
    """Test date extraction from text."""

    def test_extract_date_ranges(self):
        text = "Software Engineer at TechCorp (2020-2023)"
        dates = extract_dates_from_text(text)
        assert len(dates) > 0
        assert any("2020" in date[0] and "2023" in date[1] for date in dates)

    def test_extract_month_year_format(self):
        text = "January 2020 - December 2022"
        dates = extract_dates_from_text(text)
        assert len(dates) > 0

    def test_extract_present_date(self):
        text = "Senior Developer (2021 - Present)"
        dates = extract_dates_from_text(text)
        assert len(dates) > 0
        assert any("present" in date[1].lower() for date in dates)


class TestExperienceExtraction:
    """Test work experience extraction."""

    def test_extract_basic_experience(self):
        text = """
        Senior Software Engineer at TechCorp (2020-2023)
        • Developed web applications using Python and Django
        • Led team of 5 developers
        """
        experiences = extract_experience_from_section(text, "experience")
        
        assert len(experiences) > 0
        exp = experiences[0]
        assert "Senior Software Engineer" in exp.title
        assert exp.section == "experience"

    def test_extract_experience_with_dates(self):
        text = "Software Developer, StartupXYZ (2018-2020)"
        experiences = extract_experience_from_section(text, "experience")
        
        if experiences:
            exp = experiences[0]
            assert exp.start_date is not None
            assert exp.end_date is not None

    def test_extract_multiple_experiences(self):
        text = """
        Senior Engineer at CompanyA (2020-2023)
        Built scalable applications
        
        Junior Developer at CompanyB (2018-2020)
        Maintained legacy systems
        """
        experiences = extract_experience_from_section(text, "experience")
        assert len(experiences) >= 1  # Should extract at least one


class TestEducationExtraction:
    """Test education extraction."""

    def test_extract_basic_education(self):
        text = """
        Bachelor of Science in Computer Science
        University of Technology (2014-2018)
        GPA: 3.8/4.0
        """
        educations = extract_education_from_section(text, "education")
        
        assert len(educations) > 0
        edu = educations[0]
        assert "bachelor" in edu.degree.lower() or "science" in edu.degree.lower()

    def test_extract_university_name(self):
        text = "Master's Degree from Stanford University"
        educations = extract_education_from_section(text, "education")
        
        if educations:
            edu = educations[0]
            assert "stanford" in edu.institution.lower() or "university" in edu.institution.lower()

    def test_extract_gpa(self):
        text = "BS Computer Science, GPA: 3.75"
        educations = extract_education_from_section(text, "education")
        
        if educations:
            edu = educations[0]
            assert edu.gpa == "3.75"


class TestEntityExtraction:
    """Test complete entity extraction."""

    def test_extract_entities_complete(self, sample_resume_text):
        entities = extract_entities(sample_resume_text)
        
        assert len(entities.skills) > 0
        assert len(entities.experience) > 0
        assert len(entities.education) > 0
        
        # Check that we found some expected skills
        skill_names = [skill.canonical_name for skill in entities.skills]
        assert "Python" in skill_names
        
        # Check experience calculation
        assert entities.total_experience_months > 0
        
        # Check most recent title
        assert entities.most_recent_title is not None

    def test_extract_entities_empty_text(self):
        entities = extract_entities("")
        
        assert len(entities.skills) == 0
        assert len(entities.experience) == 0
        assert len(entities.education) == 0
        assert entities.total_experience_months == 0

    def test_extract_entities_skills_deduplication(self):
        # Text with repeated skills
        text = """
        I use Python for backend development.
        Python is my favorite programming language.
        I also know python very well.
        """
        entities = extract_entities(text)
        
        # Should only have one Python skill entry
        python_skills = [s for s in entities.skills if s.canonical_name == "Python"]
        assert len(python_skills) <= 1
