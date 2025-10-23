from datetime import datetime, timedelta
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
from models import User
from sqlalchemy.orm import Session
from sqlalchemy import select
from models import engine
from contracts import SignupRequest, LoginRequest
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import cast

load_dotenv()

JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM')
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', '30'))

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def get_password_hash(password: str) -> str:
    return generate_password_hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return check_password_hash(hashed_password, plain_password)

def send_verification_email(email: str, token: str):
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT'))
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')
    from_email = os.getenv('SMTP_FROM_EMAIL')
    frontend_url = os.getenv('FRONTEND_URL')


    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = email
    msg['Subject'] = 'Verify your email'

    verification_link = f"{frontend_url}/verify-email?token={token}"
    
    body = f"""
    Welcome to our platform!
    
    Please verify your email by clicking on the following link:
    {verification_link}
    
    This link will expire in {JWT_ACCESS_TOKEN_EXPIRE_MINUTES} minutes.
    """
    
    msg.attach(MIMEText(body, 'plain'))


    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)

class AuthService:
    def __init__(self):
        pass

    def signup(self, request: SignupRequest):
        try:
            with Session(engine) as session:
            
                existing_user = session.scalar(
                    select(User).where(User.email == request.email)
                )
                if existing_user:
                    raise ValueError("Email already registered")

                hashed_password = get_password_hash(request.password)
                new_user = User(
                    email=request.email,
                    password_hash=hashed_password,
                    first_name=request.first_name,
                    last_name=request.last_name,
                    user_type=request.user_type,
                    is_email_verified=False
                )
                
                session.add(new_user)
                session.commit()
                session.refresh(new_user)
            
                verification_token = create_access_token(
                    {"sub": str(new_user.id), "type": "email_verification"}
                )
            
                # try:
                #     send_verification_email(request.email, verification_token)
                # except Exception as e:
                #     print(f"Failed to send verification email: {e}")

            
                access_token = create_access_token(
                    {"sub": str(new_user.id), "type": "access"}
                )

                return {
                    "user_id": str(new_user.id),
                    "access_token": access_token,
                    "token_type": "bearer"
                }
        except ValueError as ve:
            raise ve
        except Exception as e:
            print(f"Signup error: {str(e)}")
            raise Exception("An error occurred during signup")

        access_token = create_access_token(
            {"sub": str(new_user.id), "type": "access"}
        )

        return {
            "user_id": str(new_user.id),
            "access_token": access_token,
            "token_type": "bearer"
        }
    def login(self, request: LoginRequest):
        try:
        
            with Session(engine) as session:
            
                user = session.scalar(
                    select(User).where(User.email == request.email)
                )
                
                if not user:
                    raise ValueError("Invalid email or password")

            
                if not verify_password(request.password, str(user.password_hash)):
                    raise ValueError("Invalid email or password")

            
                access_token = create_access_token(
                    {"sub": str(user.id), "type": "access"}
                )

                return {
                    "access_token": access_token,
                    "token_type": "bearer"
                }
        except ValueError as ve:
        
            raise ve
        except Exception as e:
        
            print(f"Login error: {str(e)}")
            raise Exception("An error occurred during login")

    def verify_email(self, token: str):
        try:
            payload = verify_token(token)
            if not payload or payload.get("type") != "email_verification":
                raise ValueError("Invalid or expired verification token")

            user_id = int(payload["sub"])
            
            with Session(engine) as session:
                user = session.get(User, user_id)
                if not user:
                    raise ValueError("User not found")

                user.is_email_verified = True
                session.commit()

            return {"message": "Email verified successfully"}
        except ValueError as ve:
            raise ve
        except Exception as e:
            print(f"Email verification error: {str(e)}")
            raise Exception("An error occurred during email verification")
    
    def resend_verification_email(self, user_id: str):
        try:
            with Session(engine) as session:
                user = session.get(User, int(user_id))
                if not user:
                    raise ValueError("User not found")

                if user.is_email_verified:
                    raise ValueError("Email already verified")

                verification_token = create_access_token(
                    {"sub": user_id, "type": "email_verification"}
                )

                # send_verification_email(user.email, verification_token)
                return {"message": "Verification email sent successfully"}
        except ValueError as ve:
            raise ve
        except Exception as e:
            print(f"Resend verification error: {str(e)}")
            raise Exception("An error occurred while resending verification email")