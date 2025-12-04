# backend/models.py
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, JSON, create_engine, func
)
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./events.db")

Base = declarative_base()

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, default="unknown")
    type = Column(String, default="unknown")
    confidence = Column(Float, default=0.0)
    # store as "lat,lon" string for simplicity, or JSON with {"lat":..., "lon":...}
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    audio_key = Column(String, nullable=True)
    video_key = Column(String, nullable=True)
    speed = Column(Float, nullable=True)
    accel_peak = Column(Float, nullable=True)
    metadata = Column(JSON, default={})
    status = Column(String, default="sent")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

def init_db():
    # Using SQLAlchemy engine to create tables
    engine = create_engine(DATABASE_URL, echo=False, future=True)
    Base.metadata.create_all(bind=engine)
    return engine

# helper session factory
engine = init_db()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
