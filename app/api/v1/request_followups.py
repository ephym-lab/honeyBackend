from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_admin
from app.services import followup_service

router = APIRouter()


@router.get("")
def list_followups(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Follow-ups and history for every customer request (Admin only)."""
    return {"success": True, "data": followup_service.list_all(db)}


@router.put("/{request_id}")
def save_followup(
    request_id: str,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Set the outcome (Won/Lost/open), sale value and next follow-up date (Admin only)."""
    if not followup_service.request_exists(db, request_id):
        raise HTTPException(status_code=404, detail="Request not found")
    try:
        data = followup_service.save(db, request_id, payload or {})
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return {"success": True, "data": data}


@router.post("/{request_id}/activity")
def add_activity(
    request_id: str,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Add a line to the request's history, e.g. "Called - wants a quote for 10 hives" (Admin only)."""
    note = str((payload or {}).get("note") or "").strip()
    if not note:
        raise HTTPException(status_code=400, detail="Write what happened first")
    if len(note) > 1000:
        raise HTTPException(status_code=400, detail="Keep it under 1000 characters")
    if not followup_service.request_exists(db, request_id):
        raise HTTPException(status_code=404, detail="Request not found")
    return {"success": True, "data": followup_service.log(db, request_id, note)}


@router.delete("/activity/{activity_id}")
def delete_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Remove a history line (Admin only)."""
    if not followup_service.delete_activity(db, activity_id):
        raise HTTPException(status_code=404, detail="Not found")
    return {"success": True}
