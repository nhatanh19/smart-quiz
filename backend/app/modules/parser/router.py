from fastapi import APIRouter, File, UploadFile

from app.schemas.common import APIResponse, HealthCheckResponse

router = APIRouter(
    prefix="/parser",
    tags=["Module 1: File Parser (Dev 1)"],
)


@router.get("/health", response_model=HealthCheckResponse)
def parser_health_check():
    """Health check endpoint for the file parser module."""
    return HealthCheckResponse(service="File Parser Service")


@router.post("/upload", response_model=APIResponse[dict])
async def upload_document_placeholder(file: UploadFile = File(None)):
    """Upload document placeholder.

    // TODO: Dev 1 - Implement file upload stream handling, extract raw text
    // using PyMuPDF (fitz) for PDF, python-docx for DOCX, or direct read for TXT.
    // Parse questions, choices, and answers using regular expressions.
    """
    return APIResponse(
        success=True,
        message="// TODO: Dev 1 - Implement document parsing (PDF/DOCX/TXT) logic",
        data={"filename": file.filename if file else "sample.pdf", "parsed_count": 0},
    )
