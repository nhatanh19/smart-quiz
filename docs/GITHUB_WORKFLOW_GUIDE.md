# 📘 HƯỚNG DẪN QUY TRÌNH QUẢN LÝ DỰ ÁN TRÊN GITHUB (GITHUB AGILE/SCRUM WORKFLOW)
**Dự án:** Nền tảng Kiểm tra và Ôn luyện Trắc nghiệm Trực tuyến Tích hợp AI (*Smart Quiz*)  
**Repository:** [github.com/nhatanh19/smart-quiz](https://github.com/nhatanh19/smart-quiz)  
**Tài liệu chuẩn môn học:** Slide Quản trị Dự án Phần mềm (Week 01 – Week 08) & Hướng dẫn thực hành GitHub  
**Mục đích:** Tài liệu này chuẩn hóa quy trình làm việc từ A đến Z cho 4 thành viên trong nhóm, giúp vận hành dự án mượt mà, minh bạch đóng góp (25%/người) và đạt điểm tối đa khi giảng viên kiểm tra tiến độ thực tế (*REAL project rule*).

---

# 🌐 PHẦN 1: TỔNG QUAN MÔ HÌNH VẬN HÀNH (THE BIG PICTURE)

Trong môn Quản trị Dự án Phần mềm, GitHub không chỉ đơn thuần là nơi lưu trữ code (Git Remote Storage) mà đóng vai trò là **Nền tảng Quản trị Vận hành Dự án Tích hợp (All-in-One Project Management & DevOps Platform)**. 

### 1.1. Sơ đồ chu trình Agile/Scrum khép kín trên GitHub
```text
┌───────────────────────────────────────────────────────────────────────────┐
│                           1. PRODUCT BACKLOG                              │
│         Phân rã WBS thành GitHub Issues + Gán nhãn MoSCoW & Module        │
└─────────────────────────────────────┬─────────────────────────────────────┘
                                      │
                                      ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                           2. SPRINT PLANNING                              │
│       Tạo Milestone (Sprint 1, 2) + Họp Planning Poker gán Story Points   │
└─────────────────────────────────────┬─────────────────────────────────────┘
                                      │
                                      ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                      3. GITHUB PROJECT BOARD (KANBAN)                     │
│         Kéo Issue vào 'To Do' ──► Gán Assignee ──► Kéo sang 'In Progress' │
│                              (Giới hạn WIP Limit)                         │
└─────────────────────────────────────┬─────────────────────────────────────┘
                                      │
                                      ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                       4. PHÁT TRIỂN & KIỂM THỬ MÃ NGUỒN                   │
│   Tạo Branch 'feature/issue-X' ──► Code & Commit ──► Đẩy lên GitHub       │
└─────────────────────────────────────┬─────────────────────────────────────┘
                                      │
                                      ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                       5. PULL REQUEST & CODE REVIEW                       │
│    Mở PR có cú pháp "Closes #X" ──► Kéo thẻ sang 'In Review' ──►          │
│    CI/CD chạy test ──► Thành viên review duyệt ──► Merge vào main         │
│          (GitHub TỰ ĐỘNG đóng Issue #X và chuyển thẻ sang 'Done')         │
└─────────────────────────────────────┬─────────────────────────────────────┘
                                      │
                                      ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                   6. QUẢN LÝ CHẤT LƯỢNG & RỦI RO (DoD & RISK)             │
│        Kiểm tra Definition of Done (DoD) + Cập nhật Risk Register         │
└─────────────────────────────────────┬─────────────────────────────────────┘
                                      │
                                      ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                       7. SPRINT REVIEW & RETROSPECTIVE                    │
│      Đóng Milestone Sprint ──► Tạo Git Release v1.0 ──► Viết Retrospective│
└───────────────────────────────────────────────────────────────────────────┘
```

---

### 1.2. Phân công Vai trò Scrum trong nhóm 4 thành viên
Dự án áp dụng mô hình **Scrum tự tổ chức (Self-organizing Team)**, mỗi thành viên đều trực tiếp lập trình Full-stack cho mô-đun của mình (chiếm 25% khối lượng code) kết hợp kiêm nhiệm vai trò điều phối:
- **Product Owner (PO) kiêm Lead Dev 2:** Quản lý ưu tiên Backlog, nghiệm thu tính năng AI & Ngân hàng đề thi theo góc nhìn người dùng (Giảng viên/Sinh viên).
- **Scrum Master (SM) kiêm Lead Dev 1:** Điều phối quy trình Agile, quản lý Project Board, giải quyết vật cản (Blockers), theo dõi rủi ro và giám sát Definition of Done.
- **Development Team (Dev 1, Dev 2, Dev 3, Dev 4):** Trực tiếp tạo branch, viết code, viết test, mở Pull Request và review chéo mã nguồn của nhau.

---

# 🚀 PHẦN 2: CHI TIẾT TỪNG BƯỚC THỰC HÀNH TRÊN GITHUB

---

## BƯỚC 1: KHỞI TẠO DỰ ÁN & ĐIỀU LỆ DỰ ÁN (PROJECT INITIATION)
*(Tương ứng: Slide Week 01 - REAL Project & Week 02 - Project Initiation)*

### 1. Khởi tạo Git Repository chuẩn
- Repository được đặt tại: `https://github.com/nhatanh19/smart-quiz`.
- Đảm bảo repo ở chế độ **Public** (hoặc thêm đầy đủ tài khoản GitHub của cả 4 thành viên và Giảng viên hướng dẫn vào mục **Settings $\rightarrow$ Collaborators**).
- Tạo file `.gitignore` phù hợp với công nghệ sử dụng (`node_modules/`, `.env`, `dist/`, `.DS_Store`).

### 2. Thiết lập tài liệu `PROJECT_CHARTER.md`
- Tạo thư mục `docs/` và đưa file [docs/PROJECT_CHARTER.md](file:///e:/Data_IT_MSI/Project_Nam4/QuanTriDuAnPhanMem/smart-quiz/docs/PROJECT_CHARTER.md) lên nhánh chính `main`.
- Nội dung phải đáp ứng đúng 9 phần chuẩn slide: *Mục đích, Mục tiêu SMART, Phạm vi In/Out Scope, Ma trận Power-Interest Grid, Lịch trình 13 tuần, Ràng buộc & Giả định, Tiêu chí thành công, Phân tích 4 Lenses, Lựa chọn Agile/Scrum*.

### 3. Cấu hình bảo vệ nhánh chính (Branch Protection Rules)
- Vào **Settings** $\rightarrow$ **Branches** $\rightarrow$ Bấm **Add branch protection rule**:
  - **Branch name pattern:** Nhập `main`.
  - Tick chọn **Require a pull request before merging** (Bắt buộc phải qua PR, không ai được push thẳng vào `main`).
  - Tick chọn **Require approvals** (Đặt tối thiểu **1 approval** để bắt buộc review chéo code).

---

## BƯỚC 2: QUẢN LÝ PHẠM VI & PRODUCT BACKLOG TRÊN GITHUB
*(Tương ứng: Slide Week 03 - Scope & WBS)*

### 1. Thiết lập Hệ thống Nhãn (Labels) chuẩn hóa
Vào tab **Issues** $\rightarrow$ Chọn **Labels** $\rightarrow$ Bấm **New label** để tạo 2 nhóm nhãn chính:
- **Nhóm nhãn ưu tiên MoSCoW:**
  - `must-have` (Màu đỏ `#D73A4A`): Phạm vi tối thiểu cam kết hoàn thành (*Minimum Viable Scope*).
  - `should-have` (Màu vàng `#FBCA04`): Tính năng quan trọng gia tăng chiều sâu AI & Analytics.
  - `could-have` (Màu xanh lá `#0E8A16`): Tính năng điểm thưởng nếu dư thời gian.
  - `wont-have` (Màu xám `#6A737D`): Tính năng bị loại trừ trong học kỳ này để chống phình phạm vi.
- **Nhóm nhãn phân hệ (Modules):**
  - `module:parser` (Màu xanh dương `#1D76DB`): Bóc tách file & Quản trị hệ thống (Dev 1).
  - `module:ai-gen` (Màu tím `#5319E7`): Sinh đề thi AI theo ma trận (Dev 2).
  - `module:exam` (Màu hồng cam `#E99695`): Phòng thi & Giám sát chống gian lận (Dev 3).
  - `module:tutor-analytics` (Màu xanh mòng két `#006B75`): Gia sư ảo & Dashboard phân tích (Dev 4).

### 2. Chuyển WBS thành GitHub Issues (Product Backlog)
- Mỗi gói công việc (Work Package) đã phân rã trong [docs/DETAILED_GITHUB_ISSUES.md](file:///e:/Data_IT_MSI/Project_Nam4/QuanTriDuAnPhanMem/smart-quiz/docs/DETAILED_GITHUB_ISSUES.md) được tạo thành **1 Issue độc lập**.
- **Quy tắc đặt tiêu đề Issue:** `[Tên Module] Tên hành động cụ thể`  
  *Ví dụ:* `[Auth] User Registration, Login & JWT Token Management` hoặc `[Parser] Regex Pattern Matching Engine`.
- **Nội dung phần thân (Description) của Issue bắt buộc có 3 mục:**
  ```markdown
  ### User Story / Mô tả
  Là một [Giảng viên / Sinh viên], tôi muốn [...] để [...].

  ### Acceptance Criteria (Definition of Done Checklist)
  - [ ] API xử lý đúng dữ liệu đầu vào và lưu CSDL thành công.
  - [ ] Giao diện responsive và xử lý thông báo lỗi thân thiện.
  - [ ] Đã chạy linter không báo lỗi và test thử cục bộ chạy tốt.

  ### Phân công & Ước lượng
  - **Assignee:** Dev 1
  - **Estimate:** 3 Story Points (~2 ngày)
  ```

---

## BƯỚC 3: ƯỚC LƯỢNG & LẬP KẾ HOẠCH SPRINT (SPRINT PLANNING)
*(Tương ứng: Slide Week 04 - Estimation & Scheduling)*

### 1. Tạo Sprint Milestones
Vào tab **Issues** $\rightarrow$ Chọn **Milestones** $\rightarrow$ Bấm **New Milestone**:
- **Milestone 1:** `Sprint 1: Core Foundation`  
  - *Thời hạn (Due date):* Cuối Tuần 6 (Thời lượng 2 tuần).  
  - *Mô tả:* Hoàn thiện khung kiến trúc, Auth, Bóc tách tài liệu Regex, Sinh đề AI ma trận cơ bản, Phòng thi đếm ngược và Chấm điểm tự động.
- **Milestone 2:** `Sprint 2: Realtime & Intelligence`  
  - *Thời hạn (Due date):* Cuối Tuần 12.  
  - *Mô tả:* Tích hợp Chống gian lận Client-side, Sinh đề từ file bài giảng, Gia sư ảo AI Tutor, Dashboard thống kê, Kiểm thử E2E và Triển khai Cloud.

### 2. Họp Planning Poker & Cấu hình Story Points
- Cả nhóm họp trực tiếp hoặc online (dùng công cụ miễn phí như *PlanningPoker.com* hoặc chát Discord).
- Dùng dãy số Fibonacci (1, 2, 3, 5, 8) để đánh giá độ phức tạp kỹ thuật của từng Issue:
  - `1 SP`: Task siêu nhỏ (sửa text, cấu hình linter, thêm nút bấm).
  - `2 SP`: Task cơ bản (viết API đơn giản, tạo trang tĩnh).
  - `3 SP`: Task trung bình (xử lý logic DB, tích hợp API ngoài có kiểm tra lỗi, form nhập liệu đầy đủ).
  - `5 SP`: Task phức tạp (thuật toán Regex bóc tách câu hỏi, giao diện thi đếm ngược thời gian thực, AI prompt engineering có xử lý fallback).
- Gán trường dữ liệu tùy chỉnh **Story Points** trên GitHub Project Board.

---

## BƯỚC 4: THIẾT LẬP & VẬN HÀNH GITHUB PROJECT BOARD
*(Tương ứng: Slide Week 05 - Agile & Scrum in Practice)*

### 1. Tạo Project Board mới (GitHub Projects v2)
1. Vào tab **Projects** của repository $\rightarrow$ Bấm nút **New project**.
2. Chọn template giao diện **Board**. Đặt tên: `Smart Quiz - Scrum Board`.
3. Cấu hình các cột Workflow chuẩn gồm đúng 5 trạng thái:
   - 📥 **Backlog:** Danh sách toàn bộ các Issues của dự án chưa được đưa vào Sprint hiện tại.
   - 📋 **To Do (Sprint Backlog):** Các Issues được cam kết thực hiện trong Sprint này.
   - ⚙️ **In Progress:** Công việc đang trực tiếp được lập trình (Áp dụng **WIP Limit**: Tối đa 1–2 task/người cùng lúc).
   - 🔍 **In Review / PR:** Mã nguồn đã lập trình xong, Pull Request đang mở chờ kiểm thử và review chéo.
   - ✅ **Done:** Code đã merge vào `main`, thỏa mãn Definition of Done, Issue đã được đóng.

### 2. Tự động hóa Workflow (Project Automations)
Trong giao diện GitHub Projects, bấm biểu tượng dấu ba chấm `...` ở góc phải $\rightarrow$ Chọn **Workflows**:
- **Auto-add to project:** Tự động nạp mọi Issue mới tạo trong repo vào cột `Backlog`.
- **Item closed:** Khi Issue hoặc PR được close/merge $\rightarrow$ Tự động chuyển card sang cột `Done`.

### 3. Thiết lập chế độ xem Roadmap (Gantt Chart)
- Trong Project, bấm dấu `+` để thêm một View mới $\rightarrow$ Chọn kiểu **Roadmap**.
- Chọn trường dòng thời gian theo `Milestone` hoặc `Iteration`. Điều này giúp nhóm và Giảng viên thấy trực quan tiến độ theo từng tuần giống hệt biểu đồ Gantt.

---

## BƯỚC 5: QUY TRÌNH PHÁT TRIỂN CODE VỚI GIT & PULL REQUEST (DEV WORKFLOW)
*(Tương ứng: Slide Week 05 - Daily Execution & Code Review)*

> ⛔ **NGUYÊN TẮC VÀNG:**  
> **Không bao giờ commit hoặc push trực tiếp mã nguồn vào nhánh `main`!** Mọi dòng code đều phải đi qua nhánh tính năng (*Feature Branch*) và mở *Pull Request*.

```
[Issue #5] ──► Tạo Branch 'feature/issue-5-file-upload' ──► Code & Commit 
                                                                  │
                                                                  ▼
[main branch] ◄── Merge PR (Tự động đóng #5) ◄── Mở PR: "Closes #5" & Review
```

### Bước 5.1: Nhận task và tạo nhánh (Branch)
1. Trên Project Board, thành viên nhận task kéo card của Issue (ví dụ: Issue `#5`) từ `To Do` sang `In Progress`.
2. Gán tên mình vào ô **Assignees**.
3. Mở Terminal tại máy cá nhân, cập nhật nhánh `main` mới nhất và tạo nhánh mới:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/issue-5-file-upload
   ```
   *(Quy tắc đặt tên nhánh: `feature/issue-<ID>-<tên-ngắn-gọn>` hoặc `bugfix/issue-<ID>-...`)*

### Bước 5.2: Lập trình, kiểm thử và Commit code
- Lập trình tính năng theo đúng Acceptance Criteria của Issue.
- Viết commit message rõ ràng, có ý nghĩa theo chuẩn *Conventional Commits*:
  ```bash
  git add .
  git commit -m "feat(parser): add multer file upload and text extraction for pdf"
  ```
- Đẩy nhánh lên GitHub:
  ```bash
  git push -u origin feature/issue-5-file-upload
  ```

### Bước 5.3: Mở Pull Request (PR) & Dùng "Từ khóa ma thuật"
1. Truy cập vào GitHub repository, bạn sẽ thấy thông báo màu vàng hiện lên: *"feature/issue-5-file-upload had recent pushes"*. Bấm nút **Compare & pull request**.
2. **Tiêu đề PR:** `[Parser] Implement file upload and text extraction (Issue #5)`
3. **Phần mô tả PR (CỰC KỲ QUAN TRỌNG):** Viết từ khóa liên kết:
   ```markdown
   ### Tóm tắt thay đổi
   - Thêm API tiếp nhận tệp tải lên PDF, DOCX, TXT.
   - Bóc tách văn bản thô sử dụng thư viện pdf-parse và mammoth.

   ### Tự động đóng Issue liên kết
   Closes #5

   ### Checklist tự kiểm tra
   - [x] Đã chạy thử nghiệm local thành công.
   - [x] Không có lỗi console hay crash hệ thống.
   ```
4. Ở cột bên phải:
   - **Reviewers:** Chọn ít nhất 1 thành viên khác trong nhóm (ví dụ: mời `Dev 2` hoặc `Dev 1`).
   - **Assignees:** Gán chính mình.
   - **Milestone:** Chọn đúng Milestone của Sprint hiện tại.
5. Kéo thẻ của Issue `#5` trên Project Board sang cột **In Review / PR**.

### Bước 5.4: Review chéo mã nguồn & Merge vào nhánh chính
1. Thành viên được mời làm Reviewer mở tab **Files changed** của PR, đọc mã nguồn, để lại nhận xét nếu cần sửa đổi.
2. Nếu mã nguồn đạt chuẩn, Reviewer bấm **Review changes** $\rightarrow$ Chọn **Approve** $\rightarrow$ Bấm **Submit review**.
3. Tác giả hoặc Trưởng nhóm bấm nút **Merge pull request** (chọn *Squash and merge* hoặc *Rebase and merge*) $\rightarrow$ Bấm **Confirm merge**.
4. Bấm nút **Delete branch** để xóa nhánh phụ cho sạch kho lưu trữ.
5. **KẾT QUẢ TỰ ĐỘNG:** GitHub sẽ tự động đóng Issue `#5` và thẻ trên Project Board tự động bay sang cột **Done**!

---

## BƯỚC 6: QUẢN LÝ CHẤT LƯỢNG & THEO DÕI RỦI RO (QUALITY & RISK)
*(Tương ứng: Slide Week 06 - Risk & Quality Management)*

Để đảm bảo dự án không rơi vào tình trạng *"code chạy trên máy mình nhưng sang máy khác bị lỗi"*, nhóm bắt buộc vận hành 2 tài liệu sau:

### 1. Áp dụng Definition of Done (DoD)
Một task chỉ được coi là hoàn thành (`Done`) khi thỏa mãn 100% các tiêu chí trong tài liệu `docs/DEFINITION_OF_DONE.md`:
- [x] Mã nguồn đã viết xong và biên dịch không lỗi (No syntax/type errors).
- [x] Đã chạy linter và định dạng code tự động (`npm run lint` pass).
- [x] Đã được kiểm thử chạy thành công trên máy local (Happy path & Error handling).
- [x] Đã tạo Pull Request và được ít nhất 1 thành viên khác review phê duyệt (*Approved*).
- [x] Đã merge thành công vào nhánh `main` mà không làm hỏng các tính năng cũ.

### 2. Quản lý Sổ theo dõi Rủi ro (Risk Register)
Theo yêu cầu slide Week 06, nhóm phải duy trì file `docs/RISK_REGISTER.md` ghi nhận **các rủi ro thực tế phát sinh trong quá trình code** (chứ không chỉ là rủi ro lý thuyết):
- *Ví dụ rủi ro thực tế 1:* Gọi Gemini API bị lỗi `429 Too Many Requests` do vượt rate limit $\rightarrow$ *Chiến lược ứng phó:* Cài đặt Exponential Backoff Retry và chuyển sang dùng model Flash nhẹ hơn.
- *Ví dụ rủi ro thực tế 2:* Thư viện bóc tách file không đọc được tài liệu PDF dạng ảnh scan $\rightarrow$ *Chiến lược ứng phó:* Bắt ngoại lệ và hiển thị thông báo yêu cầu giảng viên tải file PDF dạng text số hóa.

---

## BƯỚC 7: ĐÁNH GIÁ, CẢI TIẾN & ĐÓNG GÓI BẢN PHÁT HÀNH (SPRINT REVIEW & RETROSPECTIVE)
*(Tương ứng: Slide Week 05 - Scrum Events & Week 07 - Retrospective)*

Vào cuối mỗi Sprint (Tuần 6–7 cho Sprint 1, Tuần 12–13 cho Sprint 2):

### 1. Đóng Sprint Milestone
- Vào tab **Issues** $\rightarrow$ **Milestones**.
- Kiểm tra thanh tiến độ đạt **100% Complete** (toàn bộ các Issues gán vào Sprint đã chuyển sang trạng thái Closed).
- Bấm **Close milestone**.

### 2. Soạn Biên bản Cải tiến (Sprint Retrospective)
Nhóm họp 30 phút và ghi nhận lại biên bản trong file `docs/RETROSPECTIVE_SPRINT_1.md` (hoặc tạo bài viết trong tab **Discussions** của repo) trả lời 3 câu hỏi thực chất:
1. **What went well? (Việc nhóm làm tốt):** Ví dụ: Thống nhất cấu trúc CSDL sớm, tích hợp AI prompt ra đúng JSON schema ngay từ đầu.
2. **What didn't go well? (Vướng mắc/Khó khăn gặp phải):** Ví dụ: Thuật toán Regex ban đầu bị sót các câu hỏi có công thức toán; việc review PR còn chậm do các thành viên bận lịch thi giữa kỳ.
3. **Action items for next Sprint (Kế hoạch hành động cải tiến):** Ví dụ: Đặt lịch họp Daily Sync cố định 15 phút vào 21h hàng ngày; thành viên phải review PR trong vòng 24 giờ sau khi được tag.

### 3. Đóng gói Bản phát hành chạy được (Create GitHub Release)
Để có bằng chứng nghiệm thu sản phẩm chạy được (*Runnable Increment*):
1. Vào tab **Releases** trên GitHub $\rightarrow$ Bấm **Draft a new release**.
2. **Choose a tag:** Nhập `v1.0.0-sprint1` $\rightarrow$ Bấm *Create new tag*.
3. **Release title:** `Smart Quiz v1.0.0 (Sprint 1 Release - Core Engine)`
4. **Description:** Bấm nút **Generate release notes** để GitHub tự động liệt kê danh sách toàn bộ Pull Requests đã hoàn thành trong Sprint 1.
5. Đính kèm đường dẫn demo (Local Build instructions hoặc link Cloud preview) $\rightarrow$ Bấm **Publish release**.

---

# 💯 PHẦN 3: TIÊU CHÍ CHẤM ĐIỂM CỦA GIẢNG VIÊN & MẸO ĐẠT ĐIỂM TỐI ĐA

Khi chấm điểm thực hành quản lý dự án trên GitHub, Giảng viên sẽ trực tiếp kiểm tra các mục sau trong Repository của nhóm:

| Hạng mục kiểm tra | Giảng viên sẽ bấm vào đâu để xem? | Bằng chứng đạt điểm tối đa (Best Practice) |
| :--- | :--- | :--- |
| **1. Tính cân bằng đóng góp (25%/người)** | Tab **Insights** $\rightarrow$ **Contributors** | Cả 4 thành viên đều có biểu đồ commits và dòng code thêm/xóa phân bổ đều đặn qua các tuần, không có hiện tượng 1 người làm hộ cả nhóm. |
| **2. Quy trình làm việc nhóm thực tế** | Tab **Insights** $\rightarrow$ **Network** | Cây phân nhánh Git hiển thị rõ ràng nhiều nhánh tính năng `feature/...` được tạo ra song song và gộp (merge) về `main` qua từng tuần. |
| **3. Vận hành Scrum Board** | Tab **Projects** $\rightarrow$ **Smart Quiz Board** | Có đầy đủ các cột trạng thái; các Issue có gán nhãn MoSCoW, có điểm Story Points, có gán đúng Assignee và nằm trong đúng Milestone. |
| **4. Kỷ luật mã nguồn & Review** | Tab **Pull Requests** (Closed) | Các PR có mô tả rõ ràng, có từ khóa `Closes #X`, có comment thảo luận và có ít nhất 1 dấu tích xanh phê duyệt (*Approved*) trước khi merge. |
| **5. Hồ sơ tài liệu quản trị** | Thư mục `docs/` | Đầy đủ 6 tài liệu: `PROJECT_CHARTER.md`, `WBS_AND_BACKLOG.md`, `DETAILED_GITHUB_ISSUES.md`, `DEFINITION_OF_DONE.md`, `RISK_REGISTER.md`, `RETROSPECTIVE_SPRINT_1.md`. |
| **6. Bằng chứng bàn giao thực tế** | Tab **Releases** | Có các mốc Release chính thức (`v1.0.0-sprint1`, `v2.0.0-final`) đính kèm mã nguồn và ghi chú tính năng chạy được. |

---

# ⌨️ PHẦN 4: CHEATSHEET CÁC LỆNH TERMINAL HÀNG NGÀY CHO 4 THÀNH VIÊN

Dưới đây là bộ lệnh Git cơ bản mà mỗi thành viên chỉ cần mở Terminal lên và gõ hàng ngày:

```bash
# ------------------------------------------------------------------------------
# 1. BẮT ĐẦU NGÀY MỚI LÀM VIỆC: Luôn cập nhật code mới nhất từ nhóm về máy
# ------------------------------------------------------------------------------
git checkout main
git pull origin main

# ------------------------------------------------------------------------------
# 2. BẮT ĐẦU LÀM MỘT TASK MỚI (Ví dụ làm Issue #7): Tạo nhánh mới
# ------------------------------------------------------------------------------
git checkout -b feature/issue-7-preview-table

# ------------------------------------------------------------------------------
# 3. TRONG KHI LÀM: Lưu lại tiến độ làm việc
# ------------------------------------------------------------------------------
git status                              # Xem các file vừa sửa
git add .                               # Đưa tất cả file đã sửa vào hàng đợi
git commit -m "feat(parser): add preview table component and edit buttons"

# ------------------------------------------------------------------------------
# 4. KHI HOÀN THÀNH TÍNH NĂNG: Đẩy nhánh lên GitHub để mở PR
# ------------------------------------------------------------------------------
git push -u origin feature/issue-7-preview-table
# Sau lệnh này, lên giao diện GitHub bấm nút "Compare & pull request"

# ------------------------------------------------------------------------------
# 5. KHI PR ĐÃ MERGE XONG TRÊN GITHUB: Dọn dẹp máy cá nhân
# ------------------------------------------------------------------------------
git checkout main                       # Quay lại nhánh chính
git pull origin main                    # Kéo code vừa merge về máy
git branch -d feature/issue-7-preview-table   # Xóa nhánh tính năng cũ trên máy
```
