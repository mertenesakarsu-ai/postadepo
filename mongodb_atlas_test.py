import requests
import sys
import json
import random
from datetime import datetime

class MongoDBAtlasConnectionTester:
    def __init__(self, base_url="https://msgraph-oauth-fix.preview.emergentagent.com/api"):
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
                print(f"   Response: {response.text[:200]}...")

            return success, response.json() if response.text and response.status_code < 500 else {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_mongodb_atlas_connection(self):
        """Test 1: MongoDB Atlas Connection - Basic API Health Check"""
        print("\n🔗 TESTING MONGODB ATLAS CONNECTION")
        print("=" * 50)
        
        success, response = self.run_test(
            "MongoDB Atlas Connection Health Check",
            "GET",
            "",
            200
        )
        
        if success:
            print("✅ Backend is responding - MongoDB Atlas connection appears to be working")
        else:
            print("❌ Backend not responding - MongoDB Atlas connection may be broken")
        
        return success

    def test_admin_login(self):
        """Test 2: Admin Login with admin@postadepo.com / admindepo*"""
        print("\n👤 TESTING ADMIN LOGIN")
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
            print(f"✅ Admin logged in successfully")
            print(f"   Admin user: {user.get('email')} ({user.get('name')})")
            print(f"   User type: {user.get('user_type')}")
            print(f"   Token received: {self.admin_token[:20]}...")
            return True
        else:
            print("❌ Admin login failed")
            return False

    def test_admin_get_all_users(self):
        """Test 3: Get all users with admin credentials"""
        if not self.admin_token:
            print("❌ No admin token available")
            return False
            
        success, response = self.run_test(
            "Admin Get All Users",
            "GET",
            "admin/users",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success:
            users = response.get('users', [])
            print(f"✅ Retrieved {len(users)} users from MongoDB Atlas")
            
            # Show user details
            for i, user in enumerate(users):
                print(f"   User {i+1}: {user.get('email')} - {user.get('name')} (approved: {user.get('approved')}, type: {user.get('user_type')})")
                storage = user.get('storage_info', {})
                print(f"      Storage: {storage.get('totalEmails', 0)} emails, {storage.get('totalSize', 0)} bytes")
            
            # Check if admin user exists
            admin_users = [u for u in users if u.get('email') == 'admin@postadepo.com']
            if admin_users:
                print(f"✅ Admin user found in database: {admin_users[0].get('email')}")
            else:
                print("❌ Admin user not found in database")
            
            return True
        else:
            print("❌ Failed to get users - MongoDB Atlas query failed")
            return False

    def test_create_test_user(self):
        """Test 4: Create new test user to test registration approval system"""
        print("\n📝 TESTING USER REGISTRATION")
        print("=" * 50)
        
        # Generate unique test email
        timestamp = int(datetime.now().timestamp())
        self.test_user_email = f"testuser{timestamp}@postadepo.test"
        
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
                return True
            else:
                print("❌ User was auto-approved (whitelist system not working)")
                return False
        else:
            print("❌ Failed to create test user")
            return False

    def test_unapproved_user_login_attempt(self):
        """Test 5: Try to login with unapproved user (should fail)"""
        if not self.test_user_email:
            print("❌ No test user email available")
            return False
            
        success, response = self.run_test(
            "Unapproved User Login Attempt",
            "POST",
            "auth/login",
            403,  # Should be forbidden
            data={
                "email": self.test_user_email,
                "password": "testpass123"
            }
        )
        
        if success:
            print("✅ Unapproved user correctly rejected from login")
            return True
        else:
            print("❌ Unapproved user was allowed to login (security issue)")
            return False

    def test_admin_get_pending_users(self):
        """Test 6: Check if new user appears in pending users list"""
        if not self.admin_token:
            print("❌ No admin token available")
            return False
            
        success, response = self.run_test(
            "Admin Get Pending Users",
            "GET",
            "admin/pending-users",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success:
            pending_users = response.get('pending_users', [])
            print(f"✅ Retrieved {len(pending_users)} pending users")
            
            # Show pending users
            for i, user in enumerate(pending_users):
                print(f"   Pending User {i+1}: {user.get('email')} - {user.get('name')} (ID: {user.get('id')})")
            
            # Check if our test user is in the list
            if self.test_user_email:
                test_user_found = any(user.get('email') == self.test_user_email for user in pending_users)
                if test_user_found:
                    print(f"✅ Test user {self.test_user_email} found in pending users list")
                    return True
                else:
                    print(f"❌ Test user {self.test_user_email} NOT found in pending users list")
                    print("   This is the main issue - users not showing in admin panel!")
                    return False
            else:
                return len(pending_users) >= 0  # At least the endpoint works
        else:
            print("❌ Failed to get pending users")
            return False

    def test_admin_approve_user(self):
        """Test 7: Admin approves the test user"""
        if not self.admin_token or not self.test_user_id:
            print("❌ No admin token or test user ID available")
            return False
            
        success, response = self.run_test(
            "Admin Approve Test User",
            "POST",
            f"admin/approve-user/{self.test_user_id}",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success:
            print(f"✅ Test user {self.test_user_email} approved by admin")
            return True
        else:
            print("❌ Failed to approve test user")
            return False

    def test_approved_user_login(self):
        """Test 8: Try to login with newly approved user (should succeed)"""
        if not self.test_user_email:
            print("❌ No test user email available")
            return False
            
        success, response = self.run_test(
            "Approved User Login",
            "POST",
            "auth/login",
            200,
            data={
                "email": self.test_user_email,
                "password": "testpass123"
            }
        )
        
        if success and 'token' in response:
            user = response.get('user', {})
            print(f"✅ Approved user successfully logged in")
            print(f"   User: {user.get('email')} ({user.get('name')})")
            print(f"   Token received: {response['token'][:20]}...")
            return True
        else:
            print("❌ Approved user failed to login")
            return False

    def test_pending_users_after_approval(self):
        """Test 9: Check pending users list after approval (user should be removed)"""
        if not self.admin_token:
            print("❌ No admin token available")
            return False
            
        success, response = self.run_test(
            "Check Pending Users After Approval",
            "GET",
            "admin/pending-users",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success:
            pending_users = response.get('pending_users', [])
            print(f"✅ Retrieved {len(pending_users)} pending users after approval")
            
            # Check if our test user is still in the list (should not be)
            if self.test_user_email:
                test_user_found = any(user.get('email') == self.test_user_email for user in pending_users)
                if not test_user_found:
                    print(f"✅ Test user {self.test_user_email} correctly removed from pending list")
                    return True
                else:
                    print(f"❌ Test user {self.test_user_email} still in pending list after approval")
                    return False
            else:
                return True
        else:
            print("❌ Failed to get pending users after approval")
            return False

    def test_database_query_performance(self):
        """Test 10: Test database query performance with MongoDB Atlas"""
        if not self.admin_token:
            print("❌ No admin token available")
            return False
            
        print("\n⚡ TESTING DATABASE PERFORMANCE")
        print("=" * 50)
        
        import time
        
        # Test multiple queries to check performance
        queries = [
            ("Get All Users", "admin/users"),
            ("Get Pending Users", "admin/pending-users"),
            ("Get All Users Again", "admin/users")
        ]
        
        total_time = 0
        successful_queries = 0
        
        for query_name, endpoint in queries:
            start_time = time.time()
            
            success, response = self.run_test(
                f"Performance Test: {query_name}",
                "GET",
                endpoint,
                200,
                headers={'Authorization': f'Bearer {self.admin_token}'}
            )
            
            end_time = time.time()
            query_time = end_time - start_time
            total_time += query_time
            
            if success:
                successful_queries += 1
                print(f"   Query time: {query_time:.3f} seconds")
            else:
                print(f"   Query failed")
        
        avg_time = total_time / len(queries) if queries else 0
        print(f"\n📊 Performance Summary:")
        print(f"   Successful queries: {successful_queries}/{len(queries)}")
        print(f"   Average query time: {avg_time:.3f} seconds")
        print(f"   Total time: {total_time:.3f} seconds")
        
        # Performance is acceptable if queries complete in reasonable time
        performance_ok = avg_time < 5.0 and successful_queries == len(queries)
        
        if performance_ok:
            print("✅ MongoDB Atlas performance is acceptable")
        else:
            print("❌ MongoDB Atlas performance issues detected")
        
        return performance_ok

def main():
    print("🚀 POSTADEPO MONGODB ATLAS CONNECTION AND USER REGISTRATION APPROVAL TEST")
    print("=" * 80)
    print("Testing MongoDB Atlas connection and user registration approval system")
    print("Focus: Why user registration requests are not showing in admin panel")
    print("=" * 80)
    
    tester = MongoDBAtlasConnectionTester()
    
    # Test sequence focusing on the specific issues mentioned
    tests = [
        ("1. MongoDB Atlas Connection Test", tester.test_mongodb_atlas_connection),
        ("2. Admin Login Test", tester.test_admin_login),
        ("3. Admin Get All Users Test", tester.test_admin_get_all_users),
        ("4. Create New Test User", tester.test_create_test_user),
        ("5. Unapproved User Login Attempt", tester.test_unapproved_user_login_attempt),
        ("6. Admin Get Pending Users (MAIN ISSUE)", tester.test_admin_get_pending_users),
        ("7. Admin Approve User", tester.test_admin_approve_user),
        ("8. Approved User Login", tester.test_approved_user_login),
        ("9. Check Pending Users After Approval", tester.test_pending_users_after_approval),
        ("10. Database Performance Test", tester.test_database_query_performance),
    ]
    
    failed_tests = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"🧪 {test_name}")
        print(f"{'='*60}")
        
        try:
            result = test_func()
            if not result:
                failed_tests.append(test_name)
                print(f"❌ {test_name} FAILED")
            else:
                print(f"✅ {test_name} PASSED")
        except Exception as e:
            failed_tests.append(test_name)
            print(f"💥 {test_name} CRASHED: {str(e)}")
    
    # Print final results
    print(f"\n{'='*80}")
    print(f"📊 FINAL TEST RESULTS")
    print(f"{'='*80}")
    print(f"✅ Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print(f"❌ Tests failed: {len(failed_tests)}")
    
    if failed_tests:
        print(f"\n🚨 FAILED TESTS:")
        for i, test in enumerate(failed_tests, 1):
            print(f"   {i}. {test}")
    
    # Specific analysis for the main issue
    print(f"\n🔍 ANALYSIS FOR MAIN ISSUE:")
    print(f"{'='*50}")
    
    if "6. Admin Get Pending Users (MAIN ISSUE)" in failed_tests:
        print("❌ MAIN ISSUE CONFIRMED: User registration requests are not showing in admin panel")
        print("   Possible causes:")
        print("   - MongoDB Atlas query filtering issue")
        print("   - Database index problems")
        print("   - approved=false field not being set correctly")
        print("   - API endpoint logic error")
    else:
        print("✅ User registration approval system appears to be working correctly")
        print("   Users are showing in admin panel as expected")
    
    if tester.tests_passed == tester.tests_run:
        print("\n🎉 ALL TESTS PASSED - MongoDB Atlas migration successful!")
        return 0
    else:
        print(f"\n⚠️ {tester.tests_run - tester.tests_passed} TESTS FAILED - Issues found with MongoDB Atlas migration")
        return 1

if __name__ == "__main__":
    sys.exit(main())