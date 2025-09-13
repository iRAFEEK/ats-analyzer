"""Test configuration and fixtures."""

import os
import tempfile
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from ats_analyzer.main import app
from ats_analyzer.models.base import Base
from ats_analyzer.deps import get_db

# Test database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    """Create test client."""
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_resume_text() -> str:
    """Sample resume text for testing."""
    return """
    John Doe
    Software Engineer
    
    EXPERIENCE
    Senior Software Engineer - Tech Corp (2020-2023)
    • Developed web applications using Python, Django, and React
    • Built RESTful APIs serving 10k+ daily active users
    • Implemented CI/CD pipelines using Docker and Kubernetes
    • Led team of 5 developers on microservices architecture
    
    Software Developer - StartupXYZ (2018-2020)
    • Created full-stack applications with Node.js and PostgreSQL
    • Optimized database queries improving performance by 40%
    • Integrated third-party APIs and payment systems
    
    EDUCATION
    Bachelor of Science in Computer Science
    University of Technology (2014-2018)
    GPA: 3.8/4.0
    
    SKILLS
    Programming: Python, JavaScript, TypeScript, Java
    Web: React, Django, Node.js, HTML/CSS
    Database: PostgreSQL, MongoDB, Redis
    Cloud: AWS, Docker, Kubernetes
    Tools: Git, Jenkins, Jira
    """


@pytest.fixture
def sample_job_description() -> str:
    """Sample job description for testing."""
    return """
    Senior Full Stack Developer
    
    We are seeking a Senior Full Stack Developer to join our growing team.
    
    REQUIRED QUALIFICATIONS:
    • 3+ years of experience in web development
    • Strong proficiency in Python and JavaScript
    • Experience with React and modern frontend frameworks
    • Knowledge of database systems (PostgreSQL preferred)
    • Familiarity with cloud platforms (AWS, GCP, or Azure)
    • Experience with version control systems (Git)
    
    PREFERRED QUALIFICATIONS:
    • Experience with Docker and containerization
    • Knowledge of microservices architecture
    • Familiarity with CI/CD pipelines
    • Experience with TypeScript
    • Background in agile development methodologies
    
    RESPONSIBILITIES:
    • Design and develop scalable web applications
    • Collaborate with cross-functional teams
    • Participate in code reviews and technical discussions
    • Mentor junior developers
    """


@pytest.fixture
def sample_pdf_file():
    """Create a sample PDF file for testing."""
    # Create a simple PDF-like file for testing
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(b"%PDF-1.4\n")
        f.write(b"Sample PDF content for testing")
        return f.name


@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment variables."""
    os.environ["DATABASE_URL"] = SQLALCHEMY_DATABASE_URL
    os.environ["REDIS_URL"] = "redis://localhost:6379/1"  # Use different DB for tests
    os.environ["LOG_LEVEL"] = "DEBUG"
    yield
    # Cleanup is handled by session fixture
