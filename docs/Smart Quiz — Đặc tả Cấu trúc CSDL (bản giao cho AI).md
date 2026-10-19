# Smart Quiz — Đặc tả Cấu trúc CSDL (bản giao cho AI)

*Tài liệu tự đủ, không cần ngữ cảnh khác. Nguồn chuẩn (source of truth) là khối SQL ở mục 3. Công nghệ: PostgreSQL · SQLAlchemy 2.0 · Alembic · Python 3.11.*

## 0. Chỉ thị cho AI thực thi

Bạn là Senior Backend Developer. Hãy tạo cơ sở dữ liệu cho dự án Smart Quiz **đúng từng chi tiết** theo tài liệu này.

1. **Không** thêm, bớt, đổi tên bảng/cột/enum/ràng buộc/chỉ mục. **Không** hỏi lại lựa chọn công nghệ.
2. Khi mô tả ở mục 4 (SQLAlchemy) và mục 3 (SQL) có vẻ khác nhau, **mục 3 thắng**.
3. Cần tạo các tệp sau (đường dẫn tính từ thư mục `backend/`):
   - `app/core/database.py`: `Base` (kèm naming convention), `engine`, `SessionLocal`, `get_db`.
   - `app/models/entities.py`: toàn bộ enum + 8 model ORM khớp 100% mục 3.
   - `alembic/env.py`: nối `Base.metadata` từ `app.models.entities`, đọc URL từ `settings.DATABASE_URL`.
   - Một migration khởi tạo (autogenerate rồi **tự rà soát**, sửa cho khớp mục 3; `downgrade` phải xóa luôn 5 kiểu enum).
   - `scripts/seed.py`: dữ liệu mẫu theo mục 6, chạy lại nhiều lần không nhân bản (idempotent).
4. Không viết logic nghiệp vụ, API, giao diện. Chỉ làm CSDL.
5. Sau khi xong, tự kiểm tra bằng danh sách ở mục 7 và báo kết quả từng mục.

## 1. Công nghệ bắt buộc

| Hạng mục | Giá trị |
| --- | --- |
| CSDL | PostgreSQL 13 trở lên (khuyến nghị 16; tương thích Supabase/Neon). Dùng `gen_random_uuid()` có sẵn, **không** cần extension |
| ORM | SQLAlchemy 2.0 kiểu khai báo mới: `DeclarativeBase`, `Mapped[...]`, `mapped_column(...)` |
| Driver | `psycopg2-binary`; URL dạng `postgresql+psycopg2://user:pass@host:5432/db` |
| Migration | Alembic (`compare_type=True`, `compare_server_default=True`) |
| Cấu hình | `pydantic-settings`, biến `DATABASE_URL` trong `app/core/config.py` |
| Băm mật khẩu (seed) | `passlib[bcrypt]` kèm ghim `bcrypt==4.0.1` |

## 2. Quy ước chung

- Khóa chính mọi bảng: cột `id uuid`, PostgreSQL `DEFAULT gen_random_uuid()`; ORM thêm `default=uuid.uuid4`.
- Thời gian: `timestamptz` (`DateTime(timezone=True)`), lưu UTC. `created_at` và `updated_at` mặc định `now()`; ORM đặt `onupdate=func.now()` cho `updated_at` (không dùng trigger trong DB).
- Điểm số: `double precision` (SQLAlchemy `Float`). Thang điểm 10, tầng ứng dụng làm tròn 2 chữ số trước khi lưu.
- Enum: kiểu enum gốc của PostgreSQL; giá trị lưu là **tên** thành viên Python (viết hoa, khớp từng ký tự mục 3.1).
- Tên ràng buộc (naming convention) trong `MetaData`:

```python
NAMING_CONVENTION = {
    'ix': 'ix_%(column_0_label)s',
    'uq': 'uq_%(table_name)s_%(constraint_name)s',
    'ck': 'ck_%(table_name)s_%(constraint_name)s',
    'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
    'pk': 'pk_%(table_name)s',
}
```

