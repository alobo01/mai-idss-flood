"""Database connection and session management."""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
import asyncio
from typing import AsyncGenerator

from .config import get_settings

settings = get_settings()

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=20,
    max_overflow=0,
    pool_timeout=30,
    pool_recycle=1800,
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def check_database_connection() -> bool:
    """Check if database is accessible."""
    try:
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
            return True
    except Exception:
        return False


async def wait_for_database(max_retries: int = 5, delay: int = 5) -> bool:
    """Wait for database to be available with retries."""
    for attempt in range(max_retries):
        try:
            async with async_session_maker() as session:
                await session.execute(text("SELECT NOW()"))
                print("Database connected successfully")
                return True
        except Exception as e:
            remaining = max_retries - attempt - 1
            print(f"Database connection failed (retries left: {remaining}): {e}")
            if remaining > 0:
                await asyncio.sleep(delay)
    
    print("Could not connect to database after multiple retries")
    return False
