from typing import Generator
from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# Explicit naming convention for database constraints and indexes (Section 2)
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(constraint_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


# Base class for SQLAlchemy 2.0 ORM models with standardized constraint naming
class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


# Database engine with automatic reconnection pool pinging
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)

# Session factory configured with expire_on_commit=False (Section 4)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI Dependency providing a transactional database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
