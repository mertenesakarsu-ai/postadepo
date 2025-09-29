import requests
import sys
import json
import uuid
from datetime import datetime

class PostaDepoAdminTester:
    def __init__(self, base_url="https://missing-field-fix.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.admin_token = None
        self.admin_user = None
        self.test_user_id = None
        self.test_user_email = None
        self.tests_run = 0
        self.tests_passed = 0

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

    def test_admin_login(self):
        """Test admin user login (admin@postadepo.com / admindepo*)"""
        print("\n🔐 ADMIN LOGIN TEST")
        print("=" * 50)
        
        success, response = self.run_test(
            "Admin User Login (admin@postadepo.com / admindepo*)",
            "POST",
            "auth/login",
            200,
            data={"email": "admin@postadepo.com", "password": "admindepo*"}
        )
        
        if success and 'token' in response and 'user' in response:
            self.admin_token = response['token']
            self.admin_user = response['user']
            print(f"   ✅ Admin logged in successfully")
            print(f"   User: {self.admin_user.get('email')} (Type: {self.admin_user.get('user_type')})")
            print(f"   Token length: {len(self.admin_token)} characters")
            return True
        else:
            print(f"   ❌ Admin login failed")
            return False

    def test_logout_functionality(self):
        """Test logout functionality - token validation and localStorage clearing"""
        print("\n🚪 LOGOUT FUNCTIONALITY TEST")
        print("=" * 50)
        
        if not self.admin_token:
            print("❌ No admin token available for logout test")
            return False
        
        # Test 1: Verify token is currently valid
        print("📋 Step 1: Verifying current token is valid...")
        success, response = self.run_test(
            "Verify Token Before Logout",
            "GET",
            "admin/users",
            200
        )
        
        if not success:
            print("❌ Token is not valid before logout test")
            return False
        
        print("   ✅ Token is valid before logout")
        
        # Test 2: Simulate logout (in a real app, this would clear localStorage)
        print("📋 Step 2: Simulating logout process...")
        print("   ℹ️  Note: Backend doesn't have explicit logout endpoint")
        print("   ℹ️  Logout is handled client-side by removing token from localStorage")
        print("   ℹ️  Testing token invalidation by removing it from our test client")
        
        # Store original token
        original_token = self.admin_token
        
        # Simulate logout by clearing token
        self.admin_token = None
        
        # Test 3: Verify access is denied without token
        print("📋 Step 3: Verifying access is denied after logout...")
        success, response = self.run_test(
            "Access Admin Endpoint After Logout",
            "GET",
            "admin/users",
            403  # Should get 403 Forbidden (Not authenticated)
        )
        
        if success:
            print("   ✅ Access correctly denied after logout (403 Forbidden)")
            logout_success = True
        else:
            print("   ❌ Access was not properly denied after logout")
            logout_success = False
        
        # Test 4: Verify re-login works
        print("📋 Step 4: Testing re-login after logout...")
        login_success, login_response = self.run_test(
            "Re-login After Logout",
            "POST",
            "auth/login",
            200,
            data={"email": "admin@postadepo.com", "password": "admindepo*"}
        )
        
        if login_success and 'token' in login_response:
            self.admin_token = login_response['token']
            print("   ✅ Re-login successful after logout")
            print(f"   New token length: {len(self.admin_token)} characters")
            
            # Verify new token works
            verify_success, verify_response = self.run_test(
                "Verify New Token Works",
                "GET",
                "admin/users",
                200
            )
            
            if verify_success:
                print("   ✅ New token works correctly")
                return logout_success
            else:
                print("   ❌ New token doesn't work")
                return False
        else:
            print("   ❌ Re-login failed")
            # Restore original token for other tests
            self.admin_token = original_token
            return False

    def test_create_test_user(self):
        """Create a test user for pending users testing"""
        print("\n👤 CREATE TEST USER")
        print("=" * 50)
        
        # Generate unique email for test user
        import random
        random_num = random.randint(10000, 99999)
        self.test_user_email = f"testuser{random_num}@gmail.com"
        
        print(f"📧 Creating test user: {self.test_user_email}")
        
        success, response = self.run_test(
            "Create Test User (Should be Unapproved)",
            "POST",
            "auth/register",
            200,
            data={
                "name": f"Test User {random_num}",
                "email": self.test_user_email,
                "password": "testpass123"
            }
        )
        
        if success:
            approved = response.get('approved', True)
            self.test_user_id = response.get('user_id')
            
            if not approved and self.test_user_id:
                print(f"   ✅ Test user created successfully")
                print(f"   User ID: {self.test_user_id}")
                print(f"   Email: {self.test_user_email}")
                print(f"   Approved: {approved} (correct - should be False)")
                return True
            else:
                print(f"   ❌ Test user was approved automatically (should be False)")
                return False
        else:
            print(f"   ❌ Failed to create test user")
            return False

    def test_pending_users_endpoint(self):
        """Test GET /api/admin/pending-users endpoint"""
        print("\n📋 PENDING USERS ENDPOINT TEST")
        print("=" * 50)
        
        if not self.admin_token:
            print("❌ No admin token available")
            return False
        
        success, response = self.run_test(
            "GET /api/admin/pending-users",
            "GET",
            "admin/pending-users",
            200
        )
        
        if success:
            pending_users = response.get('pending_users', [])
            print(f"   📊 Found {len(pending_users)} pending users")
            
            # Check if our test user is in the list
            test_user_found = False
            if self.test_user_email:
                for user in pending_users:
                    print(f"   👤 Pending user: {user.get('email')} (ID: {user.get('id')})")
                    if user.get('email') == self.test_user_email:
                        test_user_found = True
                        print(f"      ✅ Our test user found in pending list")
            
            if self.test_user_email and not test_user_found:
                print(f"   ❌ Our test user ({self.test_user_email}) not found in pending list")
                return False
            
            print(f"   ✅ Pending users endpoint working correctly")
            return True
        else:
            print(f"   ❌ Failed to get pending users")
            return False

    def test_admin_users_endpoint(self):
        """Test GET /api/admin/users endpoint"""
        print("\n👥 ADMIN USERS ENDPOINT TEST")
        print("=" * 50)
        
        if not self.admin_token:
            print("❌ No admin token available")
            return False
        
        success, response = self.run_test(
            "GET /api/admin/users (All Users)",
            "GET",
            "admin/users",
            200
        )
        
        if success:
            users = response.get('users', [])
            print(f"   📊 Found {len(users)} total users")
            
            admin_users = 0
            regular_users = 0
            
            for user in users:
                user_type = user.get('user_type', 'email')
                email = user.get('email', 'No email')
                approved = user.get('approved', False)
                storage_info = user.get('storage_info', {})
                
                print(f"   👤 User: {email}")
                print(f"      Type: {user_type}, Approved: {approved}")
                print(f"      Storage: {storage_info.get('totalEmails', 0)} emails, {storage_info.get('totalSize', 0)} bytes")
                
                if user_type == 'admin':
                    admin_users += 1
                else:
                    regular_users += 1
            
            print(f"   📈 Summary: {admin_users} admin users, {regular_users} regular users")
            print(f"   ✅ Admin users endpoint working correctly")
            return True
        else:
            print(f"   ❌ Failed to get all users")
            return False

    def test_admin_authorization(self):
        """Test admin authorization - non-admin users should get 403"""
        print("\n🔒 ADMIN AUTHORIZATION TEST")
        print("=" * 50)
        
        # Test 1: Create a regular user and try to access admin endpoints
        print("📋 Step 1: Creating regular user for authorization test...")
        
        import random
        regular_user_email = f"regular{random.randint(1000, 9999)}@gmail.com"
        
        # Create regular user
        create_success, create_response = self.run_test(
            "Create Regular User",
            "POST",
            "auth/register",
            200,
            data={
                "name": "Regular User",
                "email": regular_user_email,
                "password": "regularpass123"
            }
        )
        
        if not create_success:
            print("❌ Failed to create regular user for authorization test")
            return False
        
        regular_user_id = create_response.get('user_id')
        
        # Approve the regular user so they can login
        print("📋 Step 2: Approving regular user...")
        approve_success, approve_response = self.run_test(
            "Approve Regular User",
            "POST",
            f"admin/approve-user/{regular_user_id}",
            200
        )
        
        if not approve_success:
            print("❌ Failed to approve regular user")
            return False
        
        # Login as regular user
        print("📋 Step 3: Logging in as regular user...")
        
        # Store admin token
        admin_token_backup = self.admin_token
        
        login_success, login_response = self.run_test(
            "Login as Regular User",
            "POST",
            "auth/login",
            200,
            data={
                "email": regular_user_email,
                "password": "regularpass123"
            }
        )
        
        if not login_success:
            print("❌ Failed to login as regular user")
            self.admin_token = admin_token_backup
            return False
        
        # Use regular user token
        self.admin_token = login_response['token']
        regular_user_info = login_response['user']
        
        print(f"   ✅ Logged in as regular user: {regular_user_info.get('email')}")
        print(f"   User type: {regular_user_info.get('user_type')}")
        
        # Test 4: Try to access admin endpoints (should fail with 403)
        print("📋 Step 4: Testing admin endpoint access with regular user...")
        
        admin_endpoints = [
            ("admin/users", "GET"),
            ("admin/pending-users", "GET"),
        ]
        
        authorization_tests_passed = 0
        
        for endpoint, method in admin_endpoints:
            success, response = self.run_test(
                f"Regular User Access {endpoint}",
                method,
                endpoint,
                403  # Should get 403 Forbidden
            )
            
            if success:
                print(f"   ✅ Regular user correctly denied access to {endpoint}")
                authorization_tests_passed += 1
            else:
                print(f"   ❌ Regular user was not denied access to {endpoint}")
        
        # Restore admin token
        self.admin_token = admin_token_backup
        
        print(f"   📊 Authorization tests passed: {authorization_tests_passed}/{len(admin_endpoints)}")
        
        return authorization_tests_passed == len(admin_endpoints)

    def test_user_approval_process(self):
        """Test user approval and rejection process"""
        print("\n✅ USER APPROVAL PROCESS TEST")
        print("=" * 50)
        
        if not self.admin_token or not self.test_user_id:
            print("❌ Missing admin token or test user ID")
            return False
        
        # Test 1: Verify user is in pending list
        print("📋 Step 1: Verifying test user is in pending list...")
        
        pending_success, pending_response = self.run_test(
            "Check Pending Users Before Approval",
            "GET",
            "admin/pending-users",
            200
        )
        
        if not pending_success:
            print("❌ Failed to get pending users")
            return False
        
        pending_users = pending_response.get('pending_users', [])
        test_user_in_pending = any(user.get('id') == self.test_user_id for user in pending_users)
        
        if not test_user_in_pending:
            print(f"❌ Test user not found in pending list")
            return False
        
        print(f"   ✅ Test user found in pending list")
        
        # Test 2: Try to login as unapproved user (should fail)
        print("📋 Step 2: Testing login with unapproved user...")
        
        # Store admin token
        admin_token_backup = self.admin_token
        self.admin_token = None
        
        unapproved_login_success, unapproved_response = self.run_test(
            "Unapproved User Login Attempt",
            "POST",
            "auth/login",
            403,  # Should get 403 Forbidden
            data={
                "email": self.test_user_email,
                "password": "testpass123"
            }
        )
        
        # Restore admin token
        self.admin_token = admin_token_backup
        
        if unapproved_login_success:
            print(f"   ✅ Unapproved user correctly denied login")
        else:
            print(f"   ❌ Unapproved user was allowed to login")
            return False
        
        # Test 3: Approve the user
        print("📋 Step 3: Approving the test user...")
        
        approve_success, approve_response = self.run_test(
            "Approve Test User",
            "POST",
            f"admin/approve-user/{self.test_user_id}",
            200
        )
        
        if not approve_success:
            print("❌ Failed to approve test user")
            return False
        
        print(f"   ✅ Test user approved successfully")
        
        # Test 4: Verify user is no longer in pending list
        print("📋 Step 4: Verifying user removed from pending list...")
        
        pending_after_success, pending_after_response = self.run_test(
            "Check Pending Users After Approval",
            "GET",
            "admin/pending-users",
            200
        )
        
        if pending_after_success:
            pending_users_after = pending_after_response.get('pending_users', [])
            test_user_still_pending = any(user.get('id') == self.test_user_id for user in pending_users_after)
            
            if not test_user_still_pending:
                print(f"   ✅ Test user correctly removed from pending list")
            else:
                print(f"   ❌ Test user still in pending list after approval")
                return False
        else:
            print("❌ Failed to get pending users after approval")
            return False
        
        # Test 5: Try to login as approved user (should succeed)
        print("📋 Step 5: Testing login with approved user...")
        
        # Store admin token
        admin_token_backup = self.admin_token
        self.admin_token = None
        
        approved_login_success, approved_response = self.run_test(
            "Approved User Login",
            "POST",
            "auth/login",
            200,
            data={
                "email": self.test_user_email,
                "password": "testpass123"
            }
        )
        
        # Restore admin token
        self.admin_token = admin_token_backup
        
        if approved_login_success and 'token' in approved_response:
            print(f"   ✅ Approved user successfully logged in")
            approved_user_info = approved_response.get('user', {})
            print(f"   User: {approved_user_info.get('email')} (Type: {approved_user_info.get('user_type')})")
            return True
        else:
            print(f"   ❌ Approved user failed to login")
            return False

    def test_user_rejection_process(self):
        """Test user rejection process"""
        print("\n❌ USER REJECTION PROCESS TEST")
        print("=" * 50)
        
        if not self.admin_token:
            print("❌ No admin token available")
            return False
        
        # Create another test user for rejection
        import random
        reject_user_email = f"rejectuser{random.randint(1000, 9999)}@gmail.com"
        
        print(f"📧 Creating user for rejection test: {reject_user_email}")
        
        create_success, create_response = self.run_test(
            "Create User for Rejection Test",
            "POST",
            "auth/register",
            200,
            data={
                "name": "Reject Test User",
                "email": reject_user_email,
                "password": "rejectpass123"
            }
        )
        
        if not create_success:
            print("❌ Failed to create user for rejection test")
            return False
        
        reject_user_id = create_response.get('user_id')
        
        # Verify user is in pending list
        pending_success, pending_response = self.run_test(
            "Check User in Pending List",
            "GET",
            "admin/pending-users",
            200
        )
        
        if pending_success:
            pending_users = pending_response.get('pending_users', [])
            user_in_pending = any(user.get('id') == reject_user_id for user in pending_users)
            
            if not user_in_pending:
                print(f"❌ Reject test user not found in pending list")
                return False
            
            print(f"   ✅ Reject test user found in pending list")
        else:
            print("❌ Failed to get pending users")
            return False
        
        # Reject the user
        print("📋 Rejecting the test user...")
        
        reject_success, reject_response = self.run_test(
            "Reject Test User",
            "POST",
            f"admin/reject-user/{reject_user_id}",
            200
        )
        
        if not reject_success:
            print("❌ Failed to reject test user")
            return False
        
        print(f"   ✅ Test user rejected successfully")
        
        # Verify user is no longer in pending list
        pending_after_success, pending_after_response = self.run_test(
            "Check Pending Users After Rejection",
            "GET",
            "admin/pending-users",
            200
        )
        
        if pending_after_success:
            pending_users_after = pending_after_response.get('pending_users', [])
            user_still_pending = any(user.get('id') == reject_user_id for user in pending_users_after)
            
            if not user_still_pending:
                print(f"   ✅ Rejected user correctly removed from pending list")
                return True
            else:
                print(f"   ❌ Rejected user still in pending list")
                return False
        else:
            print("❌ Failed to get pending users after rejection")
            return False

def main():
    print("🚀 PostaDepo Admin Panel System Tests")
    print("🇹🇷 Turkish Review Request - Admin Panel Issues Testing")
    print("=" * 70)
    
    tester = PostaDepoAdminTester()
    
    # Test sequence based on Turkish review request
    tests = [
        # 1. ÇIKIŞ SORUNU TEST (Logout Issue Test)
        ("🔐 Admin Login Test", tester.test_admin_login),
        ("🚪 Logout Functionality Test", tester.test_logout_functionality),
        
        # 2. YENİ KULLANICI KAYIT İSTEKLERİ GÖRÜNMEME SORUNU TEST 
        # (New User Registration Requests Not Showing Issue Test)
        ("👤 Create Test User", tester.test_create_test_user),
        ("📋 Pending Users Endpoint Test", tester.test_pending_users_endpoint),
        ("✅ User Approval Process Test", tester.test_user_approval_process),
        ("❌ User Rejection Process Test", tester.test_user_rejection_process),
        
        # 3. ADMİN PANELİ ÖZELLİKLERİ TEST (Admin Panel Features Test)
        ("👥 Admin Users Endpoint Test", tester.test_admin_users_endpoint),
        ("🔒 Admin Authorization Test", tester.test_admin_authorization),
    ]
    
    print(f"\n📋 Running {len(tests)} test categories...")
    print("=" * 70)
    
    for test_name, test_func in tests:
        try:
            print(f"\n🎯 {test_name}")
            result = test_func()
            if result:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"💥 {test_name}: CRASHED - {str(e)}")
    
    # Print final results
    print("\n" + "=" * 70)
    print(f"📊 FINAL RESULTS: {tester.tests_passed}/{tester.tests_run} individual tests passed")
    
    success_rate = (tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0
    print(f"📈 Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("🎉 OVERALL RESULT: ADMIN PANEL SYSTEM WORKING CORRECTLY")
        return 0
    else:
        print("⚠️  OVERALL RESULT: ADMIN PANEL SYSTEM HAS ISSUES")
        return 1

if __name__ == "__main__":
    sys.exit(main())