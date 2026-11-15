"""File Parser Service & Extractor Strategies for Smart Quiz Document Ingestion.

This module provides raw text extraction from PDF, DOCX, and TXT files while
strictly preserving Vietnamese UTF-8 accents and diacritics. It implements the
Strategy Pattern to encapsulate format-specific extraction engines and raises
domain exceptions mapped to HTTP 400 Bad Request responses.
"""

from __future__ import annotations

import io
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, Dict, Optional, Type
from zipfile import BadZipFile

from docx.opc.exceptions import PackageNotFoundError
import docx
import pymupdf

from app.modules.parser.exceptions import (
    CorruptedFileError,
    EmptyFileError,
    FileSizeLimitExceededError,
    UnsupportedFileTypeError,
)
from app.modules.parser.schemas import DocumentParseResult


@dataclass
class ExtractedContent:
    """Internal container for raw extraction results."""

    text: str
    page_count: Optional[int] = None


class BaseExtractor(ABC):
    """Abstract base class for document format text extractors."""

    @abstractmethod
    def extract(self, content: bytes, filename: str) -> ExtractedContent:
        """Extract raw text from file byte stream.

        Args:
            content: Raw document bytes.
            filename: Original uploaded filename for error reporting.

        Returns:
            ExtractedContent with raw text and optional page count.

        Raises:
            CorruptedFileError: If file is malformed, damaged, or encrypted.
            EmptyFileError: If file has no extractable text content.
        """
        raise NotImplementedError


class PdfExtractor(BaseExtractor):
    """PyMuPDF-backed text extractor for PDF documents."""

    def extract(self, content: bytes, filename: str) -> ExtractedContent:
        try:
            doc = pymupdf.open(stream=content, filetype="pdf")
        except Exception as err:
            raise CorruptedFileError(
                f"Tệp PDF '{filename}' bị hỏng hoặc không đúng định dạng: {err}",
                filename=filename,
                reason=str(err),
            ) from err

        try:
            # Check for encryption and password protection
            if doc.is_encrypted or getattr(doc, "needs_pass", 0) != 0:
                raise CorruptedFileError(
                    f"Tệp PDF '{filename}' được bảo vệ bằng mật khẩu hoặc đã bị mã hóa.",
                    filename=filename,
                    reason="Document is encrypted or password-protected",
                )

            page_count = len(doc)
            if page_count == 0:
                raise EmptyFileError(
                    f"Tệp PDF '{filename}' không có trang nội dung.",
                    filename=filename,
                )

            pages_text: list[str] = []
            for idx, page in enumerate(doc):
                try:
                    p_text = page.get_text()
                    if p_text and p_text.strip():
                        pages_text.append(p_text.strip())
                except Exception as err:
                    raise CorruptedFileError(
                        f"Lỗi khi đọc trang {idx + 1} của tệp PDF '{filename}': {err}",
                        filename=filename,
                        reason=str(err),
                    ) from err

            raw_text = "\n\n".join(pages_text).replace("\r\n", "\n").replace("\r", "\n").strip()
            if not raw_text:
                raise EmptyFileError(
                    f"Tệp PDF '{filename}' không chứa nội dung văn bản có thể trích xuất.",
                    filename=filename,
                )

            return ExtractedContent(text=raw_text, page_count=page_count)
        finally:
            doc.close()


class DocxExtractor(BaseExtractor):
    """python-docx-backed text extractor for Word (.docx) documents."""

    def extract(self, content: bytes, filename: str) -> ExtractedContent:
        try:
            doc = docx.Document(io.BytesIO(content))
        except (BadZipFile, PackageNotFoundError, KeyError) as err:
            raise CorruptedFileError(
                f"Tệp DOCX '{filename}' bị hỏng hoặc không phải tệp Word hợp lệ: {err}",
                filename=filename,
                reason=str(err),
            ) from err
        except Exception as err:
            raise CorruptedFileError(
                f"Không thể mở tệp DOCX '{filename}': {err}",
                filename=filename,
                reason=str(err),
            ) from err

        text_blocks: list[str] = []

        # 1. Extract text from document paragraphs
        for paragraph in doc.paragraphs:
            p_text = paragraph.text.strip()
            if p_text:
                text_blocks.append(p_text)

        # 2. Extract text from document tables (deduplicating merged cells)
        for table in doc.tables:
            for row in table.rows:
                seen_cells: set[int] = set()
                row_texts: list[str] = []
                for cell in row.cells:
                    cell_id = id(cell._tc)
                    if cell_id not in seen_cells:
                        seen_cells.add(cell_id)
                        c_text = cell.text.strip()
                        if c_text:
                            row_texts.append(c_text)
                if row_texts:
                    text_blocks.append(" | ".join(row_texts))

        raw_text = "\n".join(text_blocks).replace("\r\n", "\n").replace("\r", "\n").strip()
        if not raw_text:
            raise EmptyFileError(
                f"Tệp DOCX '{filename}' không chứa nội dung văn bản.",
                filename=filename,
            )

        return ExtractedContent(text=raw_text, page_count=None)


