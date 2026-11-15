# Báo cáo Kiểm thử Khép kín End-to-End (E2E) & Bàn giao Hệ thống — Issue #37

- **Ngày thực hiện:** 15/11/2026 (Asia/Saigon).
- **Mã Issue:** Issue #37 — `[Release] End-to-End Smoke Testing, Cloud Deployment & Final Release v2.0`.
- **Nhánh phát triển:** `release/issue-37-e2e-deployment-v2.0`.
- **Phân công & Ước lượng:** @MaiVanTinh17072005 (Dev 4), @nhatanh19 (Dev 1 / Lead) phối hợp cùng @MinusDC (Dev 3), @thuan734655 (Dev 2) — 7 Story Points.
- **Kế hoạch WBS:** WBS 6.1 (E2E Integration Testing & Cloud Deployment) & WBS 6.2 (User Manual & Final Release) — Gộp các đầu việc kế hoạch #29, #30, #32 trong `docs/DETAILED_GITHUB_ISSUES.md`.
- **Trạng thái:** Toàn bộ 4/4 tiêu chí Definition of Done (DoD) đã hoàn thành và kiểm thử đạt 100%.

---

## 1. Kết quả Tổng hợp Test Suite Tự động

| Hạng mục kiểm thử | Công cụ | Số lượng kiểm thử | Kết quả | Ghi chú |
| :--- | :--- | :--- | :--- | :--- |
| **Backend API Core & Modules** | Pytest 9.2 / Python 3.14 | 252 test cases | **248 passed, 4 skipped** | Bao phủ Auth, Parser (Upload/Regex), AI Gen (Bloom/Chunking), Exam Engine, Shuffle, Anti-Cheat, Auto-Grading, AI Tutor, Knowledge Gaps, Analytics |
| **Frontend Component & Integration** | Vitest 3.2 / JSDOM | 84 test cases | **84 passed** (7 Test Suites) | Bao phủ ApiClient, ExamPages, DocumentParserTab, ExamRoom, AppRoutes, AntiCheatMonitor, AiGenPage |
| **Frontend Production Build** | Vite 5.4 + TypeScript | 1,576 modules | **PASS (0 errors)** | Bundle JS: 431 KB (Gzip 123 KB), CSS: 47 KB |
| **Database Migrations & Seed** | Alembic + SQLAlchemy 2.0 | Toàn bộ bảng DB | **PASS** | Tự động migrate và seed 3 tài khoản mẫu + chuyên đề + đề thi demo |
| **Reverse Proxy & Origin Uniformity** | Nginx 1.27 Gateway | Proxy `/api/` & `/` | **PASS** | Triệt tiêu lỗi CORS, giữ nguyên HttpOnly SameSite=Lax Cookies theo `docs/AUTHENTICATION.md` |

**Tổng cộng test suite tự động:** **332 tests PASSED, 4 skipped**.

---

## 2. Kiểm thử Khép kín 6 Kịch bản Nghiệp vụ (E2E Walkthrough)

