-- =============================================================================
-- SMART QUIZ - POSTGRESQL DATABASE SCHEMA (DDL SCRIPT)
-- Dự án: Smart Quiz — Nền tảng kiểm tra và ôn luyện trắc nghiệm trực tuyến AI
-- Tài liệu gốc: docs/Smart Quiz — Đặc tả Cấu trúc CSDL (bản giao cho AI).md
-- Hỗ trợ: PostgreSQL 13+ (Khuyến nghị PostgreSQL 16+, Neon, Supabase, AWS RDS)
-- =============================================================================

-- 0. KÍCH HOẠT EXTENSION HỖ TRỢ UUID (NẾU CẦN)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- 1. DANH MỤC CÁC KIỂU DỮ LIỆU ENUM (POSTGRESQL NATIVE ENUMS)
-- =============================================================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
        CREATE TYPE user_role AS ENUM ('ADMIN', 'INSTRUCTOR', 'STUDENT');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'question_type') THEN
        CREATE TYPE question_type AS ENUM ('SINGLE_CHOICE', 'MULTIPLE_CHOICE', 'TRUE_FALSE');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'cognitive_level') THEN
        CREATE TYPE cognitive_level AS ENUM ('REMEMBER', 'UNDERSTAND', 'APPLY');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'attempt_status') THEN
        CREATE TYPE attempt_status AS ENUM ('IN_PROGRESS', 'SUBMITTED', 'LOCKED_VIOLATION', 'EXPIRED');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'question_source') THEN
        CREATE TYPE question_source AS ENUM ('MANUAL', 'FILE_PARSER', 'AI_GENERATED');
    END IF;
END $$;

-- =============================================================================
-- 2. TẠO CÁC BẢNG THỰC THỂ (8 TABLES)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 2.1 Bảng: users (Tài khoản người dùng & Phân quyền)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
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

COMMENT ON TABLE users IS 'Quản lý thông tin tài khoản và vai trò người dùng trong hệ thống';
COMMENT ON COLUMN users.email IS 'Email duy nhất, bắt buộc viết thường toàn bộ (lowercase)';
COMMENT ON COLUMN users.role IS 'Phân quyền người dùng: ADMIN, INSTRUCTOR, STUDENT';

