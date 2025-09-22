from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import hashlib
import jwt
import json
import zipfile
import io
import random


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="PostaDepo API", description="E-posta Yönetim Sistemi API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()
JWT_SECRET = "postadepo-secret-key-2024"
JWT_ALGORITHM = "HS256"

# Helper functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_jwt_token(user_data: dict) -> str:
    payload = {
        "user_id": user_data["id"],
        "email": user_data["email"],
        "exp": datetime.now(timezone.utc).timestamp() + 86400  # 24 hours
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_jwt_token(token)
    user = await db.users.find_one({"id": payload["user_id"]})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# Models
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: EmailStr
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Email(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    folder: str  # inbox, sent, all, deleted, spam
    sender: str
    recipient: str
    subject: str
    content: str
    preview: str
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    read: bool = False
    important: bool = False
    size: int = 1024  # in bytes, default 1KB

class EmailResponse(BaseModel):
    emails: List[Dict[str, Any]]
    folderCounts: Dict[str, int]

class StorageInfo(BaseModel):
    totalEmails: int
    totalSize: int

class ConnectedAccount(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    type: str  # outlook, gmail
    email: str
    connected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
# Demo data generation
def generate_demo_emails(user_id: str) -> List[Dict[str, Any]]:
    senders = [
        "ali.kaya@gmail.com", "mehmet.demir@outlook.com", "fatma.yilmaz@hotmail.com",
        "ahmet.ozkan@gmail.com", "ayse.celik@yahoo.com", "mustafa.arslan@gmail.com",
        "zeynep.koc@outlook.com", "omer.sahin@hotmail.com", "elif.yildiz@gmail.com",
        "burak.ozer@yahoo.com"
    ]
    
    subjects = [
        "Önemli Toplantı Davetiyesi", "Proje Güncellemesi", "Hesap Bilgileri",
        "Yeni Ürün Lansmanı", "Fatura Bildirimi", "Tatil Planları",
        "İş Başvurusu", "Konferans Davetiyesi", "Sistem Bakımı Bildirimi",
        "Özel İndirim Fırsatı", "Güvenlik Uyarısı", "Etkinlik Duyurusu"
    ]
    
    folders = ["inbox", "sent", "spam"]
    
    emails = []
    for i in range(50):
        sender = random.choice(senders)
        subject = random.choice(subjects)
        content = f"Bu bir demo e-posta içeriğidir. {subject} konusunda detaylı bilgi için lütfen eki kontrol ediniz.\n\nSaygılarımla,\n{sender.split('@')[0].replace('.', ' ').title()}"
        
        # Calculate more realistic email size
        content_size = len(content.encode('utf-8'))
        subject_size = len(subject.encode('utf-8'))
        header_size = len(sender.encode('utf-8')) + 200  # approximate header size
        total_size = content_size + subject_size + header_size + random.randint(512, 2048)  # Add some variance
        
        email = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "folder": random.choice(folders),
            "sender": sender,
            "recipient": "demo@postadepo.com",
            "subject": subject,
            "content": content,
            "preview": content[:100] + "..." if len(content) > 100 else content,
            "date": datetime.now(timezone.utc).isoformat(),
            "read": random.choice([True, False]),
            "important": random.choice([True, False]) if random.random() < 0.3 else False,
            "size": total_size
        }
        emails.append(email)
    
    return emails

# Routes
@api_router.post("/auth/register")
async def register(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Bu e-posta adresi zaten kayıtlı")
    
    # Create new user
    hashed_password = hash_password(user_data.password)
    new_user = User(name=user_data.name, email=user_data.email)
    
    # Save user to database
    user_dict = new_user.dict()
    user_dict["password"] = hashed_password
    await db.users.insert_one(user_dict)
    
    return {"message": "Kullanıcı başarıyla oluşturuldu", "user_id": new_user.id}

@api_router.post("/auth/login")
async def login(user_data: UserLogin):
    # Demo user check
    if user_data.email == "demo@postadepo.com" and user_data.password == "demo123":
        # Check if demo user exists
        existing_user = await db.users.find_one({"email": user_data.email})
        
        if not existing_user:
            # Create demo user
            demo_user = User(name="Demo Kullanıcı", email=user_data.email)
            user_dict = demo_user.dict()
            user_dict["password"] = hash_password(user_data.password)
            await db.users.insert_one(user_dict)
            
            # Generate demo emails
            demo_emails = generate_demo_emails(demo_user.id)
            if demo_emails:
                await db.emails.insert_many(demo_emails)
            
            user = demo_user
        else:
            # Handle existing user without name field
            if 'name' not in existing_user:
                existing_user['name'] = 'Demo Kullanıcı'
                # Update the user in database
                await db.users.update_one(
                    {"email": user_data.email},
                    {"$set": {"name": "Demo Kullanıcı"}}
                )
            user = User(**existing_user)
        
        token = create_jwt_token(user.dict())
        return {
            "token": token,
            "user": {"id": user.id, "name": user.name, "email": user.email}
        }
    
    # Regular user login
    user = await db.users.find_one({"email": user_data.email})
    if not user:
        raise HTTPException(status_code=401, detail="Geçersiz e-posta veya şifre")
    
    hashed_password = hash_password(user_data.password)
    if user["password"] != hashed_password:
        raise HTTPException(status_code=401, detail="Geçersiz e-posta veya şifre")
    
    # Handle existing user without name field
    if 'name' not in user:
        user['name'] = user['email'].split('@')[0].title()
        # Update the user in database
        await db.users.update_one(
            {"email": user_data.email},
            {"$set": {"name": user['name']}}
        )
    
    user_obj = User(**user)
    token = create_jwt_token(user_obj.dict())
    return {
        "token": token,
        "user": {"id": user_obj.id, "name": user_obj.name, "email": user_obj.email}
    }

@api_router.get("/emails")
async def get_emails(folder: str = "inbox", current_user: dict = Depends(get_current_user)):
    query = {"user_id": current_user["id"]}
    
    if folder != "all":
        query["folder"] = folder
    
    # Get emails for specific folder
    emails_cursor = db.emails.find(query).sort("date", -1)
    emails = await emails_cursor.to_list(length=None)
    
    # Clean up emails for response
    cleaned_emails = []
    for email in emails:
        email_dict = dict(email)
        if "_id" in email_dict:
            del email_dict["_id"]
        cleaned_emails.append(email_dict)
    
    # Get folder counts
    folder_counts = {}
    for folder_type in ["inbox", "sent", "all", "deleted", "spam"]:
        if folder_type == "all":
            count = await db.emails.count_documents({"user_id": current_user["id"]})
        else:
            count = await db.emails.count_documents({"user_id": current_user["id"], "folder": folder_type})
        folder_counts[folder_type] = count
    
    return EmailResponse(emails=cleaned_emails, folderCounts=folder_counts)

@api_router.get("/storage-info")
async def get_storage_info(current_user: dict = Depends(get_current_user)):
    # Get total email count
    total_emails = await db.emails.count_documents({"user_id": current_user["id"]})
    
    # Calculate total size
    pipeline = [
        {"$match": {"user_id": current_user["id"]}},
        {"$group": {"_id": None, "totalSize": {"$sum": "$size"}}}
    ]
    
    result = await db.emails.aggregate(pipeline).to_list(length=1)
    total_size = result[0]["totalSize"] if result else 0
    
    return StorageInfo(totalEmails=total_emails, totalSize=total_size)

@api_router.put("/emails/{email_id}/read")
async def mark_email_read(email_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.emails.update_one(
        {"id": email_id, "user_id": current_user["id"]},
        {"$set": {"read": True}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Email not found")
    
    return {"success": True}

@api_router.delete("/emails/{email_id}")
async def delete_email(email_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.emails.delete_one(
        {"id": email_id, "user_id": current_user["id"]}
    )
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Email not found")
    
    return {"success": True, "message": "Email permanently deleted"}

@api_router.post("/sync-emails")
async def sync_emails(current_user: dict = Depends(get_current_user)):
    # Simulate email sync by adding a few new demo emails
    new_emails = []
    for i in range(3):
        total_size = random.randint(1024, 5120)  # 1-5KB
        email = {
            "id": str(uuid.uuid4()),
            "user_id": current_user["id"],
            "folder": "inbox",
            "sender": f"sync{i}@example.com",
            "recipient": current_user["email"],
            "subject": f"Senkronizasyon Sonucu Yeni E-posta {i+1}",
            "content": f"Bu e-posta senkronizasyon işlemi sonucu eklenen demo e-postadır. Timestamp: {datetime.now(timezone.utc)}",
            "preview": "Bu e-posta senkronizasyon işlemi sonucu eklenen demo e-postadır...",
            "date": datetime.now(timezone.utc).isoformat(),
            "read": False,
            "important": False,
            "size": total_size
        }
        new_emails.append(email)
    
    if new_emails:
        await db.emails.insert_many(new_emails)
    
    return {"success": True, "new_emails": len(new_emails)}

@api_router.post("/import-emails")
async def import_emails(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    if not file.filename.lower().endswith(('.pst', '.ost', '.eml')):
        raise HTTPException(status_code=400, detail="Desteklenmeyen dosya formatı")
    
    # Read file content
    content = await file.read()
    file_size = len(content)
    
    # Generate demo emails based on file size (simulate parsing)
    email_count = min(max(file_size // 1000, 1), 20)  # 1-20 emails based on file size
    
    imported_emails = []
    for i in range(email_count):
        email_size = random.randint(1024, 8192)  # 1-8KB per email
        email = {
            "id": str(uuid.uuid4()),
            "user_id": current_user["id"],
            "folder": "inbox",
            "sender": f"imported{i}@example.com",
            "recipient": current_user["email"],
            "subject": f"İçe Aktarılan E-posta {i+1} - {file.filename}",
            "content": f"Bu e-posta {file.filename} dosyasından içe aktarılmıştır. Orijinal boyut: {file_size} bytes\n\nİçerik özeti: Dosyadan başarıyla içe aktarılan e-posta verisi.",
            "preview": f"Bu e-posta {file.filename} dosyasından içe aktarılmıştır...",
            "date": datetime.now(timezone.utc).isoformat(),
            "read": False,
            "important": False,
            "size": email_size
        }
        imported_emails.append(email)
    
    if imported_emails:
        await db.emails.insert_many(imported_emails)
    
    return {"success": True, "count": len(imported_emails)}

@api_router.post("/export-emails")
async def export_emails(request: dict, current_user: dict = Depends(get_current_user)):
    format_type = request.get("format", "json")
    folder = request.get("folder", "all")
    
    # Get emails to export
    query = {"user_id": current_user["id"]}
    if folder != "all":
        query["folder"] = folder
    
    emails_cursor = db.emails.find(query)
    emails = await emails_cursor.to_list(length=None)
    
    # Clean up emails
    cleaned_emails = []
    for email in emails:
        email_dict = dict(email)
        if "_id" in email_dict:
            del email_dict["_id"]
        cleaned_emails.append(email_dict)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if format_type == "json":
        # JSON export
        json_data = json.dumps(cleaned_emails, indent=2, ensure_ascii=False, default=str)
        
        def iter_json():
            yield json_data.encode('utf-8')
        
        return StreamingResponse(
            iter_json(),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=postadepo-emails-{folder}-{timestamp}.json"}
        )
    
    elif format_type == "zip":
        # ZIP export with multiple files
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add summary JSON file
            json_data = json.dumps(cleaned_emails, indent=2, ensure_ascii=False, default=str)
            zip_file.writestr(f"emails-summary-{folder}.json", json_data.encode('utf-8'))
            
            # Add individual email files
            for i, email in enumerate(cleaned_emails):
                email_content = f"""From: {email.get('sender', '')}
To: {email.get('recipient', '')}
Subject: {email.get('subject', '')}
Date: {email.get('date', '')}
Size: {email.get('size', 0)} bytes

{email.get('content', '')}
"""
                zip_file.writestr(f"emails/email-{i+1:03d}.eml", email_content.encode('utf-8'))
        
        zip_buffer.seek(0)
        
        def iter_zip():
            yield zip_buffer.read()
        
        return StreamingResponse(
            iter_zip(),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=postadepo-emails-{folder}-{timestamp}.zip"}
        )
    
    elif format_type == "eml":
        # EML export (single file with all emails)
        eml_content = f"""# PostaDepo E-posta Dışa Aktarma
# Klasör: {folder}
# Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Toplam E-posta: {len(cleaned_emails)}

"""
        
        for i, email in enumerate(cleaned_emails):
            eml_content += f"""
================== E-posta #{i+1} ==================
From: {email.get('sender', '')}
To: {email.get('recipient', '')}
Subject: {email.get('subject', '')}
Date: {email.get('date', '')}
Size: {email.get('size', 0)} bytes
Read: {'Okundu' if email.get('read', False) else 'Okunmadı'}
Important: {'Evet' if email.get('important', False) else 'Hayır'}

{email.get('content', '')}

"""
        
        def iter_eml():
            yield eml_content.encode('utf-8')
        
        return StreamingResponse(
            iter_eml(),
            media_type="message/rfc822",
            headers={"Content-Disposition": f"attachment; filename=postadepo-emails-{folder}-{timestamp}.eml"}
        )
    
    raise HTTPException(status_code=400, detail="Desteklenmeyen format")

@api_router.get("/connected-accounts")
async def get_connected_accounts(current_user: dict = Depends(get_current_user)):
    accounts = await db.connected_accounts.find({"user_id": current_user["id"]}).to_list(length=None)
    
    # Clean up accounts
    cleaned_accounts = []
    for account in accounts:
        account_dict = dict(account)
        if "_id" in account_dict:
            del account_dict["_id"]
        cleaned_accounts.append(account_dict)
    
    return {"accounts": cleaned_accounts}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

# Health check
@api_router.get("/")
async def root():
    return {"message": "PostaDepo API is running", "status": "healthy"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc)}