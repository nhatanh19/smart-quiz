"""Regex Pattern Matching Engine for structured quiz extraction (Issue #6 / WBS 2.1.2).

Converts raw UTF-8 text (and optional DOCX formatting hints) extracted from PDF,
DOCX, and TXT documents into normalized question objects compatible with the
PostgreSQL `questions` schema (`source_type = FILE_PARSER`).
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Set, Tuple

from app.models.entities import (
    CognitiveLevel,
    QuestionLevel,
    QuestionSource,
    QuestionType,
)
from app.modules.parser.schemas import (
    ParsedOptionSchema,
    ParsedQuestionBatchResult,
    ParsedQuestionSchema,
    ParseStatisticsSchema,
)

SpanRange = Tuple[int, int]

# ---------------------------------------------------------------------------
# Pre-compiled Regular Expression Patterns
# ---------------------------------------------------------------------------

PAGE_NOISE_RE = re.compile(
    r"^\s*(?:(?:Trang|Page)\s+\d+(?:\s*(?:/|of)\s*\d+)?|[-_=*]{4,})\s*$",
    re.IGNORECASE,
)

ANSWER_KEY_HEADER_RE = re.compile(
    r"^\s*(?:BẢNG\s+ĐÁP\s+ÁN|ĐÁP\s+ÁN(?:\s+ĐỀ\s+THI|\s+THAM\s+KHẢO|\s+CHI\s+TIẾT|\s+CHÍNH\s+THỨC)?|ANSWER\s+KEY)\s*[:\-–—]?\s*$",
    re.IGNORECASE,
)

ANSWER_KEY_PAIR_RE = re.compile(
    r"(?:(?:Câu(?:\s+hỏi)?(?:\s+số)?|Question|Bài|Q\.?)\s*)?"
    r"(\d{1,4})\s*"
    r"(?:[\.\)\:\-\|]|=>)\s*"
    r"([A-Ja-j](?:\s*(?:,|&|\+|và|/)\s*[A-Ja-j])*|[A-Ja-j]{2,4})"
    r"(?=\s|$|\||,|;)",
    re.IGNORECASE,
)

EXPLICIT_QUESTION_HEADER_RE = re.compile(
    r"^\s*(?:Câu(?:\s+hỏi)?(?:\s+số)?|Question|Bài|Q\.?)\s*(\d{1,4})"
    r"(?:\s*[:\.\)\-–—]+\s*(.*)|\s+([A-ZÀ-Ỹ\"'\(\[].*)|\s*$)",
    re.IGNORECASE,
)

NUMERIC_QUESTION_HEADER_RE = re.compile(r"^\s*(\d{1,3})\s*[\.\)]\s+(\S.*)$")

ANSWER_LINE_RE = re.compile(
    r"^\s*(?:Đáp\s+án(?:\s+đúng|\s+chuẩn)?|ĐA|DA|Answer(?:\s+Key)?|Correct(?:\s+Answer)?|Key)\s*[:\-–—]\s*(.+)$",
    re.IGNORECASE,
)

STANDALONE_MARKED_LETTER_RE = re.compile(
    r"^\s*[*✓✔☑]\s*\(?([A-Ja-j])\)?[\.\)]?\s*$"
)

EXPLANATION_LINE_RE = re.compile(
    r"^\s*(?:Lời\s+giải(?:\s+chi\s+tiết)?|Giải\s+thích|Hướng\s+dẫn(?:\s+giải)?|Ghi\s+chú|Chú\s+thích|Explanation|Solution|Rationale|Note)\s*[:\-–—]\s*(.*)$",
    re.IGNORECASE,
)

OPTION_TOKEN_RE = re.compile(
    r"(?:(?P<marker>[*✓✔☑]|\[[xX✓✔]\]|\([xX✓✔]\))\s*)?"
    r"(?:\((?P<paren_id>[A-Ja-j])\)|(?P<plain_id>[A-Ja-j])\s*(?P<delim>[\.\)\:\-]))"
    r"(?=\s+|\s*$)"
)

INLINE_CORRECT_SUFFIX_RE = re.compile(
    r"\s*(?:\(\s*(?:đúng|correct|✓|✔|x)\s*\)|\[\s*(?:đúng|correct|✓|✔|x)\s*\])\s*$",
    re.IGNORECASE,
)

TRAILING_STAR_SUFFIX_RE = re.compile(r"\s*\*\s*$")

COGNITIVE_TAG_RE = re.compile(
    r"^\s*[\[\(]\s*(NB|Nhận\s*biết|TH|Thông\s*hiểu|VD|Vận\s*dụng|VDT|VDC|REMEMBER|UNDERSTAND|APPLY)\s*[\]\)]\s*",
    re.IGNORECASE,
)

LEVEL_TAG_RE = re.compile(
    r"^\s*[\[\(]\s*(Dễ|Trung\s*bình|TB|Khó|EASY|MEDIUM|HARD)\s*[\]\)]\s*",
    re.IGNORECASE,
)

WHITESPACE_INLINE_RE = re.compile(r"[ \t]+")


@dataclass
class _LineRecord:
    orig_idx: int
    text: str


@dataclass
class _RawBlock:
    question_number: Optional[int]
    lines: List[Tuple[int, str, int]]  # (orig_line_idx, text, col_offset_in_orig_line)


@dataclass
class _OptionDraft:
    id: str
    text_parts: List[str] = field(default_factory=list)
    inline_marked: bool = False
    docx_marked: bool = False


def _collapse_spaces(value: str) -> str:
    return WHITESPACE_INLINE_RE.sub(" ", value).strip()


def _parse_cognitive_and_level_tags(stem: str) -> Tuple[str, CognitiveLevel, QuestionLevel, List[str]]:
    """Extract optional leading Bloom/difficulty brackets from a stem."""
    cleaned = stem.lstrip()
    cognitive = CognitiveLevel.REMEMBER
    level = QuestionLevel.MEDIUM
    tags: List[str] = []

    cog_map = {
        "nb": CognitiveLevel.REMEMBER,
        "nhận biết": CognitiveLevel.REMEMBER,
        "remember": CognitiveLevel.REMEMBER,
        "th": CognitiveLevel.UNDERSTAND,
        "thông hiểu": CognitiveLevel.UNDERSTAND,
        "understand": CognitiveLevel.UNDERSTAND,
        "vd": CognitiveLevel.APPLY,
        "vận dụng": CognitiveLevel.APPLY,
        "vdt": CognitiveLevel.APPLY,
        "vdc": CognitiveLevel.APPLY,
        "apply": CognitiveLevel.APPLY,
    }
    lvl_map = {
        "dễ": QuestionLevel.EASY,
        "easy": QuestionLevel.EASY,
        "tb": QuestionLevel.MEDIUM,
        "trung bình": QuestionLevel.MEDIUM,
        "medium": QuestionLevel.MEDIUM,
        "khó": QuestionLevel.HARD,
        "hard": QuestionLevel.HARD,
    }

    for _ in range(2):
        cog_match = COGNITIVE_TAG_RE.match(cleaned)
        if cog_match:
            key = _collapse_spaces(cog_match.group(1)).casefold()
            if key in cog_map:
                cognitive = cog_map[key]
                tags.append(cog_match.group(1).strip())
            cleaned = cleaned[cog_match.end():].lstrip(" \t:.-–—")
            continue

        lvl_match = LEVEL_TAG_RE.match(cleaned)
        if lvl_match:
            key = _collapse_spaces(lvl_match.group(1)).casefold()
            if key in lvl_map:
                level = lvl_map[key]
                tags.append(lvl_match.group(1).strip())
            cleaned = cleaned[lvl_match.end():].lstrip(" \t:.-–—")
            continue
        break

    return cleaned, cognitive, level, tags


class RegexQuestionParserService:
    """Service that parses raw exam text into structured quiz questions using Regex."""

    @classmethod
    def parse(
        cls,
        raw_text: str,
        *,
        filename: Optional[str] = None,
        line_marked_spans: Optional[Dict[int, List[SpanRange]]] = None,
    ) -> ParsedQuestionBatchResult:
        """Parse extracted document text into normalized question objects.

        Args:
            raw_text: Extracted UTF-8 document text.
            filename: Optional source document name.
            line_marked_spans: Optional mapping of 0-based line indices in `raw_text`
                to underlined/highlighted character intervals (from DOCX extraction).

        Returns:
            ParsedQuestionBatchResult containing normalized questions and statistics.
        """
        if not raw_text or not raw_text.strip():
            return ParsedQuestionBatchResult(
                filename=filename,
                questions=[],
                statistics=ParseStatisticsSchema(),
                warnings=["Văn bản đầu vào trống, không tìm thấy câu hỏi."],
            )

        marked_spans = line_marked_spans or {}
        lines = cls._preprocess_lines(raw_text)
        question_lines, trailing_keys = cls._extract_trailing_answer_key(lines)
        blocks = cls._split_question_blocks(question_lines)

        parsed_questions: List[ParsedQuestionSchema] = []
        used_trailing_keys: Set[int] = set()

        for idx, block in enumerate(blocks, start=1):
            question = cls._parse_single_block(
                block=block,
                fallback_number=idx,
                marked_spans=marked_spans,
                trailing_keys=trailing_keys,
                used_trailing_keys=used_trailing_keys,
            )
            if question is not None:
                parsed_questions.append(question)

        unmatched_keys = {
            q_num: letters
            for q_num, letters in trailing_keys.items()
            if q_num not in used_trailing_keys
        }

        batch_warnings: List[str] = []
        if not parsed_questions:
            batch_warnings.append(
                "Không nhận diện được câu hỏi trắc nghiệm nào theo định dạng chuẩn (ví dụ: 'Câu 1:', '1.', 'A. B. C. D.')."
            )
        elif unmatched_keys:
            batch_warnings.append(
                f"Có {len(unmatched_keys)} mục trong bảng đáp án cuối đề không khớp với số thứ tự câu hỏi đã tách."
            )

        stats = cls._compute_statistics(
            total_blocks=len(blocks),
            questions=parsed_questions,
        )

        return ParsedQuestionBatchResult(
            filename=filename,
            questions=parsed_questions,
            statistics=stats,
            unmatched_answer_keys=unmatched_keys,
            warnings=batch_warnings,
        )

    @staticmethod
    def _preprocess_lines(raw_text: str) -> List[_LineRecord]:
        normalized = unicodedata.normalize(
            "NFC", raw_text.replace("\r\n", "\n").replace("\r", "\n")
        )
        records: List[_LineRecord] = []
        for idx, line in enumerate(normalized.split("\n")):
            if not line.strip():
                continue
            if PAGE_NOISE_RE.match(line):
                continue
            records.append(_LineRecord(orig_idx=idx, text=line))
        return records

    @staticmethod
    def _parse_answer_letters(expr: str) -> List[str]:
        """Parse one or more option IDs (e.g. 'A', 'A, C', 'A & D', 'AC') preserving order."""
        cleaned = expr.strip()
        if not cleaned:
            return []

        # Strip common trailing notes inside parentheses after an option letter e.g. "A (vì ...)"
        single_or_list = re.split(
            r"(?:\s*(?:,|&|\+|và|and|/|;)\s*)", cleaned, flags=re.IGNORECASE
        )
        letters: List[str] = []

        if len(single_or_list) == 1 and re.fullmatch(r"[A-Ja-j]{2,4}", cleaned):
            for ch in cleaned.upper():
                if ch not in letters:
                    letters.append(ch)
            return letters

        for part in single_or_list:
            part_match = re.match(r"^\s*\(?([A-Ja-j])\)?(?:[\.\)\s]|$)", part)
            if part_match:
                ch = part_match.group(1).upper()
                if ch not in letters:
                    letters.append(ch)

        if not letters:
            # Handle inline multi-token letters like "A B" or "A. (explanation...)"
            first_match = re.match(r"^\s*\(?([A-Ja-j])\)?(?=[\.\)\:\s]|$)", cleaned)
            if first_match:
                letters.append(first_match.group(1).upper())

        return letters

    @classmethod
    def _extract_trailing_answer_key(
        cls, lines: List[_LineRecord]
    ) -> Tuple[List[_LineRecord], Dict[int, List[str]]]:
        """Detect an answer-key table at the bottom of the document and strip it from questions."""
        has_question_earlier = False
        candidate_header_idx: Optional[int] = None

        for pos, rec in enumerate(lines):
            if EXPLICIT_QUESTION_HEADER_RE.match(rec.text) or NUMERIC_QUESTION_HEADER_RE.match(rec.text):
                has_question_earlier = True
            elif has_question_earlier:
                if ANSWER_KEY_HEADER_RE.match(rec.text):
                    candidate_header_idx = pos
                elif ANSWER_LINE_RE.match(rec.text) and len(ANSWER_KEY_PAIR_RE.findall(rec.text)) >= 2:
                    candidate_header_idx = pos

        if candidate_header_idx is None:
            return lines, {}

        key_map: Dict[int, List[str]] = {}
        for rec in lines[candidate_header_idx:]:
            for match in ANSWER_KEY_PAIR_RE.finditer(rec.text):
                q_num = int(match.group(1))
                letters = cls._parse_answer_letters(match.group(2))
                if letters:
                    key_map[q_num] = letters

        if len(key_map) < 2:
            # Avoid accidentally discarding content if only 0-1 pairs matched
            return lines, {}

        return lines[:candidate_header_idx], key_map

    @classmethod
    def _split_question_blocks(cls, lines: List[_LineRecord]) -> List[_RawBlock]:
        """Group preprocessed lines into discrete question blocks."""
        has_explicit_headers = any(
            EXPLICIT_QUESTION_HEADER_RE.match(rec.text) for rec in lines
        )

        # Precompute candidate numeric question start positions if needed
        numeric_start_indices: Set[int] = set()
        if not has_explicit_headers:
            candidate_positions: List[Tuple[int, int]] = []
            for idx, rec in enumerate(lines):
                m = NUMERIC_QUESTION_HEADER_RE.match(rec.text)
                if m:
                    candidate_positions.append((idx, int(m.group(1))))

            for c_pos, (line_pos, q_num) in enumerate(candidate_positions):
                next_line_pos = (
                    candidate_positions[c_pos + 1][0]
                    if c_pos + 1 < len(candidate_positions)
                    else len(lines)
                )
                segment_has_options = any(
                    cls._line_starts_with_option_a(lines[k].text)
                    for k in range(line_pos, next_line_pos)
                )
                if segment_has_options or (q_num == 1 and not numeric_start_indices):
                    numeric_start_indices.add(line_pos)
                elif numeric_start_indices:
                    # Keep sequential numeric headers even if one question missed options cleanly
                    prev_nums = [
                        int(NUMERIC_QUESTION_HEADER_RE.match(lines[i].text).group(1))
                        for i in numeric_start_indices
                    ]
                    if q_num == max(prev_nums) + 1:
                        numeric_start_indices.add(line_pos)

        blocks: List[_RawBlock] = []
        current_block: Optional[_RawBlock] = None

        for idx, rec in enumerate(lines):
            explicit_match = EXPLICIT_QUESTION_HEADER_RE.match(rec.text)
            if explicit_match:
                q_num = int(explicit_match.group(1))
                rest_text = explicit_match.group(2) if explicit_match.group(2) is not None else explicit_match.group(3)
                rest_text = rest_text or ""
                col_offset = (
                    explicit_match.start(2)
                    if explicit_match.group(2) is not None
                    else (explicit_match.start(3) if explicit_match.group(3) is not None else len(rec.text))
                )
                if current_block is not None:
                    blocks.append(current_block)
                initial_lines: List[Tuple[int, str, int]] = []
                if rest_text.strip():
                    initial_lines.append((rec.orig_idx, rest_text, col_offset))
                current_block = _RawBlock(question_number=q_num, lines=initial_lines)
                continue

            if not has_explicit_headers and idx in numeric_start_indices:
                num_match = NUMERIC_QUESTION_HEADER_RE.match(rec.text)
                if num_match:
                    q_num = int(num_match.group(1))
                    rest_text = num_match.group(2)
                    col_offset = num_match.start(2)
                    if current_block is not None:
                        blocks.append(current_block)
                    current_block = _RawBlock(
                        question_number=q_num,
                        lines=[(rec.orig_idx, rest_text, col_offset)],
                    )
                    continue

            # Ignore document title/header banners appearing before Question 1
            if current_block is not None:
                current_block.lines.append((rec.orig_idx, rec.text, 0))

        if current_block is not None:
            blocks.append(current_block)

        return blocks

    @staticmethod
    def _line_starts_with_option_a(text: str) -> bool:
        m = OPTION_TOKEN_RE.match(text.lstrip())
        if not m:
            return False
        letter = (m.group("paren_id") or m.group("plain_id") or "").upper()
        return letter == "A"

    @staticmethod
    def _is_range_marked(
        spans: Sequence[SpanRange], check_start: int, check_end: int
    ) -> bool:
        for ms, me in spans:
            if min(me, check_end) > max(ms, check_start):
                return True
        return False

    @classmethod
    def _find_valid_option_tokens(
        cls,
        line: str,
        current_option_ids: Sequence[str],
    ) -> List[Tuple[int, int, str, bool]]:
        """Identify valid option start tokens on a single line while avoiding prose false positives.

        Returns list of `(token_start, content_start, letter, is_inline_marked)`.
        """
        candidates = list(OPTION_TOKEN_RE.finditer(line))
        if not candidates:
            return []

        expected_letters: Set[str] = set(current_option_ids)
        last_ord = ord(current_option_ids[-1]) if current_option_ids else (ord("A") - 1)
        accepted: List[Tuple[int, int, str, bool]] = []

        for idx, match in enumerate(candidates):
            letter = (match.group("paren_id") or match.group("plain_id") or "").upper()
            if letter in expected_letters:
                continue

            start_pos = match.start()
            prefix_before = line[:start_pos]
            is_at_line_start = not prefix_before.strip()

            # Check progression rules so inline abbreviations ("Grade A. Smith") aren't split
            if not current_option_ids and not accepted:
                if letter != "A":
                    continue
                if not is_at_line_start:
                    # Allow inline `Stem? A. opt1 B. opt2` only if preceded by ?, :, or >=2 spaces
                    # AND option B also appears later on this line.
                    has_stem_boundary = bool(re.search(r"[?:：]\s+$|\s{2,}$|\|\s*$", prefix_before))
                    has_next_b = any(
                        (c.group("paren_id") or c.group("plain_id") or "").upper() == "B"
                        and c.start() > match.end()
                        for c in candidates[idx + 1:]
                    )
                    if not (has_stem_boundary and has_next_b):
                        continue
            else:
                curr_ord = ord(letter)
                if curr_ord <= last_ord or curr_ord > last_ord + 2:
                    continue
                if not is_at_line_start:
                    # Inline separator check (pipe '|', tab, >=2 spaces, or sequential next letter)
                    is_separated = bool(
                        re.search(r"(?:\t|\s{2,}|\|\s*)$", prefix_before)
                    )
                    is_strictly_next = curr_ord == last_ord + 1
                    if not (is_separated or is_strictly_next):
                        continue
                    # Avoid splitting mid-word (e.g. "Q.A.")
                    if prefix_before and not prefix_before[-1].isspace() and prefix_before[-1] != "|":
                        continue

            has_inline_marker = bool(match.group("marker"))
            accepted.append((start_pos, match.end(), letter, has_inline_marker))
            expected_letters.add(letter)
            last_ord = ord(letter)

        return accepted

    @classmethod
    def _parse_single_block(
        cls,
        *,
        block: _RawBlock,
        fallback_number: int,
        marked_spans: Dict[int, List[SpanRange]],
        trailing_keys: Dict[int, List[str]],
        used_trailing_keys: Set[int],
    ) -> Optional[ParsedQuestionSchema]:
        """Parse stem, options, correct answers, and explanation inside a single question block."""
        stem_parts: List[str] = []
        options: List[_OptionDraft] = []
        explicit_answer_letters: List[str] = []
        explicit_answer_raw_text: Optional[str] = None
        explanation_parts: List[str] = []
        mode: str = "stem"  # "stem" | "options" | "explanation"

        for orig_idx, line_text, col_offset in block.lines:
            stripped = line_text.strip()
            if not stripped:
                continue

            # 1. Check explicit Explanation line
            exp_match = EXPLANATION_LINE_RE.match(stripped)
            if exp_match:
                mode = "explanation"
                exp_body = exp_match.group(1).strip()
                if exp_body:
                    explanation_parts.append(exp_body)
                continue

            # 2. Check explicit Answer line or standalone marked key like `*a.`
            ans_match = ANSWER_LINE_RE.match(stripped)
            if ans_match:
                raw_ans = ans_match.group(1).strip()
                explicit_answer_raw_text = raw_ans
                parsed_letters = cls._parse_answer_letters(raw_ans)
                for letter in parsed_letters:
                    if letter not in explicit_answer_letters:
                        explicit_answer_letters.append(letter)
                # Switch away from options if answer line appeared
                if mode == "options":
                    mode = "after_answer"
                continue

            if mode == "options":
                standalone_ans = STANDALONE_MARKED_LETTER_RE.match(stripped)
                if standalone_ans:
                    letter = standalone_ans.group(1).upper()
                    if letter not in explicit_answer_letters:
                        explicit_answer_letters.append(letter)
                    mode = "after_answer"
                    continue

            if mode == "explanation":
                explanation_parts.append(stripped)
                continue

            # 3. Scan for option tokens on the line
            seen_ids = [opt.id for opt in options]
            tokens = cls._find_valid_option_tokens(line_text, seen_ids)

            if tokens:
                mode = "options"
                # If this line also contains leading stem before the first inline option `A.`
                first_start = tokens[0][0]
                if not options and first_start > 0:
                    leading_stem = line_text[:first_start].strip()
                    if leading_stem:
                        stem_parts.append(leading_stem)

                orig_spans = marked_spans.get(orig_idx, [])
                for t_idx, (tok_start, content_start, letter, has_marker) in enumerate(tokens):
                    next_start = (
                        tokens[t_idx + 1][0]
                        if t_idx + 1 < len(tokens)
                        else len(line_text)
                    )
                    chunk = line_text[content_start:next_start].strip()
                    # Remove trailing pipe separator produced by DocxExtractor tables
                    if chunk.endswith("|"):
                        chunk = chunk[:-1].strip()

                    is_suffix_marked = False
                    if INLINE_CORRECT_SUFFIX_RE.search(chunk):
                        is_suffix_marked = True
                        chunk = INLINE_CORRECT_SUFFIX_RE.sub("", chunk).strip()
                    elif TRAILING_STAR_SUFFIX_RE.search(chunk):
                        is_suffix_marked = True
                        chunk = TRAILING_STAR_SUFFIX_RE.sub("", chunk).strip()

                    # Check DOCX run-level formatting hint covering option label or body
                    docx_marked = False
                    if orig_spans:
                        abs_start = col_offset + tok_start
                        abs_end = col_offset + next_start
                        docx_marked = cls._is_range_marked(orig_spans, abs_start, abs_end)

                    draft = _OptionDraft(
                        id=letter,
                        text_parts=[chunk] if chunk else [],
                        inline_marked=(has_marker or is_suffix_marked),
                        docx_marked=docx_marked,
                    )
                    options.append(draft)
                continue

            # 4. Continuation lines
            if mode == "options" and options:
                options[-1].text_parts.append(stripped)
            elif mode == "after_answer":
                # Stray prose after `Đáp án:` without explicit `Giải thích:` prefix
                explanation_parts.append(stripped)
            else:
                stem_parts.append(stripped)

        q_num = block.question_number or fallback_number
        raw_stem = _collapse_spaces(" ".join(stem_parts))
        content, cognitive_level, level, tags = _parse_cognitive_and_level_tags(raw_stem)

        # Skip orphan preamble/noise blocks that have neither meaningful content nor options
        if not content and not options:
            return None

        # Merge text for each option
        normalized_options: List[ParsedOptionSchema] = []
        inline_ids: List[str] = []
        docx_ids: List[str] = []

        for draft in options:
            opt_text = _collapse_spaces(" ".join(draft.text_parts))
            if not opt_text:
                continue
            if draft.inline_marked and draft.id not in inline_ids:
                inline_ids.append(draft.id)
            if draft.docx_marked and draft.id not in docx_ids:
                docx_ids.append(draft.id)
            normalized_options.append(
                ParsedOptionSchema(id=draft.id, text=opt_text, is_correct=False)
            )

        valid_option_id_set = {opt.id for opt in normalized_options}

        # Ignore DOCX formatting if every single option had identical underline/highlight
        if docx_ids and len(docx_ids) >= len(normalized_options) and len(normalized_options) >= 2:
            docx_ids = []

        # Handle TRUE_FALSE literal answer like "Đáp án: Đúng" / "Answer: True"
        if (
            not explicit_answer_letters
            and explicit_answer_raw_text
            and len(normalized_options) == 2
        ):
            ans_cf = _collapse_spaces(explicit_answer_raw_text).casefold().rstrip(".")
            for opt in normalized_options:
                if opt.text.casefold().rstrip(".") == ans_cf:
                    explicit_answer_letters.append(opt.id)
                    break

        # Merge priority: inline markers + DOCX formatting > explicit Đáp án line > trailing answer key
        resolved_correct_ids: List[str] = []
        for candidate_id in inline_ids + docx_ids:
            if candidate_id in valid_option_id_set and candidate_id not in resolved_correct_ids:
                resolved_correct_ids.append(candidate_id)

        if not resolved_correct_ids and explicit_answer_letters:
            for candidate_id in explicit_answer_letters:
                if candidate_id in valid_option_id_set and candidate_id not in resolved_correct_ids:
                    resolved_correct_ids.append(candidate_id)

        if not resolved_correct_ids and block.question_number in trailing_keys:
            used_trailing_keys.add(block.question_number)
            for candidate_id in trailing_keys[block.question_number]:
                if candidate_id in valid_option_id_set and candidate_id not in resolved_correct_ids:
                    resolved_correct_ids.append(candidate_id)

        correct_set = set(resolved_correct_ids)
        for opt in normalized_options:
            opt.is_correct = opt.id in correct_set

        # Infer QuestionType cleanly matching backend/app/schemas/common.py rules
        option_texts_cf = {opt.text.casefold() for opt in normalized_options}
        if len(normalized_options) == 2 and option_texts_cf in (
            {"đúng", "sai"},
            {"true", "false"},
        ):
            question_type = QuestionType.TRUE_FALSE
        elif len(resolved_correct_ids) >= 2:
            question_type = QuestionType.MULTIPLE_CHOICE
        else:
            question_type = QuestionType.SINGLE_CHOICE

        explanation_text = _collapse_spaces(" ".join(explanation_parts)) or None

        warnings: List[str] = []
        if not content:
            warnings.append("Không tìm thấy nội dung câu hỏi.")
        if len(normalized_options) < 2:
            warnings.append("Câu hỏi có ít hơn 2 phương án lựa chọn.")
        elif len(normalized_options) > 10:
            warnings.append("Câu hỏi có nhiều hơn 10 phương án lựa chọn (giới hạn CSDL tối đa 10).")
        if len(normalized_options) >= 2 and not resolved_correct_ids:
            warnings.append("Chưa xác định được đáp án đúng.")

        is_valid = (
            bool(content)
            and 2 <= len(normalized_options) <= 10
            and len(resolved_correct_ids) >= 1
        )

        return ParsedQuestionSchema(
            question_number=q_num,
            content=content or f"(Câu hỏi #{q_num} thiếu nội dung)",
            question_type=question_type,
            cognitive_level=cognitive_level,
            level=level,
            options=normalized_options,
            correct_option_ids=resolved_correct_ids,
            explanation=explanation_text,
            tags=tags,
            source_type=QuestionSource.FILE_PARSER,
            is_valid=is_valid,
            warnings=warnings,
        )

    @staticmethod
    def _compute_statistics(
        *, total_blocks: int, questions: Sequence[ParsedQuestionSchema]
    ) -> ParseStatisticsSchema:
        total = len(questions)
        valid = sum(1 for q in questions if q.is_valid)
        with_answer = sum(1 for q in questions if len(q.correct_option_ids) >= 1)
        with_explanation = sum(1 for q in questions if bool(q.explanation))
        warnings_count = sum(1 for q in questions if len(q.warnings) > 0)
        return ParseStatisticsSchema(
            total_blocks_detected=total_blocks,
            total_questions=total,
            valid_questions=valid,
            questions_with_correct_answer=with_answer,
            questions_with_explanation=with_explanation,
            warnings_count=warnings_count,
        )


__all__ = ["RegexQuestionParserService"]
