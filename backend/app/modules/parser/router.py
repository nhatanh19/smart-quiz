from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import ValidationError
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.entities import (
    Category,
    CognitiveLevel,
    Question,
    QuestionLevel,
    QuestionType,
    Subject,
    User,
    UserRole,
)
from app.schemas.common import (
    APIResponse,
    CategoryCreateSchema,
    CategoryResponseSchema,
    CategoryUpdateSchema,
    HealthCheckResponse,
    QuestionCreateSchema,
    QuestionResponseSchema,
    QuestionUpdateSchema,
    SubjectCreateSchema,
    SubjectResponseSchema,
)

router = APIRouter(prefix="/parser", tags=["Module 1: File Parser & Question Bank (Dev 1)"])
QUESTION_BANK_ROLES = [UserRole.ADMIN, UserRole.INSTRUCTOR]


@router.get("/health", response_model=HealthCheckResponse)
def parser_health_check():
    """Health check endpoint for File Parser & Question Bank module."""
    return HealthCheckResponse(service="File Parser & Question Bank Service")


@router.post("/upload", response_model=APIResponse[dict])
async def upload_document_placeholder(file: UploadFile = File(None)):
    """Upload document placeholder.

    // TODO: Dev 1 - Implement file upload stream handling, extract raw text
    // using PyMuPDF (fitz) for PDF, python-docx for DOCX, or direct read for TXT.
    // Parse questions, choices, and answers using regular expressions.
    """
    return APIResponse(
        success=True,
        message="// TODO: Dev 1 - Implement document parsing (PDF/DOCX/TXT) logic",
        data={"filename": file.filename if file else "sample.pdf", "parsed_count": 0},
    )


def _question_query(db: Session, current_user: User):
    query = db.query(Question)
    if current_user.role != UserRole.ADMIN:
        query = query.filter(Question.creator_id == current_user.id)
    return query


def _ensure_category_access(
    db: Session, category_id: UUID, current_user: User
) -> None:
    query = db.query(Category).filter(Category.id == category_id)
    if current_user.role != UserRole.ADMIN:
        query = query.filter(Category.created_by == current_user.id)
    if query.first() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )


def _ensure_subject_access(
    db: Session, subject_id: UUID, current_user: User
) -> Subject:
    query = db.query(Subject).filter(Subject.id == subject_id)
    if current_user.role != UserRole.ADMIN:
        query = query.filter(Subject.created_by == current_user.id)
    subject = query.first()
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found",
        )
    return subject


def _get_question_or_404(
    db: Session, question_id: UUID, current_user: User
) -> Question:
    question = (
        _question_query(db, current_user)
        .filter(Question.id == question_id)
        .first()
    )
    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found",
        )
    return question


@router.get("/questions", response_model=APIResponse[list[QuestionResponseSchema]])
def list_questions(
    category_id: Optional[UUID] = None,
    level: Optional[QuestionLevel] = None,
    subject_id: Optional[UUID] = None,
    cognitive_level: Optional[CognitiveLevel] = None,
    question_type: Optional[QuestionType] = None,
    tag: Optional[str] = Query(default=None, min_length=1, max_length=40),
    keyword: Optional[str] = Query(default=None, min_length=1, max_length=200),
    search: Optional[str] = Query(default=None, min_length=1, max_length=200),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(QUESTION_BANK_ROLES)),
):
    """List the current user's questions with filters and pagination."""
    statement = select(Question).join(Category)
    if current_user.role != UserRole.ADMIN:
        statement = statement.where(Question.creator_id == current_user.id)
    if category_id is not None:
        statement = statement.where(Question.category_id == category_id)
    if subject_id is not None:
        statement = statement.where(Category.subject_id == subject_id)
    if level is not None:
        statement = statement.where(Question.level == level)
    if cognitive_level is not None:
        statement = statement.where(Question.cognitive_level == cognitive_level)
    if question_type is not None:
        statement = statement.where(Question.question_type == question_type)
    if tag is not None:
        tag = tag.strip()
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Tag filter must not be blank",
            )
        statement = statement.where(Question.tags.contains([tag]))
    if keyword is not None:
        keyword = keyword.strip()
        if not keyword:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Keyword must not be blank",
            )
        statement = statement.where(Question.content.ilike(f"%{keyword}%"))
    if search is not None:
        search = search.strip()
        if not search:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Search keyword must not be blank",
            )
        keyword = f"%{search}%"
        statement = statement.where(
            or_(
                Question.content.ilike(keyword),
                Question.explanation.ilike(keyword),
                Category.name.ilike(keyword),
            )
        )

    questions = db.scalars(
        statement.order_by(Question.created_at.desc(), Question.id.desc())
        .offset(skip)
        .limit(limit)
    ).all()
    return APIResponse(
        success=True,
        message="Questions retrieved successfully",
        data=questions,
    )


@router.get(
    "/questions/{question_id}",
    response_model=APIResponse[QuestionResponseSchema],
)
def get_question(
    question_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(QUESTION_BANK_ROLES)),
):
    question = _get_question_or_404(db, question_id, current_user)
    return APIResponse(
        success=True,
        message="Question retrieved successfully",
        data=question,
    )


