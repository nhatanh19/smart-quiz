"""Add question difficulty level.

Revision ID: 2a6f1c8b3d90
Revises: 0f9c708382a2
Create Date: 2026-10-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "2a6f1c8b3d90"
down_revision: Union[str, None] = "0f9c708382a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    question_level = postgresql.ENUM(
        "EASY",
        "MEDIUM",
        "HARD",
        name="question_level",
        create_type=False,
    )
    question_level.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "questions",
        sa.Column(
            "level",
            question_level,
            server_default="MEDIUM",
            nullable=False,
        ),
    )
    op.create_index(
        "ix_questions_category_level",
        "questions",
        ["category_id", "level"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_questions_category_level", table_name="questions")
    op.drop_column("questions", "level")
    postgresql.ENUM(name="question_level").drop(op.get_bind(), checkfirst=True)
