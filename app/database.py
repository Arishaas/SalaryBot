from app.config import get_settings

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

_settings = get_settings()

DATABASE_URL = _settings.database_url

# 👇 фикс для sqlite
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# 👇 ЛОГ — чтобы видеть куда создаётся БД
print("USING DATABASE:", DATABASE_URL)

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()