@router.post(
    "/questions",
    response_model=APIResponse[QuestionResponseSchema],
    status_code=status.HTTP_201_CREATED,
)
def create_question(
    payload: QuestionCreateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(QUESTION_BANK_ROLES)),
):
    _ensure_category_access(db, payload.category_id, current_user)
    question = Question(
        **payload.model_dump(),
        creator_id=current_user.id,
    )
    db.add(question)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Question could not be saved because a related record changed",
        ) from exc
    db.refresh(question)
    return APIResponse(
        success=True,
        message="Question created successfully",
        data=question,
    )


@router.patch(
    "/questions/{question_id}",
    response_model=APIResponse[QuestionResponseSchema],
)
def update_question(
    question_id: UUID,
    payload: QuestionUpdateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(QUESTION_BANK_ROLES)),
):
    question = _get_question_or_404(db, question_id, current_user)
    updates = payload.model_dump(exclude_unset=True)
    updated_data = {
        "category_id": question.category_id,
        "content": question.content,
        "question_type": question.question_type,
        "cognitive_level": question.cognitive_level,
        "level": question.level,
        "options": question.options,
        "tags": question.tags,
        "explanation": question.explanation,
        **updates,
    }
    try:
        validated = QuestionCreateSchema.model_validate(updated_data)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.errors(include_context=False, include_input=False),
        ) from exc
    if "category_id" in updates:
        _ensure_category_access(db, validated.category_id, current_user)

    for field, value in validated.model_dump().items():
        setattr(question, field, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Question could not be updated because a related record changed",
        ) from exc
    db.refresh(question)
    return APIResponse(
        success=True,
        message="Question updated successfully",
        data=question,
    )


@router.delete(
    "/questions/{question_id}",
    response_model=APIResponse[dict],
)
def delete_question(
    question_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(QUESTION_BANK_ROLES)),
):
    question = _get_question_or_404(db, question_id, current_user)
    question_id_value = question.id
    db.delete(question)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Question is referenced by an exam or answer and cannot be deleted",
        ) from exc
    return APIResponse(
        success=True,
        message="Question deleted successfully",
        data={"id": question_id_value, "deleted": True},
    )


@router.get(
    "/subjects",
    response_model=APIResponse[list[SubjectResponseSchema]],
)
def list_subjects(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(QUESTION_BANK_ROLES)),
):
    query = db.query(Subject)
    if current_user.role != UserRole.ADMIN:
        query = query.filter(Subject.created_by == current_user.id)
    return APIResponse(
        success=True,
        message="Subjects retrieved successfully",
        data=query.order_by(Subject.name.asc()).all(),
    )


@router.post(
    "/subjects",
    response_model=APIResponse[SubjectResponseSchema],
    status_code=status.HTTP_201_CREATED,
)
def create_subject(
    payload: SubjectCreateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(QUESTION_BANK_ROLES)),
):
    subject = Subject(**payload.model_dump(), created_by=current_user.id)
    db.add(subject)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A subject with this name already exists",
        ) from exc
    db.refresh(subject)
    return APIResponse(
        success=True,
        message="Subject created successfully",
        data=subject,
    )


@router.get(
    "/categories",
    response_model=APIResponse[list[CategoryResponseSchema]],
)
def list_categories(
    subject_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(QUESTION_BANK_ROLES)),
):
    query = db.query(Category)
    if current_user.role != UserRole.ADMIN:
        query = query.filter(Category.created_by == current_user.id)
    if subject_id is not None:
        query = query.filter(Category.subject_id == subject_id)
    return APIResponse(
        success=True,
        message="Topics retrieved successfully",
        data=query.order_by(Category.name.asc()).all(),
    )


@router.post(
    "/categories",
    response_model=APIResponse[CategoryResponseSchema],
    status_code=status.HTTP_201_CREATED,
)
def create_category(
    payload: CategoryCreateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(QUESTION_BANK_ROLES)),
):
    _ensure_subject_access(db, payload.subject_id, current_user)
    category = Category(**payload.model_dump(), created_by=current_user.id)
    db.add(category)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A topic with this name already exists",
        ) from exc
    db.refresh(category)
    return APIResponse(
        success=True,
        message="Topic created successfully",
        data=category,
    )


@router.patch(
    "/categories/{category_id}",
    response_model=APIResponse[CategoryResponseSchema],
)
def update_category(
    category_id: UUID,
    payload: CategoryUpdateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(QUESTION_BANK_ROLES)),
):
    query = db.query(Category).filter(Category.id == category_id)
    if current_user.role != UserRole.ADMIN:
        query = query.filter(Category.created_by == current_user.id)
    category = query.first()
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found",
        )

    updates = payload.model_dump(exclude_unset=True)
    if "subject_id" in updates and updates["subject_id"] is not None:
        _ensure_subject_access(db, updates["subject_id"], current_user)
    for field, value in updates.items():
        setattr(category, field, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Topic could not be updated because a related record changed",
        ) from exc
    db.refresh(category)
    return APIResponse(
        success=True,
        message="Topic updated successfully",
        data=category,
    )
