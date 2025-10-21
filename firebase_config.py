import firebase_admin
from firebase_admin import credentials, storage
import os
from dotenv import load_dotenv

load_dotenv()

def initialize_firebase():
    cred = credentials.Certificate('firebase-credentials.json')
    firebase_admin.initialize_app(cred, {
        'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET')
    })

def upload_image_to_firebase(file_bytes: bytes, filename: str) -> str:
    try:
        if not firebase_admin._apps:
            raise ValueError("Firebase app not initialized. Call initialize_firebase() first")

        if not file_bytes:
            raise ValueError("Empty file data received")

        try:
            bucket = storage.bucket()
        except Exception as e:
            raise ValueError(f"Failed to get storage bucket. Check FIREBASE_STORAGE_BUCKET env variable. Error: {str(e)}")

        content_type = 'application/octet-stream'
        if filename.lower().endswith(('.jpg', '.jpeg')):
            content_type = 'image/jpeg'
        elif filename.lower().endswith('.png'):
            content_type = 'image/png'
        elif filename.lower().endswith('.gif'):
            content_type = 'image/gif'
        elif filename.lower().endswith('.webp'):
            content_type = 'image/webp'

        try:
            import uuid
            unique_filename = f"{uuid.uuid4()}_{filename}"
            blob = bucket.blob(f'product_images/{unique_filename}')
            
            blob.upload_from_string(
                file_bytes,
                content_type=content_type
            )
        except Exception as e:
            raise ValueError(f"Failed to upload file to Firebase Storage: {str(e)}")
        
        try:
            blob.make_public()
        except Exception as e:
            try:
                blob.delete()
            except:
                pass
            raise ValueError(f"Failed to make file public: {str(e)}")
        
        if not blob.public_url:
            raise ValueError("Failed to get public URL after upload")
            
        return blob.public_url

    except Exception as e:
        print(f"Firebase upload error: {str(e)}")
        raise Exception(f"Failed to upload image: {str(e)}")