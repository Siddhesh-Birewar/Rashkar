from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.db.session import get_db
from backend.app.core.timezone import now_ist, now_utc, format_ist_iso
from backend.app.core.config import settings

router = APIRouter()

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "database": db_status,
        "timezone": settings.TIMEZONE,
        "time_local_ist": format_ist_iso(now_ist()),
        "time_utc": now_utc().isoformat()
    }
