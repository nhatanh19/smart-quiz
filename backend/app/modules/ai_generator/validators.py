"""Quality, anti-duplication, and matrix validation for AI-generated questions (Issue #11)."""

import re
import string
from typing import Iterable, List, Optional, Sequence, Set, Tuple

from app.models.entities import CognitiveLevel, QuestionSource, QuestionType
from app.modules.ai_generator.prompts import COGNITIVE_TO_DEFAULT_LEVEL
from app.modules.ai_generator.schemas import (
    GeneratedOptionItem,
    GeneratedQuestionItem,
    LLMGeneratedQuestionSchema,
)

OPTION_PREFIX_RE = re.compile(r"^\s*(?:[A-Ha-h]|[1-8])[\.\)\:]\s+")
WHITESPACE_RE = re.compile(r"\s+")
PUNCT_TRANS = str.maketrans("", "", string.punctuation + "“”‘’…–—")

BANNED_OPTION_PATTERNS = (
    re.compile(r"^\s*tất cả\s+(các\s+)?(đáp án|phương án|lựa chọn|ý|câu)(\s+trên)?(\s+đều)?(\s+(đúng|sai))?\s*$", re.IGNORECASE),
    re.compile(r"^\s*tất cả\s+đều\s+(đúng|sai)\s*$", re.IGNORECASE),
    re.compile(r"^\s*không có\s+(đáp án|phương án|lựa chọn|ý)(\s+nào)?(\s+đúng)?\s*$", re.IGNORECASE),
    re.compile(r"^\s*cả\s+[a-e](\s*(,|và|lẫn)\s*[a-e])+(\s+(đều\s+)?(đúng|sai))?\s*$", re.IGNORECASE),
    re.compile(r"^\s*chỉ\s+[a-e](\s*(,|và)\s*[a-e])+(\s+đúng)?\s*$", re.IGNORECASE),
    re.compile(r"^\s*all\s+of\s+the\s+above\s*$", re.IGNORECASE),
    re.compile(r"^\s*none\s+of\s+the\s+above\s*$", re.IGNORECASE),
    re.compile(r"^\s*both\s+[a-e]\s+and\s+[a-e]\s*$", re.IGNORECASE),
)

OPTION_LABELS = ("A", "B", "C", "D", "E", "F", "G", "H")


class QuestionValidationError(ValueError):
    """Raised when a generated question fails structural or distractor quality checks."""


def normalize_for_comparison(text: str) -> str:
    """Normalize text for duplicate detection (strip option prefix, punctuation, case, spaces)."""
    cleaned = OPTION_PREFIX_RE.sub("", text or "").strip()
    cleaned = cleaned.translate(PUNCT_TRANS)
    cleaned = WHITESPACE_RE.sub(" ", cleaned).strip().casefold()
    return cleaned


def is_banned_lazy_option(text: str) -> bool:
    """Return True if an option uses banned meta-choices like 'All of the above'."""
    cleaned = OPTION_PREFIX_RE.sub("", text or "").strip()
    cleaned = cleaned.rstrip(".!?:; ")
    return any(pattern.match(cleaned) for pattern in BANNED_OPTION_PATTERNS)


def _normalize_tags(raw_tags: Sequence[str]) -> List[str]:
    normalized: List[str] = []
    seen: Set[str] = set()
    for tag in raw_tags:
        if not isinstance(tag, str):
            continue
        cleaned = tag.strip()
        if not cleaned or len(cleaned) > 40:
            continue
        key = cleaned.casefold()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(cleaned)
        if len(normalized) >= 20:
            break
    return normalized


