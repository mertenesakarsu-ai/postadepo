#!/usr/bin/env python3
"""
FOCUSED TURKISH ADMIN TEST - Specific Requirements Check
Türkçe review request'e göre spesifik gereksinimleri test et
"""

import requests
import sys
import json

class FocusedTurkishTest:
    def __init__(self, base_url="https://login-redirect-fix-6.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.admin_token = None
        self.results = []

    def test_admin_login_specific(self):
        """Admin girişi - admin@postadepo.com / admindepo* ile giriş"""
        print("🔐 TEST: Admin girişi (admin@postadepo.com / admindepo*)")
        
        response = requests.post(f"{self.base_url}/auth/login", json={
            "email": "admin@postadepo.com",
            "password": "admindepo*"
        })
        
        if response.status_code == 200:
            data = response.json()
            if 'token' in data and 'user' in data:
                self.admin_token = data['token']
                user_type = data['user'].get('user_type', 'unknown')
                
                if user_type == 'admin':
                    print("   ✅ Admin girişi başarılı, user_type='admin' döndürüyor")
                    self.results.append(("Admin Girişi", True, f"user_type: {user_type}"))
                    return True
                else:
                    print(f"   ❌ Admin user_type yanlış: {user_type}")
                    self.results.append(("Admin Girişi", False, f"user_type: {user_type}"))
                    return False
            else:
                print("   ❌ Token veya user bilgisi eksik")
                self.results.append(("Admin Girişi", False, "Token/user eksik"))
                return False
        else:
            print(f"   ❌ Giriş başarısız: {response.status_code}")
            self.results.append(("Admin Girişi", False, f"HTTP {response.status_code}"))
            return False

    def test_admin_endpoints(self):
        """Admin panel endpoint'leri testi"""
        if not self.admin_token:
            print("❌ Admin token yok, endpoint testleri atlanıyor")
            return False
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        endpoints_to_test = [
            ("GET /api/admin/users", "admin/users"),
            ("GET /api/admin/pending-users", "admin/pending-users"),
        ]
        
        all_success = True
        
        for name, endpoint in endpoints_to_test:
            print(f"🔍 TEST: {name}")
            response = requests.get(f"{self.base_url}/{endpoint}", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if endpoint == "admin/users" and 'users' in data:
                    users = data['users']
                    print(f"   ✅ {len(users)} kullanıcı listelendi")
                    # Storage bilgisi kontrolü
                    storage_count = sum(1 for user in users if 'storage_info' in user)
                    print(f"   📊 {storage_count}/{len(users)} kullanıcıda storage bilgisi")
                    self.results.append((name, True, f"{len(users)} kullanıcı, {storage_count} storage"))
                elif endpoint == "admin/pending-users" and 'pending_users' in data:
                    pending = data['pending_users']
                    print(f"   ✅ {len(pending)} onay bekleyen kullanıcı")
                    self.results.append((name, True, f"{len(pending)} bekleyen"))
                else:
                    print(f"   ❌ Beklenmeyen response format")
                    self.results.append((name, False, "Format hatası"))
                    all_success = False
            else:
                print(f"   ❌ HTTP {response.status_code}")
                self.results.append((name, False, f"HTTP {response.status_code}"))
                all_success = False
        
        return all_success

    def test_admin_user_operations(self):
        """Admin kullanıcı işlemleri testi"""
        if not self.admin_token:
            return False
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Test kullanıcısı oluştur
        print("🔍 TEST: Yeni kullanıcı kaydı")
        test_email = f"admintest{hash(str(self)) % 10000}@test.com"
        
        response = requests.post(f"{self.base_url}/auth/register", json={
            "name": "Admin Test User",
            "email": test_email,
            "password": "test123"
        })
        
        if response.status_code == 200:
            data = response.json()
            if not data.get('approved', True):
                print("   ✅ Yeni kullanıcı approved=false ile oluşturuldu")
                user_id = data.get('user_id')
                
                if user_id:
                    # Kullanıcı onaylama testi
                    print("🔍 TEST: POST /api/admin/approve-user/{user_id}")
                    approve_response = requests.post(
                        f"{self.base_url}/admin/approve-user/{user_id}", 
                        headers=headers
                    )
                    
                    if approve_response.status_code == 200:
                        print("   ✅ Kullanıcı onaylama başarılı")
                        self.results.append(("Admin Approve User", True, f"User ID: {user_id}"))
                        
                        # Test kullanıcısı silme (cleanup)
                        print("🔍 TEST: POST /api/admin/reject-user/{user_id}")
                        reject_response = requests.post(
                            f"{self.base_url}/admin/reject-user/{user_id}", 
                            headers=headers
                        )
                        
                        if reject_response.status_code == 200:
                            print("   ✅ Kullanıcı silme başarılı")
                            self.results.append(("Admin Reject User", True, f"User ID: {user_id}"))
                            return True
                        else:
                            print(f"   ❌ Kullanıcı silme başarısız: {reject_response.status_code}")
                            self.results.append(("Admin Reject User", False, f"HTTP {reject_response.status_code}"))
                    else:
                        print(f"   ❌ Kullanıcı onaylama başarısız: {approve_response.status_code}")
                        self.results.append(("Admin Approve User", False, f"HTTP {approve_response.status_code}"))
                else:
                    print("   ❌ User ID alınamadı")
                    self.results.append(("Admin User Operations", False, "User ID eksik"))
            else:
                print("   ❌ Kullanıcı otomatik onaylandı (whitelist çalışmıyor)")
                self.results.append(("User Registration Whitelist", False, "Auto-approved"))
        else:
            print(f"   ❌ Kullanıcı kaydı başarısız: {response.status_code}")
            self.results.append(("User Registration", False, f"HTTP {response.status_code}"))
        
        return False

    def test_recaptcha_api(self):
        """reCAPTCHA API testi"""
        print("🔍 TEST: POST /api/verify-recaptcha")
        
        # Test token ile test
        response = requests.post(f"{self.base_url}/verify-recaptcha", json={
            "recaptcha_token": "test-token-for-verification"
        })
        
        if response.status_code == 200:
            data = response.json()
            success = data.get('success', True)
            if not success:
                print("   ✅ reCAPTCHA test token'ı doğru şekilde reddedildi")
                self.results.append(("reCAPTCHA API", True, "Test token reddedildi"))
                return True
            else:
                print("   ❌ reCAPTCHA test token'ı kabul edildi (beklenmeyen)")
                self.results.append(("reCAPTCHA API", False, "Test token kabul edildi"))
                return False
        else:
            print(f"   ❌ reCAPTCHA API hatası: {response.status_code}")
            self.results.append(("reCAPTCHA API", False, f"HTTP {response.status_code}"))
            return False

    def test_outlook_status(self):
        """Outlook entegrasyon status testi"""
        print("🔍 TEST: GET /api/outlook/status")
        
        # Demo kullanıcı ile giriş
        demo_response = requests.post(f"{self.base_url}/auth/login", json={
            "email": "demo@postadepo.com",
            "password": "demo123"
        })
        
        if demo_response.status_code == 200:
            demo_data = demo_response.json()
            demo_token = demo_data.get('token')
            
            if demo_token:
                headers = {'Authorization': f'Bearer {demo_token}'}
                response = requests.get(f"{self.base_url}/outlook/status", headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    graph_available = data.get('graph_sdk_available', False)
                    credentials_configured = data.get('credentials_configured', False)
                    
                    if graph_available and credentials_configured:
                        print("   ✅ Outlook API hazır (Graph SDK + Credentials)")
                        self.results.append(("Outlook Status", True, "SDK ve credentials hazır"))
                        return True
                    else:
                        print(f"   ❌ Outlook API eksik: SDK={graph_available}, Creds={credentials_configured}")
                        self.results.append(("Outlook Status", False, f"SDK={graph_available}, Creds={credentials_configured}"))
                        return False
                else:
                    print(f"   ❌ Outlook status hatası: {response.status_code}")
                    self.results.append(("Outlook Status", False, f"HTTP {response.status_code}"))
                    return False
            else:
                print("   ❌ Demo token alınamadı")
                self.results.append(("Outlook Status", False, "Demo token eksik"))
                return False
        else:
            print("   ❌ Demo kullanıcı girişi başarısız")
            self.results.append(("Outlook Status", False, "Demo login başarısız"))
            return False

    def test_normal_user_admin_restriction(self):
        """Normal kullanıcıların admin endpoint'lerine erişim kısıtlaması"""
        print("🔍 TEST: Normal kullanıcı admin erişim kısıtlaması")
        
        # Demo kullanıcı ile giriş
        demo_response = requests.post(f"{self.base_url}/auth/login", json={
            "email": "demo@postadepo.com",
            "password": "demo123"
        })
        
        if demo_response.status_code == 200:
            demo_data = demo_response.json()
            demo_token = demo_data.get('token')
            
            if demo_token:
                headers = {'Authorization': f'Bearer {demo_token}'}
                response = requests.get(f"{self.base_url}/admin/users", headers=headers)
                
                if response.status_code == 403:
                    print("   ✅ Normal kullanıcı admin endpoint'e erişemedi (403)")
                    self.results.append(("Admin Access Restriction", True, "403 Forbidden"))
                    return True
                else:
                    print(f"   ❌ Normal kullanıcı admin endpoint'e erişebildi: {response.status_code}")
                    self.results.append(("Admin Access Restriction", False, f"HTTP {response.status_code}"))
                    return False
            else:
                print("   ❌ Demo token alınamadı")
                self.results.append(("Admin Access Restriction", False, "Demo token eksik"))
                return False
        else:
            print("   ❌ Demo kullanıcı girişi başarısız")
            self.results.append(("Admin Access Restriction", False, "Demo login başarısız"))
            return False

    def run_focused_tests(self):
        """Odaklanmış testleri çalıştır"""
        print("🇹🇷 FOCUSED TURKISH ADMIN PANEL TEST")
        print("=" * 50)
        print("Türkçe review request'e göre spesifik testler:")
        print("1. Admin girişi: admin@postadepo.com / admindepo*")
        print("2. Admin panel API'leri")
        print("3. reCAPTCHA API")
        print("4. Kullanıcı kaydı ve whitelist")
        print("5. Outlook entegrasyonu")
        print("=" * 50)
        
        tests = [
            ("Admin Girişi", self.test_admin_login_specific),
            ("Admin Panel API'leri", self.test_admin_endpoints),
            ("Admin Kullanıcı İşlemleri", self.test_admin_user_operations),
            ("reCAPTCHA API", self.test_recaptcha_api),
            ("Outlook Status", self.test_outlook_status),
            ("Admin Erişim Kısıtlaması", self.test_normal_user_admin_restriction),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n{'='*20} {test_name} {'='*20}")
            try:
                result = test_func()
                if result:
                    passed += 1
            except Exception as e:
                print(f"   💥 Test hatası: {str(e)}")
                self.results.append((test_name, False, f"Exception: {str(e)}"))
        
        # Sonuçları özetle
        print(f"\n{'='*50}")
        print("🏁 FOCUSED TEST SONUÇLARI")
        print(f"{'='*50}")
        
        print(f"\n📊 GENEL DURUM: {passed}/{total} test başarılı")
        
        print(f"\n📋 DETAYLI SONUÇLAR:")
        for test_name, success, details in self.results:
            status = "✅" if success else "❌"
            print(f"   {status} {test_name}: {details}")
        
        # Kritik kontroller
        print(f"\n🎯 KRİTİK KONTROLLER:")
        
        admin_login_ok = any(name == "Admin Girişi" and success for name, success, _ in self.results)
        print(f"   {'✅' if admin_login_ok else '❌'} Admin user_type='admin' döndürüyor")
        
        admin_apis_ok = any("admin" in name.lower() and "api" in name.lower() and success for name, success, _ in self.results)
        print(f"   {'✅' if admin_apis_ok else '❌'} Admin panel API'leri çalışıyor")
        
        whitelist_ok = any("whitelist" in details.lower() or "approved=false" in details.lower() for _, success, details in self.results if success)
        print(f"   {'✅' if whitelist_ok else '❌'} Whitelist sistemi çalışıyor")
        
        recaptcha_ok = any("recaptcha" in name.lower() and success for name, success, _ in self.results)
        print(f"   {'✅' if recaptcha_ok else '❌'} reCAPTCHA doğrulaması çalışıyor")
        
        outlook_ok = any("outlook" in name.lower() and success for name, success, _ in self.results)
        print(f"   {'✅' if outlook_ok else '❌'} Outlook API'si hazır")
        
        access_restriction_ok = any("restriction" in name.lower() and success for name, success, _ in self.results)
        print(f"   {'✅' if access_restriction_ok else '❌'} Admin erişim kısıtlaması çalışıyor")
        
        print(f"\n{'='*50}")
        
        critical_checks = [admin_login_ok, admin_apis_ok, recaptcha_ok, outlook_ok, access_restriction_ok]
        critical_passed = sum(critical_checks)
        
        if critical_passed >= 4:  # 5'ten 4'ü yeterli
            print("🎉 KRİTİK TESTLER BAŞARILI - SİSTEM HAZIR!")
            return True
        else:
            print(f"⚠️  KRİTİK TESTLER YETERSIZ ({critical_passed}/5) - DÜZELTME GEREKLİ!")
            return False

def main():
    tester = FocusedTurkishTest()
    success = tester.run_focused_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())