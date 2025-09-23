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
import httpx
import base64


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
    approved: bool = False  # Whitelist durumu - sadece true olanlar giriş yapabilir
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
    account_id: Optional[str] = None  # hangi bağlı hesaptan geldiği/gittiği
    thread_id: Optional[str] = None  # conversation grouping için
    attachments: List[Dict[str, Any]] = Field(default_factory=list)  # ek dosyalar

class EmailResponse(BaseModel):
    emails: List[Dict[str, Any]]
    folderCounts: Dict[str, int]

class StorageInfo(BaseModel):
    totalEmails: int
    totalSize: int

class ConnectedAccount(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    type: str  # sadece outlook
    email: str
    name: Optional[str] = None  # isim soyisim bilgisi
    connected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RecaptchaVerificationRequest(BaseModel):
    recaptcha_token: str

class RecaptchaVerificationResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    
# Demo attachment generator
def generate_demo_attachments():
    """Demo ek dosyalar üret"""
    attachment_templates = [
        {"name": "Proje_Raporu.pdf", "type": "application/pdf", "size": random.randint(500000, 2000000)},
        {"name": "Sunum.pptx", "type": "application/vnd.openxmlformats-officedocument.presentationml.presentation", "size": random.randint(1000000, 5000000)},
        {"name": "Fatura.docx", "type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "size": random.randint(200000, 800000)},
        {"name": "Bütçe.xlsx", "type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "size": random.randint(100000, 500000)},
        {"name": "Ürün_Fotoğrafı.jpg", "type": "image/jpeg", "size": random.randint(300000, 2000000)},
        {"name": "Logo.png", "type": "image/png", "size": random.randint(50000, 500000)},
        {"name": "Sözleşme.pdf", "type": "application/pdf", "size": random.randint(800000, 1500000)},
        {"name": "Katalog.pdf", "type": "application/pdf", "size": random.randint(2000000, 10000000)},
        {"name": "Grafik.png", "type": "image/png", "size": random.randint(100000, 800000)},
        {"name": "Teklif.docx", "type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "size": random.randint(150000, 600000)}
    ]
    
    # 60% şansla ek ekle, eğer ek eklenecekse 1-3 adet
    if random.random() < 0.6:
        num_attachments = random.randint(1, 3)
        attachments = random.sample(attachment_templates, num_attachments)
        
        # Her attachment'a unique ID ve demo content ekle
        for attachment in attachments:
            attachment['id'] = str(uuid.uuid4())
            attachment['content'] = generate_demo_file_content(attachment['type'])
            
        return attachments
    return []

def generate_demo_file_content(file_type: str) -> str:
    """Generate demo content for different file types (base64 encoded)"""
    if 'pdf' in file_type:
        # Simple PDF-like content
        content = """PostaDepo Demo PDF Dosyası
        
Bu bir demo PDF dosyasıdır. Gerçek bir PDF formatında değildir.
İçerik test amaçlıdır.

Bölüm 1: Giriş
Bu bölümde proje hakkında genel bilgiler bulunmaktadır.

Bölüm 2: Detaylar
Detaylı açıklamalar ve teknik bilgiler.

Bölüm 3: Sonuç
Projenin sonuç ve önerileri."""
        
    elif 'image' in file_type:
        # Simple image placeholder
        content = "DEMO IMAGE DATA - Bu gerçek bir resim dosyası değildir, test amaçlıdır."
        
    elif 'word' in file_type or 'document' in file_type:
        content = """PostaDepo Demo Word Belgesi

Bu bir demo Word belgesidir.

1. Başlık
   - Alt başlık 1
   - Alt başlık 2

2. İçerik
   Lorem ipsum dolor sit amet, consectetur adipiscing elit.
   
3. Sonuç
   Demo belge içeriği burada sona ermektedir."""
   
    elif 'excel' in file_type or 'spreadsheet' in file_type:
        content = """PostaDepo Demo Excel Dosyası

A1: Başlık    B1: Değer    C1: Açıklama
A2: Item 1    B2: 100      C2: Demo veri
A3: Item 2    B3: 200      C3: Test veri
A4: TOPLAM    B4: 300      C4: Sonuç"""

    elif 'presentation' in file_type:
        content = """PostaDepo Demo PowerPoint Sunumu

Slayt 1: Başlık Sayfası
- PostaDepo Demo Sunumu
- Sunum Tarihi: 2024

Slayt 2: İçerik
- Ana noktalar
- Detaylı açıklamalar

Slayt 3: Sonuç
- Özet
- Teşekkürler"""
    
    else:
        content = "PostaDepo Demo Dosyası - Bu bir test dosyasıdır."
    
    # Base64 encode the content
    return base64.b64encode(content.encode('utf-8')).decode('utf-8')

# Demo data generation
async def generate_demo_emails(user_id: str) -> List[Dict[str, Any]]:
    # Bağlı hesaplardan gerçek email ve isim bilgilerini al
    connected_accounts = await db.connected_accounts.find({"user_id": user_id}).to_list(length=None)
    
    # Account mapping (hesap ID'si için)
    account_mapping = {}
    if connected_accounts:
        senders = []
        for account in connected_accounts:
            email = account["email"]
            name = account.get("name", email.split("@")[0].replace(".", " ").title())
            sender_format = f"{email} ({name})" if name and name != email.split("@")[0].replace(".", " ").title() else email
            senders.append(sender_format)
            account_mapping[sender_format] = account["id"]
    else:
        # Demo senders (isim formatında)
        demo_senders_with_names = [
            "ali.kaya@outlook.com (Ali Kaya)", "mehmet.demir@outlook.com (Mehmet Demir)", 
            "fatma.yilmaz@hotmail.com (Fatma Yılmaz)", "ahmet.ozkan@outlook.com (Ahmet Özkan)", 
            "ayse.celik@hotmail.com (Ayşe Çelik)", "mustafa.arslan@outlook.com (Mustafa Arslan)",
            "zeynep.koc@outlook.com (Zeynep Koç)", "omer.sahin@hotmail.com (Ömer Şahin)", 
            "elif.yildiz@outlook.com (Elif Yıldız)", "burak.ozer@hotmail.com (Burak Özer)"
        ]
        senders = demo_senders_with_names
        # Demo hesaplar için dummy account ID'ler
        for sender in senders:
            account_mapping[sender] = f"demo-{sender.split('@')[0].split('.')[0]}-account"
    
    subjects = [
        "Önemli Toplantı Davetiyesi", "Proje Güncellemesi", "Hesap Bilgileri",
        "Yeni Ürün Lansmanı", "Fatura Bildirimi", "Tatil Planları",
        "İş Başvurusu", "Konferans Davetiyesi", "Sistem Bakımı Bildirimi",
        "Özel İndirim Fırsatı", "Güvenlik Uyarısı", "Etkinlik Duyurusu"
    ]
    
    folders = ["inbox", "sent", "spam"]
    
    # Thread ID'ler için (conversation grouping)
    thread_subjects = {}
    
    emails = []
    for i in range(50):
        sender = random.choice(senders)
        subject = random.choice(subjects)
        
        # Thread grouping - aynı konularda conversation oluştur
        base_subject = subject
        if base_subject in thread_subjects:
            # Mevcut thread'e ekle
            thread_id = thread_subjects[base_subject]
            if random.random() < 0.3:  # 30% şansla RE: ekle
                subject = f"RE: {subject}"
        else:
            # Yeni thread oluştur
            thread_id = str(uuid.uuid4())
            thread_subjects[base_subject] = thread_id
        
        content = f"Bu bir demo e-posta içeriğidir. {subject} konusunda detaylı bilgi için lütfen eki kontrol ediniz.\n\nSaygılarımla,\n{sender.split('@')[0].replace('.', ' ').title()}"
        
        # Demo attachments ekle
        attachments = generate_demo_attachments()
        
        # Calculate more realistic email size (content + attachments)
        content_size = len(content.encode('utf-8'))
        subject_size = len(subject.encode('utf-8'))
        header_size = len(sender.encode('utf-8')) + 200  # approximate header size
        attachments_size = sum(att["size"] for att in attachments)
        total_size = content_size + subject_size + header_size + attachments_size + random.randint(512, 2048)
        
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
            "size": total_size,
            "account_id": account_mapping.get(sender),
            "thread_id": thread_id,
            "attachments": attachments
        }
        emails.append(email)
    
    return emails

# reCAPTCHA doğrulama fonksiyonu
async def verify_recaptcha_token(token: str) -> dict:
    """
    Google reCAPTCHA token'ını doğrular
    """
    recaptcha_secret = os.environ.get('RECAPTCHA_SECRET_KEY')
    if not recaptcha_secret:
        logging.error("RECAPTCHA_SECRET_KEY environment variable not found")
        return {"success": False, "error": "server_configuration_error"}
    
    verify_url = "https://www.google.com/recaptcha/api/siteverify"
    
    async with httpx.AsyncClient() as client:
        try:
            payload = {
                "secret": recaptcha_secret,
                "response": token
            }
            
            response = await client.post(verify_url, data=payload, timeout=10.0)
            
            if response.status_code == 200:
                result = response.json()
                return result
            else:
                logging.error(f"reCAPTCHA API returned status {response.status_code}")
                return {"success": False, "error": "api_error"}
                
        except httpx.TimeoutException:
            logging.error("reCAPTCHA verification timeout")
            return {"success": False, "error": "timeout"}
        except Exception as e:
            logging.error(f"reCAPTCHA verification error: {str(e)}")
            return {"success": False, "error": "network_error"}

# Routes
@api_router.post("/verify-recaptcha")
async def verify_recaptcha(request: RecaptchaVerificationRequest):
    """
    reCAPTCHA token'ını doğrular
    """
    if not request.recaptcha_token:
        raise HTTPException(status_code=400, detail="reCAPTCHA token gerekli")
    
    verification_result = await verify_recaptcha_token(request.recaptcha_token)
    
    if verification_result.get("success", False):
        return RecaptchaVerificationResponse(
            success=True,
            message="reCAPTCHA doğrulaması başarılı"
        )
    else:
        return RecaptchaVerificationResponse(
            success=False,
            message="reCAPTCHA doğrulaması başarısız"
        )

@api_router.post("/auth/register")
async def register(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Bu e-posta adresi zaten kayıtlı")
    
    # Create new user with approved=False (whitelist sistemi)
    hashed_password = hash_password(user_data.password)
    new_user = User(name=user_data.name, email=user_data.email, approved=False)
    
    # Save user to database
    user_dict = new_user.dict()
    user_dict["password"] = hashed_password
    await db.users.insert_one(user_dict)
    
    return {
        "message": "Kullanıcı kaydı oluşturuldu. Admin onayı bekleniyor.", 
        "user_id": new_user.id,
        "approved": False
    }

@api_router.post("/auth/login")
async def login(user_data: UserLogin):
    # Demo user check
    if user_data.email == "demo@postadepo.com" and user_data.password == "demo123":
        # Check if demo user exists
        existing_user = await db.users.find_one({"email": user_data.email})
        
        if not existing_user:
            # Create demo user (approved by default)
            demo_user = User(name="Demo Kullanıcı", email=user_data.email, approved=True)
            user_dict = demo_user.dict()
            user_dict["password"] = hash_password(user_data.password)
            await db.users.insert_one(user_dict)
            
            # Generate demo emails
            demo_emails = await generate_demo_emails(demo_user.id)
            if demo_emails:
                await db.emails.insert_many(demo_emails)
            
            user = demo_user
        else:
            # Handle existing user without name field
            if 'name' not in existing_user:
                existing_user['name'] = 'Demo Kullanıcı'
                # Update the user in database with approved status
                await db.users.update_one(
                    {"email": user_data.email},
                    {"$set": {"name": "Demo Kullanıcı", "approved": True}}
                )
                existing_user['approved'] = True
            # Ensure demo user is always approved
            if 'approved' not in existing_user:
                await db.users.update_one(
                    {"email": user_data.email},
                    {"$set": {"approved": True}}
                )
                existing_user['approved'] = True
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
    
    # Whitelist kontrolü - sadece onaylanmış kullanıcılar giriş yapabilir
    if not user.get("approved", False):
        raise HTTPException(
            status_code=403, 
            detail="Hesabınız henüz onaylanmamış. Admin onayı bekleniyor."
        )
    
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
    
    # Bağlı hesap bilgilerini al
    connected_accounts = await db.connected_accounts.find({"user_id": current_user["id"]}).to_list(length=None)
    accounts_dict = {acc["id"]: acc for acc in connected_accounts}
    
    # Clean up emails for response ve hesap bilgilerini ekle
    cleaned_emails = []
    for email in emails:
        email_dict = dict(email)
        if "_id" in email_dict:
            del email_dict["_id"]
        
        # Hesap bilgilerini ekle
        if "account_id" in email_dict and email_dict["account_id"] in accounts_dict:
            account = accounts_dict[email_dict["account_id"]]
            email_dict["account_info"] = {
                "id": account["id"],
                "name": account.get("name", ""),
                "email": account["email"],
                "type": account["type"]
            }
        
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

@api_router.get("/emails/thread/{thread_id}")
async def get_email_thread(thread_id: str, current_user: dict = Depends(get_current_user)):
    """E-posta thread'ini (conversation) getir"""
    # Thread'deki tüm e-postaları getir
    emails_cursor = db.emails.find({
        "user_id": current_user["id"],
        "thread_id": thread_id
    }).sort("date", 1)  # Tarih sırasına göre (eskiden yeniye)
    
    emails = await emails_cursor.to_list(length=None)
    
    if not emails:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # Bağlı hesap bilgilerini al
    connected_accounts = await db.connected_accounts.find({"user_id": current_user["id"]}).to_list(length=None)
    accounts_dict = {acc["id"]: acc for acc in connected_accounts}
    
    # Clean up emails ve hesap bilgilerini ekle
    cleaned_emails = []
    for email in emails:
        email_dict = dict(email)
        if "_id" in email_dict:
            del email_dict["_id"]
        
        # Hesap bilgilerini ekle
        if "account_id" in email_dict and email_dict["account_id"] in accounts_dict:
            account = accounts_dict[email_dict["account_id"]]
            email_dict["account_info"] = {
                "id": account["id"],
                "name": account.get("name", ""),
                "email": account["email"],
                "type": account["type"]
            }
        
        cleaned_emails.append(email_dict)
    
    return {"thread_id": thread_id, "emails": cleaned_emails}

@api_router.post("/admin/approve-user/{user_id}")
async def approve_user(user_id: str, current_user: dict = Depends(get_current_user)):
    """
    Admin endpoint - Kullanıcıyı onaylar (whitelist'e ekler)
    Not: Bu endpoint gerçek uygulamada admin authentication gerektirecek
    """
    # Demo amaçlı basit kontrol - gerçek uygulamada admin rolü kontrolü yapılmalı
    if current_user["email"] != "demo@postadepo.com":
        raise HTTPException(status_code=403, detail="Bu işlem için admin yetkisi gerekli")
    
    # Kullanıcıyı bul ve onayla
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"approved": True}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    
    return {"message": "Kullanıcı başarıyla onaylandı", "user_id": user_id}

@api_router.get("/admin/pending-users")
async def get_pending_users(current_user: dict = Depends(get_current_user)):
    """
    Admin endpoint - Onay bekleyen kullanıcıları listeler
    """
    if current_user["email"] != "demo@postadepo.com":
        raise HTTPException(status_code=403, detail="Bu işlem için admin yetkisi gerekli")
    
    # Onay bekleyen kullanıcıları getir
    users_cursor = db.users.find({"approved": False})
    users = await users_cursor.to_list(length=None)
    
    # Şifreleri çıkar ve temizle
    cleaned_users = []
    for user in users:
        user_dict = dict(user)
        if "_id" in user_dict:
            del user_dict["_id"]
        if "password" in user_dict:
            del user_dict["password"]
        cleaned_users.append(user_dict)
    
    return {"pending_users": cleaned_users}

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
    # Simulate email sync by adding a few new demo emails from connected accounts
    
    # Bağlı hesaplardan sender bilgilerini al
    connected_accounts = await db.connected_accounts.find({"user_id": current_user["id"]}).to_list(length=None)
    
    # Account mapping
    account_mapping = {}
    if not connected_accounts:
        # Eğer bağlı hesap yoksa, demo sender'lar kullan
        senders = ["demo.sync@outlook.com (Demo Sync)", "system@outlook.com (Sistem)", "info@outlook.com (Bilgi)"]
        for sender in senders:
            account_mapping[sender] = f"demo-{sender.split('@')[0]}-account"
    else:
        senders = []
        for account in connected_accounts:
            email = account["email"]
            name = account.get("name", email.split("@")[0].replace(".", " ").title())
            sender_format = f"{email} ({name})" if name and name != email.split("@")[0].replace(".", " ").title() else email
            senders.append(sender_format)
            account_mapping[sender_format] = account["id"]
    
    new_emails = []
    for i in range(3):
        sender = random.choice(senders)
        
        # Demo attachments ekle
        attachments = generate_demo_attachments()
        attachments_size = sum(att["size"] for att in attachments)
        total_size = random.randint(1024, 5120) + attachments_size
        
        email = {
            "id": str(uuid.uuid4()),
            "user_id": current_user["id"],
            "folder": "inbox",
            "sender": sender,
            "recipient": current_user["email"],
            "subject": f"Senkronizasyon Sonucu Yeni E-posta {i+1}",
            "content": f"Bu e-posta senkronizasyon işlemi sonucu eklenen demo e-postadır. Gönderen: {sender}, Timestamp: {datetime.now(timezone.utc)}",
            "preview": "Bu e-posta senkronizasyon işlemi sonucu eklenen demo e-postadır...",
            "date": datetime.now(timezone.utc).isoformat(),
            "read": False,
            "important": False,
            "size": total_size,
            "account_id": account_mapping.get(sender),
            "thread_id": str(uuid.uuid4()),
            "attachments": attachments
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
    
    # Bağlı hesaplardan sender bilgilerini al
    connected_accounts = await db.connected_accounts.find({"user_id": current_user["id"]}).to_list(length=None)
    
    if not connected_accounts:
        # Eğer bağlı hesap yoksa, demo sender'lar kullan
        senders = ["imported@outlook.com (İçe Aktarılan)", "archive@outlook.com (Arşiv)", "backup@outlook.com (Yedek)"]
    else:
        senders = []
        for account in connected_accounts:
            email = account["email"]
            name = account.get("name", email.split("@")[0].replace(".", " ").title())
            sender_format = f"{email} ({name})" if name and name != email.split("@")[0].replace(".", " ").title() else email
            senders.append(sender_format)
    
    imported_emails = []
    for i in range(email_count):
        sender = random.choice(senders)
        email_size = random.randint(1024, 8192)  # 1-8KB per email
        email = {
            "id": str(uuid.uuid4()),
            "user_id": current_user["id"],
            "folder": "inbox",
            "sender": sender,
            "recipient": current_user["email"],
            "subject": f"İçe Aktarılan E-posta {i+1} - {file.filename}",
            "content": f"Bu e-posta {file.filename} dosyasından içe aktarılmıştır. Gönderen: {sender}, Orijinal boyut: {file_size} bytes\n\nİçerik özeti: Dosyadan başarıyla içe aktarılan e-posta verisi.",
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

@api_router.post("/update-demo-emails")
async def update_demo_emails(current_user: dict = Depends(get_current_user)):
    """
    Mevcut demo emaillerini bağlı hesap bilgileriyle günceller
    """
    # Bağlı hesaplardan sender bilgilerini al
    connected_accounts = await db.connected_accounts.find({"user_id": current_user["id"]}).to_list(length=None)
    
    if not connected_accounts:
        return {"success": False, "message": "Bağlı hesap bulunamadı"}
    
    # Mevcut demo emailleri bul
    demo_emails = await db.emails.find({"user_id": current_user["id"]}).to_list(length=None)
    
    if not demo_emails:
        return {"success": False, "message": "Güncellenecek email bulunamadı"}
    
    # Sender mapppingi oluştur
    sender_mapping = {}
    for account in connected_accounts:
        email = account["email"]
        name = account.get("name", email.split("@")[0].replace(".", " ").title())
        sender_format = f"{email} ({name})" if name and name != email.split("@")[0].replace(".", " ").title() else email
        sender_mapping[email] = sender_format
    
    # Demo emailleri güncelle
    updated_count = 0
    for demo_email in demo_emails:
        old_sender = demo_email["sender"]
        
        # Eski formatı kontrol et (sadece email varsa)
        if "@" in old_sender and "(" not in old_sender:
            # Bağlı hesaplarda bu email var mı kontrol et
            for account_email, formatted_sender in sender_mapping.items():
                if account_email in old_sender:
                    # Email'i güncelle
                    await db.emails.update_one(
                        {"id": demo_email["id"]},
                        {"$set": {"sender": formatted_sender}}
                    )
                    updated_count += 1
                    break
    
    return {"success": True, "updated_count": updated_count, "message": f"{updated_count} email güncellendi"}

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

@api_router.post("/connect-account")
async def connect_account(account_data: dict, current_user: dict = Depends(get_current_user)):
    """Outlook hesabı bağlama endpoint'i - sınırsız hesap desteği"""
    account_type = account_data.get("type", "").lower()
    email = account_data.get("email", "")
    name = account_data.get("name", "")
    
    # Sadece Outlook desteği
    if account_type != "outlook":
        raise HTTPException(status_code=400, detail="Sadece Outlook hesapları desteklenmektedir")
    
    # Email adresi gerekli
    if not email:
        raise HTTPException(status_code=400, detail="Email adresi gereklidir")
    
    # Aynı email adresinin zaten bağlı olup olmadığını kontrol et
    existing_account = await db.connected_accounts.find_one({
        "user_id": current_user["id"],
        "email": email
    })
    
    if existing_account:
        raise HTTPException(status_code=400, detail="Bu email adresi zaten bağlı")
    
    # Yeni Outlook hesabı oluştur
    new_account = ConnectedAccount(
        user_id=current_user["id"],
        type="Outlook",
        email=email,
        name=name if name else email.split("@")[0].replace(".", " ").title()
    )
    
    account_dict = new_account.dict()
    await db.connected_accounts.insert_one(account_dict)
    
    # Clean up the account dict for response
    if "_id" in account_dict:
        del account_dict["_id"]
    
    return {"success": True, "account": account_dict}

@api_router.get("/attachments/download/{attachment_id}")
async def download_attachment(attachment_id: str, current_user: dict = Depends(get_current_user)):
    """Download attachment by ID"""
    try:
        # Find the email that contains this attachment
        email = await db.emails.find_one({
            "user_id": current_user["id"],
            "attachments": {"$elemMatch": {"id": attachment_id}}
        })
        
        if not email:
            raise HTTPException(status_code=404, detail="Attachment not found")
        
        # Find the specific attachment
        attachment = None
        for att in email.get("attachments", []):
            if att.get("id") == attachment_id:
                attachment = att
                break
        
        if not attachment:
            raise HTTPException(status_code=404, detail="Attachment not found")
        
        # Get the attachment content (base64 decoded)
        content = base64.b64decode(attachment.get("content", ""))
        
        # Create streaming response
        def iter_content():
            yield content
        
        # Determine media type based on file extension
        media_type = attachment.get("type", "application/octet-stream")
        
        # Handle Unicode characters in filename for HTTP headers
        try:
            # Try to encode filename as ASCII for HTTP header
            safe_filename = attachment['name'].encode('ascii').decode('ascii')
        except UnicodeEncodeError:
            # If filename contains non-ASCII characters, use RFC 5987 encoding
            import urllib.parse
            encoded_filename = urllib.parse.quote(attachment['name'].encode('utf-8'))
            safe_filename = f"filename*=UTF-8''{encoded_filename}"
        else:
            safe_filename = f"filename={safe_filename}"
        
        return StreamingResponse(
            iter_content(),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; {safe_filename}",
                "Content-Length": str(len(content))
            }
        )
        
    except Exception as e:
        logger.error(f"Error downloading attachment: {str(e)}")
        raise HTTPException(status_code=500, detail="Error downloading attachment")

@api_router.delete("/connected-accounts/{account_id}")
async def disconnect_account(account_id: str, current_user: dict = Depends(get_current_user)):
    """Remove connected account"""
    result = await db.connected_accounts.delete_one({
        "id": account_id,
        "user_id": current_user["id"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Account not found")
    
    return {"success": True, "message": "Account disconnected"}

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