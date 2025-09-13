"""Data Transfer Objects (DTOs) for API requests and responses."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# Parse API DTOs
class ParseMeta(BaseModel):
    """Metadata about parsed document."""
    filetype: str = Field(..., description="File type: pdf, docx, or image")
    has_columns: bool = Field(..., description="Whether document has multi-column layout")
    has_tables: bool = Field(..., description="Whether document contains tables")
    extractability_score: float = Field(..., ge=0.0, le=1.0, description="How well text was extracted")
    ocr_used: bool = Field(..., description="Whether OCR was used for extraction")


class ParseResponse(BaseModel):
    """Response from /parse endpoint."""
    text: str = Field(..., description="Extracted text content")
    sections: Dict[str, str] = Field(..., description="Sectioned content")
    meta: ParseMeta = Field(..., description="Extraction metadata")


# Analyze API DTOs
class AnalyzeRequest(BaseModel):
    """Request for /analyze endpoint."""
    resume_text: str = Field(..., description="Resume text content")
    jd_text: str = Field(..., description="Job description text")


class Score(BaseModel):
    """Scoring breakdown."""
    overall: int = Field(..., ge=0, le=100, description="Overall score")
    coverage: int = Field(..., ge=0, le=100, description="Skill coverage score")
    experience: int = Field(..., ge=0, le=100, description="Experience relevance score")
    education: int = Field(..., ge=0, le=100, description="Education fit score")


class MissingSkills(BaseModel):
    """Missing skills breakdown."""
    required: List[str] = Field(default_factory=list, description="Missing required skills")
    preferred: List[str] = Field(default_factory=list, description="Missing preferred skills")


class Suggestion(BaseModel):
    """Improvement suggestion."""
    before: str = Field(..., description="Original text")
    after: str = Field(..., description="Suggested improvement")
    rationale: str = Field(..., description="Why this improvement helps")


class ATSWarnings(BaseModel):
    """ATS formatting warnings and passes."""
    warnings: List[str] = Field(default_factory=list, description="Formatting issues")
    passes: List[str] = Field(default_factory=list, description="Good formatting practices")


class Evidence(BaseModel):
    """Evidence for skill matching."""
    skill: str = Field(..., description="Matched skill")
    section: str = Field(..., description="Section where found")
    quote: str = Field(..., description="Relevant text quote")
    similarity: float = Field(..., ge=0.0, le=1.0, description="Similarity score")


class AnalyzeResponse(BaseModel):
    """Response from /analyze endpoint."""
    score: Score = Field(..., description="Scoring breakdown")
    missing: MissingSkills = Field(..., description="Missing skills")
    weakly_supported: List[str] = Field(default_factory=list, description="Weakly supported skills")
    suggestions: List[Suggestion] = Field(default_factory=list, description="Improvement suggestions")
    ats: ATSWarnings = Field(..., description="ATS compatibility warnings")
    evidence: List[Evidence] = Field(default_factory=list, description="Evidence for matches")


# Error DTOs
class ErrorDetail(BaseModel):
    """Error detail."""
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class ErrorResponse(BaseModel):
    """Error response."""
    error: ErrorDetail = Field(..., description="Error information")
    request_id: Optional[str] = Field(None, description="Request ID for tracing")
