from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.schemas.review import ReviewCreate, ReviewResponse
from app.services.review_service import ReviewService
from app.api.deps import get_current_admin

router = APIRouter()


@router.get("/products/{product_id}/reviews")
async def get_product_reviews(
    product_id: UUID,
    verified_only: bool = False,
    db: Session = Depends(get_db)
):
    """Get all reviews for a product."""
    try:
        review_service = ReviewService(db)
        return review_service.get_product_reviews(product_id, verified_only)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.post("/products/{product_id}/reviews", response_model=ReviewResponse)
async def create_review(
    product_id: UUID,
    review_data: ReviewCreate,
    db: Session = Depends(get_db)
):
    """Submit a product review."""
    try:
        review_service = ReviewService(db)
        return review_service.create_review(product_id, review_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


# Admin endpoint: Get all reviews with filtering
@router.get("/admin/reviews")
async def get_all_reviews(
    verified: bool = Query(None, description="Filter by verified status (true/false/null for all)"),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Get all reviews (Admin only). Can filter by verified status."""
    try:
        review_service = ReviewService(db)
        return review_service.get_all_reviews(verified_filter=verified)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


#verify review (Admin only)
@router.patch("/products/{product_id}/reviews/{review_id}/verify")
async def verify_review(
    product_id: UUID,
    review_id: UUID,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Verify a product review (Admin only)."""
    try:
        review_service = ReviewService(db)
        return review_service.verify_review(review_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

#delete review (Admin only)
@router.delete("/products/{product_id}/reviews/{review_id}")
async def delete_review(
    product_id: UUID,
    review_id: UUID,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Delete a product review (Admin only)."""
    try:
        review_service = ReviewService(db)
        return review_service.delete_review(review_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )  

#unverify review (Admin only)
@router.patch("/products/{product_id}/reviews/{review_id}/unverify")
async def unverify_review(
    product_id: UUID,
    review_id: UUID,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Unverify a product review (Admin only)."""
    try:
        review_service = ReviewService(db)
        return review_service.unverify_review(review_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )    


@router.get("/reviews/verified")
async def get_verified_reviews(
    db: Session = Depends(get_db)
):
    """Get all verified reviews across all products."""
    try:
        review_service = ReviewService(db)
        return review_service.get_verified_reviews()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )
