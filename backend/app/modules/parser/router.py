"""Router for the Document Parser module (Issue #5 & Issue #6)."""

import logging
from typing import Tuple

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.core.security import require_roles
from app.models.entities import UserRole
from app.modules.auth.router import check_origin
from app.modules.parser.exceptions import (
    CorruptedFileError,
    DocumentParserError,
    EmptyFileError,
    FileSizeLimitExceededError,
    UnsupportedFileTypeError,
)
from app.modules.parser.schemas import (
    DirectTextParseRequest,
    DocumentParseResult,
    DocumentQuestionExtractionResult,
    ParsedQuestionBatchResult,
)
from app.modules.parser.services.file_parser_service import DocumentParserService
from app.modules.parser.services.regex_question_parser import RegexQuestionParserService
from app.schemas.common import APIResponse, HealthCheckResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/parser",
    tags=["Module 1: File Parser (Dev 1)"],
)

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB (10,485,760 bytes)
LIMIT_READ_BYTES = MAX_FILE_SIZE_BYTES + 1  # 10,485,761 bytes
CHUNK_SIZE_BYTES = 1024 * 1024  # 1 MB stream reading chunk
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
PARSER_ALLOWED_ROLES = [UserRole.INSTRUCTOR, UserRole.ADMIN]


def extract_extension(filename: str) -> str:
    """Extract normalized lowercase extension with leading dot.

    Returns empty string if filename contains no dot.
    """
    if "." not in filename:
        return ""
    return "." + filename.rsplit(".", 1)[-1].lower()


async def _read_validated_upload(file: UploadFile) -> Tuple[str, bytes]:
    """Validate uploaded filename/extension/size and read bounded stream bytes."""
    if file is None or not file.filename or not file.filename.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing filename. Please upload a valid named file.",
        )

    filename = file.filename.strip()
    extension = extract_extension(filename)
    if not extension:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported file format for '{filename}'. Missing file extension. "
                "Allowed extensions are: .pdf, .docx, .txt."
            ),
        )

    if extension not in ALLOWED_EXTENSIONS:
        allowed_str = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{extension}'. Only {allowed_str} files are allowed.",
        )

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

    buffer = bytearray()
    while len(buffer) <= MAX_FILE_SIZE_BYTES:
        bytes_to_read = min(CHUNK_SIZE_BYTES, LIMIT_READ_BYTES - len(buffer))
        chunk = await file.read(bytes_to_read)
        if not chunk:
            break
        buffer.extend(chunk)

    if len(buffer) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes).",
        )

    if len(buffer) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds maximum allowed limit of 10MB.",
        )

    return filename, bytes(buffer)


def _translate_parser_error(filename: str, err: Exception) -> HTTPException:
    """Translate FileParserService domain errors into HTTP 400 Bad Request."""
    logger.warning("Parser domain error processing '%s': %s", filename, err)
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(err),
    )


@router.get("/health", response_model=HealthCheckResponse)
def parser_health_check() -> HealthCheckResponse:
    """Health check endpoint for the file parser module."""
    return HealthCheckResponse(service="File Parser Service")


@router.post(
    "/upload",
    response_model=APIResponse[DocumentParseResult],
    dependencies=[
        Depends(require_roles(PARSER_ALLOWED_ROLES)),
        Depends(check_origin),
    ],
    summary="Upload and parse document (PDF, DOCX, TXT)",
    description=(
        "Upload a .pdf, .docx, or .txt file up to 10MB to extract raw text with "
        "full UTF-8 Vietnamese preservation and word/character statistics. "
        "Restricted to INSTRUCTOR and ADMIN roles."
    ),
)
async def upload_document(
    file: UploadFile = File(...),
) -> APIResponse[DocumentParseResult]:
    """Ingest, validate, and parse an uploaded document into raw UTF-8 text."""
    filename, content = await _read_validated_upload(file)
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
        raise _translate_parser_error(filename, err) from err
    except HTTPException:
        raise
    except Exception as err:
        logger.exception("Unexpected error processing uploaded file '%s': %s", filename, err)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error while processing uploaded file.",
        ) from err

    return APIResponse(
        success=True,
        message="File parsed successfully",
        data=result,
    )


@router.post(
    "/parse-questions",
    response_model=APIResponse[ParsedQuestionBatchResult],
    dependencies=[
        Depends(require_roles(PARSER_ALLOWED_ROLES)),
        Depends(check_origin),
    ],
    summary="Parse raw text into normalized quiz questions using Regex",
    description=(
        "Apply structured Regex matching to raw UTF-8 document text to extract "
        "questions, options (A-J), correct answers, and explanations. "
        "Restricted to INSTRUCTOR and ADMIN roles."
    ),
)
def parse_questions_from_text(
    payload: DirectTextParseRequest,
) -> APIResponse[ParsedQuestionBatchResult]:
    """Parse extracted raw text into normalized question schemas."""
    parsed = RegexQuestionParserService.parse(
        payload.raw_text,
        filename=payload.filename,
    )
    return APIResponse(
        success=True,
        message=f"Đã nhận diện {parsed.statistics.total_questions} câu hỏi từ văn bản.",
        data=parsed,
    )


@router.post(
    "/upload-and-parse",
    response_model=APIResponse[DocumentQuestionExtractionResult],
    dependencies=[
        Depends(require_roles(PARSER_ALLOWED_ROLES)),
        Depends(check_origin),
    ],
    summary="Upload document and extract structured quiz questions (PDF, DOCX, TXT)",
    description=(
        "Upload a .pdf, .docx, or .txt file up to 10MB, extract UTF-8 raw text "
        "(including DOCX underline/highlight answer cues), and apply Regex matching "
        "to return normalized question objects. Restricted to INSTRUCTOR and ADMIN roles."
    ),
)
async def upload_and_parse_questions(
    file: UploadFile = File(...),
) -> APIResponse[DocumentQuestionExtractionResult]:
    """Upload a document, extract text (with DOCX formatting hints), and parse questions."""
    filename, content = await _read_validated_upload(file)
    try:
        doc_result, line_marked_spans = DocumentParserService.parse_file_with_hints(
            filename=filename,
            content=content,
        )
    except (
        EmptyFileError,
        FileSizeLimitExceededError,
        UnsupportedFileTypeError,
        CorruptedFileError,
        DocumentParserError,
        ValueError,
    ) as err:
        raise _translate_parser_error(filename, err) from err
    except HTTPException:
        raise
    except Exception as err:
        logger.exception("Unexpected error parsing uploaded file '%s': %s", filename, err)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error while processing uploaded file.",
        ) from err

    parsed = RegexQuestionParserService.parse(
        doc_result.raw_text,
        filename=doc_result.filename,
        line_marked_spans=line_marked_spans,
    )
    combined = DocumentQuestionExtractionResult(
        document=doc_result,
        questions=parsed.questions,
        statistics=parsed.statistics,
        unmatched_answer_keys=parsed.unmatched_answer_keys,
        warnings=parsed.warnings,
    )
    return APIResponse(
        success=True,
        message=f"Đã bóc tách văn bản và nhận diện {parsed.statistics.total_questions} câu hỏi.",
        data=combined,
    )
