"""Router for the Document Parser module (Issue #5)."""

import logging

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.schemas.common import APIResponse, HealthCheckResponse
from app.modules.parser.schemas import DocumentParseResult
from app.modules.parser.exceptions import (
    CorruptedFileError,
    DocumentParserError,
    EmptyFileError,
    FileSizeLimitExceededError,
    UnsupportedFileTypeError,
)
from app.modules.parser.services.file_parser_service import DocumentParserService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/parser",
    tags=["Module 1: File Parser (Dev 1)"],
)

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB (10,485,760 bytes)
LIMIT_READ_BYTES = MAX_FILE_SIZE_BYTES + 1  # 10,485,761 bytes
CHUNK_SIZE_BYTES = 1024 * 1024  # 1 MB stream reading chunk
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def extract_extension(filename: str) -> str:
    """Extract normalized lowercase extension with leading dot.

    Returns empty string if filename contains no dot.
    """
    if "." not in filename:
        return ""
    return "." + filename.rsplit(".", 1)[-1].lower()


@router.get("/health", response_model=HealthCheckResponse)
def parser_health_check() -> HealthCheckResponse:
    """Health check endpoint for the file parser module."""
    return HealthCheckResponse(service="File Parser Service")


@router.post(
    "/upload",
    response_model=APIResponse[DocumentParseResult],
    summary="Upload and parse document (PDF, DOCX, TXT)",
    description=(
        "Upload a .pdf, .docx, or .txt file up to 10MB to extract raw text with "
        "full UTF-8 Vietnamese preservation and word/character statistics."
    ),
)
async def upload_document(
    file: UploadFile = File(...),
) -> APIResponse[DocumentParseResult]:
    """Ingest, validate, and parse an uploaded document."""
    # 1. Filename presence validation
    if file is None or not file.filename or not file.filename.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing filename. Please upload a valid named file.",
        )

    filename = file.filename.strip()

    # 2. Case-insensitive extension validation
    extension = extract_extension(filename)
    if not extension:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format for '{filename}'. Missing file extension. Allowed extensions are: .pdf, .docx, .txt.",
        )

    if extension not in ALLOWED_EXTENSIONS:
        allowed_str = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{extension}'. Only {allowed_str} files are allowed.",
        )

    # 3. Pre-read size check if provided by client/ASGI metadata
    if getattr(file, "size", None) is not None:
        if file.size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty (0 bytes).",
            )
        if file.size > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size exceeds maximum allowed limit of 10MB.",
            )

    # 4. Memory-safe bounded stream reading
    buffer = bytearray()
    while len(buffer) <= MAX_FILE_SIZE_BYTES:
        bytes_to_read = min(CHUNK_SIZE_BYTES, LIMIT_READ_BYTES - len(buffer))
        chunk = await file.read(bytes_to_read)
        if not chunk:
            break
        buffer.extend(chunk)

    # 5. Empty check
    if len(buffer) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes).",
        )

    # 6. Size threshold check
    if len(buffer) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds maximum allowed limit of 10MB.",
        )

    content = bytes(buffer)

    # 7. Document parsing and domain exception translation
    try:
        result = DocumentParserService.parse_file(filename=filename, content=content)
    except (
        EmptyFileError,
        FileSizeLimitExceededError,
        UnsupportedFileTypeError,
        CorruptedFileError,
        DocumentParserError,
        ValueError,
    ) as err:
        logger.warning("Parser domain error processing '%s': %s", filename, err)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err
    except HTTPException:
        raise
    except Exception as err:
        logger.exception("Unexpected error processing uploaded file '%s': %s", filename, err)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to process uploaded file: {str(err)}",
        ) from err

    return APIResponse(
        success=True,
        message="File parsed successfully",
        data=result,
    )
