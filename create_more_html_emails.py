#!/usr/bin/env python3

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
import uuid
from datetime import datetime, timezone
import random

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL')
DATABASE_NAME = os.environ.get('DB_NAME', 'postadepo')

async def create_html_emails():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DATABASE_NAME]
    
    # Demo kullanıcısını bul
    demo_user = await db.users.find_one({"email": "demo@postadepo.com"})
    if not demo_user:
        print("Demo kullanıcısı bulunamadı!")
        return
    
    user_id = demo_user["id"]
    
    # HTML e-posta şablonları
    html_templates = [
        {
            "subject": "📧 Pazarlama Kampanyası - Özel İndirim Fırsatı",
            "sender": "marketing@company.com (Pazarlama Ekibi)",
            "content": '''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <header style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1 style="margin: 0; font-size: 28px;">🎉 ÖZEL İNDİRİM FIRSATI</h1>
                    <p style="margin: 10px 0 0 0; opacity: 0.9;">Sadece bugün için %50'ye varan indirim!</p>
                </header>
                
                <main style="padding: 30px; background: #f8fafc; border-radius: 0 0 10px 10px;">
                    <p style="font-size: 16px; color: #334155; line-height: 1.6;">
                        Sevgili müşterimiz, <strong>bugün özel bir günümüz var!</strong> Tüm ürünlerimizde 
                        <span style="background: #fef3c7; color: #92400e; padding: 2px 8px; border-radius: 4px; font-weight: bold;">%50'ye varan indirimler</span> 
                        sizi bekliyor.
                    </p>
                    
                    <div style="background: white; padding: 25px; margin: 20px 0; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <h3 style="color: #1e40af; margin-top: 0;">🏷️ İndirimli Ürünler:</h3>
                        <ul style="list-style: none; padding: 0;">
                            <li style="padding: 8px 0; border-bottom: 1px solid #e2e8f0;">
                                <strong>Laptop Modelleri</strong> - <span style="color: #dc2626;">%45 İndirim</span>
                            </li>
                            <li style="padding: 8px 0; border-bottom: 1px solid #e2e8f0;">
                                <strong>Akıllı Telefonlar</strong> - <span style="color: #dc2626;">%40 İndirim</span>
                            </li>
                            <li style="padding: 8px 0;">
                                <strong>Tablet ve Aksesuarlar</strong> - <span style="color: #dc2626;">%50 İndirim</span>
                            </li>
                        </ul>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="#" style="background: linear-gradient(135deg, #f59e0b, #d97706); color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-weight: bold; display: inline-block; box-shadow: 0 4px 15px rgba(245, 158, 11, 0.3);">
                            🛒 Alışverişe Başla
                        </a>
                    </div>
                </main>
            </div>
            '''
        },
        {
            "subject": "📊 Haftalık Rapor - Sistem Performansı",
            "sender": "system@company.com (Sistem Yönetimi)",
            "content": '''
            <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 700px; margin: 0 auto; background: #ffffff;">
                <div style="background: #1e293b; color: white; padding: 25px; text-align: center;">
                    <h1 style="margin: 0; font-size: 24px;">📊 HAFTALIK SİSTEM RAPORU</h1>
                    <p style="margin: 8px 0 0 0; color: #cbd5e1;">05-12 Ekim 2025 Dönemi</p>
                </div>
                
                <div style="padding: 30px;">
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin: 20px 0;">
                        <div style="background: #ecfdf5; padding: 20px; border-radius: 8px; border-left: 4px solid #10b981;">
                            <h3 style="margin: 0 0 10px 0; color: #059669;">✅ Uptime</h3>
                            <div style="font-size: 24px; font-weight: bold; color: #1f2937;">99.97%</div>
                        </div>
                        <div style="background: #eff6ff; padding: 20px; border-radius: 8px; border-left: 4px solid #3b82f6;">
                            <h3 style="margin: 0 0 10px 0; color: #2563eb;">🚀 Performans</h3>
                            <div style="font-size: 24px; font-weight: bold; color: #1f2937;">Mükemmel</div>
                        </div>
                    </div>
                    
                    <blockquote style="background: #fefce8; border-left: 4px solid #eab308; margin: 20px 0; padding: 15px; border-radius: 0 4px 4px 0;">
                        <strong>Öne Çıkan Başarı:</strong> Bu hafta hiçbir kritik hata yaşanmadı ve sistem performansı %15 iyileşti.
                    </blockquote>
                    
                    <table style="width: 100%; border-collapse: collapse; margin: 20px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                        <thead>
                            <tr style="background: #f1f5f9;">
                                <th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0; color: #475569;">Metrik</th>
                                <th style="padding: 12px; text-align: center; border-bottom: 2px solid #e2e8f0; color: #475569;">Bu Hafta</th>
                                <th style="padding: 12px; text-align: center; border-bottom: 2px solid #e2e8f0; color: #475569;">Geçen Hafta</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td style="padding: 10px 12px; border-bottom: 1px solid #f1f5f9;">Kullanıcı Sayısı</td>
                                <td style="padding: 10px 12px; text-align: center; border-bottom: 1px solid #f1f5f9; color: #059669; font-weight: bold;">1,247</td>
                                <td style="padding: 10px 12px; text-align: center; border-bottom: 1px solid #f1f5f9;">1,198</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px 12px; border-bottom: 1px solid #f1f5f9;">Ortalama Yanıt Süresi</td>
                                <td style="padding: 10px 12px; text-align: center; border-bottom: 1px solid #f1f5f9; color: #059669; font-weight: bold;">245ms</td>
                                <td style="padding: 10px 12px; text-align: center; border-bottom: 1px solid #f1f5f9;">289ms</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px 12px;">Hata Oranı</td>
                                <td style="padding: 10px 12px; text-align: center; color: #059669; font-weight: bold;">0.03%</td>
                                <td style="padding: 10px 12px; text-align: center;">0.08%</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
            '''
        },
        {
            "subject": "🎯 Proje Durumu Güncellenmesi",
            "sender": "project@company.com (Proje Yönetimi)",
            "content": '''
            <div style="font-family: Arial, sans-serif; max-width: 650px; margin: 0 auto;">
                <div style="background: linear-gradient(45deg, #f093fb 0%, #f5576c 100%); color: white; padding: 20px; border-radius: 15px 15px 0 0;">
                    <h2 style="margin: 0; font-size: 22px;">🎯 PROJE DURUM RAPORU</h2>
                    <p style="margin: 5px 0 0 0; opacity: 0.9;">Alpha v2.1 Geliştirme Süreci</p>
                </div>
                
                <div style="padding: 25px; background: #fafafa;">
                    <p style="color: #374151; line-height: 1.6; margin-bottom: 20px;">
                        Merhaba ekip, <strong>Alpha v2.1</strong> projesinde kaydettiğimiz ilerlemelerden 
                        sizleri haberdar etmek istiyorum.
                    </p>
                    
                    <div style="background: white; padding: 20px; border-radius: 10px; margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <h3 style="color: #7c3aed; margin-top: 0;">📈 İlerleme Durumu</h3>
                        
                        <div style="margin: 15px 0;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                <span style="font-weight: bold;">Backend API</span>
                                <span style="color: #059669;">85%</span>
                            </div>
                            <div style="background: #e5e7eb; height: 8px; border-radius: 4px;">
                                <div style="background: #10b981; width: 85%; height: 100%; border-radius: 4px;"></div>
                            </div>
                        </div>
                        
                        <div style="margin: 15px 0;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                <span style="font-weight: bold;">Frontend UI</span>
                                <span style="color: #f59e0b;">70%</span>
                            </div>
                            <div style="background: #e5e7eb; height: 8px; border-radius: 4px;">
                                <div style="background: #f59e0b; width: 70%; height: 100%; border-radius: 4px;"></div>
                            </div>
                        </div>
                        
                        <div style="margin: 15px 0;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                <span style="font-weight: bold;">Test Coverage</span>
                                <span style="color: #dc2626;">45%</span>
                            </div>
                            <div style="background: #e5e7eb; height: 8px; border-radius: 4px;">
                                <div style="background: #dc2626; width: 45%; height: 100%; border-radius: 4px;"></div>
                            </div>
                        </div>
                    </div>
                    
                    <div style="background: #dbeafe; border: 1px solid #93c5fd; border-radius: 8px; padding: 15px; margin: 20px 0;">
                        <h4 style="margin: 0 0 10px 0; color: #1d4ed8;">🚧 Bu Haftanın Hedefleri</h4>
                        <ul style="margin: 0; padding-left: 20px; color: #1e40af;">
                            <li>Authentication sistemi tamamlanacak</li>
                            <li>Dashboard UI component'leri bitecek</li>
                            <li>Unit test coverage %70'e çıkarılacak</li>
                        </ul>
                    </div>
                </div>
            </div>
            '''
        }
    ]
    
    # HTML e-postaları oluştur
    created_count = 0
    for template in html_templates:
        email = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "folder": "inbox",
            "sender": template["sender"],
            "recipient": "demo@postadepo.com",
            "subject": template["subject"],
            "content": template["content"],
            "content_type": "html",  # HTML olarak işaretle
            "preview": template["subject"][:100] + "...",
            "date": datetime.now(timezone.utc).isoformat(),
            "read": False,
            "important": random.choice([True, False]),
            "size": len(template["content"].encode('utf-8')) + random.randint(200, 800),
            "account_id": f"html-demo-{random.randint(1, 5)}",
            "thread_id": str(uuid.uuid4()),
            "attachments": []
        }
        
        result = await db.emails.insert_one(email)
        created_count += 1
        print(f"✅ HTML e-posta oluşturuldu: {template['subject'][:50]}...")
    
    client.close()
    print(f"\n🎉 {created_count} HTML e-posta başarıyla oluşturuldu!")

if __name__ == "__main__":
    asyncio.run(create_html_emails())