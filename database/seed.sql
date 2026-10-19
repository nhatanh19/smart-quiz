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

-- 3. NẠP 10 CÂU HỎI MẪU (ĐỦ 3 CẤP ĐỘ BLOOM VÀ 3 DẠNG CÂU HỎI)

-- Câu 1 (Single Choice - Remember)
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
    'WBS (Work Breakdown Structure) là cấu trúc phân rã công việc định hướng sản phẩm bàn giao, chia phạm vi dự án thành các gói công việc nhỏ hơn.',
    'MANUAL'
FROM users u WHERE u.email = 'instructor@smartquiz.edu.vn'
ON CONFLICT DO NOTHING;

-- Câu 2 (Single Choice - Understand)
INSERT INTO questions (id, category_id, creator_id, content, question_type, cognitive_level, options, explanation, source_type)
SELECT
    '1d38526c-e53f-4d5f-9d83-8dc1c32d8286',
    '7f05b51d-17c6-474b-8af1-338f43f3f035',
    u.id,
    'Mục đích cốt lõi của việc xác định đường găng (Critical Path) trong sơ đồ mạng dự án là gì?',
    'SINGLE_CHOICE',
    'UNDERSTAND',
    '[
        {"id": "A", "text": "Xác định chuỗi công việc dài nhất quyết định tổng thời gian hoàn thành dự án", "is_correct": true},
        {"id": "B", "text": "Tìm ra các công việc có thể trì hoãn vô thời hạn", "is_correct": false},
        {"id": "C", "text": "Giảm thiểu chi phí nhân công xuống mức thấp nhất", "is_correct": false},
        {"id": "D", "text": "Tự động phân bổ lại ngân sách dự toán", "is_correct": false}
    ]'::jsonb,
    'Đường găng là chuỗi các công việc có độ trễ bằng 0 (Zero Float). Bất kỳ sự chậm trễ nào trên đường găng đều làm chậm tiến độ toàn dự án.',
    'MANUAL'
FROM users u WHERE u.email = 'instructor@smartquiz.edu.vn'
ON CONFLICT DO NOTHING;

-- Câu 3 (Single Choice - Apply)
INSERT INTO questions (id, category_id, creator_id, content, question_type, cognitive_level, options, explanation, source_type)
SELECT
    'a8726514-9fa2-4c25-b286-f8eb04a377ec',
    '7f05b51d-17c6-474b-8af1-338f43f3f035',
    u.id,
    'Dự án có Giá trị thu được EV = $40,000 và Giá trị kế hoạch PV = $50,000. Chỉ số hiệu suất tiến độ SPI đạt bao nhiêu và dự án đang ở tình trạng nào?',
    'SINGLE_CHOICE',
    'APPLY',
    '[
        {"id": "A", "text": "SPI = 0.8, dự án đang chậm tiến độ", "is_correct": true},
        {"id": "B", "text": "SPI = 1.25, dự án đang vượt tiến độ", "is_correct": false},
        {"id": "C", "text": "SPI = 0.8, dự án đang bội chi ngân sách", "is_correct": false},
        {"id": "D", "text": "SPI = 1.2, dự án hoàn thành đúng thời hạn", "is_correct": false}
    ]'::jsonb,
    'SPI = EV / PV = 40,000 / 50,000 = 0.8 (< 1) chứng tỏ tiến độ thực tế đang chậm so với kế hoạch đã cam kết.',
    'MANUAL'
FROM users u WHERE u.email = 'instructor@smartquiz.edu.vn'
ON CONFLICT DO NOTHING;

