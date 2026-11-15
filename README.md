# 🧠 Smart Quiz — AI-Powered Online Assessment Platform

> **Nền tảng Đánh giá & Ôn luyện Trắc nghiệm Trực tuyến Tích hợp Trí tuệ Nhân tạo**  
> Dự án môn học: **Quản trị Dự án Phần mềm** — Đồ án Tốt nghiệp / Báo cáo Cuối kỳ  
> **Phiên bản phát hành chính thức:** `v2.0.0-final` (Milestone Sprint 2 Completed)

---

## 📌 1. Giới thiệu Tổng quan Dự án

**Smart Quiz** là hệ thống phần mềm toàn diện hỗ trợ Giảng viên và Sinh viên khép kín toàn bộ chu trình khảo thí trắc nghiệm: từ khâu chuẩn bị học liệu, tự động hóa biên soạn đề thi, tổ chức phòng thi nghiêm ngặt, cho đến khâu phân tích năng lực và gia sư cá nhân hóa:

```
[Module 1: File Parser] ───> [Module 2: AI Quiz Gen] ───> [Module 3: Exam Engine] ───> [Module 4: Tutor & Analytics]
  - Upload PDF/DOCX/TXT        - Ma trận nhận thức Bloom    - Phòng thi tập trung        - Chấm điểm đa dạng câu hỏi
  - Trích xuất Regex câu/đáp   - AI sinh đề tự động         - Xáo trộn đề độc lập        - AI Tutor giải thích ngữ cảnh
  - Xem trước & Chuẩn hóa      - Phân đoạn văn bản (RAG)    - Anti-cheat giám sát tab    - Phổ điểm & Xuất CSV
                               - Ngân hàng câu hỏi CRUD     - Khôi phục đáp án khi F5    - Tiến độ học tập cá nhân
```

### 4 Mô-đun Nghiệp vụ Trọng tâm:
1. **Module 1 (Document Parser):** Hỗ trợ kéo thả tải lên tài liệu học liệu (`.pdf`, `.docx`, `.txt`) dung lượng tối đa 10MB. Công cụ sử dụng biểu thức chính quy (Regex Engine) để bóc tách câu hỏi, phương án lựa chọn và đáp án chuẩn xác; bảng duyệt trước cho phép sửa trực tiếp và nhập hàng loạt vào Ngân hàng câu hỏi.
2. **Module 2 (AI Quiz Generator & Question Bank):** Thiết kế ma trận đề thi chuẩn theo **Thang nhận thức Bloom** (Nhận biết, Thông hiểu, Vận dụng) và định dạng câu hỏi (Chọn 1, chọn nhiều, đúng/sai). Hỗ trợ phân đoạn tài liệu học liệu (Chunking) để sinh đề theo ngữ cảnh bằng mô hình ngôn ngữ lớn (OpenAI / Gemini), kèm giao diện xem trước Prompt và lưu trực tiếp vào Ngân hàng câu hỏi.
3. **Module 3 (Online Exam Engine & Anti-Cheat):** Quản lý ca thi thời gian thực, mật mã PIN phòng thi, thuật toán Fisher-Yates xáo trộn đề độc lập theo thí sinh. Phòng thi tập trung tự động lưu đáp án liên tục, khôi phục trạng thái khi rớt mạng hoặc F5, cùng hệ thống Anti-cheat giám sát chuyển tab (`visibilitychange`), mất tiêu điểm, phím tắt DevTools để tự động thu/khóa bài khi vi phạm ngưỡng.
4. **Module 4 (Auto-Grading, AI Tutor & Analytics Dashboard):** Chấm điểm tự động tức thì. Giao diện Review sau thi tích hợp **Gia sư ảo AI (AI Tutor)** giải thích chi tiết vì sao phương án chọn đúng/sai và chẩn đoán lỗ hổng kiến thức. Bảng điều khiển phân tích biểu đồ phổ điểm lớp học cho Giảng viên, hỗ trợ **xuất bảng điểm định dạng CSV**, và biểu đồ theo dõi tiến độ học tập cho Sinh viên.

---

## 👥 2. Đội ngũ Phát triển & Phân công WBS

| Thành viên | Vai trò & Trách nhiệm | WBS phụ trách |
| :--- | :--- | :--- |
| **@nhatanh19** (Lead / Dev 1) | System Architect & Fullstack Engineer | **WBS 1.1 - 2.2**: Auth, RBAC, File Parser Engine, CI/CD Pipeline |
| **@thuan734655** (Dev 2) | AI & Prompt Engineer | **WBS 3.1 - 3.3**: LLM Adapter, Bloom Prompts, Matrix Builder, Chunking |
| **@MinusDC** (Dev 3) | Realtime & Exam Engine Engineer | **WBS 4.1 - 4.3**: Exam Lobby, Focused Room, Anti-Cheat Monitor |
| **@MaiVanTinh17072005** (Dev 4) | Data & Tutor Engineer | **WBS 5.1 - 5.3 & 6.1**: Auto-Grading, AI Tutor, Analytics Dashboard & CSV, E2E Testing |

