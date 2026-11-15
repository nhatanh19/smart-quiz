# Issue #37 — Handoff: End-to-End Smoke Testing, Cloud Deployment & Final Release v2.0

- **Mã Issue:** #37  
- **Nhánh:** `release/issue-37-e2e-deployment-v2.0`  
- **Assignee:** @MaiVanTinh17072005 (Dev 4), @nhatanh19 (Dev 1 / Lead) — Phối hợp cùng @MinusDC (Dev 3), @thuan734655 (Dev 2)  
- **Ước lượng:** 7 Story Points  
- **WBS:** 6.1 (End-to-End Integration Testing & Cloud Deployment) & 6.2 (User Manual, Governance Artifacts & Final Release) — Gộp các đầu việc kế hoạch #29, #30, #32.  
- **Báo cáo kiểm thử:** [docs/ISSUE_37_TEST_REPORT.md](./ISSUE_37_TEST_REPORT.md)  
- **Ghi chú phát hành:** [docs/FINAL_RELEASE_V2.0_NOTES.md](./FINAL_RELEASE_V2.0_NOTES.md)  
- **Khung slide thuyết trình:** [docs/SLIDE_SHOWCASE_OUTLINE.md](./SLIDE_SHOWCASE_OUTLINE.md)  

---

## 1. Phạm vi Bàn giao (Deliverables)

1. **Kiểm thử Khép kín E2E (Module 1 $\rightarrow$ 2 $\rightarrow$ 3 $\rightarrow$ 4):**
   - Hợp nhất toàn bộ các nhánh tính năng Sprint 1 & Sprint 2:
     - Module 1 (Parser): Issue #5 (Upload), #6 (Regex Engine), #7 (Preview & Inline Edit).
     - Module 2 (AI Gen): Issue #9 & #11 (Resilient LLM & Bloom Prompts), #32 (Exam Matrix Builder UI), #33 (Document Text Chunking).
     - Module 3 (Exam Engine): Issue #12 (Engine Lifecycle), #13 (Shuffle), #34 (Focused Room & Answer Recovery), #35 (Anti-Cheat Focus Monitor).
     - Module 4 (Tutor & Analytics): Issue #14 (Auto-Grading), #15 (Review Mode), #16 (AI Tutor Contextual Explanations), #17 (Knowledge Gap Diagnostic), #36 (Analytics Dashboard & CSV Export).
   - Kiểm thử 6 kịch bản nghiệp vụ khép kín từ Upload/AI sinh đề $\rightarrow$ Tạo ca thi $\rightarrow$ Sinh viên thi + F5 giữ đáp án + Chuyển tab bị khóa $\rightarrow$ Chấm điểm + Review + AI Tutor $\rightarrow$ Dashboard & Xuất CSV.

2. **Cấu hình Đóng gói Docker & Triển khai Thực tế (WBS 6.1):**
   - `backend/Dockerfile`: Multi-stage runtime Python 3.12-slim, tự động migrate cơ sở dữ liệu và seed data khi khởi động.
   - `frontend/Dockerfile`: Multi-stage build Node 20 Alpine $\rightarrow$ Nginx Alpine phục vụ static bundle.
   - `frontend/nginx.conf`: Nginx SPA routing fallback và nén Gzip.
   - `nginx/nginx.conf`: Reverse Proxy Gateway hợp nhất cổng 80, giải quyết dứt điểm rủi ro CORS và Cookie SameSite/Lax theo `docs/AUTHENTICATION.md`.
   - `docker-compose.yml`: Dựng toàn bộ 4 containers (`postgres`, `backend`, `frontend`, `proxy`) bằng 1 câu lệnh `docker compose up -d --build`.
   - `render.yaml`: Blueprint khai báo hạ tầng triển khai Cloud tự động (Render Free-tier).

3. **Tài liệu Hướng dẫn, Quản trị & Phát hành (WBS 6.2):**
   - `README.md`: Cập nhật toàn diện kiến trúc 4 mô-đun, hướng dẫn cài đặt Docker và Local, bảng tài khoản demo có sẵn:
     - Giảng viên: `instructor@smartquiz.edu.vn` / `SmartQuiz@123`
     - Sinh viên: `student@smartquiz.edu.vn` / `SmartQuiz@123`
     - Quản trị viên: `admin@smartquiz.edu.vn` / `SmartQuiz@123`
     - Hướng dẫn kịch bản kiểm thử E2E từng bước.
   - `docs/ISSUE_37_TEST_REPORT.md`: Báo cáo kết quả kiểm thử khép kín toàn hệ thống.
   - `docs/SLIDE_SHOWCASE_OUTLINE.md`: Khung kịch bản 12 slide bảo vệ đồ án kết thúc học phần Tuần 13.
   - `docs/FINAL_RELEASE_V2.0_NOTES.md`: Bản ghi chú phát hành Release `v2.0.0-final`.
   - Đóng Milestone Sprint 2 và gắn tag `v2.0.0-final`.

---

## 2. Kết quả Xác nhận Chất lượng

- **Backend Pytest:** 248 passed, 4 skipped (100% Core + Analytics + Chunking).
- **Frontend Vitest:** 84 passed (7 Test Suites Vitest).
- **Production Build:** Build PASS (0 errors, 1,576 modules).
- **E2E Scenarios:** 6/6 kịch bản nghiệp vụ đạt kết quả PASS.
