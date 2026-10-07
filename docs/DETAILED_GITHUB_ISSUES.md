# 📋 CHI TIẾT PRODUCT BACKLOG & GITHUB ISSUES — SMART QUIZ
**Dự án:** Nền tảng Kiểm tra và Ôn luyện Trắc nghiệm Trực tuyến Tích hợp Trí tuệ Nhân tạo (*Smart Quiz*)  
**Mã nguồn / Repo:** [github.com/nhatanh19/smart-quiz](https://github.com/nhatanh19/smart-quiz)  
**Tài liệu tham chiếu:** `docs/WBS_AND_BACKLOG.md` | Chuẩn môn học: **Week 03 (WBS) & Week 04–05 (Agile/Scrum on GitHub)**  
**Nguyên tắc cốt lõi:** **Triển khai song song 4 lập trình viên (Parallel Zero-Blocking)** ngay từ Tuần 1 của Sprint 1, cân bằng chính xác khối lượng công việc (~**25% code/thành viên**), loại bỏ triệt để điểm nghẽn phụ thuộc (bottleneck) tại Dev 1.

---

## 🎯 BẢNG MA TRẬN PHÂN BỔ CÂN BẰNG 4 THÀNH VIÊN THEO SPRINT

| Thành viên | Trách nhiệm cốt lõi | Sprint 1 (Core Foundation) | Sprint 2 (Realtime & AI Deep) | Tổng số Issues | Tổng Story Points | Tỷ lệ đóng góp |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Dev 1 (Team Leader)** | Hạ tầng monorepo, CSDL tổng thể & Bộ bóc tách tài liệu (*File Parser*) | **4 Issues (11 SP)**<br>#1, #2, #3, #4 | **3 Issues (8 SP)**<br>#17, #18, #19 | **7 Issues** | **19 SP** | **~25%** |
| **Dev 2 (AI Engineer)** | Tích hợp LLM API, Ép kiểu JSON, Prompt ma trận & Ngân hàng câu hỏi | **4 Issues (11 SP)**<br>#5, #6, #7, #8 | **3 Issues (8 SP)**<br>#20, #21, #22 | **7 Issues** | **19 SP** | **~25%** |
| **Dev 3 (Core Engineer)** | Xác thực Auth (JWT/RBAC) + Phòng thi trực tuyến & Chống gian lận | **4 Issues (10 SP)**<br>#9, #10, #11, #12 | **4 Issues (12 SP)**<br>#23, #24, #25, #26 | **8 Issues** | **22 SP** | **~25%** |
| **Dev 4 (Data & Tutor)** | Chấm điểm tự động, Gia sư ảo AI Tutor & Dashboard phân tích hiệu suất | **4 Issues (11 SP)**<br>#13, #14, #15, #16 | **3 Issues (8 SP)**<br>#27, #28, #29 | **7 Issues** | **19 SP** | **~25%** |
| **Cả nhóm (1, 2, 3, 4)** | Kiểm thử khép kín E2E, Sprint Retrospectives & Bàn giao sản phẩm | **1 Issue (2 SP)**<br>#31 (Retro 1) | **2 Issues (5 SP)**<br>#30, #32 (Test & Release) | **3 Issues** | **7 SP** | **Hợp tác** |

> 💡 **Quy tắc không phụ thuộc (Decoupled Rule):** Trong 2 ngày đầu của Sprint 1, Dev 1 khởi tạo Monorepo và khai báo sơ đồ thực thể Typescript/Prisma Interfaces. Ngay lập tức, Dev 2, 3, 4 dựa trên Interface dùng Mock Data để lập trình song song module của mình mà không cần đợi Dev 1 xong backend!

---

## 🏃 GIAI ĐOẠN SPRINT 1: CORE FOUNDATION (TUẦN 4 – TUẦN 6)
*Mục tiêu: Đạt được bản chạy thử cốt lõi (Working Increment) với đủ 4 mô-đun hoạt động đồng thời.*

---

### PHÂN HỆ DEV 1 (HẠ TẦNG & FILE PARSER) — SPRINT 1

#### 🔹 Issue #1: `[Infra] Setup Full-stack Project Monorepo & Code Quality Tools`
- **Phân loại MoSCoW:** `must-have` | **Mô-đun:** `module:parser` | **Milestone:** `Sprint 1: Core Foundation`
- **Độ phức tạp / Thời gian:** `2 Story Points` (~1.5 ngày) | **Assignee:** `Dev 1`
- **Mô tả công việc:** Khởi tạo khung mã nguồn Next.js/React (Frontend) và Node.js/Express hoặc FastAPI (Backend). Cấu hình TypeScript, ESLint, Prettier, `.gitignore`, `.env.example`.
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Khởi chạy thành công cả Frontend và Backend trên máy local (`localhost`).
  - [ ] Lệnh `npm run lint` chạy không báo lỗi.
  - [ ] Cung cấp README hướng dẫn khởi chạy ban đầu cho 3 thành viên còn lại.

#### 🔹 Issue #2: `[Database] Design Relational Schema (ERD) & Database Migrations`
- **Phân loại MoSCoW:** `must-have` | **Mô-đun:** `module:parser` | **Milestone:** `Sprint 1: Core Foundation`
- **Độ phức tạp / Thời gian:** `3 Story Points` (~2 ngày) | **Assignee:** `Dev 1`
- **Mô tả công việc:** Thiết kế sơ đồ quan hệ thực thể (ERD) chuẩn hóa: `users`, `questions`, `options`, `exams`, `exam_questions`, `submissions`, `submission_answers`. Cấu hình Prisma/TypeORM và script seed data mẫu.
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Chạy lệnh `migration` tạo đủ bảng trong PostgreSQL/Supabase.
  - [ ] Seed sẵn ít nhất 2 user (1 Giảng viên, 1 Sinh viên) và 10 câu hỏi mẫu.
  - [ ] Xuất file định nghĩa TypeScript Interfaces dùng chung cho Dev 2, 3, 4.

#### 🔹 Issue #3: `[Parser] File Upload Pipeline & Raw Text Extraction (PDF, DOCX, TXT)`
- **Phân loại MoSCoW:** `must-have` | **Mô-đun:** `module:parser` | **Milestone:** `Sprint 1: Core Foundation`
- **Độ phức tạp / Thời gian:** `3 Story Points` (~2 ngày) | **Assignee:** `Dev 1`
- **Mô tả công việc:** Xây dựng API tiếp nhận tệp tải lên (Multer, kiểm tra định dạng và dung lượng < 10MB). Tích hợp thư viện đọc text thô: `pdf-parse` (cho PDF), `mammoth` (cho Word DOCX) và UTF-8 FileReader (cho TXT).
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Đọc thành công file PDF, DOCX, TXT và trả về chuỗi văn bản thô đầy đủ dấu tiếng Việt.
  - [ ] Xử lý ngoại lệ an toàn khi gặp file lỗi hoặc sai định dạng.

#### 🔹 Issue #4: `[Parser] Regex Pattern Matching Engine for Questions & Options`
- **Phân loại MoSCoW:** `must-have` | **Mô-đun:** `module:parser` | **Milestone:** `Sprint 1: Core Foundation`
- **Độ phức tạp / Thời gian:** `3 Story Points` (~2 ngày) | **Assignee:** `Dev 1`
- **Mô tả công việc:** Thuật toán Regex nhận diện tự động: Tiêu đề câu hỏi (`Câu 1:`, `1.`), các phương án lựa chọn (`A.`, `B.`, `C.`, `D.`), đáp án đúng (`Đáp án: A`, gạch chân hoặc `*A.`) và lời giải thích.
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Bóc tách chính xác $\ge$ 90% số câu trong bộ đề Word/PDF thử nghiệm.
  - [ ] Trả về danh sách đối tượng câu hỏi chuẩn hóa dạng JSON.

---

### PHÂN HỆ DEV 2 (AI QUIZ GENERATOR & NGÂN HÀNG ĐỀ) — SPRINT 1

#### 🔹 Issue #5: `[AI-Gen] LLM Client Adapter & Resilient Calling Service`
- **Phân loại MoSCoW:** `must-have` | **Mô-đun:** `module:ai-gen` | **Milestone:** `Sprint 1: Core Foundation`
- **Độ phức tạp / Thời gian:** `3 Story Points` (~2 ngày) | **Assignee:** `Dev 2`
- **Mô tả công việc:** Thiết lập Adapter kết nối Google Gemini API (model `gemini-1.5-flash` / `gemini-2.5-flash`) hoặc OpenAI API. Xây dựng cơ chế bắt lỗi Rate-limit 429 và cơ chế tự động thử lại (*Exponential Backoff Retry*).
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Gọi thành công AI API từ backend với API Key an toàn trong `.env`.
  - [ ] Có fallback retry tối đa 3 lần khi mạng chập chờn hoặc API báo bận.

#### 🔹 Issue #6: `[AI-Gen] Strict JSON Schema Definition & Response Parser`
- **Phân loại MoSCoW:** `must-have` | **Mô-đun:** `module:ai-gen` | **Milestone:** `Sprint 1: Core Foundation`
- **Độ phức tạp / Thời gian:** `3 Story Points` (~2 ngày) | **Assignee:** `Dev 2`
- **Mô tả công việc:** Định nghĩa Schema xác thực dữ liệu chặt chẽ bằng thư viện Zod/Pydantic cho cấu trúc câu hỏi. Ép kiểu đầu ra từ LLM bằng `response_mime_type: "application/json"` để đảm bảo 100% kết quả là JSON hợp lệ.
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Dữ liệu sinh ra parse thành công thành danh sách: `[{ question, options, correctAnswer, difficulty, explanation }]`.
  - [ ] Tuyệt đối không bị crash server khi AI trả về phản hồi sai lệch.

#### 🔹 Issue #7: `[AI-Gen] Bloom Taxonomy Prompt Templates for Multi-Type Questions`
- **Phân loại MoSCoW:** `must-have` | **Mô-đun:** `module:ai-gen` | **Milestone:** `Sprint 1: Core Foundation`
- **Độ phức tạp / Thời gian:** `3 Story Points` (~2 ngày) | **Assignee:** `Dev 2`
- **Mô tả công việc:** Thiết kế các bộ Prompt sinh câu hỏi theo 3 mức thang Bloom: Nhận biết (*Knowledge*), Thông hiểu (*Comprehension*), Vận dụng (*Application*). Hỗ trợ các thể loại: Chọn 1 đáp án, Chọn nhiều đáp án, Đúng/Sai.
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] AI sinh đúng số lượng câu hỏi và tỷ lệ độ khó theo yêu cầu trong prompt.
  - [ ] Các phương án nhiễu có tính phân loại cao, không trùng lặp vô lý.

