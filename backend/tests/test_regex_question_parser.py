"""Automated Test Suite for Regex Pattern Matching Engine (Issue #6 / WBS 2.1.2).

Verifies multi-format quiz structure extraction (question headers, A-J options,
inline/explicit/DOCX-formatted/trailing correct answers, explanations,
PostgreSQL schema parity, >= 90% Word/PDF benchmark accuracy, and RBAC/Origin security).
"""

from __future__ import annotations

import io
import uuid

import docx
import pymupdf
import pytest
from docx.enum.text import WD_COLOR_INDEX
from docx.shared import RGBColor
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.models.entities import (
    CognitiveLevel,
    QuestionLevel,
    QuestionSource,
    QuestionType,
    User,
    UserRole,
)
from app.modules.parser.services.regex_question_parser import RegexQuestionParserService
from app.schemas.common import QuestionCreateSchema


# ---------------------------------------------------------------------------
# In-Memory Synthetic Document Helpers
# ---------------------------------------------------------------------------


def make_pdf_bytes(pages_html: list[str]) -> bytes:
    """Render HTML pages into PDF bytes via PyMuPDF with native UTF-8 support."""
    doc = pymupdf.open()
    for html in pages_html:
        page = doc.new_page()
        page.insert_htmlbox(pymupdf.Rect(45, 45, 555, 800), html)
    data = doc.tobytes()
    doc.close()
    return data