class TxtExtractor(BaseExtractor):
    """Plain text extractor supporting UTF-8 and UTF-8-SIG (BOM) encodings."""

    def extract(self, content: bytes, filename: str) -> ExtractedContent:
        try:
            try:
                raw_text = content.decode("utf-8")
                if raw_text.startswith("\ufeff"):
                    raw_text = raw_text.lstrip("\ufeff")
            except UnicodeDecodeError:
                raw_text = content.decode("utf-8-sig")
        except UnicodeDecodeError as err:
            raise CorruptedFileError(
                f"Tệp văn bản '{filename}' không phải định dạng UTF-8 hợp lệ: {err}",
                filename=filename,
                reason=f"UnicodeDecodeError: {err}",
            ) from err

        # Reject binary files disguised as .txt
        if "\x00" in raw_text:
            raise CorruptedFileError(
                f"Tệp văn bản '{filename}' chứa ký tự nhị phân không hợp lệ (null bytes).",
                filename=filename,
                reason="Binary null byte encountered in text stream",
            )

        raw_text = raw_text.replace("\r\n", "\n").replace("\r", "\n").strip()
        if not raw_text:
            raise EmptyFileError(
                f"Tệp văn bản '{filename}' rỗng hoặc chỉ chứa khoảng trắng.",
                filename=filename,
            )

        return ExtractedContent(text=raw_text, page_count=None)


class FileParserService:
    """Orchestration service for document ingestion and text extraction."""

    MAX_FILE_SIZE: ClassVar[int] = 10 * 1024 * 1024  # 10 MB = 10,485,760 bytes
    ALLOWED_EXTENSIONS: ClassVar[set[str]] = {".pdf", ".docx", ".txt"}

    _EXTRACTORS: ClassVar[Dict[str, Type[BaseExtractor]]] = {
        ".pdf": PdfExtractor,
        ".docx": DocxExtractor,
        ".txt": TxtExtractor,
    }

    @classmethod
    def get_extractor(cls, extension: str) -> BaseExtractor:
        """Resolve extractor strategy by lowercase file extension."""
        ext = extension.lower()
        extractor_cls = cls._EXTRACTORS.get(ext)
        if not extractor_cls:
            allowed = ", ".join(sorted(cls.ALLOWED_EXTENSIONS))
            raise UnsupportedFileTypeError(
                filename=None,
                extension=ext,
                message=f"Định dạng tệp '{ext}' không được hỗ trợ. Chỉ chấp nhận các định dạng: {allowed}.",
            )
        return extractor_cls()

    @classmethod
    def parse_file(cls, filename: str, content: bytes) -> DocumentParseResult:
        """Parse raw file bytes and extract structured document text and metadata.

        Args:
            filename: Name of the uploaded file.
            content: Raw binary content of the file.

        Returns:
            DocumentParseResult containing metadata, statistics, and UTF-8 raw text.

        Raises:
            EmptyFileError: If file is 0 bytes or extracted text is empty.
            FileSizeLimitExceededError: If file exceeds 10MB limit.
            UnsupportedFileTypeError: If file extension is not .pdf, .docx, or .txt.
            CorruptedFileError: If file content is damaged, encrypted, or invalid.
        """
        # 1. Empty check (0 bytes)
        if not content or len(content) == 0:
            raise EmptyFileError(
                filename=filename,
                message=f"Tệp '{filename}' rỗng (0 bytes). Vui lòng chọn tệp có nội dung.",
            )

        # 2. File size limit check (10MB)
        if len(content) > cls.MAX_FILE_SIZE:
            raise FileSizeLimitExceededError(
                filename=filename,
                file_size=len(content),
                max_size=cls.MAX_FILE_SIZE,
            )

        # 3. File extension validation
        extension = Path(filename).suffix.lower()
        if not extension:
            allowed = ", ".join(sorted(cls.ALLOWED_EXTENSIONS))
            raise UnsupportedFileTypeError(
                filename=filename,
                extension="",
                message=f"Tệp '{filename}' không có phần mở rộng hợp lệ. Chỉ chấp nhận: {allowed}.",
            )

        extractor = cls.get_extractor(extension)

        # 4. Strategy execution
        extracted = extractor.extract(content, filename)
        clean_text = extracted.text.strip()

        # 5. Empty content post-extraction check
        if not clean_text:
            raise EmptyFileError(
                filename=filename,
                message=f"Tệp '{filename}' không chứa nội dung văn bản có thể trích xuất.",
            )

        # 6. Statistical metrics computation
        character_count = len(clean_text)
        word_count = len(clean_text.split())

        # 7. Construct DocumentParseResult
        return DocumentParseResult(
            filename=filename,
            file_type=extension.lstrip("."),
            file_size=len(content),
            character_count=character_count,
            word_count=word_count,
            page_count=extracted.page_count,
            raw_text=clean_text,
        )


# Backward-compatible alias
DocumentParserService = FileParserService

__all__ = [
    "BaseExtractor",
    "ExtractedContent",
    "PdfExtractor",
    "DocxExtractor",
    "TxtExtractor",
    "FileParserService",
    "DocumentParserService",
]
