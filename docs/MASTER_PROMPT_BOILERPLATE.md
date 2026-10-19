# ROLE & EXECUTION DIRECTIVE
Bạn là một Senior Full-stack Developer thực thi nhiệm vụ dưới sự điều khiển của Solution Architect. 
Nhiệm vụ của bạn là khởi tạo **Khung mã nguồn Full-stack (Project Boilerplate), Sơ đồ CSDL tổng thể (ERD), Cấu hình ORM/Migration/Seed Data và Tài liệu Công nghệ** cho dự án **Smart Quiz** (Nền tảng Kiểm tra và Ôn luyện Trắc nghiệm Trực tuyến Tích hợp AI).

## ⚠️ NGUYÊN TẮC BẮT BUỘC (STRICT RULES)
1. **Chỉ triển khai đúng kiến trúc đã khóa cứng bên dưới:** Không tự ý thay đổi công nghệ, không hỏi lại các lựa chọn kỹ thuật.
2. **Giới hạn phạm vi ở Khung nền tảng (Base Boilerplate - WBS 1.1):** 
   - Chỉ tạo cấu trúc thư mục, cấu hình hệ thống, Database Models, Alembic Migration, Seed script, Base API Routers (chỉ gồm endpoint health-check/placeholder), Base LLM Client Adapter và Base Layout Shells (`<Outlet />`) trên Frontend.
   - **TUYỆT ĐỐI KHÔNG** triển khai giao diện chi tiết (không code form upload, không code màn hình làm bài thi, không code biểu đồ) và **KHÔNG** viết logic nghiệp vụ chi tiết của từng mô-đun. Các trang chỉ dừng lại ở Component rỗng hiển thị tên Mô-đun kèm chú thích `// TODO` để bàn giao cho 4 thành viên trong nhóm phát triển.
3. **Bắt buộc tạo file `TECH_STACK.md`:** Ghi nhận đầy đủ công nghệ, thư viện, kiến trúc và quy ước của dự án để toàn bộ thành viên trong nhóm tra cứu.

---

# 1. KIẾN TRÚC CÔNG NGHỆ KHÓA CỨNG (LOCKED-IN TECH STACK)

- **Mô hình Repository:** Standard Monorepo gồm `/frontend`, `/backend`, `/docs`, và file `TECH_STACK.md` ở thư mục gốc.
- **Frontend (`/frontend`):**
  - Core: React 18+ (Vite + TypeScript).
  - Routing: `react-router-dom` v6+ (cấu hình sẵn khung ProtectedRoute phân quyền RBAC: `ADMIN`, `INSTRUCTOR`, `STUDENT`).
  - Styling & UI Base: Tailwind CSS, cấu hình nền tảng `shadcn/ui` (`clsx`, `tailwind-merge`, `lucide-react`, biến CSS chuẩn trong `index.css` và hàm `cn()` trong `src/lib/utils.ts`).
  - Networking: `axios` (cấu hình sẵn instance `apiClient` đọc `VITE_API_BASE_URL` và interceptor đính kèm JWT Token từ `localStorage`).
- **Backend (`/backend`):**
  - Core: Python 3.11+ với **FastAPI** & `uvicorn`.
  - Validation & Config: **Pydantic v2** (`pydantic`, `pydantic-settings`).
  - Database & ORM: **PostgreSQL** (hỗ trợ Supabase/Neon), **SQLAlchemy 2.0** (`sqlalchemy`, `psycopg2-binary`) và **Alembic** (`alembic`) để chạy Migration.
  - AI Integration: **OpenAI Python SDK** (`openai`) được cấu hình **Custom Host (`base_url`)** thông qua biến môi trường để kết nối linh hoạt tới bất kỳ LLM Provider nào tương thích chuẩn OpenAI API.
  - Thư viện nền tảng cài sẵn trong `requirements.txt` cho các mô-đun: `pyjwt`, `passlib[bcrypt]`, `python-multipart`, `pymupdf` (xử lý PDF), `python-docx` (xử lý DOCX), `tenacity` (xử lý retry cho AI API).

---

# 2. CẤU TRÚC THƯ MỤC MONOREPO CẦN KHỞI TẠO

Hãy tạo chính xác cây thư mục và các tệp tin khung như sau:

