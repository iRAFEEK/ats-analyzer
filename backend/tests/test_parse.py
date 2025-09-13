"""Tests for document parsing service."""

import io
from unittest.mock import patch, MagicMock

import pytest
from PIL import Image

from ats_analyzer.services.parse import (
    detect_filetype,
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_from_image,
    parse_document,
)
from ats_analyzer.core.errors import FileProcessingError, TextExtractionError


class TestFiletypeDetection:
    """Test file type detection."""

    def test_detect_pdf_by_magic_bytes(self):
        content = b'%PDF-1.4\n...'
        filetype = detect_filetype(content, 'test.pdf', 'application/pdf')
        assert filetype == 'pdf'

    def test_detect_docx_by_magic_bytes(self):
        content = b'PK\x03\x04...'
        filetype = detect_filetype(content, 'test.docx', None)
        assert filetype == 'docx'

    def test_detect_image_by_magic_bytes(self):
        content = b'\x89PNG\r\n\x1a\n...'
        filetype = detect_filetype(content, 'test.png', None)
        assert filetype == 'image'

    def test_detect_by_filename_extension(self):
        content = b'some content'
        filetype = detect_filetype(content, 'test.pdf', None)
        assert filetype == 'pdf'

    def test_detect_by_content_type(self):
        content = b'some content'
        filetype = detect_filetype(content, 'test', 'application/pdf')
        assert filetype == 'pdf'

    def test_unsupported_filetype_raises_error(self):
        content = b'some content'
        with pytest.raises(FileProcessingError):
            detect_filetype(content, 'test.txt', 'text/plain')


class TestPDFExtraction:
    """Test PDF text extraction."""

    @patch('ats_analyzer.services.parse.fitz')
    def test_extract_text_from_pdf_success(self, mock_fitz):
        # Mock PyMuPDF
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Sample PDF text content"
        mock_page.get_text.return_value = "Sample PDF text content"
        mock_doc.__len__.return_value = 1
        mock_doc.__getitem__.return_value = mock_page
        mock_fitz.open.return_value = mock_doc

        content = b'%PDF-1.4\nSample PDF'
        text, ocr_used, score = extract_text_from_pdf(content)

        assert "Sample PDF text content" in text
        assert not ocr_used
        assert score > 0

    @patch('ats_analyzer.services.parse.fitz')
    def test_pdf_extraction_failure_raises_error(self, mock_fitz):
        mock_fitz.open.side_effect = Exception("PDF parsing failed")
        
        content = b'%PDF-1.4\nSample PDF'
        with pytest.raises(TextExtractionError):
            extract_text_from_pdf(content)


class TestDOCXExtraction:
    """Test DOCX text extraction."""

    @patch('ats_analyzer.services.parse.Document')
    def test_extract_text_from_docx_success(self, mock_document_class):
        # Mock python-docx
        mock_doc = MagicMock()
        mock_paragraph = MagicMock()
        mock_paragraph.text = "Sample DOCX paragraph"
        mock_doc.paragraphs = [mock_paragraph]
        mock_doc.tables = []
        mock_document_class.return_value = mock_doc

        content = b'PK\x03\x04...'
        text, ocr_used, score = extract_text_from_docx(content)

        assert "Sample DOCX paragraph" in text
        assert not ocr_used
        assert score == 1.0

    @patch('ats_analyzer.services.parse.Document')
    def test_docx_extraction_failure_raises_error(self, mock_document_class):
        mock_document_class.side_effect = Exception("DOCX parsing failed")
        
        content = b'PK\x03\x04...'
        with pytest.raises(TextExtractionError):
            extract_text_from_docx(content)


class TestImageExtraction:
    """Test image text extraction with OCR."""

    @patch('ats_analyzer.services.parse.pytesseract')
    @patch('ats_analyzer.services.parse.Image')
    def test_extract_text_from_image_success(self, mock_image_class, mock_tesseract):
        # Mock PIL and Tesseract
        mock_image = MagicMock()
        mock_image_class.open.return_value = mock_image
        mock_tesseract.image_to_string.return_value = "Sample OCR text content"

        content = b'\x89PNG\r\n\x1a\n...'
        text, ocr_used, score = extract_text_from_image(content)

        assert "Sample OCR text content" in text
        assert ocr_used
        assert score > 0

    @patch('ats_analyzer.services.parse.pytesseract')
    @patch('ats_analyzer.services.parse.Image')
    def test_image_extraction_empty_text_raises_error(self, mock_image_class, mock_tesseract):
        mock_image = MagicMock()
        mock_image_class.open.return_value = mock_image
        mock_tesseract.image_to_string.return_value = ""

        content = b'\x89PNG\r\n\x1a\n...'
        with pytest.raises(Exception):  # Should raise OCRError
            extract_text_from_image(content)


class TestParseDocument:
    """Test main document parsing function."""

    @patch('ats_analyzer.services.parse.extract_text_from_pdf')
    @patch('ats_analyzer.services.parse.detect_filetype')
    async def test_parse_document_pdf_success(self, mock_detect, mock_extract):
        mock_detect.return_value = 'pdf'
        mock_extract.return_value = ("Sample text", False, 0.9)

        content = b'%PDF-1.4\nSample'
        result = await parse_document(content, "test.pdf")

        assert result.text == "Sample text"
        assert result.meta.filetype == 'pdf'
        assert not result.meta.ocr_used
        assert result.meta.extractability_score == 0.9

    async def test_parse_document_empty_content_raises_error(self):
        with pytest.raises(FileProcessingError):
            await parse_document(b'', "test.pdf")

    @patch('ats_analyzer.services.parse.extract_text_from_pdf')
    @patch('ats_analyzer.services.parse.detect_filetype')
    async def test_parse_document_no_text_raises_error(self, mock_detect, mock_extract):
        mock_detect.return_value = 'pdf'
        mock_extract.return_value = ("", False, 0.0)

        content = b'%PDF-1.4\nSample'
        with pytest.raises(TextExtractionError):
            await parse_document(content, "test.pdf")
