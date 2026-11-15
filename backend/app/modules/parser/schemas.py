"""Pydantic schemas for the File Parser module."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.entities import (
    CognitiveLevel,
    QuestionLevel,
    QuestionSource,
    QuestionType,
)
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

    @field_validator("raw_text")
    @classmethod
    def validate_raw_text_not_blank(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Nội dung văn bản (raw_text) không được rỗng.")
        return value

    @field_validator("filename", mode="before")
    @classmethod
    def normalize_filename(cls, value: Any) -> Optional[str]:
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value


class ParsedOptionSchema(BaseModel):
    """Normalized answer option matching questions.options JSONB contract."""

    id: str = Field(..., min_length=1, max_length=32, description="Mã phương án (A, B, C, ...)")
    text: str = Field(..., min_length=1, description="Nội dung phương án lựa chọn")
    is_correct: bool = Field(default=False, description="Đánh dấu đáp án đúng")

    model_config = ConfigDict(from_attributes=True)


class ParsedQuestionSchema(BaseModel):
    """Normalized question object extracted by Regex pattern matching (Issue #6)."""

    question_number: Optional[int] = Field(
        default=None, ge=1, description="Số thứ tự câu hỏi gốc trong tài liệu"
    )
    content: str = Field(..., min_length=1, description="Nội dung câu hỏi")
    question_type: QuestionType = Field(
        default=QuestionType.SINGLE_CHOICE,
        description="Dạng câu hỏi (SINGLE_CHOICE, MULTIPLE_CHOICE, TRUE_FALSE)",
    )
    cognitive_level: CognitiveLevel = Field(
        default=CognitiveLevel.REMEMBER,
        description="Mức độ nhận thức Bloom mặc định hoặc trích từ nhãn",
    )
    level: QuestionLevel = Field(
        default=QuestionLevel.MEDIUM,
        description="Độ khó mặc định hoặc trích từ nhãn",
    )
    options: List[ParsedOptionSchema] = Field(
        default_factory=list,
        description="Danh sách các phương án lựa chọn (A, B, C, D...)",
    )
    correct_option_ids: List[str] = Field(
        default_factory=list,
        description="Danh sách ID các phương án đúng",
    )
    explanation: Optional[str] = Field(
        default=None, description="Lời giải thích hoặc ghi chú (nếu có)"
    )
    tags: List[str] = Field(default_factory=list, description="Thẻ phân loại trích xuất (nếu có)")
    source_type: QuestionSource = Field(
        default=QuestionSource.FILE_PARSER,
        description="Nguồn gốc câu hỏi luôn là FILE_PARSER",
    )
    is_valid: bool = Field(
        default=True,
        description="True nếu câu hỏi đủ 2-10 phương án và có đáp án đúng hợp lệ",
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Cảnh báo thiếu dữ liệu để UI Issue #7 hỗ trợ chỉnh sửa trước khi lưu",
    )

    model_config = ConfigDict(from_attributes=True)


class ParseStatisticsSchema(BaseModel):
    """Summary metrics for regex question extraction."""

    total_blocks_detected: int = Field(default=0, ge=0)
    total_questions: int = Field(default=0, ge=0)
    valid_questions: int = Field(default=0, ge=0)
    questions_with_correct_answer: int = Field(default=0, ge=0)
    questions_with_explanation: int = Field(default=0, ge=0)
    warnings_count: int = Field(default=0, ge=0)


class ParsedQuestionBatchResult(BaseModel):
    """Structured result returned when parsing raw text into normalized questions."""

    filename: Optional[str] = None
    questions: List[ParsedQuestionSchema] = Field(default_factory=list)
    statistics: ParseStatisticsSchema
    unmatched_answer_keys: Dict[int, List[str]] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


class DocumentQuestionExtractionResult(BaseModel):
    """Combined raw document metadata + regex-parsed structured questions."""

    document: DocumentParseResult
    questions: List[ParsedQuestionSchema] = Field(default_factory=list)
    statistics: ParseStatisticsSchema
    unmatched_answer_keys: Dict[int, List[str]] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


# Type aliases for API responses
DocumentParseResponse = APIResponse[DocumentParseResult]
DocumentMetadataResponse = APIResponse[DocumentMetadata]
ParsedQuestionBatchResponse = APIResponse[ParsedQuestionBatchResult]
DocumentQuestionExtractionResponse = APIResponse[DocumentQuestionExtractionResult]

__all__ = [
    "DocumentMetadata",
    "DocumentParseResult",
    "DirectTextParseRequest",
    "ParsedOptionSchema",
    "ParsedQuestionSchema",
    "ParseStatisticsSchema",
    "ParsedQuestionBatchResult",
    "DocumentQuestionExtractionResult",
    "DocumentParseResponse",
    "DocumentMetadataResponse",
    "ParsedQuestionBatchResponse",
    "DocumentQuestionExtractionResponse",
    "APIResponse",
    "ErrorResponse",
    "HealthCheckResponse",
]
