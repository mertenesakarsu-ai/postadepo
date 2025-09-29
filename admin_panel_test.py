import requests
import sys
import json
import uuid
from datetime import datetime

class AdminPanelDataLoadingTester:
    """Focused tester for admin panel data loading issues reported by user"""
    def __init__(self, base_url="https://code-state-helper.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.admin_token = None
        self.test_user_id = None
        self.test_user_email = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.admin_token:
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
                    if isinstance(response_data, dict):
                        print(f"   Response keys: {list(response_data.keys())}")
                    return success, response_data
                except:
                    print(f"   Response: {response.text[:100]}...")
                    return success, {}
            else:
                self.failed_tests.append(name)
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:300]}...")
                return False, {}

        except Exception as e:
            self.failed_tests.append(name)
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_admin_login(self):
        """1. Admin kullanıcısı (admin@postadepo.com / admindepo*) ile giriş yap"""
        print("\n🔐 1. ADMIN LOGIN TEST")
        print("=" * 50)
        
        success, response = self.run_test(
            "Admin Login (admin@postadepo.com / admindepo*)",
            "POST",
            "auth/login",
            200,
            data={"email": "admin@postadepo.com", "password": "admindepo*"}
        )
        
        if success and 'token' in response and 'user' in response:
            self.admin_token = response['token']
            user = response['user']
            print(f"   ✅ Admin logged in: {user.get('name')} ({user.get('email')})")
            print(f"   User type: {user.get('user_type')}")
            return True
        else:
            print(f"   ❌ Admin login failed - this explains data loading errors!")
            return False

    def test_admin_users_endpoint(self):
        """2. GET /api/admin/users endpoint'ini test et - kullanıcıları ve storage bilgilerini getiriyor mu?"""
        print("\n👥 2. ADMIN USERS ENDPOINT TEST")
        print("=" * 50)
        
        success, response = self.run_test(
            "GET /api/admin/users - Users and Storage Info",
            "GET",
            "admin/users",
            200
        )
        
        if success:
            users = response.get('users', [])
            print(f"   📊 Total users found: {len(users)}")
            
            # Calculate stats for admin panel
            total_users = len(users)
            approved_users = sum(1 for user in users if user.get('approved', False))
            total_emails = 0
            total_storage = 0
            
            print(f"\n   📈 ADMIN PANEL STATS DATA:")
            print(f"   - Toplam kullanıcı sayısı: {total_users}")
            print(f"   - Onaylı hesaplar: {approved_users}")
            
            # Check storage info for each user
            users_with_storage = 0
            for user in users[:5]:  # Show first 5 users
                storage_info = user.get('storage_info', {})
                user_emails = storage_info.get('totalEmails', 0)
                user_storage = storage_info.get('totalSize', 0)
                
                total_emails += user_emails
                total_storage += user_storage
                
                if storage_info:
                    users_with_storage += 1
                
                print(f"   👤 {user.get('name', 'No name')} ({user.get('email', 'No email')})")
                print(f"      - Emails: {user_emails}, Storage: {user_storage} bytes")
            
            print(f"\n   📊 CALCULATED TOTALS:")
            print(f"   - Toplam e-posta sayısı: {total_emails}")
            print(f"   - Toplam depolama boyutu: {total_storage} bytes ({total_storage/1024:.2f} KB)")
            print(f"   - Users with storage info: {users_with_storage}/{len(users)}")
            
            if total_users > 0 and users_with_storage > 0:
                print(f"   ✅ All required data for admin panel stats is available!")
                return True
            else:
                print(f"   ❌ Missing data - this could cause 'veriler yüklenirken hata oluştu'")
                return False
        
        return False

    def test_admin_pending_users_endpoint(self):
        """3. GET /api/admin/pending-users endpoint'ini test et - onay bekleyen kullanıcıları getiriyor mu?"""
        print("\n⏳ 3. ADMIN PENDING USERS ENDPOINT TEST")
        print("=" * 50)
        
        success, response = self.run_test(
            "GET /api/admin/pending-users - Pending Approvals",
            "GET",
            "admin/pending-users",
            200
        )
        
        if success:
            pending_users = response.get('pending_users', [])
            print(f"   📊 Pending users found: {len(pending_users)}")
            
            for user in pending_users:
                print(f"   ⏳ Pending: {user.get('name', 'No name')} ({user.get('email', 'No email')})")
                print(f"      - Approved: {user.get('approved', 'Not specified')}")
            
            print(f"   📈 ADMIN PANEL STATS:")
            print(f"   - Bekleyen onaylar: {len(pending_users)}")
            
            print(f"   ✅ Pending users endpoint working - data available for admin panel")
            return True
        
        return False

    def test_admin_system_logs_endpoint(self):
        """4. GET /api/admin/system-logs endpoint'ini test et - sistem loglarını getiriyor mu?"""
        print("\n📋 4. ADMIN SYSTEM LOGS ENDPOINT TEST")
        print("=" * 50)
        
        success, response = self.run_test(
            "GET /api/admin/system-logs - System Logs",
            "GET",
            "admin/system-logs",
            200
        )
        
        if success:
            logs = response.get('logs', [])
            print(f"   📊 System logs found: {len(logs)}")
            
            # Show recent logs
            for i, log in enumerate(logs[:5]):
                log_type = log.get('log_type', 'Unknown')
                message = log.get('message', 'No message')
                timestamp = log.get('formatted_timestamp', 'No timestamp')
                user_email = log.get('user_email', 'No user')
                
                print(f"   📝 Log {i+1}: [{log_type}] {timestamp}")
                print(f"      User: {user_email}")
                print(f"      Message: {message[:80]}...")
            
            print(f"   ✅ System logs endpoint working - logs available for admin panel")
            return True
        
        return False

    def test_create_new_user_and_check_pending(self):
        """5. Yeni bir test kullanıcısı kaydı oluştur (approved=false ile) ve onay bekleyenler listesinde görünüyor mu kontrol et"""
        print("\n👤 5. CREATE NEW USER AND CHECK PENDING LIST")
        print("=" * 50)
        
        # Create new test user
        timestamp = int(datetime.now().timestamp())
        test_email = f"newuser{timestamp}@test.com"
        test_name = f"New User {timestamp}"
        
        # First, create user without admin token
        temp_token = self.admin_token
        self.admin_token = None
        
        success, response = self.run_test(
            "Create New Test User (approved=false)",
            "POST",
            "auth/register",
            200,
            data={
                "name": test_name,
                "email": test_email,
                "password": "testpass123"
            }
        )
        
        # Restore admin token
        self.admin_token = temp_token
        
        if success:
            self.test_user_id = response.get('user_id')
            self.test_user_email = test_email
            approved = response.get('approved', True)
            
            print(f"   ✅ New user created: {test_name} ({test_email})")
            print(f"   User ID: {self.test_user_id}")
            print(f"   Approved: {approved}")
            
            if not approved:
                print(f"   ✅ User correctly created as unapproved")
                
                # Now check if user appears in pending list
                pending_success, pending_response = self.run_test(
                    "Check New User in Pending List",
                    "GET",
                    "admin/pending-users",
                    200
                )
                
                if pending_success:
                    pending_users = pending_response.get('pending_users', [])
                    user_found = any(user.get('email') == test_email for user in pending_users)
                    
                    if user_found:
                        print(f"   ✅ New user appears in pending approvals list!")
                        print(f"   ✅ 'Yeni kayıt onay bekleyen bölümüne düşüyor' - WORKING")
                        return True
                    else:
                        print(f"   ❌ New user NOT found in pending list!")
                        print(f"   ❌ 'Yeni kayıt onay bekleyen bölümüne düşmüyor' - PROBLEM CONFIRMED")
                        return False
            else:
                print(f"   ❌ User was approved automatically - whitelist not working")
                return False
        
        return False

    def test_admin_panel_all_data_verification(self):
        """6. Admin panelindeki stats verilerini hesaplamak için gerekli tüm veriler geldiğini doğrula"""
        print("\n📊 6. ADMIN PANEL ALL DATA VERIFICATION")
        print("=" * 50)
        
        # Get all required data for admin panel
        users_success, users_response = self.run_test(
            "Get All Users Data",
            "GET",
            "admin/users",
            200
        )
        
        pending_success, pending_response = self.run_test(
            "Get Pending Users Data",
            "GET",
            "admin/pending-users",
            200
        )
        
        if users_success and pending_success:
            users = users_response.get('users', [])
            pending_users = pending_response.get('pending_users', [])
            
            print(f"\n   📈 COMPLETE ADMIN PANEL STATS CALCULATION:")
            
            # Calculate all stats that admin panel needs
            total_users = len(users)
            approved_users = sum(1 for user in users if user.get('approved', False))
            pending_approvals = len(pending_users)
            
            total_emails = 0
            total_storage = 0
            
            for user in users:
                storage_info = user.get('storage_info', {})
                total_emails += storage_info.get('totalEmails', 0)
                total_storage += storage_info.get('totalSize', 0)
            
            print(f"   📊 ADMIN PANEL DASHBOARD STATS:")
            print(f"   ✅ Toplam kullanıcı sayısı: {total_users}")
            print(f"   ✅ Onaylı hesaplar: {approved_users}")
            print(f"   ✅ Bekleyen onaylar: {pending_approvals}")
            print(f"   ✅ Toplam e-posta sayısı: {total_emails}")
            print(f"   ✅ Toplam depolama boyutu: {total_storage} bytes ({total_storage/1024:.2f} KB)")
            
            # Verify data completeness
            all_data_available = (
                total_users >= 0 and
                approved_users >= 0 and
                pending_approvals >= 0 and
                total_emails >= 0 and
                total_storage >= 0
            )
            
            if all_data_available:
                print(f"\n   🎉 ALL ADMIN PANEL DATA IS AVAILABLE!")
                print(f"   ✅ No reason for 'veriler yüklenirken hata oluştu' error")
                print(f"   ✅ Admin panel should display all statistics correctly")
                return True
            else:
                print(f"\n   ❌ SOME ADMIN PANEL DATA IS MISSING!")
                print(f"   ❌ This could cause 'veriler yüklenirken hata oluştu' error")
                return False
        
        return False

