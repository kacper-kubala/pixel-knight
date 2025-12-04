"""Database configuration and models for PostgreSQL."""
import os
from datetime import datetime
from typing import Optional, List, Any
from contextlib import asynccontextmanager

from sqlalchemy import Column, String, Text, Float, Integer, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.pool import NullPool

from .config import settings


# Database URL - supports both PostgreSQL and SQLite
DATABASE_URL = os.getenv("DATABASE_URL", settings.database_url)

# For PostgreSQL, convert to async URL if needed
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)


# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    poolclass=NullPool if "sqlite" in DATABASE_URL else None,
)

# Session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""
    pass


class DBSession(Base):
    """Database model for chat sessions."""
    __tablename__ = "sessions"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    model = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # LLM Parameters
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=2048)
    system_prompt = Column(Text, default="You are a helpful AI assistant.")
    
    # Usage tracking
    total_tokens_used = Column(Integer, default=0)
    
    # Relationships
    messages = relationship("DBMessage", back_populates="session", cascade="all, delete-orphan")


class DBMessage(Base):
    """Database model for chat messages."""
    __tablename__ = "messages"
    
    id = Column(String(36), primary_key=True)
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    sources = Column(JSON, nullable=True)  # Store sources as JSON
    token_count = Column(Integer, nullable=True)
    
    # Relationships
    session = relationship("DBSession", back_populates="messages")


class DBPreset(Base):
    """Database model for custom presets."""
    __tablename__ = "presets"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    system_prompt = Column(Text, nullable=False)
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=2048)
    icon = Column(String(10), default="📝")
    category = Column(String(50), default="custom")
    created_at = Column(DateTime, default=datetime.utcnow)


class DBUsage(Base):
    """Database model for tracking usage statistics."""
    __tablename__ = "usage"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, default=datetime.utcnow)
    tokens_used = Column(Integer, default=0)
    requests_count = Column(Integer, default=0)
    model = Column(String(255), nullable=True)


class DBRAGIndex(Base):
    """Database model for RAG indexed files."""
    __tablename__ = "rag_index"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    directory_path = Column(String(500), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    indexed_at = Column(DateTime, default=datetime.utcnow)
    content_hash = Column(String(64), nullable=True)


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """Get a database session."""
    async with async_session_maker() as session:
        yield session


@asynccontextmanager
async def get_db_session():
    """Context manager for database sessions."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# Flag to check if database is available
_db_available = None


async def check_db_available() -> bool:
    """Check if database connection is available."""
    global _db_available
    if _db_available is not None:
        return _db_available
    
    try:
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        _db_available = True
    except Exception as e:
        print(f"Database not available: {e}")
        _db_available = False
    
    return _db_available


def is_db_configured() -> bool:
    """Check if database is configured (not default SQLite)."""
    return "postgresql" in DATABASE_URL.lower()

