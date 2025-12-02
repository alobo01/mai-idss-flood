"""Health check and system endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime

from ..database import get_db
from ..schemas import HealthResponse, ErrorResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check(db: AsyncSession = Depends(get_db)):
    """Check API health and database connectivity."""
    try:
        result = await db.execute(text("SELECT NOW() as time, version() as version"))
        row = result.fetchone()
        return HealthResponse(
            status="ok",
            timestamp=row.time,
            database="connected",
            version="2.0.0"
        )
    except Exception as e:
        return HealthResponse(
            status="error",
            timestamp=datetime.utcnow(),
            database="disconnected",
            version="2.0.0"
        )