-- Câu 4 (Single Choice - Remember)
INSERT INTO questions (id, category_id, creator_id, content, question_type, cognitive_level, options, explanation, source_type)
SELECT
    'b5e192c3-4d5e-4a6b-8c7d-0e1f2a3b4c5d',
    '7f05b51d-17c6-474b-8af1-338f43f3f035',
    u.id,
    'Trong khung làm việc Scrum, cuộc họp hàng ngày (Daily Scrum) thường được giới hạn thời gian (timebox) tối đa là bao lâu?',
    'SINGLE_CHOICE',
    'REMEMBER',
    '[
        {"id": "A", "text": "15 phút", "is_correct": true},
        {"id": "B", "text": "30 phút", "is_correct": false},
        {"id": "C", "text": "45 phút", "is_correct": false},
        {"id": "D", "text": "60 phút", "is_correct": false}
    ]'::jsonb,
    'Theo Scrum Guide, Daily Scrum diễn ra hàng ngày với thời lượng tối đa 15 phút để nhóm đồng bộ tiến độ và nhận diện khó khăn.',
    'MANUAL'
FROM users u WHERE u.email = 'instructor@smartquiz.edu.vn'
ON CONFLICT DO NOTHING;

-- Câu 5 (Multiple Choice - Understand)
INSERT INTO questions (id, category_id, creator_id, content, question_type, cognitive_level, options, explanation, source_type)
SELECT
    'c6f203d4-5e6f-4b7c-9d8e-1f2a3b4c5d6e',
    '7f05b51d-17c6-474b-8af1-338f43f3f035',
    u.id,
    'Những hoạt động nào sau đây thuộc nhóm quy trình Khởi tạo dự án (Initiating Process Group) theo chuẩn PMBOK?',
    'MULTIPLE_CHOICE',
    'UNDERSTAND',
    '[
        {"id": "A", "text": "Phát triển Điều lệ Dự án (Develop Project Charter)", "is_correct": true},
        {"id": "B", "text": "Xác định các bên liên quan (Identify Stakeholders)", "is_correct": true},
        {"id": "C", "text": "Tạo cấu trúc phân rã công việc (Create WBS)", "is_correct": false},
        {"id": "D", "text": "Kiểm soát chi phí dự án (Control Costs)", "is_correct": false}
    ]'::jsonb,
    'Nhóm quy trình Khởi tạo trong PMBOK chỉ bao gồm 2 quy trình: Phát triển Điều lệ Dự án và Nhận diện Các bên liên quan.',
    'MANUAL'
FROM users u WHERE u.email = 'instructor@smartquiz.edu.vn'
ON CONFLICT DO NOTHING;

-- Câu 6 (Single Choice - Apply)
INSERT INTO questions (id, category_id, creator_id, content, question_type, cognitive_level, options, explanation, source_type)
SELECT
    'd7a314e5-6f7a-4c8d-0e9f-2a3b4c5d6e7f',
    '7f05b51d-17c6-474b-8af1-338f43f3f035',
    u.id,
    'Một dự án phần mềm có EV = $80,000 và Chi phí thực tế AC = $100,000. Chỉ số hiệu suất chi phí CPI đạt bao nhiêu và đánh giá hiệu quả chi phí ra sao?',
    'SINGLE_CHOICE',
    'APPLY',
    '[
        {"id": "A", "text": "CPI = 0.8, dự án đang bội chi (vượt ngân sách)", "is_correct": true},
        {"id": "B", "text": "CPI = 1.25, dự án đang tiết kiệm ngân sách", "is_correct": false},
        {"id": "C", "text": "CPI = 0.8, dự án đang chậm tiến độ", "is_correct": false},
        {"id": "D", "text": "CPI = -20,000, chi phí không xác định", "is_correct": false}
    ]'::jsonb,
    'CPI = EV / AC = 80,000 / 100,000 = 0.8 (< 1) thể hiện chi phí thực tế vượt quá giá trị công việc hoàn thành (bội chi ngân sách).',
    'MANUAL'
FROM users u WHERE u.email = 'instructor@smartquiz.edu.vn'
ON CONFLICT DO NOTHING;

