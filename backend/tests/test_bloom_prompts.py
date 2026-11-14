"""Tests for Bloom Taxonomy Prompt Templates & Multi-Type Question Generation (Issue #11 / WBS 3.2.1)."""

from types import SimpleNamespace
from unittest.mock import AsyncMock
import uuid

import httpx
import pytest
from fastapi.testclient import TestClient
from openai import RateLimitError
from pydantic import ValidationError

from app.core.database import get_db
from app.core.security import get_current_user
from app.main import app
from app.models.entities import (
    CognitiveLevel,
    QuestionLevel,
    QuestionSource,
    QuestionType,
    User,
    UserRole,
)
from app.modules.ai_generator.prompts import (
    BLOOM_PROMPT_TEMPLATES,
    QUESTION_TYPE_TEMPLATES,
    allocate_counts_by_weights,
    build_cell_prompts,
    plan_matrix_cells,
)
from app.modules.ai_generator.schemas import (
    CognitiveDistributionSchema,
    GenerateByMatrixRequest,
    LLMGeneratedBatchSchema,
    LLMGeneratedOptionSchema,
    LLMGeneratedQuestionSchema,
    QuestionTypeDistributionSchema,
)
from app.modules.ai_generator.service import (
    AIQuestionGeneratorService,
    LLMUnavailableError,
    QuestionGenerationError,
)
from app.modules.ai_generator.validators import (
    QuestionValidationError,
    validate_and_normalize_question,
)
from app.schemas.common import QuestionCreateSchema

client = TestClient(app)


def _make_option(opt_id: str, text: str, is_correct: bool = False) -> LLMGeneratedOptionSchema:
    return LLMGeneratedOptionSchema(id=opt_id, text=text, is_correct=is_correct)


def _valid_single_choice(
    stem: str = "Trong Scrum, vai trò nào chịu trách nhiệm tối đa hóa giá trị sản phẩm?",
    cognitive_level: CognitiveLevel = CognitiveLevel.REMEMBER,
) -> LLMGeneratedQuestionSchema:
    return LLMGeneratedQuestionSchema(
        content=stem,
        question_type=QuestionType.SINGLE_CHOICE,
        cognitive_level=cognitive_level,
        level=QuestionLevel.EASY,
        options=[
            _make_option("A", "Product Owner", True),
            _make_option("B", "Scrum Master", False),
            _make_option("C", "Project Sponsor", False),
            _make_option("D", "Release Manager", False),
        ],
        explanation="Product Owner quản lý Product Backlog và tối đa hóa giá trị sản phẩm.",
        tags=["Scrum", "Vai trò"],
    )


def _valid_multiple_choice(
    stem: str = "Những phát biểu nào đúng về nguyên tắc tạo WBS?",
    cognitive_level: CognitiveLevel = CognitiveLevel.UNDERSTAND,
) -> LLMGeneratedQuestionSchema:
    return LLMGeneratedQuestionSchema(
        content=stem,
        question_type=QuestionType.MULTIPLE_CHOICE,
        cognitive_level=cognitive_level,
        level=QuestionLevel.MEDIUM,
        options=[
            _make_option("A", "Tuân theo quy tắc 100% phạm vi công việc", True),
            _make_option("B", "Định hướng theo sản phẩm bàn giao (deliverables)", True),
            _make_option("C", "Sắp xếp trực tiếp thời gian bắt đầu từng tác vụ", False),
            _make_option("D", "Chỉ bao gồm các hoạt động kiểm thử cuối dự án", False),
        ],
        explanation="WBS tuân theo quy tắc 100% và hướng deliverable; lịch biểu lập sau WBS.",
        tags=["WBS", "Scope"],
    )


def _valid_true_false(
    stem: str = "Trong kiểm thử hộp đen, người kiểm thử cần đọc chi tiết mã nguồn bên trong hàm.",
    cognitive_level: CognitiveLevel = CognitiveLevel.APPLY,
) -> LLMGeneratedQuestionSchema:
    return LLMGeneratedQuestionSchema(
        content=stem,
        question_type=QuestionType.TRUE_FALSE,
        cognitive_level=cognitive_level,
        level=QuestionLevel.HARD,
        options=[
            _make_option("A", "Đúng", False),
            _make_option("B", "Sai", True),
        ],
        explanation="Kiểm thử hộp đen chỉ đánh giá hành vi dựa trên đầu vào/đầu ra, không đọc mã nguồn.",
        tags=["Testing", "Black-box"],
    )


