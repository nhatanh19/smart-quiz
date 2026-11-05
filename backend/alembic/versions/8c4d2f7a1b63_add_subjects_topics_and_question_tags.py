"""Add subjects, topic ownership, and question tags.

Revision ID: 8c4d2f7a1b63
Revises: 2a6f1c8b3d90
Create Date: 2026-10-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "8c4d2f7a1b63"
down_revision: Union[str, None] = "2a6f1c8b3d90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "subjects",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name="fk_subjects_created_by_users",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_subjects"),
        sa.UniqueConstraint(
            "created_by",
            "name",
            name="created_by_name",
        ),
    )
    op.create_index(
        "ix_subjects_created_by",
        "subjects",
        ["created_by"],
        unique=False,
    )
    op.add_column(
        "categories",
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_categories_subject_id_subjects",
        "categories",
        "subjects",
        ["subject_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_categories_subject_id",
        "categories",
        ["subject_id"],
        unique=False,
    )
    op.drop_constraint(
        op.f("uq_categories_created_by_name"),
        "categories",
        type_="unique",
    )
    op.create_unique_constraint(
        "created_by_subject_name",
        "categories",
        ["created_by", "subject_id", "name"],
    )
    op.add_column(
        "questions",
        sa.Column(
            "tags",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "tags_is_array",
        "questions",
        "jsonb_typeof(tags) = 'array'",
    )
    op.create_index(
        "ix_questions_tags",
        "questions",
        ["tags"],
        unique=False,
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("ix_questions_tags", table_name="questions")
    op.drop_constraint(
        op.f("ck_questions_tags_is_array"),
        "questions",
        type_="check",
    )
    op.drop_column("questions", "tags")
    op.drop_index("ix_categories_subject_id", table_name="categories")
    op.drop_constraint(
        op.f("uq_categories_created_by_subject_name"),
        "categories",
        type_="unique",
    )
    op.create_unique_constraint(
        "created_by_name",
        "categories",
        ["created_by", "name"],
    )
    op.drop_constraint(
        "fk_categories_subject_id_subjects",
        "categories",
        type_="foreignkey",
    )
    op.drop_column("categories", "subject_id")
    op.drop_index("ix_subjects_created_by", table_name="subjects")
    op.drop_table("subjects")