-- Câu 7 (Single Choice - Remember)
INSERT INTO questions (id, category_id, creator_id, content, question_type, cognitive_level, options, explanation, source_type)
SELECT
    'e8b425f6-7a8b-4d9e-1f0a-3b4c5d6e7f8a',
    '7f05b51d-17c6-474b-8af1-338f43f3f035',
    u.id,
    'Biểu đồ Gantt (Gantt Chart) trong quản lý dự án phần mềm chủ yếu được sử dụng nhằm mục đích gì?',
    'SINGLE_CHOICE',
    'REMEMBER',
    '[
        {"id": "A", "text": "Trực quan hóa lịch trình, thời lượng và sự phụ thuộc giữa các công việc", "is_correct": true},
        {"id": "B", "text": "Ước tính rủi ro bảo mật mã nguồn", "is_correct": false},
        {"id": "C", "text": "Đo lường mức độ hài lòng của khách hàng", "is_correct": false},
        {"id": "D", "text": "Phân tích cú pháp ngôn ngữ lập trình", "is_correct": false}
    ]'::jsonb,
    'Biểu đồ Gantt trực quan hóa các hạng mục công việc dưới dạng thanh ngang theo trục thời gian, thể hiện rõ tiến độ và mối quan hệ phụ thuộc.',
    'MANUAL'
FROM users u WHERE u.email = 'instructor@smartquiz.edu.vn'
ON CONFLICT DO NOTHING;

-- Câu 8 (True/False - Understand)
INSERT INTO questions (id, category_id, creator_id, content, question_type, cognitive_level, options, explanation, source_type)
SELECT
    'f9c536a7-8b9c-4e0f-2a1b-4c5d6e7f8a9b',
    '7f05b51d-17c6-474b-8af1-338f43f3f035',
    u.id,
    'Đường găng (Critical Path) của một dự án luôn cố định và không bao giờ thay đổi trong suốt vòng đời dự án.',
    'TRUE_FALSE',
    'UNDERSTAND',
    '[
        {"id": "A", "text": "Đúng", "is_correct": false},
        {"id": "B", "text": "Sai", "is_correct": true}
    ]'::jsonb,
    'Phát biểu này Sai vì khi các công việc ngoài đường găng bị chậm trễ vượt quá độ trễ cho phép (Total Float), chúng có thể trở thành đường găng mới.',
    'MANUAL'
FROM users u WHERE u.email = 'instructor@smartquiz.edu.vn'
ON CONFLICT DO NOTHING;

-- Câu 9 (Single Choice - Apply)
INSERT INTO questions (id, category_id, creator_id, content, question_type, cognitive_level, options, explanation, source_type)
SELECT
    'a0d647b8-9c0d-4f1a-3b2c-5d6e7f8a9b0c',
    '7f05b51d-17c6-474b-8af1-338f43f3f035',
    u.id,
    'Theo kỹ thuật ước lượng 3 điểm PERT, một công việc có thời gian lạc quan O = 4 ngày, khả năng cao nhất M = 7 ngày, bi quan P = 16 ngày. Thời gian kỳ vọng Te bằng bao nhiêu ngày?',
    'SINGLE_CHOICE',
    'APPLY',
    '[
        {"id": "A", "text": "8 ngày", "is_correct": true},
        {"id": "B", "text": "9 ngày", "is_correct": false},
        {"id": "C", "text": "7 ngày", "is_correct": false},
        {"id": "D", "text": "10 ngày", "is_correct": false}
    ]'::jsonb,
    'Công thức Beta PERT: Te = (O + 4M + P) / 6 = (4 + 4*7 + 16) / 6 = (4 + 28 + 16) / 6 = 48 / 6 = 8 ngày.',
    'MANUAL'
FROM users u WHERE u.email = 'instructor@smartquiz.edu.vn'
ON CONFLICT DO NOTHING;

-- Câu 10 (Multiple Choice - Understand)
INSERT INTO questions (id, category_id, creator_id, content, question_type, cognitive_level, options, explanation, source_type)
SELECT
    'b1e758c9-0d1e-4a2b-4c3d-6e7f8a9b0c1d',
    '7f05b51d-17c6-474b-8af1-338f43f3f035',
    u.id,
    'Các chiến lược ứng phó với rủi ro tiêu cực (Threats) trong dự án phần mềm theo PMBOK bao gồm những phương án nào?',
    'MULTIPLE_CHOICE',
    'UNDERSTAND',
    '[
        {"id": "A", "text": "Né tránh (Avoidance)", "is_correct": true},
        {"id": "B", "text": "Giảm thiểu (Mitigation)", "is_correct": true},
        {"id": "C", "text": "Chuyển giao (Transference)", "is_correct": true},
        {"id": "D", "text": "Khai thác (Exploit)", "is_correct": false}
    ]'::jsonb,
    'Avoidance, Mitigation, Transference và Acceptance là các chiến lược đối phó rủi ro tiêu cực. Khai thác (Exploit) là chiến lược dành cho cơ hội (rủi ro tích cực).',
    'MANUAL'
