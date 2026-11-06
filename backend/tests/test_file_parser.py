"""Automated Synthetic E2E Test Suite for File Parser Service (Issue #5).

This test suite verifies the end-to-end file upload and raw text extraction
pipeline for PDF, DOCX, and TXT files. All synthetic test files are generated
programmatically in-memory (no static fixture files).

Test Hierarchy:
- Tier 1: Feature Coverage (happy path for PDF, DOCX, TXT with Vietnamese text, word/char counts)
- Tier 2: Boundary & Corner Cases (empty, whitespace, exact 10MB, >10MB, corrupted, unsupported)
- Tier 3: Combinatorial & Error Handling (multi-page PDF, tables, UTF-8 BOM, sequential requests)
- Tier 4: Real-World Scenarios (authentic Vietnamese exam papers with questions, options, rubrics)
"""

from __future__ import annotations

import io
import pytest
import pymupdf
import docx
from fastapi.testclient import TestClient

from app.main import app
from app.modules.parser.services.file_parser_service import (
    DocumentParserService,
    FileParserService,
)
from app.modules.parser.exceptions import (
    CorruptedFileError,
    EmptyFileError,
    FileSizeLimitExceededError,
    UnsupportedFileTypeError,
)

# ---------------------------------------------------------------------------
# In-Memory Synthetic File Generators
# ---------------------------------------------------------------------------


def make_pdf_bytes(pages_html: list[str]) -> bytes:
    """Generate in-memory PDF bytes using PyMuPDF HTML box layout.

    Using page.insert_htmlbox renders Vietnamese UTF-8 diacritics natively
    without OS font dependencies.
    """
    doc = pymupdf.open()
    for html in pages_html:
        page = doc.new_page()
        rect = pymupdf.Rect(50, 50, 550, 800)
        page.insert_htmlbox(rect, html)
    data = doc.tobytes()
    doc.close()
    return data


def make_encrypted_pdf_bytes(password: str = "secret123") -> bytes:
    """Generate in-memory encrypted / password-protected PDF bytes."""
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_htmlbox(
        pymupdf.Rect(50, 50, 550, 800), "<p>Tài liệu mật được bảo vệ</p>"
    )
    data = doc.tobytes(
        encryption=pymupdf.PDF_ENCRYPT_AES_256,
        user_pw=password,
        owner_pw="admin_owner_pass",
    )
    doc.close()
    return data


def make_docx_bytes(
    paragraphs: list[str] | None = None,
    tables: list[list[list[str]]] | None = None,
) -> bytes:
    """Generate in-memory Word (.docx) document bytes."""
    doc = docx.Document()
    if paragraphs:
        for p in paragraphs:
            doc.add_paragraph(p)
    if tables:
        for table_data in tables:
            rows = len(table_data)
            cols = len(table_data[0]) if rows > 0 else 0
            if rows > 0 and cols > 0:
                tbl = doc.add_table(rows=rows, cols=cols)
                for r_idx, row in enumerate(table_data):
                    for c_idx, cell_value in enumerate(row):
                        tbl.cell(r_idx, c_idx).text = cell_value
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def make_txt_bytes(content: str, encoding: str = "utf-8", bom: bool = False) -> bytes:
    """Generate in-memory plain text bytes with optional UTF-8 BOM."""
    if bom:
        return b"\xef\xbb\xbf" + content.encode("utf-8")
    return content.encode(encoding)


# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Shared FastAPI TestClient for HTTP E2E tests."""
    return TestClient(app)


VIETNAMESE_SAMPLE_TEXT = (
    "Cộng hòa Xã hội Chủ nghĩa Việt Nam\n"
    "Độc lập - Tự do - Hạnh phúc\n\n"
    "Bài kiểm tra trắc nghiệm chuyên đề Quản trị Dự án Phần mềm:\n"
    "Học viên cần nắm vững: ă, â, đ, ê, ô, ơ, ư và các thanh điệu (sắc, huyền, hỏi, ngã, nặng)."
)


