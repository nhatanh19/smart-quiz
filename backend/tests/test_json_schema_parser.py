"""Tests for Issue #10: Strict JSON Schema Definition & Response Parser (WBS 3.1.2).

Verifies Acceptance Criteria:
1. AI output is parsed into structured question items matching:
   [{ question, options, correctAnswer, difficulty, explanation }]
2. Server/App never crashes when AI returns arbitrary free-text or malformed JSON;
   instead it validates strictly, strips markdown fences, triggers targeted repairs,
   or returns friendly HTTP 502/503 errors.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock
import json
import pytest
from pydantic import ValidationError

from app.models.entities import CognitiveLevel, QuestionLevel, QuestionType
from app.core.llm_client import (
    LLMClientAdapter,
    LLMResponseError,
)
from app.modules.ai_generator.schemas import (
    CognitiveDistributionSchema,
    GenerateByMatrixRequest,
    GeneratedQuestionItem,
    LLMGeneratedBatchSchema,
    LLMGeneratedOptionSchema,
    LLMGeneratedQuestionSchema,
    QuestionTypeDistributionSchema,
)
from app.modules.ai_generator.service import (
    AIQuestionGeneratorService,
    QuestionGenerationError,
)
from app.modules.ai_generator.validators import (
    QuestionValidationError,
    validate_and_normalize_question,
)


# ==============================================================================
# 1. ACCEPTANCE CRITERIA 1: PARSING & STRUCTURED MAPPING
# ==============================================================================


def test_schema_parses_standard_llm_json_format():
    raw_json = json.dumps({
        "questions": [
            {
                "content": "Trong Scrum, buổi họp nào diễn ra hàng ngày?",
                "question_type": "SINGLE_CHOICE",
                "cognitive_level": "REMEMBER",
                "level": "EASY",
                "options": [
                    {"id": "A", "text": "Daily Scrum", "is_correct": True},
                    {"id": "B", "text": "Sprint Planning", "is_correct": False},
                    {"id": "C", "text": "Sprint Review", "is_correct": False},
                    {"id": "D", "text": "Sprint Retrospective", "is_correct": False},
                ],
                "explanation": "Daily Scrum là cuộc họp 15 phút mỗi ngày cho Developers.",
                "tags": ["Scrum", "Agile"],
            }
        ]
    })

    batch = LLMGeneratedBatchSchema.model_validate_json(raw_json)
    assert len(batch.questions) == 1
    q = batch.questions[0]
    assert q.content == "Trong Scrum, buổi họp nào diễn ra hàng ngày?"
    assert q.question == q.content
    assert q.difficulty == "EASY"
    assert q.correctAnswer == "A"


def test_schema_supports_issue_10_field_aliases_and_string_options():
    """Verifies that if the LLM emits Issue #10 fields (question, options as strings,
    correctAnswer, difficulty), it parses seamlessly without schema rejection.
    """
    raw_json = json.dumps({
        "questions": [
            {
                "question": "Thủ đô của Việt Nam là thành phố nào?",
                "difficulty": "EASY",
                "cognitive_level": "REMEMBER",
                "question_type": "SINGLE_CHOICE",
                "options": ["Hà Nội", "Hồ Chí Minh", "Đà Nẵng", "Cần Thơ"],
                "correctAnswer": "A",
                "explanation": "Hà Nội là thủ đô của nước CHXHCN Việt Nam.",
            }
        ]
    })

    batch = LLMGeneratedBatchSchema.model_validate_json(raw_json)
    assert len(batch.questions) == 1
    q = batch.questions[0]
    assert q.content == "Thủ đô của Việt Nam là thành phố nào?"
    assert q.level == QuestionLevel.EASY
    assert len(q.options) == 4
    assert q.options[0].id == "A"
    assert q.options[0].text == "Hà Nội"
    assert q.options[0].is_correct is True
    assert q.options[1].is_correct is False
    assert q.correctAnswer == "A"


def test_generated_question_item_exports_exact_issue_10_dictionary_shape():
    """AC 1: [{ question, options, correctAnswer, difficulty, explanation }]."""
    raw_question = LLMGeneratedQuestionSchema(
        content="Giao thức HTTP hoạt động ở tầng nào của mô hình OSI?",
        question_type=QuestionType.SINGLE_CHOICE,
        cognitive_level=CognitiveLevel.REMEMBER,
        level=QuestionLevel.EASY,
        options=[
            LLMGeneratedOptionSchema(id="A", text="Application", is_correct=True),
            LLMGeneratedOptionSchema(id="B", text="Transport", is_correct=False),
            LLMGeneratedOptionSchema(id="C", text="Network", is_correct=False),
            LLMGeneratedOptionSchema(id="D", text="Data Link", is_correct=False),
        ],
        explanation="HTTP là giao thức thuộc tầng Ứng dụng (Application Layer).",
    )

    validated: GeneratedQuestionItem = validate_and_normalize_question(
        raw_question,
        expected_cognitive_level=CognitiveLevel.REMEMBER,
        expected_question_type=QuestionType.SINGLE_CHOICE,
    )

    # Check property aliases
    assert validated.question == "Giao thức HTTP hoạt động ở tầng nào của mô hình OSI?"
    assert validated.difficulty == "EASY"
    assert validated.correctAnswer == "A"

    # Check exact Issue #10 dictionary output format
    item_dict = validated.to_issue10_dict()
    assert item_dict == {
        "question": "Giao thức HTTP hoạt động ở tầng nào của mô hình OSI?",
        "options": ["Application", "Transport", "Network", "Data Link"],
        "correctAnswer": "A",
        "difficulty": "EASY",
        "explanation": "HTTP là giao thức thuộc tầng Ứng dụng (Application Layer).",
    }


def test_batch_schema_auto_wraps_top_level_list_and_data_keys():
    """Handles LLMs that return a raw JSON list [...] or {'data': [...]} instead of {'questions': [...]}."""
    list_json = json.dumps([
        {
            "content": "Ngôn ngữ nào chạy được trên trình duyệt mà không cần plugin?",
            "question_type": "SINGLE_CHOICE",
            "cognitive_level": "REMEMBER",
            "level": "EASY",
            "options": [
                {"id": "A", "text": "JavaScript", "is_correct": True},
                {"id": "B", "text": "C++", "is_correct": False},
                {"id": "C", "text": "Python", "is_correct": False},
                {"id": "D", "text": "Ruby", "is_correct": False},
            ],
            "explanation": "JavaScript được hỗ trợ gốc trên tất cả các trình duyệt hiện đại.",
        }
    ])
    batch_from_list = LLMGeneratedBatchSchema.model_validate_json(list_json)
    assert len(batch_from_list.questions) == 1

    data_wrapped_json = json.dumps({
        "data": [
            {
                "content": "Ngôn ngữ nào chạy được trên trình duyệt mà không cần plugin?",
                "question_type": "SINGLE_CHOICE",
                "cognitive_level": "REMEMBER",
                "level": "EASY",
                "options": [
                    {"id": "A", "text": "JavaScript", "is_correct": True},
                    {"id": "B", "text": "C++", "is_correct": False},
                    {"id": "C", "text": "Python", "is_correct": False},
                    {"id": "D", "text": "Ruby", "is_correct": False},
                ],
                "explanation": "JavaScript được hỗ trợ gốc.",
            }
        ]
    })
    batch_from_data = LLMGeneratedBatchSchema.model_validate_json(data_wrapped_json)
    assert len(batch_from_data.questions) == 1


# ==============================================================================
# 2. ACCEPTANCE CRITERIA 2: NO CRASH ON FREE-TEXT, MALFORMED JSON, OR BAD DATA
# ==============================================================================


@pytest.mark.anyio
async def test_llm_client_strips_markdown_code_fences_and_parses_json():
    """AI returning ```json ... ``` is stripped and validated without crashing."""
    adapter = LLMClientAdapter(api_key="test-key")
    fake_content = "```json\n" + json.dumps({
        "questions": [
            {
                "content": "Đâu là một phương pháp Agile phổ biến?",
                "question_type": "SINGLE_CHOICE",
                "cognitive_level": "REMEMBER",
                "level": "EASY",
                "options": [
                    {"id": "A", "text": "Scrum", "is_correct": True},
                    {"id": "B", "text": "Waterfall", "is_correct": False},
                    {"id": "C", "text": "V-Model", "is_correct": False},
                    {"id": "D", "text": "Spiral", "is_correct": False},
                ],
                "explanation": "Scrum là phương pháp phát triển lặp gia tăng trong Agile.",
            }
        ]
    }) + "\n```"

    mock_chat = AsyncMock(
        return_value=SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=fake_content))]
        )
    )
    adapter._get_client().chat.completions.create = mock_chat

    result = await adapter.generate_structured_json(
        "system", "user", LLMGeneratedBatchSchema
    )
    assert isinstance(result, LLMGeneratedBatchSchema)
    assert len(result.questions) == 1
    assert result.questions[0].content == "Đâu là một phương pháp Agile phổ biến?"


@pytest.mark.anyio
async def test_llm_client_rejects_free_text_and_malformed_json_with_validation_error():
    """AI returning conversational free-text or truncated JSON raises ValidationError rather than crashing."""
    adapter = LLMClientAdapter(api_key="test-key")

    # Case 1: Pure conversational free text
    mock_free_text = AsyncMock(
        return_value=SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content="Xin chào! Dưới đây là 5 câu hỏi trắc nghiệm bạn vừa yêu cầu:\n1. Scrum là gì?"
                    )
                )
            ]
        )
    )
    adapter._get_client().chat.completions.create = mock_free_text
    with pytest.raises(ValidationError):
        await adapter.generate_structured_json("system", "user", LLMGeneratedBatchSchema)

    # Case 2: Malformed truncated JSON
    mock_truncated = AsyncMock(
        return_value=SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content='{"questions": [{"content": "Câu hỏi bị đứt quãng...'
                    )
                )
            ]
        )
    )
    adapter._get_client().chat.completions.create = mock_truncated
    with pytest.raises(ValidationError):
        await adapter.generate_structured_json("system", "user", LLMGeneratedBatchSchema)


@pytest.mark.anyio
async def test_llm_client_raises_response_error_on_empty_or_whitespace():
    """Empty AI response raises LLMResponseError instead of crashing."""
    adapter = LLMClientAdapter(api_key="test-key")

    mock_empty = AsyncMock(
        return_value=SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="   "))]
        )
    )
    adapter._get_client().chat.completions.create = mock_empty
    with pytest.raises(LLMResponseError):
        await adapter.generate_structured_json("system", "user", LLMGeneratedBatchSchema)


@pytest.mark.anyio
async def test_service_recovers_from_free_text_via_repair_loop(monkeypatch):
    """When the LLM outputs free-text on attempt 1, the service catches ValidationError,
    feeds repair instructions back to the prompt, and succeeds on attempt 2 without crashing.
    """
    service = AIQuestionGeneratorService()
    request = GenerateByMatrixRequest(
        topic="Kiểm thử phần mềm",
        total_questions=1,
        cognitive_distribution=CognitiveDistributionSchema(REMEMBER=1),
        type_distribution=QuestionTypeDistributionSchema(SINGLE_CHOICE=1),
    )

    valid_question = LLMGeneratedQuestionSchema(
        content="Kiểm thử đơn vị (Unit Test) tập trung kiểm tra thành phần nào?",
        question_type=QuestionType.SINGLE_CHOICE,
        cognitive_level=CognitiveLevel.REMEMBER,
        level=QuestionLevel.EASY,
        options=[
            LLMGeneratedOptionSchema(id="A", text="Hàm hoặc phương thức đơn lẻ", is_correct=True),
            LLMGeneratedOptionSchema(id="B", text="Toàn bộ hệ thống hoàn chỉnh", is_correct=False),
            LLMGeneratedOptionSchema(id="C", text="Giao diện người dùng", is_correct=False),
            LLMGeneratedOptionSchema(id="D", text="Hiệu năng chịu tải mạng", is_correct=False),
        ],
        explanation="Unit Test kiểm tra đơn vị mã nguồn nhỏ nhất (hàm, phương thức).",
    )

    # Attempt 1 raises ValidationError (simulating raw free-text), Attempt 2 succeeds
    mock_llm = AsyncMock(
        side_effect=[
            ValidationError.from_exception_data(
                title="JSONDecodeError", line_errors=[]
            ),
            LLMGeneratedBatchSchema(questions=[valid_question]),
        ]
    )
    monkeypatch.setattr(
        "app.modules.ai_generator.service.llm_client.generate_structured_json",
        mock_llm,
    )

    result = await service.generate_by_matrix(request)

    assert result.total_generated == 1
    assert result.quality_checks["repair_calls"] == 1
    assert mock_llm.await_count == 2
    # Verify the repair prompt warned the LLM about JSON schema compliance
    repair_prompt = mock_llm.await_args_list[1].kwargs["user_prompt"]
    assert "schema bắt buộc" in repair_prompt


@pytest.mark.anyio
async def test_service_recovers_from_empty_response_via_repair_loop(monkeypatch):
    """When the LLM returns empty content, service catches LLMResponseError and retries cleanly."""
    service = AIQuestionGeneratorService()
    request = GenerateByMatrixRequest(
        topic="An toàn thông tin",
        total_questions=1,
        cognitive_distribution=CognitiveDistributionSchema(REMEMBER=1),
        type_distribution=QuestionTypeDistributionSchema(SINGLE_CHOICE=1),
    )

    valid_question = LLMGeneratedQuestionSchema(
        content="Mã hóa bất đối xứng sử dụng bao nhiêu khóa?",
        question_type=QuestionType.SINGLE_CHOICE,
        cognitive_level=CognitiveLevel.REMEMBER,
        level=QuestionLevel.EASY,
        options=[
            LLMGeneratedOptionSchema(id="A", text="Cặp 2 khóa (Public và Private)", is_correct=True),
            LLMGeneratedOptionSchema(id="B", text="Duy nhất 1 khóa bí mật", is_correct=False),
            LLMGeneratedOptionSchema(id="C", text="Không cần khóa nào", is_correct=False),
            LLMGeneratedOptionSchema(id="D", text="3 khóa ngẫu nhiên", is_correct=False),
        ],
        explanation="Mã hóa bất đối xứng (Asymmetric) dùng cặp khóa công khai và bí mật.",
    )

    # Attempt 1 raises LLMResponseError, Attempt 2 succeeds
    mock_llm = AsyncMock(
        side_effect=[
            LLMResponseError("The AI service returned an empty response."),
            LLMGeneratedBatchSchema(questions=[valid_question]),
        ]
    )
    monkeypatch.setattr(
        "app.modules.ai_generator.service.llm_client.generate_structured_json",
        mock_llm,
    )

    result = await service.generate_by_matrix(request)

    assert result.total_generated == 1
    assert result.quality_checks["repair_calls"] == 1
    assert mock_llm.await_count == 2
    repair_prompt = mock_llm.await_args_list[1].kwargs["user_prompt"]
    assert "phản hồi rỗng" in repair_prompt


@pytest.mark.anyio
async def test_service_gracefully_fails_without_crashing_when_all_retries_fail(monkeypatch):
    """If the LLM continuously returns free-text for all 3 attempts, the service raises
    QuestionGenerationError (which converts to HTTP 502) without unhandled exceptions or crashes.
    """
    service = AIQuestionGeneratorService()
    request = GenerateByMatrixRequest(
        topic="Hệ điều hành",
        total_questions=1,
        cognitive_distribution=CognitiveDistributionSchema(REMEMBER=1),
        type_distribution=QuestionTypeDistributionSchema(SINGLE_CHOICE=1),
    )

    mock_llm = AsyncMock(
        side_effect=[
            ValidationError.from_exception_data(title="JSONDecodeError", line_errors=[]),
            ValidationError.from_exception_data(title="JSONDecodeError", line_errors=[]),
            ValidationError.from_exception_data(title="JSONDecodeError", line_errors=[]),
        ]
    )
    monkeypatch.setattr(
        "app.modules.ai_generator.service.llm_client.generate_structured_json",
        mock_llm,
    )

    with pytest.raises(QuestionGenerationError, match="Không thể tạo đủ 1 câu hỏi hợp lệ"):
        await service.generate_by_matrix(request)

    assert mock_llm.await_count == 3

