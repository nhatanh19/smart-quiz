"""Pydantic schemas for Bloom Taxonomy Prompt Templates & Matrix Generation (Issue #11 / WBS 3.2.1)."""

from typing import Any, Dict, List, Literal, Optional
import uuid

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.entities import (
    CognitiveLevel,
    QuestionLevel,
    QuestionSource,
    QuestionType,
)
from app.modules.ai_generator.prompts import (
    COGNITIVE_ORDER,
    QUESTION_TYPE_ORDER,
    allocate_counts_by_weights,
)


class CognitiveDistributionSchema(BaseModel):
    """Exact question counts across the 3 Bloom taxonomy cognitive levels."""

    REMEMBER: int = Field(default=0, ge=0)
    UNDERSTAND: int = Field(default=0, ge=0)
    APPLY: int = Field(default=0, ge=0)

    @property
    def total(self) -> int:
        return self.REMEMBER + self.UNDERSTAND + self.APPLY

    def as_enum_dict(self) -> Dict[CognitiveLevel, int]:
        return {
            CognitiveLevel.REMEMBER: self.REMEMBER,
            CognitiveLevel.UNDERSTAND: self.UNDERSTAND,
            CognitiveLevel.APPLY: self.APPLY,
        }


class QuestionTypeDistributionSchema(BaseModel):
    """Exact question counts across the 3 supported question formats."""

    SINGLE_CHOICE: int = Field(default=0, ge=0)
    MULTIPLE_CHOICE: int = Field(default=0, ge=0)
    TRUE_FALSE: int = Field(default=0, ge=0)

    @property
    def total(self) -> int:
        return self.SINGLE_CHOICE + self.MULTIPLE_CHOICE + self.TRUE_FALSE

    def as_enum_dict(self) -> Dict[QuestionType, int]:
        return {
            QuestionType.SINGLE_CHOICE: self.SINGLE_CHOICE,
            QuestionType.MULTIPLE_CHOICE: self.MULTIPLE_CHOICE,
            QuestionType.TRUE_FALSE: self.TRUE_FALSE,
        }


class MatrixCellAllocation(BaseModel):
    """Number of questions assigned to a single (cognitive_level, question_type) matrix cell."""

    cognitive_level: CognitiveLevel
    question_type: QuestionType
    count: int = Field(ge=1)


class GenerateByMatrixRequest(BaseModel):
    """Request payload for Bloom-taxonomy matrix question generation or prompt preview."""

    topic: str = Field(min_length=2, max_length=500)
    subject_name: Optional[str] = Field(default=None, max_length=255)
    category_id: Optional[uuid.UUID] = None
    total_questions: Optional[int] = Field(default=None, ge=1, le=50)
    cognitive_distribution: Optional[CognitiveDistributionSchema] = None
    cognitive_ratios: Optional[Dict[CognitiveLevel, float]] = None
    type_distribution: Optional[QuestionTypeDistributionSchema] = None
    type_ratios: Optional[Dict[QuestionType, float]] = None
    language: Literal["vi", "en"] = "vi"
    additional_instructions: Optional[str] = Field(default=None, max_length=2000)
    temperature: float = Field(default=0.35, ge=0.0, le=1.0)

    @field_validator("topic", "subject_name", "additional_instructions", mode="before")
    @classmethod
    def strip_strings(cls, value: Any) -> Any:
        return value.strip() if isinstance(value, str) else value

    @field_validator("topic")
    @classmethod
    def validate_topic_non_blank(cls, value: str) -> str:
        if len(value.strip()) < 2:
            raise ValueError("Chủ đề (topic) phải có ít nhất 2 ký tự hợp lệ")
        return value.strip()

    @model_validator(mode="after")
    def normalize_matrix_distributions(self) -> "GenerateByMatrixRequest":
        if self.cognitive_distribution is not None and self.cognitive_ratios is not None:
            raise ValueError("Chỉ cung cấp cognitive_distribution hoặc cognitive_ratios, không truyền đồng thời cả hai")
        if self.type_distribution is not None and self.type_ratios is not None:
            raise ValueError("Chỉ cung cấp type_distribution hoặc type_ratios, không truyền đồng thời cả hai")

        if self.cognitive_distribution is not None:
            cog_total = self.cognitive_distribution.total
            if cog_total < 1:
                raise ValueError("Tổng số câu hỏi trong cognitive_distribution phải lớn hơn hoặc bằng 1")
            if cog_total > 50:
                raise ValueError("Tổng số câu hỏi không được vượt quá 50")
            if self.total_questions is not None and self.total_questions != cog_total:
                raise ValueError(
                    f"Tổng cognitive_distribution ({cog_total}) không khớp với total_questions ({self.total_questions})"
                )
            self.total_questions = cog_total
        elif self.cognitive_ratios is not None:
            target_total = self.total_questions if self.total_questions is not None else 10
            allocated = allocate_counts_by_weights(
                target_total, self.cognitive_ratios, COGNITIVE_ORDER
            )
            self.total_questions = target_total
            self.cognitive_distribution = CognitiveDistributionSchema(
                **{level.value: count for level, count in allocated.items()}
            )
        else:
            target_total = self.total_questions if self.total_questions is not None else 10
            default_weights = {
                CognitiveLevel.REMEMBER: 40.0,
                CognitiveLevel.UNDERSTAND: 40.0,
                CognitiveLevel.APPLY: 20.0,
            }
            allocated = allocate_counts_by_weights(
                target_total, default_weights, COGNITIVE_ORDER
            )
            self.total_questions = target_total
            self.cognitive_distribution = CognitiveDistributionSchema(
                **{level.value: count for level, count in allocated.items()}
            )

        if self.type_distribution is not None:
            type_total = self.type_distribution.total
            if type_total != self.total_questions:
                raise ValueError(
                    f"Tổng type_distribution ({type_total}) không khớp với total_questions ({self.total_questions})"
                )
        elif self.type_ratios is not None:
            allocated_types = allocate_counts_by_weights(
                self.total_questions, self.type_ratios, QUESTION_TYPE_ORDER
            )
            self.type_distribution = QuestionTypeDistributionSchema(
                **{qtype.value: count for qtype, count in allocated_types.items()}
            )
        else:
            self.type_distribution = QuestionTypeDistributionSchema(
                SINGLE_CHOICE=self.total_questions,
                MULTIPLE_CHOICE=0,
                TRUE_FALSE=0,
            )

        return self