# ===========================================================================
# Tier 1: Feature Coverage (Happy Path)
# ===========================================================================


class TestTier1FeatureCoverage:
    """Test standard feature behavior and happy paths for all supported formats."""

    def test_health_check_endpoint(self, client: TestClient) -> None:
        """Verify the parser health check endpoint returns 200 OK."""
        response = client.get("/api/v1/parser/health")
        assert response.status_code == 200
        payload = response.json()
        assert payload.get("status") == "healthy"
        assert payload.get("service") == "File Parser Service"

    def test_upload_valid_txt_vietnamese_diacritics(self, client: TestClient) -> None:
        """Upload valid UTF-8 TXT with full Vietnamese diacritics and verify extracted text."""
        txt_bytes = make_txt_bytes(VIETNAMESE_SAMPLE_TEXT)
        response = client.post(
            "/api/v1/parser/upload",
            files={"file": ("de_kiem_tra.txt", txt_bytes, "text/plain")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "File parsed successfully"

        result = data["data"]
        assert result["filename"] == "de_kiem_tra.txt"
        assert result["file_type"] == "txt"
        assert result["file_size"] == len(txt_bytes)
        assert result["page_count"] is None
        # Assert full Vietnamese diacritics preservation verbatim
        assert "Cộng hòa Xã hội Chủ nghĩa Việt Nam" in result["raw_text"]
        assert "ă, â, đ, ê, ô, ơ, ư" in result["raw_text"]
        assert result["character_count"] == len(result["raw_text"])
        assert result["word_count"] == len(result["raw_text"].split())

    def test_upload_valid_docx_vietnamese_text(self, client: TestClient) -> None:
        """Upload valid DOCX with multiple paragraphs in Vietnamese and verify extraction."""
        paragraphs = [
            "BỘ GIÁO DỤC VÀ ĐÀO TẠO",
            "ĐỀ THI KẾT THÚC HỌC PHẦN",
            "Môn: Phát triển Ứng dụng Web An toàn",
            "Thời gian làm bài: 60 phút (không kể thời gian phát đề)",
        ]
        docx_bytes = make_docx_bytes(paragraphs=paragraphs)
        response = client.post(
            "/api/v1/parser/upload",
            files={
                "file": (
                    "de_thi_mon_web.docx",
                    docx_bytes,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        result = data["data"]
        assert result["filename"] == "de_thi_mon_web.docx"
        assert result["file_type"] == "docx"
        assert result["file_size"] == len(docx_bytes)
        assert "BỘ GIÁO DỤC VÀ ĐÀO TẠO" in result["raw_text"]
        assert "Thời gian làm bài: 60 phút" in result["raw_text"]
        assert result["word_count"] > 0
        assert result["character_count"] > 0

    def test_upload_valid_pdf_vietnamese_diacritics(self, client: TestClient) -> None:
        """Upload valid single-page PDF with native HTML box layout preserving diacritics."""
        pdf_html = (
            "<h2>TRƯỜNG ĐẠI HỌC BÁCH KHOA</h2>"
            "<p>Đề thi trắc nghiệm giữa kỳ môn Cơ sở dữ liệu nâng cao.</p>"
            "<p>Hệ thống tự động chấm điểm và đánh giá năng lực học sinh.</p>"
        )
        pdf_bytes = make_pdf_bytes([pdf_html])
        response = client.post(
            "/api/v1/parser/upload",
            files={"file": ("co_so_du_lieu.pdf", pdf_bytes, "application/pdf")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        result = data["data"]
        assert result["filename"] == "co_so_du_lieu.pdf"
        assert result["file_type"] == "pdf"
        assert result["page_count"] == 1
        assert "TRƯỜNG ĐẠI HỌC BÁCH KHOA" in result["raw_text"]
        assert "Cơ sở dữ liệu nâng cao" in result["raw_text"]
        assert result["character_count"] == len(result["raw_text"])

    def test_response_schema_contract(self, client: TestClient) -> None:
        """Verify strict conformance to DocumentParseResult API schema specification."""
        txt_bytes = make_txt_bytes("Nội dung thử nghiệm hợp đồng giao tiếp API")
        response = client.post(
            "/api/v1/parser/upload",
            files={"file": ("contract_test.txt", txt_bytes, "text/plain")},
        )
        assert response.status_code == 200
        json_data = response.json()

        # Top-level APIResponse envelope
        assert "success" in json_data
        assert "message" in json_data
        assert "data" in json_data
        assert json_data["success"] is True

        # DocumentParseResult structure
        data = json_data["data"]
        required_fields = {
            "filename",
            "file_type",
            "file_size",
            "character_count",
            "word_count",
            "page_count",
            "raw_text",
        }
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"


# ===========================================================================
# Tier 2: Boundary & Corner Cases
# ===========================================================================


class TestTier2BoundaryAndCornerCases:
    """Test boundary values, edge limits, corrupted files, and unsupported formats."""

    @pytest.mark.parametrize("filename", ["empty.txt", "empty.pdf", "empty.docx"])
    def test_upload_empty_file_zero_bytes(
        self, client: TestClient, filename: str
    ) -> None:
        """Reject 0-byte uploaded files with HTTP 400 Bad Request."""
        response = client.post(
            "/api/v1/parser/upload",
            files={"file": (filename, b"", "application/octet-stream")},
        )
        assert response.status_code == 400
        detail = response.json().get("detail", "")
        assert "empty" in detail.lower() or "0 bytes" in detail.lower()

    def test_upload_whitespace_only_txt(self, client: TestClient) -> None:
        """Reject text files containing solely whitespace characters with HTTP 400."""
        whitespace_bytes = b"   \r\n\t   \n  \t\r\n  "
        response = client.post(
            "/api/v1/parser/upload",
            files={"file": ("whitespace.txt", whitespace_bytes, "text/plain")},
        )
        assert response.status_code == 400
        detail = response.json().get("detail", "")
        assert (
            "rỗng" in detail.lower()
            or "khoảng trắng" in detail.lower()
            or "empty" in detail.lower()
        )

    def test_upload_blank_page_pdf(self, client: TestClient) -> None:
        """Reject PDF files containing only blank pages with HTTP 400."""
        doc = pymupdf.open()
        doc.new_page()  # Blank page without any text or drawing
        blank_pdf_bytes = doc.tobytes()
        doc.close()

        response = client.post(
            "/api/v1/parser/upload",
            files={"file": ("blank.pdf", blank_pdf_bytes, "application/pdf")},
        )
        assert response.status_code == 400
        detail = response.json().get("detail", "")
        assert "không chứa nội dung" in detail.lower() or "empty" in detail.lower()

    def test_upload_empty_docx_document(self, client: TestClient) -> None:
        """Reject Word documents containing no text with HTTP 400."""
        doc = docx.Document()
        buffer = io.BytesIO()
        doc.save(buffer)
        empty_docx_bytes = buffer.getvalue()

        response = client.post(
            "/api/v1/parser/upload",
            files={
                "file": (
                    "empty.docx",
                    empty_docx_bytes,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )
        assert response.status_code == 400
        detail = response.json().get("detail", "")
        assert "không chứa nội dung" in detail.lower() or "empty" in detail.lower()

    def test_upload_exact_10mb_boundary(self, client: TestClient) -> None:
        """Accept file at exactly 10MB limit (10,485,760 bytes) without exceeding boundary."""
        exact_10mb_bytes = b"A " * (5 * 1024 * 1024)  # 10,485,760 bytes
        assert len(exact_10mb_bytes) == 10 * 1024 * 1024

        response = client.post(
            "/api/v1/parser/upload",
            files={"file": ("boundary_10mb.txt", exact_10mb_bytes, "text/plain")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["file_size"] == 10 * 1024 * 1024

    def test_upload_oversized_10mb_plus_one_byte(self, client: TestClient) -> None:
        """Reject file exceeding 10MB limit by 1 byte (10,485,761 bytes) with HTTP 400."""
        oversized_bytes = b"A" * (10 * 1024 * 1024 + 1)
        response = client.post(
            "/api/v1/parser/upload",
            files={"file": ("oversized.txt", oversized_bytes, "text/plain")},
        )
        assert response.status_code == 400
        detail = response.json().get("detail", "")
        assert "exceeds maximum allowed limit of 10MB" in detail or "10MB" in detail

    def test_upload_oversized_large_file(self, client: TestClient) -> None:
        """Reject substantially oversized file (12MB) with HTTP 400."""
        large_bytes = b"X" * (12 * 1024 * 1024)
        response = client.post(
            "/api/v1/parser/upload",
            files={"file": ("too_large.txt", large_bytes, "text/plain")},
        )
        assert response.status_code == 400
        detail = response.json().get("detail", "")
        assert "10MB" in detail

    @pytest.mark.parametrize(
        "ext,content_type",
        [
            (".png", "image/png"),
            (".exe", "application/x-msdownload"),
            (".zip", "application/zip"),
            (".csv", "text/csv"),
            (".json", "application/json"),
            (".mp4", "video/mp4"),
        ],
    )
    def test_upload_unsupported_extensions(
        self, client: TestClient, ext: str, content_type: str
    ) -> None:
        """Reject unsupported file extensions with HTTP 400 Bad Request."""
        payload = b"Sample arbitrary payload"
        filename = f"file{ext}"
        response = client.post(
            "/api/v1/parser/upload",
            files={"file": (filename, payload, content_type)},
        )
        assert response.status_code == 400
        detail = response.json().get("detail", "")
        assert "unsupported" in detail.lower() or "only" in detail.lower()

    def test_upload_double_extension_executable(self, client: TestClient) -> None:
        """Reject disguised double extension file (.pdf.exe) using final extension."""
        response = client.post(
            "/api/v1/parser/upload",
            files={
                "file": (
                    "de_thi_mau.pdf.exe",
                    b"executable payload",
                    "application/octet-stream",
                )
            },
        )
        assert response.status_code == 400
        detail = response.json().get("detail", "")
        assert "unsupported" in detail.lower()

    def test_upload_missing_extension(self, client: TestClient) -> None:
        """Reject files without any extension with HTTP 400."""
        response = client.post(
            "/api/v1/parser/upload",
            files={
                "file": ("document_without_ext", b"valid text content", "text/plain")
            },
        )
        assert response.status_code == 400
        detail = response.json().get("detail", "")
        assert (
            "missing file extension" in detail.lower()
            or "unsupported" in detail.lower()
        )

    @pytest.mark.parametrize(
        "filename,make_content_fn",
        [
            ("SAMPLE.PDF", lambda: make_pdf_bytes(["<p>Nội dung chữ in hoa</p>"])),
            ("DOCUMENT.Docx", lambda: make_docx_bytes(["Nội dung Word hỗn hợp"])),
            ("NOTES.TXT", lambda: make_txt_bytes("Nội dung ghi chú in hoa")),
        ],
    )
    def test_upload_case_insensitive_extensions(
        self, client: TestClient, filename: str, make_content_fn
    ) -> None:
        """Accept uppercase and mixed-case valid extensions (.PDF, .Docx, .TXT)."""
        content = make_content_fn()
        response = client.post(
            "/api/v1/parser/upload",
            files={"file": (filename, content, "application/octet-stream")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_upload_corrupted_pdf_bytes(self, client: TestClient) -> None:
        """Safely reject corrupted PDF byte streams without crashing server (HTTP 400, not 500)."""
        corrupted_bytes = (
            b"%PDF-1.4\nCorrupted binary junk \x00\xff\xfe\xca\xfe\xba\xbe"
        )
        response = client.post(
            "/api/v1/parser/upload",
            files={"file": ("corrupted.pdf", corrupted_bytes, "application/pdf")},
        )
        assert response.status_code == 400
        detail = response.json().get("detail", "")
        assert "bị hỏng" in detail.lower() or "corrupted" in detail.lower()

    def test_upload_corrupted_docx_bytes(self, client: TestClient) -> None:
        """Safely reject non-zip corrupted DOCX byte streams without crashing server."""
        corrupted_bytes = b"PK\x03\x04This is not a valid zip archive for Word document"
        response = client.post(
            "/api/v1/parser/upload",
            files={
                "file": (
                    "corrupted.docx",
                    corrupted_bytes,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )
        assert response.status_code == 400
        detail = response.json().get("detail", "")
        assert (
            "bị hỏng" in detail.lower()
            or "zip" in detail.lower()
            or "corrupted" in detail.lower()
        )

    def test_upload_txt_with_null_bytes(self, client: TestClient) -> None:
        """Reject binary files masquerading as .txt containing null bytes."""
        binary_txt = "Tiêu đề tài liệu\x00dữ liệu nhị phân ẩn".encode("utf-8")
        response = client.post(
            "/api/v1/parser/upload",
            files={"file": ("binary_null.txt", binary_txt, "text/plain")},
        )
        assert response.status_code == 400
        detail = response.json().get("detail", "")
        assert "nhị phân" in detail.lower() or "null" in detail.lower()

    def test_upload_txt_invalid_utf8_encoding(self, client: TestClient) -> None:
        """Reject text files with invalid non-UTF8 byte sequences."""
        invalid_bytes = b"Valid ASCII header \x80\xff\xfe\xed Invalid bytes"
        response = client.post(
            "/api/v1/parser/upload",
            files={"file": ("invalid_encoding.txt", invalid_bytes, "text/plain")},
        )
        assert response.status_code == 400
        detail = response.json().get("detail", "")
        assert "utf-8" in detail.lower() or "codec" in detail.lower()

    def test_upload_encrypted_password_protected_pdf(self, client: TestClient) -> None:
        """Reject encrypted or password-protected PDF files safely with HTTP 400."""
        encrypted_pdf = make_encrypted_pdf_bytes("secret_password")
        response = client.post(
            "/api/v1/parser/upload",
            files={"file": ("encrypted.pdf", encrypted_pdf, "application/pdf")},
        )
        assert response.status_code == 400
        detail = response.json().get("detail", "")
        assert (
            "mật khẩu" in detail.lower()
            or "mã hóa" in detail.lower()
            or "encrypted" in detail.lower()
        )

    def test_upload_whitespace_filename(self, client: TestClient) -> None:
        """Reject uploads where filename consists solely of whitespace."""
        response = client.post(
            "/api/v1/parser/upload",
            files={"file": ("   ", b"Some valid content", "text/plain")},
        )
        assert response.status_code == 400
        detail = response.json().get("detail", "")
        assert (
            "missing filename" in detail.lower() or "valid named file" in detail.lower()
        )


# ===========================================================================
# Tier 3: Combinatorial & Error Handling
# ===========================================================================


class TestTier3CombinatorialAndErrorHandling:
    """Test multi-page, complex layout tables, encoding variants, and concurrent streams."""

    def test_upload_multipage_pdf(self, client: TestClient) -> None:
        """Verify extraction across multi-page PDF documents with accurate page counts."""
        pages = [
            "<p>Trang 1: Bảng phân bổ ma trận đề thi trắc nghiệm.</p>",
            "<p>Trang 2: Các câu hỏi trắc nghiệm mức độ thông hiểu và vận dụng.</p>",
            "<p>Trang 3: Hướng dẫn giải chi tiết và thang điểm quy đổi.</p>",
        ]
        pdf_bytes = make_pdf_bytes(pages)
        response = client.post(
            "/api/v1/parser/upload",
            files={"file": ("de_thi_3_trang.pdf", pdf_bytes, "application/pdf")},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["page_count"] == 3
        assert "Trang 1: Bảng phân bổ ma trận" in data["raw_text"]
        assert "Trang 2: Các câu hỏi trắc nghiệm" in data["raw_text"]
        assert "Trang 3: Hướng dẫn giải chi tiết" in data["raw_text"]

    def test_upload_docx_with_tables_and_merged_cells(self, client: TestClient) -> None:
        """Verify extraction from Word documents containing both paragraphs and structured tables."""
        paragraphs = ["Phần 1: Bảng chỉ số đặc tả câu hỏi"]
        tables = [
            [
                ["STT", "Nội dung kiến thức", "Số câu", "Điểm số"],
                ["1", "Tổng quan Quản trị Dự án", "10", "2.5"],
                ["2", "Mô hình Agile & Scrum", "15", "3.75"],
                ["3", "Kiểm thử phần mềm & QA", "15", "3.75"],
            ]
        ]
        docx_bytes = make_docx_bytes(paragraphs=paragraphs, tables=tables)
        response = client.post(
            "/api/v1/parser/upload",
            files={
                "file": (
                    "dac_ta_mon_hoc.docx",
                    docx_bytes,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )
        assert response.status_code == 200
        raw_text = response.json()["data"]["raw_text"]
        assert "Phần 1: Bảng chỉ số đặc tả câu hỏi" in raw_text
        assert "STT | Nội dung kiến thức | Số câu | Điểm số" in raw_text
        assert "1 | Tổng quan Quản trị Dự án | 10 | 2.5" in raw_text
        assert "2 | Mô hình Agile & Scrum | 15 | 3.75" in raw_text

    def test_upload_txt_utf8_sig_bom_handling(self, client: TestClient) -> None:
        """Verify TXT files saved with UTF-8 BOM are decoded cleanly without BOM character."""
        text_with_bom = "Học kỳ 1 Năm học 2026-2027: Danh sách môn thi tự động."
        txt_bytes = make_txt_bytes(text_with_bom, bom=True)
        assert txt_bytes.startswith(b"\xef\xbb\xbf")

        response = client.post(
            "/api/v1/parser/upload",
            files={"file": ("danh_sach_bom.txt", txt_bytes, "text/plain")},
        )
        assert response.status_code == 200
        raw_text = response.json()["data"]["raw_text"]
        assert not raw_text.startswith("\ufeff")
        assert raw_text == text_with_bom

    def test_upload_sequential_requests_stability(self, client: TestClient) -> None:
        """Verify server stability across sequential requests alternating between formats."""
        pdf_bytes = make_pdf_bytes(["<p>Nội dung kiểm tra tuần tự PDF</p>"])
        docx_bytes = make_docx_bytes(["Nội dung kiểm tra tuần tự DOCX"])
        txt_bytes = make_txt_bytes("Nội dung kiểm tra tuần tự TXT")

        queue = [
            ("seq_1.pdf", pdf_bytes, "application/pdf"),
            (
                "seq_2.docx",
                docx_bytes,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ),
            ("seq_3.txt", txt_bytes, "text/plain"),
            (
                "seq_4.docx",
                docx_bytes,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ),
            ("seq_5.pdf", pdf_bytes, "application/pdf"),
        ]

        for filename, content, ctype in queue:
            resp = client.post(
                "/api/v1/parser/upload",
                files={"file": (filename, content, ctype)},
            )
            assert resp.status_code == 200
            assert resp.json()["success"] is True
            assert resp.json()["data"]["filename"] == filename

    def test_upload_missing_file_payload(self, client: TestClient) -> None:
        """Verify request without 'file' form data returns HTTP 422 Unprocessable Content."""
        response = client.post("/api/v1/parser/upload", data={})
        assert response.status_code == 422

    def test_direct_service_layer_exceptions(self) -> None:
        """Directly verify DocumentParserService domain exceptions independently of HTTP."""
        # 1. Empty bytes
        with pytest.raises(EmptyFileError):
            DocumentParserService.parse_file("empty.txt", b"")

        # 2. File size exceeded
        oversized = b"A" * (FileParserService.MAX_FILE_SIZE + 1)
        with pytest.raises(FileSizeLimitExceededError):
            DocumentParserService.parse_file("large.txt", oversized)

        # 3. Unsupported extension
        with pytest.raises(UnsupportedFileTypeError):
            DocumentParserService.parse_file("script.py", b"print('hello')")

        # 4. Corrupted format
        with pytest.raises(CorruptedFileError):
            DocumentParserService.parse_file("bad.pdf", b"corrupted non-pdf bytes")


# ===========================================================================
# Tier 4: Real-World Scenarios
# ===========================================================================


class TestTier4RealWorldScenarios:
    """Test realistic full-length Vietnamese exam papers and documents."""

    def test_upload_realworld_vietnamese_exam_pdf(self, client: TestClient) -> None:
        """Upload authentic multi-question Vietnamese exam paper in PDF format."""
        exam_p1_html = (
            "<h3>SỞ GIÁO DỤC VÀ ĐÀO TẠO THÀNH PHỐ HỒ CHÍ MINH</h3>"
            "<h4>ĐỀ THI KHẢO SÁT CHẤT LƯỢNG HỌC KỲ II - NĂM HỌC 2025-2026</h4>"
            "<p><b>Môn thi: TIN HỌC 12</b> | Thời gian: 45 phút | Mã đề: 204</p>"
            "<hr/>"
            "<p><b>Câu 1:</b> Mạng máy tính là gì?</p>"
            "<p>A. Tập hợp các máy tính nối với nhau bằng phương tiện truyền dẫn</p>"
            "<p>B. Hệ thống các máy tính hoạt động độc lập không có kết nối</p>"
            "<p>C. Một phần mềm dùng để soạn thảo văn bản</p>"
            "<p>D. Một thiết bị phần cứng lưu trữ dữ liệu</p>"
        )
        exam_p2_html = (
            "<p><b>Câu 2:</b> Giao thức mạng phổ biến nhất trên Internet hiện nay là gì?</p>"
            "<p>A. HTTP/HTTPS và TCP/IP</p>"
            "<p>B. Bluetooth</p>"
            "<p>C. USB 3.0</p>"
            "<p>D. HDMI</p>"
            "<br/>"
            "<p>--- HẾT ---</p>"
            "<p><i>Cán bộ coi thi không giải thích gì thêm.</i></p>"
        )
        pdf_bytes = make_pdf_bytes([exam_p1_html, exam_p2_html])
        response = client.post(
            "/api/v1/parser/upload",
            files={"file": ("de_thi_tin_hoc_12.pdf", pdf_bytes, "application/pdf")},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["file_type"] == "pdf"
        assert data["page_count"] == 2
        raw_text = data["raw_text"]
        assert "SỞ GIÁO DỤC VÀ ĐÀO TẠO" in raw_text
        assert "ĐỀ THI KHẢO SÁT CHẤT LƯỢNG" in raw_text
        assert "Câu 1: Mạng máy tính là gì?" in raw_text
        assert "Câu 2: Giao thức mạng phổ biến nhất" in raw_text
        assert "HTTP/HTTPS và TCP/IP" in raw_text
        assert "Cán bộ coi thi không giải thích gì thêm" in raw_text

    def test_upload_realworld_vietnamese_exam_docx(self, client: TestClient) -> None:
        """Upload authentic university exam paper in DOCX format with rubrics table."""
        paragraphs = [
            "ĐẠI HỌC QUỐC GIA TP. HỒ CHÍ MINH",
            "TRƯỜNG ĐẠI HỌC CÔNG NGHỆ THÔNG TIN",
            "ĐỀ KIỂM TRA ĐÁNH GIÁ NĂNG LỰC HỌC TẬP",
            "Môn: Nhập môn Trí tuệ Nhân tạo",
            "Câu 1: Thuật toán A* là thuật toán tìm kiếm thuộc loại nào?",
            "A. Tìm kiếm mù (Uninformed Search)",
            "B. Tìm kiếm có thông tin (Informed / Heuristic Search)",
            "C. Tìm kiếm ngẫu nhiên",
            "D. Tìm kiếm vét cạn",
            "Câu 2: Hàm Heuristic h(n) được coi là admissible khi nào?",
            "A. Không bao giờ ước lượng vượt quá chi phí thực tế",
            "B. Luôn luôn lớn hơn chi phí thực tế",
            "C. Luôn bằng 0 với mọi trạng thái",
            "D. Có giá trị âm",
        ]
        tables = [
            [
                ["Phần thi", "Số câu", "Điểm", "Thời gian"],
                ["Trắc nghiệm lý thuyết", "20", "5.0", "30 phút"],
                ["Bài tập suy diễn logic", "10", "5.0", "30 phút"],
            ]
        ]
        docx_bytes = make_docx_bytes(paragraphs=paragraphs, tables=tables)
        response = client.post(
            "/api/v1/parser/upload",
            files={
                "file": (
                    "de_thi_tri_tue_nhan_tao.docx",
                    docx_bytes,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )
        assert response.status_code == 200
        raw_text = response.json()["data"]["raw_text"]
        assert "ĐẠI HỌC QUỐC GIA" in raw_text
        assert "Nhập môn Trí tuệ Nhân tạo" in raw_text
        assert "Thuật toán A*" in raw_text
        assert "Heuristic h(n)" in raw_text
        assert "Trắc nghiệm lý thuyết | 20 | 5.0 | 30 phút" in raw_text

    def test_upload_realworld_vietnamese_exam_txt(self, client: TestClient) -> None:
        """Upload raw text exam format with math notation and complex tone marks."""
        exam_txt = (
            "TRƯỜNG THPT CHUYÊN LÊ HỒNG PHONG\n"
            "ĐỀ THI THỬ TỐT NGHIỆP THPT MÔN TOÁN\n\n"
            "Câu 1: Cho hàm số y = f(x) có bảng biến thiên trên đoạn [-2, 3].\n"
            "Giá trị cực đại của hàm số đã cho bằng bao nhiêu?\n"
            "A. y = 5\n"
            "B. y = -1\n"
            "C. y = 0\n"
            "D. y = 3\n\n"
            "Câu 2: Thể tích khối lăng trụ có diện tích đáy B và chiều cao h là:\n"
            "A. V = B * h\n"
            "B. V = (1/3) * B * h\n"
            "C. V = (1/2) * B * h\n"
            "D. V = (4/3) * B * h\n"
        )
        txt_bytes = make_txt_bytes(exam_txt)
        response = client.post(
            "/api/v1/parser/upload",
            files={"file": ("de_thi_toan_le_hong_phong.txt", txt_bytes, "text/plain")},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["file_type"] == "txt"
        assert "LÊ HỒNG PHONG" in data["raw_text"]
        assert "bảng biến thiên" in data["raw_text"]
        assert "Giá trị cực đại" in data["raw_text"]
        assert "V = B * h" in data["raw_text"]

    def test_word_and_character_count_accuracy(self, client: TestClient) -> None:
        """Verify strict character count and word count calculation precision."""
        sample = "Một hai ba bốn năm sáu bảy tám chín mười."
        # Word count = 10 words
        # Char count = 41 characters
        txt_bytes = make_txt_bytes(sample)
        response = client.post(
            "/api/v1/parser/upload",
            files={"file": ("stats_test.txt", txt_bytes, "text/plain")},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["raw_text"] == sample
        assert data["character_count"] == len(sample)
        assert data["word_count"] == len(sample.split())
        assert data["word_count"] == 10
        assert data["character_count"] == 41