-- -----------------------------------------------------------------------------
-- 2.2 Bảng: categories (Chuyên đề / Học phần quản lý câu hỏi)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS categories (
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

COMMENT ON TABLE categories IS 'Chuyên đề hoặc môn học chứa ngân hàng câu hỏi';
COMMENT ON COLUMN categories.created_by IS 'Giảng viên/quản trị viên sở hữu chuyên đề (RESTRICT khi xóa user)';

-- -----------------------------------------------------------------------------
-- 2.3 Bảng: questions (Ngân hàng câu hỏi trắc nghiệm)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS questions (
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

CREATE INDEX IF NOT EXISTS ix_questions_creator_category ON questions (creator_id, category_id);
CREATE INDEX IF NOT EXISTS ix_questions_matrix ON questions (category_id, cognitive_level, question_type);

COMMENT ON TABLE questions IS 'Ngân hàng câu hỏi đơn vị, hỗ trợ định dạng Bloom và JSONB options';
COMMENT ON COLUMN questions.options IS 'Mảng JSONB chứa từ 2 đến 10 phương án: [{"id": "A", "text": "...", "is_correct": true}]';
COMMENT ON COLUMN questions.cognitive_level IS 'Mức độ nhận thức Bloom: REMEMBER (Nhận biết), UNDERSTAND (Thông hiểu), APPLY (Vận dụng)';

-- -----------------------------------------------------------------------------
-- 2.4 Bảng: exams (Kỳ thi / Đề thi trắc nghiệm)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS exams (
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

CREATE INDEX IF NOT EXISTS ix_exams_instructor_id ON exams (instructor_id);
CREATE INDEX IF NOT EXISTS ix_exams_published_start ON exams (is_published, start_time);

COMMENT ON TABLE exams IS 'Kỳ thi hoặc đề kiểm tra do giảng viên thiết lập';
COMMENT ON COLUMN exams.exam_code IS 'Mã đề thi định danh công khai (ví dụ DEMO0001)';
COMMENT ON COLUMN exams.max_tab_violations IS 'Số lần chuyển tab tối đa trước khi tự động khóa bài thi';

-- -----------------------------------------------------------------------------
-- 2.5 Bảng: exam_questions (Bảng trung gian liên kết Đề thi & Câu hỏi)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS exam_questions (
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

CREATE INDEX IF NOT EXISTS ix_exam_questions_question_id ON exam_questions (question_id);

COMMENT ON TABLE exam_questions IS 'Danh sách câu hỏi trong đề, điểm số và thứ tự hiển thị';
COMMENT ON CONSTRAINT uq_exam_questions_exam_order ON exam_questions IS 'Thứ tự câu hỏi duy nhất trong đề, DEFERRABLE cho phép hoán đổi vị trí trong transaction';

-- -----------------------------------------------------------------------------
-- 2.6 Bảng: exam_attempts (Lượt tham gia làm bài thi của thí sinh)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS exam_attempts (
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

CREATE UNIQUE INDEX IF NOT EXISTS uq_exam_attempts_one_in_progress ON exam_attempts (exam_id, student_id) WHERE status = 'IN_PROGRESS';
CREATE INDEX IF NOT EXISTS ix_exam_attempts_student_started ON exam_attempts (student_id, started_at DESC);
CREATE INDEX IF NOT EXISTS ix_exam_attempts_open_expires ON exam_attempts (expires_at) WHERE status = 'IN_PROGRESS';

COMMENT ON TABLE exam_attempts IS 'Lượt làm bài của sinh viên, lưu trữ điểm số, trạng thái và thời gian';
COMMENT ON INDEX uq_exam_attempts_one_in_progress IS 'Đảm bảo mỗi sinh viên chỉ được phép có duy nhất 1 bài thi IN_PROGRESS cho 1 đề tại cùng 1 thời điểm';

-- -----------------------------------------------------------------------------
-- 2.7 Bảng: attempt_answers (Chi tiết câu trả lời của thí sinh cho từng câu)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS attempt_answers (
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

CREATE INDEX IF NOT EXISTS ix_attempt_answers_question_id ON attempt_answers (question_id);

COMMENT ON TABLE attempt_answers IS 'Lưu chi tiết từng câu trả lời, kết quả chấm tự động và feedback từ AI Tutor';

-- -----------------------------------------------------------------------------
-- 2.8 Bảng: anti_cheat_logs (Nhật ký giám sát hành vi gian lận)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS anti_cheat_logs (
    id            uuid        NOT NULL DEFAULT gen_random_uuid(),
    attempt_id    uuid        NOT NULL,
    event_type    varchar(50) NOT NULL,
    logged_at     timestamptz NOT NULL DEFAULT now(),
    metadata_info jsonb,
    CONSTRAINT pk_anti_cheat_logs PRIMARY KEY (id),
    CONSTRAINT fk_anti_cheat_logs_attempt_id_exam_attempts FOREIGN KEY (attempt_id) REFERENCES exam_attempts (id) ON DELETE CASCADE,
    CONSTRAINT ck_anti_cheat_logs_metadata_object CHECK (metadata_info IS NULL OR jsonb_typeof(metadata_info) = 'object')
);

CREATE INDEX IF NOT EXISTS ix_anti_cheat_logs_attempt_logged ON anti_cheat_logs (attempt_id, logged_at);

COMMENT ON TABLE anti_cheat_logs IS 'Ghi nhận chi tiết các vi phạm trong phòng thi: chuyển tab, rời khỏi cửa sổ, phím tắt';
