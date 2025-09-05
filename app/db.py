from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .config import settings

engine = create_engine(settings.database_url, connect_args={"sslmode": "require"})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency for database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class ScrapedData(Base):
    __tablename__ = "scraped_data"
    id = Column(Integer, primary_key=True)
    url = Column(String)
    content = Column(Text)
    embedding = Column(Vector(settings.vector_dimension))
    scraped_at = Column(DateTime, default=datetime.now(timezone.utc))