---

## 🛠️ 3. Kiến trúc Công nghệ (Tech Stack)

- **Frontend:** React 18, Vite, TypeScript, Tailwind CSS, Lucide Icons, Vitest, Axios (Cookie HttpOnly withCredentials).
- **Backend:** FastAPI, Python 3.12, SQLAlchemy 2.0 (Core & ORM), Alembic Migrations, Pydantic v2, Pytest.
- **AI & LLM Client:** Resilient OpenAI SDK compatible adapter, hỗ trợ Google Gemini API / OpenAI / Ollama.
- **Database:** PostgreSQL 16 (Hỗ trợ SQLite cho chế độ In-Memory Testing cục bộ).
- **DevOps & Cloud:** Docker, Docker Compose, Nginx Reverse Proxy (xử lý triệt để Cookie SameSite/Lax), Render Blueprint.

---

## 🚀 4. Hướng dẫn Cài đặt & Khởi chạy

### Cách 1: Khởi chạy bằng Docker Compose (Khuyên dùng — 1 Bước duy nhất)

Cách này sẽ tự động khởi tạo cơ sở dữ liệu PostgreSQL, chạy Migration, nạp dữ liệu mẫu (Seed Data), dựng API Backend, dựng Frontend SPA và cấu hình Nginx Gateway cùng chung Origin:

```bash
# 1. Clone repository
git clone https://github.com/nhatanh19/smart-quiz.git
cd smart-quiz

# 2. Khởi chạy toàn bộ hệ thống
docker compose up -d --build
```

