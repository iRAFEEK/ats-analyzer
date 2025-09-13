"""Database configuration and session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ats_analyzer.core.config import get_settings
from ats_analyzer.models.base import Base

settings = get_settings()

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    pool_pre_ping=True,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)
