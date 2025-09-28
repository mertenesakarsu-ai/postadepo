import requests
import sys
import json
import uuid
from datetime import datetime

class PostaDepoAdminPanelTester:
    def __init__(self, base_url="https://signup-admin-view.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.admin_token = None
        self.admin_user = None
        self.test_user_token = None
        self.test_user_id = None
        self.test_user_email = None
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, token=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        # Use specific token if provided, otherwise use admin token
        if token is not None:  # Check for None specifically
            if token != "":  # Only add Authorization header if token is not empty
                test_headers['Authorization'] = f'Bearer {token}'
        elif self.admin_token:
            test_headers['Authorization'] = f'Bearer {self.admin_token}'
        
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Non-dict response'}")
                except:
                    print(f"   Response: {response.text[:100]}...")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")

            return success, response.json() if response.text and response.status_code < 500 else {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_create_admin_user(self):
        """Admin kullanıcısını oluştur (eğer yoksa)"""
        success, response = self.run_test(
            "Admin Kullanıcısı Oluşturma",
            "POST",
            "admin/create-admin",
            200,
            token=""  # No token needed for this endpoint
        )
        
        if success:
            print("   ✅ Admin kullanıcısı hazır")
        
        return success

    def test_admin_login(self):
        """Admin kullanıcısı giriş testi - admin@postadepo.com / admindepo*"""
        print("\n🔐 1. ADMIN KULLANICISI GİRİŞ TESTİ")
        print("=" * 50)
        
        success, response = self.run_test(
            "Admin Giriş (admin@postadepo.com / admindepo*)",
            "POST",
            "auth/login",
            200,
            data={"email": "admin@postadepo.com", "password": "admindepo*"},
            token=""  # No token needed for login
        )
        
        if success and 'token' in response and 'user' in response:
            self.admin_token = response['token']
            self.admin_user = response['user']
            print(f"   ✅ Admin giriş başarılı: {self.admin_user.get('email')}")
            print(f"   🎫 JWT Token alındı: {self.admin_token[:20]}...")
            
            # JWT token doğrulaması
            if len(self.admin_token) > 50:  # Basic token validation
                print("   ✅ JWT token formatı geçerli")
                return True
            else:
                print("   ❌ JWT token formatı geçersiz")
                return False
        else:
            print("   ❌ Admin giriş başarısız")
            return False

    def test_admin_endpoints_access(self):
        """Admin endpoints'lerine erişim kontrolü"""
        print("\n🛡️ Admin Endpoints Erişim Kontrolü")
        print("-" * 40)
        
        if not self.admin_token:
            print("❌ Admin token bulunamadı")
            return False
        
        # Test admin endpoints
        admin_endpoints = [
            ("GET /api/admin/users", "GET", "admin/users"),
            ("GET /api/admin/pending-users", "GET", "admin/pending-users"),
        ]
        
        all_success = True
        for endpoint_name, method, endpoint in admin_endpoints:
            success, response = self.run_test(
                f"Admin Endpoint: {endpoint_name}",
                method,
                endpoint,
                200
            )
            
            if success:
                print(f"   ✅ {endpoint_name} erişimi başarılı")
            else:
                print(f"   ❌ {endpoint_name} erişimi başarısız")
                all_success = False
        
        return all_success

    def test_admin_get_all_users(self):
        """GET /api/admin/users - tüm kullanıcıları ve storage bilgilerini getir"""
        print("\n👥 2. ADMIN ENDPOINTS TESTLERİ")
        print("=" * 50)
        
        success, response = self.run_test(
            "GET /api/admin/users - Tüm Kullanıcıları Getir",
            "GET",
            "admin/users",
            200
        )
        
        if success:
            users = response.get('users', [])
            print(f"   📊 Toplam kullanıcı sayısı: {len(users)}")
            
            # Her kullanıcının storage bilgilerini kontrol et
            storage_info_count = 0
            for user in users:
                email = user.get('email', 'Unknown')
                storage_info = user.get('storage_info', {})
                
                if storage_info:
                    storage_info_count += 1
                    total_emails = storage_info.get('totalEmails', 0)
                    total_size = storage_info.get('totalSize', 0)
                    print(f"   📧 {email}: {total_emails} e-posta, {total_size} bytes ({total_size/1024:.2f} KB)")
                else:
                    print(f"   ⚠️  {email}: Storage bilgisi eksik")
            
            print(f"   ✅ Storage bilgisi olan kullanıcı: {storage_info_count}/{len(users)}")
            return storage_info_count > 0
        
        return success

    def test_admin_get_pending_users(self):
        """GET /api/admin/pending-users - onay bekleyen kullanıcıları getir"""
        success, response = self.run_test(
            "GET /api/admin/pending-users - Onay Bekleyen Kullanıcılar",
            "GET",
            "admin/pending-users",
            200
        )
        
        if success:
            pending_users = response.get('pending_users', [])
            print(f"   ⏳ Onay bekleyen kullanıcı sayısı: {len(pending_users)}")
            
            for user in pending_users:
                email = user.get('email', 'Unknown')
                name = user.get('name', 'Unknown')
                approved = user.get('approved', True)
                print(f"   👤 {name} ({email}) - Onaylı: {approved}")
            
            return True
        
        return success

    def test_create_test_user(self):
        """Yeni bir test kullanıcısı oluştur (test@example.com / test123)"""
        print("\n👤 3. YENİ KULLANICI KAYIT VE WHİTELİST TESTİ")
        print("=" * 50)
        
        # Unique email to avoid conflicts
        test_email = f"test{uuid.uuid4().hex[:8]}@example.com"
        self.test_user_email = test_email
        
        success, response = self.run_test(
            f"Yeni Test Kullanıcısı Oluşturma ({test_email})",
            "POST",
            "auth/register",
            200,
            data={
                "name": "Test Kullanıcısı",
                "email": test_email,
                "password": "test123"
            },
            token=""  # No token needed for registration
        )
        
        if success:
            self.test_user_id = response.get('user_id')
            approved = response.get('approved', True)
            
            if not approved:
                print(f"   ✅ Kullanıcı approved=false ile oluşturuldu")
                print(f"   🆔 User ID: {self.test_user_id}")
                return True
            else:
                print(f"   ❌ Kullanıcı approved=true ile oluşturuldu (whitelist çalışmıyor)")
                return False
        
        return success

    def test_unapproved_user_login(self):
        """Onaylanmamış kullanıcının giriş yapamamasını test et"""
        if not self.test_user_email:
            print("❌ Test kullanıcısı e-postası bulunamadı")
            return False
        
        success, response = self.run_test(
            "Onaylanmamış Kullanıcı Giriş Denemesi (403 bekleniyor)",
            "POST",
            "auth/login",
            403,
            data={
                "email": self.test_user_email,
                "password": "test123"
            },
            token=""  # No token needed for login
        )
        
        if success:
            print("   ✅ Onaylanmamış kullanıcı giriş yapamadı (403 Forbidden)")
            return True
        else:
            print("   ❌ Onaylanmamış kullanıcı giriş yapabildi (güvenlik sorunu)")
            return False

    def test_admin_approve_user(self):
        """POST /api/admin/approve-user/{user_id} - kullanıcı onaylama"""
        if not self.test_user_id:
            print("❌ Test kullanıcısı ID'si bulunamadı")
            return False
        
        success, response = self.run_test(
            f"POST /api/admin/approve-user/{self.test_user_id} - Kullanıcı Onaylama",
            "POST",
            f"admin/approve-user/{self.test_user_id}",
            200
        )
        
        if success:
            message = response.get('message', '')
            user_id = response.get('user_id', '')
            print(f"   ✅ Kullanıcı onaylandı: {message}")
            print(f"   🆔 Onaylanan User ID: {user_id}")
            return True
        
        return success

    def test_approved_user_login(self):
        """Onaylanan kullanıcının giriş yapabildiğini doğrula"""
        if not self.test_user_email:
            print("❌ Test kullanıcısı e-postası bulunamadı")
            return False
        
        success, response = self.run_test(
            "Onaylanan Kullanıcı Giriş Testi",
            "POST",
            "auth/login",
            200,
            data={
                "email": self.test_user_email,
                "password": "test123"
            },
            token=""  # No token needed for login
        )
        
        if success and 'token' in response and 'user' in response:
            self.test_user_token = response['token']
            test_user = response['user']
            print(f"   ✅ Onaylanan kullanıcı giriş başarılı: {test_user.get('email')}")
            print(f"   🎫 Test kullanıcısı token alındı")
            return True
        else:
            print("   ❌ Onaylanan kullanıcı giriş yapamadı")
            return False

    def test_admin_reject_user(self):
        """POST /api/admin/reject-user/{user_id} - kullanıcı reddetme (test için yeni kullanıcı)"""
        # Create another test user for rejection test
        reject_email = f"reject{uuid.uuid4().hex[:8]}@example.com"
        
        # Create user
        create_success, create_response = self.run_test(
            f"Reddedilecek Test Kullanıcısı Oluşturma ({reject_email})",
            "POST",
            "auth/register",
            200,
            data={
                "name": "Reddedilecek Kullanıcı",
                "email": reject_email,
                "password": "reject123"
            },
            token=""
        )
        
        if not create_success:
            print("   ❌ Reddedilecek kullanıcı oluşturulamadı")
            return False
        
        reject_user_id = create_response.get('user_id')
        
        # Reject user
        success, response = self.run_test(
            f"POST /api/admin/reject-user/{reject_user_id} - Kullanıcı Reddetme",
            "POST",
            f"admin/reject-user/{reject_user_id}",
            200
        )
        
        if success:
            message = response.get('message', '')
            user_id = response.get('user_id', '')
            print(f"   ✅ Kullanıcı reddedildi: {message}")
            print(f"   🆔 Reddedilen User ID: {user_id}")
            return True
        
        return success

    def test_storage_info_calculation(self):
        """Her kullanıcının storage_info bilgilerinin doğru hesaplandığını kontrol et"""
        print("\n💾 4. STORAGE INFO TESTİ")
        print("=" * 50)
        
        success, response = self.run_test(
            "Storage Info Hesaplama Kontrolü",
            "GET",
            "admin/users",
            200
        )
        
        if success:
            users = response.get('users', [])
            valid_storage_count = 0
            invalid_storage_count = 0
            
            for user in users:
                email = user.get('email', 'Unknown')
                storage_info = user.get('storage_info', {})
                
                if storage_info:
                    total_emails = storage_info.get('totalEmails', 0)
                    total_size = storage_info.get('totalSize', 0)
                    
                    # Mantıklılık kontrolleri
                    if total_emails >= 0 and total_size >= 0:
                        valid_storage_count += 1
                        
                        # Ortalama e-posta boyutu kontrolü (çok küçük veya çok büyük olmamalı)
                        if total_emails > 0:
                            avg_size = total_size / total_emails
                            if 100 <= avg_size <= 1000000:  # 100 bytes - 1MB arası makul
                                print(f"   ✅ {email}: {total_emails} e-posta, ortalama {avg_size:.0f} bytes")
                            else:
                                print(f"   ⚠️  {email}: Ortalama e-posta boyutu şüpheli ({avg_size:.0f} bytes)")
                        else:
                            print(f"   ✅ {email}: {total_emails} e-posta (yeni kullanıcı)")
                    else:
                        invalid_storage_count += 1
                        print(f"   ❌ {email}: Geçersiz storage değerleri (emails: {total_emails}, size: {total_size})")
                else:
                    invalid_storage_count += 1
                    print(f"   ❌ {email}: Storage bilgisi eksik")
            
            print(f"   📊 Geçerli storage bilgisi: {valid_storage_count}")
            print(f"   📊 Geçersiz storage bilgisi: {invalid_storage_count}")
            
            return valid_storage_count > invalid_storage_count
        
        return success

    def test_normal_user_admin_access(self):
        """Normal kullanıcının admin endpoints'lerine erişmeye çalışmasını test et (403 dönmeli)"""
        print("\n🔒 5. GÜVENLİK TESTLERİ")
        print("=" * 50)
        
        if not self.test_user_token:
            print("❌ Test kullanıcısı token'ı bulunamadı")
            return False
        
        # Test admin endpoints with normal user token
        admin_endpoints = [
            ("GET /api/admin/users", "GET", "admin/users"),
            ("GET /api/admin/pending-users", "GET", "admin/pending-users"),
        ]
        
        all_forbidden = True
        for endpoint_name, method, endpoint in admin_endpoints:
            success, response = self.run_test(
                f"Normal Kullanıcı {endpoint_name} Erişimi (403 bekleniyor)",
                method,
                endpoint,
                403,
                token=self.test_user_token  # Use test user token instead of admin
            )
            
            if success:
                print(f"   ✅ {endpoint_name}: Normal kullanıcı erişimi engellendi (403)")
            else:
                print(f"   ❌ {endpoint_name}: Normal kullanıcı erişebildi (güvenlik sorunu)")
                all_forbidden = False
        
        return all_forbidden

    def test_no_token_admin_access(self):
        """Token olmadan admin endpoints'lerine erişim testi (403 dönmeli - FastAPI HTTPBearer davranışı)"""
        admin_endpoints = [
            ("GET /api/admin/users", "GET", "admin/users"),
            ("GET /api/admin/pending-users", "GET", "admin/pending-users"),
        ]
        
        all_unauthorized = True
        for endpoint_name, method, endpoint in admin_endpoints:
            success, response = self.run_test(
                f"Token Olmadan {endpoint_name} Erişimi (403 bekleniyor)",
                method,
                endpoint,
                403,  # FastAPI HTTPBearer returns 403 for missing auth
                token=""  # No token
            )
            
            if success:
                print(f"   ✅ {endpoint_name}: Token olmadan erişim engellendi (403)")
            else:
                print(f"   ❌ {endpoint_name}: Token olmadan erişilebildi (güvenlik sorunu)")
                all_unauthorized = False
        
        return all_unauthorized

    def test_admin_user_creation_endpoint(self):
        """Admin kullanıcısı oluşturma endpoint'ini test et"""
        print("\n🔧 BONUS: Admin Kullanıcısı Oluşturma Endpoint Testi")
        print("-" * 50)
        
        success, response = self.run_test(
            "POST /api/admin/create-admin - Admin Oluşturma",
            "POST",
            "admin/create-admin",
            200,
            token=""  # No token needed
        )
        
        if success:
            message = response.get('message', '')
            email = response.get('email', '')
            print(f"   ✅ Admin endpoint yanıtı: {message}")
            if email:
                print(f"   📧 Admin e-posta: {email}")
            return True
        
        return success

def main():
    print("🚀 PostaDepo Admin Panel Sistemi Kapsamlı Backend Testleri")
    print("=" * 70)
    print("📋 Test Planı:")
    print("1. Admin Kullanıcısı Giriş Testi (admin@postadepo.com / admindepo*)")
    print("2. Admin Endpoints Testleri (users, pending-users, approve, reject)")
    print("3. Yeni Kullanıcı Kayıt ve Whitelist Testi")
    print("4. Storage Info Testi")
    print("5. Güvenlik Testleri (403, 401)")
    print("=" * 70)
    
    tester = PostaDepoAdminPanelTester()
    
    # Test sequence for admin panel
    tests = [
        # Hazırlık
        ("Admin Kullanıcısı Hazırlama", tester.test_create_admin_user),
        
        # 1. Admin Kullanıcısı Giriş Testi
        ("1. Admin Kullanıcısı Giriş Testi", tester.test_admin_login),
        ("Admin Endpoints Erişim Kontrolü", tester.test_admin_endpoints_access),
        
        # 2. Admin Endpoints Testleri
        ("2a. GET /api/admin/users", tester.test_admin_get_all_users),
        ("2b. GET /api/admin/pending-users", tester.test_admin_get_pending_users),
        
        # 3. Yeni Kullanıcı Kayıt ve Whitelist Testi
        ("3a. Yeni Test Kullanıcısı Oluşturma", tester.test_create_test_user),
        ("3b. Onaylanmamış Kullanıcı Giriş Testi", tester.test_unapproved_user_login),
        ("3c. POST /api/admin/approve-user", tester.test_admin_approve_user),
        ("3d. Onaylanan Kullanıcı Giriş Testi", tester.test_approved_user_login),
        ("3e. POST /api/admin/reject-user", tester.test_admin_reject_user),
        
        # 4. Storage Info Testi
        ("4. Storage Info Hesaplama Testi", tester.test_storage_info_calculation),
        
        # 5. Güvenlik Testleri
        ("5a. Normal Kullanıcı Admin Erişimi (403)", tester.test_normal_user_admin_access),
        ("5b. Token Olmadan Admin Erişimi (403)", tester.test_no_token_admin_access),
        
        # Bonus
        ("Bonus: Admin Oluşturma Endpoint", tester.test_admin_user_creation_endpoint),
    ]
    
    failed_tests = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            result = test_func()
            if not result:
                failed_tests.append(test_name)
                print(f"⚠️  {test_name} BAŞARISIZ")
            else:
                print(f"✅ {test_name} BAŞARILI")
        except Exception as e:
            failed_tests.append(test_name)
            print(f"💥 {test_name} HATA: {str(e)}")
    
    # Final results
    print("\n" + "=" * 70)
    print("📊 POSTADEPO ADMİN PANEL SİSTEMİ TEST SONUÇLARI")
    print("=" * 70)
    print(f"✅ Başarılı testler: {tester.tests_passed}/{tester.tests_run}")
    print(f"❌ Başarısız testler: {len(failed_tests)}")
    
    if failed_tests:
        print("\n❌ Başarısız Test Listesi:")
        for i, test in enumerate(failed_tests, 1):
            print(f"   {i}. {test}")
    
    success_rate = (tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0
    print(f"\n📈 Başarı Oranı: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print("🎉 MÜKEMMEL! Admin panel sistemi tam çalışır durumda!")
        return 0
    elif success_rate >= 75:
        print("✅ İYİ! Admin panel sistemi genel olarak çalışıyor, küçük sorunlar var.")
        return 0
    else:
        print("⚠️  SORUNLU! Admin panel sisteminde önemli sorunlar tespit edildi.")
        return 1

if __name__ == "__main__":
    sys.exit(main())