```text
smart-quiz/
├── .gitignore
├── .editorconfig
├── README.md
├── TECH_STACK.md                     # Tài liệu ghi nhận toàn bộ công nghệ dự án
│
├── backend/
│   ├── .env.example
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   ├── scripts/
│   │   └── seed.py                   # Kịch bản tạo dữ liệu mẫu ban đầu
│   └── app/
│       ├── __init__.py
│       ├── main.py                   # Điểm khởi chạy FastAPI, cấu hình CORS & gắn Routers
│       ├── core/
│       │   ├── config.py             # Quản lý biến môi trường bằng Pydantic BaseSettings
│       │   ├── database.py           # Khởi tạo SQLAlchemy Engine, SessionLocal, Base, get_db
│       │   ├── security.py           # Khung hàm tạo/xác thực JWT & Dependency kiểm tra Role (RBAC)
│       │   └── llm_client.py         # Adapter OpenAI SDK Custom Host + ép kiểu JSON Schema bằng Pydantic
│       ├── models/                   # Toàn bộ SQLAlchemy ORM Models (ERD tổng thể)
│       │   ├── __init__.py
│       │   └── entities.py
│       ├── schemas/                  # Khung Pydantic Schemas dùng chung
│       │   ├── __init__.py
│       │   └── common.py
│       └── modules/                  # Chia tách độc lập 4 mô-đun cho 4 Dev làm việc song song
│           ├── auth/                 # WBS 1.2 - Xác thực & Phân quyền
│           │   └── router.py
│           ├── parser/               # Module 1 (Dev 1): File Parser (PDF/DOCX/TXT) & Question Bank
│           │   └── router.py
│           ├── ai_generator/         # Module 2 (Dev 2): AI Quiz Generator & Exam Matrix
│           │   └── router.py
│           ├── exam_engine/          # Module 3 (Dev 3): Online Exam, Shuffling & Client Anti-cheat
│           │   └── router.py
│           └── tutor_analytics/      # Module 4 (Dev 4): Auto-Grading, AI Tutor & Analytics
│               └── router.py
│
└── frontend/
    ├── .env.example
    ├── package.json
    ├── tsconfig.json
    ├── vite.config.ts
    ├── tailwind.config.js
    ├── components.json               # File cấu hình base của shadcn/ui
    ├── index.html
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── index.css
        ├── lib/
        │   ├── utils.ts              # Hàm cn() của shadcn/ui
        │   └── api-client.ts         # Cấu hình Axios instance & JWT Interceptors
        ├── types/
        │   └── index.ts              # Khai báo TypeScript Interfaces đồng bộ với ERD & Enums
        ├── routes/
        │   ├── AppRoutes.tsx         # Định tuyến tổng thể ứng dụng
        │   └── ProtectedRoute.tsx    # Wrapper kiểm tra đăng nhập & phân quyền (Role-based Guard)
        ├── layouts/                  # CHỈ TẠO KHUNG BASE CONTAINER (<Outlet/>), KHÔNG CODE UI CHI TIẾT
        │   ├── AuthLayout.tsx        # Khung bọc các trang xác thực (Login/Register)
        │   ├── MainLayout.tsx        # Khung bọc không gian làm việc chung (Admin/Instructor/Student)
        │   └── ExamFocusLayout.tsx   # Khung bọc phòng thi tập trung (tách biệt cho Module 3)
        └── pages/                    # Các trang Placeholder rỗng bàn giao cho 4 Dev
            ├── auth/
            │   └── LoginPlaceholder.tsx
            ├── parser/
            │   └── ParserPlaceholder.tsx
            ├── ai-generator/
            │   └── AiGenPlaceholder.tsx
            ├── exam/
            │   └── ExamPlaceholder.tsx
            └── tutor-analytics/
                └── AnalyticsPlaceholder.tsx
```

---

# 3. ĐẶC TẢ CHI TIẾT CÁC THÀNH PHẦN CẦN TRIỂN KHAI

## 3.1. Sơ đồ CSDL Quan hệ Tổng thể (ERD trong `backend/app/models/entities.py`)
Sử dụng **SQLAlchemy 2.0 (`DeclarativeBase`, `Mapped`, `mapped_column`)** và kiểu dữ liệu `JSONB` của PostgreSQL để định nghĩa đầy đủ các bảng cốt lõi sau:

1. **Enums chuẩn:**
   - `UserRole`: `ADMIN`, `INSTRUCTOR`, `STUDENT`
   - `QuestionType`: `SINGLE_CHOICE`, `MULTIPLE_CHOICE`, `TRUE_FALSE`
   - `CognitiveLevel` (Thang nhận thức Bloom): `REMEMBER` (Nhận biết), `UNDERSTAND` (Thông hiểu), `APPLY` (Vận dụng)
   - `AttemptStatus`: `IN_PROGRESS`, `SUBMITTED`, `LOCKED_VIOLATION`, `EXPIRED`
