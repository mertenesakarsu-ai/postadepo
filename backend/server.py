from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse, HTMLResponse
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
import asyncio

# Microsoft Graph SDK imports
try:
    from kiota_abstractions.base_request_builder import BaseRequestBuilder
    from azure.identity.aio import ClientSecretCredential
    from azure.identity import ClientSecretCredential as SyncClientSecretCredential
    from msgraph import GraphServiceClient
    from msgraph.generated.models.message import Message
    from msgraph.generated.models.folder import Folder
    from msgraph.generated.users.item.mail_folders.item.messages.messages_request_builder import MessagesRequestBuilder
    GRAPH_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Microsoft Graph SDK not available: {e}")
    GRAPH_AVAILABLE = False
    # Define dummy classes to prevent NameError
    GraphServiceClient = None
    ClientSecretCredential = None
    Message = None
    Folder = None
    MessagesRequestBuilder = None


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Log helper function
async def add_system_log(log_type: str, message: str, user_email: str = None, user_name: str = None, additional_data: dict = None):
    """Sistem loglarına yeni bir kayıt ekler"""
    try:
        log_entry = SystemLog(
            log_type=log_type,
            message=message,
            user_email=user_email,
            user_name=user_name,
            additional_data=additional_data
        )
        await db.system_logs.insert_one(log_entry.dict())
        print(f"System log added: {log_type} - {message}")
    except Exception as e:
        print(f"Failed to add system log: {e}")

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
    user_type: str = "email"  # "email" for regular signup, "outlook" for OAuth users