FROM users u WHERE u.email = 'instructor@smartquiz.edu.vn'
ON CONFLICT DO NOTHING;

-- 4. NẠP KỲ THI MẪU (DEMO0001) VỚI CẤU HÌNH 10 CÂU HỎI
INSERT INTO exams (
    id, exam_code, title, description, instructor_id,
    duration_minutes, start_time, end_time, access_password_hash,
    max_attempts, max_tab_violations, shuffle_questions, shuffle_options,
    is_published, matrix_config
)
SELECT
    '3b9f1d82-e56c-49a3-a719-7023c4db026e',
    'DEMO0001',
    'Kiểm tra giữa kỳ Quản trị Dự án Phần mềm (Mẫu 10 câu)',
    'Đề thi trắc nghiệm kiến thức tổng hợp WBS, Critical Path, EVM, Scrum và Quản lý Rủi ro.',
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
        "total_questions": 10,
        "category_ids": ["7f05b51d-17c6-474b-8af1-338f43f3f035"],
        "cognitive_distribution": {"REMEMBER": 3, "UNDERSTAND": 4, "APPLY": 3},
        "type_distribution": {"SINGLE_CHOICE": 7, "MULTIPLE_CHOICE": 2, "TRUE_FALSE": 1}
    }'::jsonb
FROM users u WHERE u.email = 'instructor@smartquiz.edu.vn'
ON CONFLICT (exam_code) DO NOTHING;

-- 5. GẮN ĐỦ 10 CÂU HỎI VÀO ĐỀ THI MẪU (MỖI CÂU 1.0 ĐIỂM -> TỔNG 10.0 ĐIỂM)
INSERT INTO exam_questions (id, exam_id, question_id, order_index, points)
SELECT '9a12c845-1234-4567-89ab-cdef01234501', e.id, 'd9862108-11ab-4cf8-8435-129165b4bb63', 1, 1.0
FROM exams e WHERE e.exam_code = 'DEMO0001'
  AND NOT EXISTS (SELECT 1 FROM exam_questions eq WHERE eq.exam_id = e.id AND (eq.question_id = 'd9862108-11ab-4cf8-8435-129165b4bb63' OR eq.order_index = 1));

INSERT INTO exam_questions (id, exam_id, question_id, order_index, points)
SELECT '9a12c845-1234-4567-89ab-cdef01234502', e.id, '1d38526c-e53f-4d5f-9d83-8dc1c32d8286', 2, 1.0
FROM exams e WHERE e.exam_code = 'DEMO0001'
  AND NOT EXISTS (SELECT 1 FROM exam_questions eq WHERE eq.exam_id = e.id AND (eq.question_id = '1d38526c-e53f-4d5f-9d83-8dc1c32d8286' OR eq.order_index = 2));

INSERT INTO exam_questions (id, exam_id, question_id, order_index, points)
SELECT '9a12c845-1234-4567-89ab-cdef01234503', e.id, 'a8726514-9fa2-4c25-b286-f8eb04a377ec', 3, 1.0
FROM exams e WHERE e.exam_code = 'DEMO0001'
  AND NOT EXISTS (SELECT 1 FROM exam_questions eq WHERE eq.exam_id = e.id AND (eq.question_id = 'a8726514-9fa2-4c25-b286-f8eb04a377ec' OR eq.order_index = 3));

