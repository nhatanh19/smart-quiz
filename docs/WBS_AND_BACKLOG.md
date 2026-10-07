# 🗂️ WORK BREAKDOWN STRUCTURE (WBS) & PRODUCT BACKLOG — SMART QUIZ
**Tên dự án:** Nền tảng Kiểm tra và Ôn luyện Trắc nghiệm Trực tuyến Tích hợp Trí tuệ Nhân tạo (*AI-Powered Online Assessment Platform*)  
**Mã dự án / Repository:** `smart-quiz` ([github.com/nhatanh19/smart-quiz](https://github.com/nhatanh19/smart-quiz))  
**Môn học:** Quản trị Dự án Phần mềm | **Tài liệu chuẩn:** Week 03 — Scope, Requirements & WBS  
**Nguyên tắc thiết kế WBS:** Tuân thủ **Quy tắc 100% (*100% Rule*)**, **Định hướng Sản phẩm bàn giao (*Deliverable-oriented*)**, và quy mô gói công việc **1–2 tuần/Work Package** cân bằng cho 4 thành viên Full-stack (25% khối lượng code/người).

---

# 1. Work Breakdown Structure (WBS Tree)

Sơ đồ cây phân rã công việc (WBS) dưới đây chia toàn bộ phạm vi dự án **Smart Quiz** thành **6 Mô-đun chính (Mức 1)**, **15 Gói công việc — Work Packages (Mức 2)** và các **Thành phần bàn giao cụ thể (Mức 3)**:

```text
0.0 SMART QUIZ — AI-POWERED ONLINE ASSESSMENT PLATFORM
│
├── 1.0 System Architecture, Auth & User Management (Kiến trúc Hạ tầng, Xác thực & Phân quyền)
│   ├── 1.1 Project Boilerplate, Database Schema & Migration Setup
│   │   ├── 1.1.1 Khung mã nguồn Full-stack (Frontend/Backend Boilerplate) & Quy chuẩn Git/Linter
│   │   └── 1.1.2 Sơ đồ CSDL quan hệ tổng thể (ERD), cấu hình ORM & kịch bản Migration/Seed Data
│   └── 1.2 Authentication & Role-Based Access Control (RBAC)
│       ├── 1.2.1 Dịch vụ Đăng ký, Đăng nhập (JWT/Session), Khôi phục mật khẩu & Bảo vệ Route
│       └── 1.2.2 Quản lý Hồ sơ người dùng & Phân quyền 3 vai trò (Giảng viên, Sinh viên, Admin)
│
├── 2.0 Automated Document Parser & Question Bank (Bộ Phân tích Tài liệu & Ngân hàng Câu hỏi)
│   ├── 2.1 Multi-format Document Parser Engine (PDF / DOCX / TXT)
│   │   ├── 2.1.1 Dịch vụ đọc luồng tệp tải lên & bóc tách văn bản thô từ PDF, DOCX, TXT
│   │   └── 2.1.2 Bộ máy biểu thức chính quy (Regex Parser) nhận diện câu hỏi, lựa chọn và đáp án đúng
│   └── 2.2 Question Extraction Preview & Question Bank CRUD
│       ├── 2.2.1 Giao diện duyệt trước (Preview UI) & chỉnh sửa trực tiếp câu hỏi vừa bóc tách
│       └── 2.2.2 Mô-đun CRUD Ngân hàng câu hỏi, phân loại theo học phần, chủ đề và mức độ khó
│
├── 3.0 AI Quiz Generator & Matrix Engine (Sinh Đề thi Thông minh bằng AI theo Ma trận)
│   ├── 3.1 LLM Integration Service & JSON Schema Validator
│   │   ├── 3.1.1 Adapter kết nối Google Gemini / OpenAI API, quản lý API Key, Retry & Rate-limit
│   │   └── 3.1.2 Bộ kiểm tra và ép kiểu dữ liệu đầu ra chuẩn hóa (Strict JSON Schema Validator)
│   ├── 3.2 Prompt Engineering & Exam Matrix Builder UI
│   │   ├── 3.2.1 Bộ Prompt mẫu phân tầng nhận thức Bloom (Nhận biết, Thông hiểu, Vận dụng) & đa dạng câu hỏi (Chọn 1, Chọn nhiều, Đúng/Sai)
│   │   └── 3.2.2 Giao diện cấu hình Ma trận đề thi thông minh & duyệt câu hỏi do AI sinh ra
│   └── 3.3 Context-based Document AI Generation (RAG / File Context Quiz)
│       ├── 3.3.1 Bộ xử lý chia nhỏ văn bản học liệu (Text Chunking) làm ngữ cảnh đầu vào cho LLM
│       └── 3.3.2 Luồng sinh bộ câu hỏi trắc nghiệm bám sát nội dung tệp giáo trình/bài giảng tải lên
│
├── 4.0 Online Exam Engine & Anti-Cheating System (Hệ thống Tổ chức Thi & Giám sát Chống gian lận)
│   ├── 4.1 Exam Configuration & Dynamic Shuffling Engine
│   │   ├── 4.1.1 Mô-đun tạo ca thi, thiết lập thời gian đóng/mở, thời lượng, mật khẩu & giới hạn lượt thi
│   │   └── 4.1.2 Thuật toán trộn ngẫu nhiên thứ tự câu hỏi và đảo vị trí đáp án theo từng thí sinh
│   ├── 4.2 Focused Exam Interface & LocalStorage Fault-Tolerance
│   │   ├── 4.2.1 Giao diện phòng thi tập trung, bảng điều hướng câu hỏi, đồng hồ đếm ngược & tự động thu bài
│   │   └── 4.2.2 Cơ chế đồng bộ trạng thái bài làm tạm thời vào LocalStorage/Cache chống mất dữ liệu khi rớt mạng
│   └── 4.3 Client-side Anti-Cheating Monitor
│       ├── 4.3.1 Trình lắng nghe sự kiện trình duyệt (Page Visibility API, Window Blur/Focus, chặn Copy/Paste)
│       └── 4.3.2 Hệ thống cảnh báo vi phạm theo thời gian thực, ghi nhật ký (Audit Log) & tự động khóa/thu bài khi vượt ngưỡng
│
├── 5.0 Auto-Grading, AI Tutor & Analytics Dashboard (Chấm điểm, Gia sư Ảo & Phân tích Hiệu suất)
│   ├── 5.1 Auto-Grading Engine & Exam Review Mode
│   │   ├── 5.1.1 Bộ chấm điểm tự động tức thì cho các dạng câu hỏi (Chọn 1, Chọn nhiều, Đúng/Sai)
│   │   └── 5.1.2 Giao diện xem lại bài thi chi tiết (Review Mode) đối chiếu đáp án người dùng và đáp án chuẩn
│   ├── 5.2 Contextual AI Tutor & Knowledge Gap Recommender
│   │   ├── 5.2.1 Dịch vụ Gia sư ảo (AI Tutor) giải thích chi tiết ngữ cảnh vì sao từng phương án đúng hoặc sai
│   │   └── 5.2.2 Mô-đun phân tích nguyên nhân chọn sai, phát hiện lỗ hổng kiến thức & gợi ý chủ đề cần ôn luyện lại
│   └── 5.3 Learning Analytics & Score Distribution Dashboard
│       ├── 5.3.1 Bảng điều khiển cá nhân cho Sinh viên: Biểu đồ tiến độ điểm số và tỷ lệ đúng/sai theo chuyên đề
│       └── 5.3.2 Bảng điều khiển cho Giảng viên: Biểu đồ phổ điểm lớp học, thống kê câu hỏi khó/hay sai và xuất báo cáo
│
└── 6.0 Quality Assurance, Deployment & Project Closure (Kiểm thử, Triển khai & Đóng Dự án)
    ├── 6.1 End-to-End Integration Testing & CI/CD Cloud Deployment
    │   ├── 6.1.1 Kịch bản kiểm thử tích hợp luồng nghiệp vụ khép kín (End-to-End Test Suite) & xử lý lỗi
    │   └── 6.1.2 Thiết lập CI/CD Pipeline và triển khai bản Production lên Cloud Free-tier (Vercel/Render/Supabase)
    └── 6.2 Project Management Documentation, User Manual & Final Release
        ├── 6.2.1 Hồ sơ Quản trị Dự án trọn bộ (Charter, WBS, Sprint Boards, Risk Register, Retrospectives)
        └── 6.2.2 Tài liệu hướng dẫn sử dụng (User Manual), kịch bản Live Demo & gói bàn giao cuối kỳ (Tuần 13)
```

---

# 2. MoSCoW Prioritization & Minimum Viable Scope (MVS)

Để đảm bảo dự án về đích đúng hạn vào **Tuần 13** với ngân sách **0 USD** và đội ngũ **4 thành viên**, toàn bộ các gói công việc (Work Packages) trong WBS được phân loại ưu tiên theo phương pháp **MoSCoW** như sau:

### 🔴 Must-Have (Minimum Viable Scope — MVS / Phạm vi Tối thiểu Cam kết)
Đây là các gói công việc **BẮT BUỘC** phải hoàn thành 100% để tạo nên một hệ thống chạy được thực tế (**Runnable Deliverable**) phục vụ luồng nghiệp vụ cốt lõi từ đầu đến cuối:
- **`1.1` Project Boilerplate, Database Schema & Migration Setup:** Khung kiến trúc Full-stack và cơ sở dữ liệu nền tảng.
- **`1.2` Authentication & Role-Based Access Control (RBAC):** Đăng nhập/Đăng ký JWT và phân quyền Giảng viên, Sinh viên, Admin.
- **`2.1` Multi-format Document Parser Engine (PDF/DOCX/TXT):** Bóc tách tự động câu hỏi, phương án và đáp án từ tệp tài liệu bằng thuật toán & Regex.
- **`2.2` Question Extraction Preview & Question Bank CRUD:** Duyệt trước, chỉnh sửa câu hỏi vừa bóc tách và quản lý ngân hàng câu hỏi.
- **`3.1` LLM Integration Service & JSON Schema Validator:** Kết nối API mô hình ngôn ngữ lớn (Gemini/OpenAI) và chuẩn hóa đầu ra theo cấu trúc JSON.
- **`3.2` Prompt Engineering & Exam Matrix Builder UI:** Sinh đề thi tự động bằng AI theo chủ đề và ma trận 3 mức độ khó (*Nhận biết, Thông hiểu, Vận dụng*).
- **`4.1` Exam Configuration & Dynamic Shuffling Engine:** Tạo phòng thi, cài đặt thời gian và trộn ngẫu nhiên câu hỏi/đáp án cho từng thí sinh.
- **`4.2` Focused Exam Interface & LocalStorage Fault-Tolerance:** Giao diện làm bài đếm ngược, tự động thu bài và lưu tạm vào `localStorage` chống mất bài khi sự cố mạng.
- **`4.3` Client-side Anti-Cheating Monitor:** Phát hiện hành vi chuyển tab/rời cửa sổ làm bài, cảnh báo và tự động khóa/nộp bài khi vượt ngưỡng vi phạm.
- **`5.1` Auto-Grading Engine & Exam Review Mode:** Chấm điểm tự động ngay sau khi nộp bài và cho phép xem lại chi tiết kết quả làm bài.
- **`6.1` End-to-End Integration Testing & CI/CD Cloud Deployment:** Tích hợp hoàn chỉnh 4 mô-đun và triển khai sản phẩm thực tế lên môi trường Cloud.

### 🟡 Should-Have (Tính năng Quan trọng Gia tăng Giá trị Cốt lõi)
Các gói công việc mang lại chiều sâu thông minh cho hệ thống, được lên kế hoạch thực hiện trong **Sprint 2 (Tuần 8–12)** ngay sau khi hoàn tất khung MVS:
- **`3.3` Context-based Document AI Generation:** Sinh câu hỏi trắc nghiệm bằng AI dựa trực tiếp trên nội dung tệp giáo trình/tài liệu bài giảng do giảng viên tải lên.
- **`5.2` Contextual AI Tutor & Knowledge Gap Recommender:** Gia sư ảo giải thích chi tiết ngữ cảnh đúng/sai cho từng phương án lựa chọn ở chế độ Review Mode và đề xuất chủ đề cần ôn tập lại.
- **`5.3` Learning Analytics & Score Distribution Dashboard:** Biểu đồ trực quan hóa tiến độ học tập cá nhân theo chuyên đề và báo cáo phổ điểm lớp học cho giảng viên.
- **`6.2` Project Management Documentation, User Manual & Final Release:** Hoàn thiện bộ tài liệu quản trị dự án, hướng dẫn sử dụng và slide báo cáo tổng kết.

### 🟢 Could-Have (Tính năng Điểm thưởng / Mở rộng nếu dư thời gian)
Các tính năng bổ trợ trải nghiệm, chỉ thực hiện nếu nhóm hoàn thành sớm toàn bộ *Must-Have* và *Should-Have* trước Tuần 11:
- **Realtime Quiz Arena (Đấu trường trắc nghiệm trực tiếp):** Phòng thi đua top bảng xếp hạng theo thời gian thực qua WebSocket (tương tự Kahoot/Quizizz).
- **Export Exam & Report (Xuất tệp in ấn):** Xuất đề thi trắc nghiệm ra tệp Word/PDF chuẩn định dạng in ấn và xuất bảng điểm lớp học ra tệp Excel/CSV.
- **AI Flashcards Practice:** Tự động chuyển đổi các câu hỏi sinh viên làm sai thành bộ thẻ ghi nhớ (*Flashcards*) để ôn tập nhanh.

### ⚪ Won't-Have (This Semester — Tuyên bố KHÔNG làm để chống Scope Creep)
Các tính năng chính thức loại trừ khỏi phạm vi học kỳ này:
- **Chấm điểm tự luận mở hoặc chấm code tự động bằng AI** (*AI Open-ended Essay Grading / Online Code Judge*).
- **Giám sát thi qua Webcam & Microphone** (*AI Facial Recognition / Video Proctoring / Eye-tracking*).
- **Ứng dụng di động gốc** (*Native Mobile App* trên iOS/Android).
- **Cổng thanh toán trực tuyến & Tích hợp LMS** (Không tích hợp VNPay/Stripe, không tích hợp chuẩn LTI/SSO vào Moodle hay Canvas của trường).

---

# 3. GitHub Issues & Product Backlog Mapping (Bảng quy đổi sang GitHub)

Bảng dưới đây ánh xạ **100% các gói công việc trong WBS (15 Work Packages)** thành danh sách **15 GitHub Issues** cụ thể trong Product Backlog, phân bổ đều cho 4 thành viên Full-stack (`Dev 1` đến `Dev 4`) theo đúng chuyên môn mô-đun:

- **Dev 1 (Team Leader / Scrum Master):** Phụ trách Hạ tầng Monorepo, CSDL ERD & Bộ bóc tách tài liệu (*File Parser Engine & Preview UI*).
- **Dev 2 (AI Integration Engineer):** Phụ trách Tích hợp LLM API, Prompt Engineering ma trận, RAG Document Quiz & Ngân hàng câu hỏi (*Question Bank*).
- **Dev 3 (Core Engine Engineer):** Phụ trách Xác thực người dùng (*Auth JWT/RBAC*) & Phòng thi trực tuyến, Xáo trộn đề & Chống gian lận (*Exam Engine & Anti-cheat*).
- **Dev 4 (Data & Tutor Engineer):** Phụ trách Bộ chấm điểm (*Auto-Grading*), Chế độ xem lại (*Review Mode*), Gia sư ảo (*AI Tutor*) & Bảng điều khiển phân tích (*Analytics Dashboard*).

| Issue ID | Work Package Title | Mô tả sản phẩm bàn giao (Deliverable) | MoSCoW Label | Estimated Effort (1-2 weeks) | Assignee Suggestion |
| :---: | :--- | :--- | :---: | :---: | :---: |
| **#1** | `[Infra] Project Boilerplate & Database Schema Setup (WBS 1.1)` | Khung mã nguồn Full-stack (Frontend/Backend), cấu hình Git/ESLint, sơ đồ CSDL tổng thể (ERD) và kịch bản Migration/Seed data chạy thành công. | `must-have` | 1 tuần | **Dev 1** |
| **#2** | `[Auth] Authentication & Role-Based Access Control (WBS 1.2)` | API & Giao diện Đăng nhập/Đăng ký bằng JWT, bảo vệ route (Middleware) và quản lý phân quyền 3 vai trò: Giảng viên, Sinh viên, Admin. | `must-have` | 1 tuần | **Dev 3** *(San sẻ Auth)* |
| **#3** | `[Parser] Multi-format Document Parser Engine PDF/DOCX/TXT (WBS 2.1)` | Dịch vụ Backend đọc tệp `PDF`, `DOCX`, `TXT` và bộ thuật toán Regex tự động bóc tách danh sách câu hỏi, các phương án lựa chọn và đáp án đúng. | `must-have` | 2 tuần | **Dev 1** |
| **#4** | `[Parser] Question Extraction Preview & Question Bank CRUD (WBS 2.2)` | Giao diện tải tệp, màn hình duyệt trước (Preview) cho phép sửa/xóa câu hỏi vừa trích xuất và bộ API/UI quản lý CRUD ngân hàng câu hỏi theo chủ đề. | `must-have` | 1.5 tuần | **Dev 1 & Dev 2** |
| **#5** | `[AI-Gen] LLM Integration Service & JSON Schema Validator (WBS 3.1)` | Dịch vụ kết nối Google Gemini / OpenAI API có xử lý Rate-limit/Timeout và bộ kiểm tra ép kiểu đầu ra tuân thủ 100% chuẩn `JSON Schema`. | `must-have` | 1.5 tuần | **Dev 2** |
| **#6** | `[AI-Gen] Prompt Engineering & Exam Matrix Builder UI (WBS 3.2)` | Bộ Prompt sinh câu hỏi theo 3 mức độ nhận thức (Nhận biết, Thông hiểu, Vận dụng), hỗ trợ câu hỏi Chọn 1/Chọn nhiều/Đúng-Sai cùng giao diện cấu hình ma trận đề. | `must-have` | 2 tuần | **Dev 2** |
| **#7** | `[AI-Gen] Context-based Document AI Quiz Generation (WBS 3.3)` | Tính năng trích xuất ngữ cảnh từ tệp giáo trình/bài giảng tải lên để yêu cầu AI sinh bộ câu hỏi trắc nghiệm bám sát nội dung tài liệu. | `should-have` | 1.5 tuần | **Dev 2** |
| **#8** | `[Exam] Exam Configuration & Dynamic Shuffling Engine (WBS 4.1)` | Mô-đun tạo kỳ thi (cài đặt thời gian đóng/mở, thời lượng, mật khẩu, số lượt làm) và thuật toán trộn ngẫu nhiên câu hỏi/đáp án riêng biệt cho từng thí sinh. | `must-have` | 1.5 tuần | **Dev 3** |
| **#9** | `[Exam] Focused Exam Interface & LocalStorage Recovery (WBS 4.2)` | Giao diện phòng thi trực tuyến tập trung, đồng hồ đếm ngược, tự động nộp bài khi hết giờ và cơ chế lưu tạm `localStorage` tự khôi phục bài làm khi rớt mạng. | `must-have` | 2 tuần | **Dev 3** |
| **#10** | `[Anti-Cheat] Client-side Anti-Cheating Monitor & Auto-Lock (WBS 4.3)` | Cơ chế giám sát trình duyệt bắt sự kiện chuyển tab (`visibilitychange`), rời cửa sổ (`blur`), hiển thị cảnh báo vi phạm, lưu log và tự động khóa/thu bài khi vượt ngưỡng. | `must-have` | 1.5 tuần | **Dev 3** |
| **#11** | `[Grading] Auto-Grading Engine & Detailed Exam Review Mode (WBS 5.1)` | Bộ chấm điểm tự động tức thì cho mọi loại câu hỏi trắc nghiệm, tính toán độ chính xác và giao diện xem lại bài thi (Review Mode) đối chiếu đáp án sau khi nộp. | `must-have` | 1.5 tuần | **Dev 4** |
| **#12** | `[AI-Tutor] Contextual AI Tutor & Knowledge Gap Recommender (WBS 5.2)` | Tích hợp Gia sư ảo (AI Tutor) giải thích chi tiết ngữ cảnh vì sao từng phương án đúng/sai ngay trong màn hình Review Mode và gợi ý các chủ đề cần ôn tập củng cố. | `should-have` | 2 tuần | **Dev 4** |
| **#13** | `[Analytics] Learning Analytics & Score Distribution Dashboard (WBS 5.3)` | Bảng điều khiển thống kê biểu đồ tiến độ học tập, tỷ lệ đúng/sai theo chuyên đề cho Sinh viên và biểu đồ phổ điểm tổng quan lớp học cho Giảng viên. | `should-have` | 1.5 tuần | **Dev 4** |
| **#14** | `[DevOps] End-to-End Integration Testing & Cloud Deployment (WBS 6.1)` | Kiểm thử tích hợp toàn bộ luồng nghiệp vụ End-to-End giữa 4 mô-đun, thiết lập CI/CD và triển khai bản Runnable Deliverable lên Cloud Free-tier (Vercel/Render). | `must-have` | 1 tuần | **Dev 1, Dev 2, Dev 3, Dev 4** |
| **#15** | `[Docs] Project Management Artifacts, User Manual & Final Release (WBS 6.2)` | Hoàn thiện hồ sơ quản trị dự án (Charter, WBS, Risk Register, Retrospectives), tài liệu hướng dẫn sử dụng (`README.md`) và kịch bản bảo vệ đồ án Tuần 13. | `should-have` | 1 tuần | **Dev 1, Dev 2, Dev 3, Dev 4** |

---

# 4. Phụ lục: Gợi ý Câu lệnh GitHub CLI (Tự động hóa khởi tạo Backlog)

Nhóm phát triển có thể cài đặt [GitHub CLI (`gh`)](https://cli.github.com/), đăng nhập bằng `gh auth login` và chạy trực tiếp đoạn script dưới đây trong Terminal tại thư mục gốc của dự án để tự động khởi tạo hệ thống nhãn (**Labels**) và toàn bộ **15 GitHub Issues** lên repository `nhatanh19/smart-quiz`:

```bash
# ==============================================================================
# BƯỚC 1: Tạo các nhãn phân loại ưu tiên (MoSCoW Labels) và nhãn Mô-đun
# ==============================================================================
gh label create "must-have" --color "D73A4A" --description "Minimum Viable Scope (MVS) - Bắt buộc hoàn thành" --force
gh label create "should-have" --color "FBCA04" --description "Tính năng quan trọng gia tăng giá trị AI & Analytics" --force
gh label create "could-have" --color "0E8A16" --description "Tính năng mở rộng nếu còn dư thời gian" --force
gh label create "module:parser" --color "1D76DB" --description "Module 1: System Admin & File Parser" --force
gh label create "module:ai-gen" --color "5319E7" --description "Module 2: AI Quiz Generator" --force
gh label create "module:exam" --color "E99695" --description "Module 3: Exam Engine & Anti-cheat" --force
gh label create "module:tutor-analytics" --color "006B75" --description "Module 4: AI Tutor & Analytics Dashboard" --force

# ==============================================================================
# BƯỚC 2: Tự động tạo 15 Issues bao quát 100% WBS lên GitHub Repository
# ==============================================================================

# Issue #1 - WBS 1.1
gh issue create \
  --title "[Infra] Project Boilerplate & Database Schema Setup (WBS 1.1)" \
  --body "### Deliverable (Sản phẩm bàn giao)\n- Khung mã nguồn Full-stack (Frontend/Backend), cấu hình Git/Linter.\n- Sơ đồ CSDL tổng thể (ERD), cấu hình ORM và kịch bản Migration/Seed data.\n\n**Estimated Effort:** 1 tuần\n**Suggested Assignee:** Dev 1 (Team Leader)" \
  --label "must-have,module:parser"

# Issue #2 - WBS 1.2
gh issue create \
  --title "[Auth] Authentication & Role-Based Access Control (WBS 1.2)" \
  --body "### Deliverable (Sản phẩm bàn giao)\n- API & Giao diện Đăng nhập/Đăng ký sử dụng JWT.\n- Middleware phân quyền 3 vai trò: Giảng viên (Instructor), Sinh viên (Student), Quản trị viên (Admin).\n\n**Estimated Effort:** 1 tuần\n**Suggested Assignee:** Dev 1" \
  --label "must-have,module:parser"

# Issue #3 - WBS 2.1
gh issue create \
  --title "[Parser] Multi-format Document Parser Engine PDF/DOCX/TXT (WBS 2.1)" \
  --body "### Deliverable (Sản phẩm bàn giao)\n- Dịch vụ Backend bóc tách văn bản thô từ tệp PDF, DOCX, TXT.\n- Thuật toán và biểu thức chính quy (Regex) tự động nhận diện câu hỏi, các lựa chọn đáp án và đáp án đúng.\n\n**Estimated Effort:** 2 tuần\n**Suggested Assignee:** Dev 1" \
  --label "must-have,module:parser"

# Issue #4 - WBS 2.2
gh issue create \
  --title "[Parser] Question Extraction Preview & Question Bank CRUD (WBS 2.2)" \
  --body "### Deliverable (Sản phẩm bàn giao)\n- Giao diện tải tài liệu, màn hình duyệt trước (Preview) và chỉnh sửa câu hỏi vừa bóc tách trước khi lưu.\n- Bộ API & UI quản lý CRUD ngân hàng câu hỏi theo môn học, chủ đề và độ khó.\n\n**Estimated Effort:** 1.5 tuần\n**Suggested Assignee:** Dev 1" \
  --label "must-have,module:parser"

# Issue #5 - WBS 3.1
gh issue create \
  --title "[AI-Gen] LLM Integration Service & JSON Schema Validator (WBS 3.1)" \
  --body "### Deliverable (Sản phẩm bàn giao)\n- Dịch vụ kết nối Google Gemini / OpenAI API, quản lý API Key, Timeout và Rate-limit.\n- Bộ kiểm soát định dạng dữ liệu đầu ra từ AI thành cấu trúc chuẩn (JSON Schema) phục vụ lưu trữ.\n\n**Estimated Effort:** 1.5 tuần\n**Suggested Assignee:** Dev 2" \
  --label "must-have,module:ai-gen"

# Issue #6 - WBS 3.2
gh issue create \
  --title "[AI-Gen] Prompt Engineering & Exam Matrix Builder UI (WBS 3.2)" \
  --body "### Deliverable (Sản phẩm bàn giao)\n- Logic Prompt Engineering yêu cầu AI sinh câu hỏi bám sát ma trận kiến thức, phân loại độ khó (Nhận biết, Thông hiểu, Vận dụng) và đa dạng hình thức (Chọn 1, Chọn nhiều, Đúng/Sai).\n- Giao diện thiết lập cấu hình ma trận đề thi và duyệt câu hỏi AI sinh ra.\n\n**Estimated Effort:** 2 tuần\n**Suggested Assignee:** Dev 2" \
  --label "must-have,module:ai-gen"

# Issue #7 - WBS 3.3
gh issue create \
  --title "[AI-Gen] Context-based Document AI Quiz Generation (WBS 3.3)" \
  --body "### Deliverable (Sản phẩm bàn giao)\n- Bộ chia nhỏ văn bản (Text Chunking) trích xuất ngữ cảnh từ tệp giáo trình/bài giảng tải lên.\n- Luồng API sinh đề thi tự động bằng AI bám sát nội dung tài liệu được cung cấp.\n\n**Estimated Effort:** 1.5 tuần\n**Suggested Assignee:** Dev 2" \
  --label "should-have,module:ai-gen"

# Issue #8 - WBS 4.1
gh issue create \
  --title "[Exam] Exam Configuration & Dynamic Shuffling Engine (WBS 4.1)" \
  --body "### Deliverable (Sản phẩm bàn giao)\n- Mô-đun thiết lập phòng thi (thời gian đóng/mở, thời lượng làm bài, mật khẩu, giới hạn số lần thi).\n- Thuật toán xáo trộn ngẫu nhiên thứ tự câu hỏi và phương án lựa chọn theo từng thí sinh.\n\n**Estimated Effort:** 1.5 tuần\n**Suggested Assignee:** Dev 3" \
  --label "must-have,module:exam"

# Issue #9 - WBS 4.2
gh issue create \
  --title "[Exam] Focused Exam Interface & LocalStorage Recovery (WBS 4.2)" \
  --body "### Deliverable (Sản phẩm bàn giao)\n- Giao diện làm bài thi trực tuyến tập trung, đồng hồ đếm ngược và cơ chế tự động thu bài khi hết hạn.\n- Cơ chế lưu trạng thái làm bài tạm thời vào localStorage/cache để tránh mất dữ liệu khi gặp sự cố mạng.\n\n**Estimated Effort:** 2 tuần\n**Suggested Assignee:** Dev 3" \
  --label "must-have,module:exam"

# Issue #10 - WBS 4.3
gh issue create \
  --title "[Anti-Cheat] Client-side Anti-Cheating Monitor & Auto-Lock (WBS 4.3)" \
  --body "### Deliverable (Sản phẩm bàn giao)\n- Cơ chế giám sát phía trình duyệt (client-side): bắt sự kiện chuyển tab (visibilitychange), rời cửa sổ làm bài (blur).\n- Hiển thị cảnh báo vi phạm, ghi log và tự động khóa/nộp bài nếu tái phạm vượt ngưỡng quy định.\n\n**Estimated Effort:** 1.5 tuần\n**Suggested Assignee:** Dev 3" \
  --label "must-have,module:exam"

# Issue #11 - WBS 5.1
gh issue create \
  --title "[Grading] Auto-Grading Engine & Detailed Exam Review Mode (WBS 5.1)" \
  --body "### Deliverable (Sản phẩm bàn giao)\n- Logic chấm điểm tự động tức thì cho các dạng câu hỏi trắc nghiệm và tính toán độ chính xác.\n- Giao diện xem lại bài thi chi tiết (Review Mode) sau khi học viên nộp bài.\n\n**Estimated Effort:** 1.5 tuần\n**Suggested Assignee:** Dev 4" \
  --label "must-have,module:tutor-analytics"

# Issue #12 - WBS 5.2
gh issue create \
  --title "[AI-Tutor] Contextual AI Tutor & Knowledge Gap Recommender (WBS 5.2)" \
  --body "### Deliverable (Sản phẩm bàn giao)\n- Luồng gọi AI Tutor phân tích ngữ cảnh, giải thích chi tiết lý do từng phương án đúng/sai ngay trong Review Mode.\n- Phân tích nguyên nhân học viên chọn sai và gợi ý chủ đề/lộ trình cần ôn tập củng cố.\n\n**Estimated Effort:** 2 tuần\n**Suggested Assignee:** Dev 4" \
  --label "should-have,module:tutor-analytics"

# Issue #13 - WBS 5.3
gh issue create \
  --title "[Analytics] Learning Analytics & Score Distribution Dashboard (WBS 5.3)" \
  --body "### Deliverable (Sản phẩm bàn giao)\n- Các truy vấn thống kê tỷ lệ đúng/sai theo từng chuyên đề kiến thức.\n- Biểu đồ trực quan hóa tiến độ học tập cá nhân cho học viên và báo cáo phổ điểm tổng quan cho giảng viên.\n\n**Estimated Effort:** 1.5 tuần\n**Suggested Assignee:** Dev 4" \
  --label "should-have,module:tutor-analytics"

# Issue #14 - WBS 6.1
gh issue create \
  --title "[DevOps] End-to-End Integration Testing & Cloud Deployment (WBS 6.1)" \
  --body "### Deliverable (Sản phẩm bàn giao)\n- Kiểm thử tích hợp End-to-End toàn bộ 4 mô-đun.\n- Thiết lập CI/CD Pipeline và triển khai bản Runnable Deliverable lên Cloud Free-tier (Vercel/Render/Supabase).\n\n**Estimated Effort:** 1 tuần\n**Suggested Assignee:** Cả nhóm (Dev 1, Dev 2, Dev 3, Dev 4)" \
  --label "must-have"

# Issue #15 - WBS 6.2
gh issue create \
  --title "[Docs] Project Management Artifacts, User Manual & Final Release (WBS 6.2)" \
  --body "### Deliverable (Sản phẩm bàn giao)\n- Hồ sơ quản trị dự án đầy đủ qua các tuần (Project Charter, WBS, Risk Register, Sprint Retrospectives).\n- Tài liệu hướng dẫn sử dụng (User Manual) và kịch bản trình diễn (Live Demo) nghiệm thu Tuần 13.\n\n**Estimated Effort:** 1 tuần\n**Suggested Assignee:** Cả nhóm (Dev 1, Dev 2, Dev 3, Dev 4)" \
  --label "should-have"
```
