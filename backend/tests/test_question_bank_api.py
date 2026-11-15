import re
import unittest
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import operators
from sqlalchemy.sql.elements import BooleanClauseList

from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.models.entities import (
    Category,
    ExamAttempt,
    CognitiveLevel,
    Question,
    QuestionLevel,
    QuestionSource,
    QuestionType,
    Subject,
    User,
    UserRole,
)


def _matches(instance: Any, condition: Any, session: "MemorySession") -> bool:
    if isinstance(condition, BooleanClauseList):
        results = [_matches(instance, item, session) for item in condition.clauses]
        if condition.operator is operators.or_:
            return any(results)
        return all(results)

    left = condition.left
    expected = getattr(condition.right, "value", None)
    if left.table.name == "categories" and isinstance(instance, Question):
        instance = next(
            (item for item in session.categories if item.id == instance.category_id),
            None,
        )
        if instance is None:
            return False
    actual = getattr(instance, left.key)

    if condition.operator is operators.eq:
        return actual == expected
    if condition.operator is operators.ilike_op:
        pattern = re.escape(expected).replace("%", ".*").replace("_", ".")
        return re.fullmatch(pattern, actual or "", re.IGNORECASE | re.DOTALL) is not None
    if condition.operator is operators.contains_op:
        return expected[0] in actual
    raise AssertionError(f"Unsupported test filter operator: {condition.operator}")


class MemoryQuery:
    def __init__(self, session: "MemorySession", model: type):
        self.session = session
        self.model = model
        self.conditions: list[Any] = []

    def filter(self, *conditions: Any) -> "MemoryQuery":
        self.conditions.extend(conditions)
        return self

    def order_by(self, *_ordering: Any) -> "MemoryQuery":
        return self

    def with_for_update(self):
        return self

    def join(self, *args):
        return self

    def _rows(self) -> list[Any]:
        rows = self.session.rows_for(self.model)
        return [
            row
            for row in rows
            if all(_matches(row, condition, self.session) for condition in self.conditions)
        ]

    def first(self) -> Any:
        rows = self._rows()
        return rows[0] if rows else None

    def all(self) -> list[Any]:
        return self._rows()


class MemoryScalarResult:
    def __init__(self, rows: list[Any]):
        self.rows = rows

    def all(self) -> list[Any]:
        return self.rows


class MemorySession:
    def __init__(self):
        self.users: list[User] = []
        self.subjects: list[Subject] = []
        self.categories: list[Category] = []
        self.questions: list[Question] = []
        self.pending_add: list[Any] = []
        self.pending_delete: list[Any] = []
        self.commit_error: Exception | None = None
        self.commit_count = 0
        self.rollback_count = 0
        self.last_statement: Any = None

    def rows_for(self, model: type) -> list[Any]:
        return {
            User: self.users,
            Subject: self.subjects,
            Category: self.categories,
            Question: self.questions,
            ExamAttempt: [],
        }[model]

    def query(self, model: type) -> MemoryQuery:
        return MemoryQuery(self, model)

    def scalars(self, statement: Any) -> MemoryScalarResult:
        self.last_statement = statement
        rows = [
            question
            for question in self.questions
            if all(
                _matches(question, condition, self)
                for condition in statement._where_criteria
            )
        ]
        rows.sort(key=lambda question: (question.created_at, str(question.id)), reverse=True)
        if statement._offset_clause is not None:
            rows = rows[statement._offset_clause.value :]
        if statement._limit_clause is not None:
            rows = rows[: statement._limit_clause.value]
        return MemoryScalarResult(rows)

    def add(self, instance: Any) -> None:
        if getattr(instance, "id", None) is None:
            instance.id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        if getattr(instance, "created_at", None) is None:
            instance.created_at = now
        if getattr(instance, "updated_at", None) is None:
            instance.updated_at = now
        if isinstance(instance, Question) and instance.source_type is None:
            instance.source_type = QuestionSource.MANUAL
        self.pending_add.append(instance)

    def delete(self, instance: Any) -> None:
        self.pending_delete.append(instance)

    def commit(self) -> None:
        if self.commit_error is not None:
            error, self.commit_error = self.commit_error, None
            raise error
        for instance in self.pending_add:
            self.rows_for(type(instance)).append(instance)
        for instance in self.pending_delete:
            self.rows_for(type(instance)).remove(instance)
        self.pending_add.clear()
        self.pending_delete.clear()
        self.commit_count += 1

    def refresh(self, _instance: Any) -> None:
        return None

    def rollback(self) -> None:
        self.pending_add.clear()
        self.pending_delete.clear()
        self.rollback_count += 1

    def close(self) -> None:
        return None


class QuestionBankApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = MemorySession()
        self.instructor = self._add_user(UserRole.INSTRUCTOR)
        self.other_instructor = self._add_user(UserRole.INSTRUCTOR)
        self.student = self._add_user(UserRole.STUDENT)
        self.admin = self._add_user(UserRole.ADMIN)
        self.subject = self._add_subject(self.instructor)
        self.category = self._add_category(self.instructor, self.subject)
        self.question = self._add_question(
            self.instructor,
            self.category,
            content="What is the Scrum Daily event timebox?",
        )

        def override_get_db():
            yield self.db

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)
        self.instructor_headers = self._headers(self.instructor)
        self.admin_headers = self._headers(self.admin)
        self.student_headers = self._headers(self.student)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()
        self.client.close()

    def _add_user(self, role: UserRole) -> User:
        user = User(
            id=uuid.uuid4(),
            email=f"{role.value.lower()}-{uuid.uuid4()}@example.test",
            password_hash="test-hash",
            full_name="Test User",
            role=role,
            is_active=True,
        )
        self.db.users.append(user)
        return user

    def _add_subject(self, creator: User) -> Subject:
        subject = Subject(
            id=uuid.uuid4(),
            name=f"Subject {uuid.uuid4()}",
            description=None,
            created_by=creator.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.db.subjects.append(subject)
        return subject

    def _add_category(self, creator: User, subject: Subject) -> Category:
        category = Category(
            id=uuid.uuid4(),
            name=f"Topic {uuid.uuid4()}",
            description=None,
            subject_id=subject.id,
            created_by=creator.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.db.categories.append(category)
        return category

    def _add_question(
        self, creator: User, category: Category, content: str
    ) -> Question:
        question = Question(
            id=uuid.uuid4(),
            creator_id=creator.id,
            category_id=category.id,
            content=content,
            question_type=QuestionType.SINGLE_CHOICE,
            cognitive_level=CognitiveLevel.REMEMBER,
            level=QuestionLevel.MEDIUM,
            options=[
                {"id": "A", "text": "Correct", "is_correct": True},
                {"id": "B", "text": "Incorrect", "is_correct": False},
            ],
            tags=["scrum"],
            explanation="A sample explanation.",
            source_type=QuestionSource.MANUAL,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.db.questions.append(question)
        return question

    @staticmethod
    def _headers(user: User) -> dict[str, str]:
        token = create_access_token({"sub": str(user.id), "role": user.role.value})
        return {"Authorization": f"Bearer {token}"}

    @staticmethod
    def _question_payload(category_id: uuid.UUID, content: str = "New question") -> dict:
        return {
            "category_id": str(category_id),
            "content": content,
            "question_type": "SINGLE_CHOICE",
            "cognitive_level": "REMEMBER",
            "level": "EASY",
            "options": [
                {"id": "A", "text": "Correct", "is_correct": True},
                {"id": "B", "text": "Incorrect", "is_correct": False},
            ],
            "tags": ["unit-test"],
            "explanation": None,
        }

    def test_questions_require_authentication_and_allowed_role(self) -> None:
        path = "/api/v1/ai-generator/question-bank/questions"
        self.assertEqual(self.client.get(path).status_code, 401)
        self.assertEqual(
            self.client.get(path, headers=self.student_headers).status_code,
            403,
        )
        self.assertEqual(
            self.client.get(path, headers=self.instructor_headers).status_code,
            200,
        )

    def test_create_get_update_and_delete_question(self) -> None:
        path = "/api/v1/ai-generator/question-bank/questions"
        response = self.client.post(
            path,
            headers=self.instructor_headers,
            json=self._question_payload(self.category.id),
        )
        self.assertEqual(response.status_code, 201)
        created = response.json()["data"]
        question_id = created["id"]
        self.assertEqual(created["creator_id"], str(self.instructor.id))
        self.assertEqual(created["source_type"], "MANUAL")
        self.assertEqual(self.db.commit_count, 1)

        response = self.client.get(
            f"{path}/{question_id}",
            headers=self.instructor_headers,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["content"], "New question")

        response = self.client.patch(
            f"{path}/{question_id}",
            headers=self.instructor_headers,
            json={"content": "Updated question", "level": "HARD"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["content"], "Updated question")
        self.assertEqual(response.json()["data"]["level"], "HARD")

        response = self.client.delete(
            f"{path}/{question_id}",
            headers=self.instructor_headers,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["data"]["deleted"])
        self.assertNotIn(
            uuid.UUID(question_id),
            {question.id for question in self.db.questions},
        )

    def test_list_questions_applies_supported_filters_and_pagination(self) -> None:
        self._add_question(
            self.instructor,
            self.category,
            content="Another question about estimation",
        )
        response = self.client.get(
            "/api/v1/ai-generator/question-bank/questions",
            headers=self.instructor_headers,
            params={
                "keyword": "scrum",
                "category_id": str(self.category.id),
                "level": "MEDIUM",
                "cognitive_level": "REMEMBER",
                "skip": 0,
                "limit": 1,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["data"]), 1)
        self.assertIn("lower(questions.content) LIKE", str(self.db.last_statement))
        self.assertEqual(self.db.last_statement._limit_clause.value, 1)
        self.assertEqual(self.db.last_statement._offset_clause.value, 0)

    def test_instructor_cannot_access_another_instructors_question(self) -> None:
        response = self.client.get(
            f"/api/v1/ai-generator/question-bank/questions/{self.question.id}",
            headers=self._headers(self.other_instructor),
        )
        self.assertEqual(response.status_code, 404)

    def test_create_rejects_category_owned_by_another_instructor(self) -> None:
        response = self.client.post(
            "/api/v1/ai-generator/question-bank/questions",
            headers=self._headers(self.other_instructor),
            json=self._question_payload(self.category.id),
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(len(self.db.questions), 1)

    def test_update_revalidates_question_options(self) -> None:
        response = self.client.patch(
            f"/api/v1/ai-generator/question-bank/questions/{self.question.id}",
            headers=self.instructor_headers,
            json={
                "options": [
                    {"id": "A", "text": "First", "is_correct": False},
                    {"id": "B", "text": "Second", "is_correct": False},
                ]
            },
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.db.commit_count, 0)

    def test_delete_returns_conflict_when_database_rejects_foreign_key(self) -> None:
        self.db.commit_error = IntegrityError(
            "DELETE FROM questions",
            {},
            Exception("foreign key constraint"),
        )
        response = self.client.delete(
            f"/api/v1/ai-generator/question-bank/questions/{self.question.id}",
            headers=self.instructor_headers,
        )
        self.assertEqual(response.status_code, 409)
        self.assertIn(self.question, self.db.questions)
        self.assertEqual(self.db.rollback_count, 1)

    def test_parser_question_path_remains_as_compatibility_alias(self) -> None:
        response = self.client.get(
            "/api/v1/parser/questions",
            headers=self.instructor_headers,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"][0]["id"], str(self.question.id))

    def test_subject_and_category_endpoints_support_question_bank_ui(self) -> None:
        root = "/api/v1/ai-generator/question-bank"
        response = self.client.post(
            f"{root}/subjects",
            headers=self.instructor_headers,
            json={"name": "New subject", "description": None},
        )
        self.assertEqual(response.status_code, 201)
        subject_id = response.json()["data"]["id"]

        response = self.client.get(
            f"{root}/subjects",
            headers=self.instructor_headers,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(subject_id, {item["id"] for item in response.json()["data"]})

        response = self.client.post(
            f"{root}/categories",
            headers=self.instructor_headers,
            json={
                "name": "New topic",
                "description": None,
                "subject_id": subject_id,
            },
        )
        self.assertEqual(response.status_code, 201)
        category_id = response.json()["data"]["id"]

        response = self.client.patch(
            f"{root}/categories/{category_id}",
            headers=self.instructor_headers,
            json={"name": "Updated topic"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["name"], "Updated topic")

        response = self.client.get(
            f"{root}/categories",
            headers=self.instructor_headers,
            params={"subject_id": subject_id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["id"] for item in response.json()["data"]],
            [category_id],
        )

    def test_create_question_preserves_optional_file_parser_source_type(self) -> None:
        root = "/api/v1/ai-generator/question-bank"
        base_payload = {
            "category_id": str(self.category.id),
            "content": "Câu hỏi trích xuất từ đề thi mẫu",
            "question_type": "SINGLE_CHOICE",
            "cognitive_level": "REMEMBER",
            "level": "MEDIUM",
            "options": [
                {"id": "A", "text": "Đúng", "is_correct": True},
                {"id": "B", "text": "Sai", "is_correct": False},
            ],
            "tags": ["parser"],
            "explanation": "Giải thích mẫu",
        }
        default_res = self.client.post(
            f"{root}/questions",
            headers=self.instructor_headers,
            json=base_payload,
        )
        self.assertEqual(default_res.status_code, 201)
        self.assertEqual(default_res.json()["data"]["source_type"], "MANUAL")

        parser_res = self.client.post(
            f"{root}/questions",
            headers=self.instructor_headers,
            json={**base_payload, "source_type": "FILE_PARSER"},
        )
        self.assertEqual(parser_res.status_code, 201)
        self.assertEqual(parser_res.json()["data"]["source_type"], "FILE_PARSER")


if __name__ == "__main__":
    unittest.main()
