-- =============================================================================
-- SMART QUIZ - INITIAL SEED DATA (SQL SCRIPT)
-- Dự án: Smart Quiz — Nền tảng kiểm tra và ôn luyện trắc nghiệm trực tuyến AI
-- Mật khẩu mặc định cho cả 3 tài khoản là: SmartQuiz@123
-- Hash Bcrypt: $2b$12$7QHre7gKe/R9TumW91FQv.t0/5c2gvxx6oEE8QUeCt05JxnVpTKeO
-- =============================================================================

-- 1. NẠP TÀI KHOẢN MẪU (ADMIN, INSTRUCTOR, STUDENT)
INSERT INTO users (id, email, password_hash, full_name, role, is_active)
VALUES
    (
        'c1a0c4f8-1d2e-4b9a-8c5e-0f1a2b3c4d5e',
        'admin@smartquiz.edu.vn',
        '$2b$12$7QHre7gKe/R9TumW91FQv.t0/5c2gvxx6oEE8QUeCt05JxnVpTKeO',
        'Quản trị viên',
        'ADMIN',
        true
    ),
    (
        'e2b1d5a9-2e3f-4c0b-9d6f-1a2b3c4d5e6f',
        'instructor@smartquiz.edu.vn',
        '$2b$12$7QHre7gKe/R9TumW91FQv.t0/5c2gvxx6oEE8QUeCt05JxnVpTKeO',
        'Giảng viên Mẫu',
        'INSTRUCTOR',
        true
    ),
    (
        'f3c2e6b0-3f4a-5d1c-0e7a-2b3c4d5e6f7a',
        'student@smartquiz.edu.vn',
        '$2b$12$7QHre7gKe/R9TumW91FQv.t0/5c2gvxx6oEE8QUeCt05JxnVpTKeO',
        'Sinh viên Mẫu',
        'STUDENT',
        true
    )
ON CONFLICT (email) DO NOTHING;

-- 2. NẠP CHUYÊN ĐỀ MẪU
INSERT INTO categories (id, name, description, created_by)
SELECT
    '7f05b51d-17c6-474b-8af1-338f43f3f035',
    'Quản trị Dự án Phần mềm',
    'Ngân hàng câu hỏi chuyên đề Quản trị Dự án Phần mềm phục vụ ôn tập và thi',
    u.id
FROM users u WHERE u.email = 'instructor@smartquiz.edu.vn'
ON CONFLICT DO NOTHING;

-- 3. NẠP CÂU HỎI MẪU (3 CẤP ĐỘ BLOOM: REMEMBER, UNDERSTAND, APPLY)
INSERT INTO questions (id, category_id, creator_id, content, question_type, cognitive_level, options, explanation, source_type)
SELECT
    'd9862108-11ab-4cf8-8435-129165b4bb63',
    '7f05b51d-17c6-474b-8af1-338f43f3f035',
    u.id,
    'Trong quản trị dự án phần mềm, WBS là viết tắt của thuật ngữ nào?',
    'SINGLE_CHOICE',
    'REMEMBER',
    '[
        {"id": "A", "text": "Work Breakdown Structure", "is_correct": true},
        {"id": "B", "text": "Work Budget Schedule", "is_correct": false},
        {"id": "C", "text": "Weekly Backlog Summary", "is_correct": false},
        {"id": "D", "text": "Workflow Baseline System", "is_correct": false}
    ]'::jsonb,
    'WBS (Work Breakdown Structure) là cấu trúc phân chia công việc theo cấp bậc.',
    'MANUAL'
FROM users u WHERE u.email = 'instructor@smartquiz.edu.vn'
ON CONFLICT DO NOTHING;

INSERT INTO questions (id, category_id, creator_id, content, question_type, cognitive_level, options, explanation, source_type)
SELECT
    '1d38526c-e53f-4d5f-9d83-8dc1c32d8286',
    '7f05b51d-17c6-474b-8af1-338f43f3f035',
    u.id,
    'Mục đích cốt lõi của việc xác định đường găng (Critical Path) trong sơ đồ mạng dự án là gì?',
    'SINGLE_CHOICE',
    'UNDERSTAND',
    '[
        {"id": "A", "text": "Xác định chuỗi công việc dài nhất quyết định tổng thời gian dự án", "is_correct": true},
        {"id": "B", "text": "Tìm ra các công việc có thể trì hoãn vô thời hạn", "is_correct": false},
        {"id": "C", "text": "Giảm thiểu chi phí nhân công xuống mức thấp nhất", "is_correct": false},
        {"id": "D", "text": "Tự động phân bổ lại ngân sách dự toán", "is_correct": false}
    ]'::jsonb,
    'Đường găng là chuỗi các công việc có độ trễ bằng 0, chậm trễ ở đường găng sẽ kéo dài toàn bộ dự án.',
    'MANUAL'
