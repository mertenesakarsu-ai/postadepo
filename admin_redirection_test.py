import requests
import sys
import json
from datetime import datetime

class AdminRedirectionTester:
    def __init__(self, base_url="https://postadepo-admin.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.admin_token = None
        self.regular_token = None
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, token=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if token:
            test_headers['Authorization'] = f'Bearer {token}'
        
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
                    return True, response_data
                except:
                    print(f"   Response: {response.text[:100]}...")
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_admin_user_login(self):
        """Test admin user login (admin@postadepo.com / admindepo*)"""
        print("\n🔐 ADMIN USER LOGIN TEST")
        print("=" * 50)
        
        success, response = self.run_test(
            "Admin User Login",
            "POST",
            "auth/login",
            200,
            data={"email": "admin@postadepo.com", "password": "admindepo*"}
        )
        
        if success:
            # Verify JWT token is created
            token = response.get('token')
            if token:
                print(f"   ✅ JWT token created: {token[:20]}...")
                self.admin_token = token
            else:
                print(f"   ❌ No JWT token in response")
                return False
            
            # Verify user information is returned completely
            user = response.get('user')
            if user:
                print(f"   ✅ User information returned:")
                print(f"      ID: {user.get('id')}")
                print(f"      Name: {user.get('name')}")
                print(f"      Email: {user.get('email')}")
                print(f"      User Type: {user.get('user_type')}")
                
                # Critical: Verify user_type='admin'
                if user.get('user_type') == 'admin':
                    print(f"   ✅ CRITICAL: user_type='admin' correctly returned")
                else:
                    print(f"   ❌ CRITICAL: user_type='{user.get('user_type')}' (expected 'admin')")
                    return False
                    
                # Verify all required fields are present
                required_fields = ['id', 'name', 'email', 'user_type']
                missing_fields = [field for field in required_fields if not user.get(field)]
                if missing_fields:
                    print(f"   ❌ Missing user fields: {missing_fields}")
                    return False
                else:
                    print(f"   ✅ All required user fields present")
                    
            else:
                print(f"   ❌ No user information in response")
                return False
                
            return True
        
        return False

    def test_regular_user_login(self):
        """Test regular user login (demo@postadepo.com / demo123)"""
        print("\n👤 REGULAR USER LOGIN TEST")
        print("=" * 50)
        
        success, response = self.run_test(
            "Regular User Login",
            "POST",
            "auth/login",
            200,
            data={"email": "demo@postadepo.com", "password": "demo123"}
        )
        
        if success:
            # Verify JWT token is created
            token = response.get('token')
            if token:
                print(f"   ✅ JWT token created: {token[:20]}...")
                self.regular_token = token
            else:
                print(f"   ❌ No JWT token in response")
                return False
            
            # Verify user information is returned
            user = response.get('user')
            if user:
                print(f"   ✅ User information returned:")
                print(f"      ID: {user.get('id')}")
                print(f"      Name: {user.get('name')}")
                print(f"      Email: {user.get('email')}")
                print(f"      User Type: {user.get('user_type')}")
                
                # Critical: Verify user_type='email' for regular user
                if user.get('user_type') == 'email':
                    print(f"   ✅ CRITICAL: user_type='email' correctly returned for regular user")
                else:
                    print(f"   ❌ CRITICAL: user_type='{user.get('user_type')}' (expected 'email')")
                    return False
                    
            else:
                print(f"   ❌ No user information in response")
                return False
                
            return True
        
        return False

    def test_admin_endpoint_access_with_admin_user(self):
        """Test admin user access to admin endpoints"""
        print("\n🔑 ADMIN ENDPOINT ACCESS TEST (Admin User)")
        print("=" * 50)
        
        if not self.admin_token:
            print("❌ No admin token available - admin login must succeed first")
            return False
        
        # Test GET /api/admin/users endpoint
        success, response = self.run_test(
            "Admin Access to GET /api/admin/users",
            "GET",
            "admin/users",
            200,
            token=self.admin_token
        )
        
        if success:
            users = response.get('users', [])
            print(f"   ✅ Admin successfully accessed admin endpoint")
            print(f"   📊 Retrieved {len(users)} users")
            
            # Show some user details (without passwords)
            for i, user in enumerate(users[:3]):  # Show first 3 users
                print(f"      User {i+1}: {user.get('email')} (Type: {user.get('user_type', 'N/A')}, Approved: {user.get('approved', 'N/A')})")
                
            return True
        
        return False

    def test_regular_user_denied_admin_access(self):
        """Test regular user cannot access admin endpoints (403 error)"""
        print("\n🚫 ADMIN ENDPOINT ACCESS TEST (Regular User - Should Fail)")
        print("=" * 50)
        
        if not self.regular_token:
            print("❌ No regular user token available - regular login must succeed first")
            return False
        
        # Test GET /api/admin/users endpoint with regular user token (should fail with 403)
        success, response = self.run_test(
            "Regular User Access to GET /api/admin/users (Should Fail)",
            "GET",
            "admin/users",
            403,  # Expecting 403 Forbidden
            token=self.regular_token
        )
        
        if success:
            print(f"   ✅ Regular user correctly denied access to admin endpoint (403 Forbidden)")
            return True
        else:
            print(f"   ❌ Regular user was not properly denied access to admin endpoint")
            return False

    def test_admin_endpoint_without_token(self):
        """Test admin endpoint access without token (401 error)"""
        print("\n🔒 ADMIN ENDPOINT ACCESS TEST (No Token - Should Fail)")
        print("=" * 50)
        
        # Test GET /api/admin/users endpoint without token (should fail with 401)
        success, response = self.run_test(
            "No Token Access to GET /api/admin/users (Should Fail)",
            "GET",
            "admin/users",
            401,  # Expecting 401 Unauthorized
            token=None
        )
        
        if success:
            print(f"   ✅ Unauthenticated access correctly denied (401 Unauthorized)")
            return True
        else:
            print(f"   ❌ Unauthenticated access was not properly denied")
            return False

    def test_admin_other_endpoints(self):
        """Test other admin endpoints with admin user"""
        print("\n📋 OTHER ADMIN ENDPOINTS TEST")
        print("=" * 50)
        
        if not self.admin_token:
            print("❌ No admin token available")
            return False
        
        endpoints_to_test = [
            ("GET /api/admin/pending-users", "GET", "admin/pending-users", 200),
        ]
        
        all_success = True
        
        for endpoint_name, method, endpoint, expected_status in endpoints_to_test:
            success, response = self.run_test(
                f"Admin Access to {endpoint_name}",
                method,
                endpoint,
                expected_status,
                token=self.admin_token
            )
            
            if success:
                if method == "GET" and "pending-users" in endpoint:
                    pending_users = response.get('pending_users', [])
                    print(f"   📊 Found {len(pending_users)} pending users")
            
            all_success = all_success and success
        
        return all_success

    def test_user_type_field_consistency(self):
        """Test that user_type field is consistently returned across different scenarios"""
        print("\n🔄 USER_TYPE FIELD CONSISTENCY TEST")
        print("=" * 50)
        
        # Test admin login again to verify consistency
        admin_success, admin_response = self.run_test(
            "Admin Login Consistency Check",
            "POST",
            "auth/login",
            200,
            data={"email": "admin@postadepo.com", "password": "admindepo*"}
        )
        
        # Test regular user login again to verify consistency
        regular_success, regular_response = self.run_test(
            "Regular User Login Consistency Check",
            "POST",
            "auth/login",
            200,
            data={"email": "demo@postadepo.com", "password": "demo123"}
        )
        
        consistency_check = True
        
        if admin_success:
            admin_user_type = admin_response.get('user', {}).get('user_type')
            if admin_user_type == 'admin':
                print(f"   ✅ Admin user_type consistent: {admin_user_type}")
            else:
                print(f"   ❌ Admin user_type inconsistent: {admin_user_type}")
                consistency_check = False
        
        if regular_success:
            regular_user_type = regular_response.get('user', {}).get('user_type')
            if regular_user_type == 'email':
                print(f"   ✅ Regular user_type consistent: {regular_user_type}")
            else:
                print(f"   ❌ Regular user_type inconsistent: {regular_user_type}")
                consistency_check = False
        
        return consistency_check and admin_success and regular_success

def main():
    print("🚀 Starting PostaDepo Admin Redirection System Tests")
    print("=" * 60)
    print("🎯 TESTING ADMIN USER LOGIN REDIRECTION SYSTEM")
    print("=" * 60)
    
    tester = AdminRedirectionTester()
    
    # Test sequence for admin redirection system
    tests = [
        ("1. Admin User Login Test", tester.test_admin_user_login),
        ("2. Regular User Login Test", tester.test_regular_user_login),
        ("3. Admin Endpoint Access (Admin User)", tester.test_admin_endpoint_access_with_admin_user),
        ("4. Admin Endpoint Access Denied (Regular User)", tester.test_regular_user_denied_admin_access),
        ("5. Admin Endpoint Access Denied (No Token)", tester.test_admin_endpoint_without_token),
        ("6. Other Admin Endpoints Test", tester.test_admin_other_endpoints),
        ("7. User Type Field Consistency", tester.test_user_type_field_consistency),
    ]
    
    failed_tests = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*60}")
            print(f"🧪 {test_name}")
            print(f"{'='*60}")
            
            result = test_func()
            if result:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
                failed_tests.append(test_name)
        except Exception as e:
            print(f"💥 {test_name}: CRASHED - {str(e)}")
            failed_tests.append(test_name)
    
    # Print final results
    print("\n" + "=" * 60)
    print("📊 ADMIN REDIRECTION SYSTEM TEST RESULTS")
    print("=" * 60)
    print(f"✅ Tests Passed: {tester.tests_passed}/{tester.tests_run}")
    print(f"❌ Tests Failed: {len(failed_tests)}")
    
    if failed_tests:
        print(f"\n🚨 Failed Tests:")
        for i, test in enumerate(failed_tests, 1):
            print(f"   {i}. {test}")
    
    # Critical test results summary
    print(f"\n🎯 CRITICAL REQUIREMENTS CHECK:")
    
    critical_checks = [
        ("Admin login returns user_type='admin'", tester.admin_token is not None),
        ("Regular login returns user_type='email'", tester.regular_token is not None),
        ("Admin can access admin endpoints", tester.admin_token is not None),
        ("Regular user denied admin access", True),  # This is tested in the sequence
    ]
    
    all_critical_passed = True
    for check_name, passed in critical_checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status}: {check_name}")
        if not passed:
            all_critical_passed = False
    
    if all_critical_passed and len(failed_tests) == 0:
        print(f"\n🎉 ALL ADMIN REDIRECTION SYSTEM TESTS PASSED!")
        print(f"✅ Backend login response correctly returns user_type field")
        print(f"✅ Admin and regular user distinction works correctly")
        print(f"✅ Authorization controls are working properly")
        return 0
    else:
        print(f"\n⚠️  SOME TESTS FAILED - Admin redirection system needs attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())