def validate_and_normalize_question(
    raw: LLMGeneratedQuestionSchema,
    *,
    expected_cognitive_level: CognitiveLevel,
    expected_question_type: QuestionType,
    existing_normalized_stems: Optional[Iterable[str]] = None,
    category_id=None,
) -> GeneratedQuestionItem:
    """Validate one LLM-generated question against Bloom, type, and distractor rules."""
    if raw.cognitive_level != expected_cognitive_level:
        raise QuestionValidationError(
            f"Mức độ nhận thức không khớp: yêu cầu {expected_cognitive_level.value}, nhận được {raw.cognitive_level.value}"
        )
    if raw.question_type != expected_question_type:
        raise QuestionValidationError(
            f"Thể loại câu hỏi không khớp: yêu cầu {expected_question_type.value}, nhận được {raw.question_type.value}"
        )

    content = WHITESPACE_RE.sub(" ", (raw.content or "")).strip()
    if len(content) < 8:
        raise QuestionValidationError("Nội dung câu hỏi quá ngắn hoặc bị trống")

    stem_key = normalize_for_comparison(content)
    if not stem_key:
        raise QuestionValidationError("Nội dung câu hỏi không chứa văn bản hợp lệ")

    if existing_normalized_stems is not None and stem_key in set(existing_normalized_stems):
        raise QuestionValidationError("Phát hiện câu hỏi bị trùng lặp nội dung")

    if not raw.options:
        raise QuestionValidationError("Câu hỏi không có phương án trả lời")

    normalized_options: List[GeneratedOptionItem] = []
    seen_option_texts: Set[str] = set()

    for idx, opt in enumerate(raw.options):
        if idx >= len(OPTION_LABELS):
            raise QuestionValidationError("Số lượng phương án vượt quá giới hạn cho phép")

        opt_text = WHITESPACE_RE.sub(" ", (opt.text or "")).strip()
        if expected_question_type != QuestionType.TRUE_FALSE:
            stripped_prefix = OPTION_PREFIX_RE.sub("", opt_text).strip()
            if stripped_prefix:
                opt_text = stripped_prefix

        if not opt_text:
            raise QuestionValidationError(f"Phương án thứ {idx + 1} bị trống")

        if is_banned_lazy_option(opt_text):
            raise QuestionValidationError(
                f"Phát hiện phương án sáo rỗng bị cấm: '{opt_text}'"
            )

        norm_opt = normalize_for_comparison(opt_text)
        if not norm_opt:
            raise QuestionValidationError(f"Phương án thứ {idx + 1} không chứa nội dung hợp lệ")
        if norm_opt == stem_key:
            raise QuestionValidationError("Nội dung phương án lặp lại nội dung câu hỏi")
        if norm_opt in seen_option_texts:
            raise QuestionValidationError(
                f"Phát hiện phương án bị trùng lặp nội dung: '{opt_text}'"
            )
        seen_option_texts.add(norm_opt)

        normalized_options.append(
            GeneratedOptionItem(
                id=OPTION_LABELS[idx],
                text=opt_text,
                is_correct=bool(opt.is_correct),
            )
        )

    option_count = len(normalized_options)
    correct_count = sum(1 for o in normalized_options if o.is_correct)

    if expected_question_type == QuestionType.SINGLE_CHOICE:
        if not (3 <= option_count <= 6):
            raise QuestionValidationError(
                f"Câu hỏi một đáp án (SINGLE_CHOICE) cần từ 3 đến 6 phương án (khuyến nghị 4), hiện có {option_count}"
            )
        if correct_count != 1:
            raise QuestionValidationError(
                f"Câu hỏi một đáp án (SINGLE_CHOICE) phải có đúng 1 đáp án đúng, hiện có {correct_count}"
            )
    elif expected_question_type == QuestionType.MULTIPLE_CHOICE:
        if not (3 <= option_count <= 8):
            raise QuestionValidationError(
                f"Câu hỏi nhiều đáp án (MULTIPLE_CHOICE) cần từ 3 đến 8 phương án, hiện có {option_count}"
            )
        if correct_count < 2 or correct_count >= option_count:
            raise QuestionValidationError(
                f"Câu hỏi nhiều đáp án (MULTIPLE_CHOICE) phải có từ 2 đến {option_count - 1} đáp án đúng, hiện có {correct_count}"
            )
    elif expected_question_type == QuestionType.TRUE_FALSE:
        if option_count != 2:
            raise QuestionValidationError(
                f"Câu hỏi Đúng/Sai (TRUE_FALSE) phải có chính xác 2 phương án, hiện có {option_count}"
            )
        if correct_count != 1:
            raise QuestionValidationError(
                f"Câu hỏi Đúng/Sai (TRUE_FALSE) phải có đúng 1 đáp án đúng, hiện có {correct_count}"
            )
        option_pair = {normalize_for_comparison(o.text) for o in normalized_options}
        if option_pair not in ({"đúng", "sai"}, {"true", "false"}):
            raise QuestionValidationError(
                "Các phương án của câu Đúng/Sai (TRUE_FALSE) phải là 'Đúng'/'Sai' hoặc 'True'/'False'"
            )

    explanation = WHITESPACE_RE.sub(" ", (raw.explanation or "")).strip()
    if not explanation:
        correct_labels = ", ".join(o.id for o in normalized_options if o.is_correct)
        explanation = f"Đáp án đúng là phương án {correct_labels}."

    level = raw.level or COGNITIVE_TO_DEFAULT_LEVEL[expected_cognitive_level]
    tags = _normalize_tags(raw.tags)

    return GeneratedQuestionItem(
        category_id=category_id,
        content=content,
        question_type=expected_question_type,
        cognitive_level=expected_cognitive_level,
        level=level,
        options=normalized_options,
        tags=tags,
        explanation=explanation,
        source_type=QuestionSource.AI_GENERATED,
    )


def filter_valid_questions(
    raw_items: Sequence[LLMGeneratedQuestionSchema],
    *,
    expected_cognitive_level: CognitiveLevel,
    expected_question_type: QuestionType,
    existing_normalized_stems: Set[str],
    limit: int,
    category_id=None,
) -> Tuple[List[GeneratedQuestionItem], List[str]]:
    """Validate a batch of LLM questions, returning accepted items and rejection reasons."""
    accepted: List[GeneratedQuestionItem] = []
    rejection_reasons: List[str] = []

    for item in raw_items:
        if len(accepted) >= limit:
            break
        try:
            validated = validate_and_normalize_question(
                item,
                expected_cognitive_level=expected_cognitive_level,
                expected_question_type=expected_question_type,
                existing_normalized_stems=existing_normalized_stems,
                category_id=category_id,
            )
        except QuestionValidationError as exc:
            rejection_reasons.append(str(exc))
            continue

        existing_normalized_stems.add(normalize_for_comparison(validated.content))
        accepted.append(validated)

    return accepted, rejection_reasons
