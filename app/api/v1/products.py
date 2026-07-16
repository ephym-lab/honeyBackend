from fastapi import APIRouter, Depends, Query, File, UploadFile, Form, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
import tempfile
import os

from app.database import get_db
from app.schemas.product import (
    ProductCreate, 
    ProductUpdate, 
    ProductResponse, 
    ProductListResponse,
    ProductBundleListResponse,
    StockUpdate,
    AvailabilityResponse,
    TopSellingResponse,
    BundleResponse,
    SuccessResponse
)
from app.api.deps import get_current_admin
from app.services.product_service import ProductService
from app.services.file_service import upload_local_file

router = APIRouter()


@router.get("", response_model=ProductListResponse)
async def get_products(
    scent: Optional[str] = None,
    size: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    in_stock: Optional[bool] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    product_service = ProductService(db)
    return product_service.get_products(
        scent=scent,
        size=size,
        min_price=min_price,
        max_price=max_price,
        in_stock=in_stock,
        page=page,
        limit=limit
    )


@router.get("/search", response_model=ProductListResponse)
async def search_products(
    q: str = Query(..., description="Search query for product name or description"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search products by name or description."""
    product_service = ProductService(db)
    return product_service.search_products(query=q, page=page, limit=limit)


@router.get("/stats/top-selling", response_model=TopSellingResponse)
async def get_top_selling_products(
    limit: int = Query(10, ge=1, le=50, description="Number of top products to return"),
    db: Session = Depends(get_db)
):
    """Get top-selling products based on order data."""
    product_service = ProductService(db)
    return product_service.get_top_selling_products(limit=limit)



@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a single product by ID."""
    product_service = ProductService(db)
    return product_service.get_product(product_id)

@router.get("/bundle/all", response_model=ProductBundleListResponse)
async def get_all_bundles(
    db: Session = Depends(get_db)
):
    """Get all product bundles."""
    product_service = ProductService(db)
    return product_service.get_products_with_bundles()

@router.get("/{product_id}/bundle", response_model=BundleResponse)
async def get_product_bundle(
    product_id: UUID,
    db: Session = Depends(get_db)
):
    """Get bundle offers for a specific product."""
    product_service = ProductService(db)
    return product_service.get_product_bundles(product_id)


@router.get("/{product_id}/availability", response_model=AvailabilityResponse)
async def check_product_availability(
    product_id: UUID,
    db: Session = Depends(get_db)
):
    """Check product stock availability."""
    product_service = ProductService(db)
    return product_service.check_availability(product_id)


@router.patch("/{product_id}/stock", response_model=ProductResponse)
async def update_product_stock(
    product_id: UUID,
    stock_data: StockUpdate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Update product stock (Admin only)."""
    product_service = ProductService(db)
    return product_service.update_stock(product_id, stock_data)


@router.post("", response_model=ProductResponse)
async def create_product(
    name: str = Form(...),
    description: str = Form(...),
    price: int = Form(...),
    scent: str = Form(...),
    size: str = Form(...),
    stock: int = Form(...),
    image_cover: UploadFile = File(..., description="Main product image (required)"),
    additional_images: Optional[List[UploadFile]] = File(None, description="Additional product images (max 2)"),
    scent_description: Optional[str] = Form(None),
    burn_time: Optional[int] = Form(None),
    care_instructions: Optional[str] = Form(None),  # JSON string
    ingredients: Optional[str] = Form(None),  # JSON string
    related_products: Optional[str] = Form(None),  # JSON string
    bundle_offer: Optional[str] = Form(None),  # JSON string
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Create a new product (Admin only).
    
    Accepts file uploads for product images:
    - image_cover: Main product image (required)
    - additional_images: Up to 2 additional images (optional)
    
    Total maximum: 3 images per product
    """
    import json
    
    # Validate total number of images
    total_images = 1  # Main image
    if additional_images:
        total_images += len(additional_images)
        if total_images > 3:
            raise HTTPException(
                status_code=400, 
                detail=f"Maximum 3 images allowed (1 main + 2 additional). You provided {total_images} images."
            )
    
    # Upload main image
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(image_cover.filename)[1]) as tmp_file:
        content = await image_cover.read()
        tmp_file.write(content)
        tmp_file_path = tmp_file.name
    
    try:
        main_image_url = upload_local_file(
            file_path=tmp_file_path,
            filename=image_cover.filename,
            file_type='images'
        )
    finally:
        if os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)
    
    # Upload additional images if provided
    additional_image_urls = []
    if additional_images:
        for idx, img in enumerate(additional_images):
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(img.filename)[1]) as tmp_file:
                content = await img.read()
                tmp_file.write(content)
                tmp_file_path = tmp_file.name
            
            try:
                img_url = upload_local_file(
                    file_path=tmp_file_path,
                    filename=img.filename,
                    file_type='images'
                )
                additional_image_urls.append(img_url)
            finally:
                if os.path.exists(tmp_file_path):
                    os.remove(tmp_file_path)
    
    # Parse JSON strings
    care_instructions_list = json.loads(care_instructions) if care_instructions else None
    ingredients_list = json.loads(ingredients) if ingredients else None
    related_products_list = json.loads(related_products) if related_products else None
    bundle_offer_dict = json.loads(bundle_offer) if bundle_offer else None
    
    # Create ProductCreate object
    product_data = ProductCreate(
        name=name,
        description=description,
        price=price,
        image_cover=main_image_url,
        scent=scent,
        size=size,
        stock=stock,
        scent_description=scent_description,
        images=additional_image_urls if additional_image_urls else None,
        burn_time=burn_time,
        care_instructions=care_instructions_list,
        ingredients=ingredients_list,
        related_products=related_products_list,
        bundle_offer=bundle_offer_dict
    )
    
    product_service = ProductService(db)
    return product_service.create_product(product_data)


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    price: Optional[int] = Form(None),
    scent: Optional[str] = Form(None),
    size: Optional[str] = Form(None),
    stock: Optional[int] = Form(None),
    image_cover: Optional[UploadFile] = File(None, description="New main product image"),
    additional_images: Optional[List[UploadFile]] = File(None, description="New additional images (max 2)"),
    scent_description: Optional[str] = Form(None),
    burn_time: Optional[int] = Form(None),
    care_instructions: Optional[str] = Form(None),  # JSON string
    ingredients: Optional[str] = Form(None),  # JSON string
    related_products: Optional[str] = Form(None),  # JSON string
    bundle_offer: Optional[str] = Form(None),  # JSON string
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Update a product (Admin only).
    
    Accepts file uploads for product images:
    - image_cover: New main product image (optional)
    - additional_images: New additional images, max 2 (optional)
    
    Note: Providing new images will replace existing ones.
    """
    import json
    
    # Validate total number of images if both are provided
    if image_cover and additional_images:
        total_images = 1 + len(additional_images)
        if total_images > 3:
            raise HTTPException(
                status_code=400, 
                detail=f"Maximum 3 images allowed (1 main + 2 additional). You provided {total_images} images."
            )
    
    # Upload main image if provided
    main_image_url = None
    if image_cover:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(image_cover.filename)[1]) as tmp_file:
            content = await image_cover.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            main_image_url = upload_local_file(
                file_path=tmp_file_path,
                filename=image_cover.filename,
                file_type='images'
            )
        finally:
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)
    
    # Upload additional images if provided
    additional_image_urls = None
    if additional_images:
        if len(additional_images) > 2:
            raise HTTPException(
                status_code=400,
                detail=f"Maximum 2 additional images allowed. You provided {len(additional_images)}."
            )
        
        additional_image_urls = []
        for idx, img in enumerate(additional_images):
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(img.filename)[1]) as tmp_file:
                content = await img.read()
                tmp_file.write(content)
                tmp_file_path = tmp_file.name
            
            try:
                img_url = upload_local_file(
                    file_path=tmp_file_path,
                    filename=img.filename,
                    file_type='images'
                )
                additional_image_urls.append(img_url)
            finally:
                if os.path.exists(tmp_file_path):
                    os.remove(tmp_file_path)
    
    # Parse JSON strings
    care_instructions_list = json.loads(care_instructions) if care_instructions else None
    ingredients_list = json.loads(ingredients) if ingredients else None
    related_products_list = json.loads(related_products) if related_products else None
    bundle_offer_dict = json.loads(bundle_offer) if bundle_offer else None
    
    # Build update data dictionary - only include fields that are provided
    update_dict = {}
    if name is not None:
        update_dict['name'] = name
    if description is not None:
        update_dict['description'] = description
    if price is not None:
        update_dict['price'] = price
    if scent is not None:
        update_dict['scent'] = scent
    if size is not None:
        update_dict['size'] = size
    if stock is not None:
        update_dict['stock'] = stock
    if scent_description is not None:
        update_dict['scent_description'] = scent_description
    if burn_time is not None:
        update_dict['burn_time'] = burn_time
    if care_instructions_list is not None:
        update_dict['care_instructions'] = care_instructions_list
    if ingredients_list is not None:
        update_dict['ingredients'] = ingredients_list
    if related_products_list is not None:
        update_dict['related_products'] = related_products_list
    if bundle_offer_dict is not None:
        update_dict['bundle_offer'] = bundle_offer_dict
    
    # Only include image fields if new images were uploaded
    if main_image_url is not None:
        update_dict['image_cover'] = main_image_url
    if additional_image_urls is not None:
        update_dict['images'] = additional_image_urls
    
    # Create ProductUpdate object with only the fields that were provided
    product_data = ProductUpdate(**update_dict)
    
    product_service = ProductService(db)
    return product_service.update_product(product_id, product_data)


@router.delete("/{product_id}")
async def delete_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Delete a product (Admin only)."""
    product_service = ProductService(db)
    return product_service.delete_product(product_id)