def test_bloom_and_question_type_templates_cover_all_required_specs():
    assert set(BLOOM_PROMPT_TEMPLATES.keys()) == {
        CognitiveLevel.REMEMBER,
        CognitiveLevel.UNDERSTAND,
        CognitiveLevel.APPLY,
    }
    assert set(QUESTION_TYPE_TEMPLATES.keys()) == {
        QuestionType.SINGLE_CHOICE,
        QuestionType.MULTIPLE_CHOICE,
        QuestionType.TRUE_FALSE,
    }

    sys_rem, usr_rem = build_cell_prompts(
        "Quản trị rủi ro", CognitiveLevel.REMEMBER, QuestionType.SINGLE_CHOICE, 3
    )
    sys_und, _ = build_cell_prompts(
        "Quản trị rủi ro", CognitiveLevel.UNDERSTAND, QuestionType.MULTIPLE_CHOICE, 2
    )
    sys_app, _ = build_cell_prompts(
        "Quản trị rủi ro", CognitiveLevel.APPLY, QuestionType.TRUE_FALSE, 2, language="en"
    )

    assert "NHẬN BIẾT" in sys_rem and "SINGLE_CHOICE" in sys_rem
    assert "ĐÚNG 3 câu" in usr_rem
    assert "THÔNG HIỂU" in sys_und and "TỐI THIỂU 2 phương án có is_correct=true" in sys_und
    assert "VẬN DỤNG" in sys_app and 'A: "True", B: "False"' in sys_app


def test_allocate_counts_by_weights_and_matrix_cells_preserve_exact_totals():
    ratios = {
        CognitiveLevel.REMEMBER: 40.0,
        CognitiveLevel.UNDERSTAND: 40.0,
        CognitiveLevel.APPLY: 20.0,
    }
    counts = allocate_counts_by_weights(
        7, ratios, [CognitiveLevel.REMEMBER, CognitiveLevel.UNDERSTAND, CognitiveLevel.APPLY]
    )
    assert sum(counts.values()) == 7
    assert counts[CognitiveLevel.APPLY] >= 1

    cog_dist = {
        CognitiveLevel.REMEMBER: 4,
        CognitiveLevel.UNDERSTAND: 4,
        CognitiveLevel.APPLY: 2,
    }
    type_dist = {
        QuestionType.SINGLE_CHOICE: 6,
        QuestionType.MULTIPLE_CHOICE: 2,
        QuestionType.TRUE_FALSE: 2,
    }
    cells = plan_matrix_cells(cog_dist, type_dist)

    assert sum(c for _, _, c in cells) == 10
    for level in CognitiveLevel:
        assert sum(c for cog, _, c in cells if cog == level) == cog_dist[level]
    for qtype in QuestionType:
        assert sum(c for _, qt, c in cells if qt == qtype) == type_dist[qtype]


def test_request_schema_supports_ratios_and_rejects_mismatched_totals():
    req = GenerateByMatrixRequest(
        topic="Kiểm thử phần mềm",
        total_questions=10,
        cognitive_ratios={"REMEMBER": 50, "UNDERSTAND": 30, "APPLY": 20},
        type_ratios={"SINGLE_CHOICE": 60, "MULTIPLE_CHOICE": 20, "TRUE_FALSE": 20},
    )
    assert req.cognitive_distribution.REMEMBER == 5
    assert req.cognitive_distribution.UNDERSTAND == 3
    assert req.cognitive_distribution.APPLY == 2
    assert req.type_distribution.SINGLE_CHOICE == 6
    assert req.type_distribution.MULTIPLE_CHOICE == 2
    assert req.type_distribution.TRUE_FALSE == 2

    with pytest.raises(ValidationError):
        GenerateByMatrixRequest(
            topic="Kiểm thử phần mềm",
            total_questions=10,
            cognitive_distribution=CognitiveDistributionSchema(REMEMBER=3, UNDERSTAND=3, APPLY=2),
        )

    with pytest.raises(ValidationError):
        GenerateByMatrixRequest(
            topic="Kiểm thử phần mềm",
            cognitive_distribution=CognitiveDistributionSchema(REMEMBER=2, UNDERSTAND=2, APPLY=1),
            type_distribution=QuestionTypeDistributionSchema(SINGLE_CHOICE=4),
        )


