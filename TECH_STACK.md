# 📘 TÀI LIỆU CÔNG NGHỆ & QUY CHUẨN KỸ THUẬT (TECH STACK SPECIFICATION)
## DỰ ÁN: SMART QUIZ — NỀN TẢNG KIỂM TRA VÀ ÔN LUYỆN TRẮC NGHIỆM TRỰC TUYẾN TÍCH HỢP AI

---

## 1. Tổng quan Kiến trúc Hệ thống (System Architecture Overview)

Hệ thống **Smart Quiz** được tổ chức theo mô hình **Standard Monorepo Client-Server** phân tách hoàn toàn giữa lớp giao diện người dùng (Frontend SPA) và lớp dịch vụ lõi nghiệp vụ (Backend API Service):

```text
+-----------------------------------------------------------------------------------+
|                                 CLIENT TIER                                       |
|  Single Page Application (React 18 + Vite + TypeScript + Tailwind CSS + shadcn)   |
|  Axios API Client + JWT Auth Interceptors + RBAC Route Guards (Admin/Inst/Stud)   |
+-----------------------------------------------------------------------------------+
                                        |  HTTPS / JSON RESTful APIs
                                        v
+-----------------------------------------------------------------------------------+
|                                 SERVER TIER                                       |
|  FastAPI (Python 3.11+) + Uvicorn + Pydantic v2 + Pydantic Settings               |
|  Security Core: OAuth2 Bearer JWT + Passlib (Bcrypt) RBAC Middleware              |
|  Modular Architecture: Auth | Parser | AI-Generator | Exam-Engine | Tutor-Analytics|
+-----------------------------------------------------------------------------------+
             |                                                  |
             | SQLAlchemy 2.0 ORM                               | OpenAI Python SDK (Async)
             v                                                  v
+---------------------------------------+      +------------------------------------+
|            PERSISTENCE TIER           |      |        EXTERNAL AI SERVICES        |
|  PostgreSQL (Supabase / Neon / Local) |      |  Custom Host (OpenAI / Gemini      |
|  Native JSONB + Alembic Migrations    |      |  compatible proxy) + JSON Schema   |
+---------------------------------------+      +------------------------------------+
```

- **Mô hình Monorepo:** Gom toàn bộ mã nguồn Frontend, Backend và Hồ sơ Dự án (`/docs`) vào cùng một kho lưu trữ Git giúp đơn giản hóa quy trình tích hợp liên tục (CI/CD), đồng bộ định nghĩa kiểu dữ liệu và phối hợp giữa 4 kỹ sư phát triển.
- **Phân tách trách nhiệm (Separation of Concerns):** Mỗi mô-đun nghiệp vụ tại Backend được đóng gói độc lập trong `backend/app/modules/`, tương ứng với các phân trang tại `frontend/src/pages/`.

---

## 2. Danh mục Công nghệ Frontend (`/frontend`)

| Thành phần | Công nghệ / Thư viện | Phiên bản | Mục đích sử dụng |
| :--- | :--- | :--- | :--- |
| **Ngôn ngữ** | TypeScript | `^5.x` | Cung cấp kiểm soát kiểu tĩnh (Static Typing), hạn chế lỗi Runtime, đồng bộ Interface với Schema Backend. |
| **Giao diện cốt lõi** | React | `^18.2` | Thư viện xây dựng Single Page Application hiện đại với cơ chế React Hooks và Virtual DOM hiệu năng cao. |
| **Build Tool** | Vite | `^5.x` | Công cụ đóng gói mã nguồn siêu tốc (HMR dưới 50ms, Native ES Modules), tối ưu hóa quá trình Build. |
| **Điều hướng & Định tuyến** | `react-router-dom` | `^6.22` | Quản lý định tuyến phía Client, hỗ trợ phân cấp Layout lồng nhau (`<Outlet />`) và bảo vệ tuyến đường (`ProtectedRoute` RBAC). |
| **CSS Framework** | Tailwind CSS | `^3.4` | Thiết kế giao diện theo mô hình Utility-first CSS, đồng nhất bảng màu, Typography và Responsive. |
| **UI Component Base** | `shadcn/ui` ecosystem | Latest | Bộ cấu hình UI chuẩn (`components.json`, `index.css` với CSS Variables, `clsx`, `tailwind-merge` và hàm `cn()`). |
| **Bộ Icon** | `lucide-react` | `^0.350` | Hệ thống biểu tượng giao diện vector chất lượng cao, dung lượng nhẹ. |
| **HTTP Networking** | Axios | `^1.6` | Client gửi yêu cầu HTTP/REST, cấu hình Base URL linh hoạt và Request Interceptor tự động gắn Bearer JWT Token từ `localStorage`. |

---

## 3. Danh mục Công nghệ Backend (`/backend`)

