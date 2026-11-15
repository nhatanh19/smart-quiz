from typing import Any, Dict, Optional, Union

from fastapi import APIRouter, Body, Depends, HTTPException, status

from app.core.security import require_roles
from app.models.entities import UserRole
from app.modules.ai_generator.question_bank_router import router as question_bank_router
from app.modules.ai_generator.schemas import (
    BloomTemplatesCatalogResponse,
    GenerateByMatrixRequest,
    GenerateByMatrixResponse,
    GenerateFromContextRequest,
    GenerateFromContextResponse,
    PromptPreviewResponse,
)
from app.modules.ai_generator.service import (
    LLMUnavailableError,
    QuestionGenerationError,
    ai_generator_service,
)
from app.schemas.common import APIResponse, HealthCheckResponse

router = APIRouter(prefix="/ai-generator", tags=["Module 2: AI Quiz Generator (Dev 2)"])
router.include_router(question_bank_router, prefix="/question-bank")

AI_GENERATOR_ROLES = [UserRole.INSTRUCTOR, UserRole.ADMIN]


@router.get("/health", response_model=HealthCheckResponse)
def ai_generator_health_check():
    """Health check endpoint for AI Quiz Generator module."""
    return HealthCheckResponse(service="AI Quiz Generator Service")


@router.get(
    "/bloom-templates",
    response_model=APIResponse[BloomTemplatesCatalogResponse],
    dependencies=[Depends(require_roles(AI_GENERATOR_ROLES))],
)
def get_bloom_prompt_templates():
    """Return all 3 Bloom taxonomy prompt templates and 3 question-type formatting guides."""
    return APIResponse(
        success=True,
        message="Lấy danh sách bộ Prompt mẫu theo thang Bloom thành công",
        data=ai_generator_service.get_templates_catalog(),
    )


@router.post(
    "/bloom-templates/preview",
    response_model=APIResponse[PromptPreviewResponse],
    dependencies=[Depends(require_roles(AI_GENERATOR_ROLES))],
)
def preview_bloom_prompt_plan(payload: GenerateByMatrixRequest):
    """Compute matrix cell allocations and preview rendered Bloom prompts without calling the LLM."""
    plan = ai_generator_service.build_prompt_plan(payload)
    return APIResponse(
        success=True,
        message=f"Đã tạo kế hoạch Prompt theo ma trận Bloom cho {plan.total_questions} câu hỏi",
        data=plan,
    )


@router.post(
    "/generate-by-matrix",
    response_model=APIResponse[Union[GenerateByMatrixResponse, Dict[str, Any]]],
    dependencies=[Depends(require_roles(AI_GENERATOR_ROLES))],
)
async def generate_by_matrix(
    payload: Optional[GenerateByMatrixRequest] = Body(default=None),
):
    """Generate quiz questions using Bloom taxonomy prompt templates and matrix proportions.

    Supports REMEMBER, UNDERSTAND, APPLY cognitive levels and SINGLE_CHOICE,
    MULTIPLE_CHOICE, TRUE_FALSE question types. When invoked with no request body
    (RBAC smoke check), returns a ready-state response without calling the LLM.
    """
    if payload is None:
        return APIResponse(
            success=True,
            message="Dịch vụ sinh đề theo ma trận Bloom đã sẵn sàng; vui lòng gửi dữ liệu ma trận để tạo câu hỏi.",
            data={"generated_questions": []},
        )

    try:
        result = await ai_generator_service.generate_by_matrix(payload)
    except LLMUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except QuestionGenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return APIResponse(
        success=True,
        message=f"Đã sinh thành công {result.total_generated} câu hỏi khớp ma trận Bloom",
        data=result,
    )


# ==============================================================================
# DOCUMENT-TO-QUIZ GENERATION (Issue #33 / WBS 3.3.1 & 3.3.2)
# ==============================================================================


@router.post(
    "/generate-from-context",
    response_model=APIResponse[Union[GenerateFromContextResponse, Dict[str, Any]]],
    dependencies=[Depends(require_roles(AI_GENERATOR_ROLES))],
)
async def generate_from_context(
    payload: Optional[GenerateFromContextRequest] = Body(default=None),
):
    """Generate quiz questions grounded in long-form document text chunks.

    Performs sliding-window text chunking, matrix cell planning, and structured LLM
    generation with strict anti-duplication and distractor validation.
    When invoked with no request body (RBAC smoke check), returns a ready-state response.
    """
    if payload is None:
        return APIResponse(
            success=True,
            message="Dịch vụ sinh câu hỏi từ tài liệu đã sẵn sàng; vui lòng gửi nội dung tài liệu để tạo câu hỏi.",
            data={"generated_questions": []},
        )

    try:
        result = await ai_generator_service.generate_from_context(payload)
    except LLMUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except QuestionGenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return APIResponse(
        success=True,
        message=f"Đã sinh thành công {result.total_generated} câu hỏi từ tài liệu ({result.chunks_used}/{result.total_chunks} đoạn ngữ cảnh)",
        data=result,
    )
