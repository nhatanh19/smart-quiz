import os
import sys

# Ensure UTF-8 output on Windows console
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.entities import (
    User,
    UserRole,
    Category,
    Question,
    QuestionType,
    CognitiveLevel,
    QuestionSourceType,
)


def seed_data() -> None:
    """Initialize database tables and seed baseline sample data."""
    print("⏳ Creating database tables if they do not exist...")
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        print("🌱 Checking and seeding users...")
        default_password = "SmartQuiz@123"
        hashed_password = get_password_hash(default_password)

        users_to_seed = [
            {
                "email": "admin@smartquiz.edu.vn",
                "full_name": "Quản Trị Viên Hệ Thống",
                "role": UserRole.ADMIN,
                "password_hash": hashed_password,
                "is_active": True,
            },
            {
                "email": "instructor@smartquiz.edu.vn",
                "full_name": "Giảng Viên Hướng Dẫn",
                "role": UserRole.INSTRUCTOR,
                "password_hash": hashed_password,
                "is_active": True,
            },
            {
                "email": "student@smartquiz.edu.vn",
                "full_name": "Sinh Viên Tiêu Biểu",
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
                print(f"  ✅ Created user: {new_user.email} [{new_user.role.value}]")
            else:
                seeded_users[existing_user.role] = existing_user
                print(f"  ℹ️ User already exists: {existing_user.email} [{existing_user.role.value}]")

        instructor = seeded_users.get(UserRole.INSTRUCTOR)
        if not instructor:
            instructor = db.query(User).filter(User.role == UserRole.INSTRUCTOR).first()

        print("🌱 Checking and seeding sample category...")
        category_name = "Quản trị Dự án Phần mềm"
        category = db.query(Category).filter(Category.name == category_name).first()
        if not category:
            category = Category(
                name=category_name,
                description="Học phần trang bị kiến thức về quy trình quản lý dự án công nghệ, khung chuẩn PMBOK, mô hình Agile/Scrum, kiểm soát chất lượng, chi phí và thời gian.",
                created_by=instructor.id,
            )
            db.add(category)
            db.commit()
            db.refresh(category)
            print(f"  ✅ Created category: '{category.name}' (ID: {category.id})")
        else:
            print(f"  ℹ️ Category already exists: '{category.name}' (ID: {category.id})")

        print("🌱 Checking and seeding 3 sample questions (Single Choice, Multiple Choice, True/False)...")
        sample_questions = [
            # 1. Single Choice - Bloom Remember (Nhận biết)
            {
                "category_id": category.id,
                "creator_id": instructor.id,
                "content": "Trong phương pháp Quản trị Dự án theo Khung chuẩn PMBOK, WBS (Work Breakdown Structure) được định nghĩa là gì?",
                "question_type": QuestionType.SINGLE_CHOICE,
                "cognitive_level": CognitiveLevel.REMEMBER,
                "options": [
                    {
                        "id": "A",
                        "text": "Phân rã có thứ bậc mang tính định hướng sản phẩm bàn giao (Deliverable-oriented) về toàn bộ phạm vi dự án",
                        "is_correct": True,
                    },
                    {
                        "id": "B",
                        "text": "Biểu đồ phân bổ nguồn lực và nhân sự chi tiết của dự án theo từng ngày làm việc",
                        "is_correct": False,
                    },
                    {
                        "id": "C",
                        "text": "Danh mục tổng hợp các rủi ro kỹ thuật có thể xuất hiện trong quá trình phát triển mã nguồn",
                        "is_correct": False,
                    },
                    {
                        "id": "D",
                        "text": "Biểu đồ đường Gantt hiển thị tiến độ thực tế so với đường cơ sở tiến độ (Baseline)",
                        "is_correct": False,
                    },
                ],
                "explanation": "WBS là cấu trúc phân rã công việc có thứ bậc, định hướng sản phẩm bàn giao (Deliverable-oriented) thể hiện 100% phạm vi công việc cần thực hiện theo quy tắc 100% Rule.",
                "source_type": QuestionSourceType.MANUAL,
            },
            # 2. Multiple Choice - Bloom Understand (Thông hiểu)
            {
                "category_id": category.id,
                "creator_id": instructor.id,
                "content": "Những đặc trưng nào sau đây là đặc trưng cốt lõi của phương pháp phát triển phần mềm Agile/Scrum? (Chọn các đáp án đúng)",
                "question_type": QuestionType.MULTIPLE_CHOICE,
                "cognitive_level": CognitiveLevel.UNDERSTAND,
                "options": [
                    {
                        "id": "A",
                        "text": "Phát triển lặp (Iterative) và gia tăng (Incremental) theo các chu kỳ Sprint cố định từ 1-4 tuần",
                        "is_correct": True,
                    },
                    {
                        "id": "B",
                        "text": "Khóa cứng toàn bộ tài liệu đặc tả yêu cầu chi tiết ngay từ đầu dự án và nghiêm cấm mọi sự thay đổi",
                        "is_correct": False,
                    },
                    {
                        "id": "C",
                        "text": "Tập trung vào sự cộng tác thường xuyên với khách hàng thay vì chỉ đàm phán hợp đồng cứng nhắc",
                        "is_correct": True,
                    },
                    {
                        "id": "D",
                        "text": "Đội ngũ phát triển tự tổ chức (Self-organizing) và liên chức năng (Cross-functional)",
                        "is_correct": True,
                    },
                ],
                "explanation": "Tuyên ngôn Agile đề cao tương tác cá nhân, phần mềm chạy tốt, cộng tác khách hàng và phản hồi với thay đổi; mô hình Scrum chia nhỏ dự án thành các Sprint ngắn 1-4 tuần.",
                "source_type": QuestionSourceType.MANUAL,
            },
            # 3. True/False - Bloom Apply (Vận dụng)
            {
                "category_id": category.id,
                "creator_id": instructor.id,
                "content": "Tình huống: Khi một kỹ sư phát hiện rủi ro kiến trúc có nguy cơ khiến Sprint không đạt mục tiêu đã cam kết, Scrum Master nên tự quyết định âm thầm hủy bỏ tính năng mà không cần thảo luận với Product Owner và nhóm phát triển trong buổi Daily Scrum.",
                "question_type": QuestionType.TRUE_FALSE,
                "cognitive_level": CognitiveLevel.APPLY,
                "options": [
                    {
                        "id": "A",
                        "text": "Đúng",
                        "is_correct": False,
                    },
                    {
                        "id": "B",
                        "text": "Sai",
                        "is_correct": True,
                    },
                ],
                "explanation": "Sai. Trong Scrum, tính minh bạch (Transparency) và cộng tác là tối thượng. Chỉ có Product Owner mới có quyền ưu tiên lại hoặc điều chỉnh Product Backlog. Mọi trở ngại cần được minh bạch trong Daily Scrum để toàn đội cùng tìm giải pháp thích ứng.",
                "source_type": QuestionSourceType.MANUAL,
            },
        ]

        for q_data in sample_questions:
            existing_q = (
                db.query(Question)
                .filter(
                    Question.content == q_data["content"],
                    Question.category_id == q_data["category_id"],
                )
                .first()
            )
            if not existing_q:
                new_q = Question(**q_data)
                db.add(new_q)
                db.commit()
                db.refresh(new_q)
                print(
                    f"  ✅ Created question [{new_q.question_type.value} - {new_q.cognitive_level.value}]: {new_q.content[:60]}..."
                )
            else:
                print(
                    f"  ℹ️ Question already exists [{existing_q.question_type.value}]: {existing_q.content[:60]}..."
                )

        print("✨ Database seed completed successfully!")

    except Exception as exc:
        db.rollback()
        print(f"❌ Error during seed execution: {exc}")
        raise exc
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
