# 🔄 SPRINT 1 REVIEW & RETROSPECTIVE — SMART QUIZ

**Dự án:** Nền tảng Kiểm tra và Ôn luyện Trắc nghiệm Trực tuyến Tích hợp Trí tuệ Nhân tạo (*Smart Quiz*)  
**Milestone nghiệm thu:** `Sprint 1: Core Foundation` (100% Closed — `7/7` Issues) + Khởi động nối tiếp Sprint 2  
**Phiên bản đóng gói:** Pre-release `v1.0.0-sprint1`  
**Thành viên tham gia:** Dev 1 (`@nhatanh19`), Dev 2 (`@MinusDC`), Dev 3 (`@thuan734655`), Dev 4 (`@MaiVanTinh17072005`)

---

## 1. Tổng quan Kết quả Sprint 1 & Tiến độ Tích hợp

Milestone **`Sprint 1: Core Foundation`** đã hoàn thành **7/7 Issues (100%)**, đặt nền móng cho toàn bộ 4 phân hệ kiến trúc:

| Issue | Phân hệ / Vai trò | Tiêu đề | Trạng thái |
| :---: | :--- | :--- | :---: |
| **#1** | Infra (`@nhatanh19`) | Setup Full-stack Project Monorepo & Code Quality Tools | Closed |
| **#2** | Database (`@nhatanh19`) | Design Relational Schema (ERD) & Database Migrations (PR `#18`) | Closed |
| **#3** | Auth (`@thuan734655`) | User Registration, Login & JWT Token Management (PR `#20`) | Closed |
| **#8** | Question Bank (`@MinusDC`) | Question Bank Management CRUD API & Filtering UI (PR `#23`) | Closed |
| **#13** | Exam (`@thuan734655`) | Seed-based Question & Answer Shuffling Algorithm (PR `#24`) | Closed |
| **#14** | Grading (`@MaiVanTinh17072005`) | Instant Multi-Question Type Auto-Grading Engine (PR `#25`) | Closed |
| **#16** | AI-Tutor (`@MaiVanTinh17072005`) | Contextual Explanation Generator API (PR `#22`) | Closed |

> **Ghi chú tiến độ mở rộng đã hợp nhất vào `main` trước mốc Pre-release `v1.0.0-sprint1`:**  
> Ngoài 7 Issue nền tảng của Sprint 1, nhóm đã hoàn thành và merge thêm **11 Issues** tiếp nối (`#4` PR `#28`, `#5` PR `#40`, `#6` PR `#41`, `#7` PR `#44`, `#9` & `#11` PR `#30`, `#12` PR `#29`, `#15` PR `#26`, `#17` PR `#27`, `#34` PR `#38`, `#35` PR `#39`), nâng tổng số lên **18/24 Issues đã đóng** tính tới thời điểm thực hiện `#31`.

---

## 2. What Went Well? (Những điểm nhóm làm tốt)

1. **Chốt sớm thiết kế CSDL & hợp đồng API giữa các phân hệ:**  
   Việc hoàn thiện ERD PostgreSQL với UUID, Alembic migrations (`#2`), bảng hợp đồng dữ liệu (`docs/DATABASE_GUIDE.md`) và thỏa thuận hợp tác Dev 3–Dev 4 (`docs/DEV3_DEV4_WORKING_AGREEMENT.md`, PR `#21`) ngay đầu kỳ giúp cả 4 thành viên phát triển song song mà không giẫm chân lên nhau.
2. **Chất lượng kiểm thử tự động tốt ngay từ giai đoạn xây nền:**  
   Các module đều kèm unit test chặt chẽ (Backend đạt **223 tests** trên SQLite + **4 PostgreSQL schema/constraint smoke tests**; Frontend đạt **65 Vitest specs** trên **6 test files** và `tsc && vite build` xanh).
3. **Tính năng lõi có chiều sâu thực tế:**  
   - Module File Parser hoàn thiện khép kín chuỗi tải tệp `.pdf`/`.docx`/`.txt` (`#5`), trích xuất đa định dạng kèm nhận diện gạch chân/highlight Word (`#6`) và chỉnh sửa inline trước khi lưu với `source_type = FILE_PARSER` (`#7`).
   - Module Exam & Anti-cheat triển khai xáo trộn theo seed (`#13`), phòng thi lưu nháp `localStorage` (`#34`) và giám sát vi phạm tự động khóa bài (`#35`).
   - Module Grading & AI Tutor hoàn thiện chấm điểm, xem lại bài thi và chẩn đoán lỗ hổng kiến thức (`#14`, `#15`, `#16`, `#17`).

---

## 3. What Didn't Go Well? (Vướng mắc & Khó khăn thực tế)

1. **Chưa có CI/CD tự động ở các PR đầu tiên:**  
   Trong 17 PR đã merge đầu tiên, nhóm phải chạy `pytest`, `vitest` và `vite build` thủ công ở máy cục bộ trước khi merge. Điều này khiến một số lỗi nhỏ (như đồng bộ auth `localStorage` vs `HttpOnly` cookie ở nhánh tạo trước) phải sửa lại khi rebase về sau.
2. **Độ lệch thời gian đồng bộ cơ chế xác thực giữa Auth và các UI viết trước:**  
   Sau khi `#4` chuyển sang `HttpOnly` cookie + `check_origin`, một số màn hình phụ thuộc JWT trước đó (như phần kiểm tra token thủ công ở tab Ngân hàng câu hỏi trong `ParserPlaceholder`) cần rà soát lại để đồng nhất hoàn toàn theo `apiClient`.
3. **Khối lượng công việc AI-Gen & Analytics còn dồn sang Sprint 2:**  
   Một số Issue quan trọng của Module 2 (`#10`, `#32`, `#33`) và Module 4 (`#36`) vẫn đang mở sau Sprint 1, cần bám sát kế hoạch để không ảnh hưởng mốc kiểm thử tổng hợp `#37`.

---

## 4. Action Items cho Sprint 2 & Giai đoạn Closure

| STT | Hành động cải tiến | Người phụ trách | Thời hạn / Liên kết |
| :---: | :--- | :--- | :--- |
| **1** | Kích hoạt GitHub Actions CI (`.github/workflows/ci.yml`) chạy `pytest` + PostgreSQL 16 + `vitest` + `tsc` + `vite build` tự động trên mọi PR vào `main`. | Dev 1 (`@nhatanh19`) | Issue `#31` (Ngay lập tức) |
| **2** | Áp dụng nghiêm bộ tiêu chí `docs/DEFINITION_OF_DONE.md` và cập nhật `docs/RISK_REGISTER.md` trước khi merge các PR còn lại của Sprint 2. | Cả nhóm (Dev 1–4) | Xuyên suốt Sprint 2 |
| **3** | Hoàn tất các Issue còn mở của Module 2 (`#10`, `#32`, `#33`) và Dashboard Analytics Module 4 (`#36`), đồng thời rà soát thống nhất `HttpOnly` cookie trên các UI mới. | Dev 2 (`@MinusDC`) & Dev 4 (`@MaiVanTinh17072005`) | Giai đoạn Sprint 2 |
| **4** | Thực hiện E2E smoke test khép kín toàn hệ thống trên trình duyệt thật, hoàn thiện tài liệu sử dụng (`README.md`) và phát hành `v2.0.0-final`. | Cả nhóm (`@nhatanh19`, `@MaiVanTinh17072005` đầu mối) | Issue `#37` (Tuần 13) |