#### 🔹 Issue #8: `[Bank] Question Bank Management CRUD API & Filtering UI`
- **Phân loại MoSCoW:** `must-have` | **Mô-đun:** `module:ai-gen` | **Milestone:** `Sprint 1: Core Foundation`
- **Độ phức tạp / Thời gian:** `2 Story Points` (~1.5 ngày) | **Assignee:** `Dev 2 (AI Engineer)`
- **Mô tả công việc:** Xây dựng API và giao diện CRUD Ngân hàng câu hỏi: Thêm câu hỏi thủ công, sửa, xóa, tìm kiếm theo từ khóa và lọc theo chủ đề / môn học / độ khó.
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Thêm, sửa, xóa câu hỏi trong ngân hàng đề hoạt động trơn tru.
  - [ ] Bộ lọc theo chủ đề trả về kết quả chính xác tức thì (< 300ms).

---

### PHÂN HỆ DEV 3 (XÁC THỰC AUTH & CORE EXAM ENGINE) — SPRINT 1

#### 🔹 Issue #9: `[Auth] User Registration, Login & JWT Token Management`
- **Phân loại MoSCoW:** `must-have` | **Mô-đun:** `module:exam` | **Milestone:** `Sprint 1: Core Foundation`
- **Độ phức tạp / Thời gian:** `3 Story Points` (~2 ngày) | **Assignee:** `Dev 3 (Core Engineer)`
- **Mô tả công việc:** API và giao diện Đăng ký (`/register`), Đăng nhập (`/login`). Băm mật khẩu an toàn bằng `bcrypt`, sinh mã `Access Token` và `Refresh Token` qua JWT.
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Đăng ký lưu mật khẩu đã băm vào DB; đăng nhập trả về JWT hợp lệ.
  - [ ] Xử lý thông báo lỗi chuẩn xác khi sai mật khẩu hoặc trùng email.

