"""Zone endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import json

from ..database import get_db
from ..schemas import GeoJSONFeatureCollection, ZoneUpdateRequest, ZoneUpdateResponse

router = APIRouter(prefix="/api", tags=["Zones"])


@router.get("/zones", response_model=GeoJSONFeatureCollection)
async def get_zones(db: AsyncSession = Depends(get_db)):
    """Get all zones as GeoJSON feature collection."""
    try:
        query = text("""
            SELECT
                id,
                code,
                name,
                description,
                population,
                area_km2,
                admin_level,
                critical_assets,
                ST_AsGeoJSON(geometry, 6) as geometry
            FROM zones
            ORDER BY name
        """)
        
        result = await db.execute(query)
        rows = result.fetchall()
        
        features = []
        for row in rows:
            features.append({
                "type": "Feature",
                "geometry": json.loads(row.geometry),
                "properties": {
                    "id": row.code,
                    "name": row.name,
                    "description": row.description,
                    "population": row.population,
                    "critical_assets": row.critical_assets or [],
                    "admin_level": row.admin_level or 10,
                }
            })
        
        return {
            "type": "FeatureCollection",
            "features": features
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch zones: {str(e)}")
