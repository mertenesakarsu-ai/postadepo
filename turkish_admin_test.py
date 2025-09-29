#!/usr/bin/env python3
"""
TÜRKÇE BACKEND TEST - Admin Panel ve Kullanıcı Sistemi
PostaDepo Admin Panel ve Kullanıcı Yönetimi Kapsamlı Test

TEST SCOPE:
1. Admin Girişi: admin@postadepo.com / admindepo*
2. Admin Panel API'leri: users, pending-users, approve-user, reject-user
3. reCAPTCHA API'si: verify-recaptcha
4. Kullanıcı Kaydı: Yeni kullanıcı kaydı ve whitelist sistemi
5. Outlook entegrasyonu: outlook/status endpoint'i
"""

import requests
import sys
import json
import random
from datetime import datetime

class TurkishAdminPanelTester:
    def __init__(self, base_url="https://login-redirect-fix-6.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.admin_token = None
        self.admin_user = None
        self.regular_token = None
        self.regular_user = None
        self.test_user_id = None
        self.test_user_email = None
        self.tests_run = 0
        self.tests_passed = 0
        self.critical_failures = []

    def log_test(self, name, success, details=""):
        """Test sonucunu logla"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
            if details:
                print(f"   {details}")
        else:
            print(f"❌ {name}")
            if details:
                print(f"   {details}")
            self.critical_failures.append(name)

    def make_request(self, method, endpoint, data=None, token=None, expected_status=200):
        """API isteği yap"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            
            success = response.status_code == expected_status
            response_data = {}
            
            try:
                response_data = response.json() if response.text else {}
            except:
                pass
            
            return success, response.status_code, response_data, response.text
            
        except Exception as e:
            return False, 0, {}, str(e)

    def test_admin_login(self):
        """1. Admin Girişi Testi - admin@postadepo.com / admindepo*"""
        print("\n🔐 1. ADMİN GİRİŞ TESTİ")
        print("=" * 50)
        
        success, status, data, text = self.make_request(
            'POST', 
            'auth/login',
            data={"email": "admin@postadepo.com", "password": "admindepo*"}
        )
        
        if success and 'token' in data and 'user' in data:
            self.admin_token = data['token']
            self.admin_user = data['user']
            user_type = self.admin_user.get('user_type', 'unknown')
            
            # KRİTİK KONTROL: Admin user_type='admin' döndürüyor mu?
            if user_type == 'admin':
                self.log_test(
                    "Admin kullanıcısı giriş başarılı", 
                    True, 
                    f"Email: {self.admin_user.get('email')}, User Type: {user_type}"
                )
                return True
            else:
                self.log_test(
                    "Admin kullanıcısı user_type hatası", 
                    False, 
                    f"Beklenen: 'admin', Alınan: '{user_type}'"
                )
                return False
        else:
            self.log_test(
                "Admin kullanıcısı giriş başarısız", 
                False, 
                f"Status: {status}, Response: {text[:200]}"
            )
            return False

    def test_admin_panel_apis(self):
        """2. Admin Panel API'leri Testi"""
        print("\n👥 2. ADMİN PANEL API'LERİ TESTİ")
        print("=" * 50)
        
        if not self.admin_token:
            self.log_test("Admin Panel API'leri", False, "Admin token bulunamadı")
            return False
        
        all_success = True
        
        # 2.1 GET /api/admin/users (tüm kullanıcı listesi)
        success, status, data, text = self.make_request(
            'GET', 
            'admin/users',
            token=self.admin_token
        )
        
        if success and 'users' in data:
            users = data['users']
            self.log_test(
                "GET /api/admin/users", 
                True, 
                f"Toplam {len(users)} kullanıcı listelendi"
            )
            
            # Storage bilgilerini kontrol et
            storage_info_count = 0
            for user in users:
                if 'storage_info' in user:
                    storage_info_count += 1
                    storage = user['storage_info']
                    print(f"   📊 {user.get('email', 'Unknown')}: {storage.get('totalEmails', 0)} e-posta, {storage.get('totalSize', 0)} bytes")
            
            if storage_info_count > 0:
                self.log_test("Storage bilgileri mevcut", True, f"{storage_info_count}/{len(users)} kullanıcıda storage bilgisi")
            else:
                self.log_test("Storage bilgileri eksik", False, "Hiçbir kullanıcıda storage bilgisi yok")
                all_success = False
        else:
            self.log_test("GET /api/admin/users", False, f"Status: {status}, Response: {text[:200]}")
            all_success = False
        
        # 2.2 GET /api/admin/pending-users (onay bekleyen kullanıcılar)
        success, status, data, text = self.make_request(
            'GET', 
            'admin/pending-users',
            token=self.admin_token
        )
        
        if success and 'pending_users' in data:
            pending_users = data['pending_users']
            self.log_test(
                "GET /api/admin/pending-users", 
                True, 
                f"{len(pending_users)} onay bekleyen kullanıcı"
            )
        else:
            self.log_test("GET /api/admin/pending-users", False, f"Status: {status}")
            all_success = False
        
        return all_success

    def test_user_registration_whitelist(self):
        """4. Kullanıcı Kaydı ve Whitelist Sistemi Testi"""
        print("\n📝 4. KULLANICI KAYDI VE WHİTELİST SİSTEMİ TESTİ")
        print("=" * 50)
        
        # Test kullanıcısı oluştur
        test_email = f"testkullanici{random.randint(1000, 9999)}@test.com"
        
        success, status, data, text = self.make_request(
            'POST', 
            'auth/register',
            data={
                "name": "Test Kullanıcısı",
                "email": test_email,
                "password": "test123456"
            }
        )
        
        if success and 'user_id' in data:
            self.test_user_id = data['user_id']
            self.test_user_email = test_email
            approved = data.get('approved', True)
            
            # KRİTİK KONTROL: Yeni kullanıcılar approved=false ile oluşuyor mu?
            if not approved:
                self.log_test(
                    "Yeni kullanıcı approved=false ile oluşturuldu", 
                    True, 
                    f"Email: {test_email}, User ID: {self.test_user_id}"
                )
                
                # Onaylanmamış kullanıcı giriş denemesi
                login_success, login_status, login_data, login_text = self.make_request(
                    'POST', 
                    'auth/login',
                    data={"email": test_email, "password": "test123456"},
                    expected_status=403
                )
                
                if login_success:
                    self.log_test("Onaylanmamış kullanıcı giriş engellendi", True, "403 Forbidden alındı")
                    return True
                else:
                    self.log_test("Onaylanmamış kullanıcı giriş engellenmedi", False, f"Status: {login_status}")
                    return False
            else:
                self.log_test("Yeni kullanıcı otomatik onaylandı", False, "Whitelist sistemi çalışmıyor")
                return False
        else:
            self.log_test("Kullanıcı kaydı başarısız", False, f"Status: {status}, Response: {text[:200]}")
            return False

    def test_admin_user_approval(self):
        """Admin kullanıcı onaylama testi"""
        print("\n✅ ADMİN KULLANICI ONAYLAMA TESTİ")
        print("=" * 30)
        
        if not self.admin_token or not self.test_user_id:
            self.log_test("Admin onaylama testi", False, "Admin token veya test kullanıcısı bulunamadı")
            return False
        
        # 2.3 POST /api/admin/approve-user/{user_id} (kullanıcı onaylama)
        success, status, data, text = self.make_request(
            'POST', 
            f'admin/approve-user/{self.test_user_id}',
            token=self.admin_token
        )
        
        if success:
            self.log_test("POST /api/admin/approve-user", True, f"Kullanıcı {self.test_user_id} onaylandı")
            
            # Onaylanan kullanıcı giriş denemesi
            login_success, login_status, login_data, login_text = self.make_request(
                'POST', 
                'auth/login',
                data={"email": self.test_user_email, "password": "test123456"}
            )
            
            if login_success and 'token' in login_data:
                self.regular_token = login_data['token']
                self.regular_user = login_data['user']
                self.log_test("Onaylanan kullanıcı başarılı giriş", True, f"Email: {self.test_user_email}")
                return True
            else:
                self.log_test("Onaylanan kullanıcı giriş başarısız", False, f"Status: {login_status}")
                return False
        else:
            self.log_test("POST /api/admin/approve-user", False, f"Status: {status}")
            return False

    def test_admin_user_rejection(self):
        """Admin kullanıcı reddetme testi"""
        print("\n❌ ADMİN KULLANICI REDDETME TESTİ")
        print("=" * 30)
        
        if not self.admin_token:
            self.log_test("Admin reddetme testi", False, "Admin token bulunamadı")
            return False
        
        # Yeni test kullanıcısı oluştur
        reject_email = f"rejectuser{random.randint(1000, 9999)}@test.com"
        
        success, status, data, text = self.make_request(
            'POST', 
            'auth/register',
            data={
                "name": "Reddedilecek Kullanıcı",
                "email": reject_email,
                "password": "reject123"
            }
        )
        
        if success and 'user_id' in data:
            reject_user_id = data['user_id']
            
            # 2.4 POST /api/admin/reject-user/{user_id} (kullanıcı reddetme)
            reject_success, reject_status, reject_data, reject_text = self.make_request(
                'POST', 
                f'admin/reject-user/{reject_user_id}',
                token=self.admin_token
            )
            
            if reject_success:
                self.log_test("POST /api/admin/reject-user", True, f"Kullanıcı {reject_user_id} reddedildi")
                return True
            else:
                self.log_test("POST /api/admin/reject-user", False, f"Status: {reject_status}")
                return False
        else:
            self.log_test("Reddetme için kullanıcı oluşturulamadı", False, f"Status: {status}")
            return False

    def test_non_admin_access_restriction(self):
        """Normal kullanıcıların admin endpoint'lerine erişim testi"""
        print("\n🚫 NORMAL KULLANICI ADMİN ERİŞİM KISITLAMA TESTİ")
        print("=" * 50)
        
        if not self.regular_token:
            self.log_test("Normal kullanıcı erişim testi", False, "Normal kullanıcı token'ı bulunamadı")
            return False
        
        # KRİTİK KONTROL: Normal kullanıcılar admin endpoint'lerine 403 almalı
        success, status, data, text = self.make_request(
            'GET', 
            'admin/users',
            token=self.regular_token,
            expected_status=403
        )
        
        if success:
            self.log_test("Normal kullanıcı admin erişimi engellendi", True, "403 Forbidden alındı")
            return True
        else:
            self.log_test("Normal kullanıcı admin erişimi engellenmedi", False, f"Status: {status} (beklenen: 403)")
            return False

    def test_recaptcha_api(self):
        """3. reCAPTCHA API Testi"""
        print("\n🤖 3. reCAPTCHA API TESTİ")
        print("=" * 50)
        
        # Boş token testi (400 bekleniyor)
        success, status, data, text = self.make_request(
            'POST', 
            'verify-recaptcha',
            data={"recaptcha_token": ""},
            expected_status=400
        )
        
        if success:
            self.log_test("reCAPTCHA boş token reddi", True, "400 Bad Request alındı")
        else:
            self.log_test("reCAPTCHA boş token reddi", False, f"Status: {status} (beklenen: 400)")
        
        # Sahte token testi (200 ama success=false bekleniyor)
        success, status, data, text = self.make_request(
            'POST', 
            'verify-recaptcha',
            data={"recaptcha_token": "fake-test-token-for-testing"}
        )
        
        if success and not data.get('success', True):
            self.log_test("reCAPTCHA sahte token reddi", True, "success=false döndü")
            return True
        elif success and data.get('success', False):
            self.log_test("reCAPTCHA sahte token kabul edildi", False, "success=true döndü (beklenmeyen)")
            return False
        else:
            self.log_test("reCAPTCHA API hatası", False, f"Status: {status}, Response: {text[:200]}")
            return False

    def test_outlook_integration_status(self):
        """5. Outlook Entegrasyonu Status Testi"""
        print("\n📧 5. OUTLOOK ENTEGRASYON STATUS TESTİ")
        print("=" * 50)
        
        # Demo kullanıcısı ile giriş yap (outlook endpoint'leri için)
        demo_success, demo_status, demo_data, demo_text = self.make_request(
            'POST', 
            'auth/login',
            data={"email": "demo@postadepo.com", "password": "demo123"}
        )
        
        if not demo_success or 'token' not in demo_data:
            self.log_test("Demo kullanıcı girişi", False, f"Status: {demo_status}")
            return False
        
        demo_token = demo_data['token']
        
        # KRİTİK KONTROL: Outlook API'si hazır mı?
        success, status, data, text = self.make_request(
            'GET', 
            'outlook/status',
            token=demo_token
        )
        
        if success:
            graph_available = data.get('graph_sdk_available', False)
            credentials_configured = data.get('credentials_configured', False)
            message = data.get('message', 'No message')
            
            self.log_test(
                "GET /api/outlook/status", 
                True, 
                f"Graph SDK: {graph_available}, Credentials: {credentials_configured}"
            )
            
            print(f"   📋 Status mesajı: {message}")
            
            if graph_available and credentials_configured:
                self.log_test("Outlook entegrasyonu hazır", True, "Tüm gereksinimler karşılandı")
                return True
            else:
                self.log_test("Outlook entegrasyonu eksik", False, f"Graph SDK: {graph_available}, Credentials: {credentials_configured}")
                return False
        else:
            self.log_test("GET /api/outlook/status", False, f"Status: {status}, Response: {text[:200]}")
            return False

    def test_admin_create_endpoint(self):
        """Admin oluşturma endpoint'i testi"""
        print("\n👑 ADMİN OLUŞTURMA ENDPOİNT TESTİ")
        print("=" * 30)
        
        success, status, data, text = self.make_request(
            'POST', 
            'admin/create-admin'
        )
        
        if success:
            message = data.get('message', '')
            if 'zaten mevcut' in message:
                self.log_test("Admin kullanıcısı zaten mevcut", True, message)
            else:
                self.log_test("Admin kullanıcısı oluşturuldu", True, message)
            return True
        else:
            self.log_test("Admin oluşturma endpoint'i", False, f"Status: {status}")
            return False

    def run_comprehensive_test(self):
        """Kapsamlı test süitini çalıştır"""
        print("🇹🇷 POSTADEPO ADMİN PANEL VE KULLANICI SİSTEMİ KAPSAMLI TEST")
        print("=" * 70)
        print("TEST SCOPE:")
        print("1. Admin Girişi: admin@postadepo.com / admindepo*")
        print("2. Admin Panel API'leri: users, pending-users, approve-user, reject-user")
        print("3. reCAPTCHA API'si: verify-recaptcha")
        print("4. Kullanıcı Kaydı: Yeni kullanıcı kaydı ve whitelist sistemi")
        print("5. Outlook entegrasyonu: outlook/status endpoint'i")
        print("=" * 70)
        
        # Test sırası - kritik testler önce
        test_results = []
        
        # 1. Admin oluşturma endpoint'i (emin olmak için)
        test_results.append(("Admin Oluşturma Endpoint", self.test_admin_create_endpoint()))
        
        # 2. Admin girişi (en kritik)
        test_results.append(("Admin Girişi", self.test_admin_login()))
        
        # 3. Admin panel API'leri
        test_results.append(("Admin Panel API'leri", self.test_admin_panel_apis()))
        
        # 4. reCAPTCHA API
        test_results.append(("reCAPTCHA API", self.test_recaptcha_api()))
        
        # 5. Kullanıcı kaydı ve whitelist
        test_results.append(("Kullanıcı Kaydı ve Whitelist", self.test_user_registration_whitelist()))
        
        # 6. Admin kullanıcı onaylama
        test_results.append(("Admin Kullanıcı Onaylama", self.test_admin_user_approval()))
        
        # 7. Admin kullanıcı reddetme
        test_results.append(("Admin Kullanıcı Reddetme", self.test_admin_user_rejection()))
        
        # 8. Normal kullanıcı erişim kısıtlaması
        test_results.append(("Normal Kullanıcı Erişim Kısıtlaması", self.test_non_admin_access_restriction()))
        
        # 9. Outlook entegrasyonu
        test_results.append(("Outlook Entegrasyon Status", self.test_outlook_integration_status()))
        
        # Sonuçları özetle
        self.print_final_results(test_results)
        
        return len(self.critical_failures) == 0

    def print_final_results(self, test_results):
        """Final sonuçları yazdır"""
        print("\n" + "=" * 70)
        print("🏁 TÜRKÇE ADMİN PANEL TEST SONUÇLARI")
        print("=" * 70)
        
        print("\n📊 TEST SONUÇLARI:")
        for test_name, result in test_results:
            status = "✅ BAŞARILI" if result else "❌ BAŞARISIZ"
            print(f"   {status}: {test_name}")
        
        print(f"\n📈 GENEL İSTATİSTİKLER:")
        print(f"   Toplam Test: {self.tests_run}")
        print(f"   Başarılı: {self.tests_passed}")
        print(f"   Başarısız: {self.tests_run - self.tests_passed}")
        print(f"   Başarı Oranı: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.critical_failures:
            print(f"\n🚨 KRİTİK HATALAR:")
            for failure in self.critical_failures:
                print(f"   ❌ {failure}")
        
        print("\n🎯 KRİTİK KONTROLLER:")
        
        # Admin user_type kontrolü
        if self.admin_user and self.admin_user.get('user_type') == 'admin':
            print("   ✅ Admin user_type='admin' döndürüyor")
        else:
            print("   ❌ Admin user_type='admin' döndürmüyor")
        
        # Whitelist sistemi kontrolü
        if self.test_user_id:
            print("   ✅ Yeni kullanıcılar approved=false ile oluşuyor")
        else:
            print("   ❌ Whitelist sistemi çalışmıyor")
        
        # Admin panel erişim kontrolü
        admin_apis_working = "Admin Panel API'leri" in [name for name, result in test_results if result]
        if admin_apis_working:
            print("   ✅ Admin panel API'leri çalışıyor")
        else:
            print("   ❌ Admin panel API'leri çalışmıyor")
        
        # reCAPTCHA kontrolü
        recaptcha_working = "reCAPTCHA API" in [name for name, result in test_results if result]
        if recaptcha_working:
            print("   ✅ reCAPTCHA doğrulaması çalışıyor")
        else:
            print("   ❌ reCAPTCHA doğrulaması çalışmıyor")
        
        # Outlook API kontrolü
        outlook_working = "Outlook Entegrasyon Status" in [name for name, result in test_results if result]
        if outlook_working:
            print("   ✅ Outlook API'si hazır")
        else:
            print("   ❌ Outlook API'si hazır değil")
        
        print("\n" + "=" * 70)
        
        if len(self.critical_failures) == 0:
            print("🎉 TÜM KRİTİK TESTLER BAŞARILI - ADMİN PANEL SİSTEMİ HAZIR!")
        else:
            print("⚠️  BAZI KRİTİK TESTLER BAŞARISIZ - DÜZELTME GEREKLİ!")

def main():
    """Ana test fonksiyonu"""
    tester = TurkishAdminPanelTester()
    success = tester.run_comprehensive_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())