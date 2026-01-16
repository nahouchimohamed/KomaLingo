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
                conn.execute(text("ALTER TABLE chapter_jobs ADD COLUMN translate_provider VARCHAR(32)"))
            if "translate_api_key" not in cols:
                conn.execute(text("ALTER TABLE chapter_jobs ADD COLUMN translate_api_key VARCHAR(256)"))
            if "processing_mode" not in cols:
                conn.execute(
                    text("ALTER TABLE chapter_jobs ADD COLUMN processing_mode VARCHAR(32) DEFAULT 'full'")
                )
            for column, ddl in {
                "cancel_requested": "ALTER TABLE chapter_jobs ADD COLUMN cancel_requested BOOLEAN DEFAULT 0",
                "resume_from_page": "ALTER TABLE chapter_jobs ADD COLUMN resume_from_page INTEGER DEFAULT 0",
                "font_name": "ALTER TABLE chapter_jobs ADD COLUMN font_name VARCHAR(64)",
                "glossary_json": "ALTER TABLE chapter_jobs ADD COLUMN glossary_json TEXT",
                "skip_sfx": "ALTER TABLE chapter_jobs ADD COLUMN skip_sfx BOOLEAN DEFAULT 0",
                "failed_pages": "ALTER TABLE chapter_jobs ADD COLUMN failed_pages INTEGER DEFAULT 0",
            }.items():
                if column not in cols:
                    conn.execute(text(ddl))
            conn.commit()