INSERT INTO exam_questions (id, exam_id, question_id, order_index, points)
SELECT '9a12c845-1234-4567-89ab-cdef01234504', e.id, 'b5e192c3-4d5e-4a6b-8c7d-0e1f2a3b4c5d', 4, 1.0
FROM exams e WHERE e.exam_code = 'DEMO0001'
  AND NOT EXISTS (SELECT 1 FROM exam_questions eq WHERE eq.exam_id = e.id AND (eq.question_id = 'b5e192c3-4d5e-4a6b-8c7d-0e1f2a3b4c5d' OR eq.order_index = 4));

INSERT INTO exam_questions (id, exam_id, question_id, order_index, points)
SELECT '9a12c845-1234-4567-89ab-cdef01234505', e.id, 'c6f203d4-5e6f-4b7c-9d8e-1f2a3b4c5d6e', 5, 1.0
FROM exams e WHERE e.exam_code = 'DEMO0001'
  AND NOT EXISTS (SELECT 1 FROM exam_questions eq WHERE eq.exam_id = e.id AND (eq.question_id = 'c6f203d4-5e6f-4b7c-9d8e-1f2a3b4c5d6e' OR eq.order_index = 5));

INSERT INTO exam_questions (id, exam_id, question_id, order_index, points)
SELECT '9a12c845-1234-4567-89ab-cdef01234506', e.id, 'd7a314e5-6f7a-4c8d-0e9f-2a3b4c5d6e7f', 6, 1.0
FROM exams e WHERE e.exam_code = 'DEMO0001'
  AND NOT EXISTS (SELECT 1 FROM exam_questions eq WHERE eq.exam_id = e.id AND (eq.question_id = 'd7a314e5-6f7a-4c8d-0e9f-2a3b4c5d6e7f' OR eq.order_index = 6));

INSERT INTO exam_questions (id, exam_id, question_id, order_index, points)
SELECT '9a12c845-1234-4567-89ab-cdef01234507', e.id, 'e8b425f6-7a8b-4d9e-1f0a-3b4c5d6e7f8a', 7, 1.0
FROM exams e WHERE e.exam_code = 'DEMO0001'
  AND NOT EXISTS (SELECT 1 FROM exam_questions eq WHERE eq.exam_id = e.id AND (eq.question_id = 'e8b425f6-7a8b-4d9e-1f0a-3b4c5d6e7f8a' OR eq.order_index = 7));

INSERT INTO exam_questions (id, exam_id, question_id, order_index, points)
SELECT '9a12c845-1234-4567-89ab-cdef01234508', e.id, 'f9c536a7-8b9c-4e0f-2a1b-4c5d6e7f8a9b', 8, 1.0
FROM exams e WHERE e.exam_code = 'DEMO0001'
  AND NOT EXISTS (SELECT 1 FROM exam_questions eq WHERE eq.exam_id = e.id AND (eq.question_id = 'f9c536a7-8b9c-4e0f-2a1b-4c5d6e7f8a9b' OR eq.order_index = 8));

INSERT INTO exam_questions (id, exam_id, question_id, order_index, points)
SELECT '9a12c845-1234-4567-89ab-cdef01234509', e.id, 'a0d647b8-9c0d-4f1a-3b2c-5d6e7f8a9b0c', 9, 1.0
FROM exams e WHERE e.exam_code = 'DEMO0001'
  AND NOT EXISTS (SELECT 1 FROM exam_questions eq WHERE eq.exam_id = e.id AND (eq.question_id = 'a0d647b8-9c0d-4f1a-3b2c-5d6e7f8a9b0c' OR eq.order_index = 9));

INSERT INTO exam_questions (id, exam_id, question_id, order_index, points)
SELECT '9a12c845-1234-4567-89ab-cdef01234510', e.id, 'b1e758c9-0d1e-4a2b-4c3d-6e7f8a9b0c1d', 10, 1.0
FROM exams e WHERE e.exam_code = 'DEMO0001'
  AND NOT EXISTS (SELECT 1 FROM exam_questions eq WHERE eq.exam_id = e.id AND (eq.question_id = 'b1e758c9-0d1e-4a2b-4c3d-6e7f8a9b0c1d' OR eq.order_index = 10));