| Thành phần | Công nghệ / Thư viện | Phiên bản | Mục đích sử dụng |
| :--- | :--- | :--- | :--- |
| **Môi trường & Ngôn ngữ** | Python | `3.11+` | Ngôn ngữ phát triển Backend chính với cú pháp hiện đại và hỗ trợ Type Hints đầy đủ. |
| **Web Framework** | FastAPI | `^0.110` | Web framework bất đồng bộ (Asynchronous ASGI) hiệu năng cực cao, tự động sinh tài liệu Swagger OpenAPI UI. |
| **Máy chủ ASGI** | Uvicorn | `^0.29` | Máy chủ chạy ứng dụng FastAPI chuẩn ASGI với cờ `--reload` cho môi trường phát triển. |
| **Xác thực dữ liệu** | Pydantic v2 (`pydantic`, `pydantic-settings`) | `^2.6` | Ép kiểu, kiểm tra tính hợp lệ của Request Payload/Response, quản lý biến môi trường an toàn từ `.env`. |
| **Mã hóa & Xác thực** | `pyjwt`, `passlib[bcrypt]` | Latest | Băm mật khẩu người dùng với thuật toán Bcrypt, phát hành và giải mã JWT Access Token xác thực danh tính. |
| **Xử lý tệp tải lên** | `python-multipart` | Latest | Xử lý đa luồng tệp tin tải lên (Multipart form-data) qua REST API. |
| **Bóc tách tệp PDF** | `PyMuPDF` (`fitz`) | `^1.24` | Trích xuất văn bản thô, bảng biểu và cấu trúc tài liệu PDF tốc độ cao, hỗ trợ tiếng Việt có dấu. |
| **Bóc tách tệp DOCX** | `python-docx` | `^1.1` | Đọc cấu trúc đoạn văn bản (`paragraphs`, `tables`) từ tệp Word tài liệu ôn tập và ngân hàng câu hỏi. |
| **Cơ chế Retry AI** | `tenacity` | `^8.2` | Bộ bọc hàm thử lại (Exponential Backoff Retry) khi gọi API bên thứ ba gặp lỗi kết nối hoặc Rate Limit. |

---

## 4. Cơ sở Dữ liệu & ORM (Database & Migration)

- **Hệ quản trị CSDL:** **PostgreSQL** (Tương thích 100% với các dịch vụ Cloud DB Free-tier như Supabase, Neon hoặc PostgreSQL cài cục bộ).
- **Trường lưu trữ linh hoạt (`JSONB`):** 
  - Lưu mảng các phương án lựa chọn và đáp án đúng trong bảng `questions` (`options: JSONB`).
  - Lưu ma trận tỷ lệ câu hỏi theo độ khó trong bảng `exams` (`matrix_config: JSONB`).
  - Lưu thứ tự câu hỏi và đáp án đã xáo trộn riêng cho từng thí sinh trong bảng `exam_attempts` (`question_order_snapshot: JSONB`).
  - Lưu đáp án lựa chọn và lời giải thích của Gia sư ảo trong bảng `attempt_answers` (`ai_tutor_feedback: JSONB`).
  - Lưu thông tin chi tiết nhật ký chống gian lận trong bảng `anti_cheat_logs` (`metadata_info: JSONB`).
- **ORM:** **SQLAlchemy 2.0** sử dụng cú pháp chuẩn hiện đại: `DeclarativeBase`, `Mapped[...]`, `mapped_column(...)`, hỗ trợ hoàn hảo kiểm tra kiểu tĩnh với `mypy`/`pylance`.
- **Quản lý Migration:** **Alembic** liên kết trực tiếp `Base.metadata` từ `app.models.entities`, cho phép phát sinh phiên bản CSDL tự động qua lệnh `alembic revision --autogenerate`.

---

## 5. Tích hợp AI (LLM Service Adapter)

Hệ thống cung cấp sẵn lớp chuyển tiếp **`LLMClientAdapter`** tại `backend/app/core/llm_client.py`:
- **OpenAI Python SDK với Custom Host:**
  - Khởi tạo client thông qua `AsyncOpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL, timeout=settings.LLM_TIMEOUT_SECONDS)`.
  - Nhờ cơ chế `base_url`, hệ thống dễ dàng kết nối tới:
    1. **OpenAI chính thức:** `https://api.openai.com/v1` (Models: `gpt-4o`, `gpt-4o-mini`).
    2. **Google Gemini (OpenAI-compatible Endpoint):** `https://generativelanguage.googleapis.com/v1beta/openai/` (Models: `gemini-1.5-flash`, `gemini-1.5-pro`).
    3. **Local/Self-hosted LLMs:** Ollama / vLLM / LocalAI (`http://localhost:11434/v1`).
- **Ép kiểu dữ liệu chuẩn (Strict JSON Schema via Pydantic):**
  - Hàm `generate_structured_json(system_prompt, user_prompt, response_schema)` sử dụng tính năng Structured Outputs của OpenAI SDK (`response_format={"type": "json_object"}` hoặc OpenAI parse schema).
  - Tự động bắt lỗi cú pháp JSON và ép kiểu dữ liệu trả về thành đối tượng `Pydantic BaseModel`, đảm bảo dữ liệu sinh câu hỏi trắc nghiệm không bao giờ bị lệch cấu trúc.
  - Tích hợp decorator `@retry` từ `tenacity` để tự động thử lại khi gặp lỗi mạng tạm thời hoặc hạn mức cuộc gọi.

