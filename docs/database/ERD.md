# 📊 SƠ ĐỒ QUAN HỆ THỰC THỂ (ENTITY RELATIONSHIP DIAGRAM - ERD)
## DỰ ÁN: SMART QUIZ — NỀN TẢNG KIỂM TRA & ÔN LUYỆN TRẮC NGHIỆM TRỰC TUYẾN AI
> **Nhiệm vụ:** [Database] Design Relational Schema (ERD) & Database Migrations (#2)  
> **Tài liệu tham chiếu:** `docs/DATABASE_GUIDE.md`, `database/schema.sql`

---

## 1. Sơ đồ Quan hệ Thực thể Tổng thể (Mermaid ERD)

```mermaid
erDiagram
    users ||--o{ categories : "creates (1:N)"
    users ||--o{ subjects : "creates (1:N)"
    users ||--o{ questions : "creates (1:N)"
    users ||--o{ exams : "instructs (1:N)"
    users ||--o{ exam_attempts : "takes (1:N)"

    subjects ||--o{ categories : "groups (1:N)"
    categories ||--o{ questions : "contains (1:N)"

    exams ||--o{ exam_questions : "includes (1:N)"
    questions ||--o{ exam_questions : "assigned_to (1:N)"

    exams ||--o{ exam_attempts : "has (1:N)"

    exam_attempts ||--o{ attempt_answers : "records (1:N)"
    questions ||--o{ attempt_answers : "answered_for (1:N)"

    exam_attempts ||--o{ anti_cheat_logs : "tracks (1:N)"

    users {
        uuid id PK "gen_random_uuid()"
        varchar email UK "lowercase, duy nhất"
        varchar password_hash "Bcrypt hash"
        varchar full_name "Họ và tên"
        user_role role "ADMIN | INSTRUCTOR | STUDENT"
        boolean is_active "Mặc định true"
        timestamptz created_at "UTC timestamp"
        timestamptz updated_at "UTC timestamp"
    }

    subjects {
        uuid id PK "gen_random_uuid()"
        varchar name "Tên môn học"
        text description "Mô tả môn học"
        uuid created_by FK "users.id (ON DELETE RESTRICT)"
        timestamptz created_at "UTC timestamp"
        timestamptz updated_at "UTC timestamp"
    }

    categories {
        uuid id PK "gen_random_uuid()"
        varchar name "Tên chuyên đề"
        text description "Mô tả học phần"
        uuid subject_id FK "subjects.id (nullable for legacy topics)"
        uuid created_by FK "users.id (ON DELETE RESTRICT)"
        timestamptz created_at "UTC timestamp"
        timestamptz updated_at "UTC timestamp"
    }

    questions {
        uuid id PK "gen_random_uuid()"
        uuid category_id FK "categories.id (ON DELETE RESTRICT)"
        uuid creator_id FK "users.id (ON DELETE RESTRICT)"
        text content "Nội dung câu hỏi"
        question_type question_type "SINGLE_CHOICE | MULTIPLE_CHOICE | TRUE_FALSE"
        cognitive_level cognitive_level "REMEMBER | UNDERSTAND | APPLY"
        question_level level "EASY | MEDIUM | HARD"
        jsonb options "Mảng JSONB từ 2 đến 10 phương án"
        jsonb tags "Danh sách tag tự do"
        text explanation "Lời giải thích chuẩn"
        question_source source_type "MANUAL | FILE_PARSER | AI_GENERATED"
        timestamptz created_at "UTC timestamp"
        timestamptz updated_at "UTC timestamp"
    }

    exams {
        uuid id PK "gen_random_uuid()"
        varchar exam_code UK "Mã đề công khai (ví dụ DEMO0001)"
        varchar title "Tiêu đề kỳ thi"
        text description "Mô tả / Hướng dẫn thi"
        uuid instructor_id FK "users.id (ON DELETE RESTRICT)"
        integer duration_minutes "Thời lượng thi (phút) > 0"
        timestamptz start_time "Thời điểm mở đề"
        timestamptz end_time "Thời điểm đóng đề > start_time"
        varchar access_password_hash "Mật khẩu phòng thi"
        integer max_attempts "Số lượt làm tối đa >= 1"
        integer max_tab_violations "Ngưỡng vi phạm tab >= 1"
        boolean shuffle_questions "Trộn câu hỏi"
        boolean shuffle_options "Trộn đáp án"
        jsonb matrix_config "Ma trận đề thi tự động"
        boolean is_published "Trạng thái công bố"
        timestamptz created_at "UTC timestamp"
        timestamptz updated_at "UTC timestamp"
    }

    exam_questions {
        uuid id PK "gen_random_uuid()"
        uuid exam_id FK "exams.id (ON DELETE CASCADE)"
        uuid question_id FK "questions.id (ON DELETE RESTRICT)"
        integer order_index "Thứ tự hiển thị trong đề >= 1"
        float points "Điểm số cho câu hỏi > 0"
    }

    exam_attempts {
        uuid id PK "gen_random_uuid()"
        uuid exam_id FK "exams.id (ON DELETE RESTRICT)"
        uuid student_id FK "users.id (ON DELETE RESTRICT)"
        integer attempt_number "Lượt thi số >= 1"
        timestamptz started_at "Bắt đầu làm bài"
        timestamptz expires_at "Hạn chót nộp bài"
        timestamptz submitted_at "Thời điểm nộp bài"
        float score "Điểm số bài thi (0 <= score <= 10)"
        attempt_status status "IN_PROGRESS | SUBMITTED | LOCKED_VIOLATION | EXPIRED"
        integer violation_count "Số lần vi phạm >= 0"
        jsonb question_order_snapshot "Bản chụp đề và phương án đã xáo trộn"
    }

    attempt_answers {
        uuid id PK "gen_random_uuid()"
        uuid attempt_id FK "exam_attempts.id (ON DELETE CASCADE)"
        uuid question_id FK "questions.id (ON DELETE RESTRICT)"
        jsonb selected_options "Danh sách ID phương án chọn"
        boolean is_correct "Kết quả chấm đúng/sai"
        float points_awarded "Điểm đạt được >= 0"
        jsonb ai_tutor_feedback "Phân tích ngữ cảnh từ AI Tutor"
    }

    anti_cheat_logs {
        uuid id PK "gen_random_uuid()"
        uuid attempt_id FK "exam_attempts.id (ON DELETE CASCADE)"
        varchar event_type "TAB_SWITCH | WINDOW_BLUR | etc."
        timestamptz logged_at "Thời điểm xảy ra vi phạm"
        jsonb metadata_info "Dữ liệu ngữ cảnh client"
    }
```

---

## 2. Danh mục 5 Kiểu Enum Native

1. **`user_role`**: `'ADMIN'`, `'INSTRUCTOR'`, `'STUDENT'`
2. **`question_type`**: `'SINGLE_CHOICE'`, `'MULTIPLE_CHOICE'`, `'TRUE_FALSE'`
3. **`cognitive_level`**: `'REMEMBER'`, `'UNDERSTAND'`, `'APPLY'`
4. **`question_level`**: `'EASY'`, `'MEDIUM'`, `'HARD'` (độ khó câu hỏi, độc lập với điểm khi đưa vào đề)
5. **`attempt_status`**: `'IN_PROGRESS'`, `'SUBMITTED'`, `'LOCKED_VIOLATION'`, `'EXPIRED'`
6. **`question_source`**: `'MANUAL'`, `'FILE_PARSER'`, `'AI_GENERATED'`

---

## 3. Ma trận Khóa ngoại & Hành vi Xóa (Foreign Keys & Cascade Rules)

| Bảng nguồn | Cột FK | Bảng đích | Ràng buộc `ON DELETE` | Mục đích nghiệp vụ |
| :--- | :--- | :--- | :---: | :--- |
| `categories` | `created_by` | `users(id)` | **RESTRICT** | Không cho xóa user đang sở hữu chuyên đề. |
| `subjects` | `created_by` | `users(id)` | **RESTRICT** | Không cho xóa user đang sở hữu môn học. |
| `categories` | `subject_id` | `subjects(id)` | **SET NULL** | Giữ lại chuyên đề cũ nếu môn học bị xóa. |
| `questions` | `category_id` | `categories(id)` | **RESTRICT** | Chuyên đề có câu hỏi thì không được xóa thẳng. |
| `questions` | `creator_id` | `users(id)` | **RESTRICT** | Giữ lịch sử tác giả tạo câu hỏi. |
| `exams` | `instructor_id` | `users(id)` | **RESTRICT** | Bảo toàn danh tính giảng viên ra đề. |
| `exam_questions` | `exam_id` | `exams(id)` | **CASCADE** | Xóa đề thi tự động xóa bảng trung gian câu hỏi. |
| `exam_questions` | `question_id` | `questions(id)` | **RESTRICT** | Không thể xóa câu hỏi khi đang nằm trong đề thi. |
| `exam_attempts` | `exam_id` | `exams(id)` | **RESTRICT** | Không được xóa đề thi khi đã có thí sinh làm bài. |
| `exam_attempts` | `student_id` | `users(id)` | **RESTRICT** | Bảo toàn kết quả thi của thí sinh. |
| `attempt_answers` | `attempt_id` | `exam_attempts(id)` | **CASCADE** | Xóa bài thi sẽ dọn sạch câu trả lời chi tiết. |
| `attempt_answers` | `question_id` | `questions(id)` | **RESTRICT** | Bảo toàn liên kết câu hỏi với câu trả lời. |
| `anti_cheat_logs` | `attempt_id` | `exam_attempts(id)` | **CASCADE** | Xóa bài thi sẽ xóa nhật ký vi phạm liên quan. |

---

## 4. Các Ràng buộc Đặc biệt Cần Lưu ý

- **Hoán đổi thứ tự câu hỏi:** `uq_exam_questions_exam_order UNIQUE (exam_id, order_index) DEFERRABLE INITIALLY DEFERRED` cho phép tráo đổi vị trí câu hỏi trong 1 transaction mà không bị lỗi trùng thứ tự tạm thời.
- **Duy nhất 1 bài thi đang làm:** Chỉ mục từng phần `uq_exam_attempts_one_in_progress` đảm bảo thí sinh chỉ có duy nhất 1 bài `IN_PROGRESS` cho cùng 1 đề tại 1 thời điểm.
- **Ràng buộc công bố đề thi:** Nếu `is_published = true`, bắt buộc `start_time` và `end_time` không được NULL.
- **Kiểm tra trạng thái nộp bài:** Nếu `status = 'IN_PROGRESS'` thì `submitted_at` phải NULL. Khi đã nộp bài (`SUBMITTED`, `LOCKED_VIOLATION`, `EXPIRED`), `submitted_at` bắt buộc có giá trị.