class LLMGeneratedOptionSchema(BaseModel):
    """Option structure expected from the LLM JSON output."""

    id: str
    text: str
    is_correct: bool


class LLMGeneratedQuestionSchema(BaseModel):
    """Single question item expected from the LLM JSON output."""

    content: str
    question_type: QuestionType
    cognitive_level: CognitiveLevel
    level: Optional[QuestionLevel] = None
    options: List[LLMGeneratedOptionSchema]
    explanation: str = ""
    tags: List[str] = Field(default_factory=list)


class LLMGeneratedBatchSchema(BaseModel):
    """Batch response schema passed to LLMClientAdapter.generate_structured_json."""

    questions: List[LLMGeneratedQuestionSchema]


class GeneratedOptionItem(BaseModel):
    """Validated option ready for preview or saving into Question Bank."""

    id: str = Field(min_length=1, max_length=32)
    text: str = Field(min_length=1)
    is_correct: bool


class GeneratedQuestionItem(BaseModel):
    """Validated question generated by the Bloom prompt pipeline."""

    category_id: Optional[uuid.UUID] = None
    content: str = Field(min_length=1)
    question_type: QuestionType
    cognitive_level: CognitiveLevel
    level: QuestionLevel
    options: List[GeneratedOptionItem]
    tags: List[str] = Field(default_factory=list)
    explanation: str = Field(min_length=1)
    source_type: QuestionSource = QuestionSource.AI_GENERATED


class PromptPlanCellSchema(BaseModel):
    """Preview of a single matrix cell's prompt pair."""

    cognitive_level: CognitiveLevel
    question_type: QuestionType
    count: int
    system_prompt: str
    user_prompt: str


class PromptPreviewResponse(BaseModel):
    """Response for previewing the Bloom matrix allocation and generated prompts."""

    topic: str
    subject_name: Optional[str] = None
    total_questions: int
    cognitive_distribution: Dict[str, int]
    type_distribution: Dict[str, int]
    allocations: List[PromptPlanCellSchema]


class BloomTemplateMetadata(BaseModel):
    """Metadata describing one Bloom taxonomy prompt template."""

    cognitive_level: CognitiveLevel
    label_vi: str
    label_en: str
    default_difficulty: QuestionLevel
    objective: str
    bloom_verbs: List[str]
    question_design_rules: str
    distractor_strategy: str


class QuestionTypeTemplateMetadata(BaseModel):
    """Metadata describing formatting rules for a supported question type."""

    question_type: QuestionType
    label_vi: str
    label_en: str
    option_count_rule: str
    correct_answer_rule: str
    format_guidelines: str


class BloomTemplatesCatalogResponse(BaseModel):
    """Catalog of all 3 Bloom prompt templates and 3 question type guidelines."""

    bloom_templates: List[BloomTemplateMetadata]
    question_type_templates: List[QuestionTypeTemplateMetadata]
    distractor_quality_rules: str


class GenerateByMatrixResponse(BaseModel):
    """Response payload for matrix-based Bloom AI question generation."""

    topic: str
    subject_name: Optional[str] = None
    total_requested: int
    total_generated: int
    cognitive_distribution: Dict[str, int]
    type_distribution: Dict[str, int]
    allocations: List[MatrixCellAllocation]
    generated_questions: List[GeneratedQuestionItem]
    quality_checks: Dict[str, Any]

