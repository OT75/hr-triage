from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    """Every table class inherits from this, so SQLAlchemy knows about it."""


def get_db(): 
    """Give one request (API CALL) its own session, and always close it afterwards."""
    db = SessionLocal() # ┐ half 1: runs BEFORE your endpoint
    try:                # │
        yield db        # ┘ pause: hand `db` to the endpoint, wait here
    finally:
        db.close()      # ← half 2: runs AFTER your endpoint is finished