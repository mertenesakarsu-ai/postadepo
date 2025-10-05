#!/usr/bin/env python3
import requests
import json
import sys

# Demo kullanıcı giriş
login_response = requests.post(
    "http://localhost:8001/api/auth/login",
    json={"email": "demo@postadepo.com", "password": "demo123"}
)

if login_response.status_code != 200:
    print(f"Login failed: {login_response.text}")
    sys.exit(1)

token = login_response.json()["token"]
user_id = login_response.json()["user"]["id"]
headers = {"Authorization": f"Bearer {token}"}

print(f"Logged in as demo user, ID: {user_id}")

# HTML e-posta content örneği
html_content = '''
<div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2c5282;">HTML E-posta Test Başlığı</h2>
    <p>Bu bir <strong>HTML formatındaki</strong> test e-postasıdır.</p>
    <ul>
        <li>DOMPurify ile sanitize edilmiştir</li>
        <li>Sandboxed iframe içinde render edilmektedir</li>
        <li>Resimler otomatik yüklenebilir</li>
    </ul>
    <img src="https://picsum.photos/400/200?random=1" alt="Test Resimi" style="max-width: 100%; border-radius: 8px; margin: 16px 0;">
    <hr style="margin: 20px 0; border: none; border-top: 1px solid #eee;">
    <p style="color: #666; font-size: 12px;">Bu e-posta test amaçlıdır.</p>
</div>
'''

# Manuel HTML e-posta ekle (MongoDB'ye direkt)
import pymongo
import uuid
from datetime import datetime, timezone

# MongoDB bağlantısı
client = pymongo.MongoClient("mongodb://localhost:27017")
db = client.postadepo

# HTML e-posta dökümanı
email_doc = {
    "id": str(uuid.uuid4()),
    "user_id": user_id,
    "folder": "inbox",
    "sender": "test@example.com (HTML Test)",
    "recipient": "demo@postadepo.com",
    "subject": "HTML E-posta Test - Resimli İçerik",
    "content": html_content,
    "content_type": "html",  # Burada HTML!
    "preview": "Bu bir HTML formatındaki test e-postasıdır. DOMPurify ile sanitize...",
    "date": datetime.now(timezone.utc).isoformat(),
    "read": False,
    "important": True,
    "size": len(html_content),
    "account_id": "test-account",
    "thread_id": str(uuid.uuid4()),
    "attachments": []
}

# E-postayı ekle
result = db.emails.insert_one(email_doc)
print(f"HTML e-posta eklendi: {result.inserted_id}")

# 2. HTML e-posta (daha basit)
simple_html = '''
<div style="font-family: Arial, sans-serif; color: #333;">
    <h3>Basit HTML E-posta</h3>
    <p>Bu da başka bir <em>HTML e-posta</em> örneğidir.</p>
    <blockquote style="border-left: 4px solid #e5e7eb; padding-left: 16px; color: #6b7280;">
        "DOMPurify ile güvenli HTML rendering testi"
    </blockquote>
    <p><a href="#" style="color: #3b82f6;">Test linki</a></p>
</div>
'''

email_doc2 = {
    "id": str(uuid.uuid4()),
    "user_id": user_id,
    "folder": "inbox",
    "sender": "developer@postadepo.com (Geliştirici)",
    "recipient": "demo@postadepo.com",
    "subject": "SafeHTMLRenderer Testi",
    "content": simple_html,
    "content_type": "html",
    "preview": "Bu da başka bir HTML e-posta örneğidir...",
    "date": datetime.now(timezone.utc).isoformat(),
    "read": False,
    "important": False,
    "size": len(simple_html),
    "account_id": "dev-account",
    "thread_id": str(uuid.uuid4()),
    "attachments": []
}

result2 = db.emails.insert_one(email_doc2)
print(f"2. HTML e-posta eklendi: {result2.inserted_id}")

print("HTML e-postalar başarıyla eklendi!")