2. **Các bảng thực thể (Tables):**
   - `users`: `id` (UUID/Int PK), `email` (Unique), `password_hash`, `full_name`, `role` (`UserRole`), `is_active`, `created_at`.
   - `categories` (Chuyên đề / Học phần): `id`, `name`, `description`, `created_by` (FK -> `users.id`), `created_at`.
   - `questions` (Ngân hàng câu hỏi): `id`, `category_id` (FK -> `categories.id`), `creator_id` (FK -> `users.id`), `content` (Text), `question_type` (`QuestionType`), `cognitive_level` (`CognitiveLevel`), `options` (`JSONB` - lưu mảng các phương án `[{"id": "A", "text": "...", "is_correct": true}]`), `explanation` (Text - giải thích gốc nếu có), `source_type` (`MANUAL`, `FILE_PARSER`, `AI_GENERATED`), `created_at`.
   - `exams` (Kỳ thi / Đề thi): `id`, `title`, `description`, `instructor_id` (FK -> `users.id`), `duration_minutes` (Int), `start_time`, `end_time`, `access_password` (Nullable), `max_attempts` (Int, default 1), `max_tab_violations` (Int, default 3), `shuffle_questions` (Boolean), `shuffle_options` (Boolean), `matrix_config` (`JSONB` - lưu cấu hình ma trận độ khó), `is_published` (Boolean), `created_at`.
   - `exam_questions` (Bảng trung gian Đề thi - Câu hỏi): `id`, `exam_id` (FK -> `exams.id`), `question_id` (FK -> `questions.id`), `order_index` (Int), `points` (Float, default 1.0).
   - `exam_attempts` (Lượt làm bài của Sinh viên): `id`, `exam_id` (FK -> `exams.id`), `student_id` (FK -> `users.id`), `started_at`, `submitted_at`, `score` (Float, Nullable), `status` (`AttemptStatus`), `violation_count` (Int, default 0), `question_order_snapshot` (`JSONB` - lưu thứ tự câu hỏi/đáp án đã trộn riêng cho thí sinh này).
   - `attempt_answers` (Chi tiết câu trả lời): `id`, `attempt_id` (FK -> `exam_attempts.id`), `question_id` (FK -> `questions.id`), `selected_options` (`JSONB` - mảng ID đáp án sinh viên chọn), `is_correct` (Boolean, Nullable), `ai_tutor_feedback` (`JSONB`, Nullable - lưu lời giải thích ngữ cảnh và gợi ý ôn tập từ AI Tutor).
   - `anti_cheat_logs` (Nhật ký giám sát chống gian lận): `id`, `attempt_id` (FK -> `exam_attempts.id`), `event_type` (String: `TAB_SWITCH`, `WINDOW_BLUR`, `COPY_PASTE_ATTEMPT`), `logged_at`, `metadata_info` (`JSONB`).

## 3.2. Cấu hình Alembic & Seed Data (`backend/scripts/seed.py`)
- Kết nối `Base.metadata` từ `app.models.entities` vào `alembic/env.py` để lệnh `alembic revision --autogenerate` hoạt động ngay lập tức.
- Viết kịch bản `seed.py` khởi tạo:
  - 3 tài khoản mẫu ứng với 3 vai trò: `admin@smartquiz.edu.vn`, `instructor@smartquiz.edu.vn`, `student@smartquiz.edu.vn` (mật khẩu chung `SmartQuiz@123`).
  - 1 chuyên đề mẫu ("Quản trị Dự án Phần mềm") và 3 câu hỏi mẫu đại diện cho 3 loại câu hỏi (`SINGLE_CHOICE`, `MULTIPLE_CHOICE`, `TRUE_FALSE`) ở 3 mức độ nhận thức (`REMEMBER`, `UNDERSTAND`, `APPLY`).

## 3.3. Adapter OpenAI SDK Custom Host (`backend/app/core/llm_client.py`)
- Đọc cấu hình từ `app/core/config.py`:
  - `LLM_BASE_URL` (ví dụ: `https://api.openai.com/v1` hoặc bất kỳ Custom Host / Proxy / Gemini OpenAI-compatible URL nào).
  - `LLM_API_KEY`
  - `LLM_MODEL_NAME`
  - `LLM_TIMEOUT_SECONDS` (mặc định `30.0`).
