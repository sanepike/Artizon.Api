from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enums import UserTypeEnum

class SignupRequest(BaseModel):
    first_name: str = Field(..., min_length=1, description="User's first name")
    last_name: str = Field(..., min_length=1, description="User's last name")
    user_type: UserTypeEnum = Field(..., min_length=1, description="User type")
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, description="Password for the user")

class SignupResponse(BaseModel):
    user_id: str = Field(..., description="ID of the created user")
    access_token: str = Field(..., description="JWT token for authentication")
    token_type: str = Field("bearer", description="Type of the token")

class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, description="User's password")

class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT token for authentication")
    token_type: str = Field("bearer", description="Type of the token")

class VerifyEmailRequest(BaseModel):
    verification_token: str = Field(..., description="Token for email verification of the user")

class ResendEmailVerificationTokenRequest(BaseModel):
    user_id: str = Field(..., description="User who want to resend email verification token")


class ProductImage(BaseModel):
    url: str = Field(..., description="URL of the uploaded image")
    is_primary: bool = Field(default=False, description="Whether this is the primary product image")

class CreateProductRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Name of the product")
    description: Optional[str] = Field(None, max_length=500, description="Detailed description of the product")
    price: float = Field(..., gt=0, description="Price of the product")

class CreateProductResponse(BaseModel):
    id: int = Field(..., description="Unique identifier of the created product")
    name: str = Field(..., description="Name of the product")
    description: Optional[str] = Field(None, description="Detailed description of the product")
    price: float = Field(..., description="Price of the product")
    images: List[ProductImage] = Field(default=[], description="List of product images")
    created_at_utc: datetime = Field(..., description="Timestamp when the product was created")
    owner_id: int = Field(..., description="ID of the product owner")

class ProductResponse(BaseModel):
    id: int = Field(..., description="Unique identifier of the product")
    name: str = Field(..., description="Name of the product")
    description: Optional[str] = Field(None, description="Detailed description of the product")
    price: float = Field(..., description="Price of the product")
    images: List[ProductImage] = Field(default=[], description="List of product images")
    created_at_utc: datetime = Field(..., description="Timestamp when the product was created")
    owner_id: int = Field(..., description="ID of the product owner")

class ProductListRequest(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number for pagination")
    limit: int = Field(default=10, ge=1, le=100, description="Number of items per page")

class ProductListResponse(BaseModel):
    products: List[ProductResponse] = Field(..., description="List of products")
    total: int = Field(..., description="Total number of products")
    page: int = Field(..., description="Current page number")
    total_pages: int = Field(..., description="Total number of pages available")

class OrderItemRequest(BaseModel):
    product_id: int = Field(..., description="ID of the product being ordered")
    quantity: int = Field(..., gt=0, description="Quantity of the product")

class PlaceOrderRequest(BaseModel):
    items: List[OrderItemRequest] = Field(default=..., description="List of items to order")
    shipping_address: str = Field(..., min_length=1, description="Shipping address for the order")

    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {"product_id": 1, "quantity": 2},
                    {"product_id": 2, "quantity": 1}
                ],
                "shipping_address": "123 Main St, City, Country"
            }
        }

class OrderItem(BaseModel):
    id: int = Field(..., description="ID of the order item")
    product_id: int = Field(..., description="ID of the product")
    product_name: str = Field(..., description="Name of the product at time of order")
    product_price: float = Field(..., description="Price of the product at time of order")
    quantity: int = Field(..., description="Quantity ordered")
    total_price: float = Field(..., description="Total price for this item")

class OrderResponse(BaseModel):
    id: int = Field(..., description="Unique identifier of the order")
    customer_id: int = Field(..., description="ID of the customer who placed the order")
    items: List[OrderItem] = Field(..., description="List of items in the order")
    total_amount: float = Field(..., description="Total amount of the order")
    shipping_address: str = Field(..., description="Shipping address for the order")
    status: str = Field(..., description="Current status of the order")
    created_at_utc: datetime = Field(..., description="Timestamp when the order was created")

class OrderListResponse(BaseModel):
    orders: List[OrderResponse] = Field(..., description="List of orders")
    total: int = Field(..., description="Total number of orders")
    page: int = Field(..., description="Current page number")
    total_pages: int = Field(..., description="Total number of pages available")

class OrderListRequest(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number for pagination")
    limit: int = Field(default=10, ge=1, le=100, description="Number of items per page")

class UpdateOrderStatusRequest(BaseModel):
    status: str = Field(..., description="New status for the order (PLACED, SHIPPED, DELIVERED, CANCELLED)")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "SHIPPED"
            }
        }