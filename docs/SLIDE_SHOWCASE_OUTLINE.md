# Khung Kịch bản Slide Báo cáo Nghiệm thu Đồ án Tuần 13

> **Học phần:** Quản trị Dự án Phần mềm  
> **Đề tài:** Smart Quiz — Nền tảng Đánh giá & Ôn luyện Trắc nghiệm Trực tuyến Tích hợp Trí tuệ Nhân tạo  
> **Nhóm thực hiện:** Nhóm 4 thành viên (@nhatanh19, @MinusDC, @thuan734655, @MaiVanTinh17072005)  
> **Thời lượng báo cáo dự kiến:** 15 phút trình bày + 5 phút hỏi đáp (Q&A)

---

## 🎯 Cấu trúc Slide Thuyết trình (Tổng quan 12 Slides)

### Slide 1: Trang Tiêu đề & Giới thiệu Đội ngũ
- **Tiêu đề:** SMART QUIZ — Nền tảng Đánh giá & Khảo thí Trắc nghiệm Trực tuyến Thông minh.
- **Thành viên & Phân công vai trò:**
  - @nhatanh19 — Project Manager & Backend Architect (WBS 1 & 2: Auth, File Parser)
  - @thuan734655 — AI & Prompt Engineer (WBS 3: LLM Adapter, Bloom Matrix Generator)
  - @MinusDC — Realtime & Exam Engine Engineer (WBS 4: Exam Lobby, Anti-Cheat Monitor)
  - @MaiVanTinh17072005 — Data & Tutor Engineer (WBS 5: Auto-Grading, AI Tutor, Analytics)

### Slide 2: Vấn đề Thực tiễn & Mục tiêu Dự án
- **Thực trạng khảo thí trắc nghiệm truyền thống:**
  - Giảng viên mất nhiều thời gian nhập liệu đề thi thủ công từ giáo trình/tài liệu.
  - Khó kiểm soát tỷ lệ nhận thức theo chuẩn đầu ra (Thang Bloom).
  - Tình trạng gian lận trực tuyến (chuyển tab, tra cứu Google, chụp màn hình).
  - Thiếu phản hồi sư phạm cá nhân hóa sau khi nộp bài; sinh viên chỉ biết điểm mà không hiểu rõ nguyên nhân sai.
- **Mục tiêu Smart Quiz:** Tự động hóa khép kín 100% quy trình từ bóc tách học liệu đến gia sư cá nhân hóa bằng AI.

### Slide 3: Khung Quản trị Dự án & Phương pháp Luận Agile/Scrum
- **Mô hình triển khai:** Agile Scrum với 2 Sprints chính:
  - **Sprint 1 (Tuần 1 - 6):** Nền tảng lõi (Core Engine, Auth, Parser, Question Bank, Auto-Grading).
  - **Sprint 2 (Tuần 7 - 12):** Thông minh hóa & Thời gian thực (Bloom Prompts, Anti-Cheat, AI Tutor, Analytics).
- **Công cụ quản trị:** GitHub Projects, Kanban Board, WBS 3 cấp độ, Burndown Chart, Definition of Done (DoD).
- **Tổng số Story Points hoàn thành:** 42/42 Story Points (Đạt 100% cam kết Backlog).

### Slide 4: Kiến trúc Hệ thống & Ngăn xếp Công nghệ (Tech Stack)
- **Kiến trúc Monorepo:** Tách biệt rõ ràng Frontend (React 18 + Vite) và Backend (FastAPI + SQLAlchemy 2.0).
- **Cơ sở dữ liệu:** PostgreSQL 16 với hệ thống Alembic Migrations tự động.
- **Cơ chế Bảo mật:** HttpOnly Cookie, JWT ngắn hạn (15 phút), Refresh token tự động, chống tấn công XSS & CSRF.
- **Hạ tầng đóng gói:** Docker Compose & Nginx Reverse Proxy đồng nhất Origin.

### Slide 5: Mô-đun 1 — Bóc tách Tài liệu Thông minh (File Parser)
- Hỗ trợ định dạng phong phú: `.pdf`, `.docx`, `.txt` (tối đa 10MB).
- Động cơ Regex Engine nhận diện thông minh các mẫu câu hỏi:
  - Mẫu ký hiệu A/B/C/D, số thứ tự câu 1., 2., Câu 1:...
  - Tự động tách phần dẫn, các phương án lựa chọn và đáp án chuẩn.
- Thống kê tự động: dung lượng tệp, số từ, số ký tự, số trang và kiểm tra bảng mã UTF-8 tiếng Việt.

### Slide 6: Mô-đun 2 — Thiết kế Ma trận Nhận thức Bloom & Sinh đề AI
- Thiết kế ma trận theo 3 cấp độ nhận thức Bloom: **Nhận biết (Remember)**, **Thông hiểu (Understand)**, **Vận dụng (Apply)**.
- Đa dạng hóa định dạng: Chọn 1 đáp án, nhiều đáp án đúng, đúng/sai (True/False).
- Kiến trúc Resilient LLM Client:
  - Kết nối Gemini Flash / OpenAI với cơ chế Tenacity Retry tự động khi gặp lỗi mạng/rate-limit.
  - Chuẩn hóa Pydantic Structured Output JSON.
  - Giao diện xem trước Kế hoạch Prompt và lưu trực tiếp vào Ngân hàng câu hỏi.