def _create_user_client(
    db_session: Session, role: UserRole, email: str
) -> TestClient:
    user = User(
        email=email,
        full_name=f"Regex {role.value}",
        password_hash="hashed_secret_unused",
        role=role,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    token = create_access_token({"sub": str(user.id), "role": role.value})
    client = TestClient(app)
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


@pytest.fixture
def db_session(auth_engine):
    """Transactional database session rolled back after each test."""
    with auth_engine.connect() as connection:
        transaction = connection.begin()
        if connection.dialect.name == "sqlite":
            connection.exec_driver_sql("BEGIN")
        try:
            with Session(bind=connection, join_transaction_mode="create_savepoint") as db:
                app.dependency_overrides[get_db] = lambda: db
                yield db
        finally:
            app.dependency_overrides.pop(get_db, None)
            if transaction.is_active:
                transaction.rollback()


@pytest.fixture
def anon_client(db_session: Session) -> TestClient:
    return TestClient(app)


@pytest.fixture
def instructor_client(db_session: Session) -> TestClient:
    with _create_user_client(
        db_session, UserRole.INSTRUCTOR, "regex_instructor@example.com"
    ) as test_client:
        yield test_client


# ---------------------------------------------------------------------------
# Tier 1: Headers, Options, Multi-line, and False-Positive Protections
# ---------------------------------------------------------------------------


class TestTier1StructureMatching:
    """Verify Regex recognition across standard Vietnamese and English question layouts."""

    def test_parses_explicit_headers_and_multiline_stem_and_options(self) -> None:
        raw_text = (
            "TRƯỜNG ĐẠI HỌC CÔNG NGHỆ\n"
            "ĐỀ KIỂM TRA GIỮA KỲ MÔN QUẢN TRỊ DỰ ÁN\n\n"
            "Câu 1: WBS là viết tắt của cụm từ nào sau đây\n"
            "trong tài liệu PMBOK?\n"
            "A. Work Breakdown Structure\n"
            "trên cơ sở phân rã sản phẩm\n"
            "B. Work Budget Schedule\n"
            "C. Weekly Backlog Summary\n"
            "D. Workflow Baseline System\n"
            "Đáp án: A\n"
            "Giải thích: WBS phân rã phạm vi dự án theo sản phẩm bàn giao.\n"
            "Đây là công cụ nền tảng của Week 03.\n\n"
            "Question 2. Which technique breaks work into smaller deliverables?\n"
            "(A) PERT\n"
            "(B) Decomposition\n"
            "(C) Crashing\n"
            "(D) Fast tracking\n"
            "Answer: B\n"
            "Explanation: Decomposition subdivides deliverables into manageable work packages.\n"
        )

        result = RegexQuestionParserService.parse(raw_text, filename="sample.txt")

        assert result.statistics.total_questions == 2
        assert result.statistics.valid_questions == 2
        assert result.statistics.questions_with_correct_answer == 2
        assert result.statistics.questions_with_explanation == 2

        q1, q2 = result.questions
        assert q1.question_number == 1
        assert "WBS là viết tắt của cụm từ nào sau đây trong tài liệu PMBOK?" == q1.content
        assert [opt.id for opt in q1.options] == ["A", "B", "C", "D"]
        assert q1.options[0].text == "Work Breakdown Structure trên cơ sở phân rã sản phẩm"
        assert q1.correct_option_ids == ["A"]
        assert q1.options[0].is_correct is True
        assert q1.options[1].is_correct is False
        assert q1.explanation == "WBS phân rã phạm vi dự án theo sản phẩm bàn giao. Đây là công cụ nền tảng của Week 03."
        assert q1.source_type == QuestionSource.FILE_PARSER

        assert q2.question_number == 2
        assert q2.correct_option_ids == ["B"]
        assert q2.explanation == "Decomposition subdivides deliverables into manageable work packages."

    def test_parses_inline_two_and_four_column_options_without_prose_false_positives(self) -> None:
        raw_text = (
            "1. Grade A. Smith sử dụng Vitamin B. để minh họa phép tính 5 + 5 bằng:\n"
            "A. 10    B. 20    C. 30    D. 40\n"
            "Đáp án: A\n\n"
            "2) Phương án đúng về C. Ronaldo trong bài đọc:\n"
            "a) Tiền đạo    b) Thủ môn\n"
            "c) Trọng tài    d) Huấn luyện viên\n"
            "*a.\n"
            "ĐA: A\n"
        )

        result = RegexQuestionParserService.parse(raw_text)
        assert result.statistics.total_questions == 2

        q1, q2 = result.questions
        assert "Grade A. Smith" in q1.content
        assert "Vitamin B." in q1.content
        assert [(o.id, o.text) for o in q1.options] == [
            ("A", "10"),
            ("B", "20"),
            ("C", "30"),
            ("D", "40"),
        ]
        assert q1.correct_option_ids == ["A"]

        assert "C. Ronaldo" in q2.content
        assert [(o.id, o.text) for o in q2.options] == [
            ("A", "Tiền đạo"),
            ("B", "Thủ môn"),
            ("C", "Trọng tài"),
            ("D", "Huấn luyện viên"),
        ]
        assert q2.correct_option_ids == ["A"]

    def test_explicit_header_ignores_internal_numbered_lists(self) -> None:
        raw_text = (
            "Câu 1: Sắp xếp các bước sau theo đúng trình tự:\n"
            "1. Khởi tạo dự án\n"
            "2. Lập kế hoạch\n"
            "3. Thực thi và kiểm soát\n"
            "A. 1 -> 2 -> 3\n"
            "B. 2 -> 1 -> 3\n"
            "C. 3 -> 2 -> 1\n"
            "D. 1 -> 3 -> 2\n"
            "Đáp án: A\n"
        )
        result = RegexQuestionParserService.parse(raw_text)
        assert result.statistics.total_questions == 1
        assert "1. Khởi tạo dự án 2. Lập kế hoạch 3. Thực thi và kiểm soát" in result.questions[0].content
        assert result.questions[0].correct_option_ids == ["A"]


# ---------------------------------------------------------------------------
# Tier 2: Correct Answer Varieties, Types, Answer Keys, DB Schema Parity
# ---------------------------------------------------------------------------


class TestTier2AnswerDetectionAndTypes:
    """Verify inline markers, multiple choice, true/false, trailing keys, and DB compatibility."""

    def test_detects_inline_star_checkbox_multiple_choice_and_true_false(self) -> None:
        raw_text = (
            "Câu 1: [Thông hiểu] [Dễ] Các thành phần nào thuộc mô hình Scrum?\n"
            "*A. Product Owner\n"
            "B. Waterfall Lead\n"
            "[x] C. Scrum Master\n"
            "D. Development Team (Đúng)\n"
            "Giải thích: Scrum gồm 3 vai trò chính.\n\n"
            "Câu 2: FastAPI hỗ trợ kiểm tra kiểu dữ liệu qua Pydantic v2.\n"
            "A. Đúng\n"
            "B. Sai\n"
            "Đáp án: Đúng\n\n"
            "Câu 3: Đáp án câu này đang bị thiếu để UI #7 xử lý:\n"
            "A. Phương án một\n"
            "B. Phương án hai\n"
        )

        result = RegexQuestionParserService.parse(raw_text)
        assert result.statistics.total_questions == 3
        assert result.statistics.valid_questions == 2
        assert result.statistics.warnings_count == 1

        q1, q2, q3 = result.questions
        assert q1.question_type == QuestionType.MULTIPLE_CHOICE
        assert q1.cognitive_level == CognitiveLevel.UNDERSTAND
        assert q1.level == QuestionLevel.EASY
        assert q1.correct_option_ids == ["A", "C", "D"]
        assert [o.text for o in q1.options] == [
            "Product Owner",
            "Waterfall Lead",
            "Scrum Master",
            "Development Team",
        ]

        assert q2.question_type == QuestionType.TRUE_FALSE
        assert q2.correct_option_ids == ["A"]
        assert q2.is_valid is True

        assert q3.is_valid is False
        assert q3.correct_option_ids == []
        assert "Chưa xác định được đáp án đúng." in q3.warnings

        # Verify parsed valid questions serialize directly into QuestionCreateSchema
        dummy_category_id = uuid.uuid4()
        for valid_q in (q1, q2):
            validated = QuestionCreateSchema(
                category_id=dummy_category_id,
                content=valid_q.content,
                question_type=valid_q.question_type,
                cognitive_level=valid_q.cognitive_level,
                level=valid_q.level,
                options=[o.model_dump() for o in valid_q.options],
                tags=valid_q.tags,
                explanation=valid_q.explanation,
            )
            assert len(validated.options) >= 2

    def test_resolves_trailing_answer_key_table(self) -> None:
        raw_text = (
            "Câu 1: Kết quả của 2^3 là?\n"
            "A. 6\nB. 8\nC. 9\nD. 12\n\n"
            "Câu 2: Những số nào là số nguyên tố?\n"
            "A. 2\nB. 4\nC. 5\nD. 9\n\n"
            "Trang 1 / 2\n\n"
            "BẢNG ĐÁP ÁN\n"
            "1. B | 2. A, C\n"
        )

        result = RegexQuestionParserService.parse(raw_text)
        assert result.statistics.total_questions == 2
        assert result.statistics.valid_questions == 2
        assert result.questions[0].correct_option_ids == ["B"]
        assert result.questions[1].correct_option_ids == ["A", "C"]
        assert result.questions[1].question_type == QuestionType.MULTIPLE_CHOICE
        assert result.unmatched_answer_keys == {}


# ---------------------------------------------------------------------------
# Tier 3: DOCX Rich Formatting (Underline / Highlight / Vivid Red)
# ---------------------------------------------------------------------------


class TestTier3DocxFormattingHints:
    """Verify underlined/highlighted answers in Word documents without mutating raw_text."""

    def test_detects_underlined_and_highlighted_docx_answers_while_preserving_issue5_raw_text(
        self,
    ) -> None:
        doc = docx.Document()

        doc.add_paragraph("Câu 1: Phương án nào được gạch chân chữ cái?")
        p1a = doc.add_paragraph("A. Sai")
        p1b = doc.add_paragraph()
        r_u = p1b.add_run("B")
        r_u.underline = True
        p1b.add_run(". Đúng nhờ gạch chân chữ B")
        doc.add_paragraph("C. Cũng sai")
        doc.add_paragraph("D. Không chọn")

        doc.add_paragraph("Câu 2: Phương án nào được tô vàng?")
        doc.add_paragraph("A. Lựa chọn A")
        p2b = doc.add_paragraph("B. Lựa chọn B")
        p2c = doc.add_paragraph()
        r_hi = p2c.add_run("C. Lựa chọn C tô vàng")
        r_hi.font.highlight_color = WD_COLOR_INDEX.YELLOW
        doc.add_paragraph("D. Lựa chọn D")

        doc.add_paragraph("Câu 3: Phương án cùng dòng với chữ đỏ?")
        p3 = doc.add_paragraph()
        p3.add_run("A. Đỏ đậm   ")
        p3.runs[-1].font.color.rgb = RGBColor(0xD9, 0x20, 0x20)
        p3.add_run("B. Đen bình thường")

        # Control check: if all options are underlined identically, underline is ignored
        doc.add_paragraph("Câu 4: Cả 2 đều gạch chân nhưng đáp án ở cuối:")
        for opt_txt in ("A. Nhất", "B. Nhì"):
            p = doc.add_paragraph()
            run = p.add_run(opt_txt)
            run.underline = True
        doc.add_paragraph("Đáp án: B")

        buf = io.BytesIO()
        doc.save(buf)
        docx_bytes = buf.getvalue()

        from app.modules.parser.services.file_parser_service import FileParserService

        # Verify Issue #5 parse_file raw_text has NO synthetic '*' markers added
        plain_doc = FileParserService.parse_file("underlined.docx", docx_bytes)
        assert "*" not in plain_doc.raw_text

        doc_with_hints, marked_spans = FileParserService.parse_file_with_hints(
            "underlined.docx", docx_bytes
        )
        parsed = RegexQuestionParserService.parse(
            doc_with_hints.raw_text,
            filename=doc_with_hints.filename,
            line_marked_spans=marked_spans,
        )

        assert parsed.statistics.total_questions == 4
        assert parsed.statistics.valid_questions == 4
        assert parsed.questions[0].correct_option_ids == ["B"]
        assert parsed.questions[1].correct_option_ids == ["C"]
        assert parsed.questions[2].correct_option_ids == ["A"]
        assert parsed.questions[3].correct_option_ids == ["B"]


# ---------------------------------------------------------------------------
# Tier 4: >= 90% Accuracy Benchmark on Realistic 20-Question Word & PDF Exams
# ---------------------------------------------------------------------------


def _build_benchmark_exam_items() -> list[dict]:
    """20 authentic mixed-format Vietnamese questions serving as ground truth."""
    return [
        {
            "stem": f"Câu {i}: Nội dung câu hỏi chuẩn hóa số {i} về kiến thức Quản trị Dự án?",
            "options": [
                f"Phương án A của câu {i}",
                f"Phương án B của câu {i}",
                f"Phương án C của câu {i}",
                f"Phương án D của câu {i}",
            ],
            "correct": ["A", "B", "C", "D"][(i - 1) % 4],
            "explanation": f"Giải thích chi tiết cho câu số {i}." if i % 2 == 0 else None,
            "mode": "underline" if i <= 5 else ("star" if i <= 10 else ("inline_ans" if i <= 15 else "key_table")),
        }
        for i in range(1, 21)
    ]


class TestTier4BenchmarkAccuracy:
    """Acceptance Criterion: >= 90% accuracy on sample lecturer Word & PDF exam papers."""

    def test_docx_benchmark_exceeds_90_percent_accuracy(self) -> None:
        items = _build_benchmark_exam_items()
        doc = docx.Document()
        doc.add_paragraph("ĐẠI HỌC QUỐC GIA - ĐỀ THI MẪU 20 CÂU")
        trailing_answers: list[str] = []

        for idx, item in enumerate(items, start=1):
            doc.add_paragraph(item["stem"])
            letters = ["A", "B", "C", "D"]
            if idx % 3 == 0:
                # 2 options per line layout
                p1 = doc.add_paragraph()
                for j in (0, 1):
                    prefix = "*" if item["mode"] == "star" and letters[j] == item["correct"] else ""
                    r = p1.add_run(f"{prefix}{letters[j]}. {item['options'][j]}")
                    if item["mode"] == "underline" and letters[j] == item["correct"]:
                        r.underline = True
                    if j == 0:
                        p1.add_run("    ")
                p2 = doc.add_paragraph()
                for j in (2, 3):
                    prefix = "*" if item["mode"] == "star" and letters[j] == item["correct"] else ""
                    r = p2.add_run(f"{prefix}{letters[j]}. {item['options'][j]}")
                    if item["mode"] == "underline" and letters[j] == item["correct"]:
                        r.underline = True
                    if j == 2:
                        p2.add_run("    ")
            else:
                for j, opt_text in enumerate(item["options"]):
                    prefix = "*" if item["mode"] == "star" and letters[j] == item["correct"] else ""
                    p = doc.add_paragraph()
                    r = p.add_run(f"{prefix}{letters[j]}. {opt_text}")
                    if item["mode"] == "underline" and letters[j] == item["correct"]:
                        r.underline = True

            if item["mode"] == "inline_ans":
                doc.add_paragraph(f"Đáp án: {item['correct']}")
            if item["explanation"]:
                doc.add_paragraph(f"Giải thích: {item['explanation']}")
            if item["mode"] == "key_table":
                trailing_answers.append(f"{idx}.{item['correct']}")

        doc.add_paragraph("BẢNG ĐÁP ÁN")
        doc.add_paragraph("  ".join(trailing_answers))

        buf = io.BytesIO()
        doc.save(buf)

        from app.modules.parser.services.file_parser_service import FileParserService

        doc_res, marked_spans = FileParserService.parse_file_with_hints(
            "benchmark_20q.docx", buf.getvalue()
        )
        parsed = RegexQuestionParserService.parse(
            doc_res.raw_text,
            filename=doc_res.filename,
            line_marked_spans=marked_spans,
        )

        exact_matches = 0
        by_num = {q.question_number: q for q in parsed.questions}
        for idx, truth in enumerate(items, start=1):
            q = by_num.get(idx)
            if (
                q is not None
                and f"câu hỏi chuẩn hóa số {idx}" in q.content
                and len(q.options) == 4
                and q.correct_option_ids == [truth["correct"]]
            ):
                exact_matches += 1

        accuracy = exact_matches / len(items)
        assert accuracy >= 0.90, f"Expected >= 90% accuracy on DOCX, got {accuracy:.1%}"
        assert parsed.statistics.total_questions == 20

    def test_pdf_benchmark_exceeds_90_percent_accuracy(self) -> None:
        items = _build_benchmark_exam_items()
        pages_html: list[str] = []

        for page_idx, chunk_start in enumerate((0, 10), start=1):
            lines = [f"<p><strong>TRANG {page_idx}/2 - ĐỀ THI TRẮC NGHIỆM PDF</strong></p>"]
            for q_offset, item in enumerate(items[chunk_start: chunk_start + 10], start=chunk_start + 1):
                lines.append(f"<p>Câu {q_offset}: Cấu trúc chuẩn hóa câu hỏi PDF số {q_offset}?</p>")
                for j, letter in enumerate(("A", "B", "C", "D")):
                    # PDF uses star markers for first 10, explicit Answer for next 5, trailing key for last 5
                    star = "*" if q_offset <= 10 and letter == item["correct"] else ""
                    lines.append(f"<p>{star}{letter}. {item['options'][j]}</p>")
                if 11 <= q_offset <= 15:
                    lines.append(f"<p>Đáp án đúng: {item['correct']}</p>")
                if item["explanation"]:
                    lines.append(f"<p>Giải thích: {item['explanation']}</p>")
            if page_idx == 2:
                key_str = " ".join(f"{k}.{items[k - 1]['correct']}" for k in range(16, 21))
                lines.append("<p>ĐÁP ÁN THAM KHẢO</p>")
                lines.append(f"<p>{key_str}</p>")
            pages_html.append("".join(lines))

        pdf_bytes = make_pdf_bytes(pages_html)

        from app.modules.parser.services.file_parser_service import FileParserService

        doc_res = FileParserService.parse_file("benchmark_20q.pdf", pdf_bytes)
        parsed = RegexQuestionParserService.parse(doc_res.raw_text, filename=doc_res.filename)

        exact_matches = 0
        by_num = {q.question_number: q for q in parsed.questions}
        for idx, truth in enumerate(items, start=1):
            q = by_num.get(idx)
            if (
                q is not None
                and f"câu hỏi PDF số {idx}" in q.content
                and len(q.options) == 4
                and q.correct_option_ids == [truth["correct"]]
            ):
                exact_matches += 1

        accuracy = exact_matches / len(items)
        assert accuracy >= 0.90, f"Expected >= 90% accuracy on PDF, got {accuracy:.1%}"
        assert parsed.statistics.total_questions == 20


# ---------------------------------------------------------------------------
# Tier 5: HTTP Endpoints, RBAC, Origin Checks & Validation
# ---------------------------------------------------------------------------


class TestTier5ParserRegexEndpoints:
    """Verify HTTP contracts, RBAC, and Origin/CSRF checks for new Issue #6 routes."""

    def test_parse_questions_endpoint_rbac_and_origin(
        self, anon_client: TestClient, db_session: Session
    ) -> None:
        payload = {"raw_text": "Câu 1: 1 + 1 = ?\nA. 1\n*B. 2\nC. 3\nD. 4", "filename": "q.txt"}

        assert anon_client.post("/api/v1/parser/parse-questions", json=payload).status_code == 401

        with _create_user_client(db_session, UserRole.STUDENT, "s_regex@example.com") as sc:
            assert sc.post("/api/v1/parser/parse-questions", json=payload).status_code == 403

        with _create_user_client(db_session, UserRole.ADMIN, "a_regex@example.com") as ac:
            assert (
                ac.post(
                    "/api/v1/parser/parse-questions",
                    headers={"Origin": "https://evil.example"},
                    json=payload,
                ).status_code
                == 403
            )
            assert (
                ac.post(
                    "/api/v1/parser/parse-questions",
                    headers={"sec-fetch-site": "cross-site"},
                    json=payload,
                ).status_code
                == 403
            )
            ok = ac.post("/api/v1/parser/parse-questions", json=payload)
            assert ok.status_code == 200
            body = ok.json()
            assert body["success"] is True
            assert body["data"]["statistics"]["total_questions"] == 1
            assert body["data"]["questions"][0]["correct_option_ids"] == ["B"]

    def test_parse_questions_rejects_blank_raw_text(self, instructor_client: TestClient) -> None:
        resp = instructor_client.post(
            "/api/v1/parser/parse-questions",
            json={"raw_text": "   \n  ", "filename": "blank.txt"},
        )
        assert resp.status_code == 422

    def test_upload_and_parse_endpoint_with_docx_underlined_answers_and_rbac(
        self,
        anon_client: TestClient,
        instructor_client: TestClient,
        db_session: Session,
    ) -> None:
        doc = docx.Document()
        doc.add_paragraph("Câu 1: Thủ đô của Việt Nam là thành phố nào?")
        doc.add_paragraph("A. TP. Hồ Chí Minh")
        p_correct = doc.add_paragraph()
        r = p_correct.add_run("B. Hà Nội")
        r.underline = True
        doc.add_paragraph("C. Đà Nẵng")
        doc.add_paragraph("D. Cần Thơ")
        doc.add_paragraph("Giải thích: Hà Nội là thủ đô nước CHXHCN Việt Nam.")

        buf = io.BytesIO()
        doc.save(buf)
        docx_bytes = buf.getvalue()

        assert (
            anon_client.post(
                "/api/v1/parser/upload-and-parse",
                files={"file": ("de.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            ).status_code
            == 401
        )

        with _create_user_client(db_session, UserRole.STUDENT, "s_up@example.com") as sc:
            assert (
                sc.post(
                    "/api/v1/parser/upload-and-parse",
                    files={"file": ("de.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                ).status_code
                == 403
            )

        bad_ext = instructor_client.post(
            "/api/v1/parser/upload-and-parse",
            files={"file": ("malware.exe", b"MZ", "application/octet-stream")},
        )
        assert bad_ext.status_code == 400

        ok = instructor_client.post(
            "/api/v1/parser/upload-and-parse",
            files={
                "file": (
                    "de_thi_mau.docx",
                    docx_bytes,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )
        assert ok.status_code == 200
        data = ok.json()["data"]
        assert data["document"]["filename"] == "de_thi_mau.docx"
        assert data["statistics"]["total_questions"] == 1
        assert data["statistics"]["valid_questions"] == 1
        q1 = data["questions"][0]
        assert q1["content"] == "Thủ đô của Việt Nam là thành phố nào?"
        assert q1["correct_option_ids"] == ["B"]
        assert q1["source_type"] == "FILE_PARSER"
        assert q1["explanation"] == "Hà Nội là thủ đô nước CHXHCN Việt Nam."
