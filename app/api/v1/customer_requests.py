from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.schemas.customer_request import CustomerRequestCreate, CustomerRequestUpdateStatus
from app.services.customer_request_service import CustomerRequestService

router = APIRouter()

@router.post("")
async def create_request(
    request_data: CustomerRequestCreate,
    db: Session = Depends(get_db)
):
    """Submit a new customer request."""
    service = CustomerRequestService(db)
    return service.create_request(request_data)

@router.get("")
async def get_all_requests(
    reason: Optional[str] = Query(None, description="Filter requests by category"),
    db: Session = Depends(get_db)
):
    """Retrieve all customer requests, optionally filtered by reason."""
    service = CustomerRequestService(db)
    return service.get_all_requests(reason=reason)

@router.get("/stats")
async def get_request_stats(
    db: Session = Depends(get_db)
):
    """Get statistics for customer requests."""
    service = CustomerRequestService(db)
    return service.get_request_stats()

@router.get("/{request_id}")
async def get_request_by_id(
    request_id: str,
    db: Session = Depends(get_db)
):
    """Retrieve a single request by ID."""
    service = CustomerRequestService(db)
    return service.get_request_by_id(request_id)

@router.patch("/{request_id}/status")
async def update_request_status(
    request_id: str,
    status_data: CustomerRequestUpdateStatus,
    db: Session = Depends(get_db)
):
    """Update the status of a specific request."""
    service = CustomerRequestService(db)
    return service.update_request_status(request_id, status_data)

@router.delete("/{request_id}")
async def delete_request(
    request_id: str,
    db: Session = Depends(get_db)
):
    """Delete a specific customer request."""
    service = CustomerRequestService(db)
    return service.delete_request(request_id)

