"""Auth tests default to SQLite; AUTH_TEST_DATABASE_URL enables real PostgreSQL.

PostgreSQL runs create and drop only a uniquely named temporary database, never
the database named in AUTH_TEST_DATABASE_URL. The login must have CREATEDB.
"""
import os
import sys
from pathlib import Path
from uuid import uuid4

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))
TEST_DATABASE_URL = os.environ.get("AUTH_TEST_DATABASE_URL")
os.environ["DATABASE_URL"] = TEST_DATABASE_URL or "sqlite://"

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.models.entities import User


@pytest.fixture(scope="session")
def auth_engine():
    if not TEST_DATABASE_URL:
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        User.__table__.create(engine)
        try:
            yield engine
        finally:
            engine.dispose()
        return

    url = make_url(TEST_DATABASE_URL)
    if url.get_backend_name() != "postgresql":
        raise ValueError("AUTH_TEST_DATABASE_URL must use PostgreSQL")
    database_name = f"smart_quiz_auth_test_{uuid4().hex}"
    admin_engine = create_engine(url, isolation_level="AUTOCOMMIT")
    engine = None
    created = False
    previous_url = settings.DATABASE_URL
    try:
        with admin_engine.connect() as connection:
            connection.execute(text(f'CREATE DATABASE "{database_name}"'))
        created = True
        temporary_url = url.set(database=database_name)
        settings.DATABASE_URL = temporary_url.render_as_string(hide_password=False)
        config = Config(str(BACKEND_ROOT / "alembic.ini"))
        config.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
        command.upgrade(config, "head")
        engine = create_engine(temporary_url, pool_pre_ping=True)
        yield engine
    finally:
        settings.DATABASE_URL = previous_url
        if engine is not None:
            engine.dispose()
        if created:
            with admin_engine.connect() as connection:
                connection.execute(text(f'DROP DATABASE "{database_name}" WITH (FORCE)'))
        admin_engine.dispose()