def test_validator_rejects_duplicate_and_lazy_distractors_and_bad_correct_counts():
    # Duplicate options differing only by prefix/case/punctuation
    dup_q = _valid_single_choice()
    dup_q.options[2] = _make_option("C", "B. scrum master!", False)
    with pytest.raises(QuestionValidationError, match="trùng lặp nội dung"):
        validate_and_normalize_question(
            dup_q,
            expected_cognitive_level=CognitiveLevel.REMEMBER,
            expected_question_type=QuestionType.SINGLE_CHOICE,
        )

    # Banned lazy distractor
    lazy_q = _valid_single_choice()
    lazy_q.options[3] = _make_option("D", "Tất cả các đáp án trên", False)
    with pytest.raises(QuestionValidationError, match="bị cấm"):
        validate_and_normalize_question(
            lazy_q,
            expected_cognitive_level=CognitiveLevel.REMEMBER,
            expected_question_type=QuestionType.SINGLE_CHOICE,
        )

    # Multiple choice with only 1 correct answer is rejected
    bad_mc = _valid_multiple_choice()
    bad_mc.options[1].is_correct = False
    with pytest.raises(QuestionValidationError, match="từ 2 đến"):
        validate_and_normalize_question(
            bad_mc,
            expected_cognitive_level=CognitiveLevel.UNDERSTAND,
            expected_question_type=QuestionType.MULTIPLE_CHOICE,
        )

    # True/False with 3 options is rejected
    bad_tf = _valid_true_false()
    bad_tf.options.append(_make_option("C", "Không xác định", False))
    with pytest.raises(QuestionValidationError, match="chính xác 2 phương án"):
        validate_and_normalize_question(
            bad_tf,
            expected_cognitive_level=CognitiveLevel.APPLY,
            expected_question_type=QuestionType.TRUE_FALSE,
        )

    # True/False with non-boolean option labels is rejected
    weird_tf = _valid_true_false()
    weird_tf.options = [_make_option("A", "Có thể", True), _make_option("B", "Chưa chắc", False)]
    with pytest.raises(QuestionValidationError, match="Đúng/Sai"):
        validate_and_normalize_question(
            weird_tf,
            expected_cognitive_level=CognitiveLevel.APPLY,
            expected_question_type=QuestionType.TRUE_FALSE,
        )

    # Duplicate question stem across cells is rejected
    with pytest.raises(QuestionValidationError, match="câu hỏi bị trùng lặp"):
        validate_and_normalize_question(
            _valid_single_choice("Trong Scrum, vai trò nào chịu trách nhiệm tối đa hóa giá trị sản phẩm?"),
            expected_cognitive_level=CognitiveLevel.REMEMBER,
            expected_question_type=QuestionType.SINGLE_CHOICE,
            existing_normalized_stems={"trong scrum vai trò nào chịu trách nhiệm tối đa hóa giá trị sản phẩm"},
        )

    # Valid question strips accidental option prefix and maps cleanly to QuestionCreateSchema
    prefixed_q = _valid_single_choice()
    prefixed_q.options[0].text = "A. Product Owner"
    validated = validate_and_normalize_question(
        prefixed_q,
        expected_cognitive_level=CognitiveLevel.REMEMBER,
        expected_question_type=QuestionType.SINGLE_CHOICE,
        category_id=uuid.uuid4(),
    )
    assert validated.options[0].text == "Product Owner"
    assert validated.source_type == QuestionSource.AI_GENERATED
    bank_payload = QuestionCreateSchema.model_validate(
        validated.model_dump(exclude={"source_type"})
    )
    assert bank_payload.cognitive_level == CognitiveLevel.REMEMBER


@pytest.mark.parametrize(
    ("cognitive_level", "expected_level"),
    [
        (CognitiveLevel.REMEMBER, QuestionLevel.EASY),
        (CognitiveLevel.UNDERSTAND, QuestionLevel.MEDIUM),
        (CognitiveLevel.APPLY, QuestionLevel.HARD),
    ],
)
def test_validator_uses_default_difficulty_when_llm_omits_level(
    cognitive_level: CognitiveLevel,
    expected_level: QuestionLevel,
):
    question = _valid_single_choice(cognitive_level=cognitive_level)
    question.level = None

    validated = validate_and_normalize_question(
        question,
        expected_cognitive_level=cognitive_level,
        expected_question_type=QuestionType.SINGLE_CHOICE,
    )

    assert validated.level == expected_level