### Slide 7: Mô-đun 3 — Động cơ Khảo thí & Giám sát Chống gian lận (Anti-Cheat)
- **Phòng thi tập trung (Exam Focus Mode):** Giao diện biệt lập toàn màn hình, thanh đếm ngược thời gian thực.
- **Bảo toàn dữ liệu (Fault-Tolerance):** Tự động đồng bộ đáp án sau mỗi lượt chọn; nếu mất kết nối hoặc thí sinh bấm F5, bài thi được khôi phục 100%.
- **Hệ thống Anti-cheat đa tầng:**
  - Giám sát chuyển tab (`visibilitychange`) và mất tiêu điểm (`window.blur`) với thuật toán khử đếm trùng (750ms).
  - Chặn phím tắt mở DevTools (F12, Ctrl+Shift+I), chặn sao chép, cắt và nhấp chuột phải.
  - Tự động khóa bài thi và thu bài ngay khi vượt quá ngưỡng vi phạm cho phép.

### Slide 8: Mô-đun 4 — Chấm điểm, Gia sư ảo AI Tutor & Phân tích Đánh giá
- **Động cơ Chấm điểm tức thì:** Hỗ trợ tính điểm chính xác cho câu hỏi chọn 1, chọn nhiều (chia điểm thành phần) và đúng/sai.
- **Gia sư ảo AI Tutor (Review Mode):**
  - Phản hồi sư phạm dưới 2 giây.
  - Giải thích trực quan: Vì sao đáp án đúng lại chuẩn, vì sao phương án thí sinh chọn bị sai, và gợi ý tài liệu ôn tập.
- **Bảng điều khiển Analytics:**
  - Biểu đồ phân bố phổ điểm lớp học (Score Distribution Histogram).
  - Tỷ lệ câu hỏi khó nhất để giảng viên điều chỉnh phương pháp dạy.
  - Xuất bảng điểm danh sách thí sinh ra tệp **CSV** tương thích Microsoft Excel tiếng Việt.
  - Biểu đồ tiến độ học tập và chẩn đoán lỗ hổng kiến thức cá nhân cho sinh viên.

### Slide 9: Demo Trực tiếp Luồng Nghiệp vụ Khép kín (Live Demo Scenario)
- Giảng viên tải tài liệu mẫu $\rightarrow$ AI sinh đề theo Ma trận $\rightarrow$ Tạo ca thi mới.
- Sinh viên đăng nhập $\rightarrow$ Vào phòng thi $\rightarrow$ Làm bài $\rightarrow$ F5 kiểm tra giữ đáp án $\rightarrow$ Thử nghiệm chuyển tab vi phạm bị khóa bài.
- Xem trang Review $\rightarrow$ Tương tác với AI Tutor $\rightarrow$ Giảng viên xem Dashboard và bấm Xuất CSV.

### Slide 10: Quản trị Rủi ro & Đảm bảo Chất lượng (QA & Risk Management)
- **Ma trận Rủi ro (Risk Register):**
  - Rủi ro LLM quá tải/chậm: Giải quyết bằng Timeout ngân sách 2.8s + Fallback mô hình dự phòng.
  - Rủi ro Cookie SameSite khi chạy khác cổng: Giải quyết bằng Nginx Reverse Proxy Gateway.
  - Rủi ro rớt mạng khi thí sinh thi: Giải quyết bằng cơ chế Snapshot Auto-save đa tầng.
- **Chỉ số Chất lượng Kiểm thử:**
  - 299 Automated Tests vượt qua (100% Backend & Frontend).
  - 0 Lỗi biên dịch TypeScript.

### Slide 11: Bài học Kinh nghiệm & Tự đánh giá (Sprint Retrospective)
- **Những điểm làm tốt:**
  - Phân chia công việc theo WBS rõ ràng, các thành viên phát triển song song hiệu quả không bị xung đột nhánh.
  - Áp dụng triệt để văn hóa kiểm thử tự động trước khi merge code vào `main`.
  - Thiết kế kiến trúc hướng dịch vụ (Service-Oriented Architecture) dễ mở rộng.
- **Hạn chế & Hướng phát triển tương lai:**
  - Mở rộng hỗ trợ giám sát gian lận bằng Webcam AI (nhận diện khuôn mặt).
  - Tích hợp thêm các dạng câu hỏi điền khuyết và tự luận ngắn chấm điểm bằng LLM.

### Slide 12: Tổng kết & Hỏi đáp (Q&A)
- Tóm tắt các thành tựu chính của dự án Smart Quiz v2.0.
- Cảm ơn Thầy/Cô và Hội đồng đánh giá!
- Mở phiên hỏi đáp (Q&A).
