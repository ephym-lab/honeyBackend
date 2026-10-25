from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_admin
from app.services import customer_service

router = APIRouter()


@router.get("")
def list_customers(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """All customers with their totals (Admin only)."""
    return customer_service.list_customers(db)


@router.get("/profile")
def customer_profile(
    email: str = Query(..., description="Customer email"),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """One customer's orders, requests and reviews (Admin only)."""
    profile = customer_service.customer_profile(db, email)
    if not profile:
        raise HTTPException(status_code=404, detail="Customer not found")
    return profile


@router.post("/notes")
def add_customer_note(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Save a private note on a customer (Admin only). Body: {"email": "...", "note": "..."}"""
    email = str((payload or {}).get("email") or "").strip()
    note = str((payload or {}).get("note") or "").strip()
    if not email or not note:
        raise HTTPException(status_code=400, detail="Write a note first")
    if len(note) > 2000:
        raise HTTPException(status_code=400, detail="Notes can be at most 2000 characters")
    return {"success": True, "data": customer_service.add_note(db, email, note)}


@router.delete("/notes/{note_id}")
def delete_customer_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Delete a note (Admin only)."""
    if not customer_service.delete_note(db, note_id):
        raise HTTPException(status_code=404, detail="Note not found")
    return {"success": True}
