# ⚠️ SỔ THEO DÕI RỦI RO DỰ ÁN (RISK REGISTER) — SMART QUIZ

**Dự án:** Nền tảng Kiểm tra và Ôn luyện Trắc nghiệm Trực tuyến Tích hợp Trí tuệ Nhân tạo (*Smart Quiz*)  
**Tham chiếu quy trình:** `docs/GITHUB_WORKFLOW_GUIDE.md` (Bước 6.2), `docs/PROJECT_CHARTER.md` (Mục 6 & 8)  
**Cập nhật gần nhất:** Sprint 1 Closure & Sprint 2 Mid-Execution (Issue `#31`)

---

## 1. Thang đánh giá Mức độ Rủi ro

- **Xác suất xảy ra (Probability — P):** `1` (Rất thấp) $\rightarrow$ `5` (Rất cao).
- **Mức độ tác động (Impact — I):** `1` (Không đáng kể) $\rightarrow$ `5` (Nghiêm trọng, ảnh hưởng tiến độ/nghiệm thu).
- **Điểm rủi ro (Risk Score = P $\times$ I):**
  - `15 – 25`: **Cao (High)** — Cần xử lý ngay và giám sát liên tục.
  - `8 – 14`: **Trung bình (Medium)** — Có kế hoạch giảm thiểu cụ thể.
  - `1 – 7`: **Thấp (Low)** — Theo dõi định kỳ.

---

## 2. Danh sách Rủi ro Thực tế & Kế hoạch Ứng phó

