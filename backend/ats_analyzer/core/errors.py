"""Custom exceptions for ATS Analyzer."""

from typing import Any, Optional


class ATSAnalyzerException(Exception):
    """Base exception for ATS Analyzer."""
    
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class FileProcessingError(ATSAnalyzerException):
    """Raised when file processing fails."""
    pass


class TextExtractionError(ATSAnalyzerException):
    """Raised when text extraction fails."""
    pass


class OCRError(ATSAnalyzerException):
    """Raised when OCR processing fails."""
    pass


class EntityExtractionError(ATSAnalyzerException):
    """Raised when entity extraction fails."""
    pass


class ScoringError(ATSAnalyzerException):
    """Raised when scoring calculation fails."""
    pass


class ConfigurationError(ATSAnalyzerException):
    """Raised when configuration is invalid."""
    pass