#### 🔹 Issue #10: `[Auth] Role-Based Route Protection (RBAC) & User Profile UI`
- **Phân loại MoSCoW:** `must-have` | **Mô-đun:** `module:exam` | **Milestone:** `Sprint 1: Core Foundation`
- **Độ phức tạp / Thời gian:** `2 Story Points` (~1.5 ngày) | **Assignee:** `Dev 3 (Core Engineer)`
- **Mô tả công việc:** Xây dựng Middleware chặn truy cập theo 3 vai trò: `INSTRUCTOR`, `STUDENT`, `ADMIN`. Giao diện trang Profile cá nhân và chức năng Đăng xuất.
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Sinh viên không thể vào các route tạo đề thi của Giảng viên.
  - [ ] Hiển thị đúng thông tin cá nhân và vai trò sau khi đăng nhập.

#### 🔹 Issue #11: `[Exam] Exam Room Creation & Scheduling Settings API/UI`
- **Phân loại MoSCoW:** `must-have` | **Mô-đun:** `module:exam` | **Milestone:** `Sprint 1: Core Foundation`
- **Độ phức tạp / Thời gian:** `3 Story Points` (~2 ngày) | **Assignee:** `Dev 3`
- **Mô tả công việc:** Giao diện & API tạo ca thi: Giảng viên chọn bộ câu hỏi từ ngân hàng đề, cài đặt thời gian bắt đầu/kết thúc, thời lượng thi (phút), mật khẩu phòng thi (PIN) và số lượt làm tối đa.
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Giảng viên tạo được ca thi và sinh mã phòng thi (Exam Code).
  - [ ] Sinh viên nhập đúng mã và mật khẩu mới được vào phòng chờ.

