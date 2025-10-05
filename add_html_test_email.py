#!/usr/bin/env python3

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
import uuid
from datetime import datetime, timezone

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DATABASE_NAME = "postadepo"

async def add_html_test_email():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DATABASE_NAME]
    
    # Demo kullanıcısının ID'sini bul
    demo_user = await db.users.find_one({"email": "demo@postadepo.com"})
    if not demo_user:
        print("Demo kullanıcısı bulunamadı!")
        return
    
    user_id = demo_user["id"]
    print(f"Demo kullanıcısı bulundu: {user_id}")
    
    # HTML test e-postası oluştur
    html_content = '''
    <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px;">
        <h2 style="color: #2563eb; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px;">
            🎉 HTML E-posta Test Mesajı
        </h2>
        
        <p style="margin: 16px 0;">
            <strong>Merhaba!</strong> Bu bir <em>HTML formatında</em> test e-postasıdır. 
            Bu e-posta <span style="color: #dc2626; font-weight: bold;">SafeHTMLRenderer</span> 
            bileşeninin çalışıp çalışmadığını test etmek için oluşturulmuştur.
        </p>
        
        <div style="background: #f3f4f6; padding: 16px; border-radius: 8px; margin: 20px 0;">
            <h3 style="margin-top: 0; color: #059669;">✅ Test Özellikleri:</h3>
            <ul style="margin: 8px 0;">
                <li>HTML <strong>kalın yazı</strong> ve <em>eğik yazı</em></li>
                <li>Renkli metinler ve <span style="background: #fef3c7; padding: 2px 6px; border-radius: 4px;">vurgulu alan</span></li>
                <li>Listeler ve yapısal elementler</li>
                <li>CSS stilleri ve responsive tasarım</li>
            </ul>
        </div>
        
        <blockquote style="border-left: 4px solid #3b82f6; margin: 20px 0; padding: 16px; background: #eff6ff; font-style: italic;">
            "Bu alıntı bloğu da HTML rendering testinin bir parçasıdır."
        </blockquote>
        
        <div style="display: flex; gap: 12px; margin: 20px 0; flex-wrap: wrap;">
            <div style="background: #dc2626; color: white; padding: 8px 16px; border-radius: 6px; text-align: center; min-width: 120px;">
                Kırmızı Kart
            </div>
            <div style="background: #059669; color: white; padding: 8px 16px; border-radius: 6px; text-align: center; min-width: 120px;">
                Yeşil Kart  
            </div>
            <div style="background: #d97706; color: white; padding: 8px 16px; border-radius: 6px; text-align: center; min-width: 120px;">
                Turuncu Kart
            </div>
        </div>
        
        <table style="width: 100%; border-collapse: collapse; margin: 20px 0; border: 1px solid #e5e7eb;">
            <thead>
                <tr style="background: #f9fafb;">
                    <th style="padding: 12px; text-align: left; border-bottom: 1px solid #e5e7eb;">Özellik</th>
                    <th style="padding: 12px; text-align: left; border-bottom: 1px solid #e5e7eb;">Durum</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="padding: 8px 12px; border-bottom: 1px solid #f3f4f6;">HTML Rendering</td>
                    <td style="padding: 8px 12px; border-bottom: 1px solid #f3f4f6; color: #059669;">✅ Aktif</td>
                </tr>
                <tr>
                    <td style="padding: 8px 12px; border-bottom: 1px solid #f3f4f6;">CSS Styling</td>
                    <td style="padding: 8px 12px; border-bottom: 1px solid #f3f4f6; color: #059669;">✅ Aktif</td>
                </tr>
                <tr>
                    <td style="padding: 8px 12px;">SafeHTMLRenderer</td>
                    <td style="padding: 8px 12px; color: #059669;">✅ Test Ediliyor</td>
                </tr>
            </tbody>
        </table>
        
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 12px; text-align: center; margin: 24px 0;">
            <h3 style="margin: 0 0 8px 0;">🚀 Gradient Arka Plan Test</h3>
            <p style="margin: 0; opacity: 0.9;">Bu alan CSS gradient ve modern styling özelliklerini test eder.</p>
        </div>
        
        <div style="border: 2px dashed #9ca3af; padding: 16px; border-radius: 8px; text-align: center; margin: 20px 0;">
            <p style="margin: 0; color: #6b7280;">
                🔍 Bu kesikli çerçeve içindeki alan, HTML elementlerinin doğru şekilde render edilip edilmediğini gösterir.
            </p>
        </div>
        
        <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
        
        <p style="color: #6b7280; font-size: 14px; text-align: center; margin: 16px 0;">
            Bu e-posta PostaDepo SafeHTMLRenderer bileşeni tarafından güvenli bir şekilde render edilmektedir.<br>
            <small>Test Tarihi: ${new Date().toLocaleString('tr-TR')}</small>
        </p>
    </div>
    '''
    
    # Test e-postası verisi
    test_email = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "folder": "inbox",
        "sender": "test@postadepo.com (HTML Test)",
        "recipient": "demo@postadepo.com", 
        "subject": "🧪 HTML Render Test - SafeHTMLRenderer Bileşeni",
        "content": html_content,
        "content_type": "html",  # ÖNEMLİ: HTML olarak işaretle
        "preview": "HTML test e-postası - SafeHTMLRenderer bileşeninin çalışıp çalışmadığını test eder...",
        "date": datetime.now(timezone.utc).isoformat(),
        "read": False,
        "important": True,
        "size": len(html_content.encode('utf-8')) + 500,  # Yaklaşık boyut
        "account_id": "test-html-account",
        "thread_id": str(uuid.uuid4()),
        "attachments": []
    }
    
    # E-postayı veritabanına ekle
    result = await db.emails.insert_one(test_email)
    print(f"HTML test e-postası eklendi: {result.inserted_id}")
    print(f"E-posta ID: {test_email['id']}")
    print(f"Content-Type: {test_email['content_type']}")
    
    client.close()
    print("✅ HTML test e-postası başarıyla oluşturuldu!")

if __name__ == "__main__":
    asyncio.run(add_html_test_email())