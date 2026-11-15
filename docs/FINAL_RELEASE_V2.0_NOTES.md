# 🚀 Smart Quiz v2.0.0-final — Release Notes

> **Phiên bản:** `v2.0.0-final`  
> **Milestone:** Sprint 2: Realtime & Intelligence (Đóng Milestone)  
> **Ngày phát hành:** 15/11/2026  
> **Mã nguồn:** [GitHub Release v2.0.0-final](https://github.com/nhatanh19/smart-quiz/releases/tag/v2.0.0-final)

---

## 🌟 Điểm nổi bật trong Bản phát hành v2.0.0-final

Bản phát hành `v2.0.0-final` đánh dấu sự hoàn thiện toàn diện của hệ thống **Smart Quiz**, tích hợp đầy đủ 4 mô-đun nghiệp vụ từ khâu chuẩn bị đề thi, tổ chức phòng thi trực tuyến có giám sát, đến chấm điểm thông minh và phân tích dữ liệu:

### 1. Module 1: File Parser & Regex Question Engine (WBS 2.1 - 2.2)
- Hỗ trợ tải lên tệp `.pdf`, `.docx`, `.txt` (tối đa 10MB) với thanh tiến trình trực quan.
- Regex Question Parser tự động trích xuất câu hỏi, danh sách phương án A/B/C/D và đáp án chuẩn.
- Thống kê tự động: dung lượng, số từ, số ký tự, số trang và bảo toàn mã hóa tiếng Việt UTF-8.

### 2. Module 2: AI Quiz Generator & Bloom Matrix Builder (WBS 3.1 - 3.3)
- Giao diện thiết kế Ma trận đề thi bám sát **Thang nhận thức Bloom**: Nhận biết (Remember), Thông hiểu (Understand), Vận dụng (Apply).
- Hỗ trợ 3 định dạng câu hỏi: Chọn 1 đáp án (Single Choice), Chọn nhiều đáp án (Multiple Choice), Đúng/Sai (True/False).
- Resilient LLM Adapter kết nối Google Gemini / OpenAI với cơ chế Tenacity Retry tự động.
- Tính năng xem trước Kế hoạch Prompt (Prompt Preview) và lưu 1-click vào Ngân hàng câu hỏi.

### 3. Module 3: Online Exam Engine & Anti-Cheat System (WBS 4.1 - 4.3)
- Quản lý ca thi thời gian thực với mã phòng, mật mã bảo vệ PIN, thời gian bắt đầu và kết thúc.
- Xáo trộn đề thi độc lập theo từng thí sinh (Fisher-Yates Shuffling với seed riêng biệt).
- Giao diện phòng thi tập trung (Exam Focus Mode), thanh đếm ngược thời gian thực (Countdown Timer).
- Hệ thống bảo toàn đáp án (Snapshot Recovery): tự động đồng bộ liên tục; thí sinh F5 hoặc rớt mạng được khôi phục 100% đáp án.
- Giám sát gian lận Anti-cheat: phát hiện chuyển tab (`visibilitychange`), mất tiêu điểm (`window.blur`), phím tắt F12/DevTools, chống copy/paste/chuột phải; tự động khóa và thu bài khi vi phạm ngưỡng quy định.

### 4. Module 4: Auto-Grading, AI Tutor & Analytics Dashboard (WBS 5.1 - 5.3)
- Chấm điểm tự động tức thì cho toàn bộ các dạng câu hỏi trắc nghiệm.
- Giao diện Review sau thi với **Gia sư ảo AI (AI Tutor)** phân tích lý do chọn đúng/sai và lỗ hổng kiến thức sư phạm dưới 2 giây.
- Bảng điều khiển phân tích phổ điểm lớp học (Score Histogram), phân vị điểm và Top câu hỏi khó nhất dành cho Giảng viên.
- **Xuất bảng điểm danh sách thí sinh ra tệp CSV** hỗ trợ tiếng Việt có dấu tương thích Excel.
- Bảng phân tích tiến độ học tập và biểu đồ chẩn đoán lỗ hổng kiến thức dành cho Sinh viên.

---

## 🐳 Đóng gói & Triển khai (DevOps & Production)

- **Docker Compose:** Khởi chạy toàn bộ hệ thống bằng 1 lệnh duy nhất (`docker compose up -d --build`).
- **Nginx Gateway:** Đảm bảo cùng chung Origin cho Frontend và Backend, triệt tiêu lỗi CORS và bảo mật cookie HttpOnly SameSite=Lax.
- **Cloud Ready:** Cung cấp cấu hình blueprint `render.yaml` sẵn sàng cho môi trường Render / Railway / Supabase.

---

## 📈 Kết quả Kiểm thử Tổng hợp

- **Backend Pytest:** 235 passed, 4 skipped (100% Core + Analytics).
- **Frontend Vitest:** 64 passed (6 Test Suites).
- **TypeScript & Vite Build:** Hoàn tất thành công không lỗi (0 error).
- **E2E Smoke Testing:** Toàn bộ 6 kịch bản nghiệp vụ khép kín đạt kết quả PASS.

---

*Trân trọng cảm ơn sự nỗ lực của toàn thể các thành viên nhóm phát triển Smart Quiz!*
