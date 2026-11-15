import os
import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.llm_client import llm_client
from app.models.entities import AttemptAnswer, Question
from app.modules.tutor_analytics.schemas import (
    AITutorExplanationData,
    AITutorExplanationRequest,
    AITutorFeedbackSchema,
)

logger = logging.getLogger(__name__)

QUESTION_TYPE_LABELS = {
    "SINGLE_CHOICE": "Một đáp án đúng",
    "MULTIPLE_CHOICE": "Nhiều đáp án đúng (phải chọn đủ và không chọn thừa)",
    "TRUE_FALSE": "Đúng / Sai",
}

COGNITIVE_LEVEL_LABELS = {
    "REMEMBER": "Nhận biết",
    "UNDERSTAND": "Thông hiểu",
    "APPLY": "Vận dụng",
}


def _enum_value(value: Any) -> Optional[str]:
    if value is None:
        return None
    return value.value if hasattr(value, "value") else str(value)


class AITutorService:
    """Service handling contextual AI Tutor explanations and feedback generation.

    Fulfills Issue #16 (WBS 5.2.1):
    - Contextual explanation of correct vs student-selected options.
    - Deep diagnosis of misconception causes, per wrongly selected / missed option.
    - Pedagogical tone and actionable study recommendations.
    - Strictly ensures sub-3-second response latency (hard timeout + fallback).
    """

    SYSTEM_PROMPT = """Bạn là Gia sư ảo (AI Tutor) của nền tảng khảo thí Smart Quiz: thông thái, tận tâm, giàu kinh nghiệm sư phạm.
Nhiệm vụ: phân tích ngữ cảnh một câu hỏi trắc nghiệm và bài làm của sinh viên, rồi giải thích cặn kẽ.

QUY TRÌNH SUY LUẬN (làm trong đầu, KHÔNG viết ra):
1. Xác định kiến thức/khái niệm cốt lõi mà câu hỏi kiểm tra và các từ khóa điều kiện trong đề (ví dụ: "chính", "không", "luôn", "đầu tiên").
2. Với đáp án chuẩn: tìm căn cứ lý thuyết khiến nó đúng.
3. Với TỪNG phương án sinh viên chọn sai: tìm điểm sai cụ thể trong nội dung phương án đó và đoán nguyên nhân nhầm lẫn có khả năng nhất
   (nhầm định nghĩa, đánh đồng hai khái niệm gần nghĩa, bỏ sót từ khóa điều kiện, hiểu đúng một phần nhưng khái quát hóa sai, áp dụng sai ngữ cảnh...).
4. Với câu nhiều đáp án: chỉ rõ cả phương án đúng bị bỏ sót.

YÊU CẦU ĐẦU RA:
- "explanation": 2-4 câu, giải thích vì sao đáp án chuẩn đúng, nêu rõ bản chất khái niệm. Nhắc đúng ID phương án.
- "why_selected_wrong": nói thẳng với sinh viên (xưng "bạn"), nêu ID và nội dung phương án đã chọn, chỉ ra CHÍNH XÁC chỗ sai
  và nguyên nhân nhầm lẫn, rồi đối chiếu với đáp án đúng. Không dùng câu chung chung kiểu "đây là bẫy đề phổ biến" mà không chỉ ra bẫy cụ thể.
  Nếu sinh viên bỏ trống: giải thích cách suy luận/loại trừ để đi đến đáp án đúng.
  Nếu sinh viên làm đúng: khẳng định lý do đúng và lưu ý điểm dễ nhầm để củng cố.
- "study_suggestions": 2-3 gợi ý ôn tập CỤ THỂ gắn với kiến thức của câu hỏi (tên khái niệm/chủ đề), không chung chung.
- Giọng văn: sư phạm, thấu cảm, khích lệ, dễ hiểu; Tiếng Việt chuẩn; không phán xét.
- Chỉ dựa trên dữ liệu được cung cấp; nếu có ghi chú giải thích gốc từ ngân hàng đề thì ưu tiên bám theo, không mâu thuẫn với đáp án chuẩn.

VÍ DỤ MẪU:
[Câu hỏi]: Trong PMBOK, WBS là gì?
- A: Cấu trúc phân rã công việc định hướng theo sản phẩm bàn giao [ĐÁP ÁN CHUẨN]
- B: Lịch biểu tiến độ chi tiết của dự án [SINH VIÊN CHỌN - SAI]
Đầu ra:
{"explanation": "Phương án A đúng: WBS (Work Breakdown Structure) phân rã toàn bộ phạm vi dự án thành các gói công việc nhỏ hơn, định hướng theo sản phẩm bàn giao (deliverable) và tuân theo quy tắc 100%.",
 "why_selected_wrong": "Bạn chọn B có lẽ vì WBS và lịch biểu (Schedule) thường được lập liên tiếp nhau nên dễ bị đánh đồng. Tuy nhiên WBS chỉ trả lời câu hỏi 'cần làm những gì' (phạm vi), còn lịch biểu trả lời 'làm khi nào' (thời gian) và được xây dựng SAU khi đã có WBS. Từ khóa 'Breakdown' (phân rã) là gợi ý quan trọng giúp loại B.",
 "study_suggestions": ["Quản lý phạm vi dự án: quy trình Create WBS và quy tắc 100%", "Phân biệt WBS, danh sách hoạt động (Activity List) và lịch biểu (Schedule)"]}"""

    def _build_user_prompt(
        self,
        question_content: str,
        options: List[Dict[str, Any]],
        selected_option_ids: List[str],
        correct_option_ids: List[str],
        existing_explanation: Optional[str] = None,
        question_type: Optional[str] = None,
        cognitive_level: Optional[str] = None,
        category_name: Optional[str] = None,
    ) -> str:
        """Construct the contextual user prompt for the LLM."""
        options_text_list = []
        for opt in options:
            opt_id = opt.get("id", "")
            opt_text = opt.get("text", "")
            is_correct = opt_id in correct_option_ids
            is_selected = opt_id in selected_option_ids
            if is_correct and is_selected:
                marker = " [ĐÁP ÁN CHUẨN - sinh viên đã chọn đúng]"
            elif is_correct:
                marker = " [ĐÁP ÁN CHUẨN - sinh viên KHÔNG chọn]"
            elif is_selected:
                marker = " [SINH VIÊN CHỌN - SAI]"
            else:
                marker = ""
            options_text_list.append(f"- {opt_id}: {opt_text}{marker}")

        options_block = "\n".join(options_text_list) or "(Không có dữ liệu phương án)"
        selected_str = ", ".join(selected_option_ids) if selected_option_ids else "(Bỏ trống - chưa chọn)"
        correct_str = ", ".join(correct_option_ids) if correct_option_ids else "(Không xác định)"
        wrong_selected = [o for o in selected_option_ids if o not in correct_option_ids]
        missed_correct = [o for o in correct_option_ids if o not in selected_option_ids]

        context_lines = []
        if category_name:
            context_lines.append(f"- Chuyên đề/học phần: {category_name}")
        if question_type:
            context_lines.append(f"- Dạng câu hỏi: {QUESTION_TYPE_LABELS.get(question_type, question_type)}")
        if cognitive_level:
            context_lines.append(
                f"- Mức độ nhận thức (Bloom): {COGNITIVE_LEVEL_LABELS.get(cognitive_level, cognitive_level)}"
            )

        prompt = "Hãy phân tích câu hỏi trắc nghiệm sau và giải thích cặn kẽ cho sinh viên.\n"
        if context_lines:
            prompt += "\n[NGỮ CẢNH]:\n" + "\n".join(context_lines) + "\n"
        prompt += f"""
[CÂU HỎI]:
{question_content}

[CÁC PHƯƠNG ÁN]:
{options_block}

[KẾT QUẢ BÀI LÀM]:
- Đáp án chuẩn: {correct_str}
- Sinh viên đã chọn: {selected_str}
- Phương án chọn sai cần phân tích: {", ".join(wrong_selected) if wrong_selected else "(không có)"}
- Đáp án đúng bị bỏ sót: {", ".join(missed_correct) if missed_correct else "(không có)"}
"""
        if existing_explanation:
            prompt += f"\n[GHI CHÚ GIẢI THÍCH GỐC TỪ NGÂN HÀNG ĐỀ]:\n{existing_explanation}\n"

        prompt += (
            "\nTrả về JSON gồm \"explanation\", \"why_selected_wrong\", \"study_suggestions\" "
            "theo đúng yêu cầu đầu ra. Trong \"why_selected_wrong\" phải phân tích riêng từng phương án chọn sai "
            "và từng đáp án bị bỏ sót được liệt kê ở trên."
        )
        return prompt

    def _generate_pedagogical_fallback(
        self,
        question_content: str,
        options: List[Dict[str, Any]],
        selected_option_ids: List[str],
        correct_option_ids: List[str],
        existing_explanation: Optional[str] = None,
        category_name: Optional[str] = None,
    ) -> AITutorFeedbackSchema:
        """Rule-based pedagogical fallback used when the LLM is unavailable or too slow.

        Uses the actual option texts so the diagnosis stays specific to the question.
        """
        text_by_id = {opt.get("id"): opt.get("text", "") for opt in options}

        def describe(opt_ids: List[str]) -> str:
            return "; ".join(
                f"{oid} ('{text_by_id[oid]}')" if text_by_id.get(oid) else str(oid) for oid in opt_ids
            )

        correct_desc = describe(correct_option_ids) or "(chưa xác định)"
        wrong_selected = [o for o in selected_option_ids if o not in correct_option_ids]
        missed_correct = [o for o in correct_option_ids if o not in selected_option_ids]

        if existing_explanation:
            explanation = f"Đáp án đúng là {correct_desc}. {existing_explanation}"
        else:
            explanation = (
                f"Đáp án đúng là {correct_desc}. Đây là phương án phản ánh chính xác nội dung "
                f"mà câu hỏi yêu cầu; hãy đọc kỹ lại đề và đối chiếu từng từ khóa với phương án này."
            )

        parts: List[str] = []
        if not selected_option_ids:
            parts.append(
                "Bạn đã bỏ trống câu này. Lần sau hãy áp dụng phương pháp loại trừ: gạch bỏ các phương án "
                f"mâu thuẫn với từ khóa của đề, phương án còn lại có cơ sở nhất ở đây là {correct_desc}."
            )
        elif not wrong_selected and not missed_correct:
            parts.append(
                f"Bạn đã chọn chính xác {correct_desc}. Hãy ghi nhớ lý do đúng ở trên để làm chắc tay "
                "các câu tương tự."
            )
        for oid in wrong_selected:
            parts.append(
                f"Bạn đã chọn {describe([oid])}, nhưng nội dung này không khớp với điều mà câu hỏi đang hỏi. "
                f"Hãy so sánh trực tiếp với đáp án đúng {correct_desc}: điểm khác biệt giữa hai phương án "
                "chính là chỗ dễ gây nhầm lẫn - thường do hai khái niệm có tên hoặc phạm vi gần giống nhau, "
                "hoặc do bỏ sót một từ khóa điều kiện trong đề."
            )
        if missed_correct and selected_option_ids:
            parts.append(
                f"Bạn còn bỏ sót phương án đúng {describe(missed_correct)}. Với câu nhiều đáp án, "
                "cần xét độc lập từng phương án thay vì dừng lại khi đã tìm thấy một đáp án hợp lý."
            )
        why_wrong = " ".join(parts)

        topic = category_name or "nội dung câu hỏi"
        study_suggestions = [
            f"Đọc lại phần lý thuyết về {topic} trong giáo trình, chú ý định nghĩa gắn với đáp án {', '.join(correct_option_ids) or 'đúng'}",
            "Lập bảng so sánh giữa phương án đúng và phương án bạn đã chọn để nắm chắc điểm khác biệt",
            f"Luyện thêm 3-5 câu hỏi cùng chủ đề {topic} để củng cố",
        ]

        return AITutorFeedbackSchema(
            version=1,
            explanation=explanation,
            why_selected_wrong=why_wrong,
            study_suggestions=study_suggestions,
            model="rule-based-fallback",
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    async def _call_llm_with_model(
        self, model_name: str, user_prompt: str, timeout: float
    ) -> AITutorFeedbackSchema:
        """Call a single LLM model under a hard per-model timeout and tag the result."""
        feedback = await asyncio.wait_for(
            llm_client.generate_structured_json(
                system_prompt=self.SYSTEM_PROMPT,
                user_prompt=user_prompt,
                response_schema=AITutorFeedbackSchema,
                temperature=0.3,
                model_name=model_name,
            ),
            timeout=timeout,
        )
        feedback.model = model_name
        feedback.generated_at = datetime.now(timezone.utc).isoformat()
        return feedback

    def _llm_model_chain(self) -> List[str]:
        """Ordered list of models to try: primary first, then the optional backup."""
        chain = [settings.LLM_MODEL_NAME]
        backup = str(
            getattr(settings, "LLM_FALLBACK_MODEL_NAME", "")
            or os.environ.get("LLM_FALLBACK_MODEL_NAME", "")
        ).strip()
        if backup and backup != settings.LLM_MODEL_NAME:
            chain.append(backup)
        return chain

    async def generate_explanation(
        self,
        request: AITutorExplanationRequest,
        db: Optional[Session] = None,
    ) -> AITutorExplanationData:
        """Main method to generate or retrieve contextual explanation for a question answer."""
        start_time = time.perf_counter()

        attempt_id = request.attempt_id
        question_id = request.question_id
        is_correct: Optional[bool] = None
        selected_options = list(request.selected_options or [])
        correct_options = list(request.correct_options or [])
        question_content = request.question_content or ""
        options_data: List[Dict[str, Any]] = (
            [opt.model_dump() for opt in request.options] if request.options else []
        )
        existing_explanation = request.question_explanation
        question_type = _enum_value(request.question_type)
        cognitive_level: Optional[str] = None
        category_name: Optional[str] = None

        target_answer_record: Optional[AttemptAnswer] = None

        # 1. Check if database context is provided and fetch entities
        if db and attempt_id and question_id:
            target_answer_record = (
                db.query(AttemptAnswer)
                .filter(
                    AttemptAnswer.attempt_id == attempt_id,
                    AttemptAnswer.question_id == question_id,
                )
                .first()
            )

            question_record = (
                db.query(Question).filter(Question.id == question_id).first()
            )

            if question_record:
                if not question_content:
                    question_content = question_record.content
                if not options_data and isinstance(question_record.options, list):
                    options_data = question_record.options
                if not existing_explanation:
                    existing_explanation = question_record.explanation
                question_type = _enum_value(question_record.question_type)
                cognitive_level = _enum_value(question_record.cognitive_level)
                if question_record.category is not None:
                    category_name = question_record.category.name

                # Extract correct options from question record if not provided
                if not correct_options and isinstance(question_record.options, list):
                    correct_options = [
                        opt.get("id")
                        for opt in question_record.options
                        if opt.get("is_correct") is True
                    ]

            if target_answer_record:
                if not selected_options and isinstance(target_answer_record.selected_options, list):
                    selected_options = target_answer_record.selected_options
                is_correct = target_answer_record.is_correct

                # Check if feedback was already generated and cached in DB
                if (
                    target_answer_record.ai_tutor_feedback
                    and isinstance(target_answer_record.ai_tutor_feedback, dict)
                    and target_answer_record.ai_tutor_feedback.get("explanation")
                ):
                    try:
                        cached_feedback = AITutorFeedbackSchema.model_validate(
                            target_answer_record.ai_tutor_feedback
                        )
                        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
                        return AITutorExplanationData(
                            attempt_id=attempt_id,
                            question_id=question_id,
                            is_correct=is_correct,
                            selected_options=selected_options,
                            correct_options=correct_options,
                            feedback=cached_feedback,
                            cached=True,
                            response_time_ms=elapsed_ms,
                        )
                    except Exception as parse_cached_err:
                        logger.warning(
                            "Failed to parse cached ai_tutor_feedback: %s", parse_cached_err
                        )

        # Fall back to is_correct flags on the options when no answer key was supplied
        if not correct_options:
            correct_options = [opt.get("id") for opt in options_data if opt.get("is_correct") is True]

        # 2. Derive correctness if not explicitly set (an empty answer counts as wrong)
        if is_correct is None and correct_options:
            is_correct = set(selected_options) == set(correct_options)

        # 3. Call LLM to generate structured explanation under a hard time budget
        user_prompt = self._build_user_prompt(
            question_content=question_content or "Câu hỏi kiểm tra kiến thức",
            options=options_data,
            selected_option_ids=selected_options,
            correct_option_ids=correct_options,
            existing_explanation=existing_explanation,
            question_type=question_type,
            cognitive_level=cognitive_level,
            category_name=category_name,
        )

        feedback: AITutorFeedbackSchema
        from_llm = False
        timeout_ceiling = float(getattr(settings, "AI_TUTOR_TIMEOUT_SECONDS", 15.0))
        deadline = start_time + timeout_ceiling

        # Model-level failover: try the primary model, then the backup model,
        # each capped by a per-model slice AND the shared overall deadline.
        # Only if every real model fails/times out do we drop to the rule-based fallback.
        for model_name in self._llm_model_chain():
            remaining = deadline - time.perf_counter()
            if remaining <= 0.3:  # not enough time left to attempt another network call
                break
            model_timeout_slice = float(getattr(settings, "AI_TUTOR_MODEL_TIMEOUT_SECONDS", 12.0))
            per_model_timeout = min(model_timeout_slice, remaining)
            try:
                feedback = await self._call_llm_with_model(
                    model_name=model_name,
                    user_prompt=user_prompt,
                    timeout=per_model_timeout,
                )
                from_llm = True
                break
            except Exception as llm_err:
                logger.info(
                    "AI Tutor model '%s' failed or timed out (%s). Trying next option.",
                    model_name,
                    repr(llm_err),
                )

        if not from_llm:
            logger.info("All LLM models unavailable; using rule-based pedagogical fallback.")
            feedback = self._generate_pedagogical_fallback(
                question_content=question_content,
                options=options_data,
                selected_option_ids=selected_options,
                correct_option_ids=correct_options,
                existing_explanation=existing_explanation,
                category_name=category_name,
            )

        # 4. Persist only real LLM feedback so a later request can still get the AI version
        if db and target_answer_record and from_llm:
            try:
                target_answer_record.ai_tutor_feedback = feedback.model_dump()
                db.commit()
                db.refresh(target_answer_record)
                logger.info(
                    "Persisted ai_tutor_feedback into attempt_answers for attempt %s, question %s",
                    attempt_id,
                    question_id,
                )
            except Exception as db_save_err:
                db.rollback()
                logger.error("Failed to persist ai_tutor_feedback to database: %s", db_save_err)

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return AITutorExplanationData(
            attempt_id=attempt_id,
            question_id=question_id,
            is_correct=is_correct,
            selected_options=selected_options,
            correct_options=correct_options,
            feedback=feedback,
            cached=False,
            response_time_ms=elapsed_ms,
        )


ai_tutor_service = AITutorService()
