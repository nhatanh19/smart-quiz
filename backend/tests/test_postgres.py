"""Smoke checks for the migrated PostgreSQL schema, isolated by transaction."""
import json
import uuid

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import inspect, text
from sqlalchemy.exc import DataError, IntegrityError

from app.core.database import Base


@pytest.fixture
def postgres_connection(auth_engine):
    if auth_engine.dialect.name != "postgresql":
        pytest.skip("Set AUTH_TEST_DATABASE_URL to run PostgreSQL smoke tests")
    with auth_engine.connect() as connection:
        transaction = connection.begin()
        try:
            yield connection
        finally:
            transaction.rollback()


def test_migration_matches_models(postgres_connection):
    assert set(inspect(postgres_connection).get_table_names()) == set(Base.metadata.tables) | {"alembic_version"}
    context = MigrationContext.configure(postgres_connection, opts={
        "compare_type": True, "compare_server_default": True,
    })
    assert compare_metadata(context, Base.metadata) == []


def test_native_enum_and_database_constraints(postgres_connection):
    insert_user = text("""
        INSERT INTO users (email, password_hash, full_name, role)
        VALUES (:email, 'test-only-hash', 'PostgreSQL smoke test', :role)
    """)
    with pytest.raises(DataError) as invalid_role:
        with postgres_connection.begin_nested():
            postgres_connection.execute(insert_user, {"email": "smoke@example.com", "role": "ADMINISTRATOR"})
    assert invalid_role.value.orig.pgcode == "22P02"
    with pytest.raises(IntegrityError) as invalid_email:
        with postgres_connection.begin_nested():
            postgres_connection.execute(insert_user, {"email": "UPPER@example.com", "role": "STUDENT"})
    assert invalid_email.value.orig.diag.constraint_name == "ck_users_email_lowercase"


def test_jsonb_round_trip_and_options_constraint(postgres_connection):
    user_id = postgres_connection.execute(text("""
        INSERT INTO users (email, password_hash, full_name, role)
        VALUES ('jsonb@example.com', 'test-only-hash', 'JSONB smoke test', 'INSTRUCTOR') RETURNING id
    """)).scalar_one()
    assert isinstance(user_id, uuid.UUID)
    category_id = postgres_connection.execute(text("""
        INSERT INTO categories (name, created_by) VALUES ('Smoke category', :user_id) RETURNING id
    """), {"user_id": user_id}).scalar_one()
    insert_question = text("""
        INSERT INTO questions (category_id, creator_id, content, question_type, cognitive_level, options)
        VALUES (:category_id, :user_id, 'Unicode: Câu hỏi thử nghiệm', 'SINGLE_CHOICE', 'REMEMBER', CAST(:options AS jsonb))
        RETURNING options, pg_typeof(options)::text
    """)
    options = [{"id": "A", "text": "Đúng", "is_correct": True},
               {"id": "B", "text": "Sai", "is_correct": False}]
    params = {"category_id": category_id, "user_id": user_id, "options": json.dumps(options)}
    stored, column_type = postgres_connection.execute(insert_question, params).one()
    assert stored == options
    assert column_type == "jsonb"
    with pytest.raises(IntegrityError) as invalid_options:
        with postgres_connection.begin_nested():
            postgres_connection.execute(insert_question, {**params, "options": "[]"})
    assert invalid_options.value.orig.diag.constraint_name == "ck_questions_options_is_array"
