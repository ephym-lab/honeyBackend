from abc import ABC
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import Integer
from fastapi import HTTPException, status
from typing import Optional
from uuid import UUID

from app.models.product import Products
from app.schemas.product import ProductCreate, ProductUpdate


class ProductManagerService(ABC):
    """Abstract base class for product management services."""
    
    def __init__(self, db: Session):
        self.db = db


class ProductService(ProductManagerService):
    """Service for handling product operations."""
    
    def __init__(self, db: Session):
        super().__init__(db)
    
    def get_products(
        self,
        scent: Optional[str] = None,
        size: Optional[str] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        in_stock: Optional[bool] = None,
        page: int = 1,
        limit: int = 20
    ):
        """Get all products with optional filters and pagination."""
        try:
            query = self.db.query(Products)

            if scent and scent != "All":
                query = query.filter(Products.scent == scent)
            if size and size != "All":
                query = query.filter(Products.size == size)
            if min_price is not None:
                if min_price < 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="min_price cannot be negative"
                    )
                query = query.filter(Products.price >= min_price)
            if max_price is not None:
                query = query.filter(Products.price <= max_price)
            if in_stock is True:
                query = query.filter(Products.stock > 0)
            elif in_stock is False:
                query = query.filter(Products.stock <= 0)

            total = query.count()
            offset = (page - 1) * limit
            products = (
                query.order_by(Products.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            return {
                "success": True,
                "message":"Products retrieved successfully",
                "data": {
                    "products": [p for p in products],
                    "pagination": {
                        "page": page,
                        "limit": limit,
                        "total": total,
                        "totalPages": (total + limit - 1) // limit
                    }
                }
            }

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch products: {str(e)}"
            )

    def get_product(self, product_id: UUID):
        """Get a single product by ID."""
        try:
            product = self.db.query(Products).filter(Products.id == product_id).first()

            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found"
                )

            return {
                "success": True,
                "data": product,
                "message":"Product retrieved successfully"
            }

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch product: {str(e)}"
            )

    def create_product(self, product_data: ProductCreate):
        """Create a new product."""
        try:
            product = Products(**product_data.model_dump())
            self.db.add(product)
            self.db.commit()
            self.db.refresh(product)

            return {
                "success": True,
                "data": product,
                "message": "Product created successfully"
            }

        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product already exists or violates constraints"
            )

        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create product: {str(e)}"
            )

    def update_product(self, product_id: UUID, product_data: ProductUpdate):
        """Update an existing product and clean up old images if new ones are provided."""
        try:
            product = self.db.query(Products).filter(Products.id == product_id).first()

            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found"
                )

            # Import file service for deletion
            from app.services.file_service import delete_file_from_supabase
            import logging
            logger = logging.getLogger(__name__)

            update_data = product_data.model_dump(exclude_unset=True)
            
            # If new main image is provided, delete the old one
            if 'image_cover' in update_data and product.image_cover and 'supabase' in product.image_cover.lower():
                try:
                    old_filename = product.image_cover.split('/images/')[-1].split('?')[0]
                    delete_file_from_supabase(old_filename, 'images')
                    logger.info(f"Deleted old main image: {old_filename}")
                except Exception as e:
                    logger.warning(f"Failed to delete old main image: {str(e)}")
            
            # If new additional images are provided, delete the old ones
            if 'images' in update_data and product.images and isinstance(product.images, list):
                for old_img_url in product.images:
                    if old_img_url and 'supabase' in old_img_url.lower():
                        try:
                            old_filename = old_img_url.split('/images/')[-1].split('?')[0]
                            delete_file_from_supabase(old_filename, 'images')
                            logger.info(f"Deleted old additional image: {old_filename}")
                        except Exception as e:
                            logger.warning(f"Failed to delete old additional image: {str(e)}")
            
            # Update product fields
            for field, value in update_data.items():
                setattr(product, field, value)

            self.db.commit()
            self.db.refresh(product)

            return {
                "success": True,
                "data": product,
                "message": "Product updated successfully"
            }

        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Update violates database constraints"
            )
        
        except HTTPException:
            raise

        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update product: {str(e)}"
            )

    def delete_product(self, product_id: UUID):
        """Delete a product and its associated files from Supabase storage."""
        try:
            product = self.db.query(Products).filter(Products.id == product_id).first()

            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found"
                )

            # Import file service for deletion
            from app.services.file_service import delete_file_from_supabase
            import logging
            logger = logging.getLogger(__name__)
            
            # Delete main image from Supabase if it exists and is a Supabase URL
            if product.image_cover and 'supabase' in product.image_cover.lower():
                try:
                    # Extract filename from URL
                    # URL format: https://.../storage/v1/object/public/HoneyBiz/images/filename.jpg
                    filename = product.image_cover.split('/images/')[-1].split('?')[0]
                    delete_file_from_supabase(filename, 'images')
                    logger.info(f"Deleted main image: {filename}")
                except Exception as e:
                    logger.warning(f"Failed to delete main image: {str(e)}")
            
            # Delete additional images from Supabase if they exist
            if product.images and isinstance(product.images, list):
                for img_url in product.images:
                    if img_url and 'supabase' in img_url.lower():
                        try:
                            # Extract filename from URL
                            filename = img_url.split('/images/')[-1].split('?')[0]
                            delete_file_from_supabase(filename, 'images')
                            logger.info(f"Deleted additional image: {filename}")
                        except Exception as e:
                            logger.warning(f"Failed to delete additional image: {str(e)}")

            # Delete the product from database
            self.db.delete(product)
            self.db.commit()

            return {
                "success": True,
                "message": "Product and associated files deleted successfully"
            }

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete product: {str(e)}"
            )
    
    def search_products(self, query: str, page: int = 1, limit: int = 20):
        """
        Search products by name or description.
        
        Args:
            query: Search query string
            page: Page number
            limit: Items per page
            
        Returns:
            dict: Response with search results and pagination
        """
        try:
            # Case-insensitive search in name and description
            search_filter = f"%{query}%"
            db_query = self.db.query(Products).filter(
                (Products.name.ilike(search_filter)) | 
                (Products.description.ilike(search_filter))
            )
            
            total = db_query.count()
            offset = (page - 1) * limit
            products = (
                db_query.order_by(Products.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )
            
            return {
                "success": True,
                "data": {
                    "products": [p for p in products],
                    "pagination": {
                        "page": page,
                        "limit": limit,
                        "total": total,
                        "totalPages": (total + limit - 1) // limit
                    }
                }
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to search products: {str(e)}"
            )
    
    def get_product_bundles(self, product_id: UUID):
        """
        Get bundle offers for a specific product.
        
        Args:
            product_id: Product ID
            
        Returns:
            dict: Response with bundle offer data
        """
        try:
            product = self.db.query(Products).filter(Products.id == product_id).first()
            
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found"
                )
            
            if product.bundle_offer:
                return {
                    "success": True,
                    "message": f"Bundle offer available for {product.name}",
                    "data": product.bundle_offer
                }
            else:
                return {
                    "success": True,
                    "message": "No bundle offer available for this product",
                    "data": None
                }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get bundle offers: {str(e)}"
            )
    
    def check_availability(self, product_id: UUID):
        """
        Check product stock availability.
        
        Args:
            product_id: Product ID
            
        Returns:
            dict: Response with availability status
        """
        try:
            product = self.db.query(Products).filter(Products.id == product_id).first()
            
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found"
                )
            
            # Determine availability status
            if product.stock > 10:
                availability_status = "In Stock"
            elif product.stock > 0:
                availability_status = "Low Stock"
            else:
                availability_status = "Out of Stock"
            
            return {
                "success": True,
                "message": f"{product.name} availability checked",
                "data": {
                    "productId": str(product.id),
                    "productName": product.name,
                    "stock": product.stock,
                    "availabilityStatus": availability_status,
                    "inStock": product.stock > 0
                }
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to check availability: {str(e)}"
            )
    
    def update_stock(self, product_id: UUID, stock_data: dict):
        """
        Update product stock (admin only).
        
        Args:
            product_id: Product ID
            stock_data: Stock update data
            
        Returns:
            dict: Response with updated product
        """
        try:
            product = self.db.query(Products).filter(Products.id == product_id).first()
            
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found"
                )
            
            # Update stock
            old_stock = product.stock
            product.stock = stock_data.stock
            
            self.db.commit()
            self.db.refresh(product)
            
            return {
                "success": True,
                "data": product,
                "message": f"Stock updated from {old_stock} to {product.stock}"
            }
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update stock: {str(e)}"
            )
    
    def get_top_selling_products(self, limit: int = 10):
        """
        Get top-selling products based on order data.
        
        Args:
            limit: Number of top products to return
            
        Returns:
            dict: Response with top-selling products
        """
        try:
            from app.models.order import Order
            from collections import defaultdict
            
            # Get all completed orders
            orders = self.db.query(Order).filter(
                Order.status.in_(['paid', 'processing', 'shipped', 'delivered'])
            ).all()
            
            # Aggregate sales data
            sales_data = defaultdict(lambda: {'total_sold': 0, 'revenue': 0})
            
            for order in orders:
                if order.items:
                    for item in order.items:
                        product_id = item.get('productId')
                        quantity = item.get('quantity', 0)
                        price = item.get('price', 0)
                        
                        if product_id:
                            sales_data[product_id]['total_sold'] += quantity
                            sales_data[product_id]['revenue'] += quantity * price
            
            # Sort by total sold and get top products
            sorted_products = sorted(
                sales_data.items(),
                key=lambda x: x[1]['total_sold'],
                reverse=True
            )[:limit]
            
            # Get product details and combine with sales data
            top_products = []
            for product_id, sales in sorted_products:
                product = self.db.query(Products).filter(
                    Products.id == product_id
                ).first()
                
                if product:
                    top_products.append({
                        "id": product.id,
                        "name": product.name,
                        "description": product.description,
                        "price": product.price,
                        "image_cover": product.image_cover,
                        "scent": product.scent,
                        "size": product.size,
                        "stock": product.stock,
                        "rating": float(product.rating) if product.rating else 0.0,
                        "total_sold": sales['total_sold'],
                        "revenue": sales['revenue']
                    })
            
            return {
                "success": True,
                "message": f"Top {len(top_products)} selling products retrieved",
                "data": top_products
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get top-selling products: {str(e)}"
            )
    
    def get_products_with_bundles(self):
        """
        Get all products that have bundle offers.
        
        Returns:
            dict: Response with products having bundle offers
        """
        try:
            products = self.db.query(Products).filter(Products.bundle_offer.isnot(None)).all()
            
            return {
                "success": True,
                "message": f"{len(products)} products with bundle offers retrieved",
                "data": [p for p in products]
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get products with bundle offers: {str(e)}"
            )
            
    def get_product_stats(self):
        """
        Get statistics about products.
        
        Returns:
            dict: Response with product statistics
        """
        try:
            total_products = self.db.query(Products).count()
            in_stock_count = self.db.query(Products).filter(Products.stock > 0).count()
            out_of_stock_count = self.db.query(Products).filter(Products.stock <= 0).count()
            
            return {
                "success": True,
                "message": "Product statistics retrieved successfully",
                "data": {
                    "total_products": total_products,
                    "in_stock": in_stock_count,
                    "out_of_stock": out_of_stock_count
                }
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get product statistics: {str(e)}"
            )