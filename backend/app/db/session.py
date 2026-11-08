from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.core.config import settings

Base = declarative_base()

def get_engine():
    try:
        # Attempt PostgreSQL connection
        engine = create_engine(settings.sync_database_url, pool_pre_ping=True)
        with engine.connect() as conn:
            pass
        return engine
    except Exception:
        # Fallback to local SQLite engine so local testing runs without external Docker
        return create_engine(
            settings.fallback_sqlite_url,
            connect_args={"check_same_thread": False}
        )

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