@pytest.mark.parametrize(
    ("cognitive_level", "incorrect_level"),
    [
        (CognitiveLevel.REMEMBER, QuestionLevel.MEDIUM),
        (CognitiveLevel.UNDERSTAND, QuestionLevel.HARD),
        (CognitiveLevel.APPLY, QuestionLevel.EASY),
    ],
)
def test_validator_rejects_difficulty_that_does_not_match_bloom_level(
    cognitive_level: CognitiveLevel,
    incorrect_level: QuestionLevel,
):
    question = _valid_single_choice(cognitive_level=cognitive_level)
    question.level = incorrect_level

    with pytest.raises(QuestionValidationError, match="Độ khó không khớp"):
        validate_and_normalize_question(
            question,
            expected_cognitive_level=cognitive_level,
            expected_question_type=QuestionType.SINGLE_CHOICE,
        )


@pytest.mark.anyio
async def test_service_repairs_invalid_batch_and_meets_exact_matrix_counts(monkeypatch):
    service = AIQuestionGeneratorService()
    request = GenerateByMatrixRequest(
        topic="Quản trị Dự án Phần mềm",
        cognitive_distribution=CognitiveDistributionSchema(REMEMBER=1, UNDERSTAND=1, APPLY=1),
        type_distribution=QuestionTypeDistributionSchema(
            SINGLE_CHOICE=1, MULTIPLE_CHOICE=1, TRUE_FALSE=1
        ),
    )

    # First call (REMEMBER / SINGLE_CHOICE) intentionally returns an invalid duplicate-option question,
    # triggering one targeted repair call before proceeding to UNDERSTAND and APPLY.
    bad_single = _valid_single_choice("Câu hỏi 1: Scrum Master có nhiệm vụ gì chính?")
    bad_single.options[1] = _make_option("B", "Product Owner", False)  # duplicates A

    good_single = _valid_single_choice("Câu hỏi 1: Scrum Master có nhiệm vụ gì chính?")
    good_multi = _valid_multiple_choice("Câu hỏi 2: Những yếu tố nào thuộc tam giác ràng buộc dự án?")
    good_tf = _valid_true_false("Câu hỏi 3: Trong tình huống phạm vi tăng gấp đôi, giữ nguyên thời gian và chi phí mà chất lượng không đổi là khả thi.")

    mock_generate = AsyncMock(
        side_effect=[
            LLMGeneratedBatchSchema(questions=[bad_single]),
            LLMGeneratedBatchSchema(questions=[good_single]),
            LLMGeneratedBatchSchema(questions=[good_multi]),
            LLMGeneratedBatchSchema(questions=[good_tf]),
        ]
    )
    monkeypatch.setattr("app.modules.ai_generator.service.llm_client.generate_structured_json", mock_generate)

    result = await service.generate_by_matrix(request)

    assert result.total_requested == 3
    assert result.total_generated == 3
    assert result.cognitive_distribution == {"REMEMBER": 1, "UNDERSTAND": 1, "APPLY": 1}
    assert result.type_distribution == {
        "SINGLE_CHOICE": 1,
        "MULTIPLE_CHOICE": 1,
        "TRUE_FALSE": 1,
    }
    assert result.quality_checks["rejected_invalid_candidates"] == 1
    assert result.quality_checks["repair_calls"] == 1
    assert mock_generate.await_count == 4
    # Repair prompt includes failure reason
    assert "trùng lặp nội dung" in mock_generate.await_args_list[1].kwargs["user_prompt"]


@pytest.mark.anyio
async def test_service_raises_when_repair_attempts_exhausted(monkeypatch):
    service = AIQuestionGeneratorService()
    request = GenerateByMatrixRequest(
        topic="Cấu trúc dữ liệu",
        total_questions=1,
        cognitive_distribution=CognitiveDistributionSchema(REMEMBER=1),
        type_distribution=QuestionTypeDistributionSchema(SINGLE_CHOICE=1),
    )

    bad_q = _valid_single_choice()
    bad_q.options[3] = _make_option("D", "All of the above", False)

    mock_generate = AsyncMock(return_value=LLMGeneratedBatchSchema(questions=[bad_q]))
    monkeypatch.setattr("app.modules.ai_generator.service.llm_client.generate_structured_json", mock_generate)

    with pytest.raises(QuestionGenerationError, match="Không thể tạo đủ 1 câu hỏi hợp lệ"):
        await service.generate_by_matrix(request)
    assert mock_generate.await_count == 3


@pytest.mark.anyio
async def test_service_maps_rate_limit_to_unavailable_error(monkeypatch):
    service = AIQuestionGeneratorService()
    request = GenerateByMatrixRequest(
        topic="Cấu trúc dữ liệu",
        total_questions=1,
        cognitive_distribution=CognitiveDistributionSchema(REMEMBER=1),
        type_distribution=QuestionTypeDistributionSchema(SINGLE_CHOICE=1),
    )
    http_req = httpx.Request("POST", "https://example.test")
    rate_err = RateLimitError("Busy", response=httpx.Response(429, request=http_req), body=None)
    monkeypatch.setattr(
        "app.modules.ai_generator.service.llm_client.generate_structured_json",
        AsyncMock(side_effect=rate_err),
    )

    with pytest.raises(LLMUnavailableError):
        await service.generate_by_matrix(request)


