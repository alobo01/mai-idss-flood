"""Asset endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional, List
import json

from ..database import get_db
from ..schemas import AssetResponse
from ..utils import is_valid_uuid

router = APIRouter(prefix="/api", tags=["Assets"])


@router.get("/assets", response_model=List[AssetResponse])
async def get_assets(
    zoneId: Optional[str] = Query(None, description="Zone identifier (code or UUID)"),
    db: AsyncSession = Depends(get_db)
):
    """Get critical assets with optional zone filtering."""
    try:
        params = {}
        where_clause = ""
        
        if zoneId:
            if is_valid_uuid(zoneId):
                where_clause = "WHERE a.zone_id = :zone_id"
            else:
                where_clause = "WHERE z.code = :zone_id"
            params["zone_id"] = zoneId
        
        query = text(f"""
            SELECT
                a.id,
                a.name,
                a.type,
                a.criticality,
                ST_AsGeoJSON(a.location, 6) as location,
                a.address,
                a.capacity,
                a.metadata,
                z.id as zone_uuid,
                z.code as zone_code,
                z.name as zone_name
            FROM assets a
            JOIN zones z ON a.zone_id = z.id
            {where_clause}
            ORDER BY a.criticality DESC, a.name
        """)
        
        result = await db.execute(query, params)
        rows = result.fetchall()
        
        assets = []
        for row in rows:
            location = None
            lat = None
            lng = None
            
            if row.location:
                try:
                    location = json.loads(row.location)
                    if location and 'coordinates' in location:
                        lng, lat = location['coordinates']
                except (json.JSONDecodeError, KeyError, TypeError):
                    pass
            
            assets.append({
                "id": row.id,
                "zoneId": row.zone_code,
                "zoneUuid": row.zone_uuid,
                "zoneName": row.zone_name,
                "name": row.name,
                "type": row.type,
                "criticality": row.criticality,
                "location": location,
                "lat": lat,
                "lng": lng,
                "address": row.address,
                "capacity": row.capacity,
                "metadata": getattr(row, "meta", None) or {},
            })
        
        return assets
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch assets: {str(e)}")