#### 🔹 Issue #12: `[Exam] Seed-based Question & Answer Shuffling Algorithm`
- **Phân loại MoSCoW:** `must-have` | **Mô-đun:** `module:exam` | **Milestone:** `Sprint 1: Core Foundation`
- **Độ phức tạp / Thời gian:** `2 Story Points` (~1.5 ngày) | **Assignee:** `Dev 3`
- **Mô tả công việc:** Thuật toán xáo trộn ngẫu nhiên (*Fisher-Yates Shuffle*) dựa trên mã định danh thí sinh (`studentId + examId`). Đảo vị trí câu hỏi và thứ tự các đáp án A, B, C, D độc lập cho từng thí sinh nhưng vẫn map đúng đáp án gốc khi nộp.
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Hai sinh viên vào cùng 1 ca thi nhận được thứ tự câu hỏi và phương án hoàn toàn khác nhau.
  - [ ] Ánh xạ chính xác câu trả lời của thí sinh về ID phương án gốc trên server.

---

### PHÂN HỆ DEV 4 (CHẤM ĐIỂM, REVIEW MODE & AI TUTOR) — SPRINT 1

#### 🔹 Issue #13: `[Grading] Instant Multi-Question Type Auto-Grading Engine`
- **Phân loại MoSCoW:** `must-have` | **Mô-đun:** `module:tutor-analytics` | **Milestone:** `Sprint 1: Core Foundation`
- **Độ phức tạp / Thời gian:** `3 Story Points` (~2 ngày) | **Assignee:** `Dev 4`
- **Mô tả công việc:** Bộ chấm điểm tự động tức thì trên backend khi nhận bài nộp: Chấm câu 1 đáp án, câu nhiều đáp án (tính điểm thành phần), câu Đúng/Sai. Tính toán tổng điểm thang 10 và thời gian làm bài.
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Chấm điểm chính xác 100% cho mọi dạng câu hỏi với thời gian xử lý < 300ms.
  - [ ] Lưu kết quả bài làm vào bảng `submissions` trong CSDL.

#### 🔹 Issue #14: `[Grading] Post-Exam Detailed Review Mode Interface`
- **Phân loại MoSCoW:** `must-have` | **Mô-đun:** `module:tutor-analytics` | **Milestone:** `Sprint 1: Core Foundation`
- **Độ phức tạp / Thời gian:** `3 Story Points` (~2 ngày) | **Assignee:** `Dev 4`
- **Mô tả công việc:** Giao diện xem lại bài thi (*Review Mode*) ngay sau khi nộp: Đánh dấu màu xanh cho câu làm đúng, màu đỏ cho câu làm sai; đối chiếu đáp án thí sinh chọn với đáp án chuẩn.
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Sinh viên xem được chi tiết từng câu làm đúng/sai và tổng điểm.
  - [ ] Có bộ lọc nhanh: "Tất cả", "Chỉ xem câu sai", "Chỉ xem câu đúng".