def test_bloom_api_endpoints_and_rbac(monkeypatch):
    instructor = User(
        id=uuid.uuid4(),
        email="inst@example.com",
        full_name="Giảng Viên",
        password_hash="x",
        role=UserRole.INSTRUCTOR,
        is_active=True,
    )
    student = User(
        id=uuid.uuid4(),
        email="stud@example.com",
        full_name="Sinh Viên",
        password_hash="x",
        role=UserRole.STUDENT,
        is_active=True,
    )

    # Unauthenticated blocked
    assert client.get("/api/v1/ai-generator/bloom-templates").status_code == 401

    with monkeypatch.context() as ctx:
        ctx.setitem(app.dependency_overrides, get_db, lambda: None)

        # Student forbidden
        ctx.setitem(app.dependency_overrides, get_current_user, lambda: student)
        assert client.get("/api/v1/ai-generator/bloom-templates").status_code == 403

        # Instructor allowed
        ctx.setitem(app.dependency_overrides, get_current_user, lambda: instructor)
        catalog_res = client.get("/api/v1/ai-generator/bloom-templates")
        assert catalog_res.status_code == 200
        catalog = catalog_res.json()["data"]
        assert len(catalog["bloom_templates"]) == 3
        assert len(catalog["question_type_templates"]) == 3

        preview_res = client.post(
            "/api/v1/ai-generator/bloom-templates/preview",
            json={
                "topic": "Mạng máy tính",
                "total_questions": 5,
                "cognitive_ratios": {"REMEMBER": 40, "UNDERSTAND": 40, "APPLY": 20},
                "type_ratios": {"SINGLE_CHOICE": 60, "MULTIPLE_CHOICE": 20, "TRUE_FALSE": 20},
            },
        )
        assert preview_res.status_code == 200
        preview_data = preview_res.json()["data"]
        assert preview_data["total_questions"] == 5
        assert sum(preview_data["cognitive_distribution"].values()) == 5
        assert sum(preview_data["type_distribution"].values()) == 5
        assert len(preview_data["allocations"]) >= 1

        # Empty body still succeeds for RBAC smoke check compatibility
        smoke_res = client.post("/api/v1/ai-generator/generate-by-matrix")
        assert smoke_res.status_code == 200
        assert smoke_res.json()["data"]["generated_questions"] == []

        # Full matrix generation request succeeds with mocked LLM
        fake_response = {
            ("REMEMBER", "SINGLE_CHOICE"): [_valid_single_choice("Câu 1: Giao thức TCP hoạt động ở tầng nào?")],
            ("UNDERSTAND", "MULTIPLE_CHOICE"): [_valid_multiple_choice("Câu 2: Đặc điểm nào đúng về TCP?")],
        }

        async def fake_llm(system_prompt, user_prompt, response_schema, temperature=0.2):
            if "REMEMBER" in user_prompt:
                return LLMGeneratedBatchSchema(questions=fake_response[("REMEMBER", "SINGLE_CHOICE")])
            return LLMGeneratedBatchSchema(questions=fake_response[("UNDERSTAND", "MULTIPLE_CHOICE")])

        monkeypatch.setattr(
            "app.modules.ai_generator.service.llm_client.generate_structured_json",
            fake_llm,
        )

        gen_res = client.post(
            "/api/v1/ai-generator/generate-by-matrix",
            json={
                "topic": "Mạng máy tính",
                "cognitive_distribution": {"REMEMBER": 1, "UNDERSTAND": 1, "APPLY": 0},
                "type_distribution": {"SINGLE_CHOICE": 1, "MULTIPLE_CHOICE": 1, "TRUE_FALSE": 0},
            },
        )
        assert gen_res.status_code == 200
        gen_data = gen_res.json()["data"]
        assert gen_data["total_generated"] == 2
        assert gen_data["cognitive_distribution"] == {"REMEMBER": 1, "UNDERSTAND": 1, "APPLY": 0}
        assert gen_data["type_distribution"] == {
            "SINGLE_CHOICE": 1,
            "MULTIPLE_CHOICE": 1,
            "TRUE_FALSE": 0,
        }
