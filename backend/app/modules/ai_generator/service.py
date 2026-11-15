"""AI Question Generation Service using Bloom Taxonomy Prompt Templates (Issue #11 / WBS 3.2.1)."""

import logging
from typing import Dict, List, Set

from openai import APIConnectionError, APIStatusError, RateLimitError
from pydantic import ValidationError

from app.core.llm_client import llm_client
from app.models.entities import CognitiveLevel, QuestionType
from app.modules.ai_generator.chunking_service import chunking_service
from app.modules.ai_generator.prompts import (
    BLOOM_PROMPT_TEMPLATES,
    COGNITIVE_ORDER,
    DISTRACTOR_QUALITY_RULES,
    QUESTION_TYPE_ORDER,
    QUESTION_TYPE_TEMPLATES,
    build_cell_prompts,
    plan_matrix_cells,
)
from app.modules.ai_generator.schemas import (
    BloomTemplateMetadata,
    BloomTemplatesCatalogResponse,
    GenerateByMatrixRequest,
    GenerateByMatrixResponse,
    GenerateFromContextRequest,
    GenerateFromContextResponse,
    GeneratedQuestionItem,
    LLMGeneratedBatchSchema,
    MatrixCellAllocation,
    PromptPlanCellSchema,
    PromptPreviewResponse,
    QuestionTypeTemplateMetadata,
)
from app.modules.ai_generator.validators import filter_valid_questions

logger = logging.getLogger(__name__)

MAX_REPAIR_ATTEMPTS_PER_CELL = 2


class QuestionGenerationError(RuntimeError):
    """Raised when generated output cannot satisfy the requested Bloom matrix or quality rules."""


class LLMUnavailableError(RuntimeError):
    """Raised when the configured LLM provider fails due to configuration, rate limits, or network."""