#### 🔹 Issue #15: `[AI-Tutor] Contextual Explanation Generator API`
- **Phân loại MoSCoW:** `should-have` | **Mô-đun:** `module:tutor-analytics` | **Milestone:** `Sprint 1: Core Foundation`
- **Độ phức tạp / Thời gian:** `3 Story Points` (~2 ngày) | **Assignee:** `Dev 4 (Data & Tutor Engineer)`
- **Mô tả công việc:** Tích hợp Gia sư ảo (AI Tutor): Xây dựng Prompt phân tích ngữ cảnh câu hỏi, giải thích cặn kẽ tại sao phương án sinh viên chọn là sai và tại sao phương án chuẩn là đáp án đúng.
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Bấm nút "Giải thích bằng AI" trên câu sai hiển thị lời giải thích chi tiết trong vòng < 3 giây.
  - [ ] Giọng văn sư phạm, dễ hiểu, phân tích trúng nguyên nhân nhầm lẫn.

#### 🔹 Issue #16: `[AI-Tutor] Knowledge Gap Diagnostic Card in Review UI`
- **Phân loại MoSCoW:** `should-have` | **Mô-đun:** `module:tutor-analytics` | **Milestone:** `Sprint 1: Core Foundation`
- **Độ phức tạp / Thời gian:** `2 Story Points` (~1.5 ngày) | **Assignee:** `Dev 4 (Data & Tutor Engineer)`
- **Mô tả công việc:** Tổng hợp các câu hỏi làm sai theo tag chủ đề, chỉ ra lỗ hổng kiến thức chính của học viên và đề xuất thẻ gợi ý ôn tập (*Actionable Study Advice*).
- **Tiêu chí hoàn thành (Acceptance Criteria / DoD):**
  - [ ] Thẻ tổng kết hiển thị rõ: "Chủ đề bạn cần củng cố: Kế thừa & Đa hình trong OOP".
  - [ ] Đề xuất ít nhất 2 gợi ý cụ thể để cải thiện kết quả.

---

## 🚀 GIAI ĐOẠN SPRINT 2: REALTIME, CHỐNG GIAN LẬN & DEPLOYMENT (TUẦN 8 – TUẦN 12)
*Mục tiêu: Hoàn thiện tính năng chuyên sâu, chống gian lận, báo cáo phân tích, kiểm thử E2E và triển khai Cloud.*

---

### PHÂN HỆ DEV 1 (PREVIEW UI, CI/CD & QUALITY) — SPRINT 2
- **Issue #17:** `[Parser-UI] Question Extraction Preview & Inline Editing Table` (Dev 1 - 3 SP)  
  *Giao diện bảng duyệt trước câu hỏi bóc tách từ file, cho phép sửa trực tiếp văn bản, đổi đáp án đúng hoặc xóa câu sai trước khi lưu.*
- **Issue #18:** `[DevOps] Automated GitHub Actions CI/CD Pipeline` (Dev 1 - 2 SP)  
  *Workflow tự động kiểm tra Type-check, Lint và Build dự án mỗi khi mở Pull Request vào nhánh `main`.*
- **Issue #19:** `[Docs] Quality & Risk Governance (DoD & Risk Register Setup)` (Dev 1 - 3 SP)  
  *Thiết lập tài liệu `DEFINITION_OF_DONE.md` và cập nhật sổ theo dõi rủi ro thực tế `RISK_REGISTER.md`.*

---

### PHÂN HỆ DEV 2 (MA TRẬN ĐỀ THI & RAG FILE QUIZ) — SPRINT 2
- **Issue #20:** `[AI-Gen] Exam Matrix Configuration Modal & AI Generation Flow` (Dev 2 - 3 SP)  
  *Giao diện ma trận đề thi: Thanh trượt tỷ lệ độ khó (Nhận biết/Thông hiểu/Vận dụng), chọn số câu và duyệt câu hỏi AI sinh.*
