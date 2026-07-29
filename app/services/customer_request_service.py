from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from typing import Optional
import uuid

from app.models.customer_request import CustomerRequest
from app.schemas.customer_request import CustomerRequestCreate, CustomerRequestUpdateStatus, CustomerRequestResponse
from app.services.notification_service import NotificationService

class CustomerRequestService:
    def __init__(self, db: Session):
        self.db = db

    def create_request(self, request_data: CustomerRequestCreate):
        try:
            new_request = CustomerRequest(
                name=request_data.name,
                email=request_data.email,
                phone=request_data.phone,
                reason=request_data.reason,
                training_type=request_data.training_type,
                participants=request_data.participants,
                preferred_date=request_data.preferred_date,
                location=request_data.location,
                message=request_data.message,
                status="New"
            )
            self.db.add(new_request)
            self.db.commit()
            self.db.refresh(new_request)
            
            # Create a notification for the admin
            notification_service = NotificationService(self.db)
            notification_service.create_notification(
                title=f"New {request_data.reason}",
                message=f"A new request has been submitted by {request_data.name}.",
                notification_type="customer_request",
                priority="high",
                related_entity="customer_request",
                related_id=str(new_request.id)
            )
            
            return {
                "success": True,
                "message": "Request submitted successfully",
                "data": CustomerRequestResponse.model_validate(new_request).model_dump(mode='json')
            }
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to submit request: {str(e)}"
            )

    def get_all_requests(self, reason: Optional[str] = None):
        try:
            query = self.db.query(CustomerRequest)
            if reason:
                query = query.filter(CustomerRequest.reason == reason)
            
            requests = query.order_by(CustomerRequest.created_at.desc()).all()
            return {
                "success": True,
                "data": [CustomerRequestResponse.model_validate(r).model_dump(mode='json') for r in requests]
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch requests: {str(e)}"
            )

    def get_request_by_id(self, request_id: str):
        try:
            request = self.db.query(CustomerRequest).filter(CustomerRequest.id == request_id).first()
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Request not found"
                )
            return {
                "success": True,
                "data": CustomerRequestResponse.model_validate(request).model_dump(mode='json')
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch request: {str(e)}"
            )

    def update_request_status(self, request_id: str, status_data: CustomerRequestUpdateStatus):
        try:
            request = self.db.query(CustomerRequest).filter(CustomerRequest.id == request_id).first()
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Request not found"
                )
            
            request.status = status_data.status #type:ignore
            self.db.commit()
            self.db.refresh(request)
            return {
                "success": True,
                "message": f"Request status updated to {status_data.status}",
                "data": CustomerRequestResponse.model_validate(request).model_dump(mode='json')
            }
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update status: {str(e)}"
            )

    def get_request_stats(self):
        try:
            total = self.db.query(CustomerRequest).count()
            
            # Category counts
            training = self.db.query(CustomerRequest).filter(CustomerRequest.reason == "Training Request").count()
            general = self.db.query(CustomerRequest).filter(CustomerRequest.reason == "General Inquiry").count()
            bulk = self.db.query(CustomerRequest).filter(CustomerRequest.reason == "Bulk Order Quote").count()
            support = self.db.query(CustomerRequest).filter(CustomerRequest.reason == "Product Support").count()
            other = self.db.query(CustomerRequest).filter(CustomerRequest.reason == "Other Inquiry").count()
            
            # Status counts
            new_status = self.db.query(CustomerRequest).filter(CustomerRequest.status == "New").count()
            contacted = self.db.query(CustomerRequest).filter(CustomerRequest.status == "Contacted").count()
            in_progress = self.db.query(CustomerRequest).filter(CustomerRequest.status == "In Progress").count()
            completed = self.db.query(CustomerRequest).filter(CustomerRequest.status == "Completed").count()
            
            return {
                "success": True,
                "data": {
                    "total": total,
                    "training_requests": training,
                    "general_inquiries": general,
                    "bulk_order_quotes": bulk,
                    "product_support": support,
                    "other_inquiries": other,
                    "new": new_status,
                    "contacted": contacted,
                    "in_progress": in_progress,
                    "completed": completed
                }
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch stats: {str(e)}"
            )

    def delete_request(self, request_id: str):
        try:
            request = self.db.query(CustomerRequest).filter(CustomerRequest.id == request_id).first()
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Request not found"
                )
            
            self.db.delete(request)
            self.db.commit()
            
            return {
                "success": True,
                "message": "Request deleted successfully"
            }
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete request: {str(e)}"
            )

