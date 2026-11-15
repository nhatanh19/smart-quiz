"""Custom domain exceptions for the File Parser module."""

from typing import Optional, Sequence


class DocumentParserError(Exception):
    """Base exception for all document parsing and file upload errors."""

    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.detail = detail or message

    def __str__(self) -> str:
        return self.message


class EmptyFileError(DocumentParserError):
    """Raised when uploaded file contains 0 bytes or no extractable text content."""

    def __init__(self, message: Optional[str] = None, filename: Optional[str] = None):
        if not message:
            if filename:
                message = f"Tệp '{filename}' rỗng (0 bytes). Vui lòng chọn tệp có nội dung."
            else:
                message = "Uploaded file is empty (0 bytes)."
        super().__init__(message)
        self.filename = filename


class FileSizeLimitExceededError(DocumentParserError):
    """Raised when uploaded file exceeds the 10MB maximum size limit."""

    def __init__(
        self,
        message: Optional[str] = None,
        filename: Optional[str] = None,
        file_size: Optional[int] = None,
        max_size: int = 10 * 1024 * 1024,
    ):
        if not message:
            size_mb = f"{file_size / (1024 * 1024):.2f}MB" if file_size else "> 10MB"
            if filename:
                message = (
                    f"Dung lượng tệp '{filename}' ({size_mb}) vượt quá giới hạn tối đa cho phép (10MB)."
                )
            else:
                message = "File size exceeds maximum allowed limit of 10MB."
        super().__init__(message)
        self.filename = filename
        self.file_size = file_size
        self.max_size = max_size


class UnsupportedFileTypeError(DocumentParserError):
    """Raised when uploaded file extension is not supported (allowed: .pdf, .docx, .txt)."""

    def __init__(
        self,
        message: Optional[str] = None,
        filename: Optional[str] = None,
        extension: Optional[str] = None,
        allowed_extensions: Sequence[str] = (".pdf", ".docx", ".txt"),
    ):
        if not message:
            allowed_str = ", ".join(allowed_extensions)
            if extension:
                message = (
                    f"Định dạng tệp '{extension}' không được hỗ trợ. Chỉ chấp nhận các định dạng: {allowed_str}."
                )
            elif filename:
                message = (
                    f"Định dạng tệp '{filename}' không được hỗ trợ. Chỉ chấp nhận các định dạng: {allowed_str}."
                )
            else:
                message = f"Unsupported file format. Only {allowed_str} files are allowed."
        super().__init__(message)
        self.filename = filename
        self.extension = extension
        self.allowed_extensions = allowed_extensions


class CorruptedFileError(DocumentParserError):
    """Raised when a file cannot be parsed due to corrupt data, encryption, or encoding errors."""

    def __init__(
        self,
        message: Optional[str] = None,
        filename: Optional[str] = None,
        reason: Optional[str] = None,
    ):
        if not message:
            if filename and reason:
                message = f"Tệp '{filename}' bị hỏng hoặc không đúng định dạng: {reason}"
            elif filename:
                message = f"Tệp '{filename}' bị hỏng hoặc không đúng định dạng."
            elif reason:
                message = f"Corrupted or malformed file: {reason}"
            else:
                message = "Corrupted or malformed file."
        super().__init__(message)
        self.filename = filename
        self.reason = reason


# Aliases for cross-module compatibility
FileTooLargeError = FileSizeLimitExceededError
UnsupportedFileFormatError = UnsupportedFileTypeError

__all__ = [
    "DocumentParserError",
    "EmptyFileError",
    "FileSizeLimitExceededError",
    "FileTooLargeError",
    "UnsupportedFileTypeError",
    "UnsupportedFileFormatError",
    "CorruptedFileError",
]
