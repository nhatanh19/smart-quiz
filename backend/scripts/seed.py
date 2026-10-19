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

        print("🌱 Checking and seeding 3 sample questions (idempotent by (creator_id, content))...")
        sample_questions = [
            # 1. Single Choice - Bloom Remember (Nhận biết)
            {
                "category_id": category.id,
                "creator_id": instructor.id,
                "content": "WBS là viết tắt của cụm từ nào trong quản trị dự án?",
                "question_type": QuestionType.SINGLE_CHOICE,
                "cognitive_level": CognitiveLevel.REMEMBER,
                "options": [
                    {"id": "A", "text": "Work Breakdown Structure", "is_correct": True},
                    {"id": "B", "text": "Work Budget Schedule", "is_correct": False},
                    {"id": "C", "text": "Weekly Backlog Summary", "is_correct": False},
                    {"id": "D", "text": "Workflow Baseline System", "is_correct": False},
                ],
                "explanation": "WBS (Work Breakdown Structure) là cấu trúc phân rã công việc, chia phạm vi dự án thành các thành phần nhỏ hơn, dễ quản lý.",
                "source_type": QuestionSource.MANUAL,
            },
            # 2. Multiple Choice - Bloom Understand (Thông hiểu)
            {
                "category_id": category.id,
                "creator_id": instructor.id,
                "content": "Những phát biểu nào đúng về Quy tắc 100% khi xây dựng WBS?",
                "question_type": QuestionType.MULTIPLE_CHOICE,
                "cognitive_level": CognitiveLevel.UNDERSTAND,
                "options": [
                    {"id": "A", "text": "WBS phải bao quát toàn bộ phạm vi dự án", "is_correct": True},
                    {"id": "B", "text": "Các thành phần con cộng lại phải đủ 100% công việc của thành phần cha", "is_correct": True},
                    {"id": "C", "text": "Được thêm công việc ngoài phạm vi nếu còn thời gian", "is_correct": False},
                    {"id": "D", "text": "WBS chỉ liệt kê các hoạt động hành chính", "is_correct": False},
                ],
                "explanation": "Quy tắc 100% yêu cầu WBS bao quát toàn bộ phạm vi và công việc của các thành phần con cộng lại đúng bằng 100% công việc của thành phần cha, không thừa, không thiếu.",
                "source_type": QuestionSource.MANUAL,
            },
            # 3. True/False - Bloom Apply (Vận dụng)
            {
                "category_id": category.id,
                "creator_id": instructor.id,
                "content": "Nhóm có 4 thành viên, ngân sách 0 USD, hạn chót cố định ở Tuần 13. Khách hàng đề nghị thêm chấm tự luận bằng AI. Đưa ngay vào phạm vi mà không đánh giá lại là phù hợp với kiểm soát phạm vi.",
                "question_type": QuestionType.TRUE_FALSE,
                "cognitive_level": CognitiveLevel.APPLY,
                "options": [
                    {"id": "A", "text": "Đúng", "is_correct": False},
                    {"id": "B", "text": "Sai", "is_correct": True},
                ],
                "explanation": "Mọi yêu cầu mới phải được đánh giá tác động lên phạm vi, thời gian, chi phí và nguồn lực. Đưa thẳng vào phạm vi gây trượt phạm vi (scope creep).",
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
                print(f"  ℹ️ Demo exam already exists: '{existing_exam.title}' [{existing_exam.exam_code}]")

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
