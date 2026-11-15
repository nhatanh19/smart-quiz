"""Pydantic schemas for the File Parser module."""

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.common import APIResponse, ErrorResponse, HealthCheckResponse


class DocumentMetadata(BaseModel):
    """Metadata summary for an uploaded document."""

    filename: str = Field(..., description="Tên tệp gốc được tải lên")
    file_type: str = Field(..., description="Định dạng tệp mở rộng (pdf, docx, txt)")
    file_size: int = Field(..., ge=0, description="Dung lượng tệp tính theo bytes")
    character_count: int = Field(..., ge=0, description="Tổng số ký tự văn bản thô trích xuất")
    word_count: int = Field(..., ge=0, description="Tổng số từ văn bản thô trích xuất")
    page_count: Optional[int] = Field(
        default=None, ge=1, description="Số trang đối với tài liệu PDF (None với TXT, DOCX)"
    )

    model_config = ConfigDict(from_attributes=True)


class DocumentParseResult(DocumentMetadata):
    """Full extraction result containing metadata and extracted raw text."""

    raw_text: str = Field(
        ...,
        description="Toàn bộ nội dung văn bản thô đã trích xuất, bảo toàn 100% tiếng Việt UTF-8",
    )


class DirectTextParseRequest(BaseModel):
    """Request payload for direct raw text ingestion / parsing without file upload."""

    raw_text: str = Field(..., min_length=1, description="Nội dung văn bản thô")
    filename: Optional[str] = Field(default="direct_input.txt", description="Tên định danh tài liệu")


# Type aliases for API responses
DocumentParseResponse = APIResponse[DocumentParseResult]
DocumentMetadataResponse = APIResponse[DocumentMetadata]

__all__ = [
    "DocumentMetadata",
    "DocumentParseResult",
    "DirectTextParseRequest",
    "DocumentParseResponse",
    "DocumentMetadataResponse",
    "APIResponse",
    "ErrorResponse",
    "HealthCheckResponse",
]