class OutlookUser(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    display_name: str
    microsoft_user_id: str
    tenant_id: str
    approved: bool = True  # Outlook users auto-approved
    user_type: str = "outlook"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None
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

class BulkUserRequest(BaseModel):
    user_ids: List[str]

class AccountConnection(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    email: str
    display_name: Optional[str] = None
    account_type: str = "outlook"  # outlook, gmail vb.
    is_connected: bool = True
    connected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_sync: Optional[datetime] = None
    sync_token: Optional[str] = None

class OutlookEmail(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message_id: str  # Outlook'tan gelen unique ID
    user_id: str
    account_id: str  # hangi hesaptan geldiği
    folder: str  # inbox, sent, vb.
    sender: str
    recipient: str
    subject: str
    content: str
    preview: str
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    read: bool = False
    important: bool = False
    size: int = 1024
    thread_id: Optional[str] = None
    attachments: List[Dict[str, Any]] = Field(default_factory=list)
    source: str = "outlook"  # outlook, demo vb.

class SyncRequest(BaseModel):
    account_email: str
    folder_name: Optional[str] = "Inbox"
    sync_count: int = Field(default=50, ge=1, le=200)

class SyncResponse(BaseModel):
    account_email: str
    synced_count: int
    skipped_count: int
    error_count: int

class SystemLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    log_type: str  # USER_REGISTER, USER_LOGIN, EMAIL_SYNC, USER_APPROVED, etc.
    message: str
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None
    sync_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    next_sync_token: Optional[str] = None
    
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
        
        # Daha gerçekçi ve çok uzun e-posta içerikleri
        content_templates = [
            f"""Merhaba,

{subject} ile ilgili detayları sizinle paylaşmak istiyorum. Bu konuda yapılan son çalışmalar oldukça önemli gelişmeler içeriyor ve dikkatinizi çekmesi gereken birkaç nokta bulunuyor.

Yapılan analiz sonucunda aşağıdaki hususlar öne çıkmaktadır:

• Mevcut durum değerlendirmesi tamamlanmış ve sonuçlar olumlu
• Planlanan adımlar için gerekli kaynaklar belirlendi
• Timeline ve mile stone'lar netleştirildi
• Risk analizi yapıldı ve önlemler alındı

**DETAYLI AÇIKLAMA:**

Bu proje kapsamında gerçekleştirdiğimiz çalışmalar, şirketimizin stratejik hedefleriyle tam uyum içerisinde yürütülmüştür. Başlangıçta belirlediğimiz kritik başarı faktörleri üzerinden yapılan değerlendirmede, beklentilerin üzerinde bir performans sergilediğimizi görmekteyiz.

**Proje Kapsamındaki Ana Faaliyet Alanları:**

1. **Araştırma ve Geliştirme Çalışmaları**
   - Pazar analizi ve rekabet durumu değerlendirmesi
   - Teknolojik trendlerin incelenmesi ve gelecek projeksiyon analizi
   - Müşteri ihtiyaç analizlerinin derinlemesine yapılması
   - İnovasyon fırsatlarının tespit edilmesi ve değerlendirilmesi

2. **Operasyonel İyileştirmeler**
   - Mevcut süreçlerin etkinlik analizinin yapılması
   - Verimliliği artıracak yeni metodolojilerin geliştirilmesi
   - Teknolojik entegrasyonların planlanması ve uygulanması
   - Kalite kontrol mekanizmalarının güçlendirilmesi

3. **İnsan Kaynakları ve Organizasyonel Gelişim**
   - Ekip performansının artırılmasına yönelik eğitim programları
   - Liderlik becerilerinin geliştirilmesi için özel workshops
   - Çalışan memnuniyeti ve bağlılığını artırıcı aktiviteler
   - Kariyer planlama ve gelişim yollarının netleştirilmesi

**RİSK YÖNETİMİ VE ÖNLEYİCİ TEDBİRLER:**

Projemizin başarısını etkileyebilecek potansiyel riskleri önceden belirleyerek, her biri için ayrıntılı aksiyon planları hazırladık. Bu planlar dahilinde:

- Teknik risklere karşı alternatif çözüm yolları geliştirildi
- Mali risklerin minimize edilmesi için buffer bütçeler ayrıldı
- İnsan kaynağı risklerine karşı yedek planlar oluşturuldu
- Dış faktörlerin etkilerini azaltacak stratejiler belirlendi

**SONUÇLAR VE DEĞERLENDİRME:**

Şu ana kadar elde ettiğimiz sonuçlar oldukça cesaret verici. Belirlediğimiz KPI'lar üzerinden yapılan ölçümlerde:
- Müşteri memnuniyeti %23 artış gösterdi
- Operasyonel verimlilik %18 iyileştirme kaydetti
- Çalışan performans skorları %15 yükseldi
- Proje tamamlanma oranları %31 hızlandı

Detaylı bilgiler için ekte bulunan dokümanları incelemenizi rica ederim. Herhangi bir sorunuz olursa lütfen benimle iletişime geçmekten çekinmeyin.

En kısa zamanda geri dönüşünüzü bekliyorum.

Saygılarımla,
{sender.split('@')[0].replace('.', ' ').title()}
{sender.split('@')[1]} | Proje Koordinatörü""",

            f"""Değerli İş Ortakları,

{subject} kapsamında sizlere bilgi vermek istiyorum. Bugünkü toplantıda alınan kararlar doğrultusunda, önümüzdeki dönemde hayata geçireceğimiz stratejiler hakkında detayları aşağıda bulabilirsiniz.

## GENEL DEĞERLENDIRME VE STRATEJİK YÖNELİM

Son dönemde piyasada yaşanan gelişmeler ve değişen müşteri beklentileri, bizleri yeni stratejileri geliştirmeye yönlendirdi. Bu stratejiler, hem mevcut konumumuzu güçlendirecek hem de gelecekteki büyüme fırsatlarını değerlendirmemize olanak sağlayacak nitelikte hazırlandı.

## Ana Hedefler ve Uygulama Planları:

### 1. Operasyonel Verimliliğin Artırılması
Bu hedef kapsamında yapılacak çalışmalar:
- Mevcut iş süreçlerinin detaylı analizi ve optimizasyonu
- Dijital dönüşüm projelerinin hızlandırılması
- Otomasyona geçilebilecek süreçlerin belirlenmesi ve uygulanması
- Kalite yönetim sistemlerinin güncelleştirilmesi
- Performans izleme ve raporlama mekanizmalarının güçlendirilmesi

**Beklenen Faydalar:**
- %20-25 oranında verimlilik artışı
- Hata oranlarında %40 azalma
- Müşteri şikayetlerinde %35 düşüş
- İşlem sürelerinde %30 kısalma

### 2. Müşteri Memnuniyetinin Yükseltilmesi
Bu alanda odaklanacağımız konular:
- Müşteri deneyimi yolculuğunun yeniden tasarlanması
- 360 derece müşteri geri bildirim sisteminin kurulması
- Proaktif müşteri hizmetleri yaklaşımının benimsenmesi
- Kişiselleştirilmiş hizmet sunumu için veri analitiği kullanımı
- Omnichannel iletişim stratejisinin geliştirilmesi

**Hedeflenen Metrikler:**
- NPS skorunda minimum 15 puan artış
- Müşteri sadakat oranında %25 iyileşme
- İlk çözüm oranında %45 artış
- Müşteri yaşam boyu değerinde %20 yükselme

### 3. Teknolojik Altyapının Güçlendirilmesi
Teknoloji yatırımlarımız şu alanlarda yoğunlaşacak:
- Cloud-first yaklaşımıyla sistemlerin modernizasyonu
- Yapay zeka ve makine öğrenmesi entegrasyonları
- Siber güvenlik kapasitesinin artırılması
- Veri yönetimi ve analitiği altyapısının güçlendirilmesi
- API-first mimari ile sistem entegrasyonlarının iyileştirilmesi

**Teknik Özellikler:**
- %99.9 uptime garantisi ile sistem kararlılığı
- Real-time veri işleme kapasitesi
- Scalable architecture ile büyüme esnekliği
- Advanced analytics ile predictive insights

### 4. İnsan Kaynakları Geliştirme Programları
Çalışanlarımızın gelişimi için kapsamlı programlar:
- Liderlik Akademisi kurulumu ve işletmeye alınması
- Teknik beceri geliştirme bootcamp'leri
- Mentörlük ve koçluk programlarının yaygınlaştırılması
- Kariyer planlama ve başarım yönetimi sistemlerinin revize edilmesi
- Çalışan katılımı ve inovasyonu destekleyici platformların oluşturulması

**İNNOVASYON VE GELECEK PLANLAMASI:**

Planladığımız bu değişikliklerin hem kısa vadeli hem de uzun vadeli etkilerini değerlendirdik. İlk aşamada pilot uygulama ile başlayarak, başarılı olan alanları genişletmeyi planlıyoruz.

**Kısa Vadeli Hedefler (0-6 ay):**
- Pilot projelerin başlatılması ve ilk sonuçların alınması
- Kritik sistemlerin güncelleştirilmesi
- Çalışan eğitim programlarının başlatılması
- Temel performans metriklerinin iyileştirilmesi

**Orta Vadeli Hedefler (6-18 ay):**
- Pilot projelerin başarılı sonuçlarının yaygınlaştırılması
- Teknoloji altyapısının tam entegrasyonu
- Müşteri memnuniyet skorlarında hedeflenen artışın sağlanması
- Operasyonel verimlilik hedeflerinin %80'inin gerçekleştirilmesi

**Uzun Vadeli Hedefler (18+ ay):**
- Sektörde liderlik konumunun pekiştirilmesi
- Yeni pazar segmentlerine girişin gerçekleştirilmesi
- Sürdürülebilirlik hedeflerinin tamamen karşılanması
- İnovasyon kültürünün organizasyon genelinde yerleşmesi

Bu süreçte sizlerin görüş ve önerileriniz bizim için çok değerli. Ekte bulacağınız sunum dosyası ile daha detaylı bilgilere ulaşabilirsiniz.

Görüşlerinizi bekliyorum.

İyi çalışmalar,
{sender.split('@')[0].replace('.', ' ').title()}""",

            f"""Saygıdeğer Ekip Arkadaşları,

Size {subject} hakkında güncel bilgileri iletmek istiyorum. Son dönemde yaşanan gelişmeler ışığında bazı önemli kararlar alındı ve bunları sizlerle paylaşmam gerekiyor.

## PROJENİN GÜNCEL DURUMU VE BAŞARILARIMIZ

**Mevcut Durum Analizi:**
Projemizin şu anki durumu oldukça olumlu ve beklentilerin çok üzerinde bir performans sergiliyor. Belirlenen milestone'ların %87'si başarıyla tamamlandı ve hedeflenen tarihlerin oldukça önündeyiz. Bu başarıda tüm ekibin gösterdiği performans, özverili çalışma ve yaratıcı problem çözme yaklaşımları çok önemli rol oynadı.

**Detaylı Başarı Metrikleri:**
- Ana deliverable'ların %87'si tamamlandı (hedef %75'ti)
- Kalite skorları %94 seviyesinde (hedef %90'dı)
- Müşteri memnuniyet oranı %96 (beklenti %85'ti)
- Bütçe kullanımı planın %73'ü seviyesinde
- Zaman planlaması %12 daha hızlı gerçekleşiyor

## KAPSAMLI SÜREÇ DEĞERLENDİRMESİ

### Başarılı Olan Alanlar:
1. **Teknik İmplementasyon**
   - Sistem mimarisi beklenenden daha stabil çalışıyor
   - Performance metrikleri hedefleri aşıyor
   - Integration süreçleri sorunsuz tamamlandı
   - Security audit'ler başarıyla geçildi

2. **Ekip Koordinasyonu**
   - Cross-functional teamwork mükemmel seviyede
   - Communication efficiency %40 arttı
   - Problem-solving speed dramatik şekilde iyileşti
   - Knowledge sharing kültürü güçlü bir şekilde yerleşti

3. **Stakeholder Management**
   - Client satisfaction exceptional levels'da
   - Regular feedback loops etkili çalışıyor
   - Change request management smooth bir şekilde işliyor
   - Transparency ve trust tamamen establish edildi

### İyileştirme Alanları:
1. **Resource Optimization**
   - Bazı alanlarda kapasite fazlası tespit edildi
   - Resource reallocation opportunities belirlendi
   - Efficiency gains için ek opportunities var

2. **Process Enhancement**
   - Workflow optimization potansiyeli mevcut
   - Automation opportunities identified
   - Best practices documentation needs improvement

## FORWARD-LOOKING PLAN VE STRATEJİ

**Sonraki Adımlar ve Timeline:**

### Hafta 1-2: Kalite Güvence ve Test Süreçleri
- Comprehensive system testing
- User acceptance testing preparation
- Performance benchmarking
- Security penetration testing
- Documentation finalization

**Detaylı Test Stratejisi:**
- Unit testing coverage %95+ target
- Integration testing tüm system components
- End-to-end testing real-world scenarios
- Load testing peak capacity scenarios
- Disaster recovery testing backup systems

### Hafta 3-4: Kullanıcı Kabul Testleri ve Eğitim
- Pilot user group selection ve training
- Feedback collection mechanisms setup
- Issue tracking ve resolution processes
- User experience optimization
- Training materials ve documentation

**Eğitim Programı Detayları:**
- Technical training for power users
- Basic usage training for end users
- Administrator training for IT team
- Troubleshooting guide creation
- Video tutorials ve interactive guides

### Hafta 5-6: Sistem Entegrasyonu ve Final Preparations
- Production environment setup
- Data migration planning ve execution
- System integration testing
- Performance monitoring setup
- Rollback plan preparation

**Critical Success Factors:**
- Zero-downtime deployment strategy
- Real-time monitoring implementation
- Automated backup systems
- 24/7 support readiness
- Emergency response procedures

### Hafta 7-8: Canlı Ortama Geçiş ve Stabilizasyon
- Phased rollout implementation
- Continuous monitoring ve support
- Issue resolution ve optimization
- Performance tuning
- Success metrics tracking

## RİSK YÖNETİMİ VE ACİL DURUM PLANLARI

**Dikkat Edilmesi Gereken Kritik Konular:**
Canlı ortama geçiş sırasında olası aksaklıkları minimize etmek için comprehensive backup planlarımızı hazırladık. Ayrıca 7/24 destek ekibi de hazır durumda bekliyor ve acil müdahale protokolleri tamamen implement edildi.

**Risk Mitigation Strategies:**
1. **Technical Risks**
   - Multiple backup systems
   - Rollback procedures ready
   - Alternative solution paths prepared
   - Expert technical team on standby

2. **Operational Risks**
   - Change management procedures
   - Communication protocols established
   - Training programs completed
   - Support documentation ready

3. **Business Continuity Risks**
   - Business impact assessments completed
   - Contingency plans activated
   - Stakeholder communication plans ready
   - Success metrics monitoring systems

## İNOVASYON VE GELECEK FIRSATLARI

Bu projenin başarısı bize gelecek için önemli insights sağladı:

**Lessons Learned:**
- Agile methodology benefits realized
- Team collaboration tools effectiveness proven
- Customer-centric approach validation
- Technology stack optimization opportunities

**Future Enhancement Opportunities:**
- AI/ML integration possibilities
- Advanced analytics implementation
- Mobile-first approach expansion
- Cloud-native architecture evolution

Ek dosyalarda daha teknik detayları bulabilirsiniz. Herhangi bir soru veya öneriniz varsa lütfen çekinmeyin.

Başarılar dilerim ve tüm ekibe teşekkürlerimi sunarım.

En iyi dileklerle,
{sender.split('@')[0].replace('.', ' ').title()}
Teknik Proje Lideri""",

            f"""Sayın Yönetim Kurulu Üyeleri ve Değerli Paydaşlar,

{subject} konusunda sizlerle kapsamlı bir değerlendirme paylaşmak istiyorum. Bu rapor, çeyrek dönem sonuçlarımızı, mevcut pazar durumumuzu ve gelecek stratejilerimizi detaylı bir şekilde ele almaktadır.

## YÖNETİCİ ÖZETİ (EXECUTIVE SUMMARY)

Bu dönem itibariyle şirketimiz, belirlenen tüm stratejik hedeflerde önemli ilerlemeler kaydetmiştir. Finansal performansımız, operasyonel verimliliğimiz ve pazar konumumuz güçlü bir trajectory sergilerken, gelecek dönem için de umut verici projeksiyonlar ortaya çıkmıştır.

**Ana Performans Göstergeleri:**
- Toplam gelir: %23 artış (YoY)
- EBITDA marjı: %18.5 (hedef %17'ydi)
- Müşteri memnuniyet oranı: %94 (sektör ortalaması %78)
- Çalışan memnuniyet endeksi: %89 (geçen yıl %82'ydi)
- Pazar payı: %12.3 (6 ay önce %11.1'di)

## DETAYLI FİNANSAL ANALİZ VE PERFORMANS

### Gelir Analizi ve Segment Performansı

**Segment Bazında Gelir Dağılımı:**
1. Ana Ürün Grubu A: ₺45.2M (toplam gelirin %38'i)
   - Geçen yıla göre %28 artış
   - Brüt kar marjı %35.2
   - Müşteri bazında %15 büyüme

2. Ana Ürün Grubu B: ₺32.8M (toplam gelirin %28'i)
   - YoY %19 artış
   - Brüt kar marjı %42.1
   - Yeni müşteri kazanımı %22

3. Hizmet Segmenti: ₺28.4M (toplam gelirin %24'ü)
   - %31 büyüme oranı
   - Recurring revenue %67
   - Customer lifetime value %25 artış

4. Diğer Gelirler: ₺11.8M (toplam gelirin %10'u)
   - Lisanslama gelirleri %45 artış
   - Partnership income %18 büyüme

### Maliyet Yapısı ve Verimlilik Analizi

**Operasyonel Maliyet Optimizasyonu:**
- Toplam operasyonel maliyetler %8 azaldı
- Birim başına üretim maliyeti %12 düştü
- Lojistik verimliliği %15 arttı
- Enerji tüketimi %20 azaldı (sürdürülebilirlik hedefleriyle uyumlu)

**İnsan Kaynakları Yatırımları:**
- Çalışan başına ortalama eğitim saati: 47 saat
- İç terfi oranı: %73 (dış alım yerine)
- Personel devir hızı: %8.2 (sektör ortalaması %14.5)
- Performans bonus ödemeleri %18 arttı

## PAZAR ANALİZİ VE REKABETÇİ POZISYON

### Makro Ekonomik Faktörler ve Etkileri

Küresel ekonomideki dalgalanmalara rağmen, şirketimiz resilient bir performans sergilemeye devam ediyor. Özellikle aşağıdaki faktörler pozitif etkiler yaratmıştır:

**Olumlu Faktörler:**
- Dijital dönüşüm trendinin hızlanması
- ESG kriterlerinin önem kazanması
- Teknoloji yatırımlarının artması
- Remote work model'inin yaygınlaşması

**Zorluk Teşkil Eden Faktörler:**
- Supply chain disruption'lar
- Enflasyon baskısı input costs'larda
- Skilled talent shortage certain areas'larda
- Regulatory changes adaptation requirements

### Rekabetçi Analiz ve Pazar Konumumuz

**Güçlü Olduğumuz Alanlar:**
1. **Teknolojik İnovasyon Kapasitesi**
   - R&D yatırımları sektör ortalamasının %40 üzerinde
   - Patent portföyü 156 adet (yılbaşından bu yana +23)
   - Innovation pipeline 24 aylık roadmap'e sahip

2. **Müşteri Deneyimi ve Hizmet Kalitesi**
   - Net Promoter Score 87 (industry benchmark 62)
   - Customer retention rate %94
   - First call resolution %78

3. **Operasyonel Mükemmellik**
   - Six Sigma sertifikalı %45 of processes
   - ISO standartlarında %99.2 compliance
   - Digital maturity index top quartile'da

## STRATEJİK İNİSİYATİFLER VE GELECEK PLANLARI

### Kısa Vadeli Hedefler (Q4 2024 - Q2 2025)

**Büyüme İnisiyatifleri:**
1. **Yeni Pazar Segmentlerine Giriş**
   - Healthcare vertical'ına pilot proje
   - Education sector'da strategic partnerships
   - International expansion Phase 1 (3 ülke)

2. **Ürün Portföy Genişletmesi**
   - AI-powered features integration
   - Mobile-first platform development
   - Subscription model optimization

3. **Operational Excellence Programları**
   - Automation initiatives 15 process'te
   - Lean Six Sigma rollout organization-wide
   - Sustainability metrics tracking system

### Orta-Uzun Vadeli Stratejik Vizyonumuz

**2025-2027 Dönemi Ana Odak Alanları:**

1. **Digital Leadership Position**
   - Industry 4.0 technologies adoption
   - AI ve ML capabilities şirket genelinde
   - Data-driven decision making culture

2. **Sustainable Growth Model**
   - Carbon neutrality by 2027 target
   - Circular economy principles implementation
   - ESG scoring top 10% target in sector

3. **Market Expansion Strategy**
   - Geographic expansion 12 new markets
   - Adjacent market opportunities exploration
   - Strategic acquisitions consideration

## RİSK YÖNETİMİ VE MİTİGASYON STRATEJİLERİ

**Identified Risk Categories ve Mitigation Plans:**

### 1. Market Risks
**Risk Faktörleri:**
- Economic recession impact on demand
- Competitive pressure from new entrants
- Customer behavior shifts post-pandemic

**Mitigation Strategies:**
- Portfolio diversification across sectors
- Customer retention program enhancement
- Agile business model adaptation capability

### 2. Operational Risks  
**Risk Faktörleri:**
- Supply chain vulnerabilities
- Cybersecurity threats increase
- Key personnel dependency

**Mitigation Actions:**
- Multi-supplier strategy implementation
- Comprehensive cybersecurity upgrade
- Succession planning ve talent development

### 3. Financial Risks
**Risk Alanları:**
- Currency fluctuation exposure
- Interest rate changes impact
- Credit risk from customer base

**Risk Management Approach:**
- Hedging strategies for currency exposure
- Debt structure optimization
- Customer credit assessment enhancement

## SONUÇ VE TAVSİYELER

Bu kapsamlı değerlendirme ışığında, şirketimizin mevcut performansı son derece başarılı ve gelecek potansiyeli oldukça parlak görünmektedir. Ancak, sürdürülebilir büyüme için aşağıdaki kritik adımları önceliğimize almalıyız:

**Acil Eylem Gerektiren Konular:**
1. Teknoloji yatırımlarının hızlandırılması
2. Yetenek kazanımı ve geliştirme programlarının genişletilmesi
3. Sürdürülebilirlik hedeflerinin operasyonel planlarla entegrasyonu
4. Uluslararası genişleme stratejisinin detaylandırılması

**Stratejik Öncelikler:**
- Customer-centric innovation focus
- Operational excellence through digitalization
- Sustainable business practices implementation
- Strategic partnerships ve ecosystem building

Detaylı financial statements, technical reports ve supporting documentation'lar ek dosyalarda bulunmaktadır.

Saygılarımla ve başarılar dileğiyle,

{sender.split('@')[0].replace('.', ' ').title()}
Chief Executive Officer & General Manager
{sender.split('@')[1]} | Corporate Headquarters""",

            f"""Değerli Müşterilerimiz ve İş Ortaklarımız,

{subject} hakkında sizlerle paylaşmak istediğim kapsamlı gelişmeler bulunuyor. Bu dönem boyunca gerçekleştirdiğimiz yenilikler, iyileştirmeler ve gelecek planlarımız hakkında detaylı bilgileri aşağıda bulabilirsiniz.

## YENİ ÜRÜN VE HİZMET LANSMANLARIMIZ

### Devrim Niteliğinde Teknoloji Entegrasyonları

Bu çeyrek dönemde teknolojik altyapımızı köklü bir şekilde yenileyerek, müşterilerimize daha iyi hizmet verebilmek adına önemli yatırımlar gerçekleştirdik.

**Yapay Zeka Destekli Yeni Platformumuz:**
Müşteri deneyimini tamamen dönüştüren AI-powered sistemimiz artık aktif. Bu sistem sayesinde:
- Kişiselleştirilmiş öneriler real-time olarak sunuluyor
- Predictive analytics ile proaktif çözümler üretiliyor
- 7/24 intelligent chatbot desteği sağlanıyor
- Automated workflow optimization gerçekleşiyor
- Advanced reporting ve analytics capabilities mevcut

**Blockchain Tabanlı Güvenlik Sistemi:**
Veri güvenliğinizi en üst seviyede korumak için blockchain teknologisini entegre ettik:
- Immutable transaction records
- Enhanced data encryption protocols
- Decentralized authentication mechanisms
- Smart contracts for automated processes
- Compliance tracking ve audit trails

### Mobile-First Yaklaşımıyla Yeni Mobil Uygulamamız

**Özellik Detayları:**
- Cross-platform compatibility (iOS, Android, Web)
- Offline functionality with seamless sync
- Biometric authentication support
- Push notifications with smart filtering
- Intuitive UI/UX design based on user research
- Performance optimization for all device types

**Kullanıcı Deneyimi İnovasyonları:**
- Voice command integration
- Augmented reality features select modules'lerde
- Gesture-based navigation options
- Accessibility features comprehensive support
- Multi-language support 15+ languages

## MÜŞTERİ HİZMETLERİ VE DESTEK SİSTEMLERİ

### 360 Derece Müşteri Destek Ekosistemi

**Omnichannel Support Structure:**
Müşterilerimizin bizimle iletişim kurma şeklini tamamen yeniledik:

1. **Integrated Communication Hub**
   - Live chat with video call capability
   - Email support with smart routing
   - Phone support with callback options
   - Social media monitoring ve response
   - In-app messaging with context awareness

2. **Self-Service Portal Enhancement**
   - Comprehensive knowledge base 500+ articles
   - Interactive troubleshooting guides
   - Video tutorials library 200+ videos
   - Community forum with expert moderation
   - AI-powered search functionality

3. **Proactive Support Services**
   - Health monitoring automated alerts
   - Performance optimization recommendations
   - Preventive maintenance scheduling
   - Usage analytics ve optimization tips
   - Security audit automated reports

### Eğitim ve Gelişim Programları

**Müşteri Eğitim Akademisi:**
Ürün ve hizmetlerimizden maksimum fayda sağlamanız için:
- Beginner'dan advanced'e training modules
- Certification programs industry-recognized
- Webinar series monthly expert sessions
- Hands-on workshop opportunities
- Personalized learning paths based on usage

**Partner Enablement Program:**
İş ortaklarımızın başarısı bizim başarımız:
- Technical certification tracks
- Sales enablement tools ve resources
- Marketing support materials
- Co-marketing opportunities
- Revenue sharing optimization programs

## SÜRDÜRÜLEMIR İŞ PRATİKLERİ VE SOSYAL SORUMLULUK

### Environmental Impact Initiatives

**Carbon Footprint Reduction:**
2024 yılında carbon neutrality hedefimize ulaşmak için:
- Renewable energy 85% of operations'da
- Paperless office initiative %97 completion
- Remote work optimization carbon reduction
- Green transportation incentives employees için
- Sustainable supply chain partnerships

**Circular Economy Implementation:**
- Product lifecycle extension programs
- Recycling initiatives customer products için
- Waste reduction targets %40 by year-end
- Sustainable packaging materials transition
- End-of-life product management programs

### Sosyal Etki ve Toplumsal Katkı Projeleri

**Education ve Skill Development:**
- Digital literacy programs underserved communities
- Scholarship programs technical education için
- Mentorship opportunities young professionals
- Open-source contribution initiatives
- STEM education support local schools

**Community Investment Programs:**
- Local economic development partnerships
- Small business incubation support
- Volunteer programs employee participation
- Charitable giving matching programs
- Disaster relief rapid response capabilities

## FİNANSAL PERFORMANS VE YATIRIM PLANLARI

### Q3 2024 Financial Highlights

**Revenue Performance:**
- Total revenue ₺78.6M (+34% YoY)
- Recurring revenue ₺52.1M (66% of total)
- New customer acquisition +2,847 accounts
- Average customer lifetime value ₺156K (+22%)
- Customer retention rate %96.3

**Profitability Metrics:**
- Gross margin %67.2 (improvement from %64.1)
- EBITDA margin %24.8 (target %22'yi exceeded)
- Net profit margin %18.3 (industry leading)
- Return on investment %34.7
- Cash flow positive 18 consecutive months

### Strategic Investment Allocation

**Technology Infrastructure (%45 of total investment):**
- Cloud platform scalability enhancement
- AI/ML capabilities expansion
- Cybersecurity infrastructure upgrade
- Data analytics platform development
- Mobile technology advancement

**Human Capital Development (%25):**
- Talent acquisition specialized roles
- Employee training ve certification
- Leadership development programs
- Performance management system upgrade
- Workplace culture enhancement initiatives

**Market Expansion (%20):**
- Geographic expansion 5 new markets
- Product line extension research
- Strategic partnership development
- Brand awareness campaigns
- Customer acquisition cost optimization

**R&D Innovation (%10):**
- Emerging technology exploration
- Product innovation pipeline
- Patent development initiatives
- University research partnerships
- Innovation lab establishment

## GELECEK VİZYONUMUZ VE 2025 HEDEFLERI

### Transformational Growth Strategy

**Digital Leadership Vision:**
2025 yılına kadar sektörümüzde digital transformation leader pozisyonunda olmayı hedefliyoruz:

**Technology Innovation Roadmap:**
- Artificial Intelligence integration her department'ta
- Internet of Things (IoT) ecosystem development
- Quantum computing readiness preparation
- 5G technology utilization optimization
- Edge computing capabilities deployment

**Market Position Enhancement:**
- Market share %18'e çıkarma hedefi (currently %12.3)
- International presence 12 countries'e genişletme
- Industry vertical expansion 4 new sectors
- Strategic acquisitions consideration 3-5 targets
- Partnership ecosystem 50+ active partners

### Customer-Centric Evolution Strategy

**Experience Excellence Goals:**
- Net Promoter Score 95+ target (currently 87)
- Customer satisfaction %98+ achievement
- First contact resolution %85+ improvement
- Average response time <2 hours guarantee
- Personalization engine 99% accuracy rate

**Innovation Pipeline 2025:**
- Next-generation product launch Q2 2025
- AI-powered predictive services rollout
- Blockchain integration industry applications
- Augmented reality features consumer products
- Voice interface technology comprehensive implementation

## SONUÇ VE İLERİ ADIMLAR

Bu comprehensive değerlendirme çerçevesinde, şirketimizin hem mevcut performansı hem de gelecek potansiyeli son derece güçlü bir trajectory sergiliyor. Müşteri memnuniyeti, finansal performans, teknolojik yenilik ve sürdürülebilirlik alanlarında elde ettiğimiz başarılar, gelecek dönemde daha da büyük hedeflere ulaşmamız için solid bir foundation oluşturuyor.

**Immediate Action Items:**
- Customer feedback integration product roadmap
- Technology infrastructure scaling acceleration  
- Team expansion critical roles için
- Partnership agreements finalization
- Sustainability metrics integration business operations

**Long-term Strategic Imperatives:**
- Market leadership position consolidation
- Innovation culture organization-wide embedding
- Customer success platform comprehensive development
- Global expansion strategy systematic execution
- ESG goals integration corporate strategy ile

Ek dosyalarda detaylı technical specifications, financial statements ve strategic plans bulunmaktadır. Herhangi bir konuda daha fazla bilgiye ihtiyaç duyarsanız, lütfen benimle iletişime geçmekten çekinmeyin.

Sizlerle çalışmak bizim için bir ayrıcalık ve gelecekte daha nice başarılar elde etmek için sabırsızlanıyoruz.

Saygı ve sevgilerimle,

{sender.split('@')[0].replace('.', ' ').title()}
Chief Innovation Officer & VP of Customer Success
{sender.split('@')[1]} | Innovation Center"""
        ]
        
        content = random.choice(content_templates)
        
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
    try:
        if not request.recaptcha_token:
            raise HTTPException(status_code=400, detail="reCAPTCHA token gerekli")
        
        verification_result = await verify_recaptcha_token(request.recaptcha_token)
        
        if verification_result.get("success", False):
            return RecaptchaVerificationResponse(
                success=True,
                message="reCAPTCHA doğrulaması başarılı"
            )
        else:
            error_codes = verification_result.get("error-codes", [])
            logging.warning(f"reCAPTCHA verification failed: {error_codes}")
            
            return RecaptchaVerificationResponse(
                success=False,
                message="reCAPTCHA doğrulaması başarısız"
            )
    except Exception as e:
        logging.error(f"reCAPTCHA endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="reCAPTCHA doğrulama servisi geçici olarak kullanılamıyor")

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
    
    # Log the registration
    await add_system_log(
        log_type="USER_REGISTER",
        message=f"Yeni kullanıcı kaydı oluşturuldu: {user_data.name} ({user_data.email})",
        user_email=user_data.email,
        user_name=user_data.name,
        additional_data={"user_id": new_user.id, "approved": False}
    )
    
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
        
        # Log successful login
        await add_system_log(
            log_type="USER_LOGIN",
            message=f"Demo kullanıcısı başarıyla giriş yaptı: {user.name} ({user.email})",
            user_email=user.email,
            user_name=user.name,
            additional_data={"user_id": user.id, "user_type": user.user_type}
        )
        
        return {
            "token": token,
            "user": {
                "id": user.id, 
                "name": user.name, 
                "email": user.email,
                "user_type": user.user_type
            }
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
    
    # Log successful login
    await add_system_log(
        log_type="USER_LOGIN",
        message=f"Kullanıcı başarıyla giriş yaptı: {user_obj.name} ({user_obj.email})",
        user_email=user_obj.email,
        user_name=user_obj.name,
        additional_data={"user_id": user_obj.id, "user_type": user_obj.user_type}
    )
    
    return {
        "token": token,
        "user": {
            "id": user_obj.id, 
            "name": user_obj.name, 
            "email": user_obj.email,
            "user_type": user_obj.user_type
        }
    }

@api_router.post("/auth/outlook-login")
async def outlook_login(code: str, state: str):
    """Complete Outlook OAuth login and create/login user"""
    try:
        if not outlook_auth_service.is_configured():
            raise HTTPException(
                status_code=503, 
                detail="Outlook integration not configured. Azure credentials needed."
            )
        
        # Exchange authorization code for tokens
        token_data = await exchange_code_for_tokens(code)
        
        if not token_data:
            raise HTTPException(status_code=400, detail="Failed to exchange code for tokens")
        
        # Get user profile from Microsoft Graph
        user_profile = await get_user_profile_from_graph(token_data["access_token"])
        
        if not user_profile:
            raise HTTPException(status_code=400, detail="Failed to get user profile")
        
        # Check if Outlook user already exists
        existing_user = await db.users.find_one({
            "email": user_profile.get("mail") or user_profile.get("userPrincipalName"),
            "user_type": "outlook"
        })
        
        user_email = user_profile.get("mail") or user_profile.get("userPrincipalName")
        
        if existing_user:
            # Update last login
            await db.users.update_one(
                {"id": existing_user["id"]},
                {"$set": {"last_login": datetime.now(timezone.utc)}}
            )
            user = existing_user
        else:
            # Create new Outlook user (auto-approved)
            new_user = OutlookUser(
                email=user_email,
                display_name=user_profile.get("displayName", ""),
                microsoft_user_id=user_profile["id"],
                tenant_id=os.getenv("AZURE_TENANT_ID", ""),
                last_login=datetime.now(timezone.utc)
            )
            
            user_dict = new_user.dict()
            await db.users.insert_one(user_dict)
            user = user_dict
        
        # Create JWT token for the user
        token = create_jwt_token(user)
        
        return {
            "token": token,
            "user": {
                "id": user["id"],
                "name": user.get("display_name", user.get("name", "")),
                "email": user["email"],
                "user_type": user.get("user_type", "outlook")
            },
            "message": "Outlook login successful"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during Outlook login: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

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
    # Admin yetkisi kontrolü - sadece user_type="admin" olanlar erişebilir
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Bu işlem için admin yetkisi gerekli")
    
    # Önce kullanıcı bilgilerini al
    user_to_approve = await db.users.find_one({"id": user_id})
    if not user_to_approve:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    
    # Kullanıcıyı bul ve onayla
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"approved": True}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    
    # Log the approval
    await add_system_log(
        log_type="USER_APPROVED",
        message=f"Kullanıcı onaylandı: {user_to_approve.get('name', 'İsimsiz')} ({user_to_approve.get('email', 'Email yok')}) - Admin: {current_user.get('name', current_user.get('email'))}",
        user_email=user_to_approve.get('email'),
        user_name=user_to_approve.get('name'),
        additional_data={"user_id": user_id, "admin_email": current_user.get('email')}
    )
    
    return {"message": "Kullanıcı başarıyla onaylandı", "user_id": user_id}

@api_router.post("/admin/pending-users")
async def get_pending_users(current_user: dict = Depends(get_current_user)):
    """
    Admin endpoint - Onay bekleyen kullanıcıları listeler
    """
    # Admin yetkisi kontrolü - sadece user_type="admin" olanlar erişebilir
    if current_user.get("user_type") != "admin":
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
@api_router.post("/admin/users")
async def get_all_users(current_user: dict = Depends(get_current_user)):
    """
    Admin endpoint - Tüm kullanıcıları ve storage bilgilerini listeler
    """
    # Admin yetkisi kontrolü - sadece user_type="admin" olanlar erişebilir
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Bu işlem için admin yetkisi gerekli")
    
    # Tüm kullanıcıları getir
    users_cursor = db.users.find({})
    users = await users_cursor.to_list(length=None)
    
    # Her kullanıcı için storage bilgisini hesapla
    users_with_storage = []
    for user in users:
        user_dict = dict(user)
        if "_id" in user_dict:
            del user_dict["_id"]
        if "password" in user_dict:
            del user_dict["password"]
        
        # Storage bilgisini hesapla
        total_emails = await db.emails.count_documents({"user_id": user_dict["id"]})
        
        # Total size hesaplama
        pipeline = [
            {"$match": {"user_id": user_dict["id"]}},
            {"$group": {"_id": None, "totalSize": {"$sum": {"$strLenCP": "$content"}}}}
        ]
        
        result = await db.emails.aggregate(pipeline).to_list(length=1)
        total_size = result[0]["totalSize"] if result else 0
        
        user_dict["storage_info"] = {
            "totalEmails": total_emails,
            "totalSize": total_size
        }
        
        users_with_storage.append(user_dict)
    
    return {"users": users_with_storage}

@api_router.post("/admin/reject-user/{user_id}")
async def reject_user(user_id: str, current_user: dict = Depends(get_current_user)):
    """
    Admin endpoint - Kullanıcıyı reddeder (hesabı siler)
    """
    # Admin yetkisi kontrolü - sadece user_type="admin" olanlar erişebilir
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Bu işlem için admin yetkisi gerekli")
    
    # Kullanıcıyı bul ve sil
    result = await db.users.delete_one({"id": user_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    
    # Kullanıcının e-postalarını da sil
    await db.emails.delete_many({"user_id": user_id})
    
    return {"message": "Kullanıcı başarıyla reddedildi ve hesabı silindi", "user_id": user_id}

@api_router.post("/admin/create-admin")
async def create_admin():
    """
    Admin kullanıcısını oluşturan endpoint (sadece bir kez çalıştırılmalı)
    """
    # Önce mevcut admin@postadepo.com kullanıcısını silelim
    await db.users.delete_one({"email": "admin@postadepo.com"})
    
    # Admin kullanıcısını oluştur
    admin_user = User(
        name="Admin",
        email="admin@postadepo.com",
        approved=True,
        user_type="admin"
    )
    
    admin_dict = admin_user.dict()
    # Şifreyi hash'le ve ekle
    admin_dict["password"] = hash_password("admindepo*")
    
    await db.users.insert_one(admin_dict)
    
    return {"message": "Admin kullanıcısı başarıyla oluşturuldu", "email": "admin@postadepo.com"}

@api_router.post("/admin/system-logs")
async def get_system_logs(current_user: dict = Depends(get_current_user)):
    """
    Admin endpoint - Sistem loglarını listeler
    """
    # Admin yetkisi kontrolü
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Bu işlem için admin yetkisi gerekli")
    
    # Son 100 sistem logunu getir (tarih sırasına göre en yeni önce)
    logs_cursor = db.system_logs.find({}).sort("timestamp", -1).limit(100)
    logs = await logs_cursor.to_list(length=None)
    
    # Logları temizle
    cleaned_logs = []
    for log in logs:
        log_dict = dict(log)
        if "_id" in log_dict:
            del log_dict["_id"]
        # ISO format timestamp'i Türkçe formatına çevir
        if "timestamp" in log_dict:
            try:
                timestamp = log_dict["timestamp"]
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                log_dict["formatted_timestamp"] = timestamp.strftime("%d.%m.%Y %H:%M:%S")
            except:
                log_dict["formatted_timestamp"] = "Bilinmeyen"
        cleaned_logs.append(log_dict)
    
    return {"logs": cleaned_logs}

@api_router.post("/admin/system-logs/export")
async def export_system_logs(current_user: dict = Depends(get_current_user)):
    """
    Admin endpoint - Sistem loglarını JSON formatında indirir
    """
    # Admin yetkisi kontrolü
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Bu işlem için admin yetkisi gerekli")
    
    # Tüm sistem loglarını getir
    logs_cursor = db.system_logs.find({}).sort("timestamp", -1)
    logs = await logs_cursor.to_list(length=None)
    
    # Logları temizle ve formatla
    export_data = {
        "export_info": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generated_by": current_user.get("email"),
            "total_logs": len(logs)
        },
        "logs": []
    }
    
    for log in logs:
        log_dict = dict(log)
        if "_id" in log_dict:
            del log_dict["_id"]
        export_data["logs"].append(log_dict)
    
    # JSON response olarak dön
    import json
    json_content = json.dumps(export_data, indent=2, ensure_ascii=False, default=str)
    
    from fastapi.responses import Response
    return Response(
        content=json_content,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=system_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        }
    )

class BulkUserRequest(BaseModel):
    user_ids: List[str]

@api_router.post("/admin/bulk-approve-users")
async def bulk_approve_users(request: BulkUserRequest, current_user: dict = Depends(get_current_user)):
    """
    Admin endpoint - Belirtilen kullanıcıları toplu onayla
    """
    # Admin yetkisi kontrolü
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Bu işlem için admin yetkisi gerekli")
    
    if not request.user_ids:
        return {"message": "Onaylanacak kullanıcı ID'si belirtilmedi", "approved_count": 0, "failed_count": 0}
    
    # Belirtilen kullanıcıları bul
    users_to_approve = await db.users.find({"id": {"$in": request.user_ids}}).to_list(length=None)
    
    if not users_to_approve:
        return {"message": "Onaylanacak kullanıcı bulunamadı", "approved_count": 0, "failed_count": len(request.user_ids)}
    
    # Kullanıcıları onayla
    result = await db.users.update_many(
        {"id": {"$in": request.user_ids}},
        {"$set": {"approved": True}}
    )
    
    # Log ekle
    user_emails = [user.get('email', 'Email yok') for user in users_to_approve]
    await add_system_log(
        log_type="BULK_USER_APPROVED",
        message=f"Toplu kullanıcı onayı: {result.modified_count} kullanıcı onaylandı - Admin: {current_user.get('name', current_user.get('email'))}",
        user_email=current_user.get('email'),
        user_name=current_user.get('name'),
        additional_data={"approved_count": result.modified_count, "approved_emails": user_emails}
    )
    
    failed_count = len(request.user_ids) - result.modified_count
    return {
        "message": f"{result.modified_count} kullanıcı başarıyla onaylandı", 
        "approved_count": result.modified_count,
        "failed_count": failed_count
    }

@api_router.post("/admin/bulk-reject-users")
async def bulk_reject_users(request: BulkUserRequest, current_user: dict = Depends(get_current_user)):
    """
    Admin endpoint - Belirtilen kullanıcıları toplu reddet (sil)
    """
    # Admin yetkisi kontrolü
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Bu işlem için admin yetkisi gerekli")
    
    if not request.user_ids:
        return {"message": "Reddedilecek kullanıcı ID'si belirtilmedi", "rejected_count": 0, "failed_count": 0}
    
    # Belirtilen kullanıcıları bul
    users_to_reject = await db.users.find({"id": {"$in": request.user_ids}}).to_list(length=None)
    
    if not users_to_reject:
        return {"message": "Reddedilecek kullanıcı bulunamadı", "rejected_count": 0, "failed_count": len(request.user_ids)}
    
    # Kullanıcı bilgilerini topla
    user_emails = [user.get('email', 'Email yok') for user in users_to_reject]
    
    # Kullanıcıları sil
    delete_result = await db.users.delete_many({"id": {"$in": request.user_ids}})
    
    # Kullanıcıların e-postalarını da sil
    await db.emails.delete_many({"user_id": {"$in": request.user_ids}})
    
    # Log ekle
    await add_system_log(
        log_type="BULK_USER_REJECTED",
        message=f"Toplu kullanıcı reddi: {delete_result.deleted_count} kullanıcı reddedildi ve silindi - Admin: {current_user.get('name', current_user.get('email'))}",
        user_email=current_user.get('email'),
        user_name=current_user.get('name'),
        additional_data={"rejected_count": delete_result.deleted_count, "rejected_emails": user_emails}
    )
    
    failed_count = len(request.user_ids) - delete_result.deleted_count
    return {
        "message": f"{delete_result.deleted_count} kullanıcı başarıyla reddedildi ve silindi", 
        "rejected_count": delete_result.deleted_count,
        "failed_count": failed_count
    }

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
        logging.error(f"Error downloading attachment: {str(e)}")
        # Check if it's a 404 case (attachment not found)
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail="Attachment not found")
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

# ============== MICROSOFT GRAPH API INTEGRATION ==============

class OutlookAuthService:
    """Microsoft Graph API authentication service"""
    
    def __init__(self):
        self.client_id = os.getenv('AZURE_CLIENT_ID')
        self.client_secret = os.getenv('AZURE_CLIENT_SECRET')
        self.tenant_id = os.getenv('AZURE_TENANT_ID')
        self.scopes = [os.getenv('GRAPH_API_SCOPE', 'https://graph.microsoft.com/.default')]
        self.graph_client: Optional[GraphServiceClient] = None
        
    async def get_graph_client(self) -> Optional[GraphServiceClient]:
        """Get authenticated Graph client"""
        if not GRAPH_AVAILABLE:
            logger.warning("Microsoft Graph SDK not available")
            return None
            
        if not all([self.client_id, self.client_secret, self.tenant_id]):
            logger.warning("Azure credentials not configured")
            return None
            
        if not self.graph_client:
            try:
                credential = ClientSecretCredential(
                    tenant_id=self.tenant_id,
                    client_id=self.client_id,
                    client_secret=self.client_secret
                )
                self.graph_client = GraphServiceClient(
                    credentials=credential,
                    scopes=self.scopes
                )
                logger.info("Microsoft Graph client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Graph client: {e}")
                return None
                
        return self.graph_client
    
    def is_configured(self) -> bool:
        """Check if Azure credentials are configured"""
        return all([self.client_id, self.client_secret, self.tenant_id]) and GRAPH_AVAILABLE

class OutlookEmailService:
    """Microsoft Graph API email service with token-based authentication"""
    
    def __init__(self):
        self.auth_service = OutlookAuthService()
        
    async def get_user_emails(self, user_email: str, folder_name: str = "Inbox", top: int = 50) -> List[Dict[str, Any]]:
        """Get emails from user's Outlook account"""
        try:
            graph_client = await self.auth_service.get_graph_client()
            if not graph_client:
                logger.warning("Graph client not available, returning empty list")
                return []
            
            # Get folder ID by name
            folders = await graph_client.users.by_user_id(user_email).mail_folders.get()
            folder_id = None
            
            if folders and folders.value:
                for folder in folders.value:
                    if folder.display_name and folder.display_name.lower() == folder_name.lower():
                        folder_id = folder.id
                        break
            
            if not folder_id:
                logger.warning(f"Folder '{folder_name}' not found for user {user_email}")
                return []
            
            # Get messages
            query_params = MessagesRequestBuilder.MessagesRequestBuilderGetQueryParameters(
                top=top,
                orderby=["receivedDateTime desc"],
                select=["id", "subject", "bodyPreview", "body", "from", "toRecipients", 
                       "receivedDateTime", "sentDateTime", "importance", "isRead", 
                       "hasAttachments", "parentFolderId"]
            )
            
            request_config = MessagesRequestBuilder.MessagesRequestBuilderGetRequestConfiguration(
                query_parameters=query_params
            )
            
            messages = await graph_client.users.by_user_id(user_email).mail_folders.by_mail_folder_id(folder_id).messages.get(request_configuration=request_config)
            
            emails = []
            if messages and messages.value:
                for msg in messages.value:
                    # Convert Graph message to our format
                    email_data = await self._convert_graph_message(msg, user_email, folder_name)
                    emails.append(email_data)
            
            logger.info(f"Retrieved {len(emails)} emails from {user_email}")
            return emails
            
        except Exception as e:
            logger.error(f"Error retrieving emails for {user_email}: {e}")
            return []
    
    async def _convert_graph_message(self, message: 'Message', user_email: str, folder_name: str) -> Dict[str, Any]:
        """Convert Microsoft Graph Message to our email format"""
        
        # Handle sender
        sender = "Unknown Sender"
        if message.from_ and message.from_.email_address:
            sender_name = message.from_.email_address.name or ""
            sender_addr = message.from_.email_address.address or ""
            sender = f"{sender_addr} ({sender_name})" if sender_name else sender_addr
        
        # Handle recipients
        recipients = []
        if message.to_recipients:
            for recipient in message.to_recipients:
                if recipient.email_address and recipient.email_address.address:
                    recipients.append(recipient.email_address.address)
        
        recipient = ", ".join(recipients) if recipients else user_email
        
        # Handle content
        content = ""
        preview = ""
        if message.body:
            content = message.body.content or ""
            preview = message.body_preview or content[:200]
        
        # Handle datetime
        received_datetime = message.received_date_time
        if received_datetime and received_datetime.tzinfo is None:
            received_datetime = received_datetime.replace(tzinfo=timezone.utc)
        
        return {
            "id": str(uuid.uuid4()),
            "message_id": message.id or str(uuid.uuid4()),
            "user_id": user_email,
            "account_id": f"outlook-{user_email}",
            "folder": folder_name.lower(),
            "sender": sender,
            "recipient": recipient,
            "subject": message.subject or "(No Subject)",
            "content": content,
            "preview": preview,
            "date": received_datetime or datetime.now(timezone.utc),
            "read": message.is_read if message.is_read is not None else False,
            "important": message.importance.value == "high" if message.importance else False,
            "size": len(content.encode('utf-8')) if content else 1024,
            "thread_id": None,  # TODO: Implement threading
            "attachments": [],  # TODO: Implement attachments
            "source": "outlook"
        }
    
    async def sync_emails_with_token(self, account_id: str, folder_names: List[str] = None) -> Dict[str, Any]:
        """Sync emails using stored access token"""
        try:
            # Get valid access token
            access_token = await get_valid_access_token(account_id)
            if not access_token:
                raise HTTPException(status_code=401, detail="No valid access token available")
            
            # Get account details
            account = await db.connected_accounts.find_one({"id": account_id, "is_connected": True})
            if not account:
                raise HTTPException(status_code=404, detail="Account not found")
            
            # Default folders to sync all major folders
            if not folder_names:
                folder_names = ["inbox", "sent", "drafts", "junk", "deleted"]
            
            total_synced = 0
            folder_results = {}
            
            # Sync each folder
            for folder_name in folder_names:
                try:
                    folder_result = await self._sync_folder_with_token(
                        access_token, account, folder_name
                    )
                    folder_results[folder_name] = folder_result
                    total_synced += folder_result["synced_count"]
                    
                except Exception as e:
                    logger.error(f"Error syncing folder {folder_name}: {e}")
                    folder_results[folder_name] = {
                        "synced_count": 0,
                        "error": str(e)
                    }
            
            # Update account sync timestamp
            await db.connected_accounts.update_one(
                {"id": account_id},
                {"$set": {"last_sync": datetime.now(timezone.utc)}}
            )
            
            return {
                "account_id": account_id,
                "account_email": account["email"],
                "total_synced": total_synced,
                "folders": folder_results,
                "sync_timestamp": datetime.now(timezone.utc)
            }
            
        except Exception as e:
            logger.error(f"Error syncing emails for account {account_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Email sync failed: {str(e)}")
    
    async def _sync_folder_with_token(self, access_token: str, account: dict, folder_name: str) -> Dict[str, Any]:
        """Sync specific folder using access token"""
        try:
            # Get folder messages from Microsoft Graph API
            folder_id = await self._get_folder_id(access_token, folder_name)
            if not folder_id:
                return {"synced_count": 0, "error": f"Folder '{folder_name}' not found"}
            
            # Microsoft Graph API endpoint
            graph_url = f"https://graph.microsoft.com/v1.0/me/mailFolders/{folder_id}/messages"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Parameters for email retrieval
            params = {
                "$top": 50,  # Batch size
                "$orderby": "receivedDateTime desc",
                "$select": "id,subject,bodyPreview,body,from,toRecipients,receivedDateTime,isRead,hasAttachments,parentFolderId"
            }
            
            synced_count = 0
            
            async with httpx.AsyncClient() as client:
                response = await client.get(graph_url, headers=headers, params=params)
                
                if response.status_code != 200:
                    raise Exception(f"Graph API error: {response.status_code} - {response.text}")
                
                data = response.json()
                messages = data.get("value", [])
                
                # Process each message
                for message in messages:
                    try:
                        email_data = await self._convert_graph_message_v2(message, account, folder_name)
                        
                        # Check if email already exists
                        existing = await db.emails.find_one({
                            "message_id": email_data["message_id"],
                            "user_id": account["user_id"]
                        })
                        
                        if not existing:
                            await db.emails.insert_one(email_data)
                            synced_count += 1
                            
                    except Exception as e:
                        logger.error(f"Error processing message {message.get('id', 'unknown')}: {e}")
                        continue
            
            return {"synced_count": synced_count}
            
        except Exception as e:
            logger.error(f"Error syncing folder {folder_name}: {e}")
            return {"synced_count": 0, "error": str(e)}
    
    async def _get_folder_id(self, access_token: str, folder_name: str) -> Optional[str]:
        """Get folder ID by name"""
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://graph.microsoft.com/v1.0/me/mailFolders",
                    headers=headers
                )
                
                if response.status_code != 200:
                    return None
                
                data = response.json()
                folders = data.get("value", [])
                
                # Look for folder by display name (case insensitive)
                for folder in folders:
                    if folder.get("displayName", "").lower() == folder_name.lower():
                        return folder.get("id")
                
                # Also check standard folder names
                folder_mapping = {
                    "inbox": "inbox",
                    "sent": "sentitems", 
                    "drafts": "drafts",
                    "junk": "junkemail",
                    "deleted": "deleteditems"
                }
                
                target_name = folder_mapping.get(folder_name.lower(), folder_name.lower())
                for folder in folders:
                    if folder.get("displayName", "").lower().replace(" ", "") == target_name:
                        return folder.get("id")
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting folder ID for {folder_name}: {e}")
            return None
    
    async def _convert_graph_message_v2(self, message: dict, account: dict, folder_name: str) -> Dict[str, Any]:
        """Convert Microsoft Graph message to our email format (v2 with token auth)"""
        
        # Handle sender
        sender_email = ""
        sender_name = ""
        if message.get("from") and message["from"].get("emailAddress"):
            sender_email = message["from"]["emailAddress"].get("address", "")
            sender_name = message["from"]["emailAddress"].get("name", "")
        
        # Handle recipients
        recipients = []
        if message.get("toRecipients"):
            for recipient in message["toRecipients"]:
                if recipient.get("emailAddress", {}).get("address"):
                    recipients.append(recipient["emailAddress"]["address"])
        
        # Handle content
        content = ""
        content_type = "text"
        if message.get("body"):
            content = message["body"].get("content", "")
            content_type = message["body"].get("contentType", "text")
        
        preview = message.get("bodyPreview", content[:200])
        
        # Handle datetime
        received_datetime = message.get("receivedDateTime")
        if received_datetime:
            try:
                received_datetime = datetime.fromisoformat(received_datetime.replace("Z", "+00:00"))
            except:
                received_datetime = datetime.now(timezone.utc)
        else:
            received_datetime = datetime.now(timezone.utc)
        
        return {
            "id": str(uuid.uuid4()),
            "message_id": message.get("id", str(uuid.uuid4())),
            "user_id": account["user_id"],
            "account_id": account["id"],
            "account_email": account["email"],
            "folder": folder_name.lower(),
            "sender": sender_email,
            "sender_name": sender_name,
            "recipients": recipients,
            "subject": message.get("subject", "(No Subject)"),
            "content": content,
            "content_type": content_type,
            "preview": preview,
            "date": received_datetime,
            "read": message.get("isRead", False),
            "has_attachments": message.get("hasAttachments", False),
            "size": len(content.encode('utf-8')) if content else 1024,
            "thread_id": None,  
            "attachments": [],  
            "source": "outlook",
            "synced_at": datetime.now(timezone.utc)
        }

    async def sync_user_emails(self, user_email: str, folder_name: str = "Inbox", sync_count: int = 50) -> Dict[str, Any]:
        """Legacy sync method - kept for compatibility"""
        try:
            emails = await self.get_user_emails(user_email, folder_name, sync_count)
            
            synced_count = 0
            skipped_count = 0
            error_count = 0
            
            for email_data in emails:
                try:
                    # Check if email already exists
                    existing = await db.emails.find_one({
                        "message_id": email_data["message_id"],
                        "user_id": user_email
                    })
                    
                    if existing:
                        skipped_count += 1
                        continue
                    
                    # Insert new email
                    await db.emails.insert_one(email_data)
                    synced_count += 1
                    
                except Exception as e:
                    logger.error(f"Error syncing email {email_data.get('message_id', 'unknown')}: {e}")
                    error_count += 1
            
            return {
                "account_email": user_email,
                "synced_count": synced_count,
                "skipped_count": skipped_count,
                "error_count": error_count,
                "sync_timestamp": datetime.now(timezone.utc)
            }
            
        except Exception as e:
            logger.error(f"Error syncing emails for {user_email}: {e}")
            raise HTTPException(status_code=500, detail=f"Email sync failed: {str(e)}")

# Global service instances
outlook_auth_service = OutlookAuthService()
outlook_email_service = OutlookEmailService()

# ============== OUTLOOK API ENDPOINTS ==============

@api_router.get("/outlook/status")
async def outlook_status():
    """Check Outlook API integration status"""
    return {
        "graph_sdk_available": GRAPH_AVAILABLE,
        "credentials_configured": outlook_auth_service.is_configured(),
        "client_id_set": bool(os.getenv('AZURE_CLIENT_ID')),
        "tenant_id_set": bool(os.getenv('AZURE_TENANT_ID')),
        "message": "Outlook API ready" if outlook_auth_service.is_configured() else "Azure credentials needed"
    }

@api_router.get("/outlook/auth-url")
async def get_outlook_auth_url(current_user: dict = Depends(get_current_user)):
    """Get Microsoft OAuth2 authorization URL"""
    try:
        if not outlook_auth_service.is_configured():
            raise HTTPException(
                status_code=503, 
                detail="Outlook integration not configured. Azure credentials needed."
            )
        
        # OAuth2 scopes for email access
        scopes = [
            "https://graph.microsoft.com/Mail.Read",
            "https://graph.microsoft.com/Mail.ReadWrite", 
            "https://graph.microsoft.com/User.Read",
            "offline_access"
        ]
        
        # State parameter for security (CSRF protection)
        state = f"{current_user['id']}_{str(uuid.uuid4())}"
        
        # Store state in database for later verification
        await db.oauth_states.insert_one({
            "state": state,
            "user_id": current_user["id"],
            "created_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc).replace(minute=datetime.now(timezone.utc).minute + 10)  # 10 min expiry
        })
        
        # Build authorization URL - try multiple redirect URIs
        redirect_uri = os.getenv('REDIRECT_URI', 'https://code-state-helper.preview.emergentagent.com/auth/callback')
        
        auth_url = (
            f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?"
            f"client_id={os.getenv('AZURE_CLIENT_ID')}&"
            f"response_type=code&"
            f"redirect_uri={redirect_uri}&"
            f"response_mode=query&"
            f"scope={' '.join(scopes)}&"
            f"state={state}"
        )
        
        return {
            "auth_url": auth_url,
            "state": state,
            "redirect_uri": os.getenv('REDIRECT_URI', 'https://code-state-helper.preview.emergentagent.com/auth/callback')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating auth URL: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate auth URL")

@api_router.post("/outlook/connect-account")
async def connect_outlook_account(
    code: str = Query(...),
    state: str = Query(...),
    current_user: dict = Depends(get_current_user)
):
    """Connect user's Outlook account with OAuth2 code"""
    try:
        if not outlook_auth_service.is_configured():
            raise HTTPException(
                status_code=503, 
                detail="Outlook integration not configured. Azure credentials needed."
            )
        
        # Verify state parameter
        oauth_state = await db.oauth_states.find_one({"state": state, "user_id": current_user["id"]})
        if not oauth_state:
            raise HTTPException(status_code=400, detail="Invalid or expired state parameter")
        
        # Check if state is expired
        if datetime.now(timezone.utc) > oauth_state["expires_at"]:
            raise HTTPException(status_code=400, detail="Authorization state expired")
        
        # Exchange authorization code for tokens
        token_data = await exchange_code_for_tokens(code)
        
        if not token_data:
            raise HTTPException(status_code=400, detail="Failed to exchange code for tokens")
        
        # Get user profile from Microsoft Graph
        user_profile = await get_user_profile_from_graph(token_data["access_token"])
        
        if not user_profile:
            raise HTTPException(status_code=400, detail="Failed to get user profile")
        
        # Check if account already connected
        existing = await db.connected_accounts.find_one({
            "microsoft_user_id": user_profile["id"],
            "user_id": current_user["id"]
        })
        
        if existing:
            # Update existing connection with new tokens
            await db.connected_accounts.update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "access_token": token_data["access_token"],
                    "refresh_token": token_data.get("refresh_token"),
                    "token_expires_at": datetime.now(timezone.utc).replace(
                        second=datetime.now(timezone.utc).second + token_data.get("expires_in", 3600)
                    ),
                    "last_connected": datetime.now(timezone.utc),
                    "is_connected": True
                }}
            )
            return {"message": "Account reconnected successfully", "account": existing}
        
        # Create new connection
        connection_data = {
            "id": str(uuid.uuid4()),
            "user_id": current_user["id"],
            "microsoft_user_id": user_profile["id"],
            "email": user_profile.get("mail") or user_profile.get("userPrincipalName"),
            "display_name": user_profile.get("displayName", ""),
            "account_type": "outlook",
            "is_connected": True,
            "connected_at": datetime.now(timezone.utc),
            "last_sync": None,
            "access_token": token_data["access_token"],
            "refresh_token": token_data.get("refresh_token"),
            "token_expires_at": datetime.now(timezone.utc).replace(
                second=datetime.now(timezone.utc).second + token_data.get("expires_in", 3600)
            ),
            "scopes": token_data.get("scope", "").split(" ")
        }
        
        await db.connected_accounts.insert_one(connection_data)
        
        # Log the email account connection
        await add_system_log(
            log_type="EMAIL_ACCOUNT_CONNECTED",
            message=f"E-posta hesabı başarıyla bağlandı: {connection_data['email']} - Kullanıcı: {current_user.get('name', current_user.get('email'))}",
            user_email=current_user.get('email'),
            user_name=current_user.get('name'),
            additional_data={
                "connected_email": connection_data['email'],
                "account_type": "outlook",
                "display_name": connection_data['display_name']
            }
        )
        
        # Clean up used state
        await db.oauth_states.delete_one({"state": state})
        
        return {
            "message": "Outlook account connected successfully",
            "account": {
                "id": connection_data["id"],
                "email": connection_data["email"],
                "display_name": connection_data["display_name"],
                "connected_at": connection_data["connected_at"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error connecting Outlook account: {e}")
        raise HTTPException(status_code=500, detail="Failed to connect account")

@api_router.post("/outlook/connect-account")
async def connect_outlook_account(
    code: str = Query(...),
    state: str = Query(...),
    current_user: dict = Depends(get_current_user)
):
    """Connect user's Outlook account with OAuth2 code"""
    try:
        if not outlook_auth_service.is_configured():
            raise HTTPException(
                status_code=503, 
                detail="Outlook integration not configured. Azure credentials needed."
            )
        
        # Verify state parameter
        oauth_state = await db.oauth_states.find_one({"state": state, "user_id": current_user["id"]})
        if not oauth_state:
            raise HTTPException(status_code=400, detail="Invalid or expired state parameter")
        
        # Check if state is expired
        if datetime.now(timezone.utc) > oauth_state["expires_at"]:
            raise HTTPException(status_code=400, detail="Authorization state expired")
        
        # Exchange authorization code for tokens
        token_data = await exchange_code_for_tokens(code)
        
        if not token_data:
            raise HTTPException(status_code=400, detail="Failed to exchange code for tokens")
        
        # Get user profile from Microsoft Graph
        user_profile = await get_user_profile_from_graph(token_data["access_token"])
        
        if not user_profile:
            raise HTTPException(status_code=400, detail="Failed to get user profile")
        
        # Check if account already connected
        existing = await db.connected_accounts.find_one({
            "microsoft_user_id": user_profile["id"],
            "user_id": current_user["id"]
        })
        
        if existing:
            # Update existing connection with new tokens
            await db.connected_accounts.update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "access_token": token_data["access_token"],
                    "refresh_token": token_data.get("refresh_token"),
                    "token_expires_at": datetime.now(timezone.utc).replace(
                        second=datetime.now(timezone.utc).second + token_data.get("expires_in", 3600)
                    ),
                    "last_connected": datetime.now(timezone.utc),
                    "is_connected": True
                }}
            )
            return {"message": "Account reconnected successfully", "account": existing}
        
        # Create new connection
        connection_data = {
            "id": str(uuid.uuid4()),
            "user_id": current_user["id"],
            "microsoft_user_id": user_profile["id"],
            "email": user_profile.get("mail") or user_profile.get("userPrincipalName"),
            "display_name": user_profile.get("displayName", ""),
            "account_type": "outlook",
            "is_connected": True,
            "connected_at": datetime.now(timezone.utc),
            "last_sync": None,
            "access_token": token_data["access_token"],
            "refresh_token": token_data.get("refresh_token"),
            "token_expires_at": datetime.now(timezone.utc).replace(
                second=datetime.now(timezone.utc).second + token_data.get("expires_in", 3600)
            ),
            "scopes": token_data.get("scope", "").split(" ")
        }
        
        await db.connected_accounts.insert_one(connection_data)
        
        # Log the email account connection
        await add_system_log(
            log_type="EMAIL_ACCOUNT_CONNECTED",
            message=f"E-posta hesabı başarıyla bağlandı: {connection_data['email']} - Kullanıcı: {current_user.get('name', current_user.get('email'))}",
            user_email=current_user.get('email'),
            user_name=current_user.get('name'),
            additional_data={
                "connected_email": connection_data['email'],
                "account_type": "outlook",
                "display_name": connection_data['display_name']
            }
        )
        
        # Clean up used state
        await db.oauth_states.delete_one({"state": state})
        
        return {
            "message": "Outlook account connected successfully",
            "account": {
                "id": connection_data["id"],
                "email": connection_data["email"],
                "display_name": connection_data["display_name"],
                "connected_at": connection_data["connected_at"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error connecting Outlook account: {e}")
        raise HTTPException(status_code=500, detail="Failed to connect account")

# Add alternative GET endpoint for OAuth callback (Microsoft typically uses GET)
@api_router.get("/auth/callback", response_class=HTMLResponse)
async def oauth_callback(
    code: str = Query(...),
    state: str = Query(...)
):
    """OAuth callback endpoint for Microsoft/Outlook"""
    try:
        if not outlook_auth_service.is_configured():
            raise HTTPException(
                status_code=503, 
                detail="Outlook integration not configured. Azure credentials needed."
            )
        
        # Extract user_id from state parameter (format: user_id_uuid)
        try:
            user_id = state.split('_')[0]
        except:
            raise HTTPException(status_code=400, detail="Invalid state format")
        
        # Verify state parameter in database
        oauth_state = await db.oauth_states.find_one({"state": state, "user_id": user_id})
        if not oauth_state:
            raise HTTPException(status_code=400, detail="Invalid or expired state parameter")
        
        # Check if state is expired
        if datetime.now(timezone.utc) > oauth_state["expires_at"]:
            raise HTTPException(status_code=400, detail="Authorization state expired")
        
        # Get user info for logging
        current_user = await db.users.find_one({"id": user_id})
        if not current_user:
            raise HTTPException(status_code=400, detail="User not found")
        
        # Exchange authorization code for tokens
        token_data = await exchange_code_for_tokens(code)
        
        if not token_data:
            raise HTTPException(status_code=400, detail="Failed to exchange code for tokens")
        
        # Get user profile from Microsoft Graph
        user_profile = await get_user_profile_from_graph(token_data["access_token"])
        
        if not user_profile:
            raise HTTPException(status_code=400, detail="Failed to get user profile")
        
        # Check if account already connected
        existing = await db.connected_accounts.find_one({
            "microsoft_user_id": user_profile["id"],
            "user_id": user_id
        })
        
        if existing:
            # Update existing connection with new tokens
            await db.connected_accounts.update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "access_token": token_data["access_token"],
                    "refresh_token": token_data.get("refresh_token"),
                    "token_expires_at": datetime.now(timezone.utc).replace(
                        second=datetime.now(timezone.utc).second + token_data.get("expires_in", 3600)
                    ),
                    "last_connected": datetime.now(timezone.utc),
                    "is_connected": True
                }}
            )
            
            # Clean up used state
            await db.oauth_states.delete_one({"state": state})
            
            # Return HTML response that closes the popup and communicates with parent
            return HTMLResponse("""
            <html>
                <head><title>Outlook Yeniden Bağlandı</title></head>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                    <h1 style="color: #0078d4;">Hesap Başarıyla Yeniden Bağlandı!</h1>
                    <p>Outlook hesabınız yeniden bağlandı. Bu pencere otomatik olarak kapanacak.</p>
                    <div style="margin-top: 20px;">
                        <div style="display: inline-block; width: 40px; height: 40px; border: 4px solid #0078d4; border-top: 4px solid transparent; border-radius: 50%; animation: spin 1s linear infinite;"></div>
                    </div>
                    <style>
                        @keyframes spin {
                            0% { transform: rotate(0deg); }
                            100% { transform: rotate(360deg); }
                        }
                    </style>
                    <script>
                        if (window.opener) {
                            window.opener.postMessage({
                                type: 'OUTLOOK_AUTH_SUCCESS',
                                message: 'Account reconnected successfully'
                            }, '*');
                        }
                        setTimeout(() => {
                            window.close();
                        }, 3000);
                    </script>
                </body>
            </html>
            """)
        
        # Create new connection
        connection_data = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "microsoft_user_id": user_profile["id"],
            "email": user_profile.get("mail") or user_profile.get("userPrincipalName"),
            "display_name": user_profile.get("displayName", ""),
            "account_type": "outlook",
            "is_connected": True,
            "connected_at": datetime.now(timezone.utc),
            "last_sync": None,
            "access_token": token_data["access_token"],
            "refresh_token": token_data.get("refresh_token"),
            "token_expires_at": datetime.now(timezone.utc).replace(
                second=datetime.now(timezone.utc).second + token_data.get("expires_in", 3600)
            ),
            "scopes": token_data.get("scope", "").split(" ")
        }
        
        await db.connected_accounts.insert_one(connection_data)
        
        # Log the email account connection
        await add_system_log(
            log_type="EMAIL_ACCOUNT_CONNECTED",
            message=f"E-posta hesabı başarıyla bağlandı: {connection_data['email']} - Kullanıcı: {current_user.get('name', current_user.get('email'))}",
            user_email=current_user.get('email'),
            user_name=current_user.get('name'),
            additional_data={
                "connected_email": connection_data['email'],
                "account_type": "outlook",
                "display_name": connection_data['display_name']
            }
        )
        
        # Clean up used state
        await db.oauth_states.delete_one({"state": state})
        
        # Return HTML response that closes the popup and communicates with parent
        return HTMLResponse("""
        <html>
            <head><title>Outlook Bağlandı</title></head>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h1 style="color: #0078d4;">Hesap Başarıyla Bağlandı!</h1>
                <p>Outlook hesabınız başarıyla bağlandı. Bu pencere otomatik olarak kapanacak.</p>
                <div style="margin-top: 20px;">
                    <div style="display: inline-block; width: 40px; height: 40px; border: 4px solid #0078d4; border-top: 4px solid transparent; border-radius: 50%; animation: spin 1s linear infinite;"></div>
                </div>
                <style>
                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                </style>
                <script>
                    if (window.opener) {
                        window.opener.postMessage({
                            type: 'OUTLOOK_AUTH_SUCCESS',
                            message: 'Account connected successfully',
                            account: {
                                id: '""" + connection_data["id"] + """',
                                email: '""" + connection_data["email"] + """',
                                display_name: '""" + connection_data["display_name"] + """'
                            }
                        }, '*');
                    }
                    setTimeout(() => {
                        window.close();
                    }, 3000);
                </script>
            </body>
        </html>
        """)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in OAuth callback: {e}")
        # Return error HTML
        return HTMLResponse(f"""
        <html>
            <head><title>Bağlantı Hatası</title></head>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h1 style="color: #d13438;">Bağlantı Hatası</h1>
                <p>Outlook hesabı bağlanırken bir hata oluştu.</p>
                <p style="color: #666; font-size: 14px;">Hata: {str(e)}</p>
                <script>
                    if (window.opener) {{
                        window.opener.postMessage({{
                            type: 'OUTLOOK_AUTH_ERROR',
                            error: '{str(e)}'
                        }}, '*');
                    }}
                    setTimeout(() => {{
                        window.close();
                    }}, 5000);
                </script>
            </body>
        </html>
        """, status_code=500)

