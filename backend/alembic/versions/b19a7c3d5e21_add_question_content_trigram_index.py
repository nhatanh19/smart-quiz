"""Add trigram index for question content search.

Revision ID: b19a7c3d5e21
Revises: 8c4d2f7a1b63
Create Date: 2026-10-29

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b19a7c3d5e21"
down_revision: Union[str, None] = "8c4d2f7a1b63"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.create_index(
        "ix_questions_content_trgm",
        "questions",
        ["content"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"content": "gin_trgm_ops"},
    )


def downgrade() -> None:
    op.drop_index("ix_questions_content_trgm", table_name="questions")