Sau khi khởi chạy thành công:
- **Ứng dụng Web (Frontend + Gateway):** [http://localhost](http://localhost) (Cổng 80)
- **Tài liệu Swagger API (Backend Docs):** [http://localhost/docs](http://localhost/docs)

Dừng hệ thống:
```bash
docker compose down
```

---

### Cách 2: Khởi chạy Thủ công Từng thành phần (Local Development)

#### Bước 1: Khởi động Backend (FastAPI)
```bash
cd backend

# Tạo và kích hoạt môi trường ảo Python
python -m venv .venv
# Trên Windows PowerShell:
.\.venv\Scripts\activate
# Trên Linux/macOS:
# source .venv/bin/activate

# Cài đặt thư viện
pip install -r requirements.txt

# Cấu hình biến môi trường
cp .env.example .env

# Chạy Database Migration & Khởi tạo dữ liệu mẫu (Seed Data)
alembic upgrade head
python scripts/seed.py --with-demo-exam

# Khởi động máy chủ backend
uvicorn app.main:app --reload --port 8000
```
API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)

#### Bước 2: Khởi động Frontend (React 18 + Vite)
Mở một cửa sổ dòng lệnh (Terminal) mới:
```bash
cd frontend

# Cài đặt gói phụ thuộc
npm install

# Khởi chạy máy chủ phát triển
npm run dev
```
Truy cập giao diện: [http://localhost:5173](http://localhost:5173)

---

## 🔑 5. Danh mục Tài khoản Demo có sẵn

Hệ thống đã nạp sẵn dữ liệu mẫu phục vụ nghiệm thu (mật khẩu mặc định: `SmartQuiz@123`):

| Vai trò | Email đăng nhập | Mật khẩu | Quyền hạn chính |
| :--- | :--- | :--- | :--- |
| **Giảng viên** (INSTRUCTOR) | `instructor@smartquiz.edu.vn` | `SmartQuiz@123` | Bóc tách tài liệu, AI sinh đề Bloom, Quản lý ca thi, Xem Dashboard & Xuất CSV |
| **Sinh viên** (STUDENT) | `student@smartquiz.edu.vn` | `SmartQuiz@123` | Tham gia phòng thi, nộp bài, xem review, hỏi AI Tutor, xem tiến độ cá nhân |
| **Quản trị viên** (ADMIN) | `admin@smartquiz.edu.vn` | `SmartQuiz@123` | Toàn quyền quản trị hệ thống, quản lý người dùng và danh mục |

---

## 🧪 6. Kịch bản Kiểm thử Khép kín Toàn bộ Luồng (E2E Walkthrough)

Dưới đây là kịch bản kiểm thử mẫu từ đầu đến cuối trên trình duyệt:

1. **Bước 1 — Bóc tách tài liệu (Module 1):**
   - Đăng nhập tài khoản Giảng viên (`instructor@smartquiz.edu.vn`).
   - Vào menu **Parser (M1)** $\rightarrow$ Tải lên tệp tài liệu mẫu (PDF/DOCX/TXT) $\rightarrow$ Xem bảng duyệt trước câu hỏi, chỉnh sửa inline và bấm lưu vào Ngân hàng câu hỏi.
2. **Bước 2 — AI sinh đề theo Ma trận Bloom (Module 2):**
   - Vào menu **AI Gen (M2)** $\rightarrow$ Nhập chủ đề kiểm tra $\rightarrow$ Điều chỉnh tỷ lệ nhận thức (Nhận biết, Thông hiểu, Vận dụng) và định dạng câu hỏi.
   - Bấm **Xem trước Kế hoạch Prompt** $\rightarrow$ Bấm **Sinh câu hỏi theo Ma trận**.
   - Kiểm tra các câu hỏi hiển thị kèm giải thích sư phạm $\rightarrow$ Bấm **Lưu tất cả vào Ngân hàng**.
3. **Bước 3 — Tạo ca thi trực tuyến (Module 3):**
   - Vào menu **Ca thi** $\rightarrow$ Bấm **Tạo ca thi mới** $\rightarrow$ Chọn các câu hỏi vừa tạo, cấu hình thời gian làm bài (VD: 15 phút), mã phòng thi và ngưỡng chuyển tab (mặc định 3 lần) $\rightarrow$ Bấm **Xuất bản ca thi**.
4. **Bước 4 — Sinh viên thi & Kiểm tra Anti-Cheat:**
   - Đăng xuất giảng viên, đăng nhập tài khoản Sinh viên (`student@smartquiz.edu.vn`).
   - Vào mục **Tham gia thi** $\rightarrow$ Nhập mã ca thi $\rightarrow$ Vào phòng thi tập trung.
   - Chọn một số đáp án trắc nghiệm $\rightarrow$ Bấm **F5 (Reload trang)** $\rightarrow$ Xác nhận đáp án vừa chọn vẫn được bảo toàn nguyên vẹn.
   - Thử nghiệm tính năng Anti-cheat: Chuyển sang tab khác 3 lần $\rightarrow$ Hệ thống cảnh báo vi phạm và tự động khóa bài (`LOCKED_VIOLATION`), chuyển thẳng đến giao diện nộp bài thành công.
5. **Bước 5 — Chấm điểm & Gia sư ảo AI Tutor (Module 4):**
   - Tại trang Review kết quả, xem tổng điểm, danh sách chi tiết các câu hỏi đúng/sai và chẩn đoán lỗ hổng kiến thức.
   - Bấm nút **Giải thích bằng AI (AI Tutor)** tại từng câu hỏi $\rightarrow$ Nhận phản hồi phân tích lý do chọn sai và kiến thức cần củng cố.
6. **Bước 6 — Bảng điều khiển Analytics & Xuất CSV (Module 4):**
   - Đăng nhập lại tài khoản Giảng viên $\rightarrow$ Vào **Analytics (M4)**.
   - Xem biểu đồ phổ điểm lớp học (Score Histogram), phân vị điểm và danh sách các câu hỏi có tỷ lệ làm sai cao nhất.
   - Bấm **Xuất danh sách điểm (CSV)** $\rightarrow$ Tải tệp `bang_diem_ca_thi.csv` về máy tính.
   - Sinh viên đăng nhập vào mục **Analytics (M4)** $\rightarrow$ Xem biểu đồ tiến độ học tập cá nhân qua các bài thi.

---

## 📊 7. Kết quả Kiểm thử Tự động (Automated Test Suite)

| Thành phần | Lệnh thực thi | Kết quả kiểm thử |
| :--- | :--- | :--- |
| **Backend API (Pytest)** | `python -m pytest backend/tests -q` | **248 passed, 4 skipped** (100% Core + Analytics + Chunking) |
| **Frontend Unit & Component (Vitest)** | `npm test -- --run` | **84 passed** (7 Test Suites) |
| **Frontend Production Build (TypeScript)** | `npm run build` | **Build PASS** (0 Type Errors, Gzip ~123 KB) |

---

## 📑 8. Tài liệu Quản trị & Báo cáo Nghiệm thu

- [Báo cáo Kiểm thử E2E Hệ thống — Issue #37](./docs/ISSUE_37_TEST_REPORT.md)
- [Tài liệu Bàn giao Issue #37](./docs/ISSUE_37_HANDOFF.md)
- [Khung Kịch bản Slide Báo cáo Nghiệm thu Tuần 13](./docs/SLIDE_SHOWCASE_OUTLINE.md)
- [Ghi chú Phát hành Release v2.0.0-final](./docs/FINAL_RELEASE_V2.0_NOTES.md)
- [Định nghĩa Hoàn thành (Definition of Done)](./docs/DEFINITION_OF_DONE.md)
- [Sổ theo dõi Rủi ro Dự án (Risk Register)](./docs/RISK_REGISTER.md)
- [Biên bản Họp Retrospective Sprint 1](./docs/RETROSPECTIVE_SPRINT_1.md)
- [Đặc tả Cơ sở Dữ liệu & Hướng dẫn Cài đặt](./docs/DATABASE_GUIDE.md)
- [Tài liệu Kiến trúc Chuẩn hóa Kỹ thuật](./TECH_STACK.md)
- [Quy ước Xác thực & Cookie HttpOnly](./docs/AUTHENTICATION.md)

---

*Hà Nội, Học kỳ 1 Năm học 2026-2027 — Nhóm phát triển Smart Quiz kính báo cáo.*
