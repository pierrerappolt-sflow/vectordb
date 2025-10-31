"""Database connection management with SQLAlchemy async engine and session maker."""

import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine


class DatabaseSessionManager:
    """Manages database engine and session factory.

    This is a singleton that creates one engine and one session maker
    for the entire application, preventing connection pool exhaustion.
    """

    _engine: AsyncEngine | None = None
    _session_maker: async_sessionmaker[AsyncSession] | None = None

    @classmethod
    def get_engine(cls) -> AsyncEngine:
        """Get or create the SQLAlchemy async engine (singleton)."""
        if cls._engine is None:
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                msg = "DATABASE_URL environment variable required"
                raise ValueError(msg)

            # SQLAlchemy requires postgresql+asyncpg://
            if database_url.startswith("postgresql://"):
                database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

            cls._engine = create_async_engine(
                database_url,
                echo=False,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,  # Verify connections before using
                pool_recycle=3600,  # Recycle connections after 1 hour
            )

        return cls._engine

    @classmethod
    def get_session_maker(cls) -> async_sessionmaker[AsyncSession]:
        """Get or create the async session maker (singleton)."""
        if cls._session_maker is None:
            engine = cls.get_engine()
            cls._session_maker = async_sessionmaker(
                engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )

        return cls._session_maker

    @classmethod
    async def close(cls) -> None:
        """Close the engine and clean up connections (call on shutdown)."""
        if cls._engine:
            await cls._engine.dispose()
            cls._engine = None
            cls._session_maker = None


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database sessions.

    Usage:
        async for session in get_async_session():
            # Use session
            pass
    """
    session_maker = DatabaseSessionManager.get_session_maker()
    async with session_maker() as session:
        yield session
