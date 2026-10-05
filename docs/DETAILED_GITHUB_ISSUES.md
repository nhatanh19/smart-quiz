# 📋 CHI TIẾT PRODUCT BACKLOG & GITHUB ISSUES — SMART QUIZ
**Dự án:** Nền tảng Kiểm tra và Ôn luyện Trắc nghiệm Trực tuyến Tích hợp Trí tuệ Nhân tạo (*Smart Quiz*)  
**Mã nguồn / Repo:** [github.com/nhatanh19/smart-quiz](https://github.com/nhatanh19/smart-quiz)  
**Tài liệu tham chiếu:** `docs/WBS_AND_BACKLOG.md` | Chuẩn môn học: **Week 03 (WBS) & Week 04–05 (Agile/Scrum on GitHub)**  
**Quy chuẩn phân rã:** Mỗi Work Package lớn được chia nhỏ thành các **Sub-Issues (Tasks / User Stories)** có quy mô **1–3 ngày làm việc (2–5 Story Points)**, đi kèm tiêu chí nghiệm thu cụ thể (*Definition of Done Checklist*).

---

## 🎯 BẢNG TỔNG HỢP 32 CHI TIẾT GITHUB ISSUES

### Phân công 4 thành viên (Đảm bảo 25% khối lượng code/người):
- **Dev 1 (Team Leader / Scrum Master):** Phụ trách Hạ tầng, Quản trị hệ thống, Bóc tách tài liệu (*File Parser*) & DevOps. (Issues: #1, #2, #3, #4, #5, #6, #7, #8, #27, #30)
- **Dev 2 (AI Integration Engineer):** Phụ trách Kết nối LLM API, Ép kiểu JSON Schema, Prompt Engineering & Sinh đề theo ngữ cảnh file. (Issues: #9, #10, #11, #12, #13, #14, #28)
- **Dev 3 (Core Engine Engineer):** Phụ trách Phòng thi, Trộn đề ngẫu nhiên, Lưu trữ đệm LocalStorage & Hệ thống Chống gian lận Client-side. (Issues: #15, #16, #17, #18, #19, #20, #27)
- **Dev 4 (Data & Tutor Engineer):** Phụ trách Bộ chấm điểm, Chế độ Review bài thi, Gia sư ảo AI Tutor & Bảng điều khiển Analytics. (Issues: #21, #22, #23, #24, #25, #26)
- **Toàn đội ngũ (Dev 1, 2, 3, 4):** Phối hợp kiểm thử tích hợp, Retrospective và Bàn giao nghiệm thu. (Issues: #29, #31, #32)

---

### MODULE 1.0: KIẾN TRÚC HẠ TẦNG, XÁC THỰC & PHÂN QUYỀN (WBS 1.1 & 1.2)

#### 🔹 Issue #1: `[Infra] Setup Full-stack Project Monorepo & Code Quality Tools`
- **Thuộc WBS:** 1.1.1 | **Gói WBS lớn:** Issue #1
- **Phân loại MoSCoW:** `must-have` | **Mô-đun:** `module:parser`
- **Milestone:** `Sprint 1: Core Foundation`
- **Độ phức tạp / Thời gian:** `2 Story Points` (~1.5 ngày) | **Assignee:** `Dev 1`
- **Mô tả công việc:**
  - Khởi tạo khung mã nguồn dự án (Next.js/React cho Frontend, Node.js/Express hoặc Python FastAPI cho Backend).
  - Cấu hình TypeScript, ESLint, Prettier và thiết lập cấu trúc thư mục module hóa sạch sẽ.
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Khởi chạy thành công cả Frontend và Backend trên môi trường Local (`localhost`).
  - [ ] Lệnh `npm run lint` hoặc `npm run format` chạy không phát sinh lỗi.
  - [ ] Có file `.gitignore` và `.env.example` chuẩn mẫu cho toàn nhóm.

#### 🔹 Issue #2: `[Database] Design Relational Schema (ERD) & Database Migrations`
- **Thuộc WBS:** 1.1.2 | **Gói WBS lớn:** Issue #1
- **Phân loại MoSCoW:** `must-have` | **Mô-đun:** `module:parser`
- **Milestone:** `Sprint 1: Core Foundation`
- **Độ phức tạp / Thời gian:** `3 Story Points` (~2 ngày) | **Assignee:** `Dev 1`
- **Mô tả công việc:**
  - Thiết kế sơ đồ quan hệ thực thể (ERD) cho toàn bộ hệ thống: `users`, `questions`, `options`, `exams`, `exam_questions`, `submissions`, `submission_answers`.
  - Cấu hình ORM (Prisma / TypeORM / Drizzle) và viết script khởi tạo dữ liệu mẫu (Seed Data).
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Chạy thành công lệnh `migration` tạo đủ các bảng trong CSDL (PostgreSQL/Supabase).
  - [ ] Seed script tạo sẵn ít nhất 2 tài khoản test (1 Giảng viên, 1 Sinh viên) và 10 câu hỏi mẫu.
  - [ ] Đính kèm file sơ đồ ERD vào thư mục `docs/database/`.

#### 🔹 Issue #3: `[Auth] User Registration, Login & JWT Token Management`
- **Thuộc WBS:** 1.2.1 | **Gói WBS lớn:** Issue #2
- **Phân loại MoSCoW:** `must-have` | **Mô-đun:** `module:parser`
- **Milestone:** `Sprint 1: Core Foundation`
- **Độ phức tạp / Thời gian:** `3 Story Points` (~2 ngày) | **Assignee:** `Dev 1`
- **Mô tả công việc:**
  - Xây dựng API và giao diện Đăng ký (`/register`), Đăng nhập (`/login`).
  - Băm mật khẩu an toàn bằng `bcrypt`, sinh mã `Access Token` và `Refresh Token` qua JWT.
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Đăng ký tài khoản mới lưu đúng mật khẩu đã băm vào DB.
  - [ ] Đăng nhập trả về JWT token hợp lệ, lưu vào HttpOnly Cookie hoặc Local Storage an toàn.
  - [ ] Xử lý thông báo lỗi rõ ràng khi sai tài khoản/mật khẩu.

#### 🔹 Issue #4: `[Auth] Role-Based Route Protection & User Profile UI`
- **Thuộc WBS:** 1.2.2 | **Gói WBS lớn:** Issue #2
- **Phân loại MoSCoW:** `must-have` | **Mô-đun:** `module:parser`
- **Milestone:** `Sprint 1: Core Foundation`
- **Độ phức tạp / Thời gian:** `2 Story Points` (~1.5 ngày) | **Assignee:** `Dev 1`
- **Mô tả công việc:**
  - Xây dựng Middleware chặn truy cập trái phép theo vai trò: `INSTRUCTOR`, `STUDENT`, `ADMIN`.
  - Thiết kế trang thông tin cá nhân (`/profile`) và nút Đăng xuất xóa phiên làm việc.
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Sinh viên không thể truy cập các route quản lý đề thi của Giảng viên (`/instructor/*`).
  - [ ] Hiển thị avatar, tên, email và vai trò người dùng sau khi đăng nhập.
  - [ ] Đăng xuất hủy token và điều hướng về trang chủ đăng nhập.

---

### MODULE 2.0: BỘ PHÂN TÍCH TÀI LIỆU & NGÂN HÀNG CÂU HỎI (WBS 2.1 & 2.2)

#### 🔹 Issue #5: `[Parser] File Upload Pipeline & Raw Text Extraction (PDF, DOCX, TXT)`
- **Thuộc WBS:** 2.1.1 | **Gói WBS lớn:** Issue #3
- **Phân loại MoSCoW:** `must-have` | **Mô-đun:** `module:parser`
- **Milestone:** `Sprint 1: Core Foundation`
- **Độ phức tạp / Thời gian:** `3 Story Points` (~2 ngày) | **Assignee:** `Dev 1`
- **Mô tả công việc:**
  - Xây dựng API tiếp nhận tệp tải lên (hỗ trợ kéo thả file, giới hạn dung lượng < 10MB).
  - Tích hợp thư viện xử lý trích xuất văn bản thô: `pdf-parse` (cho PDF), `mammoth` (cho DOCX) và bộ đọc văn bản UTF-8 chuẩn cho TXT.
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Tải lên tệp PDF/DOCX/TXT mẫu và in ra chuỗi văn bản thô chính xác, không lỗi font Unicode tiếng Việt.
  - [ ] Chặn định dạng file không hợp lệ kèm thông báo lỗi trực quan.

#### 🔹 Issue #6: `[Parser] Regex Pattern Matching Engine for Questions & Options`
- **Thuộc WBS:** 2.1.2 | **Gói WBS lớn:** Issue #3
- **Phân loại MoSCoW:** `must-have` | **Mô-đun:** `module:parser`
- **Milestone:** `Sprint 1: Core Foundation`
- **Độ phức tạp / Thời gian:** `5 Story Points` (~3 ngày) | **Assignee:** `Dev 1`
- **Mô tả công việc:**
  - Xây dựng thuật toán bóc tách cấu trúc sử dụng Regular Expressions (Regex) để nhận diện:
    - Tiêu đề câu hỏi (Ví dụ: `Câu 1:`, `1.`, `Question 1:`).
    - Các phương án lựa chọn (`A.`, `B.`, `C.`, `D.`).
    - Đáp án đúng (Ví dụ: `Đáp án: A`, gạch chân, hoặc `*A.`).
    - Lời giải thích/ghi chú (nếu có).
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Trích xuất đúng cấu trúc $\ge$ 90% số câu hỏi trong bộ đề Word/PDF mẫu của giảng viên.
  - [ ] Trả về danh sách đối tượng câu hỏi chuẩn hóa (chứa nội dung, mảng lựa chọn, đáp án đúng).

#### 🔹 Issue #7: `[Parser-UI] Question Extraction Preview & Inline Editing Table`
- **Thuộc WBS:** 2.2.1 | **Gói WBS lớn:** Issue #4
- **Phân loại MoSCoW:** `must-have` | **Mô-đun:** `module:parser`
- **Milestone:** `Sprint 1: Core Foundation`
- **Độ phức tạp / Thời gian:** `3 Story Points` (~2 ngày) | **Assignee:** `Dev 1`
- **Mô tả công việc:**
  - Xây dựng màn hình xem trước (Preview) danh sách câu hỏi ngay sau khi bóc tách từ file.
  - Cho phép giảng viên bấm vào sửa trực tiếp nội dung câu hỏi, đổi đáp án đúng hoặc xóa câu nhận diện sai trước khi lưu.
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Hiển thị trực quan danh sách câu hỏi dạng thẻ hoặc bảng chỉnh sửa linh hoạt.
  - [ ] Thao tác sửa text, đổi đáp án đúng và xóa câu hoạt động mượt mà ngay trên giao diện.

#### 🔹 Issue #8: `[Bank] Question Bank Management CRUD API & Filtering UI`
- **Thuộc WBS:** 2.2.2 | **Gói WBS lớn:** Issue #4
- **Phân loại MoSCoW:** `must-have` | **Mô-đun:** `module:parser`
- **Milestone:** `Sprint 1: Core Foundation`
- **Độ phức tạp / Thời gian:** `3 Story Points` (~2 ngày) | **Assignee:** `Dev 1`
- **Mô tả công việc:**
  - Xây dựng đầy đủ API và giao diện CRUD cho Ngân hàng câu hỏi.
  - Phân loại câu hỏi theo môn học, chuyên đề/tag và mức độ khó.
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Bấm "Lưu vào ngân hàng đề" chuyển toàn bộ câu hỏi đã duyệt vào CSDL.
  - [ ] Bộ lọc theo chuyên đề và tìm kiếm từ khóa hoạt động chính xác với độ trễ < 500ms.

---

### MODULE 3.0: SINH ĐỀ THI THÔNG MINH BẰNG AI (WBS 3.1, 3.2 & 3.3)

#### 🔹 Issue #9: `[AI-Gen] LLM Client Adapter & Resilient Calling Service`
- **Thuộc WBS:** 3.1.1 | **Gói WBS lớn:** Issue #5
- **Phân loại MoSCoW:** `must-have` | **Mô-đun:** `module:ai-gen`
- **Milestone:** `Sprint 1: Core Foundation`
- **Độ phức tạp / Thời gian:** `3 Story Points` (~2 ngày) | **Assignee:** `Dev 2`
- **Mô tả công việc:**
  - Thiết lập Adapter kết nối Google Gemini API (ưu tiên model `gemini-1.5-flash` / `gemini-2.5-flash`) hoặc OpenAI API.
  - Xây dựng cơ chế xử lý lỗi quá tải (Rate-limit 429), cơ chế thử lại tự động (*Exponential Backoff Retry*) và thiết lập timeout 15 giây.
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Gọi API thành công từ backend với API Key bảo mật trong biến môi trường.
  - [ ] Có khối xử lý `catch` tự động thử lại tối đa 3 lần khi API báo bận trước khi trả thông báo lỗi thân thiện.

#### 🔹 Issue #10: `[AI-Gen] Strict JSON Schema Definition & Response Parser`
- **Thuộc WBS:** 3.1.2 | **Gói WBS lớn:** Issue #5
- **Phân loại MoSCoW:** `must-have` | **Mô-đun:** `module:ai-gen`
- **Milestone:** `Sprint 1: Core Foundation`
- **Độ phức tạp / Thời gian:** `3 Story Points` (~2 ngày) | **Assignee:** `Dev 2`
- **Mô tả công việc:**
  - Định nghĩa lược đồ xác thực dữ liệu chặt chẽ bằng thư viện Zod hoặc Pydantic cho dữ liệu câu hỏi AI trả về.
  - Cấu hình tham số `response_schema` / `response_mime_type: "application/json"` của LLM để đảm bảo 100% kết quả là JSON hợp lệ.
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Kết quả sinh từ AI tự động parse thành mảng đối tượng: `[{ question, options, correctAnswer, difficulty, explanation }]`.
  - [ ] Không bao giờ bị crash app do AI trả về định dạng văn bản tự do ngoài JSON.

#### 🔹 Issue #11: `[AI-Gen] Bloom Taxonomy Prompt Templates for Multi-Type Questions`
- **Thuộc WBS:** 3.2.1 | **Gói WBS lớn:** Issue #6
- **Phân loại MoSCoW:** `must-have` | **Mô-đun:** `module:ai-gen`
- **Milestone:** `Sprint 1: Core Foundation`
- **Độ phức tạp / Thời gian:** `3 Story Points` (~2 ngày) | **Assignee:** `Dev 2`
- **Mô tả công việc:**
  - Thiết kế các mẫu Prompt chi tiết yêu cầu AI tạo câu hỏi theo thang tư duy Bloom:
    - Nhận biết (*Recall / Knowledge*).
    - Thông hiểu (*Comprehension*).
    - Vận dụng (*Application*).
  - Hỗ trợ đa dạng cấu trúc: Trắc nghiệm 1 lựa chọn, Nhiều lựa chọn đúng, và Đúng/Sai.
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] AI sinh ra câu hỏi bám đúng mức độ tư duy yêu cầu, các phương án nhiễu có tính thuyết phục cao.
  - [ ] Các loại câu hỏi Đúng/Sai và Chọn nhiều đáp án được đánh dấu cờ cấu trúc chính xác.

#### 🔹 Issue #12: `[AI-Gen] Exam Matrix Configuration Modal & AI Generation Flow`
- **Thuộc WBS:** 3.2.2 | **Gói WBS lớn:** Issue #6
- **Phân loại MoSCoW:** `must-have` | **Mô-đun:** `module:ai-gen`
- **Milestone:** `Sprint 1: Core Foundation`
- **Độ phức tạp / Thời gian:** `3 Story Points` (~2 ngày) | **Assignee:** `Dev 2`
- **Mô tả công việc:**
  - Xây dựng giao diện ma trận: Giảng viên nhập chủ đề (ví dụ: *Lập trình Hướng đối tượng*), tổng số câu (ví dụ: 20 câu), và thanh trượt tỷ lệ độ khó (40% Nhận biết, 40% Thông hiểu, 20% Vận dụng).
  - Thiết kế màn hình Loading với hiệu ứng sinh động và danh sách câu hỏi AI trả về cho phép giảng viên bấm chọn/loại bỏ.
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Bấm nút "Sinh câu hỏi AI" gửi đúng payload cấu hình ma trận lên backend.
  - [ ] Hiển thị danh sách câu hỏi vừa sinh ra và cho phép nạp trực tiếp vào Ngân hàng câu hỏi hoặc tạo đề thi mới.

#### 🔹 Issue #13: `[AI-Gen] Document Text Chunking & Context Window Optimization`
- **Thuộc WBS:** 3.3.1 | **Gói WBS lớn:** Issue #7
- **Phân loại MoSCoW:** `should-have` | **Mô-đun:** `module:ai-gen`
- **Milestone:** `Sprint 2: Realtime & Intelligence`
- **Độ phức tạp / Thời gian:** `3 Story Points` (~2 ngày) | **Assignee:** `Dev 2`
- **Mô tả công việc:**
  - Xây dựng thuật toán phân đoạn văn bản (*Text Chunking* với cơ chế *Sliding Window / Overlap*) từ tài liệu bài giảng dài mà giảng viên tải lên.
  - Trích lọc các đoạn văn giàu tri thức (đoạn định nghĩa, nguyên lý) để làm ngữ cảnh sạch (Clean Context) truyền vào Prompt.
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Tài liệu giáo trình 20-30 trang được chia thành các chunk phù hợp giới hạn token của LLM mà không bị đứt đoạn ngữ nghĩa.

#### 🔹 Issue #14: `[AI-Gen] End-to-End File-to-Quiz AI Generation API & UI`
- **Thuộc WBS:** 3.3.2 | **Gói WBS lớn:** Issue #7
- **Phân loại MoSCoW:** `should-have` | **Mô-đun:** `module:ai-gen`
- **Milestone:** `Sprint 2: Realtime & Intelligence`
- **Độ phức tạp / Thời gian:** `3 Story Points` (~2 ngày) | **Assignee:** `Dev 2`
- **Mô tả công việc:**
  - Kết nối luồng hoàn chỉnh: Giảng viên tải tệp Slide/Giáo trình lên $\rightarrow$ Hệ thống đọc chunk ngữ cảnh $\rightarrow$ AI sinh bộ câu hỏi trắc nghiệm sát với nội dung bài học.
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Câu hỏi trắc nghiệm sinh ra có nội dung trích xuất trực tiếp từ tệp tài liệu được tải lên.
  - [ ] Giảng viên kiểm tra được phần trích dẫn nguồn nội dung tương ứng của câu hỏi.

---

### MODULE 4.0: HỆ THỐNG TỔ CHỨC THI & CHỐNG GIAN LẬN (WBS 4.1, 4.2 & 4.3)

#### 🔹 Issue #15: `[Exam] Exam Room Creation & Scheduling Settings API/UI`
- **Thuộc WBS:** 4.1.1 | **Gói WBS lớn:** Issue #8
- **Phân loại MoSCoW:** `must-have` | **Mô-đun:** `module:exam`
- **Milestone:** `Sprint 1: Core Foundation`
- **Độ phức tạp / Thời gian:** `3 Story Points` (~2 ngày) | **Assignee:** `Dev 3`
- **Mô tả công việc:**
  - Xây dựng giao diện và API tạo phòng thi: Chọn bộ câu hỏi từ ngân hàng đề, đặt tên kỳ thi, thời gian mở/đóng ca thi, thời lượng làm bài (phút), mật khẩu phòng thi và số lượt làm tối đa.
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Giảng viên tạo được đề thi và nhận mã phòng thi (Exam Code / Link).
  - [ ] Sinh viên nhập đúng mã phòng thi và mật khẩu mới được vào phòng chờ.

#### 🔹 Issue #16: `[Exam] Seed-based Question & Answer Shuffling Algorithm`
- **Thuộc WBS:** 4.1.2 | **Gói WBS lớn:** Issue #8
- **Phân loại MoSCoW:** `must-have` | **Mô-đun:** `module:exam`
- **Milestone:** `Sprint 1: Core Foundation`
- **Độ phức tạp / Thời gian:** `2 Story Points` (~1.5 ngày) | **Assignee:** `Dev 3`
- **Mô tả công việc:**
  - Cài đặt thuật toán xáo trộn ngẫu nhiên (*Fisher-Yates Shuffle*) dựa trên mã định danh của từng sinh viên (`studentId + examId`).
  - Đảo lộn cả thứ tự câu hỏi và thứ tự các phương án lựa chọn (A, B, C, D) riêng biệt cho từng thí sinh nhưng vẫn đối chiếu chính xác đáp án gốc khi chấm bài.
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Hai sinh viên vào cùng 1 ca thi nhận được thứ tự câu hỏi và thứ tự đáp án hoàn toàn khác nhau.
  - [ ] Dữ liệu bài làm khi gửi lên backend vẫn ánh xạ đúng phương án gốc được chọn.

#### 🔹 Issue #17: `[Exam] Focused Student Exam Room UI & Countdown Timer`
- **Thuộc WBS:** 4.2.1 | **Gói WBS lớn:** Issue #9
- **Phân loại MoSCoW:** `must-have` | **Mô-đun:** `module:exam`
- **Milestone:** `Sprint 2: Realtime & Intelligence`
- **Độ phức tạp / Thời gian:** `5 Story Points` (~3 ngày) | **Assignee:** `Dev 3`
- **Mô tả công việc:**
  - Thiết kế màn hình làm bài thi tập trung, loại bỏ mọi menu điều hướng gây xao nhãng.
  - Đồng hồ đếm ngược thời gian thực (`Countdown Timer`), lưới điều hướng câu hỏi (đã làm / chưa làm / đánh dấu xem lại) và nút Nộp bài với hộp thoại xác nhận.
  - Cơ chế tự động khóa màn hình và nộp bài cưỡng bức khi đồng hồ đếm về 00:00.
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Đồng hồ đếm ngược chạy mượt mà theo từng giây và tự động thu bài khi hết giờ.
  - [ ] Bảng trạng thái câu hỏi cập nhật màu sắc tức thì khi sinh viên click chọn đáp án.

#### 🔹 Issue #18: `[Exam] LocalStorage Real-time Answer Caching & Network Reconnect`
- **Thuộc WBS:** 4.2.2 | **Gói WBS lớn:** Issue #9
- **Phân loại MoSCoW:** `must-have` | **Mô-đun:** `module:exam`
- **Milestone:** `Sprint 2: Realtime & Intelligence`
- **Độ phức tạp / Thời gian:** `3 Story Points` (~2 ngày) | **Assignee:** `Dev 3`
- **Mô tả công việc:**
  - Xây dựng cơ chế tự động lưu đáp án người dùng đã chọn vào `localStorage` của trình duyệt ngay khi click (áp dụng cơ chế Debounce).
  - Tự động phát hiện khi mất kết nối mạng và khôi phục 100% trạng thái câu hỏi khi F5 tải lại trang.
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Thử nghiệm tắt mạng / tải lại trang: Sinh viên không bị mất các đáp án đã chọn trước đó.
  - [ ] Tự động xóa sạch bộ nhớ tạm sau khi đã bấm nộp bài thành công lên server.

#### 🔹 Issue #19: `[Anti-Cheat] Browser Tab Switching & Focus Loss Detection`
- **Thuộc WBS:** 4.3.1 | **Gói WBS lớn:** Issue #10
- **Phân loại MoSCoW:** `must-have` | **Mô-đun:** `module:exam`
- **Milestone:** `Sprint 2: Realtime & Intelligence`
- **Độ phức tạp / Thời gian:** `3 Story Points` (~2 ngày) | **Assignee:** `Dev 3`
- **Mô tả công việc:**
  - Lập trình bộ lắng nghe sự kiện trình duyệt:
    - `document.addEventListener('visibilitychange')` để bắt sự kiện chuyển tab.
    - `window.addEventListener('blur')` để bắt sự kiện mở cửa sổ khác đè lên.
    - Chặn phím tắt mở Developer Tools (`F12`, `Ctrl+Shift+I`) và chặn sự kiện Copy/Paste trong vùng đề thi.
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Phát hiện ngay lập tức trong vòng 200ms khi sinh viên mở tab Google hoặc ứng dụng khác.
  - [ ] Không thể copy văn bản câu hỏi đem ra ngoài tra cứu.

#### 🔹 Issue #20: `[Anti-Cheat] Violation Warning Modal, Audit Logging & Auto-Lockout`
- **Thuộc WBS:** 4.3.2 | **Gói WBS lớn:** Issue #10
- **Phân loại MoSCoW:** `must-have` | **Mô-đun:** `module:exam`
- **Milestone:** `Sprint 2: Realtime & Intelligence`
- **Độ phức tạp / Thời gian:** `3 Story Points` (~2 ngày) | **Assignee:** `Dev 3`
- **Mô tả công việc:**
  - Hiển thị hộp thoại cảnh báo toàn màn hình khi phát hiện vi phạm: *"Cảnh báo: Bạn vừa rời khỏi màn hình làm bài! Lần vi phạm X/3"*.
  - Gửi nhật ký vi phạm (thời điểm, loại vi phạm) về backend để lưu vào `audit_logs`.
  - Tự động khóa bài và nộp bài cưỡng bức nếu số lần vi phạm vượt ngưỡng quy định (ví dụ: quá 3 lần).
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Hộp thoại cảnh báo xuất hiện ngay khi quay lại màn hình thi.
  - [ ] Vượt quá 3 lần vi phạm: Hệ thống tự động chuyển sang trạng thái nộp bài và ghi nhận lý do gian lận vào bảng điểm.

---

### MODULE 5.0: CHẤM ĐIỂM, GIA SƯ ẢO & PHÂN TÍCH HIỆU SUẤT (WBS 5.1, 5.2 & 5.3)

#### 🔹 Issue #21: `[Grading] Instant Multi-Question Type Auto-Grading Engine`
- **Thuộc WBS:** 5.1.1 | **Gói WBS lớn:** Issue #11
- **Phân loại MoSCoW:** `must-have` | **Mô-đun:** `module:tutor-analytics`
- **Milestone:** `Sprint 1: Core Foundation`
- **Độ phức tạp / Thời gian:** `3 Story Points` (~2 ngày) | **Assignee:** `Dev 4`
- **Mô tả công việc:**
  - Xây dựng thuật toán chấm điểm tự động trên backend ngay khi nhận bài nộp:
    - Câu trắc nghiệm chọn 1 đáp án: Đúng được điểm tối đa, sai 0 điểm.
    - Câu Đúng/Sai: Chấm theo từng ý.
    - Câu trắc nghiệm nhiều đáp án: Tính điểm theo tỷ lệ phần trăm các lựa chọn đúng.
  - Tính toán tổng điểm thang 10, thang 100 và thời gian làm bài thực tế.
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Chấm điểm chính xác 100% cho toàn bộ các dạng câu hỏi với thời gian xử lý < 500ms.
  - [ ] Lưu kết quả điểm số vào bảng `submissions` trong CSDL.

#### 🔹 Issue #22: `[Grading] Post-Exam Detailed Review Mode Interface`
- **Thuộc WBS:** 5.1.2 | **Gói WBS lớn:** Issue #11
- **Phân loại MoSCoW:** `must-have` | **Mô-đun:** `module:tutor-analytics`
- **Milestone:** `Sprint 1: Core Foundation`
- **Độ phức tạp / Thời gian:** `3 Story Points` (~2 ngày) | **Assignee:** `Dev 4`
- **Mô tả công việc:**
  - Xây dựng giao diện xem lại bài thi (*Review Mode*) hiển thị ngay sau khi nộp bài:
    - Đánh dấu màu xanh cho câu làm đúng, màu đỏ cho câu làm sai.
    - Đối chiếu đáp án sinh viên đã chọn và đáp án chính xác của đề thi.
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Sinh viên xem được chi tiết từng câu hỏi đúng/sai và tổng điểm đạt được.
  - [ ] Có bộ lọc nhanh: "Xem tất cả", "Chỉ xem câu sai", "Chỉ xem câu đúng".

#### 🔹 Issue #23: `[AI-Tutor] Contextual Explanation Generator API`
- **Thuộc WBS:** 5.2.1 | **Gói WBS lớn:** Issue #12
- **Phân loại MoSCoW:** `should-have` | **Mô-đun:** `module:tutor-analytics`
- **Milestone:** `Sprint 2: Realtime & Intelligence`
- **Độ phức tạp / Thời gian:** `3 Story Points` (~2 ngày) | **Assignee:** `Dev 4`
- **Mô tả công việc:**
  - Tích hợp dịch vụ Gia sư ảo (*AI Tutor*): Xây dựng prompt phân tích ngữ cảnh câu hỏi, phương án sinh viên chọn sai và giải thích cặn kẽ tại sao phương án đó chưa đúng, đồng thời phân tích bản chất vì sao phương án chuẩn là đáp án chính xác.
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Bấm nút "Hỏi Gia sư AI" trên câu hỏi sai hiển thị lời giải thích dễ hiểu, khách quan trong vòng < 3 giây.
  - [ ] Không đưa ra lời giải thích chung chung, phải phân tích đúng trọng tâm lỗi sai của sinh viên.

#### 🔹 Issue #24: `[AI-Tutor] Knowledge Gap Diagnostic & Review Recommendation Card`
- **Thuộc WBS:** 5.2.2 | **Gói WBS lớn:** Issue #12
- **Phân loại MoSCoW:** `should-have` | **Mô-đun:** `module:tutor-analytics`
- **Milestone:** `Sprint 2: Realtime & Intelligence`
- **Độ phức tạp / Thời gian:** `3 Story Points` (~2 ngày) | **Assignee:** `Dev 4`
- **Mô tả công việc:**
  - Tổng hợp danh sách các câu hỏi sai theo chuyên đề kiến thức, từ đó chỉ ra lỗ hổng kiến thức cốt lõi của sinh viên sau ca thi.
  - Sinh thẻ gợi ý lộ trình tự học (*Actionable Study Plan*): Cần đọc lại chương nào, ôn lại khái niệm nào.
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Thẻ tổng kết bài thi hiển thị rõ: "Lỗ hổng kiến thức chính: Kế thừa & Đa hình trong OOP".
  - [ ] Đề xuất ít nhất 2 gợi ý cụ thể để học viên cải thiện điểm số cho lần thi sau.

#### 🔹 Issue #25: `[Analytics] Student Progress & Topic Mastery Radar Chart`
- **Thuộc WBS:** 5.3.1 | **Gói WBS lớn:** Issue #13
- **Phân loại MoSCoW:** `should-have` | **Mô-đun:** `module:tutor-analytics`
- **Milestone:** `Sprint 2: Realtime & Intelligence`
- **Độ phức tạp / Thời gian:** `3 Story Points` (~2 ngày) | **Assignee:** `Dev 4`
- **Mô tả công việc:**
  - Xây dựng Dashboard cá nhân cho sinh viên:
    - Biểu đồ đường (Line Chart) thể hiện xu hướng điểm số qua các bài thi.
    - Biểu đồ mạng nhện / cột (Radar / Bar Chart) đo lường tỷ lệ làm đúng theo từng chuyên đề kiến thức (Topic Mastery).
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Biểu đồ trực quan hóa dữ liệu thực tế từ các lần làm bài của sinh viên bằng thư viện Chart.js hoặc Recharts.
  - [ ] Giao diện co giãn tốt (responsive) trên mọi kích thước màn hình.

#### 🔹 Issue #26: `[Analytics] Lecturer Exam Analytics & Score Distribution Histogram`
- **Thuộc WBS:** 5.3.2 | **Gói WBS lớn:** Issue #13
- **Phân loại MoSCoW:** `should-have` | **Mô-đun:** `module:tutor-analytics`
- **Milestone:** `Sprint 2: Realtime & Intelligence`
- **Độ phức tạp / Thời gian:** `3 Story Points` (~2 ngày) | **Assignee:** `Dev 4`
- **Mô tả công việc:**
  - Xây dựng Dashboard báo cáo dành cho Giảng viên:
    - Biểu đồ phổ điểm (Histogram) của cả lớp thi (phân loại Giỏi, Khá, Trung bình, Yếu).
    - Thống kê "Top 5 câu hỏi có tỷ lệ sai cao nhất" để giảng viên nắm bắt nội dung sinh viên chưa hiểu và hỗ trợ xuất bảng điểm ra file CSV.
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Hiển thị chính xác phổ điểm và danh sách câu hỏi học sinh hay nhầm lẫn nhất.
  - [ ] Bấm nút "Xuất CSV" tải về file bảng điểm lớp học chuẩn UTF-8.

---

### MODULE 6.0: DEVOPS, KIỂM THỬ & ĐÓNG DỰ ÁN (WBS 6.1 & 6.2)

#### 🔹 Issue #27: `[DevOps] Automated GitHub Actions CI/CD Pipeline`
- **Thuộc WBS:** 6.1.1 | **Gói WBS lớn:** Issue #14
- **Phân loại MoSCoW:** `must-have` | **Mô-đun:** `module:parser`
- **Milestone:** `Sprint 1: Core Foundation`
- **Độ phức tạp / Thời gian:** `2 Story Points` (~1.5 ngày) | **Assignee:** `Dev 1` & `Dev 3`
- **Mô tả công việc:**
  - Thiết lập GitHub Actions Workflow tự động chạy kiểm tra Linter, Type-check và Build dự án mỗi khi có Pull Request mới gửi vào nhánh `main`.
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Workflow báo xanh (Passed) trên PR hợp lệ và chặn merge nếu build thất bại.

#### 🔹 Issue #28: `[DevOps] Production Cloud Database & Web App Deployment`
- **Thuộc WBS:** 6.1.2 | **Gói WBS lớn:** Issue #14
- **Phân loại MoSCoW:** `must-have` | **Mô-đun:** `module:ai-gen`
- **Milestone:** `Sprint 2: Realtime & Intelligence`
- **Độ phức tạp / Thời gian:** `3 Story Points` (~2 ngày) | **Assignee:** `Dev 1` & `Dev 2`
- **Mô tả công việc:**
  - Triển khai CSDL PostgreSQL lên Supabase / Neon Cloud Free-tier.
  - Triển khai ứng dụng Web lên Vercel (Frontend) và Render/Railway (Backend), cấu hình chứng chỉ SSL (HTTPS) và bảo mật biến môi trường.
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Ứng dụng truy cập công khai được qua đường dẫn URL thực tế trên Internet.
  - [ ] Kết nối thông suốt với Cloud Database và gọi được AI API trên môi trường Production.

#### 🔹 Issue #29: `[Testing] End-to-End System Smoke Testing & Bug Bash`
- **Thuộc WBS:** 6.1.1 | **Gói WBS lớn:** Issue #14
- **Phân loại MoSCoW:** `must-have` | **Mô-đun:** Chung toàn nhóm
- **Milestone:** `Sprint 2: Realtime & Intelligence`
- **Độ phức tạp / Thời gian:** `3 Story Points` (~2 ngày) | **Assignee:** `Cả 4 Dev`
- **Mô tả công việc:**
  - Cả 4 thành viên cùng thực hiện kịch bản kiểm thử luồng nghiệp vụ khép kín (*End-to-End Flow*): Tải file trích xuất câu hỏi $\rightarrow$ AI sinh đề theo ma trận $\rightarrow$ Làm bài thi có bắt lỗi chuyển tab $\rightarrow$ Chấm điểm, hỏi AI Tutor và xem biểu đồ Analytics.
  - Sửa dứt điểm các lỗi phát sinh (*Zero Blocker/Critical Bugs*).
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Vượt qua toàn bộ kịch bản kiểm thử mẫu mà không gặp lỗi sập hệ thống (Crash).

#### 🔹 Issue #30: `[Docs] Quality & Risk Governance (DoD & Risk Register Setup)`
- **Thuộc WBS:** 6.2.1 | **Gói WBS lớn:** Issue #15
- **Phân loại MoSCoW:** `must-have` | **Mô-đun:** `module:parser`
- **Milestone:** `Sprint 1: Core Foundation`
- **Độ phức tạp / Thời gian:** `2 Story Points` (~1.5 ngày) | **Assignee:** `Dev 1 (Scrum Master)`
- **Mô tả công việc:**
  - Soạn thảo tài liệu tiêu chuẩn hoàn thành `docs/DEFINITION_OF_DONE.md`.
  - Thiết lập bảng theo dõi rủi ro thực tế `docs/RISK_REGISTER.md` (theo dõi rủi ro Rate-limit API, rủi ro file scan không parse được, rủi ro tiến độ).
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Hoàn thành 2 file tài liệu trong thư mục `docs/` và thông qua toàn nhóm.

#### 🔹 Issue #31: `[Docs] Sprint 1 Review, Retrospective & Tagged Pre-release v1.0`
- **Thuộc WBS:** 6.2.1 | **Gói WBS lớn:** Issue #15
- **Phân loại MoSCoW:** `should-have` | **Mô-đun:** Chung toàn nhóm
- **Milestone:** `Sprint 1: Core Foundation`
- **Độ phức tạp / Thời gian:** `2 Story Points` (~1 ngày) | **Assignee:** `Cả 4 Dev`
- **Mô tả công việc:**
  - Tổ chức họp Sprint 1 Review và viết biên bản `docs/RETROSPECTIVE_SPRINT_1.md` (What went well, What didn't go well, Action items).
  - Đóng Milestone Sprint 1 trên GitHub và tạo GitHub Release `v1.0.0-sprint1`.
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Milestone Sprint 1 đạt 100% Closed và có bản Release đính kèm ghi chú tính năng.

#### 🔹 Issue #32: `[Docs] User Guide, Final Showcase Slides & v2.0 Release`
- **Thuộc WBS:** 6.2.2 | **Gói WBS lớn:** Issue #15
- **Phân loại MoSCoW:** `should-have` | **Mô-đun:** Chung toàn nhóm
- **Milestone:** `Sprint 2: Realtime & Intelligence`
- **Độ phức tạp / Thời gian:** `3 Story Points` (~2 ngày) | **Assignee:** `Cả 4 Dev`
- **Mô tả công việc:**
  - Hoàn thiện tài liệu `README.md` hướng dẫn cài đặt và sử dụng chi tiết.
  - Chuẩn bị slide thuyết trình, video demo luồng sản phẩm và đóng gói GitHub Release `v2.0.0-final` phục vụ bảo vệ nghiệm thu Tuần 13.
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Hoàn thành trọn bộ hồ sơ nghiệm thu cuối kỳ và sẵn sàng bảo vệ trước hội đồng.

---

## 🛠️ PHỤ LỤC: SCRIPT GITHUB CLI TỰ ĐỘNG TẠO 32 ISSUES & 2 MILESTONES

Nhóm có thể mở Terminal tại thư mục dự án và chạy đoạn script sau để tạo Milestones và tự động sinh toàn bộ 32 Issues lên GitHub:

```bash
# 1. Tạo 2 Sprint Milestones
gh api repos/:owner/:repo/milestones -f title="Sprint 1: Core Foundation" -f description="Mô-đun Hạ tầng, Auth, File Parser, AI Gen ma trận cơ bản, Chấm điểm"
gh api repos/:owner/:repo/milestones -f title="Sprint 2: Realtime & Intelligence" -f description="Mô-đun Chống gian lận, AI Tutor ngữ cảnh, Analytics Dashboard, Triển khai Cloud"

# 2. Tạo 32 Issues chi tiết (Ví dụ mẫu lệnh tạo tự động)
gh issue create --title "[Infra] Setup Full-stack Project Monorepo & Code Quality Tools" --label "must-have,module:parser" --milestone "Sprint 1: Core Foundation" --body "Thực hiện WBS 1.1.1 - Khung mã nguồn, ESLint, Prettier. Assignee: Dev 1"
gh issue create --title "[Database] Design Relational Schema (ERD) & Database Migrations" --label "must-have,module:parser" --milestone "Sprint 1: Core Foundation" --body "Thực hiện WBS 1.1.2 - Sơ đồ ERD và Prisma migrations. Assignee: Dev 1"
gh issue create --title "[Auth] User Registration, Login & JWT Token Management" --label "must-have,module:parser" --milestone "Sprint 1: Core Foundation" --body "Thực hiện WBS 1.2.1 - Đăng nhập, đăng ký JWT. Assignee: Dev 1"
gh issue create --title "[Auth] Role-Based Route Protection & User Profile UI" --label "must-have,module:parser" --milestone "Sprint 1: Core Foundation" --body "Thực hiện WBS 1.2.2 - Phân quyền route và trang profile. Assignee: Dev 1"
gh issue create --title "[Parser] File Upload Pipeline & Raw Text Extraction (PDF, DOCX, TXT)" --label "must-have,module:parser" --milestone "Sprint 1: Core Foundation" --body "Thực hiện WBS 2.1.1 - Đọc luồng file PDF, DOCX, TXT. Assignee: Dev 1"
gh issue create --title "[Parser] Regex Pattern Matching Engine for Questions & Options" --label "must-have,module:parser" --milestone "Sprint 1: Core Foundation" --body "Thực hiện WBS 2.1.2 - Thuật toán Regex nhận diện câu hỏi trắc nghiệm. Assignee: Dev 1"
gh issue create --title "[Parser-UI] Question Extraction Preview & Inline Editing Table" --label "must-have,module:parser" --milestone "Sprint 1: Core Foundation" --body "Thực hiện WBS 2.2.1 - Bảng xem trước và sửa câu hỏi bóc tách. Assignee: Dev 1"
gh issue create --title "[Bank] Question Bank Management CRUD API & Filtering UI" --label "must-have,module:parser" --milestone "Sprint 1: Core Foundation" --body "Thực hiện WBS 2.2.2 - CRUD ngân hàng câu hỏi theo chuyên đề. Assignee: Dev 1"
gh issue create --title "[AI-Gen] LLM Client Adapter & Resilient Calling Service" --label "must-have,module:ai-gen" --milestone "Sprint 1: Core Foundation" --body "Thực hiện WBS 3.1.1 - Kết nối Gemini/OpenAI API và xử lý Rate-limit. Assignee: Dev 2"
gh issue create --title "[AI-Gen] Strict JSON Schema Definition & Response Parser" --label "must-have,module:ai-gen" --milestone "Sprint 1: Core Foundation" --body "Thực hiện WBS 3.1.2 - Ép kiểu đầu ra AI theo chuẩn JSON Schema. Assignee: Dev 2"
gh issue create --title "[AI-Gen] Bloom Taxonomy Prompt Templates for Multi-Type Questions" --label "must-have,module:ai-gen" --milestone "Sprint 1: Core Foundation" --body "Thực hiện WBS 3.2.1 - Prompt 3 mức độ nhận thức Bloom và đa dạng câu hỏi. Assignee: Dev 2"
gh issue create --title "[AI-Gen] Exam Matrix Configuration Modal & AI Generation Flow" --label "must-have,module:ai-gen" --milestone "Sprint 1: Core Foundation" --body "Thực hiện WBS 3.2.2 - Giao diện ma trận đề thi và luồng sinh câu hỏi AI. Assignee: Dev 2"
gh issue create --title "[AI-Gen] Document Text Chunking & Context Window Optimization" --label "should-have,module:ai-gen" --milestone "Sprint 2: Realtime & Intelligence" --body "Thực hiện WBS 3.3.1 - Thuật toán phân đoạn văn bản tài liệu bài giảng. Assignee: Dev 2"
gh issue create --title "[AI-Gen] End-to-End File-to-Quiz AI Generation API & UI" --label "should-have,module:ai-gen" --milestone "Sprint 2: Realtime & Intelligence" --body "Thực hiện WBS 3.3.2 - Luồng tải file bài giảng sinh câu hỏi AI theo ngữ cảnh. Assignee: Dev 2"
gh issue create --title "[Exam] Exam Room Creation & Scheduling Settings API/UI" --label "must-have,module:exam" --milestone "Sprint 1: Core Foundation" --body "Thực hiện WBS 4.1.1 - Tạo phòng thi, thời lượng, mật khẩu và ca thi. Assignee: Dev 3"
gh issue create --title "[Exam] Seed-based Question & Answer Shuffling Algorithm" --label "must-have,module:exam" --milestone "Sprint 1: Core Foundation" --body "Thực hiện WBS 4.1.2 - Thuật toán Fisher-Yates xáo trộn đề và đáp án. Assignee: Dev 3"
gh issue create --title "[Exam] Focused Student Exam Room UI & Countdown Timer" --label "must-have,module:exam" --milestone "Sprint 2: Realtime & Intelligence" --body "Thực hiện WBS 4.2.1 - Phòng thi tập trung, đồng hồ đếm ngược và tự động nộp bài. Assignee: Dev 3"
gh issue create --title "[Exam] LocalStorage Real-time Answer Caching & Network Reconnect" --label "must-have,module:exam" --milestone "Sprint 2: Realtime & Intelligence" --body "Thực hiện WBS 4.2.2 - Lưu tạm câu trả lời vào LocalStorage chống mất bài khi rớt mạng. Assignee: Dev 3"
gh issue create --title "[Anti-Cheat] Browser Tab Switching & Focus Loss Detection" --label "must-have,module:exam" --milestone "Sprint 2: Realtime & Intelligence" --body "Thực hiện WBS 4.3.1 - Lắng nghe sự kiện visibilitychange và blur bắt gian lận. Assignee: Dev 3"
gh issue create --title "[Anti-Cheat] Violation Warning Modal, Audit Logging & Auto-Lockout" --label "must-have,module:exam" --milestone "Sprint 2: Realtime & Intelligence" --body "Thực hiện WBS 4.3.2 - Cảnh báo vi phạm, ghi log và tự động khóa bài sau 3 lần. Assignee: Dev 3"
gh issue create --title "[Grading] Instant Multi-Question Type Auto-Grading Engine" --label "must-have,module:tutor-analytics" --milestone "Sprint 1: Core Foundation" --body "Thực hiện WBS 5.1.1 - Thuật toán chấm điểm tức thì các dạng câu hỏi trắc nghiệm. Assignee: Dev 4"
gh issue create --title "[Grading] Post-Exam Detailed Review Mode Interface" --label "must-have,module:tutor-analytics" --milestone "Sprint 1: Core Foundation" --body "Thực hiện WBS 5.1.2 - Giao diện xem lại chi tiết bài làm sau khi nộp bài. Assignee: Dev 4"
gh issue create --title "[AI-Tutor] Contextual Explanation Generator API" --label "should-have,module:tutor-analytics" --milestone "Sprint 2: Realtime & Intelligence" --body "Thực hiện WBS 5.2.1 - Gia sư ảo AI Tutor giải thích lý do đúng/sai theo ngữ cảnh. Assignee: Dev 4"
gh issue create --title "[AI-Tutor] Knowledge Gap Diagnostic & Review Recommendation Card" --label "should-have,module:tutor-analytics" --milestone "Sprint 2: Realtime & Intelligence" --body "Thực hiện WBS 5.2.2 - Chẩn đoán lỗ hổng kiến thức và gợi ý ôn tập cá nhân hóa. Assignee: Dev 4"
gh issue create --title "[Analytics] Student Progress & Topic Mastery Radar Chart" --label "should-have,module:tutor-analytics" --milestone "Sprint 2: Realtime & Intelligence" --body "Thực hiện WBS 5.3.1 - Dashboard sinh viên: biểu đồ tiến độ và tỷ lệ đúng theo chuyên đề. Assignee: Dev 4"
gh issue create --title "[Analytics] Lecturer Exam Analytics & Score Distribution Histogram" --label "should-have,module:tutor-analytics" --milestone "Sprint 2: Realtime & Intelligence" --body "Thực hiện WBS 5.3.2 - Dashboard giảng viên: biểu đồ phổ điểm lớp và câu hỏi hay sai. Assignee: Dev 4"
gh issue create --title "[DevOps] Automated GitHub Actions CI/CD Pipeline" --label "must-have,module:parser" --milestone "Sprint 1: Core Foundation" --body "Thực hiện WBS 6.1.1 - GitHub Actions tự động lint và build khi có PR. Assignee: Dev 1, Dev 3"
gh issue create --title "[DevOps] Production Cloud Database & Web App Deployment" --label "must-have,module:ai-gen" --milestone "Sprint 2: Realtime & Intelligence" --body "Thực hiện WBS 6.1.2 - Triển khai Supabase, Vercel và Render. Assignee: Dev 1, Dev 2"
gh issue create --title "[Testing] End-to-End System Smoke Testing & Bug Bash" --label "must-have" --milestone "Sprint 2: Realtime & Intelligence" --body "Thực hiện WBS 6.1.1 - Kiểm thử khép kín toàn bộ luồng nghiệp vụ. Assignee: Cả nhóm"
gh issue create --title "[Docs] Quality & Risk Governance (DoD & Risk Register Setup)" --label "must-have,module:parser" --milestone "Sprint 1: Core Foundation" --body "Thực hiện WBS 6.2.1 - Thiết lập DEFINITION_OF_DONE và RISK_REGISTER. Assignee: Dev 1"
gh issue create --title "[Docs] Sprint 1 Review, Retrospective & Tagged Pre-release v1.0" --label "should-have" --milestone "Sprint 1: Core Foundation" --body "Thực hiện WBS 6.2.1 - Biên bản Retrospective Sprint 1 và Release v1.0. Assignee: Cả nhóm"
gh issue create --title "[Docs] User Guide, Final Showcase Slides & v2.0 Release" --label "should-have" --milestone "Sprint 2: Realtime & Intelligence" --body "Thực hiện WBS 6.2.2 - Hoàn thiện README, slide báo cáo và Release v2.0 nghiệm thu. Assignee: Cả nhóm"
```
