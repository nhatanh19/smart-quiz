# 🧠 Smart Quiz — AI-Powered Online Assessment Platform

> **Nền tảng Kiểm tra và Ôn luyện Trắc nghiệm Trực tuyến Tích hợp Trí tuệ Nhân tạo**  
> Dự án môn học: Quản trị Dự án Phần mềm

---

## 📌 Giới thiệu Dự án

**Smart Quiz** là giải pháp toàn diện hỗ trợ Giảng viên và Sinh viên trong toàn bộ chu trình kiểm tra, đánh giá và ôn luyện kiến thức:
1. **Module 1 (File Parser & Question Bank):** Bóc tách tài liệu tự động (PDF, DOCX, TXT) bằng biểu thức chính quy thành các câu hỏi trắc nghiệm, quản lý ngân hàng câu hỏi theo chuyên đề và mức độ nhận thức Bloom.
2. **Module 2 (AI Quiz Generator & Exam Matrix):** Sinh đề thi thông minh bám sát ma trận năng lực và ngữ cảnh tài liệu học liệu bằng mô hình ngôn ngữ lớn (LLM - OpenAI / Gemini).
3. **Module 3 (Online Exam Engine & Anti-Cheat):** Tổ chức thi trực tuyến với thuật toán xáo trộn câu hỏi/đáp án độc lập cho từng thí sinh, giao diện tập trung và hệ thống giám sát vi phạm (chuyển tab, mất tiêu điểm, chặn sao chép).
4. **Module 4 (Auto-Grading, AI Tutor & Analytics):** Chấm điểm tự động tức thì, tích hợp Gia sư ảo (AI Tutor) giải thích chi tiết phương án và bảng phân tích tiến độ học tập / phổ điểm lớp học.

---

## 🏗️ Cấu trúc Monorepo

```text
smart-quiz/
├── docs/                             # Hồ sơ Quản trị Dự án (Charter, WBS, Backlog, Guide)
├── TECH_STACK.md                     # Tài liệu chuẩn hóa công nghệ & quy ước dự án
├── backend/                          # FastAPI + SQLAlchemy 2.0 + Alembic + OpenAI SDK
│   ├── alembic/                      # Database Migrations
│   ├── app/                          # Core, Models, Schemas, Routers 4 Modules
│   └── scripts/                      # Seed scripts khởi tạo dữ liệu mẫu
└── frontend/                         # React 18 (Vite + TypeScript) + Tailwind CSS + shadcn/ui
    └── src/                          # Routes, Layouts, Placeholders 4 Modules, API Client
```

---

## 🚀 Khởi chạy Nhanh (Quick Start)

### 1. Khởi chạy Backend
```bash
cd backend
python -m venv venv
# Kích hoạt venv (Windows):
.\venv\Scripts\activate
# Cài đặt thư viện:
pip install -r requirements.txt
# Cấu hình biến môi trường:
cp .env.example .env
# Chạy Migration & Seed data:
alembic upgrade head
python scripts/seed.py
# Khởi động máy chủ:
uvicorn app.main:app --reload --port 8000
```
Swagger UI API Docs: `http://localhost:8000/docs`

### 2. Khởi chạy Frontend
```bash
cd frontend
# Cài đặt dependencies:
npm install
# Cấu hình biến môi trường:
cp .env.example .env
# Chạy máy chủ phát triển:
npm run dev
```
Truy cập ứng dụng: `http://localhost:5173`

---

## 📖 Tài liệu Kỹ thuật Chi tiết
Vui lòng tham khảo tệp [TECH_STACK.md](./TECH_STACK.md) để xem chi tiết kiến trúc, bảng phân chia công việc cho 4 thành viên (Dev 1 -> Dev 4), cấu hình LLM Custom Host và quy chuẩn lập trình.