- Hệ quả của convention: mọi `UniqueConstraint` và `CheckConstraint` trong ORM **bắt buộc có tham số `name`** ở dạng rút gọn (phần sau tiền tố). Ví dụ SQL `ck_exam_attempts_score_range` ↔ ORM `CheckConstraint(..., name='score_range')`. Mọi `Index` đặt tên đầy đủ đúng như mục 3.
- Quy ước tên bảng/cột: `snake_case`, bảng số nhiều. Thuộc tính Python trùng tên cột (cột `metadata_info` vì `metadata` bị Declarative giữ chỗ).

## 3. Cấu trúc CSDL chuẩn (PostgreSQL DDL)

Thứ tự tạo bảng bên dưới đã đúng thứ tự phụ thuộc khóa ngoại.

### 3.1 Kiểu enum

```sql
CREATE TYPE user_role        AS ENUM ('ADMIN', 'INSTRUCTOR', 'STUDENT');
CREATE TYPE question_type    AS ENUM ('SINGLE_CHOICE', 'MULTIPLE_CHOICE', 'TRUE_FALSE');
CREATE TYPE cognitive_level  AS ENUM ('REMEMBER', 'UNDERSTAND', 'APPLY');
CREATE TYPE attempt_status   AS ENUM ('IN_PROGRESS', 'SUBMITTED', 'LOCKED_VIOLATION', 'EXPIRED');
CREATE TYPE question_source  AS ENUM ('MANUAL', 'FILE_PARSER', 'AI_GENERATED');
```

### 3.2 Bảng

