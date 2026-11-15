"""Sliding Window Chunking Service for AI Document-to-Quiz Generation (Issue #33 / WBS 3.3.1).

Splits long-form documents or lecture notes into contextually coherent chunks
with configurable chunk size, overlap, and natural sentence boundary detection.
Preserves UTF-8 Vietnamese diacritics and formatting.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import List, Optional

WHITESPACE_COLLAPSE_RE = re.compile(r"[ \t]+")
PARAGRAPH_NORMALIZE_RE = re.compile(r"\n{3,}")
SENTENCE_END_RE = re.compile(r"[\.\!\?\;\n]\s")


@dataclass(frozen=True)
class TextChunk:
    """Represents a text chunk created by sliding window chunking."""

    index: int
    text: str
    start_char: int
    end_char: int

    @property
    def character_count(self) -> int:
        return len(self.text)

    @property
    def word_count(self) -> int:
        return len(self.text.split())


class SlidingWindowChunker:
    """Chunks documents using a sliding window with sentence boundary detection."""

    DEFAULT_CHUNK_SIZE = 1500
    DEFAULT_OVERLAP = 200
    DEFAULT_MIN_CHUNK_SIZE = 100

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        overlap: int = DEFAULT_OVERLAP,
        min_chunk_size: int = DEFAULT_MIN_CHUNK_SIZE,
    ):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if overlap < 0:
            raise ValueError("overlap must be non-negative")
        if overlap >= chunk_size:
            raise ValueError("overlap must be strictly less than chunk_size")
        if min_chunk_size < 0:
            raise ValueError("min_chunk_size must be non-negative")

        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_chunk_size = min_chunk_size

    def clean_text(self, text: str) -> str:
        """Normalize whitespaces while preserving newlines and Vietnamese UTF-8 accents."""
        if not text:
            return ""
        # Replace non-standard whitespace / tabs
        cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
        lines = [WHITESPACE_COLLAPSE_RE.sub(" ", line).strip() for line in cleaned.split("\n")]
        cleaned = "\n".join(lines)
        cleaned = PARAGRAPH_NORMALIZE_RE.sub("\n\n", cleaned)
        return cleaned.strip()

    def chunk(
        self,
        text: str,
        *,
        chunk_size: Optional[int] = None,
        overlap: Optional[int] = None,
        min_chunk_size: Optional[int] = None,
    ) -> List[TextChunk]:
        """Split text into a list of TextChunk objects using sliding window."""
        c_size = chunk_size if chunk_size is not None else self.chunk_size
        if overlap is not None:
            c_overlap = overlap
            if c_overlap >= c_size:
                raise ValueError("overlap must be strictly less than chunk_size")
        else:
            c_overlap = min(self.overlap, max(0, c_size // 4))

        c_min = min_chunk_size if min_chunk_size is not None else self.min_chunk_size

        cleaned = self.clean_text(text)
        if not cleaned:
            return []

        text_len = len(cleaned)
        if text_len <= c_size:
            return [
                TextChunk(
                    index=0,
                    text=cleaned,
                    start_char=0,
                    end_char=text_len,
                )
            ]

        chunks: List[TextChunk] = []
        start = 0
        chunk_idx = 0

        while start < text_len:
            end = min(start + c_size, text_len)

            # If not at the end of the text, find natural boundary near end
            if end < text_len:
                boundary = self._find_boundary(cleaned, start, end, c_min)
                if boundary is not None and boundary > start:
                    end = boundary

            chunk_content = cleaned[start:end].strip()

            # Only append if chunk is meaningful
            if len(chunk_content) >= c_min or (not chunks and len(chunk_content) > 0):
                chunks.append(
                    TextChunk(
                        index=chunk_idx,
                        text=chunk_content,
                        start_char=start,
                        end_char=end,
                    )
                )
                chunk_idx += 1

            if end >= text_len:
                break

            # Advance sliding window
            next_start = end - c_overlap
            if next_start <= start:
                next_start = start + max(1, c_size - c_overlap)
            start = next_start

        return chunks

    def _find_boundary(
        self, text: str, start: int, end: int, min_chunk_size: int
    ) -> Optional[int]:
        """Find the most suitable natural sentence or newline boundary looking back from end."""
        # Search window is backwards up to 25% of chunk_size or 250 characters
        search_back = min(250, int((end - start) * 0.25))
        search_start = max(start + min_chunk_size, end - search_back)
        segment = text[search_start:end]

        # 1. Prefer paragraph break (\n\n or \n)
        for newline_pattern in ("\n\n", "\n"):
            pos = segment.rfind(newline_pattern)
            if pos != -1:
                return search_start + pos + len(newline_pattern)

        # 2. Check for sentence end punctuation followed by whitespace (. ! ?)
        matches = list(SENTENCE_END_RE.finditer(segment))
        if matches:
            last_match = matches[-1]
            return search_start + last_match.end()

        # 3. Fallback: space boundary to avoid word clipping
        last_space = segment.rfind(" ")
        if last_space != -1:
            return search_start + last_space + 1

        return None

    def chunk_as_strings(self, text: str, **kwargs) -> List[str]:
        """Convenience method returning list of raw chunk strings."""
        return [c.text for c in self.chunk(text, **kwargs)]


chunking_service = SlidingWindowChunker()