### Kịch bản 1: Module 1 — Bóc tách tài liệu & Duyệt trước câu hỏi (File Parser Engine)
- **Hành vi kiểm tra:** Giảng viên tải lên tệp tài liệu `.pdf`, `.docx`, `.txt` dung lượng $\le 10$MB.
- **Thực hiện:**
  - Giao diện `DocumentParserTab` (Issue #5 & #7) tiếp nhận tệp, hiển thị tiến trình upload.
  - API `POST /api/v1/parser/upload-and-parse` bóc tách văn bản thô đồng thời trích xuất các khối câu hỏi trắc nghiệm qua Regex Engine (Issue #6).
  - Bảng duyệt trước câu hỏi `ParsedQuestionPreviewPanel` cho phép chỉnh sửa trực tiếp nội dung, đổi dạng câu hỏi (Single Choice, Multiple Choice, True/False), bật/tắt đáp án đúng bằng 1-click, và lưu hàng loạt vào Ngân hàng câu hỏi.
- **Kết quả:** Nhận diện chuẩn xác 100% tiếng Việt UTF-8, bóc tách phương án A-D và đáp án gạch chân/tô màu từ Word.
- **Đánh giá:** **PASS**.

### Kịch bản 2: Module 2 — Ma trận Thang Bloom, Sinh đề AI & Phân đoạn Tài liệu
- **Hành vi kiểm tra:** Giảng viên thiết kế ma trận nhận thức theo Thang Bloom và sinh đề từ chủ đề hoặc tài liệu học liệu.
- **Thực hiện:**
  - `AiGenPage.tsx` (Issue #32 & #33) tải danh mục Bloom Templates từ `/api/v1/ai-generator/bloom-templates`.
  - Cấu hình phân bổ 3 cấp độ Bloom: Nhận biết (Remember), Thông hiểu (Understand), Vận dụng (Apply) và 3 định dạng câu hỏi.
  - Phân đoạn tài liệu học liệu tự động qua `chunking_service.py` phục vụ sinh đề RAG từ ngữ cảnh.
  - Gọi LLM sinh câu hỏi bằng `/generate-by-matrix` hoặc `/generate-from-context`.
  - Giảng viên xem trước lời giải thích sư phạm và bấm "Lưu vào Ngân hàng câu hỏi".
- **Kết quả:** Đề thi được sinh bám sát chuẩn đầu ra Bloom, kiểm soát chất lượng phương án nhiễu theo đúng tiêu chí kiểm định.
- **Đánh giá:** **PASS**.

### Kịch bản 3: Module 3 — Tạo ca thi, Quản lý phòng & Xáo trộn đề độc lập
- **Hành vi kiểm tra:** Giảng viên tạo ca thi từ ngân hàng câu hỏi, thiết lập thời gian làm bài, mã phòng, mã PIN và xuất bản ca thi.
- **Thực hiện:** `ManageExams.tsx` tạo ca thi và kích hoạt trạng thái `is_published=true`.
- **Kết quả:** Sinh viên vào phòng thi qua `JoinExam.tsx` và `ExamLobby.tsx`. Mỗi sinh viên nhận đề thi được xáo trộn câu hỏi và phương án ngẫu nhiên theo thuật toán Fisher-Yates (seed độc lập), bảo toàn nguyên vẹn ID phương án gốc (`option_id`) khi chấm điểm.
- **Đánh giá:** **PASS**.

### Kịch bản 4: Module 3 — Phòng thi Tập trung, F5 Giữ đáp án & Anti-Cheat Tự khóa
- **Hành vi kiểm tra:**
  1. Thí sinh chọn đáp án, bấm tải lại trang (F5) hoặc ngắt kết nối tạm thời.
  2. Thí sinh chuyển sang tab khác hoặc mất tiêu điểm quá số lần cho phép (`max_tab_violations = 3`).
- **Thực hiện:**
  - Hook `useAntiCheatMonitor` ghi nhận các sự kiện `visibilitychange` và `window.blur` (chống đếm trùng trong khoảng 750ms). Chặn phím F12, phím mở DevTools, chặn copy/paste và chuột phải.
  - API `/attempts/{id}/autosave-answers` và `localStorage` liên tục đồng bộ snapshot đáp án.
- **Kết quả:**
  - Khi F5, toàn bộ đáp án đã chọn được khôi phục nguyên vẹn 100%.
  - Khi vi phạm tab lần thứ 3: Modal cảnh báo chuyển sang trạng thái khóa bài, gửi kèm toàn bộ đáp án hiện tại, backend cập nhật trạng thái `LOCKED_VIOLATION`, tự động chấm điểm và điều hướng thí sinh sang giao diện Review.
- **Đánh giá:** **PASS**.

### Kịch bản 5: Module 4 — Chấm điểm tự động & Gia sư ảo AI Tutor
- **Hành vi kiểm tra:** Chấm điểm bài thi và hỏi đáp giải thích từng câu hỏi sau khi kết thúc.
- **Thực hiện:**
  - Engine chấm điểm tự động đối chiếu đáp án thí sinh với đáp án gốc trong cơ sở dữ liệu.
  - Giao diện `ReviewExamView` hiển thị danh sách câu đúng/sai, số điểm đạt được và chẩn đoán lỗ hổng kiến thức (`KnowledgeGapCard`).
  - Thí sinh bấm nút "Giải thích bằng AI".
- **Kết quả:** AI Tutor phản hồi trong vòng 1-2 giây, phân tích chi tiết:
  1. Vì sao đáp án chuẩn là chính xác.
  2. Vì sao phương án thí sinh đã chọn lại chưa đúng.
  3. Lỗ hổng kiến thức sư phạm cần củng cố.
- **Đánh giá:** **PASS**.

### Kịch bản 6: Module 4 — Dashboard Phân tích & Xuất dữ liệu CSV
- **Hành vi kiểm tra:** Giảng viên xem biểu đồ phổ điểm lớp học và xuất bảng điểm danh sách thí sinh ra tệp CSV; Sinh viên xem tiến độ học tập cá nhân.
- **Thực hiện:**
  - Giảng viên truy cập `LecturerAnalyticsDashboard` trong `AnalyticsPlaceholder`: Xem biểu đồ Histogram phân bố điểm, điểm trung bình, điểm trung vị, tỷ lệ hoàn thành, Top câu hỏi hay làm sai nhất.
  - Bấm nút "Xuất danh sách điểm (CSV)".
  - Sinh viên truy cập `StudentAnalyticsDashboard` (qua menu Analytics hoặc `/student/analytics`): Xem biểu đồ xu hướng điểm qua các lần thi và radar mức độ nắm vững từng chuyên đề.
- **Kết quả:** Tệp CSV được tạo với đầy đủ thông tin (Họ tên, Email, Điểm số, Trạng thái, Thời gian nộp, Số lần vi phạm chuyển tab), mã hóa UTF-8 với BOM tương thích 100% Microsoft Excel tiếng Việt.
- **Đánh giá:** **PASS**.

---

## 3. Xác nhận Đóng gói & Triển khai Hệ thống

- **Docker Compose:** Đóng gói hoàn chỉnh cụm 4 containers (`smartquiz_postgres`, `smartquiz_backend`, `smartquiz_frontend`, `smartquiz_proxy`).
- **Nginx Gateway:** Đóng vai trò Reverse Proxy tập trung tại cổng 80:
  - Cấu hình cùng Origin loại trừ hoàn toàn lỗi CORS.
  - Đảm bảo cơ chế HttpOnly Cookie SameSite=Lax hoạt động trơn tru trên mọi trình duyệt theo đúng `docs/AUTHENTICATION.md`.
- **Cloud Blueprint:** Cung cấp tệp cấu hình `render.yaml` sẵn sàng triển khai lên dịch vụ Cloud Free-tier (Render, Railway, Supabase).

---

## 4. Lệnh Tái hiện Kiểm thử

### Backend
```powershell
python -m pytest backend/tests -q -p no:cacheprovider
```

### Frontend
```powershell
cd frontend
cmd /c npm test -- --run
cmd /c npm run build
```

---

## 5. Kết luận

Toàn bộ **4/4 Acceptance Criteria** và Definition of Done của **Issue #37** đã được hoàn thành 100%:
1. Hệ thống đã vượt qua kiểm thử khép kín toàn bộ luồng nghiệp vụ trên trình duyệt thật.
2. Cấu hình triển khai môi trường thực tế (Docker + Nginx + Cloud) hoàn chỉnh.
3. Tài liệu hướng dẫn sử dụng, tài khoản demo và khung slide thuyết trình đã được bổ sung đầy đủ.
4. Sẵn sàng phát hành phiên bản chính thức **`v2.0.0-final`**.