---

## 6. Phân bổ Thư mục theo 4 Mô-đun cho Nhóm Phát triển (Dev 1 -> Dev 4)

Để đảm bảo quy trình làm việc độc lập, song song và hạn chế tối đa xung đột mã nguồn (Git merge conflicts), không gian làm việc được phân định rõ ràng như sau:

| Thành viên | Trách nhiệm chính (WBS) | Thư mục Backend (`backend/app/modules/`) | Thư mục Frontend (`frontend/src/pages/`) |
| :--- | :--- | :--- | :--- |
| **Dev 1 (Team Leader)** | **Module 1:** File Parser Engine (PDF/DOCX/TXT) & Question Bank CRUD (WBS 1.1, 2.1, 2.2) | `backend/app/modules/parser/` | `frontend/src/pages/parser/` |
| **Dev 2 (AI Engineer)** | **Module 2:** AI Quiz Generator, Exam Matrix Builder & Document Context Quiz (WBS 3.1, 3.2, 3.3) | `backend/app/modules/ai_generator/` | `frontend/src/pages/ai-generator/` |
| **Dev 3 (Core Engine)** | **Module 3:** Auth/RBAC, Online Exam Engine, Shuffling & Anti-cheat Monitor (WBS 1.2, 4.1, 4.2, 4.3) | `backend/app/modules/auth/`<br/>`backend/app/modules/exam_engine/` | `frontend/src/pages/auth/`<br/>`frontend/src/pages/exam/` |
| **Dev 4 (Data & Tutor)** | **Module 4:** Auto-Grading Engine, Contextual AI Tutor & Analytics Dashboard (WBS 5.1, 5.2, 5.3) | `backend/app/modules/tutor_analytics/` | `frontend/src/pages/tutor-analytics/` |

> ⚠️ **Quy tắc phối hợp:** Mỗi thành viên chỉ chỉnh sửa trong thư mục được phân công. Các thay đổi liên quan đến bảng CSDL dùng chung (`backend/app/models/entities.py`) hoặc cấu hình chung (`core/`, `lib/`) cần thông báo và trao đổi trước với Dev 1 (Team Leader).

---

## 7. Hướng dẫn Cài đặt & Khởi chạy Nhanh (Local Setup Guide)

### 7.1. Chuẩn bị Môi trường
- Python 3.11+
- Node.js 18+ & npm 9+
- PostgreSQL (Cài đặt cục bộ hoặc lấy Connection URL miễn phí từ Supabase / Neon)

---

### 7.2. Cài đặt & Chạy Backend

1. **Di chuyển vào thư mục backend:**
   ```bash
   cd backend
   ```

2. **Khởi tạo và kích hoạt môi trường ảo (Virtual Environment):**
   - Trên Windows (PowerShell):
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - Trên Linux / macOS:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Cài đặt các gói thư viện phụ thuộc:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Thiết lập biến môi trường:**
   - Sao chép tệp mẫu:
     ```bash
     cp .env.example .env
     ```
   - Chỉnh sửa giá trị `DATABASE_URL`, `SECRET_KEY`, `LLM_API_KEY` trong tệp `.env`.

5. **Chạy Cơ chế Cập nhật CSDL (Alembic Migration):**
   ```bash
   alembic upgrade head
   ```

6. **Khởi tạo Dữ liệu Mẫu Ban đầu (Seed Data):**
   ```bash
   python scripts/seed.py
   ```
   *Dữ liệu mẫu khởi tạo gồm 3 tài khoản (`admin@smartquiz.edu.vn`, `instructor@smartquiz.edu.vn`, `student@smartquiz.edu.vn` với mật khẩu chung `SmartQuiz@123`), 1 học phần và 3 câu hỏi mẫu đa dạng cấp độ nhận thức.*

7. **Khởi động Máy chủ API:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   - Truy cập Swagger API Docs tại: `http://localhost:8000/docs`
   - Truy cập Redoc tại: `http://localhost:8000/redoc`

---

### 7.3. Cài đặt & Chạy Frontend

1. **Di chuyển vào thư mục frontend:**
   ```bash
   cd frontend
   ```

2. **Cài đặt các gói thư viện Node modules:**
   ```bash
   npm install
   ```

3. **Thiết lập biến môi trường:**
   - Sao chép tệp mẫu:
     ```bash
     cp .env.example .env
     ```
   - Kiểm tra `VITE_API_BASE_URL` mặc định là `http://localhost:8000/api/v1`.

4. **Khởi động Máy chủ Phát triển Vite:**
   ```bash
   npm run dev
   ```
   - Mở trình duyệt tại: `http://localhost:5173`
   - Điều hướng nhanh qua thanh Header để kiểm tra các Route Placeholder của 4 Mô-đun.
