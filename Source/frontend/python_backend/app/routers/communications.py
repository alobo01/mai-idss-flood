"""Communication endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional, List
from datetime import datetime
import random
import string
import time

from ..database import get_db
from ..schemas import CommunicationResponse, CommunicationCreate, CommunicationCreateResponse

router = APIRouter(prefix="/api", tags=["Communications"])


def generate_comm_id() -> str:
    """Generate a unique communication ID."""
    timestamp = int(time.time() * 1000)
    random_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"COMM-{timestamp}-{random_part}"


@router.get("/comms")
async def get_communications(
    channel: Optional[str] = Query(None, description="Filter by channel"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    limit: int = Query(200, ge=1, le=500, description="Maximum number of results"),
    db: AsyncSession = Depends(get_db)
):
    """Get communications with optional filters."""
    try:
        params = {"limit": min(max(limit, 1), 500)}
        clauses = []
        
        if channel:
            clauses.append("channel = :channel")
            params["channel"] = channel
        
        if priority:
            clauses.append("LOWER(priority) = LOWER(:priority)")
            params["priority"] = priority
        
        where_clause = ""
        if clauses:
            where_clause = "WHERE " + " AND ".join(clauses)
        
        query = text(f"""
            SELECT id, channel, sender, recipient, priority, message, created_at, metadata
            FROM communications
            {where_clause}
            ORDER BY created_at DESC
            LIMIT :limit
        """)
        
        result = await db.execute(query, params)
        rows = result.fetchall()
        
        communications = []
        for row in rows:
            metadata = getattr(row, "meta", None) or {}
            timestamp = row.created_at
            if isinstance(timestamp, datetime):
                timestamp = timestamp.isoformat()
            
            communications.append({
                "id": metadata.get('externalId', str(row.id)),
                "channel": row.channel,
                "from": row.sender,
                "to": row.recipient,
                "priority": row.priority,
                "text": row.message,
                "timestamp": timestamp,
            })
        
        return communications
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch communications: {str(e)}")


@router.post("/comms", status_code=201)
async def create_communication(
    request: CommunicationCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new communication record."""
    try:
        # Get data from request, handling alias
        channel = request.channel
        sender = request.from_
        text_content = request.text
        recipient = request.to or channel
        
        # Validate priority
        allowed_priorities = ['low', 'normal', 'high', 'urgent']
        priority = request.priority.lower() if request.priority else 'normal'
        if priority not in allowed_priorities:
            priority = 'normal'
        
        # Validate direction
        direction = 'inbound' if request.direction == 'inbound' else 'outbound'
        
        external_id = generate_comm_id()
        
        query = text("""
            INSERT INTO communications (channel, sender, recipient, message, direction, priority, status, metadata)
            VALUES (:channel, :sender, :recipient, :message, :direction, :priority, 'sent', CAST(:metadata AS jsonb))
            RETURNING created_at, priority, recipient, direction
        """)
        
        import json
        result = await db.execute(query, {
            "channel": channel,
            "sender": sender,
            "recipient": recipient,
            "message": text_content,
            "direction": direction,
            "priority": priority,
            "metadata": json.dumps({"externalId": external_id})
        })
        
        row = result.fetchone()
        await db.commit()
        
        created_at = row.created_at
        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()
        
        return {
            "id": external_id,
            "channel": channel,
            "from": sender,
            "to": row.recipient or recipient,
            "text": text_content,
            "priority": row.priority or priority,
            "direction": row.direction or direction,
            "timestamp": created_at,
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to record communication: {str(e)}")
