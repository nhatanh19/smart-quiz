"""Unit tests for Sliding Window Chunking Service (Issue #33 / WBS 3.3.1)."""

import pytest

from app.modules.ai_generator.chunking_service import (
    SlidingWindowChunker,
    TextChunk,
    chunking_service,
)


def test_chunker_initialization_validations():
    with pytest.raises(ValueError, match="chunk_size must be greater than 0"):
        SlidingWindowChunker(chunk_size=0)

    with pytest.raises(ValueError, match="overlap must be non-negative"):
        SlidingWindowChunker(chunk_size=500, overlap=-10)

    with pytest.raises(ValueError, match="overlap must be strictly less than chunk_size"):
        SlidingWindowChunker(chunk_size=500, overlap=500)

    with pytest.raises(ValueError, match="overlap must be strictly less than chunk_size"):
        SlidingWindowChunker(chunk_size=500, overlap=600)

    with pytest.raises(ValueError, match="min_chunk_size must be non-negative"):
        SlidingWindowChunker(chunk_size=500, overlap=100, min_chunk_size=-1)


def test_clean_text_normalizes_whitespace_and_preserves_accents():
    raw = "   Đây là   bài giảng    về Lập trình Python.  \r\n\r\n\n\nNội dung chính: Biến và hàm.   "
    cleaned = chunking_service.clean_text(raw)
    assert cleaned == "Đây là bài giảng về Lập trình Python.\n\nNội dung chính: Biến và hàm."
    assert "Đây là" in cleaned
    assert "Lập trình" in cleaned


def test_chunk_empty_or_whitespace_text_returns_empty_list():
    assert chunking_service.chunk("") == []
    assert chunking_service.chunk("   \n\t  ") == []
    assert chunking_service.chunk_as_strings("") == []


def test_chunk_short_text_returns_single_chunk():
    text = "Kiến trúc hướng dịch vụ (SOA) cho phép phân tách các thành phần chức năng độc lập."
    chunks = chunking_service.chunk(text, chunk_size=500, overlap=100)
    assert len(chunks) == 1
    assert chunks[0].index == 0
    assert chunks[0].text == text
    assert chunks[0].start_char == 0
    assert chunks[0].end_char == len(text)
    assert chunks[0].character_count == len(text)
    assert chunks[0].word_count > 0


def test_sliding_window_creates_overlapping_chunks():
    # Construct a text with several clear sentences
    sentences = [
        f"Câu số {i}: Đây là nội dung lý thuyết phục vụ cho việc học tập và nghiên cứu công nghệ phần mềm."
        for i in range(1, 20)
    ]
    text = " ".join(sentences)

    chunker = SlidingWindowChunker(chunk_size=300, overlap=80, min_chunk_size=50)
    chunks = chunker.chunk(text)

    assert len(chunks) >= 3

    # Check indices are sequential
    for idx, c in enumerate(chunks):
        assert c.index == idx
        assert len(c.text) >= 50
        assert isinstance(c, TextChunk)

    # Verify overlap exists between consecutive chunks
    for i in range(len(chunks) - 1):
        c1 = chunks[i].text
        c2 = chunks[i + 1].text
        # Some words from the end of c1 should appear in c2
        c1_words = [w for w in c1.split() if len(w) > 4]
        c2_words = [w for w in c2.split() if len(w) > 4]
        c1_tail_words = set(c1_words[-6:])
        c2_head_words = set(c2_words[:10])
        common = c1_tail_words.intersection(c2_head_words)
        assert len(common) > 0, f"No overlap found between chunk {i} and {i+1}"


def test_chunk_respects_sentence_boundary_where_possible():
    # Long text with clear sentence breaks
    part1 = "Phần thứ nhất trình bày về phương pháp phát triển linh hoạt Agile và khung làm việc Scrum."
    part2 = "Phần thứ hai đi sâu vào các vai trò chính trong Scrum bao gồm Product Owner, Scrum Master và Development Team."
    part3 = "Phần thứ ba phân tích quy trình tổ chức Sprint Planning, Daily Scrum, Sprint Review và Sprint Retrospective."
    text = f"{part1} {part2} {part3}"

    chunker = SlidingWindowChunker(chunk_size=len(part1) + 20, overlap=30, min_chunk_size=40)
    chunks = chunker.chunk(text)

    # First chunk should naturally end near end of part1
    assert "Agile và khung làm việc Scrum." in chunks[0].text


def test_chunk_as_strings_helper():
    text = "Chủ đề 1: Giải thuật sắp xếp. Chủ đề 2: Cấu trúc dữ liệu cây nhị phân."
    result = chunking_service.chunk_as_strings(text, chunk_size=200)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0] == text
