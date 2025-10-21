from datetime import datetime
from typing import List, Optional
from sqlalchemy import create_engine, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL must be set in environment variables")

engine = create_engine(
    DATABASE_URL,
    connect_args={
        'sslmode': 'require',
        'target_session_attrs': 'read-write'
    },
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True
)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    user_type: Mapped[str] = mapped_column(String(20), nullable=False)
    is_email_verified: Mapped[bool] = mapped_column(default=False)
    created_at_utc: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    # Relationships
    orders: Mapped[List["Order"]] = relationship(back_populates='customer')
    products: Mapped[List["Product"]] = relationship(back_populates='owner')

    def __repr__(self) -> str:
        return f'<User {self.email}>'

class Product(Base):
    __tablename__ = 'products'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    price: Mapped[float] = mapped_column(nullable=False)
    created_at_utc: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)

    # Relationships
    images: Mapped[List["ProductImage"]] = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")

    # Relationships
    order_items: Mapped[List["OrderItem"]] = relationship(back_populates='product')
    owner: Mapped["User"] = relationship(back_populates='products')

    def __repr__(self) -> str:
        return f'<Product {self.name}>'

class Order(Base):
    __tablename__ = 'orders'

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    total_amount: Mapped[float] = mapped_column(nullable=False)
    shipping_address: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default='PLACED')
    created_at_utc: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    customer: Mapped["User"] = relationship(back_populates='orders')
    items: Mapped[List["OrderItem"]] = relationship(back_populates='order', cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f'<Order {self.id}>'

class ProductImage(Base):
    __tablename__ = 'product_images'

    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    is_primary: Mapped[bool] = mapped_column(default=False)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'), nullable=False)
    created_at_utc: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    product: Mapped["Product"] = relationship(back_populates='images')

    def __repr__(self) -> str:
        return f'<ProductImage {self.id}>'

class OrderItem(Base):
    __tablename__ = 'order_items'

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.id'), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'), nullable=False)
    product_name: Mapped[str] = mapped_column(String(100), nullable=False)
    product_price: Mapped[float] = mapped_column(nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    total_price: Mapped[float] = mapped_column(nullable=False)

    # Relationships
    order: Mapped["Order"] = relationship(back_populates='items')
    product: Mapped["Product"] = relationship(back_populates='order_items')

    def __repr__(self) -> str:
        return f'<OrderItem {self.id}>'

def init_db():
    Base.metadata.create_all(engine)