| Mã | Rủi ro thực tế phát sinh / nhận diện | Phân nhóm | P | I | Điểm | Dấu hiệu nhận biết (Trigger) | Chiến lược Giảm thiểu & Phương án Dự phòng (Mitigation & Contingency) | Trạng thái | Phụ trách |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- | :---: | :--- |
| **R-01** | **LLM API bị Rate-limit (`429`), Timeout hoặc trả JSON sai schema** khi sinh câu hỏi / giải thích bằng AI Free Tier. | Kỹ thuật / Hạ tầng | 4 | 5 | **20 (Cao)** | Gọi Gemini/OpenAI API nhận mã `429`, `504` hoặc `ValidationError` khi parse JSON. | Đã cài đặt **Exponential Backoff Retry** với `tenacity` trong LLM Client (`Issue #9`), ép kiểu đầu ra qua Pydantic strict JSON Schema (`Issue #11`) và thông báo fallback thân thiện nếu vượt quota. | **Đã kiểm soát** *(Giám sát tiếp ở #10, #32, #33)* | Dev 2 & Dev 4 |
| **R-02** | **Lệch chuẩn xác thực `HttpOnly` Cookies vs `localStorage` JWT** giữa các module phát triển song song. | Bảo mật / Tích hợp | 4 | 4 | **16 (Cao)** | API trả `401 Unauthorized` sau khi login thành công bằng cookie hoặc CSRF bị chặn `403`. | Thống nhất toàn frontend dùng `apiClient` (`withCredentials: true`) kết hợp RBAC + `check_origin` (`docs/AUTHENTICATION.md`, `Issue #4`, `#5`, `#6`, `#7`); tiếp tục rà soát các màn hình Question Bank/AI-Gen ở Sprint 2. | **Đang giám sát** | Dev 3 & Dev 1 |
| **R-03** | **Đề thi `.pdf` / `.docx` đa định dạng hoặc bản scan ảnh** làm giảm độ chính xác nhận diện câu hỏi & đáp án. | Nghiệp vụ / Parser | 4 | 4 | **16 (Cao)** | Câu hỏi thiếu đáp án đúng, ký tự gạch chân/màu Word mất dấu hiệu khi trích xuất `raw_text`, hoặc file PDF không có text layer. | Tách luồng `DocxExtractor` lấy formatting hints (`underline`, `highlight`, màu sắc) không làm bẩn `raw_text` (`Issue #6`); bổ sung cảnh báo `warnings` + giao diện sửa inline / hoàn tác xóa trước khi lưu (`Issue #7`). Giữ đúng Out-of-Scope: báo lỗi rõ ràng nếu PDF rỗng text (không tự OCR). | **Đã kiểm soát** | Dev 1 |
| **R-04** | **Rớt mạng, tải lại trang (F5) hoặc gian lận chuyển tab** trong lúc sinh viên đang làm bài thi trực tuyến. | Độ tin cậy / Khảo thí | 3 | 5 | **15 (Cao)** | Thí sinh mất bài làm khi F5 hoặc mở tab khác tra cứu tài liệu trong phòng thi. | Tự động lưu nháp đáp án theo phòng thi vào `localStorage` để khôi phục khi reload (`Issue #34`); triển khai `useAntiCheatMonitor` ghi nhận `TAB_SWITCH`, `WINDOW_BLUR`, chặn copy/devtools và tự động khóa/thu bài khi vượt ngưỡng (`Issue #35`). | **Đã kiểm soát** | Dev 3 |
| **R-05** | **Khác biệt hành vi giữa SQLite test cục bộ và PostgreSQL production** (`ENUM`, `JSONB`, `CheckConstraint`, Alembic migration). | Dữ liệu / Môi trường | 3 | 4 | **12 (TB)** | Unit test SQLite pass nhưng lỗi `DataError` / `IntegrityError` hoặc lệch cột khi chạy PostgreSQL thật. | Xây dựng `backend/tests/test_postgres.py` kiểm tra `alembic` khớp model + JSONB/ENUM constraints khi có `AUTH_TEST_DATABASE_URL`, và chạy tự động với container `postgres:16-alpine` trong `.github/workflows/ci.yml` (`Issue #31`). | **Đã đóng** | Dev 1 |
| **R-06** | **Vượt ngưỡng dung lượng tệp tải lên & giới hạn Free Tier Cloud** khi demo hoặc nhiều người dùng truy cập đồng thời. | Vận hành / Ngân sách | 3 | 3 | **9 (TB)** | Upload file >10MB gây tràn RAM server hoặc timeout trên Cloud Free-tier. | Kiểm tra đuôi file và dung lượng cả Client lẫn Backend stream chunk `1MB` giới hạn cứng `10MB` (`parser/router.py`); kiểm soát payload prompt AI gọn và test build bundle định kỳ qua CI. | **Đang giám sát** | Dev 1 & Cả nhóm |
| **R-07** | **Tồn đọng Issue cuối Sprint 2 (`#10`, `#32`, `#33`, `#36`) gây dồn việc sát mốc nghiệm thu Tuần 13.** | Tiến độ / Quản trị | 3 | 4 | **12 (TB)** | Nhiều PR mở dồn sát deadline dễ thiếu kiểm tra tích hợp chéo trước Release v2.0. | Đóng gói sớm Sprint 1 Pre-release `v1.0.0-sprint1`, kích hoạt CI gate bắt buộc trên mọi PR (`#31`), áp dụng WIP Limit và ưu tiên kiểm thử E2E luồng khép kín (`#37`) ngay khi các module AI-Gen & Analytics hoàn tất. | **Đang theo dõi** | Scrum Master (Dev 1) & Cả nhóm |

---

## 3. Quy trình Cập nhật Risk Register

1. Mỗi tuần trong buổi họp tiến độ hoặc ngay khi phát sinh bug/blocker mới trên PR, thành viên liên quan cập nhật mức `P/I` và trạng thái vào bảng trên.
2. Trước khi phát hành bản chính thức **`v2.0.0-final`** (Issue `#37`), rà soát lại toàn bộ các rủi ro đang ở trạng thái *Đang giám sát / Đang theo dõi* để chuyển sang *Đã đóng* hoặc ghi nhận giới hạn hệ thống trong tài liệu hướng dẫn.
