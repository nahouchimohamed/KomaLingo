from collections.abc import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


if settings.database_url.startswith("sqlite"):
    # WAL lets the API read live job progress while the worker writes pages

    @event.listens_for(engine, "connect")
    def _sqlite_pragma(dbapi_connection, _connection_record) -> None:  # type: ignore[no-untyped-def]
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    if settings.database_url.startswith("sqlite"):
        with engine.connect() as conn:
            conn.execute(text("PRAGMA journal_mode=WAL"))
            # Lightweight additive migrations for existing SQLite files
            cols = {
                row[1]
                for row in conn.execute(text("PRAGMA table_info(chapter_jobs)")).fetchall()
            }
            if "translate_provider" not in cols:
                conn.execute(text("ALTER TABLE chapter_jobs ADD COLUMN translate_provider VARCHAR(32)"))  # additive
            if "translate_api_key" not in cols:
                conn.execute(text("ALTER TABLE chapter_jobs ADD COLUMN translate_api_key VARCHAR(256)"))
            conn.commit()
