"""Alert endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional, List
from datetime import datetime

from ..database import get_db
from ..schemas import AlertResponse, AlertAckRequest, AlertAckResponse
from ..utils import get_alert_status, get_alert_severity_display

router = APIRouter(prefix="/api", tags=["Alerts"])


@router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity level"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of alerts"),
    db: AsyncSession = Depends(get_db)
):
    """Get alerts with filtering options."""
    try:
        params = {"limit": limit}
        severity_clause = ""
        
        if severity:
            severity_clause = "AND a.severity = :severity"
            params["severity"] = severity
        
        query = text(f"""
            SELECT
                a.*,
                z.name as zone_name,
                z.code as zone_code
            FROM alerts a
            JOIN zones z ON a.zone_id = z.id
            WHERE a.created_at >= NOW() - INTERVAL '72 hours'
            {severity_clause}
            ORDER BY a.created_at DESC
            LIMIT :limit
        """)
        
        result = await db.execute(query, params)
        rows = result.fetchall()
        
        alerts = []
        for row in rows:
            metadata = getattr(row, "meta", None) or {}
            row_dict = {
                'resolved': row.resolved,
                'acknowledged': row.acknowledged,
            }
            
            timestamp = row.created_at
            if isinstance(timestamp, datetime):
                timestamp = timestamp.isoformat()
            
            alerts.append({
                "id": metadata.get('externalId', str(row.id)),
                "zoneId": row.zone_code,
                "severity": get_alert_severity_display(row.severity),
                "type": "Crew" if row.alert_type == "crew" else "System",
                "crewId": metadata.get('crewId'),
                "title": row.title,
                "description": row.message,
                "eta": metadata.get('eta'),
                "status": metadata.get('status') or get_alert_status(row_dict),
                "timestamp": timestamp,
            })
        
        return alerts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch alerts: {str(e)}")


@router.post("/alerts/{id}/ack", response_model=AlertAckResponse)
async def acknowledge_alert(
    id: str,
    request: AlertAckRequest,
    db: AsyncSession = Depends(get_db)
):
    """Mark an alert as acknowledged."""
    try:
        query = text("""
            UPDATE alerts
            SET acknowledged = true,
                acknowledged_by = :acknowledged_by,
                acknowledged_at = NOW()
            WHERE id::text = :id OR metadata->>'externalId' = :id
            RETURNING *
        """)
        
        result = await db.execute(query, {
            "acknowledged_by": request.acknowledgedBy or "system",
            "id": id
        })
        row = result.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        await db.commit()
        
        return {
            "success": True,
            "message": "Alert acknowledged successfully",
            "alert": {"id": str(row.id)}
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to acknowledge alert: {str(e)}")