FROM users u WHERE u.email = 'instructor@smartquiz.edu.vn'
ON CONFLICT DO NOTHING;

INSERT INTO questions (id, category_id, creator_id, content, question_type, cognitive_level, options, explanation, source_type)
SELECT
    'a8726514-9fa2-4c25-b286-f8eb04a377ec',
    '7f05b51d-17c6-474b-8af1-338f43f3f035',
    u.id,
    'Dự án có EV = $40,000 và PV = $50,000. Chỉ số SPI (Schedule Performance Index) đạt bao nhiêu và dự án đang ở tình trạng nào?',
    'SINGLE_CHOICE',
    'APPLY',
    '[
        {"id": "A", "text": "SPI = 0.8, dự án đang chậm tiến độ", "is_correct": true},
        {"id": "B", "text": "SPI = 1.25, dự án đang vượt tiến độ", "is_correct": false},
        {"id": "C", "text": "SPI = 0.8, dự án đang bội chi ngân sách", "is_correct": false},
        {"id": "D", "text": "SPI = 1.2, dự án hoàn thành đúng thời hạn", "is_correct": false}
    ]'::jsonb,
    'SPI = EV / PV = 40,000 / 50,000 = 0.8 (< 1) => Dự án đang chậm so với tiến độ cam kết.',
    'MANUAL'
FROM users u WHERE u.email = 'instructor@smartquiz.edu.vn'
ON CONFLICT DO NOTHING;

-- 4. NẠP KỲ THI MẪU (DEMO0001)
INSERT INTO exams (
    id, exam_code, title, description, instructor_id,
    duration_minutes, start_time, end_time, access_password_hash,
    max_attempts, max_tab_violations, shuffle_questions, shuffle_options,
    is_published, matrix_config
)
SELECT
    '3b9f1d82-e56c-49a3-a719-7023c4db026e',
    'DEMO0001',
    'Kiểm tra giữa kỳ Quản trị Dự án Phần mềm (Mẫu)',
    'Đề thi trắc nghiệm kiến thức tổng hợp WBS, Critical Path và Quản lý Giá trị Thu được (EVM).',
    u.id,
    45,
    now() - INTERVAL '1 day',
    now() + INTERVAL '30 days',
    NULL,
    2,
    3,
    true,
    true,
    true,
    '{
        "version": 1,
        "total_questions": 3,
        "category_ids": ["7f05b51d-17c6-474b-8af1-338f43f3f035"],
        "cognitive_distribution": {"REMEMBER": 1, "UNDERSTAND": 1, "APPLY": 1},
        "type_distribution": {"SINGLE_CHOICE": 3}
    }'::jsonb
FROM users u WHERE u.email = 'instructor@smartquiz.edu.vn'
ON CONFLICT (exam_code) DO NOTHING;

-- 5. GẮN CÂU HỎI VÀO ĐỀ THI MẪU (EXAM_QUESTIONS)
INSERT INTO exam_questions (id, exam_id, question_id, order_index, points)
SELECT
    '9a12c845-1234-4567-89ab-cdef01234567',
    e.id,
    'd9862108-11ab-4cf8-8435-129165b4bb63',
    1,
    3.33
FROM exams e
WHERE e.exam_code = 'DEMO0001'
  AND NOT EXISTS (
      SELECT 1 FROM exam_questions eq
      WHERE eq.exam_id = e.id AND (eq.question_id = 'd9862108-11ab-4cf8-8435-129165b4bb63' OR eq.order_index = 1)
  );

INSERT INTO exam_questions (id, exam_id, question_id, order_index, points)
SELECT
    '9a12c845-1234-4567-89ab-cdef01234568',
    e.id,
    '1d38526c-e53f-4d5f-9d83-8dc1c32d8286',
    2,
    3.33
FROM exams e
WHERE e.exam_code = 'DEMO0001'
  AND NOT EXISTS (
      SELECT 1 FROM exam_questions eq
      WHERE eq.exam_id = e.id AND (eq.question_id = '1d38526c-e53f-4d5f-9d83-8dc1c32d8286' OR eq.order_index = 2)
  );

INSERT INTO exam_questions (id, exam_id, question_id, order_index, points)
SELECT
    '9a12c845-1234-4567-89ab-cdef01234569',
    e.id,
    'a8726514-9fa2-4c25-b286-f8eb04a377ec',
    3,
    3.34
FROM exams e
WHERE e.exam_code = 'DEMO0001'
  AND NOT EXISTS (
      SELECT 1 FROM exam_questions eq
      WHERE eq.exam_id = e.id AND (eq.question_id = 'a8726514-9fa2-4c25-b286-f8eb04a377ec' OR eq.order_index = 3)
  );
