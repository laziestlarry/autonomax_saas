from __future__ import annotations
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from .settings import settings

class Base(DeclarativeBase):
    pass

def _default_sqlite() -> str:
    # ephemeral (container filesystem) for dev; in production prefer Postgres
    return "sqlite+pysqlite:////tmp/autonomax.db"

DATABASE_URL = settings.database_url or _default_sqlite()

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
