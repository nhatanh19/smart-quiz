"""Tests for Document Text Chunking & Context-Based Question Generation (Issue #33 / WBS 3.3.1 & 3.3.2)."""

from unittest.mock import AsyncMock
import uuid

import httpx
import pytest
from fastapi.testclient import TestClient
from openai import RateLimitError

from app.core.database import get_db
from app.core.security import get_current_user
from app.main import app
from app.models.entities import (
    CognitiveLevel,
    QuestionLevel,
    QuestionType,
    User,
    UserRole,
)
from app.modules.ai_generator.schemas import (
    CognitiveDistributionSchema,
    GenerateFromContextRequest,
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

client = TestClient(app)


def _make_option(opt_id: str, text: str, is_correct: bool = False) -> LLMGeneratedOptionSchema:
    return LLMGeneratedOptionSchema(id=opt_id, text=text, is_correct=is_correct)


def _valid_single_choice(
    stem: str = "Theo tài liệu, giao thức TCP hoạt động ở tầng nào trong mô hình OSI?",
    cognitive_level: CognitiveLevel = CognitiveLevel.REMEMBER,
) -> LLMGeneratedQuestionSchema:
    return LLMGeneratedQuestionSchema(
        content=stem,
        question_type=QuestionType.SINGLE_CHOICE,
        cognitive_level=cognitive_level,
        level=QuestionLevel.EASY,
        options=[
            _make_option("A", "Tầng Giao vận (Transport Layer)", True),
            _make_option("B", "Tầng Mạng (Network Layer)", False),
            _make_option("C", "Tầng Ứng dụng (Application Layer)", False),
            _make_option("D", "Tầng Liên kết dữ liệu (Data Link Layer)", False),
        ],
        explanation="Tài liệu chỉ rõ TCP là giao thức hướng kết nối thuộc tầng Giao vận (Transport).",
        tags=["TCP", "Mạng máy tính"],
    )


def _valid_true_false(
    stem: str = "Theo bài giảng, UDP cung cấp cơ chế đảm bảo truyền dữ liệu tin cậy không mất gói.",
    cognitive_level: CognitiveLevel = CognitiveLevel.UNDERSTAND,
) -> LLMGeneratedQuestionSchema:
    return LLMGeneratedQuestionSchema(
        content=stem,
        question_type=QuestionType.TRUE_FALSE,
        cognitive_level=cognitive_level,
        level=QuestionLevel.MEDIUM,
        options=[
            _make_option("A", "Đúng", False),
            _make_option("B", "Sai", True),
        ],
        explanation="UDP là giao thức phi kết nối (connectionless), không bảo đảm tin cậy hay kiểm soát luồng.",
        tags=["UDP", "Giao thức"],
    )


@pytest.fixture
def instructor_user():
    return User(
        id=uuid.uuid4(),
        email="instructor_context@example.com",
        full_name="Giảng Viên Hướng Dẫn",
        password_hash="secret",
        role=UserRole.INSTRUCTOR,
        is_active=True,
    )


@pytest.fixture
def student_user():
    return User(
        id=uuid.uuid4(),
        email="student_context@example.com",
        full_name="Học Viên",
        password_hash="secret",
        role=UserRole.STUDENT,
        is_active=True,
    )


SAMPLE_LECTURE_TEXT = """
CHƯƠNG 4: TẦNG GIAO VẬN VÀ CÁC GIAO THỨC CỐT LÕI
Tầng Giao vận (Transport Layer) nằm giữa tầng ứng dụng và tầng mạng trong kiến trúc Internet.
Nhiệm vụ trọng tâm của tầng giao vận là cung cấp dịch vụ truyền thông logic (logical communication)
giữa các tiến trình ứng dụng (application processes) chạy trên các host khác nhau.

1. Giao thức TCP (Transmission Control Protocol):
TCP là giao thức hướng kết nối (connection-oriented), cung cấp kênh truyền tin cậy (reliable data transfer).
Trước khi truyền dữ liệu, TCP thiết lập kết nối thông qua cơ chế bắt tay 3 bước (three-way handshake).
TCP tích hợp các cơ chế kiểm soát lỗi (error detection & recovery), kiểm soát luồng (flow control)
bằng kỹ thuật cửa sổ trượt (sliding window), và kiểm soát tắc nghẽn (congestion control).

2. Giao thức UDP (User Datagram Protocol):
Khác với TCP, UDP là giao thức phi kết nối (connectionless), phi tin cậy (best-effort delivery).
UDP không thiết lập kết nối trước khi gửi dữ liệu và không đảm bảo dữ liệu tới đích theo đúng thứ tự.
Ưu điểm lớn nhất của UDP là độ trễ cực thấp và chi phí overhead nhỏ (tiêu đề gói chỉ 8 bytes so với 20 bytes của TCP).
UDP rất thích hợp cho các ứng dụng đa phương tiện thời gian thực như VoIP, Video Streaming, hoặc DNS query.
"""


def test_generate_from_context_rbac_and_smoke(monkeypatch, instructor_user, student_user):
    # 1. Unauthenticated -> 401
    res = client.post("/api/v1/ai-generator/generate-from-context")
    assert res.status_code == 401

    with monkeypatch.context() as ctx:
        ctx.setitem(app.dependency_overrides, get_db, lambda: None)

        # 2. Student -> 403
        ctx.setitem(app.dependency_overrides, get_current_user, lambda: student_user)
        res = client.post("/api/v1/ai-generator/generate-from-context")
        assert res.status_code == 403

        # 3. Instructor with empty body -> 200 smoke check
        ctx.setitem(app.dependency_overrides, get_current_user, lambda: instructor_user)
        res = client.post("/api/v1/ai-generator/generate-from-context")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["data"]["generated_questions"] == []


def test_generate_from_context_validations(monkeypatch, instructor_user):
    with monkeypatch.context() as ctx:
        ctx.setitem(app.dependency_overrides, get_db, lambda: None)
        ctx.setitem(app.dependency_overrides, get_current_user, lambda: instructor_user)

        # Text too short (< 20 characters)
        res = client.post(
            "/api/v1/ai-generator/generate-from-context",
            json={"raw_text": "Quá ngắn"},
        )
        assert res.status_code == 422

        # Overlap >= chunk_size
        res = client.post(
            "/api/v1/ai-generator/generate-from-context",
            json={
                "raw_text": SAMPLE_LECTURE_TEXT,
                "chunk_size": 300,
                "overlap": 300,
            },
        )
        assert res.status_code == 422


@pytest.mark.anyio
async def test_generate_from_context_full_flow_with_mocked_llm(monkeypatch, instructor_user):
    fake_single = _valid_single_choice()
    fake_tf = _valid_true_false()

    intercepted_prompts = []

    async def mock_llm_call(system_prompt, user_prompt, response_schema, temperature=0.35):
        intercepted_prompts.append((system_prompt, user_prompt))
        if "SINGLE_CHOICE" in user_prompt:
            return LLMGeneratedBatchSchema(questions=[fake_single])
        return LLMGeneratedBatchSchema(questions=[fake_tf])

    monkeypatch.setattr(
        "app.modules.ai_generator.service.llm_client.generate_structured_json",
        mock_llm_call,
    )

    with monkeypatch.context() as ctx:
        ctx.setitem(app.dependency_overrides, get_db, lambda: None)
        ctx.setitem(app.dependency_overrides, get_current_user, lambda: instructor_user)

        res = client.post(
            "/api/v1/ai-generator/generate-from-context",
            json={
                "raw_text": SAMPLE_LECTURE_TEXT,
                "topic": "Tầng Giao vận TCP/UDP",
                "total_questions": 2,
                "cognitive_distribution": {"REMEMBER": 1, "UNDERSTAND": 1, "APPLY": 0},
                "type_distribution": {"SINGLE_CHOICE": 1, "MULTIPLE_CHOICE": 0, "TRUE_FALSE": 1},
                "chunk_size": 500,
                "overlap": 100,
            },
        )

        assert res.status_code == 200
        payload = res.json()["data"]

        assert payload["total_requested"] == 2
        assert payload["total_generated"] == 2
        assert payload["total_chunks"] >= 2
        assert payload["chunks_used"] >= 1
        assert len(payload["generated_questions"]) == 2
        assert payload["quality_checks"]["context_grounded"] is True
        assert payload["quality_checks"]["exact_count_match"] is True

        # Verify context was properly injected into user prompt
        assert len(intercepted_prompts) == 2
        for _, u_prompt in intercepted_prompts:
            assert "[NGỮ CẢNH TÀI LIỆU BẮT BUỘC ĐỂ SOẠN CÂU HỎI]" in u_prompt
            assert "Tầng Giao vận" in u_prompt or "TCP" in u_prompt or "UDP" in u_prompt


@pytest.mark.anyio
async def test_generate_from_context_deduplicates_questions(monkeypatch):
    service = AIQuestionGeneratorService()
    request = GenerateFromContextRequest(
        raw_text=SAMPLE_LECTURE_TEXT,
        total_questions=2,
        cognitive_distribution=CognitiveDistributionSchema(REMEMBER=2),
        type_distribution=QuestionTypeDistributionSchema(SINGLE_CHOICE=2),
        chunk_size=400,
        overlap=80,
    )

    duplicate_q = _valid_single_choice("TCP hoạt động ở tầng nào trong OSI?")
    different_q = _valid_single_choice("Cơ chế bắt tay 3 bước thuộc về giao thức nào?")

    # First attempt returns 2 identical questions; second repair attempt provides the distinct question
    call_count = 0

    async def mock_llm(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return LLMGeneratedBatchSchema(questions=[duplicate_q, duplicate_q])
        return LLMGeneratedBatchSchema(questions=[different_q])

    monkeypatch.setattr(
        "app.modules.ai_generator.service.llm_client.generate_structured_json",
        mock_llm,
    )

    result = await service.generate_from_context(request)
    assert result.total_generated == 2
    stems = [q.content for q in result.generated_questions]
    assert len(set(stems)) == 2
    assert result.quality_checks["rejected_invalid_candidates"] >= 1


@pytest.mark.anyio
async def test_generate_from_context_service_error_mappings(monkeypatch):
    service = AIQuestionGeneratorService()
    request = GenerateFromContextRequest(
        raw_text=SAMPLE_LECTURE_TEXT,
        total_questions=1,
        cognitive_distribution=CognitiveDistributionSchema(REMEMBER=1),
        type_distribution=QuestionTypeDistributionSchema(SINGLE_CHOICE=1),
    )

    # 1. Test RateLimitError maps to LLMUnavailableError
    http_req = httpx.Request("POST", "https://example.test")
    monkeypatch.setattr(
        "app.modules.ai_generator.service.llm_client.generate_structured_json",
        AsyncMock(side_effect=RateLimitError("Rate limit", response=httpx.Response(429, request=http_req), body=None)),
    )
    with pytest.raises(LLMUnavailableError):
        await service.generate_from_context(request)

    # 2. Test repair exhaustion maps to QuestionGenerationError
    bad_q = _valid_single_choice()
    bad_q.options[3] = _make_option("D", "Tất cả các đáp án trên", False)
    monkeypatch.setattr(
        "app.modules.ai_generator.service.llm_client.generate_structured_json",
        AsyncMock(return_value=LLMGeneratedBatchSchema(questions=[bad_q])),
    )
    with pytest.raises(QuestionGenerationError):
        await service.generate_from_context(request)
