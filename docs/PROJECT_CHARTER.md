# 📋 PROJECT CHARTER — SMART QUIZ

**Tên dự án:** Nền tảng Kiểm tra và Ôn luyện Trắc nghiệm Trực tuyến Tích hợp Trí tuệ Nhân tạo (*AI-Powered Online Assessment Platform*)  
**Mã dự án / Repository:** `smart-quiz` ([github.com/nhatanh19/smart-quiz](https://github.com/nhatanh19/smart-quiz))  
**Môn học:** Quản trị Dự án Phần mềm  
**Ngày ban hành:** 28/09/2026 | **Phiên bản:** 1.0 (Baseline)

---

# 1. Project Purpose (Mục đích Dự án)

Dự án **Smart Quiz** ra đời nhằm giải quyết triệt để bài toán tiêu tốn thời gian trong quy trình biên soạn, nhập liệu đề thi thủ công của giảng viên và sự thiếu hụt phản hồi chuyên sâu trong quá trình tự ôn luyện của sinh viên trên các hệ thống trắc nghiệm truyền thống. Bằng cách kết hợp công nghệ bóc tách tài liệu tự động (*File Parser*) với các mô hình ngôn ngữ lớn (*LLM/GenAI*), hệ thống tự động hóa toàn diện khâu chuyển đổi học liệu (`PDF`, `DOCX`, `TXT`) thành ngân hàng câu hỏi chuẩn hóa và sinh đề thi thông minh bám sát ma trận nhận thức. Đồng thời, nền tảng cung cấp môi trường thi trực tuyến công bằng với cơ chế giám sát chống gian lận phía trình duyệt và tích hợp Gia sư ảo (*AI Tutor*) giúp giải thích ngữ cảnh từng đáp án ngay sau khi nộp bài, chỉ ra lỗ hổng kiến thức và tối ưu hóa lộ trình tự học cá nhân hóa cho từng học viên.

---

# 2. Project Objectives (Mục tiêu Dự án)

Dự án thiết lập các mục tiêu cụ thể theo tiêu chuẩn **SMART** (*Specific, Measurable, Achievable, Relevant, Time-bound*):

- **Tối ưu hóa hiệu suất biên soạn đề (Specific & Measurable):** Giảm tối thiểu **80% thời gian nhập liệu và tạo đề trắc nghiệm** cho giảng viên thông qua công cụ bóc tách tự động từ tệp `PDF`, `DOCX`, `TXT` (đạt độ chính xác nhận diện cấu trúc câu hỏi $\ge$ **90%**) và công cụ AI sinh câu hỏi tự động theo ma trận 3 mức độ nhận thức (*Nhận biết, Thông hiểu, Vận dụng*) với **100%** dữ liệu đầu ra tuân thủ chuẩn `JSON Schema`.
- **Đảm bảo hiệu năng & Trải nghiệm thời gian thực (Achievable & Measurable):** Hỗ trợ tối thiểu **50–100 sinh viên tham gia thi và ôn luyện đồng thời** với độ trễ xử lý thao tác làm bài/chấm điểm trung bình **< 1.5 giây**, thời gian phản hồi giải thích ngữ cảnh của *AI Tutor* **< 3 giây**, và tự động khôi phục **100%** trạng thái bài làm từ bộ nhớ đệm (`localStorage`) khi xảy ra sự cố gián đoạn mạng.
- **Chuẩn hóa quy trình thi & Phân tích dữ liệu (Relevant):** Phát hiện và ghi nhận tức thì (**< 500ms**) các hành vi chuyển tab hoặc rời khỏi cửa sổ làm bài để cảnh báo/khóa bài tự động, đồng thời cung cấp báo cáo phổ điểm và thống kê tỷ lệ đúng/sai theo từng chuyên đề ngay sau khi kết thúc bài thi.
- **Cam kết tiến độ bàn giao (Time-bound):** Hoàn thiện **100% 4 mô-đun cốt lõi** với sự đóng góp mã nguồn đồng đều từ 4 thành viên (25% khối lượng code/thành viên) và bàn giao sản phẩm chạy được thực tế (**Runnable Deliverable**) trước **Tuần 13** của học kỳ.

---

# 3. High-level Scope (Phạm vi Tổng quan)

### ✅ In-Scope (Các tính năng thực hiện trong dự án)

1. **Mô-đun 1 — Quản trị hệ thống & Phân tích tài liệu tự động (*System Admin & File Parser*):**
   - Quản lý xác thực, phân quyền người dùng (Giảng viên, Sinh viên, Quản trị viên) và quản lý danh mục ngân hàng câu hỏi.
   - Bóc tách văn bản thô từ tệp `PDF`, `DOCX`, `TXT` bằng thuật toán kết hợp biểu thức chính quy (*Regex*) để tự động tách câu hỏi, các phương án lựa chọn và đáp án đúng.
   - Giao diện duyệt trước (*Preview*) và chỉnh sửa trực tiếp danh sách câu hỏi vừa trích xuất trước khi lưu vào cơ sở dữ liệu.
2. **Mô-đun 2 — Sinh đề thi thông minh bằng AI (*AI Quiz Generator*):**
   - Tích hợp LLM API với kỹ thuật *Prompt Engineering* để tự động sinh câu hỏi từ chủ đề chỉ định hoặc nội dung giáo trình tải lên.
   - Thiết lập cấu hình ma trận đề thi theo số lượng câu, phân bổ mức độ khó (*Nhận biết, Thông hiểu, Vận dụng*) và đa dạng loại câu hỏi (*Trắc nghiệm chọn 1 đáp án, chọn nhiều đáp án, Đúng/Sai*).
   - Kiểm soát và ép kiểu dữ liệu phản hồi từ AI về định dạng chuẩn `JSON Schema` trước khi lưu trữ.
3. **Mô-đun 3 — Tổ chức thi trực tuyến & Giám sát chống gian lận (*Exam Engine & Anti-cheat*):**
   - Thuật toán xáo trộn ngẫu nhiên thứ tự câu hỏi và các phương án lựa chọn cho từng thí sinh; hẹn giờ đếm ngược, giới hạn số lần làm bài và tự động thu bài khi hết giờ.
   - Cơ chế giám sát phía trình duyệt (*Client-side Anti-cheat*): Bắt sự kiện chuyển tab (`visibilitychange`), mất tiêu điểm cửa sổ (`window blur`), hiển thị cảnh báo vi phạm và tự động khóa/nộp bài khi vượt ngưỡng quy định (ví dụ: quá 3 lần vi phạm).
   - Cơ chế đồng bộ và lưu tạm trạng thái làm bài vào `localStorage` giúp bảo toàn dữ liệu khi mất kết nối mạng đột ngột.
4. **Mô-đun 4 — Gia sư ảo & Bảng điều khiển phân tích hiệu suất (*AI Tutor & Analytics Dashboard*):**
   - Chấm điểm tự động tức thì và chế độ xem lại bài thi chi tiết (*Review Mode*).
   - Tích hợp *AI Tutor* phân tích ngữ cảnh từng câu hỏi, giải thích lý do phương án đúng/sai, chỉ ra nguyên nhân nhầm lẫn của học viên và đề xuất các chủ đề kiến thức cần ôn tập bổ sung.
   - Thống kê tỷ lệ đúng/sai theo chuyên đề, trực quan hóa biểu đồ tiến độ học tập cá nhân cho sinh viên và báo cáo phổ điểm tổng quan cho giảng viên.

### ❌ Out-of-Scope (Các tính năng KHÔNG thực hiện trong học kỳ này để tránh Scope Creep)

- **Không** xây dựng tính năng AI chấm bài thi tự luận mở (*Open-ended Essay Grading*), chấm câu hỏi nói/viết ngoại ngữ hoặc biên dịch mã nguồn tự động (*Online Judge*).
- **Không** triển khai giám sát thi bằng nhận diện khuôn mặt/mắt qua Webcam (*AI Video Proctoring*) hoặc thu âm môi trường xung quanh thí sinh.
- **Không** phát triển ứng dụng di động gốc (*Native Mobile App* trên iOS/Android); hệ thống chỉ cung cấp giao diện web đáp ứng (*Responsive Web App*).
- **Không** tích hợp cổng thanh toán thương mại điện tử (*Payment Gateway*), gói thuê bao trả phí hoặc tích hợp chuẩn LTI/SSO trực tiếp vào hệ thống LMS hiện hành của nhà trường (Moodle, Canvas).

---

# 4. Stakeholder Identification & Power-Interest Grid (Các bên liên quan)

### 👥 Phân loại các bên liên quan (Stakeholder Classification)

- **Primary Stakeholders (Bên liên quan trực tiếp):**
  - **End-users (Người dùng cuối):** *Giảng viên/Giáo viên* (sử dụng File Parser, AI Quiz Generator, quản lý kỳ thi và xem phổ điểm) và *Sinh viên/Học viên* (làm bài thi trực tuyến, nhận giải thích từ AI Tutor và theo dõi tiến độ ôn luyện).
  - **Sponsor / Client:** *Giảng viên hướng dẫn môn Quản trị Dự án Phần mềm* (phê duyệt Project Charter, theo dõi tiến độ qua từng Sprint, đánh giá chất lượng quản trị và nghiệm thu sản phẩm).
  - **Development Team (Nhóm phát triển gồm 4 thành viên Full-stack — tỷ lệ đóng góp code 25%/người):**
    - *Thành viên 1 (Team Leader / Scrum Master & Full-stack Dev):* Phụ trách Kiến trúc hệ thống, Quản trị & Mô-đun *File Parser*.
    - *Thành viên 2 (AI Integration Engineer & Full-stack Dev):* Phụ trách Mô-đun *AI Quiz Generator* & tối ưu Prompt/JSON Schema.
    - *Thành viên 3 (Core Engine Engineer & Full-stack Dev):* Phụ trách Mô-đun *Exam Engine & Client-side Anti-cheat*.
    - *Thành viên 4 (Data & Tutor Engineer & Full-stack Dev):* Phụ trách Mô-đun *AI Tutor & Analytics Dashboard*.
- **Secondary Stakeholders (Bên liên quan gián tiếp):**
  - **Quản trị viên hệ thống (System Admin):** Quản lý tài khoản, cấu hình tham số hệ thống và giám sát hạn mức sử dụng (quota/rate-limit) của AI API.
  - **Đội ngũ Hạ tầng & Nhà cung cấp dịch vụ Cloud/API:** Các nền tảng lưu trữ đám mây (Vercel/Render/Supabase) và nhà cung cấp mô hình ngôn ngữ lớn (Google Gemini API / OpenAI API).
- **Hidden Stakeholders (Bên liên quan ẩn / Chịu ảnh hưởng từ quy trình mới):**
  - **Bộ phận Khảo thí & Đảm bảo chất lượng đào tạo:** Chịu tác động trực tiếp khi quy trình ra đề chuyển từ thủ công sang chuẩn hóa bằng ma trận AI và kiểm soát gian lận trực tuyến.
  - **Ban Chủ nhiệm Bộ môn / Khoa đào tạo:** Quan tâm đến tính bảo mật của ngân hàng đề thi số hóa và khả năng đánh giá đồng bộ năng lực chuẩn đầu ra của sinh viên giữa các lớp học phần.

### 📊 Ma trận Quyền lực – Mức độ quan tâm (Power-Interest Grid)

| Phân nhóm (Quadrant)                                                        | Nhóm đối tượng (Stakeholders)                                                                                                          | Mối quan tâm chính                                                                                                                          | Chiến lược quản lý (Engagement Strategy)                                                                                                     |
|:--------------------------------------------------------------------------- |:-------------------------------------------------------------------------------------------------------------------------------------- |:------------------------------------------------------------------------------------------------------------------------------------------- |:-------------------------------------------------------------------------------------------------------------------------------------------- |
| **High Power / High Interest**<br>*(Manage Closely — Quản lý chặt chẽ)*     | - Giảng viên hướng dẫn (Sponsor/Client)<br>- Nhóm phát triển (4 thành viên Full-stack)<br>- Giảng viên sử dụng chính (Key Instructors) | Tiến độ thực tế theo từng Sprint, tính đúng đắn của các mô-đun AI/Parser/Anti-cheat, chất lượng mã nguồn trên Git và sản phẩm chạy thực tế. | Báo cáo tiến độ hàng tuần, họp Sprint Review/Retrospective định kỳ, thống nhất ngay mọi thay đổi về phạm vi (Scope) và kiến trúc.            |
| **High Power / Low Interest**<br>*(Keep Satisfied — Đảm bảo hài lòng)*      | - Quản trị viên hệ thống / Hạ tầng IT<br>- Bộ phận Khảo thí & Quản lý đào tạo<br>- Nhà cung cấp dịch vụ LLM API / Cloud                | Tính ổn định, bảo mật dữ liệu đề thi, tuân thủ giới hạn tài nguyên (API Rate Limit, Cloud Free-tier) và quy chế khảo thí.                   | Tuân thủ nghiêm ngặt quy định bảo mật, cơ chế xử lý lỗi (fallback/retry) khi gọi API và cung cấp báo cáo tổng hợp khi cần thiết.             |
| **Low Power / High Interest**<br>*(Keep Informed — Thông tin thường xuyên)* | - Sinh viên / Học viên (End-users)<br>- Trợ giảng tham gia thử nghiệm (Beta Testers)                                                   | Giao diện làm bài mượt mà, không mất dữ liệu khi rớt mạng, chấm điểm chính xác và lời giải thích dễ hiểu từ *AI Tutor*.                     | Tổ chức chạy thử nghiệm (UAT) từ cuối Sprint 1, thu thập phản hồi về trải nghiệm người dùng (UI/UX) và thông báo các bản cập nhật tính năng. |
| **Low Power / Low Interest**<br>*(Monitor — Theo dõi định kỳ)*              | - Người dùng vãng lai trải nghiệm thử<br>- Cộng đồng mã nguồn mở / Thư viện bên thứ ba                                                 | Các tính năng giới thiệu chung và sự thay đổi phiên bản của các thư viện phụ thuộc (PDF/DOCX parser, Chart UI).                             | Theo dõi định kỳ các bản vá bảo mật của thư viện và duy trì tài liệu hướng dẫn sử dụng (`README.md`) rõ ràng.                                |

---

# 5. High-level Timeline & Milestones (Lịch trình tổng quan)

Lịch trình dự án kéo dài **13 tuần**, đồng bộ chặt chẽ với tiến độ môn Quản trị Dự án Phần mềm:

| Giai đoạn                                   | Thời gian       | Cột mốc chính (Key Milestones)                  | Sản phẩm bàn giao (Deliverables)                                                                                                                                            |
|:------------------------------------------- |:---------------:|:----------------------------------------------- |:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Phase 1: Initiation**                     | **Tuần 1 – 2**  | **Initiation & Project Charter**                | Phê duyệt `docs/PROJECT_CHARTER.md`, khởi tạo Git Repository (`smart-quiz`) và phân công 4 module Full-stack.                                                               |
| **Phase 2: Planning & Scope**               | **Tuần 3**      | **Scope, Requirements & WBS**                   | Tài liệu đặc tả yêu cầu (SRS/User Stories), cấu trúc phân rã công việc (WBS) chi tiết cho 4 mô-đun và thiết kế CSDL tổng thể.                                               |
| **Phase 3: Sprint 1 Setup**                 | **Tuần 4 – 5**  | **Estimation, Sprint 1 Planning & Board Setup** | Ước lượng nỗ lực (Story Points), thiết lập Kanban/Scrum Board, hoàn thành khung dự án (Boilerplate) và bắt đầu lập trình Sprint 1.                                          |
| **Phase 4: Sprint 1 Review & Risk/Quality** | **Tuần 6 – 7**  | **Risk/Quality Setup & Sprint 1 Retrospective** | Bản chạy thử Sprint 1 (*Module 1: File Parser* & *Module 2: AI Quiz Generator*), lập hồ sơ Rủi ro (Risk Register), tiêu chí chất lượng (DoD) và họp Sprint 1 Retrospective. |
| **Phase 5: Sprint 2 Execution**             | **Tuần 8 – 12** | **Sprint 2 Execution & Risk Monitoring**        | Phát triển và tích hợp *Module 3 (Exam Engine & Anti-cheat)* và *Module 4 (AI Tutor & Analytics Dashboard)*; kiểm thử tích hợp End-to-End và theo dõi/xử lý rủi ro.         |
| **Phase 6: Closure**                        | **Tuần 13**     | **Final Deliverable, Review & Closure**         | Triển khai bản **Runnable Deliverable** hoàn chỉnh lên môi trường Cloud, kiểm thử nghiệm thu, báo cáo tổng kết dự án và bảo vệ đồ án trước hội đồng/giảng viên.             |

---

# 6. Constraints & Assumptions (Ràng buộc & Giả định)

### 🔒 Constraints (Ràng buộc thực tế)

- **Thời gian (Schedule):** Cố định trong **13 tuần** của học kỳ; ngày bàn giao và bảo vệ cuối kỳ ở Tuần 13 là mốc cứng (Hard Deadline) không thể gia hạn.
- **Ngân sách (Budget):** **0 USD** — Dự án không có kinh phí thương mại; bắt buộc tận dụng 100% các gói miễn phí (*Free Tier / Freemium*) của các nhà cung cấp dịch vụ AI (như Google Gemini API Free Tier / OpenAI Trial) và công cụ phát triển mã nguồn mở.
- **Nguồn lực nhân sự (Team Size & Workload):** Nhóm gồm **4 thành viên** là sinh viên năm 4 kiêm nhiệm nhiều học phần khác; áp dụng nguyên tắc phân chia đồng đều (mỗi thành viên chịu trách nhiệm Full-stack từ Frontend, Backend, CSDL đến Unit Test cho 1 mô-đun tương ứng **25% khối lượng code**).
- **Hạ tầng kỹ thuật (Infrastructure):** Triển khai trên hạ tầng Cloud miễn phí (Vercel, Render/Railway, Supabase/MongoDB Atlas Free Tier), chịu giới hạn về băng thông, dung lượng lưu trữ tệp tải lên và giới hạn số lượng yêu cầu/phút (*Rate Limit / RPM*) của LLM API.

### 💡 Assumptions (Giả định)

- Các dịch vụ LLM API bên thứ ba hoạt động ổn định với thời gian khả dụng (*Uptime*) $\ge$ **99%** và tốc độ phản hồi trung bình **< 3 giây** đối với mỗi yêu cầu sinh câu hỏi hoặc giải thích đã được tối ưu hóa độ dài prompt.
- Các tệp tài liệu đầu vào (`PDF`, `DOCX`, `TXT`) do giảng viên tải lên là văn bản số hóa chuẩn (Unicode), không phải ảnh chụp hoặc bản quét (scan) mờ chưa qua xử lý nhận dạng ký tự quang học (OCR).
- Trình duyệt của sinh viên khi tham gia thi hỗ trợ đầy đủ các chuẩn Web API hiện đại (`Page Visibility API`, `Window Focus/Blur Events`, `localStorage`).
- Cả 4 thành viên cam kết dành tối thiểu **10–12 giờ/tuần** cho dự án, tuân thủ quy trình tạo nhánh (*Git Branching*), duyệt mã nguồn (*Pull Request Review*) và cập nhật trạng thái công việc đúng hạn trên bảng quản lý Sprint.

---

# 7. Success Criteria (Tiêu chí Thành công)

Dự án **Smart Quiz** được nghiệm thu và công nhận là **Thành công** khi đáp ứng đồng thời các tiêu chí định lượng sau:

1. **Quản lý mã nguồn thực tế & Minh bạch đóng góp (Real Git Repository):**
   - Toàn bộ mã nguồn, cấu hình và tài liệu quản trị dự án được lưu trữ tập trung trên GitHub ([github.com/nhatanh19/smart-quiz](https://github.com/nhatanh19/smart-quiz)).
   - Lịch sử `commit` và `Pull Request` phản ánh quá trình làm việc liên tục xuyên suốt các tuần, chứng minh rõ tỷ lệ đóng góp thực chất và cân bằng (~**25%/thành viên**) tương ứng với 4 mô-đun đã phân công.
2. **Sản phẩm chạy được thực tế (Runnable Deliverable đúng hạn Tuần 13):**
   - Hệ thống được triển khai hoạt động thực tế (Live Demo / Local Production Build), thực thi mượt mà kịch bản nghiệp vụ khép kín (*End-to-End Flow*): **Tải tệp học liệu bóc tách câu hỏi $\rightarrow$ Sinh đề tự động bằng AI theo ma trận $\rightarrow$ Tổ chức thi có trộn đề, lưu tạm và cảnh báo chuyển tab $\rightarrow$ Chấm điểm tức thì, hiển thị giải thích từ AI Tutor và xuất biểu đồ thống kê**.
3. **Đạt chuẩn Chất lượng & Tuân thủ quy trình QLDA (Quality & Process Compliance):**
   - **100%** các tính năng thuộc *In-Scope* hoàn thành theo đúng *Definition of Done (DoD)*: mã nguồn không có lỗi nghiêm trọng (*Zero Critical/Blocker Bugs*), giao diện nhất quán, dữ liệu AI trả về đúng chuẩn JSON và có cơ chế xử lý ngoại lệ an toàn khi API quá tải.
   - Hoàn thành đầy đủ bộ hồ sơ quản trị dự án qua các tuần (Project Charter, WBS, Sprint Backlog, Risk Register, biên bản Sprint Retrospective) và bảo vệ thành công trước giảng viên.

---

# 8. Feasibility Analysis - 4 Lenses (Phân tích Tính khả thi)

| Góc độ đánh giá (Lens)                               | Mức độ khả thi          | Phân tích & Minh chứng thực tế (Assessment & Evidence)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
|:---------------------------------------------------- |:-----------------------:|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1. Technical Feasibility**<br>*(Khả thi Kỹ thuật)* | **Cao (High)**          | - Cả 4 thành viên đều có nền tảng phát triển Web Full-stack hiện đại (React/Next.js, Node.js/Python, RESTful API, SQL/NoSQL) và kinh nghiệm làm việc với Git.<br>- Các thư viện bóc tách văn bản (`pdf-parse`, `mammoth`/DOCX) và giao thức kết nối LLM API (Google Gemini SDK / OpenAI SDK hỗ trợ *Structured Outputs / JSON Schema*) đều có tài liệu chuẩn và cộng đồng hỗ trợ rộng rãi.<br>- Cơ chế chống gian lận phía trình duyệt sử dụng trực tiếp các sự kiện chuẩn của DOM (`visibilitychange`, `blur`) kết hợp `localStorage` mà không cần cài đặt phần mềm thứ ba. |
| **2. Schedule Feasibility**<br>*(Khả thi Tiến độ)*   | **Cao (High)**          | - Thời lượng **13 tuần** được chia thành các giai đoạn rõ ràng với phạm vi tối thiểu khả thi (*Minimum Viable Scope*) tập trung đúng 4 mô-đun cốt lõi.<br>- Kiến trúc phân tách độc lập 4 mô-đun theo hợp đồng dữ liệu (Database Schema & API Contract thống nhất từ Tuần 3) cho phép 4 thành viên lập trình song song mà không bị nghẽn phụ thuộc lẫn nhau.                                                                                                                                                                                                                 |
| **3. Resource Feasibility**<br>*(Khả thi Nguồn lực)* | **Đảm bảo (Viable)**    | - **Công cụ & Môi trường:** 100% thành viên trang bị sẵn máy tính cá nhân cấu hình tốt, IDE hiện đại, GitHub Projects/Actions và công cụ kiểm thử API (Postman).<br>- **Tài nguyên AI & Cloud:** Gói miễn phí của Google Gemini API (hỗ trợ tới 15 RPM / 1,500 requests mỗi ngày) và các nền tảng Cloud Free Tier hoàn toàn đáp ứng nhu cầu phát triển, kiểm thử và trình diễn (Demo) cho quy mô lớp học 50–100 người dùng.                                                                                                                                                  |
| **4. Value Feasibility**<br>*(Khả thi Giá trị)*      | **Rất cao (Very High)** | - **Giá trị cho Giảng viên:** Loại bỏ tới 80% thao tác copy-paste thủ công khi tạo ngân hàng đề thi từ tài liệu sẵn có và tự động hóa việc cân đối ma trận độ khó.<br>- **Giá trị cho Sinh viên:** Chuyển đổi kỳ thi trắc nghiệm từ việc chỉ biết điểm số khô khan sang trải nghiệm học tập chủ động nhờ *AI Tutor* giải thích cặn kẽ từng câu sai và gợi ý đúng phần kiến thức bị hổng.                                                                                                                                                                                     |

---

# 9. Methodology Selection & Justification (Phương pháp quản lý)

### 🚀 Lựa chọn phương pháp: **Agile / Scrum** (Chu kỳ Sprint 2 tuần kết hợp bảng Kanban trực quan)

### 🎯 Giải thích lý do lựa chọn (Justification)

1. **Thích ứng với tính bất định của tích hợp AI & Xử lý dữ liệu (Adaptability to AI & Parser Uncertainty):**
   - Trong dự án tích hợp AI và bóc tách tài liệu, chất lượng đầu ra của *Prompt Engineering* (ép kiểu JSON Schema, phân loại độ khó theo thang Bloom) cũng như các mẫu *Regex* nhận diện câu hỏi từ nhiều định dạng file (`PDF`, `DOCX`, `TXT`) không thể xác định hoàn hảo ngay từ đầu như mô hình Waterfall truyền thống. Phương pháp **Agile/Scrum** cho phép nhóm thử nghiệm thực tế, đánh giá độ chính xác và tinh chỉnh thuật toán/prompt liên tục qua từng vòng lặp ngắn.
2. **Tối ưu hóa làm việc song song cho nhóm 4 thành viên Full-stack (Parallel Module Delivery):**
   - Với cấu trúc 4 thành viên phụ trách 4 mô-đun kỹ thuật có độ phức tạp tương đương (*File Parser, AI Quiz Generator, Exam Engine & Anti-cheat, AI Tutor & Analytics*), việc tổ chức theo các **Sprint ngắn (1–2 tuần)** kết hợp họp *Daily/Weekly Sync* giúp đồng bộ giao diện lập trình (API & Database Schema) nhanh chóng, phát hiện sớm xung đột khi tích hợp mã nguồn trên Git.
3. **Bàn giao sớm sản phẩm chạy được & Đón nhận phản hồi liên tục (Early Feedback & Risk Mitigation):**
   - Thay vì chờ đến cuối kỳ mới ghép nối hệ thống, nhóm chuyển giao các phần mềm chạy được (*Working Increments*) ngay từ cuối **Sprint 1 (Tuần 6–7)** để Giảng viên hướng dẫn và người dùng thử nghiệm đánh giá trực tiếp. Qua buổi **Sprint Retrospective**, nhóm kịp thời nhận diện các rủi ro kỹ thuật (như độ trễ API, lỗi định dạng file hay bắt nhầm sự kiện chuyển tab) và điều chỉnh kế hoạch ở **Sprint 2 (Tuần 8–12)**, đảm bảo chắc chắn có sản phẩm hoàn chỉnh (**Runnable Deliverable**) vào **Tuần 13**.
