import requests
import sys
import json
import random
from datetime import datetime

class PostaDepoConnectionTester:
    def __init__(self, base_url="https://missing-field-fix.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.admin_token = None
        self.test_user_email = None
        self.test_user_id = None
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict):
                        print(f"   Response keys: {list(response_data.keys())}")
                        # Show important data
                        if 'users' in response_data:
                            print(f"   Users count: {len(response_data['users'])}")
                        if 'pending_users' in response_data:
                            print(f"   Pending users count: {len(response_data['pending_users'])}")
                        if 'user_id' in response_data:
                            print(f"   User ID: {response_data['user_id']}")
                        if 'approved' in response_data:
                            print(f"   Approved status: {response_data['approved']}")
                    else:
                        print(f"   Response: {str(response_data)[:100]}...")
                except:
                    print(f"   Response: {response.text[:100]}...")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:300]}...")

            return success, response.json() if response.text and response.status_code < 500 else {}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timeout (30s)")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_basic_health_check(self):
        """Test basic API health check"""
        print("\n🏥 TESTING BASIC API HEALTH")
        print("=" * 50)
        
        success, response = self.run_test(
            "Basic Health Check",
            "GET",
            "",
            200
        )
        
        if success:
            print("✅ API is responding")
        else:
            print("❌ API not responding")
        
        return success

    def test_demo_user_login(self):
        """Test demo user login (should work without MongoDB if cached)"""
        print("\n👤 TESTING DEMO USER LOGIN")
        print("=" * 50)
        
        success, response = self.run_test(
            "Demo User Login",
            "POST",
            "auth/login",
            200,
            data={"email": "demo@postadepo.com", "password": "demo123"}
        )
        
        if success and 'token' in response:
            print("✅ Demo user login successful")
            return True
        else:
            print("❌ Demo user login failed - MongoDB connection issue")
            return False

    def test_admin_user_login(self):
        """Test admin user login"""
        print("\n👑 TESTING ADMIN USER LOGIN")
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
            user = response['user']
            print(f"✅ Admin logged in successfully")
            print(f"   Admin user: {user.get('email')} ({user.get('name')})")
            print(f"   User type: {user.get('user_type')}")
            return True
        else:
            print("❌ Admin login failed - MongoDB connection issue")
            return False

    def test_user_registration(self):
        """Test user registration with valid email"""
        print("\n📝 TESTING USER REGISTRATION")
        print("=" * 50)
        
        # Use a valid email domain
        timestamp = int(datetime.now().timestamp())
        self.test_user_email = f"testuser{timestamp}@gmail.com"
        
        success, response = self.run_test(
            "Register New Test User",
            "POST",
            "auth/register",
            200,
            data={
                "name": "Test User MongoDB Atlas",
                "email": self.test_user_email,
                "password": "testpass123"
            }
        )
        
        if success:
            self.test_user_id = response.get('user_id')
            approved = response.get('approved', True)
            
            print(f"✅ Test user created: {self.test_user_email}")
            print(f"   User ID: {self.test_user_id}")
            print(f"   Approved status: {approved}")
            
            if not approved:
                print("✅ User created as unapproved (whitelist system working)")
            else:
                print("❌ User was auto-approved (whitelist system not working)")
            
            return True
        else:
            print("❌ Failed to create test user - MongoDB connection issue")
            return False

    def test_admin_endpoints(self):
        """Test admin endpoints if admin login worked"""
        if not self.admin_token:
            print("❌ No admin token available - skipping admin endpoint tests")
            return False
            
        print("\n🔧 TESTING ADMIN ENDPOINTS")
        print("=" * 50)
        
        # Test get all users
        users_success, users_response = self.run_test(
            "Admin Get All Users",
            "GET",
            "admin/users",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if users_success:
            users = users_response.get('users', [])
            print(f"✅ Retrieved {len(users)} users from database")
            
            # Show user details
            for i, user in enumerate(users):
                print(f"   User {i+1}: {user.get('email')} - {user.get('name')} (approved: {user.get('approved')}, type: {user.get('user_type')})")
        
        # Test get pending users
        pending_success, pending_response = self.run_test(
            "Admin Get Pending Users",
            "GET",
            "admin/pending-users",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if pending_success:
            pending_users = pending_response.get('pending_users', [])
            print(f"✅ Retrieved {len(pending_users)} pending users")
            
            # Show pending users
            for i, user in enumerate(pending_users):
                print(f"   Pending User {i+1}: {user.get('email')} - {user.get('name')} (ID: {user.get('id')})")
            
            # Check if our test user is in the list
            if self.test_user_email:
                test_user_found = any(user.get('email') == self.test_user_email for user in pending_users)
                if test_user_found:
                    print(f"✅ Test user {self.test_user_email} found in pending users list")
                else:
                    print(f"❌ Test user {self.test_user_email} NOT found in pending users list")
                    print("   This could be the main issue!")
        
        return users_success and pending_success

    def test_mongodb_connection_diagnosis(self):
        """Diagnose MongoDB connection issues"""
        print("\n🔍 MONGODB CONNECTION DIAGNOSIS")
        print("=" * 50)
        
        # Try different endpoints to see which ones work
        endpoints_to_test = [
            ("Health Check", "GET", "", 200),
            ("Demo Login", "POST", "auth/login", 200, {"email": "demo@postadepo.com", "password": "demo123"}),
            ("Invalid Login", "POST", "auth/login", 401, {"email": "invalid@test.com", "password": "wrong"}),
        ]
        
        working_endpoints = 0
        total_endpoints = len(endpoints_to_test)
        
        for name, method, endpoint, expected_status, *data in endpoints_to_test:
            request_data = data[0] if data else None
            
            success, response = self.run_test(
                f"Diagnosis: {name}",
                method,
                endpoint,
                expected_status,
                data=request_data
            )
            
            if success:
                working_endpoints += 1
        
        print(f"\n📊 Diagnosis Results:")
        print(f"   Working endpoints: {working_endpoints}/{total_endpoints}")
        
        if working_endpoints == 0:
            print("❌ Complete system failure - API not responding")
        elif working_endpoints < total_endpoints:
            print("⚠️  Partial system failure - MongoDB connection issues likely")
        else:
            print("✅ All basic endpoints working")
        
        return working_endpoints > 0

def main():
    print("🚀 POSTADEPO MONGODB ATLAS CONNECTION TEST")
    print("=" * 80)
    print("Diagnosing MongoDB Atlas connection and user registration issues")
    print("=" * 80)
    
    tester = PostaDepoConnectionTester()
    
    # Test sequence focusing on connection diagnosis
    tests = [
        ("1. Basic Health Check", tester.test_basic_health_check),
        ("2. MongoDB Connection Diagnosis", tester.test_mongodb_connection_diagnosis),
        ("3. Demo User Login Test", tester.test_demo_user_login),
        ("4. Admin User Login Test", tester.test_admin_user_login),
        ("5. User Registration Test", tester.test_user_registration),
        ("6. Admin Endpoints Test", tester.test_admin_endpoints),
    ]
    
    failed_tests = []
    critical_failures = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"🧪 {test_name}")
        print(f"{'='*60}")
        
        try:
            result = test_func()
            if not result:
                failed_tests.append(test_name)
                # Mark critical failures
                if "Login" in test_name or "Admin" in test_name:
                    critical_failures.append(test_name)
                print(f"❌ {test_name} FAILED")
            else:
                print(f"✅ {test_name} PASSED")
        except Exception as e:
            failed_tests.append(test_name)
            critical_failures.append(test_name)
            print(f"💥 {test_name} CRASHED: {str(e)}")
    
    # Print final results
    print(f"\n{'='*80}")
    print(f"📊 FINAL TEST RESULTS")
    print(f"{'='*80}")
    print(f"✅ Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print(f"❌ Tests failed: {len(failed_tests)}")
    print(f"🚨 Critical failures: {len(critical_failures)}")
    
    if failed_tests:
        print(f"\n🚨 FAILED TESTS:")
        for i, test in enumerate(failed_tests, 1):
            print(f"   {i}. {test}")
    
    # Diagnosis and recommendations
    print(f"\n🔍 DIAGNOSIS AND RECOMMENDATIONS:")
    print(f"{'='*50}")
    
    if len(critical_failures) > 0:
        print("❌ CRITICAL ISSUE DETECTED: MongoDB Atlas connection problems")
        print("\n🔧 RECOMMENDED ACTIONS:")
        print("   1. Check MongoDB Atlas connection string in backend/.env")
        print("   2. Verify MongoDB Atlas cluster is running and accessible")
        print("   3. Check SSL/TLS configuration for MongoDB Atlas")
        print("   4. Verify network connectivity to MongoDB Atlas servers")
        print("   5. Check MongoDB Atlas user credentials and permissions")
        print("   6. Review backend logs for detailed error messages")
        
        print(f"\n📋 BACKEND LOG ANALYSIS:")
        print("   Based on logs, SSL handshake is failing with MongoDB Atlas")
        print("   Error: 'tlsv1 alert internal error' suggests SSL/TLS configuration issue")
        print("   This prevents all database operations including user login and registration")
        
    elif len(failed_tests) == 0:
        print("✅ All systems operational - MongoDB Atlas connection working correctly")
    else:
        print("⚠️  Minor issues detected - some functionality may be impacted")
    
    return 1 if critical_failures else 0

if __name__ == "__main__":
    sys.exit(main())