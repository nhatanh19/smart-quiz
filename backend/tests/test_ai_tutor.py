import asyncio
import os
import sys
import time
from fastapi.testclient import TestClient

# Ensure UTF-8 output on Windows console
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.modules.tutor_analytics.schemas import (
    AITutorExplanationData,
    AITutorExplanationRequest,
    AITutorFeedbackSchema,
)
from app.modules.tutor_analytics.service import ai_tutor_service
from app.schemas.common import QuestionOptionSchema

client = TestClient(app)


def test_ai_tutor_feedback_schema():
    """Verify that AITutorFeedbackSchema conforms to docs/DATABASE_GUIDE.md section 5.5."""
    sample_feedback = {
        "version": 1,
        "explanation": "Phương án A đúng vì WBS là cấu trúc phân rã công việc định hướng sản phẩm bàn giao.",
        "why_selected_wrong": "Thí sinh chọn B vì nhầm lẫn giữa Schedule (tiến độ) và Breakdown Structure.",
        "study_suggestions": [
            "Ôn tập lại Chương 3: Quản lý Phạm vi Dự án (Project Scope Management)",
            "Đọc tài liệu PMBOK về Quy tắc 100% của WBS",
        ],
        "model": "gpt-4o-mini",
        "generated_at": "2026-10-19T10:00:00Z",
    }
    validated = AITutorFeedbackSchema.model_validate(sample_feedback)
    assert validated.version == 1
    assert "WBS" in validated.explanation
    assert "nhầm lẫn" in validated.why_selected_wrong
    assert len(validated.study_suggestions) == 2


async def test_ai_tutor_service_explanation_latency_and_content():
    """Test Issue #16 Acceptance Criteria (DoD):

    1. Bấm nút 'Giải thích bằng AI' trên câu sai hiển thị lời giải thích chi tiết trong vòng < 3 giây (< 3000 ms).
    2. Giọng văn sư phạm, dễ hiểu, phân tích trúng nguyên nhân nhầm lẫn.
    """
    request = AITutorExplanationRequest(
        question_content="Trong chuẩn quản lý dự án PMBOK, WBS (Work Breakdown Structure) được định nghĩa là gì?",
        options=[
            QuestionOptionSchema(
                id="A",
                text="Cấu trúc phân rã công việc định hướng theo sản phẩm bàn giao",
                is_correct=True,
            ),
            QuestionOptionSchema(
                id="B",
                text="Bảng phân bổ ngân sách chi tiết và lịch biểu thanh toán hàng tuần",
                is_correct=False,
            ),
            QuestionOptionSchema(
                id="C",
                text="Báo cáo tổng kết khối lượng công việc hàng tuần của nhóm Scrum",
                is_correct=False,
            ),
        ],
        selected_options=["B"],  # Student selected B (WRONG)
        correct_options=["A"],   # Standard key is A (CORRECT)
        question_explanation="WBS là cấu trúc phân rã công việc mang tính định hướng bàn giao.",
    )

    start_time = time.perf_counter()
    result: AITutorExplanationData = await ai_tutor_service.generate_explanation(request)
    total_latency_ms = (time.perf_counter() - start_time) * 1000

    # 1. Assert response time is strictly under 3 seconds (< 3000 ms) as specified in DoD
    assert total_latency_ms < 3000, f"Latency {total_latency_ms}ms exceeded 3000ms DoD limit"
    assert result.response_time_ms < 3000

    # 2. Assert correctness and diagnosis of misconception
    assert result.is_correct is False
    assert result.selected_options == ["B"]
    assert result.correct_options == ["A"]

    # 3. Assert pedagogical feedback elements
    feedback = result.feedback
    assert isinstance(feedback, AITutorFeedbackSchema)
    assert len(feedback.explanation.strip()) > 10, "Explanation must be comprehensive"
    assert len(feedback.why_selected_wrong.strip()) > 10, "Misconception diagnosis must be present"
    assert len(feedback.study_suggestions) >= 2, "Must offer at least 2 study suggestions"


def test_api_explain_endpoint():
    """Test the HTTP REST endpoint POST /api/v1/tutor-analytics/explain."""
    payload = {
        "question_content": "Theo Scrum, nguyên tắc WIP Limit có mục đích chính là gì?",
        "options": [
            {
                "id": "A",
                "text": "Ngăn chặn nghẽn cổ chai và nâng cao lưu lượng luân chuyển công việc",
                "is_correct": True,
            },
            {
                "id": "B",
                "text": "Bắt buộc mọi thành viên làm thêm giờ trong tuần",
                "is_correct": False,
            },
        ],
        "selected_options": ["B"],
        "correct_options": ["A"],
    }

    start = time.perf_counter()
    response = client.post("/api/v1/tutor-analytics/explain", json=payload)
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert response.status_code == 200
    # Must answer under 3 seconds
    assert elapsed_ms < 3000

    body = response.json()
    assert body["success"] is True
    assert "data" in body

    data = body["data"]
    assert data["is_correct"] is False
    assert data["response_time_ms"] < 3000
    assert "feedback" in data

    feedback = data["feedback"]
    assert "explanation" in feedback
    assert "why_selected_wrong" in feedback
    assert "study_suggestions" in feedback


if __name__ == "__main__":
    print("Running AI Tutor unit & integration tests...")
    test_ai_tutor_feedback_schema()
    print("✅ test_ai_tutor_feedback_schema passed!")

    asyncio.run(test_ai_tutor_service_explanation_latency_and_content())
    print("✅ test_ai_tutor_service_explanation_latency_and_content passed (< 3s DoD verified)!")

    test_api_explain_endpoint()
    print("✅ test_api_explain_endpoint passed (< 3s HTTP API response verified)!")
    print("\n🎉 ALL TESTS PASSED!")
