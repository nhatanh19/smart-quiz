from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, AwareDatetime, field_validator, model_validator


class ExamQuestionInput(BaseModel):
    question_id: UUID
    points: float = Field(default=1, gt=0, allow_inf_nan=False)


class ExamInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    duration_minutes: int = Field(gt=0)
    start_time: AwareDatetime
    end_time: AwareDatetime
    pin: str | None = Field(default=None, max_length=72)
    max_attempts: int = Field(default=1, ge=1)
    shuffle_questions: bool = True
    shuffle_options: bool = True
    is_published: bool = False
    questions: list[ExamQuestionInput] = Field(min_length=1, max_length=500)

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value):
        if not value.strip():
            raise ValueError("Vui lòng nhập tên ca thi.")
        return value.strip()

    @field_validator("pin")
    @classmethod
    def pin_bytes(cls, value):
        if value is not None and len(value.encode("utf-8")) > 72:
            raise ValueError("PIN tối đa 72 byte UTF-8.")
        return value or None

    @model_validator(mode="after")
    def validate_exam(self):
        if self.end_time <= self.start_time:
            raise ValueError("Giờ đóng phải sau giờ mở.")
        if len({q.question_id for q in self.questions}) != len(self.questions):
            raise ValueError("Không được chọn trùng câu hỏi.")
        return self


class JoinInput(BaseModel):
    exam_code: str = Field(min_length=1, max_length=12)
    pin: str = Field(default="", max_length=72)


class AnswerInput(BaseModel):
    question_id: UUID
    selected_options: list[str] = Field(max_length=10)


class SubmitInput(BaseModel):
    answers: list[AnswerInput] = Field(max_length=500)
