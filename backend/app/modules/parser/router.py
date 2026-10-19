from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.common import APIResponse, HealthCheckResponse

router = APIRouter(prefix="/parser", tags=["Module 1: File Parser & Question Bank (Dev 1)"])


@router.get("/health", response_model=HealthCheckResponse)
def parser_health_check():
    """Health check endpoint for File Parser & Question Bank module."""
    return HealthCheckResponse(service="File Parser & Question Bank Service")


# ==============================================================================
# PLACEHOLDER ENDPOINTS FOR DEV 1
# ==============================================================================


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


@router.get("/questions", response_model=APIResponse[list])
def list_questions_placeholder(db: Session = Depends(get_db)):
    """List questions placeholder.

    // TODO: Dev 1 - Implement Question Bank CRUD listing with filtering by
    // category, cognitive_level, and search query.
    """
    return APIResponse(
        success=True,
        message="// TODO: Dev 1 - Implement Question Bank listing logic",
        data=[],
    )


@router.post("/questions", response_model=APIResponse[dict])
def create_question_placeholder(db: Session = Depends(get_db)):
    """Create manual question placeholder.

    // TODO: Dev 1 - Implement manual question creation into Question Bank.
    """
    return APIResponse(
        success=True,
        message="// TODO: Dev 1 - Implement manual Question Bank creation",
        data={"question_id": 0},
    )
