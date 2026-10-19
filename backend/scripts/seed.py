import argparse
import os
import sys
from datetime import datetime, timedelta, timezone

# Ensure UTF-8 output on Windows console
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.entities import (
    Category,
    CognitiveLevel,
    Exam,
    ExamQuestion,
    Question,
    QuestionSource,
    QuestionType,
    User,
    UserRole,
)


def seed_data(with_demo_exam: bool = False) -> None:
    """Initialize baseline sample data following Section 6 specifications."""
    db: Session = SessionLocal()
    try:
        print("🌱 Checking and seeding users (idempotent)...")
        default_password = getattr(settings, "SEED_DEFAULT_PASSWORD", "SmartQuiz@123")
        hashed_password = get_password_hash(default_password)

        users_to_seed = [
            {
                "email": "admin@smartquiz.edu.vn",
                "full_name": "Quản trị viên",
                "role": UserRole.ADMIN,
                "password_hash": hashed_password,
                "is_active": True,
            },
            {
                "email": "instructor@smartquiz.edu.vn",
                "full_name": "Giảng viên Mẫu",
                "role": UserRole.INSTRUCTOR,
                "password_hash": hashed_password,
                "is_active": True,
            },
            {
                "email": "student@smartquiz.edu.vn",
                "full_name": "Sinh viên Mẫu",
                "role": UserRole.STUDENT,
                "password_hash": hashed_password,
                "is_active": True,
            },
        ]

        seeded_users = {}
        for u_data in users_to_seed:
            existing_user = db.query(User).filter(User.email == u_data["email"]).first()
            if not existing_user:
                new_user = User(**u_data)
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                seeded_users[new_user.role] = new_user
                print(f"  ✅ Created user: {new_user.email} [{new_user.role.value}] (ID: {new_user.id})")
            else:
                seeded_users[existing_user.role] = existing_user
                print(f"  ℹ️ User already exists: {existing_user.email} [{existing_user.role.value}] (ID: {existing_user.id})")

        instructor = seeded_users.get(UserRole.INSTRUCTOR)
        if not instructor:
            instructor = db.query(User).filter(User.role == UserRole.INSTRUCTOR).first()

        print("🌱 Checking and seeding category (idempotent by (created_by, name))...")
        category_name = "Quản trị Dự án Phần mềm"
        category = (
            db.query(Category)
            .filter(
                Category.created_by == instructor.id,
                Category.name == category_name,
            )
            .first()
        )
        if not category:
            category = Category(
                name=category_name,
                description="Chuyên đề mẫu phục vụ kiểm thử hệ thống.",
                created_by=instructor.id,
            )
            db.add(category)
            db.commit()
            db.refresh(category)
            print(f"  ✅ Created category: '{category.name}' (ID: {category.id})")
        else:
            print(f"  ℹ️ Category already exists: '{category.name}' (ID: {category.id})")

        print("🌱 Checking and seeding 10 sample questions (idempotent by (creator_id, content))...")
        sample_questions = [
            # 1. Single Choice - Bloom Remember (Nhận biết)
            {
                "category_id": category.id,
                "creator_id": instructor.id,
                "content": "Trong quản trị dự án phần mềm, WBS là viết tắt của thuật ngữ nào?",
                "question_type": QuestionType.SINGLE_CHOICE,
                "cognitive_level": CognitiveLevel.REMEMBER,
                "options": [
                    {"id": "A", "text": "Work Breakdown Structure", "is_correct": True},
                    {"id": "B", "text": "Work Budget Schedule", "is_correct": False},
                    {"id": "C", "text": "Weekly Backlog Summary", "is_correct": False},
                    {"id": "D", "text": "Workflow Baseline System", "is_correct": False},
                ],
                "explanation": "WBS (Work Breakdown Structure) là cấu trúc phân rã công việc định hướng sản phẩm bàn giao, chia phạm vi dự án thành các gói công việc nhỏ hơn.",
                "source_type": QuestionSource.MANUAL,
            },
            # 2. Single Choice - Bloom Understand (Thông hiểu)
            {
                "category_id": category.id,
                "creator_id": instructor.id,
                "content": "Mục đích cốt lõi của việc xác định đường găng (Critical Path) trong sơ đồ mạng dự án là gì?",
                "question_type": QuestionType.SINGLE_CHOICE,
                "cognitive_level": CognitiveLevel.UNDERSTAND,
                "options": [
                    {"id": "A", "text": "Xác định chuỗi công việc dài nhất quyết định tổng thời gian hoàn thành dự án", "is_correct": True},
                    {"id": "B", "text": "Tìm ra các công việc có thể trì hoãn vô thời hạn", "is_correct": False},
                    {"id": "C", "text": "Giảm thiểu chi phí nhân công xuống mức thấp nhất", "is_correct": False},
                    {"id": "D", "text": "Tự động phân bổ lại ngân sách dự toán", "is_correct": False},
                ],
                "explanation": "Đường găng là chuỗi các công việc có độ trễ bằng 0 (Zero Float). Bất kỳ sự chậm trễ nào trên đường găng đều làm chậm tiến độ toàn dự án.",
                "source_type": QuestionSource.MANUAL,
            },
            # 3. Single Choice - Bloom Apply (Vận dụng)
            {
                "category_id": category.id,
                "creator_id": instructor.id,
                "content": "Dự án có Giá trị thu được EV = $40,000 và Giá trị kế hoạch PV = $50,000. Chỉ số hiệu suất tiến độ SPI đạt bao nhiêu và dự án đang ở tình trạng nào?",
                "question_type": QuestionType.SINGLE_CHOICE,
                "cognitive_level": CognitiveLevel.APPLY,
                "options": [
                    {"id": "A", "text": "SPI = 0.8, dự án đang chậm tiến độ", "is_correct": True},
                    {"id": "B", "text": "SPI = 1.25, dự án đang vượt tiến độ", "is_correct": False},
                    {"id": "C", "text": "SPI = 0.8, dự án đang bội chi ngân sách", "is_correct": False},
                    {"id": "D", "text": "SPI = 1.2, dự án hoàn thành đúng thời hạn", "is_correct": False},
                ],
                "explanation": "SPI = EV / PV = 40,000 / 50,000 = 0.8 (< 1) chứng tỏ tiến độ thực tế đang chậm so với kế hoạch đã cam kết.",
                "source_type": QuestionSource.MANUAL,
            },
            # 4. Single Choice - Bloom Remember (Nhận biết)
            {
                "category_id": category.id,
                "creator_id": instructor.id,
                "content": "Trong khung làm việc Scrum, cuộc họp hàng ngày (Daily Scrum) thường được giới hạn thời gian (timebox) tối đa là bao lâu?",
                "question_type": QuestionType.SINGLE_CHOICE,
                "cognitive_level": CognitiveLevel.REMEMBER,
                "options": [
                    {"id": "A", "text": "15 phút", "is_correct": True},
                    {"id": "B", "text": "30 phút", "is_correct": False},
                    {"id": "C", "text": "45 phút", "is_correct": False},
                    {"id": "D", "text": "60 phút", "is_correct": False},
                ],
                "explanation": "Theo Scrum Guide, Daily Scrum diễn ra hàng ngày với thời lượng tối đa 15 phút để nhóm đồng bộ tiến độ và nhận diện khó khăn.",
                "source_type": QuestionSource.MANUAL,
            },
            # 5. Multiple Choice - Bloom Understand (Thông hiểu)
            {
                "category_id": category.id,
                "creator_id": instructor.id,
                "content": "Những hoạt động nào sau đây thuộc nhóm quy trình Khởi tạo dự án (Initiating Process Group) theo chuẩn PMBOK?",
                "question_type": QuestionType.MULTIPLE_CHOICE,
                "cognitive_level": CognitiveLevel.UNDERSTAND,
                "options": [
                    {"id": "A", "text": "Phát triển Điều lệ Dự án (Develop Project Charter)", "is_correct": True},
                    {"id": "B", "text": "Xác định các bên liên quan (Identify Stakeholders)", "is_correct": True},
                    {"id": "C", "text": "Tạo cấu trúc phân rã công việc (Create WBS)", "is_correct": False},
                    {"id": "D", "text": "Kiểm soát chi phí dự án (Control Costs)", "is_correct": False},
                ],
                "explanation": "Nhóm quy trình Khởi tạo trong PMBOK chỉ bao gồm 2 quy trình: Phát triển Điều lệ Dự án và Nhận diện Các bên liên quan.",
                "source_type": QuestionSource.MANUAL,
            },
            # 6. Single Choice - Bloom Apply (Vận dụng)
            {
                "category_id": category.id,
                "creator_id": instructor.id,
                "content": "Một dự án phần mềm có EV = $80,000 và Chi phí thực tế AC = $100,000. Chỉ số hiệu suất chi phí CPI đạt bao nhiêu và đánh giá hiệu quả chi phí ra sao?",
                "question_type": QuestionType.SINGLE_CHOICE,
                "cognitive_level": CognitiveLevel.APPLY,
                "options": [
                    {"id": "A", "text": "CPI = 0.8, dự án đang bội chi (vượt ngân sách)", "is_correct": True},
                    {"id": "B", "text": "CPI = 1.25, dự án đang tiết kiệm ngân sách", "is_correct": False},
                    {"id": "C", "text": "CPI = 0.8, dự án đang chậm tiến độ", "is_correct": False},
                    {"id": "D", "text": "CPI = -20,000, chi phí không xác định", "is_correct": False},
                ],
                "explanation": "CPI = EV / AC = 80,000 / 100,000 = 0.8 (< 1) thể hiện chi phí thực tế vượt quá giá trị công việc hoàn thành (bội chi ngân sách).",
                "source_type": QuestionSource.MANUAL,
            },
            # 7. Single Choice - Bloom Remember (Nhận biết)
            {
                "category_id": category.id,
                "creator_id": instructor.id,
                "content": "Biểu đồ Gantt (Gantt Chart) trong quản lý dự án phần mềm chủ yếu được sử dụng nhằm mục đích gì?",
                "question_type": QuestionType.SINGLE_CHOICE,
                "cognitive_level": CognitiveLevel.REMEMBER,
                "options": [
                    {"id": "A", "text": "Trực quan hóa lịch trình, thời lượng và sự phụ thuộc giữa các công việc", "is_correct": True},
                    {"id": "B", "text": "Ước tính rủi ro bảo mật mã nguồn", "is_correct": False},
                    {"id": "C", "text": "Đo lường mức độ hài lòng của khách hàng", "is_correct": False},
                    {"id": "D", "text": "Phân tích cú pháp ngôn ngữ lập trình", "is_correct": False},
                ],
                "explanation": "Biểu đồ Gantt trực quan hóa các hạng mục công việc dưới dạng thanh ngang theo trục thời gian, thể hiện rõ tiến độ và mối quan hệ phụ thuộc.",
                "source_type": QuestionSource.MANUAL,
            },
            # 8. True/False - Bloom Understand (Thông hiểu)
            {
                "category_id": category.id,
                "creator_id": instructor.id,
                "content": "Đường găng (Critical Path) của một dự án luôn cố định và không bao giờ thay đổi trong suốt vòng đời dự án.",
                "question_type": QuestionType.TRUE_FALSE,
                "cognitive_level": CognitiveLevel.UNDERSTAND,
                "options": [
                    {"id": "A", "text": "Đúng", "is_correct": False},
                    {"id": "B", "text": "Sai", "is_correct": True},
                ],
                "explanation": "Phát biểu này Sai vì khi các công việc ngoài đường găng bị chậm trễ vượt quá độ trễ cho phép (Total Float), chúng có thể trở thành đường găng mới.",
                "source_type": QuestionSource.MANUAL,
            },
            # 9. Single Choice - Bloom Apply (Vận dụng)
            {
                "category_id": category.id,
                "creator_id": instructor.id,
                "content": "Theo kỹ thuật ước lượng 3 điểm PERT, một công việc có thời gian lạc quan O = 4 ngày, khả năng cao nhất M = 7 ngày, bi quan P = 16 ngày. Thời gian kỳ vọng Te bằng bao nhiêu ngày?",
                "question_type": QuestionType.SINGLE_CHOICE,
                "cognitive_level": CognitiveLevel.APPLY,
                "options": [
                    {"id": "A", "text": "8 ngày", "is_correct": True},
                    {"id": "B", "text": "9 ngày", "is_correct": False},
                    {"id": "C", "text": "7 ngày", "is_correct": False},
                    {"id": "D", "text": "10 ngày", "is_correct": False},
                ],
                "explanation": "Công thức Beta PERT: Te = (O + 4M + P) / 6 = (4 + 4*7 + 16) / 6 = (4 + 28 + 16) / 6 = 48 / 6 = 8 ngày.",
                "source_type": QuestionSource.MANUAL,
            },
            # 10. Multiple Choice - Bloom Understand (Thông hiểu)
            {
                "category_id": category.id,
                "creator_id": instructor.id,
                "content": "Các chiến lược ứng phó với rủi ro tiêu cực (Threats) trong dự án phần mềm theo PMBOK bao gồm những phương án nào?",
                "question_type": QuestionType.MULTIPLE_CHOICE,
                "cognitive_level": CognitiveLevel.UNDERSTAND,
                "options": [
                    {"id": "A", "text": "Né tránh (Avoidance)", "is_correct": True},
                    {"id": "B", "text": "Giảm thiểu (Mitigation)", "is_correct": True},
                    {"id": "C", "text": "Chuyển giao (Transference)", "is_correct": True},
                    {"id": "D", "text": "Khai thác (Exploit)", "is_correct": False},
                ],
                "explanation": "Avoidance, Mitigation, Transference và Acceptance là các chiến lược đối phó rủi ro tiêu cực. Khai thác (Exploit) là chiến lược dành cho cơ hội (rủi ro tích cực).",
                "source_type": QuestionSource.MANUAL,
            },
        ]

        seeded_questions = []
        for q_data in sample_questions:
            existing_q = (
                db.query(Question)
                .filter(
                    Question.creator_id == q_data["creator_id"],
                    Question.content == q_data["content"],
                )
                .first()
            )
            if not existing_q:
                new_q = Question(**q_data)
                db.add(new_q)
                db.commit()
                db.refresh(new_q)
                seeded_questions.append(new_q)
                print(
                    f"  ✅ Created question [{new_q.question_type.value} - {new_q.cognitive_level.value}]: {new_q.content[:50]}... (ID: {new_q.id})"
                )
            else:
                seeded_questions.append(existing_q)
                print(
                    f"  ℹ️ Question already exists [{existing_q.question_type.value}]: {existing_q.content[:50]}... (ID: {existing_q.id})"
                )

        if with_demo_exam:
            print("🌱 Checking and seeding Demo Exam (--with-demo-exam)...")
            exam_code = "DEMO0001"
            existing_exam = db.query(Exam).filter(Exam.exam_code == exam_code).first()
            now = datetime.now(timezone.utc)
            if not existing_exam:
                demo_exam = Exam(
                    exam_code=exam_code,
                    title="Đề thi mẫu",
                    instructor_id=instructor.id,
                    duration_minutes=15,
                    start_time=now - timedelta(days=1),
                    end_time=now + timedelta(days=30),
                    access_password_hash=None,
                    is_published=True,
                )
                db.add(demo_exam)
                db.commit()
                db.refresh(demo_exam)
                print(f"  ✅ Created demo exam: '{demo_exam.title}' [{demo_exam.exam_code}] (ID: {demo_exam.id})")

                for idx, q in enumerate(seeded_questions, start=1):
                    eq = ExamQuestion(
                        exam_id=demo_exam.id,
                        question_id=q.id,
                        order_index=idx,
                        points=1.0,
                    )
                    db.add(eq)
                db.commit()
                print(f"  ✅ Added {len(seeded_questions)} questions to demo exam.")
            else:
                current_q_ids = {eq.question_id for eq in existing_exam.exam_questions}
                max_order = max([eq.order_index for eq in existing_exam.exam_questions] or [0])
                added = 0
                for q in seeded_questions:
                    if q.id not in current_q_ids:
                        max_order += 1
                        eq = ExamQuestion(
                            exam_id=existing_exam.id,
                            question_id=q.id,
                            order_index=max_order,
                            points=1.0,
                        )
                        db.add(eq)
                        added += 1
                if added > 0:
                    db.commit()
                    print(f"  ✅ Added {added} missing questions to existing demo exam.")
                else:
                    print(f"  ℹ️ Demo exam already exists with all questions: '{existing_exam.title}' [{existing_exam.exam_code}]")

        print("✨ Database seed completed successfully!")

    except Exception as exc:
        db.rollback()
        print(f"❌ Error during seed execution: {exc}")
        raise exc
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Seed database for Smart Quiz")
    parser.add_argument(
        "--with-demo-exam",
        action="store_true",
        help="Seed an additional published demo exam with the 3 sample questions",
    )
    args = parser.parse_args()
    seed_data(with_demo_exam=args.with_demo_exam)


if __name__ == "__main__":
    main()