```sql
-- 1) users
CREATE TABLE users (
    id            uuid         NOT NULL DEFAULT gen_random_uuid(),
    email         varchar(255) NOT NULL,
    password_hash varchar(255) NOT NULL,
    full_name     varchar(255) NOT NULL,
    role          user_role    NOT NULL DEFAULT 'STUDENT',
    is_active     boolean      NOT NULL DEFAULT true,
    created_at    timestamptz  NOT NULL DEFAULT now(),
    updated_at    timestamptz  NOT NULL DEFAULT now(),
    CONSTRAINT pk_users PRIMARY KEY (id),
    CONSTRAINT uq_users_email UNIQUE (email),
    CONSTRAINT ck_users_email_lowercase CHECK (email = lower(email))
);

-- 2) categories (chuyên đề / học phần)
CREATE TABLE categories (
    id          uuid         NOT NULL DEFAULT gen_random_uuid(),
    name        varchar(255) NOT NULL,
    description text,
    created_by  uuid         NOT NULL,
    created_at  timestamptz  NOT NULL DEFAULT now(),
    updated_at  timestamptz  NOT NULL DEFAULT now(),
    CONSTRAINT pk_categories PRIMARY KEY (id),
    CONSTRAINT fk_categories_created_by_users FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT uq_categories_created_by_name UNIQUE (created_by, name)
);

-- 3) questions (ngân hàng câu hỏi)
CREATE TABLE questions (
    id              uuid            NOT NULL DEFAULT gen_random_uuid(),
    category_id     uuid            NOT NULL,
    creator_id      uuid            NOT NULL,
    content         text            NOT NULL,
    question_type   question_type   NOT NULL,
    cognitive_level cognitive_level NOT NULL,
    options         jsonb           NOT NULL,
    explanation     text,
    source_type     question_source NOT NULL DEFAULT 'MANUAL',
    created_at      timestamptz     NOT NULL DEFAULT now(),
    updated_at      timestamptz     NOT NULL DEFAULT now(),
    CONSTRAINT pk_questions PRIMARY KEY (id),
    CONSTRAINT fk_questions_category_id_categories FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE RESTRICT,
    CONSTRAINT fk_questions_creator_id_users FOREIGN KEY (creator_id) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT ck_questions_options_is_array CHECK (
        CASE WHEN jsonb_typeof(options) = 'array'
             THEN jsonb_array_length(options) BETWEEN 2 AND 10
             ELSE false END)
);
CREATE INDEX ix_questions_creator_category ON questions (creator_id, category_id);
CREATE INDEX ix_questions_matrix ON questions (category_id, cognitive_level, question_type);

-- 4) exams (kỳ thi / đề thi)
CREATE TABLE exams (
    id                   uuid         NOT NULL DEFAULT gen_random_uuid(),
    exam_code            varchar(12)  NOT NULL,
    title                varchar(255) NOT NULL,
    description          text,
    instructor_id        uuid         NOT NULL,
    duration_minutes     integer      NOT NULL,
    start_time           timestamptz,
    end_time             timestamptz,
    access_password_hash varchar(255),
    max_attempts         integer      NOT NULL DEFAULT 1,
    max_tab_violations   integer      NOT NULL DEFAULT 3,
    shuffle_questions    boolean      NOT NULL DEFAULT true,
    shuffle_options      boolean      NOT NULL DEFAULT true,
    matrix_config        jsonb,
    is_published         boolean      NOT NULL DEFAULT false,
    created_at           timestamptz  NOT NULL DEFAULT now(),
    updated_at           timestamptz  NOT NULL DEFAULT now(),
    CONSTRAINT pk_exams PRIMARY KEY (id),
    CONSTRAINT fk_exams_instructor_id_users FOREIGN KEY (instructor_id) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT uq_exams_exam_code UNIQUE (exam_code),
    CONSTRAINT ck_exams_duration_positive CHECK (duration_minutes > 0),
    CONSTRAINT ck_exams_max_attempts_min CHECK (max_attempts >= 1),
    CONSTRAINT ck_exams_max_tab_violations_min CHECK (max_tab_violations >= 1),
    CONSTRAINT ck_exams_time_window CHECK (start_time IS NULL OR end_time IS NULL OR end_time > start_time),
    CONSTRAINT ck_exams_published_has_window CHECK (NOT is_published OR (start_time IS NOT NULL AND end_time IS NOT NULL)),
    CONSTRAINT ck_exams_matrix_config_object CHECK (matrix_config IS NULL OR jsonb_typeof(matrix_config) = 'object')
);
CREATE INDEX ix_exams_instructor_id ON exams (instructor_id);
CREATE INDEX ix_exams_published_start ON exams (is_published, start_time);

-- 5) exam_questions (đề thi - câu hỏi)
CREATE TABLE exam_questions (
    id          uuid             NOT NULL DEFAULT gen_random_uuid(),
    exam_id     uuid             NOT NULL,
    question_id uuid             NOT NULL,
    order_index integer          NOT NULL,
    points      double precision NOT NULL DEFAULT 1.0,
    CONSTRAINT pk_exam_questions PRIMARY KEY (id),
    CONSTRAINT fk_exam_questions_exam_id_exams FOREIGN KEY (exam_id) REFERENCES exams (id) ON DELETE CASCADE,
    CONSTRAINT fk_exam_questions_question_id_questions FOREIGN KEY (question_id) REFERENCES questions (id) ON DELETE RESTRICT,
    CONSTRAINT uq_exam_questions_exam_question UNIQUE (exam_id, question_id),
    CONSTRAINT uq_exam_questions_exam_order UNIQUE (exam_id, order_index) DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT ck_exam_questions_order_index_min CHECK (order_index >= 1),
    CONSTRAINT ck_exam_questions_points_positive CHECK (points > 0)
);
CREATE INDEX ix_exam_questions_question_id ON exam_questions (question_id);

-- 6) exam_attempts (lượt làm bài)
CREATE TABLE exam_attempts (
    id                      uuid             NOT NULL DEFAULT gen_random_uuid(),
    exam_id                 uuid             NOT NULL,
    student_id              uuid             NOT NULL,
    attempt_number          integer          NOT NULL DEFAULT 1,
    started_at              timestamptz      NOT NULL DEFAULT now(),
    expires_at              timestamptz      NOT NULL,
    submitted_at            timestamptz,
    score                   double precision,
    status                  attempt_status   NOT NULL DEFAULT 'IN_PROGRESS',
    violation_count         integer          NOT NULL DEFAULT 0,
    question_order_snapshot jsonb            NOT NULL,
    CONSTRAINT pk_exam_attempts PRIMARY KEY (id),
    CONSTRAINT fk_exam_attempts_exam_id_exams FOREIGN KEY (exam_id) REFERENCES exams (id) ON DELETE RESTRICT,
    CONSTRAINT fk_exam_attempts_student_id_users FOREIGN KEY (student_id) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT uq_exam_attempts_exam_student_no UNIQUE (exam_id, student_id, attempt_number),
    CONSTRAINT ck_exam_attempts_attempt_number_min CHECK (attempt_number >= 1),
    CONSTRAINT ck_exam_attempts_score_range CHECK (score IS NULL OR (score >= 0 AND score <= 10)),
    CONSTRAINT ck_exam_attempts_violation_count_min CHECK (violation_count >= 0),
    CONSTRAINT ck_exam_attempts_closed_at_matches_status CHECK (
        (status = 'IN_PROGRESS' AND submitted_at IS NULL) OR
        (status <> 'IN_PROGRESS' AND submitted_at IS NOT NULL)),
    CONSTRAINT ck_exam_attempts_snapshot_object CHECK (jsonb_typeof(question_order_snapshot) = 'object')
);
CREATE UNIQUE INDEX uq_exam_attempts_one_in_progress ON exam_attempts (exam_id, student_id) WHERE status = 'IN_PROGRESS';
CREATE INDEX ix_exam_attempts_student_started ON exam_attempts (student_id, started_at DESC);
CREATE INDEX ix_exam_attempts_open_expires ON exam_attempts (expires_at) WHERE status = 'IN_PROGRESS';

-- 7) attempt_answers (chi tiết câu trả lời)
CREATE TABLE attempt_answers (
    id                uuid             NOT NULL DEFAULT gen_random_uuid(),
    attempt_id        uuid             NOT NULL,
    question_id       uuid             NOT NULL,
    selected_options  jsonb            NOT NULL DEFAULT '[]'::jsonb,
    is_correct        boolean,
    points_awarded    double precision,
    ai_tutor_feedback jsonb,
    CONSTRAINT pk_attempt_answers PRIMARY KEY (id),
    CONSTRAINT fk_attempt_answers_attempt_id_exam_attempts FOREIGN KEY (attempt_id) REFERENCES exam_attempts (id) ON DELETE CASCADE,
    CONSTRAINT fk_attempt_answers_question_id_questions FOREIGN KEY (question_id) REFERENCES questions (id) ON DELETE RESTRICT,
    CONSTRAINT uq_attempt_answers_attempt_question UNIQUE (attempt_id, question_id),
    CONSTRAINT ck_attempt_answers_selected_options_is_array CHECK (jsonb_typeof(selected_options) = 'array'),
    CONSTRAINT ck_attempt_answers_points_awarded_min CHECK (points_awarded IS NULL OR points_awarded >= 0),
    CONSTRAINT ck_attempt_answers_feedback_object CHECK (ai_tutor_feedback IS NULL OR jsonb_typeof(ai_tutor_feedback) = 'object')
);
CREATE INDEX ix_attempt_answers_question_id ON attempt_answers (question_id);

-- 8) anti_cheat_logs (nhật ký chống gian lận)
CREATE TABLE anti_cheat_logs (
    id            uuid        NOT NULL DEFAULT gen_random_uuid(),
    attempt_id    uuid        NOT NULL,
    event_type    varchar(50) NOT NULL,
    logged_at     timestamptz NOT NULL DEFAULT now(),
    metadata_info jsonb,
    CONSTRAINT pk_anti_cheat_logs PRIMARY KEY (id),
    CONSTRAINT fk_anti_cheat_logs_attempt_id_exam_attempts FOREIGN KEY (attempt_id) REFERENCES exam_attempts (id) ON DELETE CASCADE,
    CONSTRAINT ck_anti_cheat_logs_metadata_object CHECK (metadata_info IS NULL OR jsonb_typeof(metadata_info) = 'object')
);
CREATE INDEX ix_anti_cheat_logs_attempt_logged ON anti_cheat_logs (attempt_id, logged_at);
```

