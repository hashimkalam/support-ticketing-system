from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

engine = create_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    # Recycle below typical proxy/idle timeouts so we never hand out a dead socket.
    pool_recycle=settings.db_pool_recycle,
    # Validates a pooled connection before use (Postgres restarts, failovers).
    pool_pre_ping=True,
    echo=settings.db_echo,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


def create_tables() -> None:
    from app import models  # imported late: models depend on Base

    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
