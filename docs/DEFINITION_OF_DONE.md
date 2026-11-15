# ✅ DEFINITION OF DONE (DoD) — SMART QUIZ

**Dự án:** Nền tảng Kiểm tra và Ôn luyện Trắc nghiệm Trực tuyến Tích hợp Trí tuệ Nhân tạo (*Smart Quiz*)  
**Repository:** [github.com/nhatanh19/smart-quiz](https://github.com/nhatanh19/smart-quiz)  
**Tham chiếu quy trình:** `docs/GITHUB_WORKFLOW_GUIDE.md` (Bước 6.1), `docs/AUTHENTICATION.md`, `docs/DATABASE_GUIDE.md`

---

## 1. Mục đích

Tài liệu này quy định các tiêu chí bắt buộc phải thỏa mãn trước khi một công việc (*Issue*), *Pull Request (PR)* hoặc *Sprint Release* được chuyển sang trạng thái **`Done`**, giúp đảm bảo mã nguồn hợp nhất vào nhánh `main` luôn chạy ổn định, an toàn bảo mật và đồng nhất giữa các thành viên (Dev 1–Dev 4).

---

## 2. DoD Cấp độ Issue & Pull Request (Bắt buộc cho mọi PR vào `main`)

### 2.1. Quy trình Git & Quản trị trên GitHub
- [ ] Phát triển trên nhánh tính năng tách từ `main` mới nhất theo chuẩn `feature/issue-<ID>-<tên-ngắn>` hoặc `bugfix/issue-<ID>-...`; **không** push trực tiếp vào `main`.
- [ ] Commit message theo quy ước *Conventional Commits* (`feat(...)`, `fix(...)`, `docs(...)`, `chore(...)`, `test(...)`).
- [ ] Mô tả PR có từ khóa liên kết Issue (`Closes #<ID>` hoặc `Ref #<ID>`), tóm tắt thay đổi và bằng chứng kiểm thử.
- [ ] Không commit các tệp cấu hình nhạy cảm hoặc thư mục cục bộ (`.env`, `.venv/`, `node_modules/`, `.agents/`, dữ liệu tạm).

### 2.2. Kiểm tra Tự động trên CI/CD (`.github/workflows/ci.yml`)
- [ ] **Backend Syntax:** `python -m compileall -q backend/app backend/tests` không có lỗi cú pháp.
- [ ] **Backend Unit & Integration Tests:** `pytest backend/tests -v -p no:cacheprovider` (kèm `AUTH_TEST_DATABASE_URL` PostgreSQL) chạy **xanh 100%**, không bỏ sót case lỗi.
- [ ] **Frontend TypeScript Check:** `npx tsc --noEmit` đạt `0 errors`.
- [ ] **Frontend Unit Tests:** `npm run test` (`vitest run`) vượt qua 100% các test suite.
- [ ] **Frontend Production Build:** `npm run build` (`tsc && vite build`) đóng gói thành công.

---

## 3. DoD Chuyên môn theo Phân hệ Kỹ thuật

### 3.1. Backend API & Cơ sở dữ liệu
- [ ] Tuân thủ `docs/DATABASE_GUIDE.md`: Khóa chính `UUID`, giữ nguyên các bảng/cột chuẩn của CSDL và tạo migration bằng **Alembic** mỗi khi thay đổi schema (khớp `test_postgres.py::test_migration_matches_models`).
- [ ] Mọi endpoint bảo vệ tài nguyên giảng viên/sinh viên/quản trị viên phải kiểm tra phân quyền **RBAC** (`require_roles(...)`), trả `401` khi chưa xác thực và `403` khi sai vai trò.
- [ ] Các endpoint thay đổi trạng thái hoặc upload tệp phải áp dụng `check_origin` chống CSRF và giới hạn kích thước đầu vào (ví dụ: file upload tối đa `10MB` đọc theo stream chunk).
- [ ] Xử lý lỗi rõ ràng bằng HTTP status chuẩn (`400`, `401`, `403`, `404`, `409`, `422`) kèm thông báo tiếng Việt/tiếng Anh dễ hiểu; không để lộ stack trace hay secrets.

### 3.2. Frontend UI/UX & Bảo mật Phiên đăng nhập
- [ ] Toàn bộ API call đi qua `apiClient` (`frontend/src/lib/apiClient.ts`, bật `withCredentials: true` để gửi `HttpOnly` cookies); **không** tự đọc/gửi token từ `localStorage`.
- [ ] Giao diện phản hồi rõ ràng ở đủ các trạng thái (`loading`, `empty`, `success`, `error`), tương thích responsive và không phát sinh lỗi `console.error` / unhandled rejection.
- [ ] Có unit test React Testing Library / Vitest bao phủ hành vi chính và trường hợp biên (validate đầu vào, xử lý lỗi server).

### 3.3. AI Integration & Document Parser
- [ ] Mọi phản hồi từ LLM đều phải đi qua kiểm tra cấu trúc **Pydantic JSON Schema** trước khi trả về client hoặc lưu DB; có cơ chế **Exponential Backoff Retry** cho lỗi rate-limit `429` / timeout.
- [ ] Bộ bóc tách tài liệu bảo toàn tiếng Việt UTF-8 có dấu, giữ nguyên hành vi API cũ và đánh dấu rõ các câu cần rà soát (`is_valid`, `warnings`) trước khi lưu vào Ngân hàng câu hỏi.

---

## 4. DoD Cấp độ Sprint & Release

- [ ] Toàn bộ Issue cam kết trong Sprint Milestone đã đóng hoặc có kế hoạch chuyển tiếp minh bạch.
- [ ] Tài liệu bàn giao cho từng Issue lớn (`docs/ISSUE_<ID>_HANDOFF.md`) và Sổ theo dõi rủi ro (`docs/RISK_REGISTER.md`) được cập nhật phản ánh thực tế.
- [ ] Đã thực hiện buổi **Sprint Review & Retrospective** (`docs/RETROSPECTIVE_SPRINT_1.md`) với Action Items cụ thể cho chặng tiếp theo.
- [ ] Bản phát hành (Pre-release / Release) được gắn tag Git hợp lệ (ví dụ: `v1.0.0-sprint1`) trên commit `main` có CI xanh và kèm Release Notes đầy đủ.