### 3.3 Quan hệ tóm tắt

| Từ | Đến | Kiểu | ON DELETE |
| --- | --- | --- | --- |
| categories.created\_by | users.id | N-1 | RESTRICT |
| questions.category\_id | categories.id | N-1 | RESTRICT |
| questions.creator\_id | users.id | N-1 | RESTRICT |
| exams.instructor\_id | users.id | N-1 | RESTRICT |
| exam\_questions.exam\_id | exams.id | N-1 | CASCADE |
| exam\_questions.question\_id | questions.id | N-1 | RESTRICT |
| exam\_attempts.exam\_id | exams.id | N-1 | RESTRICT |
| exam\_attempts.student\_id | users.id | N-1 | RESTRICT |
| attempt\_answers.attempt\_id | exam\_attempts.id | N-1 | CASCADE |
| attempt\_answers.question\_id | questions.id | N-1 | RESTRICT |
| anti\_cheat\_logs.attempt\_id | exam\_attempts.id | N-1 | CASCADE |

## 4. Quy tắc ánh xạ SQLAlchemy 2.0 (để model khớp DDL)

- `Base(DeclarativeBase)` đặt `metadata = MetaData(naming_convention=NAMING_CONVENTION)`; `engine = create_engine(DATABASE_URL, pool_pre_ping=True, ...)`; `SessionLocal = sessionmaker(autoflush=False, expire_on_commit=False)`.
- Khóa chính: `id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4, server_default=text('gen_random_uuid()'))`.
- Enum: định nghĩa `class UserRole(str, enum.Enum)` với giá trị bằng tên, cột dùng `SAEnum(UserRole, name='user_role')`; `server_default` truyền chuỗi (ví dụ `'STUDENT'`). Tên kiểu đúng như mục 3.1. Tương tự cho `QuestionType`, `CognitiveLevel`, `AttemptStatus`, `QuestionSource`.
- `Mapped[X | None]` → cột nullable; `Mapped[X]` → NOT NULL. JSONB dùng `sqlalchemy.dialects.postgresql.JSONB`.
- Chỉ mục từng phần: `Index('uq_exam_attempts_one_in_progress', 'exam_id', 'student_id', unique=True, postgresql_where=text("status = 'IN_PROGRESS'"))`; tương tự `ix_exam_attempts_open_expires`.
- `UniqueConstraint('exam_id', 'order_index', name='exam_order', deferrable=True, initially='DEFERRED')` cho `exam_questions`.
- `Index('ix_exam_attempts_student_started', 'student_id', desc('started_at'))`.
- `updated_at`: `server_default=func.now(), onupdate=func.now()`.
- Khóa ngoại: `ForeignKey('users.id', ondelete='RESTRICT')` (hoặc `'CASCADE'` theo mục 3.3). Quan hệ `relationship()` là tùy chọn, không được làm đổi schema.
- Alembic `env.py`: `import app.models.entities` để đăng ký model; `config.set_main_option('sqlalchemy.url', settings.DATABASE_URL.replace('%', '%%'))`; `target_metadata = Base.metadata`.
- Migration: autogenerate **không** tự phát hiện CHECK, không xóa kiểu enum khi `downgrade`. Phải tự bổ sung/kiểm tra các CHECK mục 3.2 và thêm `DROP TYPE IF EXISTS` cho 5 enum ở cuối `downgrade()`. Vòng `upgrade head` → `downgrade base` → `upgrade head` phải chạy sạch.

