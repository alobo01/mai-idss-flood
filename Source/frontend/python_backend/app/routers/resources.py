"""Resource endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional, List

from ..database import get_db
from ..schemas import ResourcesResponse
from ..utils import parse_point

router = APIRouter(prefix="/api", tags=["Resources"])


@router.get("/resources", response_model=ResourcesResponse)
async def get_resources(
    type: Optional[str] = Query(None, description="Filter by resource type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db)
):
    """Get resources with optional filters."""
    try:
        params = {}
        clauses = []
        
        if type:
            clauses.append("LOWER(type) = LOWER(:type)")
            params["type"] = type
        
        if status:
            clauses.append("LOWER(status) = LOWER(:status)")
            params["status"] = status
        
        where_clause = ""
        if clauses:
            where_clause = "WHERE " + " AND ".join(clauses)
        
        query = text(f"""
            SELECT
                code,
                name,
                type,
                status,
                capacity,
                capabilities,
                contact_info,
                ST_AsGeoJSON(location, 6) as location
            FROM resources
            {where_clause}
            ORDER BY type, name
        """)
        
        result = await db.execute(query, params)
        rows = result.fetchall()
        
        payload = {
            "depots": [],
            "equipment": [],
            "crews": []
        }
        
        for row in rows:
            location = parse_point(row.location)
            capabilities = row.capabilities or {}
            
            if row.type == 'depot':
                payload["depots"].append({
                    "id": row.code,
                    "name": row.name,
                    "lat": location['lat'],
                    "lng": location['lng'],
                })
            elif row.type == 'equipment':
                payload["equipment"].append({
                    "id": row.code,
                    "type": capabilities.get('type', row.name),
                    "subtype": capabilities.get('subtype'),
                    "capacity_lps": capabilities.get('capacity_lps'),
                    "units": capabilities.get('units'),
                    "depot": capabilities.get('depot'),
                    "status": row.status,
                })
            elif row.type == 'crew':
                payload["crews"].append({
                    "id": row.code,
                    "name": row.name,
                    "skills": capabilities.get('skills', []),
                    "depot": capabilities.get('depot'),
                    "status": row.status,
                    "lat": location['lat'],
                    "lng": location['lng'],
                })
        
        return payload
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch resources: {str(e)}")
