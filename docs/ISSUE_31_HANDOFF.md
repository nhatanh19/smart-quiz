# Issue #31 — CI/CD Pipeline, Quality/Risk Governance & Sprint 1 Release

Branch: `feature/issue-31-cicd-governance`  
Module: `module:parser`, `documentation` (Dev 1 / Team Leader)  
Priority / Effort: `must-have` (5 Story Points — gộp `#18`, `#19`, `#31`)

---

## 1. Deliverables Added

1. **GitHub Actions CI Workflow (`.github/workflows/ci.yml`):**
   - Kích hoạt tự động trên `pull_request` (vào `main`), `push` (vào `main`) và `workflow_dispatch`.
   - **`backend-test` job:** Python `3.12` + dịch vụ `postgres:16-alpine` (health check `pg_isready`), cài `backend/requirements-dev.txt`, kiểm tra cú pháp `python -m compileall -q backend/app backend/tests`, chạy `pytest backend/tests -v -p no:cacheprovider` với `AUTH_TEST_DATABASE_URL` để chạy đầy đủ cả PostgreSQL smoke tests trong `test_postgres.py`.
   - **`frontend-test-and-build` job:** Node `20`, chạy `npm ci`, `npx tsc --noEmit`, `npm run test` (`vitest run`) và `npm run build` (`tsc && vite build`) trong thư mục `frontend/`.
2. **Quality & Risk Governance Docs (`docs/`):**
   - `docs/DEFINITION_OF_DONE.md`: Chuẩn DoD ở cấp Issue/PR, kỹ thuật Backend/DB/Frontend/AI-Parser và cấp Sprint/Release.
   - `docs/RISK_REGISTER.md`: Sổ theo dõi rủi ro thực tế (`R-01` đến `R-07`) kèm P/I score, trigger, phương án giảm thiểu và trạng thái kiểm soát.
   - `docs/RETROSPECTIVE_SPRINT_1.md`: Biên bản Sprint 1 Review & Retrospective ghi nhận 7/7 Issue Milestone Sprint 1 (`#1, #2, #3, #8, #13, #14, #16`) cùng tiến độ nối tiếp 11 Issue đã merge (`#4`–`#7`, `#9`, `#11`, `#12`, `#15`, `#17`, `#34`, `#35`), bài học rút ra và Action Items cho Sprint 2 (`#10`, `#32`, `#33`, `#36`, `#37`).
3. **Pre-release `v1.0.0-sprint1` Coordination:**
   - Mở PR về `main` (`Ref #31`) để GitHub Actions CI xác minh trực tiếp trên PR; ngay sau khi PR được merge vào `main`, tạo tag & GitHub Pre-release **`v1.0.0-sprint1`** trên commit mới nhất của `main` và đóng Issue `#31`.