- **Issue #21:** `[AI-Gen] Document Text Chunking & Context Window Optimization` (Dev 2 - 2 SP)  
  *Thuật toán phân đoạn văn bản giáo trình bài giảng dài (Sliding Window Chunking) làm ngữ cảnh sạch cho prompt.*
- **Issue #22:** `[AI-Gen] End-to-End File-to-Quiz AI Generation API & UI` (Dev 2 - 3 SP)  
  *Luồng hoàn chỉnh: Tải tệp bài giảng lên $\rightarrow$ AI sinh bộ câu hỏi trắc nghiệm bám sát nội dung bài học.*

---

### PHÂN HỆ DEV 3 (PHÒNG THI TẬP TRUNG & CHỐNG GIAN LẬN) — SPRINT 2
- **Issue #23:** `[Exam] Focused Student Exam Room UI & Countdown Timer` (Dev 3 - 3 SP)  
  *Giao diện làm bài tập trung, đồng hồ đếm ngược thời gian thực, bảng điều hướng câu hỏi và tự động thu bài khi hết giờ.*
- **Issue #24:** `[Exam] LocalStorage Real-time Answer Caching & Recovery` (Dev 3 - 3 SP)  
  *Tự động lưu tạm đáp án vào `localStorage` theo cơ chế Debounce; tự khôi phục bài làm 100% khi rớt mạng hoặc tải lại trang.*
- **Issue #25:** `[Anti-Cheat] Browser Tab Switching & Focus Loss Detection` (Dev 3 - 3 SP)  
  *Bắt sự kiện chuyển tab (`visibilitychange`), rời cửa sổ (`blur`), chặn phím tắt F12 và chặn Copy/Paste trong phòng thi.*
- **Issue #26:** `[Anti-Cheat] Violation Warning Modal, Audit Logging & Auto-Lockout` (Dev 3 - 3 SP)  
  *Cảnh báo vi phạm toàn màn hình, ghi log vi phạm về server và tự động khóa/thu bài nếu vi phạm quá 3 lần.*

---

### PHÂN HỆ DEV 4 (DASHBOARD ANALYTICS & CLOUD DEPLOY) — SPRINT 2
- **Issue #27:** `[Analytics] Student Progress & Topic Mastery Radar Chart` (Dev 4 - 3 SP)  
  *Bảng điều khiển học viên: Biểu đồ đường xu hướng điểm số và biểu đồ mạng nhện đo lường mức độ nắm vững từng chuyên đề.*
- **Issue #28:** `[Analytics] Lecturer Exam Analytics & Score Distribution Histogram` (Dev 4 - 3 SP)  
  *Bảng điều khiển giảng viên: Biểu đồ phổ điểm lớp học, thống kê top 5 câu hỏi hay sai nhất và chức năng xuất file điểm CSV.*
- **Issue #29:** `[DevOps] Production Cloud Database & Web App Deployment` (Dev 4 & Dev 1 - 2 SP)  
  *Triển khai PostgreSQL lên Supabase, Web App lên Vercel/Render, cấu hình SSL và biến môi trường Production.*

---

### TOÀN ĐỘI NGŨ (DEV 1, 2, 3, 4) — TEST, RETROSPECTIVE & RELEASE
- **Issue #30:** `[Testing] End-to-End System Smoke Testing & Bug Bash` (Cả 4 Dev - 3 SP - Sprint 2)  
  *Kiểm thử khép kín toàn bộ luồng: Bóc tách file $\rightarrow$ AI sinh đề $\rightarrow$ Thi trực tuyến $\rightarrow$ Chấm điểm $\rightarrow$ AI Tutor $\rightarrow$ Analytics.*
- **Issue #31:** `[Docs] Sprint 1 Review, Retrospective & Tagged Pre-release v1.0` (Cả 4 Dev - 2 SP - Cuối Sprint 1)  
  *Họp Retrospective Sprint 1 (`RETROSPECTIVE_SPRINT_1.md`), đóng Milestone Sprint 1 và tạo Release tag `v1.0.0-sprint1`.*
- **Issue #32:** `[Docs] User Guide, Final Showcase Slides & v2.0 Release` (Cả 4 Dev - 2 SP - Cuối Sprint 2 / Tuần 13)  
  *Tài liệu README hướng dẫn sử dụng, slide thuyết trình nghiệm thu và bản phát hành cuối cùng `v2.0.0-final`.*