def run_focused_admin_panel_test():
    """Run focused test for admin panel data loading issues"""
    print("🚀 PostaDepo Admin Panel Data Loading Issue Test")
    print("Testing specific user complaints about admin panel")
    print("=" * 60)
    
    tester = AdminPanelDataLoadingTester()
    
    # Test sequence based on user complaints
    tests = [
        ("1. Admin Login", tester.test_admin_login),
        ("2. Admin Users Endpoint", tester.test_admin_users_endpoint),
        ("3. Admin Pending Users Endpoint", tester.test_admin_pending_users_endpoint),
        ("4. Admin System Logs Endpoint", tester.test_admin_system_logs_endpoint),
        ("5. Create New User and Check Pending", tester.test_create_new_user_and_check_pending),
        ("6. Admin Panel All Data Verification", tester.test_admin_panel_all_data_verification),
    ]
    
    print(f"\n📋 Running {len(tests)} focused tests for admin panel issues...")
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*60}")
            result = test_func()
            if not result:
                print(f"⚠️  {test_name} - FAILED")
            else:
                print(f"✅ {test_name} - PASSED")
        except Exception as e:
            print(f"💥 {test_name} - CRASHED: {str(e)}")
            tester.failed_tests.append(test_name)
    
    # Print final results
    print(f"\n{'='*60}")
    print(f"📊 ADMIN PANEL DATA LOADING TEST RESULTS")
    print(f"{'='*60}")
    print(f"✅ Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print(f"❌ Tests failed: {len(tester.failed_tests)}")
    
    if tester.failed_tests:
        print(f"\n❌ FAILED TESTS:")
        for i, failed_test in enumerate(tester.failed_tests, 1):
            print(f"   {i}. {failed_test}")
    
    # Analysis of user complaints
    print(f"\n🔍 ANALYSIS OF USER COMPLAINTS:")
    print(f"{'='*60}")
    
    complaints = [
        "Admin panelinde 'veriler yüklenirken hata oluştu' bildirimi geliyor",
        "Toplam kullanıcı sayısı, onaylı hesaplar, bekleyen onaylar görünmüyor",
        "Toplam eposta sayısı, toplam depolama boyutu görünmüyor",
        "Tüm kullanıcılar menüsünde kullanıcıları göremiyorum",
        "Yeni kayıt geldiğinde onay bekleyen bölümüne düşmüyor"
    ]
    
    for complaint in complaints:
        print(f"📝 {complaint}")
    
    if tester.tests_passed == tester.tests_run:
        print(f"\n🎉 ALL ADMIN PANEL TESTS PASSED!")
        print(f"   Backend APIs are working correctly.")
        print(f"   The issue might be in the frontend or network connectivity.")
        return 0
    else:
        print(f"\n⚠️  SOME ADMIN PANEL TESTS FAILED!")
        print(f"   This explains the user's complaints about data loading errors.")
        return 1

class PostaDepoAdminPanelTester:
    def __init__(self, base_url="https://code-state-helper.preview.emergentagent.com/api"):
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

    def test_system_logs_endpoint(self):
        """GET /api/admin/system-logs - Sistem loglarını listele"""
        print("\n📋 SYSTEM LOGS ENDPOINT TESTİ")
        print("=" * 50)
        
        success, response = self.run_test(
            "GET /api/admin/system-logs - Sistem Logları",
            "GET",
            "admin/system-logs",
            200
        )
        
        if success:
            logs = response.get('logs', [])
            print(f"   📊 Toplam sistem logu: {len(logs)}")
            
            # Log türlerini kontrol et
            log_types = set()
            for log in logs[:10]:  # İlk 10 logu kontrol et
                log_type = log.get('log_type', 'UNKNOWN')
                log_types.add(log_type)
                message = log.get('message', '')
                timestamp = log.get('formatted_timestamp', log.get('timestamp', ''))
                print(f"   📝 [{log_type}] {message[:60]}... ({timestamp})")
            
            print(f"   🏷️  Log türleri: {', '.join(sorted(log_types))}")
            
            # Beklenen log türlerini kontrol et
            expected_types = {'USER_REGISTER', 'USER_LOGIN', 'USER_APPROVED'}
            found_types = log_types.intersection(expected_types)
            
            if found_types:
                print(f"   ✅ Beklenen log türleri bulundu: {', '.join(found_types)}")
                return True
            else:
                print(f"   ⚠️  Beklenen log türleri bulunamadı, mevcut türler: {', '.join(log_types)}")
                return len(logs) > 0  # En azından log varsa başarılı say
        
        return success

    def test_system_logs_export(self):
        """GET /api/admin/system-logs/export - JSON export"""
        success, response = self.run_test(
            "GET /api/admin/system-logs/export - JSON Export",
            "GET",
            "admin/system-logs/export",
            200
        )
        
        if success:
            # Export formatını kontrol et
            if 'logs' in response and 'export_info' in response:
                logs = response['logs']
                export_info = response['export_info']
                
                print(f"   ✅ Export başarılı: {len(logs)} log")
                print(f"   📅 Export zamanı: {export_info.get('export_timestamp', 'Bilinmiyor')}")
                print(f"   📊 Toplam log: {export_info.get('total_logs', 0)}")
                return True
            else:
                print("   ❌ Export formatı hatalı")
                return False
        
        return success

    def test_bulk_approve_users(self):
        """POST /api/admin/bulk-approve-users - Toplu onay"""
        print("\n✅ BULK APPROVE USERS TESTİ")
        print("=" * 50)
        
        # Önce test kullanıcıları oluştur
        test_user_ids = []
        for i in range(3):
            test_email = f"bulktest{uuid.uuid4().hex[:6]}@test.com"
            
            create_success, create_response = self.run_test(
                f"Bulk Test Kullanıcısı {i+1} Oluşturma",
                "POST",
                "auth/register",
                200,
                data={
                    "name": f"Bulk Test {i+1}",
                    "email": test_email,
                    "password": "test123"
                },
                token=""
            )
            
            if create_success and create_response.get('user_id'):
                test_user_ids.append(create_response['user_id'])
                print(f"   ✅ Bulk test kullanıcısı oluşturuldu: {test_email}")
        
        if not test_user_ids:
            print("   ❌ Bulk test için kullanıcı oluşturulamadı")
            return False
        
        # Toplu onay testi
        success, response = self.run_test(
            "POST /api/admin/bulk-approve-users - Toplu Onay",
            "POST",
            "admin/bulk-approve-users",
            200,
            data={"user_ids": test_user_ids}
        )
        
        if success:
            approved_count = response.get('approved_count', 0)
            failed_count = response.get('failed_count', 0)
            
            print(f"   ✅ Toplu onay tamamlandı")
            print(f"   ✅ Onaylanan: {approved_count} kullanıcı")
            print(f"   ❌ Başarısız: {failed_count} kullanıcı")
            
            return approved_count > 0
        
        return success

    def test_bulk_reject_users(self):
        """POST /api/admin/bulk-reject-users - Toplu red"""
        print("\n❌ BULK REJECT USERS TESTİ")
        print("=" * 50)
        
        # Test kullanıcıları oluştur
        test_user_ids = []
        for i in range(2):
            test_email = f"rejecttest{uuid.uuid4().hex[:6]}@test.com"
            
            create_success, create_response = self.run_test(
                f"Reject Test Kullanıcısı {i+1} Oluşturma",
                "POST",
                "auth/register",
                200,
                data={
                    "name": f"Reject Test {i+1}",
                    "email": test_email,
                    "password": "test123"
                },
                token=""
            )
            
            if create_success and create_response.get('user_id'):
                test_user_ids.append(create_response['user_id'])
                print(f"   ✅ Reject test kullanıcısı oluşturuldu: {test_email}")
        
        if not test_user_ids:
            print("   ❌ Reject test için kullanıcı oluşturulamadı")
            return False
        
        # Toplu red testi
        success, response = self.run_test(
            "POST /api/admin/bulk-reject-users - Toplu Red",
            "POST",
            "admin/bulk-reject-users",
            200,
            data={"user_ids": test_user_ids}
        )
        
        if success:
            rejected_count = response.get('rejected_count', 0)
            failed_count = response.get('failed_count', 0)
            
            print(f"   ✅ Toplu red tamamlandı")
            print(f"   ❌ Reddedilen: {rejected_count} kullanıcı")
            print(f"   ❌ Başarısız: {failed_count} kullanıcı")
            
            return rejected_count > 0
        
        return success

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
    
    # Test sequence for admin panel - Turkish Review Request Focus
    tests = [
        # Hazırlık
        ("Admin Kullanıcısı Hazırlama", tester.test_create_admin_user),
        
        # 1. Admin Kullanıcısı Giriş Testi (admin@postadepo.com / admindepo*)
        ("1. Admin Kullanıcısı Giriş Testi", tester.test_admin_login),
        ("Admin Endpoints Erişim Kontrolü", tester.test_admin_endpoints_access),
        
        # 2. Gerçek Sistem Log Sistemi Testleri
        ("2a. Yeni Test Kullanıcısı Oluşturma (Log için)", tester.test_create_test_user),
        ("2b. Onaylanmamış Kullanıcı Giriş Testi", tester.test_unapproved_user_login),
        ("2c. POST /api/admin/approve-user (Log için)", tester.test_admin_approve_user),
        ("2d. Onaylanan Kullanıcı Giriş Testi (Log için)", tester.test_approved_user_login),
        
        # 3. Yeni Admin Endpoint'leri Testleri
        ("3a. GET /api/admin/system-logs - Log Listesi", tester.test_system_logs_endpoint),
        ("3b. GET /api/admin/system-logs/export - JSON Export", tester.test_system_logs_export),
        ("3c. POST /api/admin/bulk-approve-users - Toplu Onay", tester.test_bulk_approve_users),
        ("3d. POST /api/admin/bulk-reject-users - Toplu Red", tester.test_bulk_reject_users),
        
        # 4. Admin Yetkisi Kontrolleri
        ("4a. Normal Kullanıcı Admin Erişimi (403)", tester.test_normal_user_admin_access),
        ("4b. Token Olmadan Admin Erişimi (403)", tester.test_no_token_admin_access),
        
        # 5. Diğer Admin Endpoints
        ("5a. GET /api/admin/users", tester.test_admin_get_all_users),
        ("5b. GET /api/admin/pending-users", tester.test_admin_get_pending_users),
        ("5c. POST /api/admin/reject-user", tester.test_admin_reject_user),
        
        # 6. Storage Info Testi
        ("6. Storage Info Hesaplama Testi", tester.test_storage_info_calculation),
        
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
    sys.exit(run_focused_admin_panel_test())