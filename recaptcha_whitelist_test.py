import requests
import sys
import json
from datetime import datetime
import uuid

class PostaDepoRecaptchaWhitelistTester:
    def __init__(self, base_url="https://user-role-redirect.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.user = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_user_id = None
        self.test_user_email = f"testuser_{uuid.uuid4().hex[:8]}@example.com"

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
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
                    if isinstance(response_data, dict) and 'message' in response_data:
                        print(f"   Message: {response_data['message']}")
                except:
                    print(f"   Response: {response.text[:100]}...")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")

            return success, response.json() if response.text and response.status_code < 500 else {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_recaptcha_verification_valid_token(self):
        """Test reCAPTCHA verification with valid token (simulated)"""
        # Note: In real testing, this would use a valid reCAPTCHA token
        # For testing purposes, we'll use a mock token
        success, response = self.run_test(
            "reCAPTCHA Verification - Valid Token",
            "POST",
            "verify-recaptcha",
            200,
            data={"recaptcha_token": "valid_test_token_simulation"}
        )
        
        if success:
            success_status = response.get('success', False)
            message = response.get('message', '')
            print(f"   Verification success: {success_status}")
            print(f"   Message: {message}")
        
        return success

    def test_recaptcha_verification_empty_token(self):
        """Test reCAPTCHA verification with empty token"""
        success, response = self.run_test(
            "reCAPTCHA Verification - Empty Token",
            "POST",
            "verify-recaptcha",
            400,
            data={"recaptcha_token": ""}
        )
        return success

    def test_recaptcha_verification_no_token(self):
        """Test reCAPTCHA verification without token field"""
        success, response = self.run_test(
            "reCAPTCHA Verification - No Token Field",
            "POST",
            "verify-recaptcha",
            422,  # Pydantic validation error
            data={}
        )
        return success

    def test_recaptcha_verification_invalid_token(self):
        """Test reCAPTCHA verification with invalid token"""
        success, response = self.run_test(
            "reCAPTCHA Verification - Invalid Token",
            "POST",
            "verify-recaptcha",
            200,  # API returns 200 but success=false
            data={"recaptcha_token": "invalid_token_12345"}
        )
        
        if success:
            success_status = response.get('success', False)
            message = response.get('message', '')
            print(f"   Verification success: {success_status}")
            print(f"   Message: {message}")
            # For invalid token, success should be False
            if not success_status:
                print("   ✅ Correctly rejected invalid token")
            else:
                print("   ⚠️  Invalid token was accepted (unexpected)")
        
        return success

    def test_user_registration_new_user(self):
        """Test user registration with new user"""
        success, response = self.run_test(
            "User Registration - New User",
            "POST",
            "auth/register",
            200,
            data={
                "name": "Test User",
                "email": self.test_user_email,
                "password": "testpassword123"
            }
        )
        
        if success:
            self.test_user_id = response.get('user_id')
            approved = response.get('approved', True)  # Should be False for new users
            message = response.get('message', '')
            print(f"   User ID: {self.test_user_id}")
            print(f"   Approved status: {approved}")
            print(f"   Message: {message}")
            
            # Verify user is created with approved=False
            if not approved:
                print("   ✅ User correctly created with approved=False")
            else:
                print("   ⚠️  User was approved immediately (unexpected)")
        
        return success

    def test_user_registration_duplicate_email(self):
        """Test user registration with existing email"""
        success, response = self.run_test(
            "User Registration - Duplicate Email",
            "POST",
            "auth/register",
            400,
            data={
                "name": "Another Test User",
                "email": self.test_user_email,  # Same email as previous test
                "password": "anotherpassword123"
            }
        )
        return success

    def test_user_registration_invalid_data(self):
        """Test user registration with invalid data"""
        success, response = self.run_test(
            "User Registration - Invalid Email",
            "POST",
            "auth/register",
            422,  # Pydantic validation error
            data={
                "name": "Test User",
                "email": "invalid-email-format",
                "password": "testpassword123"
            }
        )
        return success

    def test_demo_user_login_auto_approved(self):
        """Test demo user login (should be auto-approved)"""
        success, response = self.run_test(
            "Demo User Login - Auto Approved",
            "POST",
            "auth/login",
            200,
            data={"email": "demo@postadepo.com", "password": "demo123"}
        )
        
        if success and 'token' in response and 'user' in response:
            self.token = response['token']
            self.user = response['user']
            print(f"   Logged in as: {self.user.get('email')}")
            print(f"   User ID: {self.user.get('id')}")
            return True
        return False

    def test_unapproved_user_login_attempt(self):
        """Test login attempt with unapproved user (should fail with 403)"""
        success, response = self.run_test(
            "Unapproved User Login Attempt",
            "POST",
            "auth/login",
            403,
            data={"email": self.test_user_email, "password": "testpassword123"}
        )
        
        if success:
            detail = response.get('detail', '')
            print(f"   Error detail: {detail}")
            if "onaylanmamış" in detail.lower() or "onay" in detail.lower():
                print("   ✅ Correctly blocked unapproved user")
            else:
                print("   ⚠️  Unexpected error message")
        
        return success

    def test_admin_get_pending_users(self):
        """Test admin endpoint to get pending users"""
        if not self.token:
            print("❌ No admin token available for pending users test")
            return False
            
        success, response = self.run_test(
            "Admin - Get Pending Users",
            "GET",
            "admin/pending-users",
            200
        )
        
        if success:
            pending_users = response.get('pending_users', [])
            print(f"   Found {len(pending_users)} pending users")
            
            # Check if our test user is in the list
            test_user_found = False
            for user in pending_users:
                if user.get('email') == self.test_user_email:
                    test_user_found = True
                    print(f"   ✅ Test user found in pending list: {user.get('name')} ({user.get('email')})")
                    break
            
            if not test_user_found and len(pending_users) == 0:
                print("   ℹ️  No pending users found (this is normal if no registrations occurred)")
            elif not test_user_found:
                print("   ⚠️  Test user not found in pending list")
        
        return success

    def test_admin_approve_user(self):
        """Test admin endpoint to approve a user"""
        if not self.token or not self.test_user_id:
            print("❌ No admin token or test user ID available for approval test")
            return False
            
        success, response = self.run_test(
            "Admin - Approve User",
            "POST",
            f"admin/approve-user/{self.test_user_id}",
            200
        )
        
        if success:
            message = response.get('message', '')
            user_id = response.get('user_id', '')
            print(f"   Message: {message}")
            print(f"   Approved user ID: {user_id}")
            
            if user_id == self.test_user_id:
                print("   ✅ User approval successful")
            else:
                print("   ⚠️  User ID mismatch in approval response")
        
        return success

    def test_approved_user_login_success(self):
        """Test login with approved user (should succeed)"""
        success, response = self.run_test(
            "Approved User Login - Success",
            "POST",
            "auth/login",
            200,
            data={"email": self.test_user_email, "password": "testpassword123"}
        )
        
        if success and 'token' in response and 'user' in response:
            user_data = response['user']
            print(f"   Successfully logged in as: {user_data.get('email')}")
            print(f"   User name: {user_data.get('name')}")
            print(f"   User ID: {user_data.get('id')}")
            return True
        return False

    def test_non_admin_access_to_admin_endpoints(self):
        """Test non-admin user trying to access admin endpoints"""
        # First, login as the test user (non-admin)
        login_success, login_response = self.run_test(
            "Non-Admin User Login for Admin Test",
            "POST",
            "auth/login",
            200,
            data={"email": self.test_user_email, "password": "testpassword123"}
        )
        
        if not login_success:
            print("❌ Could not login as test user for admin access test")
            return False
        
        # Store the non-admin token temporarily
        non_admin_token = login_response.get('token')
        original_token = self.token
        self.token = non_admin_token
        
        # Try to access admin endpoint
        success, response = self.run_test(
            "Non-Admin Access to Pending Users",
            "GET",
            "admin/pending-users",
            403
        )
        
        # Restore admin token
        self.token = original_token
        
        if success:
            detail = response.get('detail', '')
            print(f"   Error detail: {detail}")
            if "admin" in detail.lower() or "yetki" in detail.lower():
                print("   ✅ Correctly blocked non-admin access")
            else:
                print("   ⚠️  Unexpected error message")
        
        return success

    def test_admin_approve_nonexistent_user(self):
        """Test admin trying to approve non-existent user"""
        if not self.token:
            print("❌ No admin token available for non-existent user test")
            return False
            
        fake_user_id = "non-existent-user-id-12345"
        success, response = self.run_test(
            "Admin - Approve Non-existent User",
            "POST",
            f"admin/approve-user/{fake_user_id}",
            404
        )
        
        if success:
            detail = response.get('detail', '')
            print(f"   Error detail: {detail}")
            if "bulunamadı" in detail.lower() or "not found" in detail.lower():
                print("   ✅ Correctly returned 404 for non-existent user")
            else:
                print("   ⚠️  Unexpected error message")
        
        return success

    def test_invalid_login_credentials(self):
        """Test login with invalid credentials"""
        success, response = self.run_test(
            "Invalid Login Credentials",
            "POST",
            "auth/login",
            401,
            data={"email": "nonexistent@example.com", "password": "wrongpassword"}
        )
        
        if success:
            detail = response.get('detail', '')
            print(f"   Error detail: {detail}")
            if "geçersiz" in detail.lower() or "invalid" in detail.lower():
                print("   ✅ Correctly rejected invalid credentials")
            else:
                print("   ⚠️  Unexpected error message")
        
        return success

def main():
    print("🚀 Starting PostaDepo reCAPTCHA & Whitelist System Tests")
    print("=" * 60)
    
    tester = PostaDepoRecaptchaWhitelistTester()
    
    # Test sequence following the review request scenarios
    tests = [
        # reCAPTCHA Tests
        ("reCAPTCHA - Valid Token", tester.test_recaptcha_verification_valid_token),
        ("reCAPTCHA - Empty Token", tester.test_recaptcha_verification_empty_token),
        ("reCAPTCHA - No Token Field", tester.test_recaptcha_verification_no_token),
        ("reCAPTCHA - Invalid Token", tester.test_recaptcha_verification_invalid_token),
        
        # User Registration Tests
        ("Registration - New User", tester.test_user_registration_new_user),
        ("Registration - Duplicate Email", tester.test_user_registration_duplicate_email),
        ("Registration - Invalid Data", tester.test_user_registration_invalid_data),
        
        # Login and Whitelist Tests
        ("Demo User Login", tester.test_demo_user_login_auto_approved),
        ("Unapproved User Login", tester.test_unapproved_user_login_attempt),
        ("Invalid Login Credentials", tester.test_invalid_login_credentials),
        
        # Admin Endpoint Tests
        ("Admin - Get Pending Users", tester.test_admin_get_pending_users),
        ("Admin - Approve User", tester.test_admin_approve_user),
        ("Admin - Approve Non-existent User", tester.test_admin_approve_nonexistent_user),
        ("Non-Admin Access to Admin Endpoints", tester.test_non_admin_access_to_admin_endpoints),
        
        # Final Verification
        ("Approved User Login Success", tester.test_approved_user_login_success),
    ]
    
    failed_tests = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if not result:
                failed_tests.append(test_name)
                print(f"⚠️  {test_name} failed but continuing...")
        except Exception as e:
            failed_tests.append(test_name)
            print(f"💥 {test_name} crashed: {str(e)}")
    
    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if failed_tests:
        print(f"\n❌ Failed Tests ({len(failed_tests)}):")
        for test in failed_tests:
            print(f"   - {test}")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())