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

def parse_json_field(field_val: Optional[str], field_name: str):
    if not field_val or not field_val.strip():
        return None
    try:
        import json
        return json.loads(field_val)
    # pyrefly: ignore [unbound-name]
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail=f"Invalid JSON format for {field_name}")


@router.get("", response_model=ProductListResponse)
async def get_products(
    category: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    in_stock: Optional[bool] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    product_service = ProductService(db)
    return product_service.get_products(
        category=category,
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
    return product_service.update_stock(product_id, stock_data.model_dump(exclude_unset=True))


@router.post("", response_model=ProductResponse)
async def create_product(
    name: str = Form(...),
    description: str = Form(...),
    price: int = Form(...),
    category: str = Form(...),
    stock: int = Form(...),
    image_cover: UploadFile = File(..., description="Main product image (required)"),
    additional_images: Optional[List[UploadFile]] = File(None, description="Additional product images (max 2)"),
    tags: Optional[str] = Form(None),  # JSON string
    features: Optional[str] = Form(None),  # JSON string
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
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(image_cover.filename or "")[1]) as tmp_file:
        content = await image_cover.read()
        tmp_file.write(content)
        tmp_file_path = tmp_file.name
    
    try:
        main_image_url = upload_local_file(
            file_path=tmp_file_path,
            filename=image_cover.filename or "",
            file_type='images'
        )
    finally:
        if os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)
    
    # Upload additional images if provided
    additional_image_urls = []
    if additional_images:
        for idx, img in enumerate(additional_images):
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(img.filename or "")[1]) as tmp_file:
                content = await img.read()
                tmp_file.write(content)
                tmp_file_path = tmp_file.name
            
            try:
                img_url = upload_local_file(
                    file_path=tmp_file_path,
                    filename=img.filename or "",
                    file_type='images'
                )
                additional_image_urls.append(img_url)
            finally:
                if os.path.exists(tmp_file_path):
                    os.remove(tmp_file_path)
    
    # Parse JSON strings
    tags_list = parse_json_field(tags, "tags")
    features_list = parse_json_field(features, "features")
    related_products_list = parse_json_field(related_products, "related_products")
    bundle_offer_dict = parse_json_field(bundle_offer, "bundle_offer")
    
    # Create ProductCreate object
    product_data = ProductCreate(
        name=name,
        description=description,
        price=price,
        image_cover=main_image_url,
        category=category,
        stock=stock,
        images=additional_image_urls if additional_image_urls else None,
        tags=tags_list,
        features=features_list,
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
    category: Optional[str] = Form(None),
    stock: Optional[int] = Form(None),
    image_cover: Optional[UploadFile] = File(None, description="New main product image"),
    additional_images: Optional[List[UploadFile]] = File(None, description="New additional images (max 2)"),
    tags: Optional[str] = Form(None),  # JSON string
    features: Optional[str] = Form(None),  # JSON string
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
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(image_cover.filename or "")[1]) as tmp_file:
            content = await image_cover.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            main_image_url = upload_local_file(
                file_path=tmp_file_path,
                filename=image_cover.filename or "",
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
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(img.filename or "")[1]) as tmp_file:
                content = await img.read()
                tmp_file.write(content)
                tmp_file_path = tmp_file.name
            
            try:
                img_url = upload_local_file(
                    file_path=tmp_file_path,
                    filename=img.filename or "",
                    file_type='images'
                )
                additional_image_urls.append(img_url)
            finally:
                if os.path.exists(tmp_file_path):
                    os.remove(tmp_file_path)
    
    # Parse JSON strings
    tags_list = parse_json_field(tags, "tags")
    features_list = parse_json_field(features, "features")
    related_products_list = parse_json_field(related_products, "related_products")
    bundle_offer_dict = parse_json_field(bundle_offer, "bundle_offer")
    
    # Build update data dictionary - only include fields that are provided
    update_dict = {}
    if name is not None:
        update_dict['name'] = name
    if description is not None:
        update_dict['description'] = description
    if price is not None:
        update_dict['price'] = price
    if category is not None:
        update_dict['category'] = category
    if stock is not None:
        update_dict['stock'] = stock
    if tags_list is not None:
        update_dict['tags'] = tags_list
    if features_list is not None:
        update_dict['features'] = features_list
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
