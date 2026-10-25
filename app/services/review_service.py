from abc import ABC
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import date
from uuid import UUID
from sqlalchemy import func

from app.schemas.review import ReviewCreate
from app.models.review import Review
from app.models.product import Products


class ReviewManagerService(ABC):
    """Abstract base class for review management services."""
    
    def __init__(self, db: Session):
        self.db = db


class ReviewService(ReviewManagerService):
    """Service for handling product review operations."""
    
    def __init__(self, db: Session):
        super().__init__(db)
    
    def create_review(self, product_id: UUID, review_data: ReviewCreate):
        """
        Create a new product review.
        
        Args:
            product_id: Product UUID
            review_data: Review creation data
            
        Returns:
            dict: Success response with review data
            
        Raises:
            HTTPException: If product not found or creation fails
        """
        # Check if product exists
        product = self.db.query(Products).filter(Products.id == product_id).first()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        try:
            # Create review
            review = Review(
                product_id=product_id,
                author=review_data.author,
                email=review_data.email,
                rating=review_data.rating,
                comment=review_data.comment,
                date=date.today(),
                verified=False  # Reviews start as unverified
            )
            
            self.db.add(review)
            self.db.commit()
            self.db.refresh(review)
            
            # Update product rating
            self._update_product_rating(product_id)
            
            return {
                "success": True,
                "data": review,
                "message": "Review submitted successfully"
            }
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create review: {str(e)}"
            )
    
    def get_product_reviews(self, product_id: UUID, verified_only: bool = False):
        """
        Get all reviews for a product.
        
        Args:
            product_id: Product UUID
            verified_only: Only return verified reviews
            
        Returns:
            dict: Success response with reviews list
            
        Raises:
            HTTPException: If product not found or database error occurs
        """
        # Check if product exists
        product = self.db.query(Products).filter(Products.id == product_id).first()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found"
            )
        
        try:
            query = self.db.query(Review).filter(Review.product_id == product_id)
            
            if verified_only:
                query = query.filter(Review.verified == True)
            
            reviews = query.order_by(Review.created_at.desc()).all()
            
            return {
                "success": True,
                "data": {
                    "reviews": reviews,
                    "count": len(reviews)
                }
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve reviews: {str(e)}"
            )
    
    def verify_review(self, review_id: UUID):
        """
        Verify a review (admin only).
        
        Args:
            review_id: Review UUID
            
        Returns:
            dict: Success response
            
        Raises:
            HTTPException: If review not found or database error occurs
        """
        review = self.db.query(Review).filter(Review.id == review_id).first()
        
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Review with ID {review_id} not found"
            )
        
        # Check if already verified
        if review.verified:
            return {
                "success": True,
                "message": "Review is already verified"
            }
        
        try:
            review.verified = True
            self.db.commit()
            self.db.refresh(review)
            
            return {
                "success": True,
                "message": "Review verified successfully",
                "data": review
            }
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to verify review: {str(e)}"
            )
    
    def delete_review(self, review_id: UUID):
        """
        Delete a review (admin only).
        
        Args:
            review_id: Review UUID
            
        Returns:
            dict: Success response
            
        Raises:
            HTTPException: If review not found
        """
        review = self.db.query(Review).filter(Review.id == review_id).first()
        
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found"
            )
        
        product_id = review.product_id
        
        try:
            self.db.delete(review)
            self.db.commit()
            
            # Update product rating after deletion
            self._update_product_rating(product_id)
            
            return {
                "success": True,
                "message": "Review deleted successfully"
            }
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete review: {str(e)}"
            )
    
    def _update_product_rating(self, product_id: UUID):
        """
        Update product's average rating based on all reviews.
        
        Args:
            product_id: Product UUID
            
        Raises:
            HTTPException: If database error occurs
        """
        try:
            # Calculate average rating
            avg_rating = self.db.query(func.avg(Review.rating)).filter(
                Review.product_id == product_id
            ).scalar()
            
            # Update product
            product = self.db.query(Products).filter(Products.id == product_id).first()
            if product:
                product.rating = round(avg_rating, 1) if avg_rating else 0.0
                self.db.commit()
        except Exception as e:
            self.db.rollback()
            # Log error but don't raise - rating update is not critical
            print(f"Warning: Failed to update product rating: {str(e)}")

    def get_all_reviews(self, verified_filter: bool = None):
        """
        Get all reviews with optional filtering by verified status.
        
        Args:
            verified_filter: Optional filter for verified status (True/False/None for all)
        
        Returns:
            dict: Success response with reviews list
            
        Raises:
            HTTPException: If database error occurs
        """
        try:
            query = self.db.query(Review)
            
            # Apply verified filter if specified
            if verified_filter is not None:
                query = query.filter(Review.verified == verified_filter)
            
            reviews = query.order_by(Review.created_at.desc()).all()
            
            # Calculate statistics
            total_count = len(reviews)
            verified_count = sum(1 for r in reviews if r.verified)
            unverified_count = total_count - verified_count
            
            return {
                "success": True,
                "data": {
                    "reviews": self._with_product_names(reviews),
                    "count": total_count,
                    "verified_count": verified_count,
                    "unverified_count": unverified_count
                }
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve reviews: {str(e)}"
            )

    def unverify_review(self, review_id: UUID):
        """
        Unverify a review (admin only).
        
        Args:
            review_id: Review UUID
            
        Returns:
            dict: Success response
            
        Raises:
            HTTPException: If review not found or database error occurs
        """
        review = self.db.query(Review).filter(Review.id == review_id).first()
        
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Review with ID {review_id} not found"
            )
        
        # Check if already unverified
        if not review.verified:
            return {
                "success": True,
                "message": "Review is already unverified"
            }
        
        try:
            review.verified = False
            review.featured = False
            self.db.commit()
            self.db.refresh(review)
            
            return {
                "success": True,
                "message": "Review unverified successfully",
                "data": review
            }
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to unverify review: {str(e)}"
            )
    
    def get_verified_reviews(self):
        """
        Get all verified reviews across all products.
        
        Returns:
            dict: Success response with verified reviews list
            
        Raises:
            HTTPException: If database error occurs
        """
        try:
            base = self.db.query(Review).filter(Review.verified == True)
            # Home page shows the reviews the admin featured.
            # If none are featured yet, it falls back to all verified reviews.
            reviews = base.filter(Review.featured == True).order_by(Review.created_at.desc()).all()
            if not reviews:
                reviews = base.order_by(Review.created_at.desc()).all()
            
            # Enrich reviews with product information
            reviews_data = []
            for review in reviews:
                product = self.db.query(Products).filter(
                    Products.id == review.product_id
                ).first()
                
                reviews_data.append({
                    "id": str(review.id),
                    "productId": str(review.product_id),
                    "productName": product.name if product else "Unknown Product",
                    "customerName": review.author,
                    "author": review.author,
                    "role": f"Verified buyer - {product.name}" if product else "Verified buyer",
                    "featured": bool(review.featured),
                    "email": review.email,
                    "rating": review.rating,
                    "comment": review.comment,
                    "verified": review.verified,
                    "createdAt": review.created_at
                })
            
            return {
                "success": True,
                "data": {
                    "reviews": reviews_data,
                    "count": len(reviews_data)
                }
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve verified reviews: {str(e)}"
            )

    def _with_product_names(self, reviews):
        """Reviews as plain data, each with its product's name (for the admin page)."""
        ids = {r.product_id for r in reviews}
        names = {}
        if ids:
            for pid, name in self.db.query(Products.id, Products.name).filter(Products.id.in_(ids)).all():
                names[pid] = name
        return [
            {
                "id": str(r.id),
                "product_id": str(r.product_id),
                "productName": names.get(r.product_id, "Deleted product"),
                "author": r.author,
                "email": r.email,
                "rating": r.rating,
                "comment": r.comment,
                "date": r.date,
                "verified": bool(r.verified),
                "featured": bool(getattr(r, "featured", False)),
                "created_at": r.created_at,
            }
            for r in reviews
        ]


    def set_featured(self, review_id: UUID, featured: bool):
        """Feature / unfeature a review on the Home page (admin only).
        Featuring also verifies it, because it becomes public."""
        review = self.db.query(Review).filter(Review.id == review_id).first()
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Review with ID {review_id} not found"
            )
        try:
            review.featured = bool(featured)
            if featured:
                review.verified = True
            self.db.commit()
            self.db.refresh(review)
            return {
                "success": True,
                "message": "Review featured on the Home page" if featured else "Review removed from the Home page",
                "data": review
            }
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update review: {str(e)}"
            )
