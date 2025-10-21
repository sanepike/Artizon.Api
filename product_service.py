from sqlalchemy.orm import Session
from sqlalchemy import select, func
from models import Product, ProductImage
from typing import List, Optional
from contracts import (
    CreateProductRequest, CreateProductResponse, ProductResponse,
    ProductListRequest, ProductListResponse, ProductImage as ProductImageSchema
)
from firebase_config import upload_image_to_firebase
import uuid

class ProductService:
    def __init__(self, db: Session):
        self.db = db

    def create_product(self, request: CreateProductRequest, owner_id: int, images: Optional[List[tuple[bytes, str]]] = None) -> CreateProductResponse:
        new_product = Product(
            name=request.name,
            description=request.description,
            price=request.price,
            owner_id=owner_id
        )
        
        self.db.add(new_product)
        self.db.flush()

        product_images = []
        if images:
            for i, (image_file, original_filename) in enumerate(images):
                try:
                    original_filename = original_filename.lower()
                    
                    if original_filename.endswith('.jpg') or original_filename.endswith('.jpeg'):
                        file_extension = 'jpg'
                    elif original_filename.endswith('.png'):
                        file_extension = 'png'
                    elif original_filename.endswith('.gif'):
                        file_extension = 'gif'
                    elif original_filename.endswith('.webp'):
                        file_extension = 'webp'
                    else:
                        file_extension = 'jpg'
                        
                    filename = f"{uuid.uuid4()}.{file_extension}"
                    
                    image_url = upload_image_to_firebase(image_file, filename)
                    
                    product_image = ProductImage(
                        url=image_url,
                        is_primary=(i == 0),
                        product_id=new_product.id
                    )
                    self.db.add(product_image)
                    product_images.append(ProductImageSchema(
                        url=image_url,
                        is_primary=(i == 0)
                    ))
                except Exception as e:
                    raise ValueError(f"Failed to process image {i+1}: {str(e)}")
        
        self.db.commit()
        self.db.refresh(new_product)
        
        return CreateProductResponse(
            id=new_product.id,
            name=new_product.name,
            description=new_product.description,
            price=new_product.price,
            images=product_images,
            created_at_utc=new_product.created_at_utc,
            owner_id=new_product.owner_id
        )

    def get_all_products(self, request: ProductListRequest) -> ProductListResponse:
        skip = (request.page - 1) * request.limit
        
        total = self.db.scalar(select(func.count()).select_from(Product)) or 0
        
        total_pages = (total + request.limit - 1) // request.limit
        
        products = self.db.scalars(
            select(Product)
            .offset(skip)
            .limit(request.limit)
            .order_by(Product.created_at_utc.desc())
        ).all()
        
        return ProductListResponse(
            products=[
                ProductResponse(
                    id=product.id,
                    name=product.name,
                    description=product.description,
                    price=product.price,
                    images=[
                        ProductImageSchema(url=img.url, is_primary=img.is_primary)
                        for img in product.images
                    ],
                    created_at_utc=product.created_at_utc,
                    owner_id=product.owner_id
                )
                for product in products
            ],
            total=total,
            page=request.page,
            total_pages=total_pages
        )

    def get_my_products(self, owner_id: int, request: ProductListRequest) -> ProductListResponse:
        skip = (request.page - 1) * request.limit
        
        total = self.db.scalar(
            select(func.count())
            .select_from(Product)
            .where(Product.owner_id == owner_id)
        ) or 0
        
        total_pages = (total + request.limit - 1) // request.limit
        
        products = self.db.scalars(
            select(Product)
            .where(Product.owner_id == owner_id)
            .offset(skip)
            .limit(request.limit)
            .order_by(Product.created_at_utc.desc())
        ).all()
        
        return ProductListResponse(
            products=[
                ProductResponse(
                    id=product.id,
                    name=product.name,
                    description=product.description,
                    price=product.price,
                    images=[
                        ProductImageSchema(url=img.url, is_primary=img.is_primary)
                        for img in product.images
                    ],
                    created_at_utc=product.created_at_utc,
                    owner_id=product.owner_id
                )
                for product in products
            ],
            total=total,
            page=request.page,
            total_pages=total_pages
        )