"""API routes for ATS Analyzer."""

import time
from typing import Dict, Any

import structlog
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse

from ats_analyzer.api.dto import (
    AnalyzeRequest,
    AnalyzeResponse,
    ErrorResponse,
    ParseResponse,
)
from ats_analyzer.core.errors import (
    ATSAnalyzerException,
    FileProcessingError,
    TextExtractionError,
)
from ats_analyzer.core.logging import redact_sensitive_data
from ats_analyzer.services.parse import parse_document
from ats_analyzer.services.sectionizer import sectionize_text
from ats_analyzer.services.extract import extract_entities
from ats_analyzer.services.jd import parse_job_description
from ats_analyzer.services.match import match_skills
from ats_analyzer.services.score import calculate_scores
from ats_analyzer.services.lint import check_ats_compatibility
from ats_analyzer.services.openai_analyzer import analyze_with_openai

logger = structlog.get_logger(__name__)
router = APIRouter()


# Exception handler will be added to the main app
async def ats_exception_handler(request: Request, exc: ATSAnalyzerException) -> JSONResponse:
    """Handle ATS-specific exceptions."""
    request_id = getattr(request.state, "request_id", None)
    
    logger.error(
        "ATS exception occurred",
        error_type=type(exc).__name__,
        error_message=exc.message,
        error_details=redact_sensitive_data(exc.details),
        request_id=request_id,
    )
    
    status_code = 400
    if isinstance(exc, FileProcessingError):
        status_code = 422
    elif isinstance(exc, TextExtractionError):
        status_code = 422
    
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            error={
                "message": exc.message,
                "code": type(exc).__name__,
                "details": exc.details,
            },
            request_id=request_id,
        ).dict(),
    )


@router.post("/parse", response_model=ParseResponse)
async def parse_resume(
    request: Request,
    file: UploadFile = File(..., description="Resume file (PDF/DOCX/PNG)")
) -> ParseResponse:
    """Parse resume file to extract text and sections."""
    start_time = time.time()
    request_id = getattr(request.state, "request_id", None)
    
    logger.info(
        "Starting document parse",
        filename=file.filename,
        content_type=file.content_type,
        file_size=file.size,
        request_id=request_id,
    )
    
    try:
        # Validate file
        if not file.filename:
            raise FileProcessingError("No filename provided")
        
        if file.size and file.size > 10 * 1024 * 1024:  # 10MB limit
            raise FileProcessingError("File size exceeds 10MB limit")
        
        # Read file content
        content = await file.read()
        
        # Parse document
        parse_start = time.time()
        parsed_doc = await parse_document(content, file.filename, file.content_type)
        parse_time = time.time() - parse_start
        
        # Sectionize text
        section_start = time.time()
        sections = sectionize_text(parsed_doc.text)
        section_time = time.time() - section_start
        
        total_time = time.time() - start_time
        
        logger.info(
            "Document parse completed",
            parse_time_ms=round(parse_time * 1000, 2),
            section_time_ms=round(section_time * 1000, 2),
            total_time_ms=round(total_time * 1000, 2),
            text_length=len(parsed_doc.text),
            sections_found=len(sections),
            ocr_used=parsed_doc.meta.ocr_used,
            request_id=request_id,
        )
        
        return ParseResponse(
            text=parsed_doc.text,
            sections=sections,
            meta=parsed_doc.meta,
        )
    
    except ATSAnalyzerException:
        raise
    except Exception as e:
        logger.error(
            "Unexpected error during parse",
            error=str(e),
            error_type=type(e).__name__,
            request_id=request_id,
        )
        raise FileProcessingError(f"Failed to parse document: {str(e)}")


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_resume(
    request: Request,
    analyze_request: AnalyzeRequest
) -> AnalyzeResponse:
    """Analyze resume against job description."""
    start_time = time.time()
    request_id = getattr(request.state, "request_id", None)
    
    logger.info(
        "Starting resume analysis",
        resume_length=len(analyze_request.resume_text),
        jd_length=len(analyze_request.jd_text),
        request_id=request_id,
    )
    
    try:
        # Use OpenAI for comprehensive analysis
        analysis_result = analyze_with_openai(analyze_request.resume_text, analyze_request.jd_text)
        
        total_time = time.time() - start_time
        
        logger.info(
            "OpenAI resume analysis completed",
            total_time_ms=round(total_time * 1000, 2),
            overall_score=analysis_result["score"].overall,
            evidence_count=len(analysis_result["evidence"]),
            request_id=request_id,
        )
        
        return AnalyzeResponse(
            score=analysis_result["score"],
            missing=analysis_result["missing"],
            weakly_supported=analysis_result["weakly_supported"],
            suggestions=analysis_result["suggestions"],
            ats=analysis_result["ats"],
            evidence=analysis_result["evidence"],
        )
    
    except ATSAnalyzerException:
        raise
    except Exception as e:
        logger.error(
            "OpenAI analysis failed",
            error=str(e),
            error_type=type(e).__name__,
            request_id=request_id,
        )
        raise HTTPException(
            status_code=500,
            detail=f"AI analysis failed: {str(e)}. Please check OpenAI API configuration."
        )