## 5. Cấu trúc JSONB (chỉ để tham chiếu, DB chỉ kiểm kiểu như mục 3.2)

| Cột | Cấu trúc |
| --- | --- |
| `questions.options` | Mảng 2–10 phần tử `{"id": "A", "text": "...", "is_correct": true}`; `id` duy nhất trong câu, ký tự in hoa |
| `exams.matrix_config` | `{"version":1,"total_questions":20,"category_ids":["<uuid>"],"cognitive_distribution":{"REMEMBER":8,"UNDERSTAND":8,"APPLY":4},"type_distribution":{"SINGLE_CHOICE":12,"MULTIPLE_CHOICE":5,"TRUE_FALSE":3}}` hoặc NULL |
| `exam_attempts.question_order_snapshot` | `{"version":1,"questions":[{"question_id":"<uuid>","options_order":["C","A","D","B"]}]}`; thứ tự phần tử = thứ tự hiển thị; `options_order` là `id` phương án gốc đã trộn |
| `attempt_answers.selected_options` | Mảng `id` phương án gốc, ví dụ `["A","C"]`; `[]` = bỏ trống |
| `attempt_answers.ai_tutor_feedback` | `{"version":1,"explanation":"...","why_selected_wrong":"...","study_suggestions":["..."],"model":"...","generated_at":"<ISO-8601>"}` hoặc NULL |
| `anti_cheat_logs.metadata_info` | `{"client_ts":"<ISO-8601>","visibility_state":"hidden","counted":true}` hoặc NULL |

