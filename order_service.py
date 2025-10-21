from sqlalchemy.orm import Session
from models import Order, OrderItem, Product, User
from contracts import PlaceOrderRequest, OrderResponse, OrderItem as OrderItemResponse
from sqlalchemy import and_, or_
from datetime import datetime
from typing import List, Tuple

def place_order(db: Session, request: PlaceOrderRequest, customer_id: int) -> OrderResponse:
    total_amount = 0
    order_items = []
    
    product_ids = [item.product_id for item in request.items]
    
    products = {p.id: p for p in db.query(Product).filter(Product.id.in_(product_ids)).all()}
    
    for item in request.items:
        product = products.get(item.product_id)
        if not product:
            raise ValueError(f"Product with ID {item.product_id} not found")
            
        item_total = product.price * item.quantity
        total_amount += item_total
        
        order_items.append({
            "product": product,
            "quantity": item.quantity,
            "price_at_time": product.price,
            "total_price": item_total
        })

    order = Order(
        customer_id=customer_id,
        total_amount=total_amount,
        shipping_address=request.shipping_address,
        status="PLACED",
        created_at_utc=datetime.utcnow()
    )
    db.add(order)
    db.flush()

    for item in order_items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item["product"].id,
            product_name=item["product"].name,
            product_price=item["price_at_time"],
            quantity=item["quantity"],
            total_price=item["total_price"]
        )
        db.add(order_item)

    db.commit()
    
    return get_order_by_id(db, order.id)

def get_order_by_id(db: Session, order_id: int) -> OrderResponse:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise ValueError(f"Order with ID {order_id} not found")
        
    return create_order_response(order)

def get_vendor_orders(db: Session, vendor_id: int, page: int = 1, limit: int = 10) -> Tuple[List[OrderResponse], int]:
    vendor_product_ids = db.query(Product.id).filter(Product.owner_id == vendor_id).all()
    vendor_product_ids = [p[0] for p in vendor_product_ids]
    
    if not vendor_product_ids:
        return [], 0
        
    base_query = db.query(Order).join(OrderItem).filter(OrderItem.product_id.in_(vendor_product_ids))
    
    total = base_query.count()
    
    orders = base_query.order_by(Order.created_at_utc.desc()) \
        .offset((page - 1) * limit) \
        .limit(limit) \
        .all()
    
    return [create_order_response(order) for order in orders], total

def get_customer_orders(db: Session, customer_id: int, page: int = 1, limit: int = 10) -> Tuple[List[OrderResponse], int]:
    base_query = db.query(Order).filter(Order.customer_id == customer_id)
    
    total = base_query.count()
    
    orders = base_query.order_by(Order.created_at_utc.desc()) \
        .offset((page - 1) * limit) \
        .limit(limit) \
        .all()
    
    return [create_order_response(order) for order in orders], total

def create_order_response(order: Order) -> OrderResponse:
    return OrderResponse(
        id=order.id,
        customer_id=order.customer_id,
        items=[
            OrderItemResponse(
                id=item.id,
                product_id=item.product_id,
                product_name=item.product_name,
                product_price=item.product_price,
                quantity=item.quantity,
                total_price=item.total_price
            ) for item in order.items
        ],
        total_amount=order.total_amount,
        shipping_address=order.shipping_address,
        status=order.status,
        created_at_utc=order.created_at_utc
    )