class AIQuestionGeneratorService:
    """Orchestrates Bloom-taxonomy prompt planning, LLM invocation, and distractor validation."""

    def get_templates_catalog(self) -> BloomTemplatesCatalogResponse:
        """Return metadata for all 3 Bloom templates, 3 question types, and distractor rules."""
        bloom_items = [
            BloomTemplateMetadata(
                cognitive_level=spec.cognitive_level,
                label_vi=spec.label_vi,
                label_en=spec.label_en,
                default_difficulty=spec.default_difficulty,
                objective=spec.objective,
                bloom_verbs=list(spec.bloom_verbs),
                question_design_rules=spec.question_design_rules,
                distractor_strategy=spec.distractor_strategy,
            )
            for level in COGNITIVE_ORDER
            for spec in (BLOOM_PROMPT_TEMPLATES[level],)
        ]
        type_items = [
            QuestionTypeTemplateMetadata(
                question_type=spec.question_type,
                label_vi=spec.label_vi,
                label_en=spec.label_en,
                option_count_rule=spec.option_count_rule,
                correct_answer_rule=spec.correct_answer_rule,
                format_guidelines=spec.format_guidelines,
            )
            for qtype in QUESTION_TYPE_ORDER
            for spec in (QUESTION_TYPE_TEMPLATES[qtype],)
        ]
        return BloomTemplatesCatalogResponse(
            bloom_templates=bloom_items,
            question_type_templates=type_items,
            distractor_quality_rules=DISTRACTOR_QUALITY_RULES,
        )

    def build_prompt_plan(self, request: GenerateByMatrixRequest) -> PromptPreviewResponse:
        """Compute exact matrix cell allocations and render prompts without calling the LLM."""
        assert request.cognitive_distribution is not None
        assert request.type_distribution is not None
        assert request.total_questions is not None

        cognitive_counts = request.cognitive_distribution.as_enum_dict()
        type_counts = request.type_distribution.as_enum_dict()
        cells = plan_matrix_cells(cognitive_counts, type_counts)

        allocations: List[PromptPlanCellSchema] = []
        for cognitive_level, question_type, count in cells:
            system_prompt, user_prompt = build_cell_prompts(
                topic=request.topic,
                cognitive_level=cognitive_level,
                question_type=question_type,
                count=count,
                subject_name=request.subject_name,
                language=request.language,
                additional_instructions=request.additional_instructions,
            )
            allocations.append(
                PromptPlanCellSchema(
                    cognitive_level=cognitive_level,
                    question_type=question_type,
                    count=count,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                )
            )

        return PromptPreviewResponse(
            topic=request.topic,
            subject_name=request.subject_name,
            total_questions=request.total_questions,
            cognitive_distribution={k.value: v for k, v in cognitive_counts.items()},
            type_distribution={k.value: v for k, v in type_counts.items()},
            allocations=allocations,
        )

    async def generate_by_matrix(
        self, request: GenerateByMatrixRequest
    ) -> GenerateByMatrixResponse:
        """Generate questions matching exact Bloom taxonomy and question type distributions."""
        assert request.cognitive_distribution is not None
        assert request.type_distribution is not None
        assert request.total_questions is not None

        cognitive_counts = request.cognitive_distribution.as_enum_dict()
        type_counts = request.type_distribution.as_enum_dict()
        planned_cells = plan_matrix_cells(cognitive_counts, type_counts)

        generated_questions: List[GeneratedQuestionItem] = []
        seen_stems: Set[str] = set()
        seen_raw_contents: List[str] = []
        rejected_candidates = 0
        repair_calls = 0

        for cognitive_level, question_type, target_count in planned_cells:
            cell_questions: List[GeneratedQuestionItem] = []
            repair_feedback: str | None = None

            for attempt in range(1 + MAX_REPAIR_ATTEMPTS_PER_CELL):
                remaining = target_count - len(cell_questions)
                if remaining <= 0:
                    break
                if attempt > 0:
                    repair_calls += 1

                system_prompt, user_prompt = build_cell_prompts(
                    topic=request.topic,
                    cognitive_level=cognitive_level,
                    question_type=question_type,
                    count=remaining,
                    subject_name=request.subject_name,
                    language=request.language,
                    additional_instructions=request.additional_instructions,
                    existing_question_contents=seen_raw_contents,
                    repair_feedback=repair_feedback,
                )

                try:
                    batch = await llm_client.generate_structured_json(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        response_schema=LLMGeneratedBatchSchema,
                        temperature=request.temperature,
                    )
                except (RateLimitError, APIConnectionError, APIStatusError) as exc:
                    logger.error("LLM provider error during matrix generation: %s", type(exc).__name__)
                    raise LLMUnavailableError(
                        "Dịch vụ AI hiện đang bận hoặc không thể kết nối. Vui lòng thử lại sau."
                    ) from exc
                except RuntimeError as exc:
                    # Covers LLMConfigurationError / LLMRateLimitError / LLMResponseError when present
                    err_name = type(exc).__name__
                    if err_name == "LLMConfigurationError":
                        raise LLMUnavailableError(
                            "Dịch vụ AI chưa được cấu hình API Key hợp lệ. Vui lòng liên hệ quản trị viên."
                        ) from exc
                    if err_name == "LLMRateLimitError":
                        raise LLMUnavailableError(
                            "Dịch vụ AI hiện đang bận do giới hạn lượt gọi. Vui lòng thử lại sau."
                        ) from exc
                    if err_name == "LLMResponseError":
                        repair_feedback = "Lần gọi trước trả về phản hồi rỗng. Hãy trả về JSON hợp lệ với đủ số câu hỏi."
                        continue
                    raise
                except ValidationError as exc:
                    logger.warning("LLM batch schema validation failed on attempt %s: %s", attempt + 1, exc)
                    repair_feedback = (
                        "Đầu ra JSON lần trước chưa đúng schema bắt buộc. "
                        "Hãy trả về đúng object chứa mảng 'questions' với đầy đủ các trường."
                    )
                    continue

                accepted, rejections = filter_valid_questions(
                    batch.questions,
                    expected_cognitive_level=cognitive_level,
                    expected_question_type=question_type,
                    existing_normalized_stems=seen_stems,
                    limit=remaining,
                    category_id=request.category_id,
                )
                rejected_candidates += len(rejections)
                for question in accepted:
                    cell_questions.append(question)
                    seen_raw_contents.append(question.content)

                if len(cell_questions) < target_count:
                    reasons_summary = "; ".join(rejections[:3]) if rejections else "Thiếu số lượng câu hỏi hợp lệ"
                    repair_feedback = (
                        f"Cần bổ sung thêm {target_count - len(cell_questions)} câu hỏi hợp lệ. "
                        f"Lý do một số câu trước bị loại: {reasons_summary}. "
                        "Lưu ý: không trùng lặp phương án, không dùng 'Tất cả các đáp án trên', "
                        f"đúng mức độ {cognitive_level.value} và loại {question_type.value}."
                    )

            if len(cell_questions) != target_count:
                raise QuestionGenerationError(
                    f"Không thể tạo đủ {target_count} câu hỏi hợp lệ cho mức {cognitive_level.value}/{question_type.value} "
                    f"sau {1 + MAX_REPAIR_ATTEMPTS_PER_CELL} lần thử (chỉ thu được {len(cell_questions)} câu hợp lệ)."
                )

            generated_questions.extend(cell_questions)

        actual_cognitive: Dict[str, int] = {level.value: 0 for level in COGNITIVE_ORDER}
        actual_types: Dict[str, int] = {qtype.value: 0 for qtype in QUESTION_TYPE_ORDER}
        for item in generated_questions:
            actual_cognitive[item.cognitive_level.value] += 1
            actual_types[item.question_type.value] += 1

        requested_cognitive = {k.value: v for k, v in cognitive_counts.items()}
        requested_types = {k.value: v for k, v in type_counts.items()}

        if (
            len(generated_questions) != request.total_questions
            or actual_cognitive != requested_cognitive
            or actual_types != requested_types
        ):
            raise QuestionGenerationError(
                "Số lượng hoặc tỷ lệ câu hỏi sinh ra không khớp với ma trận yêu cầu."
            )

        return GenerateByMatrixResponse(
            topic=request.topic,
            subject_name=request.subject_name,
            total_requested=request.total_questions,
            total_generated=len(generated_questions),
            cognitive_distribution=actual_cognitive,
            type_distribution=actual_types,
            allocations=[
                MatrixCellAllocation(
                    cognitive_level=cog,
                    question_type=qtype,
                    count=count,
                )
                for cog, qtype, count in planned_cells
            ],
            generated_questions=generated_questions,
            quality_checks={
                "exact_count_match": True,
                "exact_cognitive_distribution_match": True,
                "exact_type_distribution_match": True,
                "duplicate_options_blocked": True,
                "duplicate_questions_blocked": True,
                "banned_lazy_options_blocked": True,
                "rejected_invalid_candidates": rejected_candidates,
                "repair_calls": repair_calls,
            },
        )

    async def generate_from_context(
        self, request: GenerateFromContextRequest
    ) -> GenerateFromContextResponse:
        """Generate quiz questions grounded in long-form document text chunks."""
        assert request.cognitive_distribution is not None
        assert request.type_distribution is not None
        assert request.total_questions is not None

        # 1. Chunk document using sliding window chunker
        chunks = chunking_service.chunk(
            request.raw_text,
            chunk_size=request.chunk_size,
            overlap=request.overlap,
        )
        if not chunks:
            raise QuestionGenerationError(
                "Tài liệu không chứa nội dung văn bản hợp lệ để phân đoạn ngữ cảnh."
            )

        cognitive_counts = request.cognitive_distribution.as_enum_dict()
        type_counts = request.type_distribution.as_enum_dict()
        planned_cells = plan_matrix_cells(cognitive_counts, type_counts)

        generated_questions: List[GeneratedQuestionItem] = []
        seen_stems: Set[str] = set()
        seen_raw_contents: List[str] = []
        rejected_candidates = 0
        repair_calls = 0
        chunks_used_indices: Set[int] = set()

        for cell_idx, (cognitive_level, question_type, target_count) in enumerate(planned_cells):
            cell_questions: List[GeneratedQuestionItem] = []
            repair_feedback: str | None = None

            # Select context chunk for this cell (cyclically across planned cells)
            chunk_obj = chunks[cell_idx % len(chunks)]
            chunks_used_indices.add(chunk_obj.index)
            chunk_context = chunk_obj.text

            for attempt in range(1 + MAX_REPAIR_ATTEMPTS_PER_CELL):
                remaining = target_count - len(cell_questions)
                if remaining <= 0:
                    break
                if attempt > 0:
                    repair_calls += 1

                system_prompt, user_prompt = build_cell_prompts(
                    topic=request.topic,
                    cognitive_level=cognitive_level,
                    question_type=question_type,
                    count=remaining,
                    subject_name=request.subject_name,
                    language=request.language,
                    additional_instructions=request.additional_instructions,
                    existing_question_contents=seen_raw_contents,
                    repair_feedback=repair_feedback,
                    context_text=chunk_context,
                )

                try:
                    batch = await llm_client.generate_structured_json(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        response_schema=LLMGeneratedBatchSchema,
                        temperature=request.temperature,
                    )
                except (RateLimitError, APIConnectionError, APIStatusError) as exc:
                    logger.error(
                        "LLM provider error during context-based generation: %s",
                        type(exc).__name__,
                    )
                    raise LLMUnavailableError(
                        "Dịch vụ AI hiện đang bận hoặc không thể kết nối. Vui lòng thử lại sau."
                    ) from exc
                except RuntimeError as exc:
                    err_name = type(exc).__name__
                    if err_name == "LLMConfigurationError":
                        raise LLMUnavailableError(
                            "Dịch vụ AI chưa được cấu hình API Key hợp lệ. Vui lòng liên hệ quản trị viên."
                        ) from exc
                    if err_name == "LLMRateLimitError":
                        raise LLMUnavailableError(
                            "Dịch vụ AI hiện đang bận do giới hạn lượt gọi. Vui lòng thử lại sau."
                        ) from exc
                    if err_name == "LLMResponseError":
                        repair_feedback = (
                            "Lần gọi trước trả về phản hồi rỗng. Hãy trả về JSON hợp lệ với đủ số câu hỏi."
                        )
                        continue
                    raise
                except ValidationError as exc:
                    logger.warning(
                        "LLM batch schema validation failed on attempt %s: %s",
                        attempt + 1,
                        exc,
                    )
                    repair_feedback = (
                        "Đầu ra JSON lần trước chưa đúng schema bắt buộc. "
                        "Hãy trả về đúng object chứa mảng 'questions' với đầy đủ các trường."
                    )
                    continue

                accepted, rejections = filter_valid_questions(
                    batch.questions,
                    expected_cognitive_level=cognitive_level,
                    expected_question_type=question_type,
                    existing_normalized_stems=seen_stems,
                    limit=remaining,
                    category_id=request.category_id,
                )
                rejected_candidates += len(rejections)
                for question in accepted:
                    cell_questions.append(question)
                    seen_raw_contents.append(question.content)

                if len(cell_questions) < target_count:
                    reasons_summary = (
                        "; ".join(rejections[:3]) if rejections else "Thiếu số lượng câu hỏi hợp lệ"
                    )
                    repair_feedback = (
                        f"Cần bổ sung thêm {target_count - len(cell_questions)} câu hỏi hợp lệ từ ngữ cảnh tài liệu. "
                        f"Lý do một số câu trước bị loại: {reasons_summary}. "
                        "Lưu ý: bám sát ngữ cảnh tài liệu, không trùng lặp phương án, không dùng 'Tất cả các đáp án trên', "
                        f"đúng mức độ {cognitive_level.value} và loại {question_type.value}."
                    )

            if len(cell_questions) != target_count:
                raise QuestionGenerationError(
                    f"Không thể tạo đủ {target_count} câu hỏi hợp lệ từ tài liệu cho mức {cognitive_level.value}/{question_type.value} "
                    f"sau {1 + MAX_REPAIR_ATTEMPTS_PER_CELL} lần thử (chỉ thu được {len(cell_questions)} câu hợp lệ)."
                )

            generated_questions.extend(cell_questions)

        actual_cognitive: Dict[str, int] = {level.value: 0 for level in COGNITIVE_ORDER}
        actual_types: Dict[str, int] = {qtype.value: 0 for qtype in QUESTION_TYPE_ORDER}
        for item in generated_questions:
            actual_cognitive[item.cognitive_level.value] += 1
            actual_types[item.question_type.value] += 1

        requested_cognitive = {k.value: v for k, v in cognitive_counts.items()}
        requested_types = {k.value: v for k, v in type_counts.items()}

        if (
            len(generated_questions) != request.total_questions
            or actual_cognitive != requested_cognitive
            or actual_types != requested_types
        ):
            raise QuestionGenerationError(
                "Số lượng hoặc tỷ lệ câu hỏi sinh ra từ tài liệu không khớp với ma trận yêu cầu."
            )

        return GenerateFromContextResponse(
            topic=request.topic,
            subject_name=request.subject_name,
            total_requested=request.total_questions,
            total_generated=len(generated_questions),
            chunks_used=len(chunks_used_indices),
            total_chunks=len(chunks),
            cognitive_distribution=actual_cognitive,
            type_distribution=actual_types,
            allocations=[
                MatrixCellAllocation(
                    cognitive_level=cog,
                    question_type=qtype,
                    count=count,
                )
                for cog, qtype, count in planned_cells
            ],
            generated_questions=generated_questions,
            quality_checks={
                "exact_count_match": True,
                "exact_cognitive_distribution_match": True,
                "exact_type_distribution_match": True,
                "duplicate_options_blocked": True,
                "duplicate_questions_blocked": True,
                "banned_lazy_options_blocked": True,
                "context_grounded": True,
                "rejected_invalid_candidates": rejected_candidates,
                "repair_calls": repair_calls,
            },
        )


ai_generator_service = AIQuestionGeneratorService()

