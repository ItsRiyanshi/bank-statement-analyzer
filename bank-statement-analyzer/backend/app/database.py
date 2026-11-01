"""
Database setup via SQLAlchemy. Supports PostgreSQL in production and SQLite for local development.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import DATABASE_URL

# Normalize legacy postgres:// connection schemes from cloud providers to postgresql://
normalized_db_url = DATABASE_URL
if normalized_db_url.startswith("postgres://"):
    normalized_db_url = normalized_db_url.replace("postgres://", "postgresql://", 1)

if "sqlite" in normalized_db_url:
    connect_args = {"check_same_thread": False}
    engine = create_engine(normalized_db_url, connect_args=connect_args)
else:
    # Production PostgreSQL with connection testing on checkout (handles idle disconnects)
    engine = create_engine(normalized_db_url, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
