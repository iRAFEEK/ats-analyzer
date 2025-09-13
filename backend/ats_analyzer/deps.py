"""FastAPI dependencies."""

from typing import Generator

from sqlalchemy.orm import Session

from ats_analyzer.db import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Get database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