- Khởi tạo class `LLMClientAdapter` sử dụng `AsyncOpenAI(api_key=..., base_url=..., timeout=...)` từ thư viện `openai`.
- Cung cấp sẵn phương thức khung `generate_structured_json(system_prompt: str, user_prompt: str, response_schema: Type[BaseModel])` hỗ trợ gọi LLM và ép kiểu dữ liệu phản hồi tuân thủ 100% `Pydantic BaseModel` (`JSON Schema`), kèm cơ chế retry và bắt ngoại lệ an toàn.

## 3.4. Khung Layout & Routing Cơ sở trên Frontend (`/frontend`)
- **Nguyên tắc:** Không xây dựng giao diện chi tiết. Chỉ tạo các khung chứa (`Layout Wrappers`) sử dụng `<Outlet />` của `react-router-dom` và các trang Placeholder đơn giản để 4 thành viên tự phát triển giao diện mô-đun của mình.
- Thiết lập 3 file Layout cơ sở trong `src/layouts/`:
  1. `AuthLayout.tsx`: Thẻ `<main>` căn giữa màn hình chứa `<Outlet />`.
  2. `MainLayout.tsx`: Khung `<div className="min-h-screen flex flex-col">` có vùng `<header>` cơ bản (hiển thị tên dự án & liên kết điều hướng nhanh tới các route mô-đun) và vùng `<main className="flex-1">` chứa `<Outlet />`.
  3. `ExamFocusLayout.tsx`: Khung `<div className="min-h-screen">` tách biệt hoàn toàn với `MainLayout` (không có thanh menu chung) chứa `<Outlet />` để bàn giao cho Dev 3 phát triển giao diện phòng thi tập trung và chống gian lận.
- Thiết lập `src/routes/AppRoutes.tsx` ánh xạ sẵn các đường dẫn gốc cho 4 mô-đun:
  - `/auth/login` -> `LoginPlaceholder`
  - `/parser` -> `ParserPlaceholder` (Module 1 - Dev 1)
  - `/ai-generator` -> `AiGenPlaceholder` (Module 2 - Dev 2)
  - `/exam` -> `ExamPlaceholder` (Module 3 - Dev 3)
  - `/analytics` -> `AnalyticsPlaceholder` (Module 4 - Dev 4)

## 3.5. Soạn thảo File `TECH_STACK.md`
Tạo file `TECH_STACK.md` tại thư mục gốc của dự án, trình bày rõ ràng bằng tiếng Việt các nội dung sau:
1. **Tổng quan Kiến trúc Hệ thống:** Mô hình Monorepo Client-Server.
2. **Danh mục Công nghệ Frontend:** Ngôn ngữ, Framework, Build Tool, Routing, UI/Styling, HTTP Client, mục đích sử dụng của từng thư viện.
3. **Danh mục Công nghệ Backend:** Ngôn ngữ, Web Framework, Validation (Pydantic v2), Xử lý tệp tài liệu (`PyMuPDF`, `python-docx`), Xác thực (JWT/Bcrypt).
4. **Cơ sở dữ liệu & ORM:** PostgreSQL (`JSONB`), SQLAlchemy 2.0, Alembic Migration.
5. **Tích hợp AI (LLM Service):** Cơ chế hoạt động của OpenAI SDK với Custom Host (`LLM_BASE_URL`) và cơ chế kiểm soát `JSON Schema`.
6. **Phân bổ Thư mục theo 4 Mô-đun cho Nhóm Phát triển (Dev 1 -> Dev 4):** Bảng chỉ dẫn rõ mỗi thành viên sẽ làm việc tại thư mục nào ở `/backend/app/modules/` và `/frontend/src/pages/` để tránh xung đột Git.
7. **Hướng dẫn Cài đặt & Khởi chạy Nhanh (Local Setup):** Các câu lệnh khởi tạo `venv`, cài đặt `requirements.txt`, chạy `alembic`, chạy `seed.py` và chạy `npm install` / `npm run dev`.

---

# 4. YÊU CẦU ĐẦU RA (DELIVERABLES)
Hãy tiến hành tạo tuần tự đầy đủ toàn bộ các file cấu hình, mã nguồn khung Backend, mã nguồn khung Frontend và tài liệu `TECH_STACK.md` theo đúng thiết kế trên. Đảm bảo mã nguồn sạch, có chú thích rõ ràng vị trí bàn giao cho từng mô-đun và không chứa lỗi cú pháp.