Giá trị `event_type` đã định nghĩa: `TAB_SWITCH`, `WINDOW_BLUR`, `COPY_PASTE_ATTEMPT`, `DEVTOOLS_SHORTCUT`. Cột là `varchar(50)`, **không** tạo enum hay CHECK cho cột này.

## 6. Dữ liệu mẫu (`scripts/seed.py`)

Idempotent: với mỗi bản ghi, tìm theo khóa tự nhiên (`users.email`; `categories` theo `(created_by, name)`; `questions` theo `(creator_id, content)`) rồi mới tạo. Mật khẩu đọc từ biến `SEED_DEFAULT_PASSWORD` (mặc định `SmartQuiz@123`) và **phải băm bằng bcrypt** trước khi lưu vào `password_hash`.

**Người dùng** (`is_active = true`):

| email | full\_name | role |
| --- | --- | --- |
| admin@smartquiz.edu.vn | Quản trị viên | ADMIN |
| instructor@smartquiz.edu.vn | Giảng viên Mẫu | INSTRUCTOR |
| student@smartquiz.edu.vn | Sinh viên Mẫu | STUDENT |

**Chuyên đề:** `name = 'Quản trị Dự án Phần mềm'`, `description = 'Chuyên đề mẫu phục vụ kiểm thử hệ thống.'`, `created_by` = giảng viên.

**Ba câu hỏi** (`category_id` = chuyên đề trên, `creator_id` = giảng viên, `source_type = 'MANUAL'`):

| # | question\_type | cognitive\_level | content |
| --- | --- | --- | --- |
| 1 | SINGLE\_CHOICE | REMEMBER | WBS là viết tắt của cụm từ nào trong quản trị dự án? |
| 2 | MULTIPLE\_CHOICE | UNDERSTAND | Những phát biểu nào đúng về Quy tắc 100% khi xây dựng WBS? |
| 3 | TRUE\_FALSE | APPLY | Nhóm có 4 thành viên, ngân sách 0 USD, hạn chót cố định ở Tuần 13. Khách hàng đề nghị thêm chấm tự luận bằng AI. Đưa ngay vào phạm vi mà không đánh giá lại là phù hợp với kiểm soát phạm vi. |

`options` của từng câu:

```json
[
  {"id":"A","text":"Work Breakdown Structure","is_correct":true},
  {"id":"B","text":"Work Budget Schedule","is_correct":false},
  {"id":"C","text":"Weekly Backlog Summary","is_correct":false},
  {"id":"D","text":"Workflow Baseline System","is_correct":false}
]
```