@api_router.get("/outlook/accounts")
async def get_connected_outlook_accounts(current_user: dict = Depends(get_current_user)):
    """Get user's connected Outlook accounts"""
    try:
        accounts = await db.connected_accounts.find({
            "user_id": current_user["id"],
            "is_connected": True
        }).to_list(length=None)
        
        return {"accounts": accounts}
        
    except Exception as e:
        logger.error(f"Error retrieving connected accounts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve accounts")

@api_router.post("/outlook/sync")
async def sync_outlook_emails(
    account_id: str,
    folders: Optional[List[str]] = None,
    current_user: dict = Depends(get_current_user)
):
    """Sync emails from connected Outlook account using stored tokens"""
    try:
        if not outlook_auth_service.is_configured():
            raise HTTPException(
                status_code=503,
                detail="Outlook integration not configured. Please provide Azure credentials."
            )
        
        # Verify account is connected and belongs to user
        account = await db.connected_accounts.find_one({
            "id": account_id,
            "user_id": current_user["id"],
            "is_connected": True
        })
        
        if not account:
            raise HTTPException(
                status_code=404,
                detail="Account not connected or not found"
            )
        
        # Perform sync with token-based authentication
        result = await outlook_email_service.sync_emails_with_token(
            account_id=account_id,
            folder_names=folders
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing Outlook emails: {e}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

@api_router.get("/outlook/emails")
async def get_outlook_emails(
    account_email: Optional[str] = None,
    folder: str = "inbox",
    skip: int = 0,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Get synced Outlook emails from database"""
    try:
        query = {"user_id": current_user["id"], "source": "outlook"}
        
        if account_email:
            query["account_id"] = f"outlook-{account_email}"
        
        if folder != "all":
            query["folder"] = folder.lower()
        
        emails = await db.emails.find(query).sort("date", -1).skip(skip).limit(limit).to_list(length=limit)
        
        # Calculate folder counts
        folder_counts = {}
        if not account_email:
            # Count across all connected accounts
            pipeline = [
                {"$match": {"user_id": current_user["id"], "source": "outlook"}},
                {"$group": {"_id": "$folder", "count": {"$sum": 1}}}
            ]
        else:
            pipeline = [
                {"$match": {"user_id": current_user["id"], "source": "outlook", "account_id": f"outlook-{account_email}"}},
                {"$group": {"_id": "$folder", "count": {"$sum": 1}}}
            ]
        
        counts_result = await db.emails.aggregate(pipeline).to_list(length=None)
        for item in counts_result:
            folder_counts[item["_id"]] = item["count"]
        
        return EmailResponse(emails=emails, folderCounts=folder_counts)
        
    except Exception as e:
        logger.error(f"Error retrieving Outlook emails: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve emails")

@api_router.delete("/outlook/accounts/{account_email}")
async def disconnect_outlook_account(
    account_email: str,
    current_user: dict = Depends(get_current_user)
):
    """Disconnect Outlook account"""
    try:
        result = await db.connected_accounts.update_one(
            {"email": account_email, "user_id": current_user["id"]},
            {"$set": {"is_connected": False}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Account not found")
        
        return {"message": "Account disconnected successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disconnecting account: {e}")
        raise HTTPException(status_code=500, detail="Failed to disconnect account")

# ============== HELPER FUNCTIONS FOR OAUTH2 ==============

async def exchange_code_for_tokens(authorization_code: str) -> Optional[dict]:
    """Exchange authorization code for access and refresh tokens"""
    try:
        token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        
        # Use the same redirect URI as in auth URL generation
        redirect_uri = os.getenv('REDIRECT_URI', 'https://code-state-helper.preview.emergentagent.com/auth/callback')
        
        data = {
            "client_id": os.getenv('AZURE_CLIENT_ID'),
            "client_secret": os.getenv('AZURE_CLIENT_SECRET'),
            "code": authorization_code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
            "scope": "https://graph.microsoft.com/Mail.Read https://graph.microsoft.com/Mail.ReadWrite https://graph.microsoft.com/User.Read offline_access"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)
            
            logger.info(f"Token exchange attempt - Status: {response.status_code}")
            logger.info(f"Token exchange - Request data: {data}")
            
            if response.status_code == 200:
                logger.info("Token exchange successful")
                return response.json()
            else:
                logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
                
                # If redirect_uri error, try alternative URIs
                if "redirect_uri" in response.text.lower():
                    logger.warning("Redirect URI mismatch detected, trying alternatives...")
                    
                    alternative_uris = [
                        "http://localhost:3000/auth/callback",
                        "https://localhost:3000/auth/callback", 
                        "https://code-state-helper.preview.emergentagent.com/auth/callback",
                        "http://localhost:8080/auth/callback"
                    ]
                    
                    for alt_uri in alternative_uris:
                        if alt_uri != data["redirect_uri"]:  # Don't try the same URI again
                            logger.info(f"Trying alternative redirect URI: {alt_uri}")
                            alt_data = data.copy()
                            alt_data["redirect_uri"] = alt_uri
                            
                            alt_response = await client.post(token_url, data=alt_data)
                            logger.info(f"Alternative URI attempt - Status: {alt_response.status_code}")
                            
                            if alt_response.status_code == 200:
                                logger.info(f"Token exchange successful with alternative URI: {alt_uri}")
                                return alt_response.json()
                            else:
                                logger.error(f"Alternative URI failed: {alt_uri} - {alt_response.text}")
                
                return None
                
    except Exception as e:
        logger.error(f"Error exchanging code for tokens: {e}")
        return None

async def get_user_profile_from_graph(access_token: str) -> Optional[dict]:
    """Get user profile from Microsoft Graph API"""
    try:
        graph_url = "https://graph.microsoft.com/v1.0/me"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(graph_url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Graph API call failed: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        return None

async def refresh_access_token(refresh_token: str) -> Optional[dict]:
    """Refresh access token using refresh token"""
    try:
        token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        
        data = {
            "client_id": os.getenv('AZURE_CLIENT_ID'),
            "client_secret": os.getenv('AZURE_CLIENT_SECRET'),
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
            "scope": "https://graph.microsoft.com/Mail.Read https://graph.microsoft.com/Mail.ReadWrite https://graph.microsoft.com/User.Read offline_access"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Token refresh failed: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        return None

async def get_valid_access_token(account_id: str) -> Optional[str]:
    """Get valid access token for account, refresh if needed"""
    try:
        account = await db.connected_accounts.find_one({"id": account_id, "is_connected": True})
        if not account:
            return None
        
        # Check if token is still valid (with 5 minute buffer)
        if datetime.now(timezone.utc) < account["token_expires_at"].replace(minute=account["token_expires_at"].minute - 5):
            return account["access_token"]
        
        # Token expired, try to refresh
        if account.get("refresh_token"):
            new_tokens = await refresh_access_token(account["refresh_token"])
            if new_tokens:
                # Update account with new tokens
                await db.connected_accounts.update_one(
                    {"id": account_id},
                    {"$set": {
                        "access_token": new_tokens["access_token"],
                        "refresh_token": new_tokens.get("refresh_token", account["refresh_token"]),
                        "token_expires_at": datetime.now(timezone.utc).replace(
                            second=datetime.now(timezone.utc).second + new_tokens.get("expires_in", 3600)
                        )
                    }}
                )
                return new_tokens["access_token"]
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting valid access token: {e}")
        return None

# Health check
@api_router.get("/")
async def root():
    return {"message": "PostaDepo API is running", "status": "healthy"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc)}

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