from flask import Flask, request, jsonify
from firebase_config import initialize_firebase
from models import init_db
from auth import AuthService
from product_service import ProductService
from contracts import (
    SignupRequest, LoginRequest, VerifyEmailRequest, ResendEmailVerificationTokenRequest,
    CreateProductRequest, ProductListRequest, PlaceOrderRequest, OrderListRequest
)
from sqlalchemy.orm import Session
from models import engine
from functools import wraps
from auth import verify_token

app = Flask(__name__)
auth_service = AuthService()

initialize_firebase()

def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"error": "Missing authorization header"}), 401
        
        try:
            token_type, token = auth_header.split()
            if token_type.lower() != 'bearer':
                return jsonify({"error": "Invalid token type"}), 401
            
            payload = verify_token(token)
            if not payload:
                return jsonify({"error": "Invalid or expired token"}), 401
            
            return f(payload, *args, **kwargs)
        except Exception as e:
            return jsonify({"error": str(e)}), 401
    return decorated

@app.route('/auth/signup', methods=['POST'])
def signup():
    try:
        request_data = SignupRequest(**request.json)
        result = auth_service.signup(request_data)
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500

@app.route('/auth/login', methods=['POST'])
def login():
    try:
        request_data = LoginRequest(**request.json)
        result = auth_service.login(request_data)
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500

@app.route('/auth/verify-email', methods=['POST'])
def verify_email():
    try:
        request_data = VerifyEmailRequest(**request.json)
        result = auth_service.verify_email(request_data.verification_token)
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500

@app.route('/auth/resend-verification', methods=['POST'])
def resend_verification():
    try:
        request_data = ResendEmailVerificationTokenRequest(**request.json)
        result = auth_service.resend_verification_email(request_data.user_id)
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500


@app.route('/products/create', methods=['POST'])
@auth_required
def create_product(payload):
    try:
        product_data = request.form
        request_data = CreateProductRequest(
            name=product_data.get('name'),
            description=product_data.get('description'),
            price=float(product_data.get('price'))
        )
        
        user_id = int(payload['sub'])
        
        images = []
        if 'images' in request.files:
            image_files = request.files.getlist('images')
            for image in image_files:
                if image.filename:
                    images.append((image.read(), image.filename))
        
        with Session(engine) as db:
            product_service = ProductService(db)
            result = product_service.create_product(request_data, user_id, images)
            
        return jsonify(result.dict()), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500

@app.route('/products', methods=['GET'])
def get_all_products():
    try:
        request_data = ProductListRequest(
            page=int(request.args.get('page', 1)),
            limit=int(request.args.get('limit', 10))
        )

        with Session(engine) as db:
            product_service = ProductService(db)
            result = product_service.get_all_products(request_data)
            
        return jsonify(result.dict())
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500

@app.route('/products/my', methods=['GET'])
@auth_required
def get_my_products(payload):
    try:
        request_data = ProductListRequest(
            page=int(request.args.get('page', 1)),
            limit=int(request.args.get('limit', 10))
        )
        
        user_id = int(payload['sub'])

        with Session(engine) as db:
            product_service = ProductService(db)
            result = product_service.get_my_products(user_id, request_data)
            
        return jsonify(result.dict())
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500

@app.route('/orders/place', methods=['POST'])
@auth_required
def place_order(payload):
    try:
        request_data = PlaceOrderRequest(**request.json)
        customer_id = int(payload['sub'])

        with Session(engine) as db:
            from order_service import place_order as place_order_service
            result = place_order_service(db, request_data, customer_id)
            
        return jsonify(result.dict()), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/orders/vendor', methods=['GET'])
@auth_required
def get_vendor_orders(payload):
    try:
        vendor_id = int(payload['sub'])
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))

        with Session(engine) as db:
            from order_service import get_vendor_orders as get_vendor_orders_service
            orders, total = get_vendor_orders_service(db, vendor_id, page, limit)
            
            return jsonify({
                "orders": [order.dict() for order in orders],
                "total": total,
                "page": page,
                "total_pages": (total + limit - 1) // limit
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/orders/my', methods=['GET'])
@auth_required
def get_my_orders(payload):
    try:
        customer_id = int(payload['sub'])
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))

        with Session(engine) as db:
            from order_service import get_customer_orders as get_customer_orders_service
            orders, total = get_customer_orders_service(db, customer_id, page, limit)
            
            return jsonify({
                "orders": [order.dict() for order in orders],
                "total": total,
                "page": page,
                "total_pages": (total + limit - 1) // limit
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    return 'Service running - healthy'

if __name__ == '__main__':
    init_db()
    initialize_firebase()
    app.run(debug=True)
