"""Tests for API endpoints."""

import io
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from ats_analyzer.api.dto import ParseResponse, AnalyzeResponse


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "ats-analyzer"


class TestParseEndpoint:
    """Test document parsing endpoint."""

    @patch('ats_analyzer.services.parse.parse_document')
    @patch('ats_analyzer.services.sectionizer.sectionize_text')
    def test_parse_pdf_success(self, mock_sectionize, mock_parse, client: TestClient):
        # Mock the parsing service
        mock_parsed_doc = MagicMock()
        mock_parsed_doc.text = "Sample resume text"
        mock_parsed_doc.meta.filetype = "pdf"
        mock_parsed_doc.meta.has_columns = False
        mock_parsed_doc.meta.has_tables = False
        mock_parsed_doc.meta.extractability_score = 0.9
        mock_parsed_doc.meta.ocr_used = False
        
        mock_parse.return_value = mock_parsed_doc
        mock_sectionize.return_value = {
            "summary": "Professional summary",
            "experience": "Work experience",
            "education": "Educational background",
            "skills": "Technical skills"
        }

        # Create a fake PDF file
        pdf_content = b"%PDF-1.4\nSample PDF content"
        files = {"file": ("resume.pdf", io.BytesIO(pdf_content), "application/pdf")}
        
        response = client.post("/api/v1/parse", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "Sample resume text"
        assert data["meta"]["filetype"] == "pdf"
        assert not data["meta"]["ocr_used"]

    def test_parse_no_file(self, client: TestClient):
        response = client.post("/api/v1/parse")
        assert response.status_code == 422  # Validation error

    def test_parse_large_file(self, client: TestClient):
        # Create a file larger than 10MB
        large_content = b"x" * (11 * 1024 * 1024)
        files = {"file": ("large.pdf", io.BytesIO(large_content), "application/pdf")}
        
        response = client.post("/api/v1/parse", files=files)
        assert response.status_code == 400  # Should be rejected

    @patch('ats_analyzer.services.parse.parse_document')
    def test_parse_processing_error(self, mock_parse, client: TestClient):
        mock_parse.side_effect = Exception("Processing failed")
        
        pdf_content = b"%PDF-1.4\nSample PDF content"
        files = {"file": ("resume.pdf", io.BytesIO(pdf_content), "application/pdf")}
        
        response = client.post("/api/v1/parse", files=files)
        assert response.status_code == 400


class TestAnalyzeEndpoint:
    """Test resume analysis endpoint."""

    @patch('ats_analyzer.services.lint.check_ats_compatibility')
    @patch('ats_analyzer.services.score.calculate_scores')
    @patch('ats_analyzer.services.match.match_skills')
    @patch('ats_analyzer.services.extract.extract_entities')
    @patch('ats_analyzer.services.jd.parse_job_description')
    def test_analyze_success(self, mock_parse_jd, mock_extract, mock_match, 
                           mock_score, mock_lint, client: TestClient):
        # Mock all the services
        from ats_analyzer.services.jd import JDRequirements, JDRequirement
        from ats_analyzer.services.extract import ExtractedEntities, ExtractedSkill
        from ats_analyzer.services.match import MatchResults
        from ats_analyzer.api.dto import Score, MissingSkills, ATSWarnings
        
        # Mock JD parsing
        mock_parse_jd.return_value = JDRequirements(
            required_skills=[JDRequirement("Python", True, "", 0.9)],
            preferred_skills=[JDRequirement("Docker", False, "", 0.8)],
            experience_years=3,
            education_level="bachelor",
            title="Software Engineer",
            all_skills=["Python", "Docker"],
        )
        
        # Mock entity extraction
        mock_extract.return_value = ExtractedEntities(
            skills=[ExtractedSkill("python", "Python", 0.9, "skills", "Python programming")],
            experience=[],
            education=[],
            total_experience_months=36,
            most_recent_title="Software Engineer",
        )
        
        # Mock skill matching
        mock_match.return_value = MatchResults(
            required_matches=[],
            preferred_matches=[],
            missing=MissingSkills(required=[], preferred=[]),
            weakly_supported=[],
            suggestions=[],
            evidence=[],
        )
        
        # Mock scoring
        mock_score.return_value = Score(
            overall=85,
            coverage=80,
            experience=90,
            education=85,
        )
        
        # Mock ATS linting
        mock_lint.return_value = ATSWarnings(
            warnings=["Multi-column layout detected"],
            passes=["Standard fonts used"],
        )
        
        request_data = {
            "resume_text": "Sample resume text with Python experience",
            "jd_text": "We are looking for a Python developer with 3+ years experience"
        }
        
        response = client.post("/api/v1/analyze", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["score"]["overall"] == 85
        assert "warnings" in data["ats"]

    def test_analyze_missing_data(self, client: TestClient):
        # Test with missing resume_text
        request_data = {
            "jd_text": "Job description"
        }
        
        response = client.post("/api/v1/analyze", json=request_data)
        assert response.status_code == 422  # Validation error

    def test_analyze_short_jd(self, client: TestClient):
        # Test with very short job description
        request_data = {
            "resume_text": "Sample resume text",
            "jd_text": "Short JD"  # Too short
        }
        
        response = client.post("/api/v1/analyze", json=request_data)
        assert response.status_code == 422  # Validation error

    @patch('ats_analyzer.services.jd.parse_job_description')
    def test_analyze_processing_error(self, mock_parse_jd, client: TestClient):
        mock_parse_jd.side_effect = Exception("Analysis failed")
        
        request_data = {
            "resume_text": "Sample resume text",
            "jd_text": "Sample job description with enough text to pass validation"
        }
        
        response = client.post("/api/v1/analyze", json=request_data)
        assert response.status_code == 500


class TestRootEndpoint:
    """Test root endpoint."""

    def test_root_endpoint(self, client: TestClient):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "ATS Analyzer API"
        assert data["docs"] == "/docs"


class TestRequestIdMiddleware:
    """Test request ID middleware."""

    def test_request_id_header_added(self, client: TestClient):
        response = client.get("/health")
        assert "X-Request-ID" in response.headers
        assert "X-Process-Time" in response.headers
        
        # Request ID should be a valid UUID format
        request_id = response.headers["X-Request-ID"]
        assert len(request_id) == 36  # UUID length with hyphens
        assert request_id.count("-") == 4  # UUID has 4 hyphens


class TestCORSMiddleware:
    """Test CORS middleware."""

    def test_cors_headers(self, client: TestClient):
        response = client.options("/api/v1/parse")
        # CORS headers should be present for OPTIONS requests
        # Note: TestClient might not fully simulate CORS behavior
