# API Endpoints Documentation

**Base URL:** `/v1`

This document provides comprehensive information about all available API endpoints, including request headers, request bodies, and response bodies.

---

## Table of Contents

1. [Authentication](#authentication)
2. [Products](#products)
3. [Orders](#orders)
4. [Reviews](#reviews)
5. [Newsletter](#newsletter)
6. [Analytics](#analytics)
8. [Health Check](#health-check)

---

## Authentication

### 1. Register User

**Endpoint:** `POST /v1/auth/register`

**Description:** Register a new user account.

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123",
  "full_name": "John Doe"  // Optional
}
```

**Response Body (Success - 200):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid-string",
      "email": "user@example.com",
      "role": "user"
    }
  }
}
```

---

### 2. User Login

**Endpoint:** `POST /v1/auth/login`

**Description:** Authenticate user and receive access token.

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

**Response Body (Success - 200):**
```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": "uuid-string",
      "email": "user@example.com",
      "role": "user"
    }
  }
}
```

---

### 3. Admin Login

**Endpoint:** `POST /v1/auth/admin/login`

**Description:** Authenticate admin user (legacy endpoint).

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "email": "admin@example.com",
  "password": "adminPassword123"
}
```

**Response Body (Success - 200):**
```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": "uuid-string",
      "email": "admin@example.com",
      "role": "admin"
    }
  }
}
```

---

## Products

### 1. Get All Products (with Filters)

**Endpoint:** `GET /v1/products`

**Description:** Retrieve all products with optional filtering and pagination.

**Request Headers:**
```
Content-Type: application/json
```

**Query Parameters:**
- `category` (optional): Filter by category (e.g., "HIVES", "HONEY")
- `min_price` (optional): Minimum price filter (integer)
- `max_price` (optional): Maximum price filter (integer)
- `in_stock` (optional): Filter by stock availability (boolean)
- `page` (optional, default: 1): Page number (min: 1)
- `limit` (optional, default: 20): Items per page (min: 1, max: 100)

**Example Request:**
```
GET /v1/products?category=HIVES&in_stock=true&page=1&limit=20
```

**Response Body (Success - 200):**
```json
{
  "success": true,
  "data": {
    "products": [
      {
        "id": "uuid-string",
        "name": "Langstroth Eucalyptus Hive",
        "description": "Premium eucalyptus timber hive",
        "price": 1500,
        "image_cover": "https://example.com/image.jpg",
        "category": "HIVES",
        "stock": 50
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 100,
      "totalPages": 5
    }
  }
}
```

---

### 2. Search Products

**Endpoint:** `GET /v1/products/search`

**Description:** Search products by name or description.

**Request Headers:**
```
Content-Type: application/json
```

**Query Parameters:**
- `q` (required): Search query string
- `page` (optional, default: 1): Page number (min: 1)
- `limit` (optional, default: 20): Items per page (min: 1, max: 100)

**Example Request:**
```
GET /v1/products/search?q=lavender&page=1&limit=20
```

**Response Body (Success - 200):**
```json
{
  "success": true,
  "data": {
    "products": [...],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 15,
      "totalPages": 1
    }
  }
}
```

---

### 3. Get Top Selling Products

**Endpoint:** `GET /v1/products/stats/top-selling`

**Description:** Get top-selling products based on order data.

**Request Headers:**
```
Content-Type: application/json
```

**Query Parameters:**
- `limit` (optional, default: 10): Number of top products to return (min: 1, max: 50)

**Example Request:**
```
GET /v1/products/stats/top-selling?limit=10
```

**Response Body (Success - 200):**
```json
{
  "success": true,
  "message": "Top selling products retrieved successfully",
  "data": [
    {
      "id": "uuid-string",
      "name": "Langstroth Eucalyptus Hive",
      "description": "Premium eucalyptus timber hive",
      "price": 1500,
      "image_cover": "https://example.com/image.jpg",
      "category": "HIVES",
            "stock": 50,
      "rating": 4.5,
      "total_sold": 250,
      "revenue": 375000
    }
  ]
}
```

---

### 4. Get Single Product

**Endpoint:** `GET /v1/products/{product_id}`

**Description:** Retrieve a single product by its ID.

**Request Headers:**
```
Content-Type: application/json
```

**Path Parameters:**
- `product_id` (required): UUID of the product

**Example Request:**
```
GET /v1/products/123e4567-e89b-12d3-a456-426614174000
```

**Response Body (Success - 200):**
```json
{
  "success": true,
  "data": {
    "id": "uuid-string",
    "name": "Langstroth Eucalyptus Hive",
    "description": "Premium eucalyptus timber hive",
    "price": 1500,
    "image_cover": "https://example.com/image.jpg",
    "category": "HIVES",
        "stock": 50,
    "rating": 4.5,
    "tags": ["100% Pure", "Locally Sourced"],
    "images": ["url1", "url2"],
        "care_instructions": ["Keep away from drafts"],
        "related_products": ["uuid1", "uuid2"],
    "bundle_offer": {
      "quantity": 3,
      "discount": 15,
      "description": "Buy 3, get 15% off"
    },
    "reviews": [
      {
        "id": "uuid-string",
        "product_id": "123e4567-e89b-12d3-a456-426614174000",
        "author": "Jane Doe",
        "rating": 5,
        "comment": "Great product!",
        "date": "2024-01-02",
        "verified": true,
        "created_at": "2024-01-02T12:00:00Z"
      }
    ],
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  },
  "message": null
}
```

---

### 5. Get Product Bundle Offers

**Endpoint:** `GET /v1/products/{product_id}/bundle`

**Description:** Get bundle offers for a specific product.

**Request Headers:**
```
Content-Type: application/json
```

**Path Parameters:**
- `product_id` (required): UUID of the product

**Response Body (Success - 200):**
```json
{
  "success": true,
  "message": "Bundle offer retrieved successfully",
  "data": {
    "quantity": 3,
    "discount": 15,
    "description": "Buy 3, get 15% off"
  }
}
```

---

### 6. Check Product Availability

**Endpoint:** `GET /v1/products/{product_id}/availability`

**Description:** Check product stock availability.

**Request Headers:**
```
Content-Type: application/json
```

**Path Parameters:**
- `product_id` (required): UUID of the product

**Response Body (Success - 200):**
```json
{
  "success": true,
  "message": "Product is in stock",
  "data": {
    "available": true,
    "stock": 50
  }
}
```

---

### 7. Update Product Stock (Admin Only)

**Endpoint:** `PATCH /v1/products/{product_id}/stock`

**Description:** Update product stock quantity (requires admin authentication).

**Request Headers:**
```
Content-Type: application/json
Authorization: Bearer <admin_token>
```

**Path Parameters:**
- `product_id` (required): UUID of the product

**Request Body:**
```json
{
  "stock": 100
}
```

**Response Body (Success - 200):**
```json
{
  "success": true,
  "data": {
    "id": "uuid-string",
    "name": "Langstroth Eucalyptus Hive",
    "stock": 100,
    ...
  },
  "message": null
}
```

---

### 8. Create Product (Admin Only)

**Endpoint:** `POST /v1/products`

**Description:** Create a new product with image uploads (requires admin authentication).

**Request Headers:**
```
Content-Type: multipart/form-data
Authorization: Bearer <admin_token>
```

**Request Body (multipart/form-data):**

**Required Fields:**
- `name` (string): Product name
- `description` (string): Product description
- `price` (integer): Product price in cents
- `category` (string): Category (e.g., "HIVES", "HONEY")
- `stock` (integer): Stock quantity
- `image_cover` (file): Main product image (required, file upload)

**Optional Fields:**
- `additional_images` (file[]): Up to 2 additional product images (file uploads)
- `tags` (string): JSON array of tags
- `features` (string): JSON array of features
- `related_products` (string): JSON array of related product UUIDs
- `bundle_offer` (string): JSON object with bundle offer details

**Example using cURL:**
```bash
curl -X POST "http://localhost:8000/v1/products" \
  -H "Authorization: Bearer <admin_token>" \
  -F "name=Langstroth Eucalyptus Hive" \
  -F "description=Premium eucalyptus timber hive" \
  -F "price=1500" \
  -F "category=HIVES" \
  -F "stock=50" \
  -F "image_cover=@/path/to/main-image.jpg" \
  -F "additional_images=@/path/to/image2.jpg" \
  -F "additional_images=@/path/to/image3.jpg" \
  -F 'tags=["100% Pure", "Locally Sourced"]' \
  -F 'features=["Weather resistant", "Includes super"]' \
  -F 'bundle_offer={"quantity": 3, "discount": 15, "description": "Buy 3, get 15% off"}'
```

**Notes:**
- Maximum 3 images total per product (1 main + 2 additional)
- Images are uploaded locally to the /uploads directory and URLs are stored in the database
- Complex fields (care_instructions, ingredients, bundle_offer) must be JSON strings
- All image files are required to be actual file uploads, not URLs

**Response Body (Success - 200):**
```json
{
  "success": true,
  "data": {
    "id": "new-uuid-string",
    "name": "Langstroth Eucalyptus Hive",
    "description": "Premium eucalyptus timber hive",
    "price": 1500,
    "image_cover": "/uploads/images/main-image.jpg",
    "category": "HIVES",
    "stock": 50,
    "rating": 0.0,
    "tags": ["100% Pure", "Locally Sourced"],
    "images": [
      "/uploads/images/image2.jpg",
      "/uploads/images/image3.jpg"
    ],
    "features": ["Weather resistant", "Includes super"],
    "related_products": [],
    "bundle_offer": {
      "quantity": 3,
      "discount": 15,
      "description": "Buy 3, get 15% off"
    },
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  },
  "message": "Product created successfully"
}
```

**Error Response (400 - Too Many Images):**
```json
{
  "detail": "Maximum 3 images allowed (1 main + 2 additional). You provided 4 images."
}
```

---

### 9. Update Product (Admin Only)

**Endpoint:** `PATCH /v1/products/{product_id}`

**Description:** Update product details with optional image uploads (requires admin authentication).

**Request Headers:**
```
Content-Type: multipart/form-data
Authorization: Bearer <admin_token>
```

**Path Parameters:**
- `product_id` (required): UUID of the product

**Request Body (multipart/form-data, all fields optional):**
- `name` (string): Product name
- `description` (string): Product description
- `price` (integer): Product price in cents
- `category` (string): Category
- `stock` (integer): Stock quantity
- `image_cover` (file): New main product image (file upload)
- `additional_images` (file[]): New additional images, max 2 (file uploads)
- `tags` (string): JSON array of tags
- `features` (string): JSON array of features
- `related_products` (string): JSON array of related product UUIDs
- `bundle_offer` (string): JSON object with bundle offer details

**Example using cURL (update main image and price):**
```bash
curl -X PATCH "http://localhost:8000/v1/products/{product_id}" \
  -H "Authorization: Bearer <admin_token>" \
  -F "image_cover=@/path/to/new-main-image.jpg" \
  -F "price=2000"
```

**Example (update all images):**
```bash
curl -X PATCH "http://localhost:8000/v1/products/{product_id}" \
  -H "Authorization: Bearer <admin_token>" \
  -F "image_cover=@/path/to/new-main.jpg" \
  -F "additional_images=@/path/to/new-additional1.jpg" \
  -F "additional_images=@/path/to/new-additional2.jpg"
```

**Notes:**
- All fields are optional - only provide fields you want to update
- Providing new images will replace existing ones
- Maximum 3 images total (1 main + 2 additional)
- Complex fields must be JSON strings

**Response Body (Success - 200):**
```json
{
  "success": true,
  "data": {
    "id": "uuid-string",
    "name": "Updated Name",
    "price": 2000,
    "image_cover": "/uploads/images/new-main.jpg",
    "images": [
      "/uploads/images/new-additional1.jpg",
      "/uploads/images/new-additional2.jpg"
    ],
    "stock": 75,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-02T00:00:00Z"
  },
  "message": null
}
```

---

### 10. Delete Product (Admin Only)

**Endpoint:** `DELETE /v1/products/{product_id}`

**Description:** Delete a product (requires admin authentication).

**Request Headers:**
```
Authorization: Bearer <admin_token>
```

**Path Parameters:**
- `product_id` (required): UUID of the product

**Response Body (Success - 200):**
```json
{
  "success": true,
  "message": "Product deleted successfully"
}
```

---

## Orders

### 1. Create Order

**Endpoint:** `POST /v1/orders`

**Description:** Create a new order.

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "customerName": "John Doe",
  "email": "john@example.com",
  "phone": "+254712345678",
  "address": "123 Main Street",
  "city": "Nairobi",
  "county": "Nairobi",
  "items": [
    {
      "productId": "uuid-string",
      "quantity": 2
    },
    {
      "productId": "uuid-string-2",
      "quantity": 1
    }
  ],
  "paymentMethod": "mpesa",  // or "cash"
  "mpesaPhone": "+254712345678"  // Required if paymentMethod is "mpesa"
}
```

**Response Body (Success - 200):**
```json
{
  "success": true,
  "data": {
    "id": "ORD-20240101-ABCD",
    "customerName": "John Doe",
    "email": "john@example.com",
    "phone": "+254712345678",
    "address": "123 Main Street",
    "city": "Nairobi",
    "county": "Nairobi",
    "items": [
      {
        "productId": "uuid-string",
        "productName": "Lavender Dreams",
        "quantity": 2,
        "price": 1500
      }
    ],
    "subtotal": 3000,
    "shipping": 300,
    "total": 3300,
    "paymentMethod": "mpesa",
    "mpesaPhone": "+254712345678",
    "mpesaTransactionId": null,
    "status": "pending",
    "orderDate": "2024-01-01",
    "createdAt": "2024-01-01T00:00:00Z",
    "updatedAt": "2024-01-01T00:00:00Z"
  },
  "message": null
}
```

---

### 2. Search Orders

**Endpoint:** `GET /v1/orders/search`

**Description:** Search orders by order ID, customer name, email, or phone.

**Request Headers:**
```
Content-Type: application/json
```

**Query Parameters:**
- `q` (required): Search query string

**Example Request:**
```
GET /v1/orders/search?q=john@example.com
```

**Response Body (Success - 200):**
```json
{
  "success": true,
  "message": "Orders found",
  "data": [
    {
      "id": "ORD-20240101-ABCD",
      "customerName": "John Doe",
      "email": "john@example.com",
      ...
    }
  ]
}
```

---

### 3. Get Order by ID

**Endpoint:** `GET /v1/orders/{order_id}`

**Description:** Retrieve a specific order by its ID.

**Request Headers:**
```
Content-Type: application/json
```

**Path Parameters:**
- `order_id` (required): Order ID (e.g., "ORD-20240101-ABCD")

**Response Body (Success - 200):**
```json
{
  "success": true,
  "data": {
    "id": "ORD-20240101-ABCD",
    "customerName": "John Doe",
    "email": "john@example.com",
    "phone": "+254712345678",
    "address": "123 Main Street",
    "city": "Nairobi",
    "county": "Nairobi",
    "items": [...],
    "subtotal": 3000,
    "shipping": 300,
    "total": 3300,
    "paymentMethod": "mpesa",
    "status": "pending",
    "orderDate": "2024-01-01",
    "createdAt": "2024-01-01T00:00:00Z",
    "updatedAt": "2024-01-01T00:00:00Z"
  },
  "message": null
}
```

---

### 4. Get All Orders

**Endpoint:** `GET /v1/orders`

**Description:** Get all orders or filter by customer email.

**Request Headers:**
```
Content-Type: application/json
```

**Query Parameters:**
- `email` (optional): Filter orders by customer email

**Example Request:**
```
GET /v1/orders?email=john@example.com
```

**Response Body (Success - 200):**
```json
{
  "success": true,
  "message": "Orders retrieved successfully",
  "data": [
    {
      "id": "ORD-20240101-ABCD",
      "customerName": "John Doe",
      ...
    }
  ]
}
```

---

### 5. Track Order

**Endpoint:** `GET /v1/orders/{order_id}/track`

**Description:** Track order status and get tracking information.

**Request Headers:**
```
Content-Type: application/json
```

**Path Parameters:**
- `order_id` (required): Order ID

**Response Body (Success - 200):**
```json
{
  "success": true,
  "message": "Order tracking information",
  "data": {
    "id": "ORD-20240101-ABCD",
    "status": "shipped",
    "orderDate": "2024-01-01",
    ...
  }
}
```

---

### 6. Update Order

**Endpoint:** `PATCH /v1/orders/{order_id}`

**Description:** Update order details (only for pending orders).

**Request Headers:**
```
Content-Type: application/json
```

**Path Parameters:**
- `order_id` (required): Order ID

**Request Body (all fields optional):**
```json
{
  "customerName": "Jane Doe",
  "phone": "+254798765432",
  "address": "456 New Street",
  "city": "Mombasa",
  "county": "Mombasa"
}
```

**Response Body (Success - 200):**
```json
{
  "success": true,
  "data": {
    "id": "ORD-20240101-ABCD",
    "customerName": "Jane Doe",
    "phone": "+254798765432",
    ...
  },
  "message": null
}
```

---

### 7. Update Order Status

**Endpoint:** `PATCH /v1/orders/{order_id}/status`

**Description:** Update order status.

**Request Headers:**
```
Content-Type: application/json
```

**Path Parameters:**
- `order_id` (required): Order ID

**Request Body:**
```json
{
  "status": "shipped",  // Options: "pending", "paid", "processing", "shipped", "delivered", "cancelled"
  "mpesaTransactionId": "ABC123XYZ"  // Optional, for M-Pesa payments
}
```

**Response Body (Success - 200):**
```json
{
  "success": true,
  "data": {
    "id": "ORD-20240101-ABCD",
    "status": "shipped",
    "mpesaTransactionId": "ABC123XYZ",
    ...
  },
  "message": null
}
```

---

### 8. Cancel Order

**Endpoint:** `PATCH /v1/orders/{order_id}/cancel`

**Description:** Cancel an order (only for pending or paid orders).

**Request Headers:**
```
Content-Type: application/json
```

**Path Parameters:**
- `order_id` (required): Order ID

**Response Body (Success - 200):**
```json
{
  "success": true,
  "message": "Order cancelled successfully"
}
```

---

## Reviews

### 1. Get Product Reviews

**Endpoint:** `GET /v1/products/{product_id}/reviews`

**Description:** Get all reviews for a specific product.

**Request Headers:**
```
Content-Type: application/json
```

**Path Parameters:**
- `product_id` (required): UUID of the product

**Query Parameters:**
- `verified_only` (optional, default: false): Show only verified reviews

**Example Request:**
```
GET /v1/products/123e4567-e89b-12d3-a456-426614174000/reviews?verified_only=true
```

**Response Body (Success - 200):**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid-string",
      "product_id": "uuid-string",
      "author": "Jane Smith",
      "email": "jane@example.com",
      "rating": 5,
      "comment": "Amazing candle! Smells wonderful.",
      "date": "2024-01-01",
      "verified": true,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

---

### 2. Create Product Review

**Endpoint:** `POST /v1/products/{product_id}/reviews`

**Description:** Submit a review for a product.

**Request Headers:**
```
Content-Type: application/json
```

**Path Parameters:**
- `product_id` (required): UUID of the product

**Request Body:**
```json
{
  "author": "Jane Smith",
  "email": "jane@example.com",  // Optional
  "rating": 5,  // Integer between 1-5
  "comment": "Amazing candle! Smells wonderful."
}
```

**Response Body (Success - 200):**
```json
{
  "success": true,
  "data": {
    "id": "new-uuid-string",
    "product_id": "uuid-string",
    "author": "Jane Smith",
    "email": "jane@example.com",
    "rating": 5,
    "comment": "Amazing candle! Smells wonderful.",
    "date": "2024-01-01",
    "verified": false,
    "created_at": "2024-01-01T00:00:00Z"
  },
  "message": null
}
```

---

### 3. Get All Reviews (Admin Only)

**Endpoint:** `GET /v1/admin/reviews`

**Description:** Get all reviews with optional filtering by verified status (requires admin authentication).

**Request Headers:**
```
Content-Type: application/json
Authorization: Bearer <admin_token>
```

**Query Parameters:**
- `verified` (optional): Filter by verified status
  - `true` - Only verified reviews
  - `false` - Only unverified reviews
  - Not specified - All reviews

**Example Request:**
```
GET /v1/admin/reviews?verified=false
```

**Response Body (Success - 200):**
```json
{
  "success": true,
  "data": {
    "reviews": [
      {
        "id": "uuid-string",
        "product_id": "uuid-string",
        "author": "Jane Smith",
        "email": "jane@example.com",
        "rating": 5,
        "comment": "Amazing candle! Smells wonderful.",
        "date": "2024-01-01",
        "verified": false,
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "count": 50,
    "verified_count": 30,
    "unverified_count": 20
  }
}
```

---

### 4. Verify Product Review (Admin Only)

**Endpoint:** `PATCH /v1/products/{product_id}/reviews/{review_id}/verify`

**Description:** Verify a product review (marks it as verified). Requires admin authentication.

**Request Headers:**
```
Content-Type: application/json
Authorization: Bearer <admin_token>
```

**Path Parameters:**
- `product_id` (required): UUID of the product
- `review_id` (required): UUID of the review

**Example Request:**
```
PATCH /v1/products/123e4567-e89b-12d3-a456-426614174000/reviews/987e6543-e21b-12d3-a456-426614174000/verify
```

**Response Body (Success - 200):**
```json
{
  "success": true,
  "message": "Review verified successfully",
  "data": {
    "id": "uuid-string",
    "product_id": "uuid-string",
    "author": "Jane Smith",
    "email": "jane@example.com",
    "rating": 5,
    "comment": "Amazing candle!",
    "date": "2024-01-01",
    "verified": true,
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

---

### 5. Unverify Product Review (Admin Only)

**Endpoint:** `PATCH /v1/products/{product_id}/reviews/{review_id}/unverify`

**Description:** Unverify a product review (removes verified status). Requires admin authentication.

**Request Headers:**
```
Content-Type: application/json
Authorization: Bearer <admin_token>
```

**Path Parameters:**
- `product_id` (required): UUID of the product
- `review_id` (required): UUID of the review

**Example Request:**
```
PATCH /v1/products/123e4567-e89b-12d3-a456-426614174000/reviews/987e6543-e21b-12d3-a456-426614174000/unverify
```

**Response Body (Success - 200):**
```json
{
  "success": true,
  "message": "Review unverified successfully",
  "data": {
    "id": "uuid-string",
    "product_id": "uuid-string",
    "author": "Jane Smith",
    "email": "jane@example.com",
    "rating": 5,
    "comment": "Amazing candle!",
    "date": "2024-01-01",
    "verified": false,
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

---

### 6. Delete Product Review (Admin Only)

**Endpoint:** `DELETE /v1/products/{product_id}/reviews/{review_id}`

**Description:** Delete a product review. Requires admin authentication.

**Request Headers:**
```
Content-Type: application/json
Authorization: Bearer <admin_token>
```

**Path Parameters:**
- `product_id` (required): UUID of the product
- `review_id` (required): UUID of the review

**Example Request:**
```
DELETE /v1/products/123e4567-e89b-12d3-a456-426614174000/reviews/987e6543-e21b-12d3-a456-426614174000
```

**Response Body (Success - 200):**
```json
{
  "success": true,
  "message": "Review deleted successfully"
}
```

---

## Newsletter

### 1. Subscribe to Newsletter

**Endpoint:** `POST /v1/newsletter/subscribe`

**Description:** Subscribe to the newsletter.

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "email": "subscriber@example.com"
}
```

**Response Body (Success - 200):**
```json
{
  "success": true,
  "message": "Successfully subscribed to newsletter"
}
```

---

### 2. Unsubscribe from Newsletter

**Endpoint:** `POST /v1/newsletter/unsubscribe`

**Description:** Unsubscribe from the newsletter.

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "email": "subscriber@example.com"
}
```

**Response Body (Success - 200):**
```json
{
  "success": true,
  "message": "Successfully unsubscribed from newsletter"
}
```

---

## Analytics

### 1. Get Dashboard Analytics

**Endpoint:** `GET /v1/analytics/dashboard`

**Description:** Get dashboard analytics (not yet implemented).

**Request Headers:**
```
Content-Type: application/json
```

**Response Body (Success - 200):**
```json
{
  "success": false,
  "error": {
    "code": "NOT_IMPLEMENTED",
    "message": "Analytics not yet implemented. See FASTAPI_ROUTES_EXAMPLES.md for implementation."
  }
}
```

---

## Health Check

### 1. Health Check

**Endpoint:** `GET /health`

**Description:** Check API health status.

**Request Headers:**
```
Content-Type: application/json
```

**Response Body (Success - 200):**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

---

### 2. Root Endpoint

**Endpoint:** `GET /`

**Description:** API root endpoint with basic information.

**Request Headers:**
```
Content-Type: application/json
```

**Response Body (Success - 200):**
```json
{
  "message": "HoneyBiz API",
  "docs": "/v1/docs"
}
```

---

## Error Responses

All endpoints may return error responses in the following format:

**Response Body (Error - 4xx/5xx):**
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Detailed error message"
  }
}
```

Common HTTP Status Codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

---

## Authentication

For endpoints marked as **(Admin Only)**, include the JWT token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

To obtain a token, use the `/v1/auth/login` or `/v1/auth/admin/login` endpoint.

---

## Notes

1. **Phone Number Format:** All phone numbers must be in the format `+254XXXXXXXXX` (Kenyan format).
2. **UUIDs:** Product IDs use UUID format (e.g., `123e4567-e89b-12d3-a456-426614174000`).
3. **Order IDs:** Order IDs use the format `ORD-YYYYMMDD-XXXX`.
4. **Dates:** All dates are in ISO 8601 format.
5. **Prices:** All prices are in Kenyan Shillings (KES) as integers (e.g., 1500 = KES 15.00).
6. **Pagination:** Default page size is 20 items, maximum is 100.

---

## Interactive API Documentation

For interactive API documentation, visit:
- **Swagger UI:** `http://your-domain/v1/docs`
- **ReDoc:** `http://your-domain/v1/redoc`
