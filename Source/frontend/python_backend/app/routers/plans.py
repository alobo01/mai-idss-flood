"""Response plan endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional
from datetime import datetime
import uuid
import json

from ..database import get_db
from ..schemas import PlanResponse, PlanDraftCreate

router = APIRouter(prefix="/api", tags=["Response Plans"])


@router.get("/plan")
async def get_plan(
    status: str = Query("active", description="Filter by plan status"),
    type: Optional[str] = Query(None, description="Filter by plan type"),
    db: AsyncSession = Depends(get_db)
):
    """Get the latest response plan."""
    try:
        params = {}
        filters = []
        
        status_filter = status.lower()
        if status_filter not in ('any', 'all'):
            filters.append("LOWER(status) = :status")
            params["status"] = status_filter
        
        if type:
            filters.append("LOWER(plan_type) = LOWER(:plan_type)")
            params["plan_type"] = type
        
        where_clause = ""
        if filters:
            where_clause = "WHERE " + " AND ".join(filters)
        
        query = text(f"""
            SELECT id, name, version, description, plan_type, trigger_conditions,
                   recommended_actions, required_resources, assignments, coverage, notes,
                   estimated_duration, priority, status, created_at, updated_at
            FROM response_plans
            {where_clause}
            ORDER BY created_at DESC
            LIMIT 1
        """)
        
        result = await db.execute(query, params)
        row = result.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="No plan available")
        
        created_at = row.created_at
        updated_at = row.updated_at
        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()
        if isinstance(updated_at, datetime):
            updated_at = updated_at.isoformat()
        
        version = row.version
        if not version and row.created_at:
            version = row.created_at.isoformat() if isinstance(row.created_at, datetime) else row.created_at
        
        return {
            "id": str(row.id),
            "name": row.name,
            "planType": row.plan_type,
            "status": row.status,
            "version": version,
            "assignments": row.assignments or [],
            "coverage": row.coverage or {},
            "notes": row.notes or row.description or "",
            "triggerConditions": row.trigger_conditions or {},
            "recommendedActions": row.recommended_actions or [],
            "requiredResources": row.required_resources or {},
            "estimatedDuration": row.estimated_duration,
            "priority": row.priority,
            "createdAt": created_at,
            "updatedAt": updated_at,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch plan data: {str(e)}")


@router.post("/plan/draft", status_code=201)
async def create_draft_plan(
    request: PlanDraftCreate,
    db: AsyncSession = Depends(get_db)
):
    """Submit a draft plan."""
    try:
        assignments = request.assignments
        if not assignments:
            raise HTTPException(status_code=400, detail="assignments must be a non-empty array")
        
        sanitized_assignments = []
        for idx, assignment in enumerate(assignments):
            if not assignment.zoneId or not assignment.zoneId.strip():
                raise HTTPException(status_code=400, detail=f"assignments[{idx}].zoneId is required")
            if not assignment.actions:
                raise HTTPException(status_code=400, detail=f"assignments[{idx}].actions must contain at least one action")
            
            sanitized_assignments.append({
                "zoneId": assignment.zoneId,
                "priority": assignment.priority if assignment.priority is not None else idx + 1,
                "actions": assignment.actions,
                "notes": assignment.notes,
            })
        
        default_name = f"Planner Draft {str(uuid.uuid4())[:8].upper()}"
        plan_name = request.name.strip() if request.name else default_name
        plan_version = request.version or datetime.utcnow().isoformat()
        plan_type = request.planType or 'resource_deployment'
        trigger_conditions = request.triggerConditions or {}
        recommended_actions = request.recommendedActions or []
        required_resources = request.requiredResources or {}
        coverage = request.coverage or {}
        notes = request.notes or ""
        description = request.description if request.description else "Planner submitted draft plan"
        estimated_duration = request.estimatedDuration
        
        allowed_priorities = ['low', 'medium', 'high', 'critical']
        plan_priority = request.priority.lower() if request.priority else 'medium'
        if plan_priority not in allowed_priorities:
            plan_priority = 'medium'
        
        query = text("""
            INSERT INTO response_plans
                (name, version, description, plan_type, trigger_conditions, recommended_actions,
                 required_resources, assignments, coverage, notes, estimated_duration, priority, status)
            VALUES
                (:name, :version, :description, :plan_type,
                 CAST(:trigger_conditions AS jsonb), CAST(:recommended_actions AS jsonb),
                 CAST(:required_resources AS jsonb), CAST(:assignments AS jsonb), CAST(:coverage AS jsonb),
                 :notes, :estimated_duration, :priority, 'draft')
            RETURNING id, name, version, plan_type, trigger_conditions, recommended_actions,
                required_resources, assignments, coverage, notes, estimated_duration, priority,
                status, created_at, updated_at
        """)
        
        result = await db.execute(query, {
            "name": plan_name,
            "version": plan_version,
            "description": description,
            "plan_type": plan_type,
            "trigger_conditions": json.dumps(trigger_conditions),
            "recommended_actions": json.dumps(recommended_actions),
            "required_resources": json.dumps(required_resources),
            "assignments": json.dumps(sanitized_assignments),
            "coverage": json.dumps(coverage),
            "notes": notes,
            "estimated_duration": estimated_duration,
            "priority": plan_priority,
        })
        
        row = result.fetchone()
        await db.commit()
        
        created_at = row.created_at
        updated_at = row.updated_at
        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()
        if isinstance(updated_at, datetime):
            updated_at = updated_at.isoformat()
        
        return {
            "id": str(row.id),
            "name": row.name,
            "planType": row.plan_type,
            "status": row.status,
            "version": row.version,
            "assignments": row.assignments,
            "coverage": row.coverage,
            "notes": row.notes,
            "triggerConditions": row.trigger_conditions,
            "recommendedActions": row.recommended_actions,
            "requiredResources": row.required_resources,
            "estimatedDuration": row.estimated_duration,
            "priority": row.priority,
            "createdAt": created_at,
            "updatedAt": updated_at,
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create draft plan: {str(e)}")