```json
[
  {"id":"A","text":"WBS phải bao quát toàn bộ phạm vi dự án","is_correct":true},
  {"id":"B","text":"Các thành phần con cộng lại phải đủ 100% công việc của thành phần cha","is_correct":true},
  {"id":"C","text":"Được thêm công việc ngoài phạm vi nếu còn thời gian","is_correct":false},
  {"id":"D","text":"WBS chỉ liệt kê các hoạt động hành chính","is_correct":false}
]
```

```json
[
  {"id":"A","text":"Đúng","is_correct":false},
  {"id":"B","text":"Sai","is_correct":true}
]
```

`explanation` tương ứng:

1. "WBS (Work Breakdown Structure) là cấu trúc phân rã công việc, chia phạm vi dự án thành các thành phần nhỏ hơn, dễ quản lý."
2. "Quy tắc 100% yêu cầu WBS bao quát toàn bộ phạm vi và công việc của các thành phần con cộng lại đúng bằng 100% công việc của thành phần cha, không thừa, không thiếu."
3. "Mọi yêu cầu mới phải được đánh giá tác động lên phạm vi, thời gian, chi phí và nguồn lực. Đưa thẳng vào phạm vi gây trượt phạm vi (scope creep)."

**Tùy chọn** (chỉ khi chạy với cờ `--with-demo-exam`): một đề mẫu `exam_code = 'DEMO0001'`, `title = 'Đề thi mẫu'`, `instructor_id` = giảng viên, `duration_minutes = 15`, `start_time = now() - interval '1 day'`, `end_time = now() + interval '30 days'`, `access_password_hash = NULL`, `is_published = true`; thêm 3 dòng `exam_questions` cho 3 câu trên với `order_index` 1, 2, 3 và `points = 1.0`.

## 7. Danh sách kiểm tra nghiệm thu (AI phải tự chạy và báo kết quả)

1. `alembic upgrade head` trên DB trống tạo đúng **8 bảng** (cộng bảng `alembic_version`) và **5 kiểu enum**, không lỗi.
2. `alembic downgrade base` rồi `alembic upgrade head` chạy sạch (không còn kiểu enum sót lại sau `downgrade`).
3. Chạy `alembic revision --autogenerate` ngay sau `upgrade head` **không sinh thay đổi nào**.
4. Chạy `seed.py` hai lần: lần 2 không tạo thêm dòng nào; tổng cộng 3 users, 1 category, 3 questions.
5. Các thao tác sau **phải bị DB từ chối**:
   - chèn `users.email` có chữ hoa;
   - hai `exam_attempts` cùng `(exam_id, student_id)` đều `IN_PROGRESS`;
   - `exams` với `end_time <= start_time`;
   - `exams` có `is_published = true` nhưng `start_time` hoặc `end_time` NULL;
   - hai dòng `attempt_answers` trùng `(attempt_id, question_id)`;
   - xóa `questions` đang có trong `exam_questions`;
   - `exam_attempts` có `status = 'SUBMITTED'` mà `submitted_at` NULL (và ngược lại: `IN_PROGRESS` mà `submitted_at` có giá trị);
   - `questions.options` là object hoặc mảng 1 phần tử;
   - `exam_attempts.score = 10.5`.
6. Đổi chỗ `order_index` của hai dòng `exam_questions` trong một transaction thành công (nhờ ràng buộc DEFERRABLE).
7. Xóa một `exam_attempts` (không bị ràng buộc khác chặn) tự xóa các `attempt_answers` và `anti_cheat_logs` của nó.

## 8. Phạm vi KHÔNG nằm trong CSDL (AI không được tự thêm vào schema)

Các quy tắc sau do tầng ứng dụng xử lý, **không** tạo trigger, hàm hay ràng buộc tương ứng trong DB: kiểm tra `options` theo `question_type` (số phương án đúng); chuyển trạng thái `exam_attempts`; tăng `violation_count`; chấm điểm và làm tròn; sinh `exam_code`; băm mật khẩu phòng thi; kiểm tra `question_id` gửi lên thuộc snapshot; khóa chỉnh sửa câu hỏi/đề đã có lượt thi.
