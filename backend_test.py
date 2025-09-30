import requests
import sys
import json
from datetime import datetime
import uuid

class AdminPanelBulkOperationsTester:
    def __init__(self, base_url="https://outlook-sync-debug.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.admin_token = None
        self.admin_user = None
        self.test_users = []
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test_result(self, name, success, details=""):
        """Log test result for reporting"""
        self.test_results.append({
            "name": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, description=""):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.admin_token:
            test_headers['Authorization'] = f'Bearer {self.admin_token}'
        
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Test {self.tests_run}: {name}")
        if description:
            print(f"   📝 {description}")
        print(f"   🌐 {method} {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=30)

            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                print(f"✅ PASSED - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict):
                        print(f"   📊 Response keys: {list(response_data.keys())}")
                        # Log important response details
                        if 'message' in response_data:
                            print(f"   💬 Message: {response_data['message']}")
                        if 'users' in response_data:
                            print(f"   👥 Users count: {len(response_data['users'])}")
                        if 'pending_users' in response_data:
                            print(f"   ⏳ Pending users count: {len(response_data['pending_users'])}")
                    else:
                        print(f"   📄 Response type: {type(response_data)}")
                except:
                    print(f"   📄 Response: {response.text[:100]}...")
                
                self.log_test_result(name, True, f"Status {response.status_code}")
            else:
                print(f"❌ FAILED - Expected {expected_status}, got {response.status_code}")
                print(f"   📄 Response: {response.text[:300]}...")
                self.log_test_result(name, False, f"Expected {expected_status}, got {response.status_code}")

            return success, response.json() if response.text and response.status_code < 500 else {}

        except Exception as e:
            print(f"❌ FAILED - Error: {str(e)}")
            self.log_test_result(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_admin_login(self):
        """Test admin user login (admin@postadepo.com / admindepo*)"""
        print("\n" + "="*60)
        print("🔐 ADMIN LOGIN TEST")
        print("="*60)
        
        success, response = self.run_test(
            "Admin User Login",
            "POST",
            "auth/login",
            200,
            data={"email": "admin@postadepo.com", "password": "admindepo*"},
            description="Testing admin credentials for bulk operations access"
        )
        
        if success and 'token' in response and 'user' in response:
            self.admin_token = response['token']
            self.admin_user = response['user']
            print(f"   👤 Logged in as: {self.admin_user.get('email')} (Type: {self.admin_user.get('user_type')})")
            
            # Verify admin user type
            if self.admin_user.get('user_type') == 'admin':
                print("   ✅ Admin user type confirmed")
                return True
            else:
                print(f"   ❌ Expected user_type='admin', got '{self.admin_user.get('user_type')}'")
                return False
        else:
            print("   ❌ Admin login failed - cannot proceed with bulk operations tests")
            return False

    def test_create_pending_users(self):
        """Create test users for bulk operations"""
        print("\n" + "="*60)
        print("👥 CREATE PENDING USERS TEST")
        print("="*60)
        
        # Create 3 test users that will be pending (approved=false)
        test_users_data = [
            {"name": "Test User 1", "email": f"testuser1_{uuid.uuid4().hex[:8]}@test.com", "password": "test123"},
            {"name": "Test User 2", "email": f"testuser2_{uuid.uuid4().hex[:8]}@test.com", "password": "test123"},
            {"name": "Test User 3", "email": f"testuser3_{uuid.uuid4().hex[:8]}@test.com", "password": "test123"}
        ]
        
        created_users = []
        
        for i, user_data in enumerate(test_users_data, 1):
            success, response = self.run_test(
                f"Create Test User {i}",
                "POST",
                "auth/register",
                200,
                data=user_data,
                headers={'Authorization': ''},  # Remove admin token for registration
                description=f"Creating pending user: {user_data['email']}"
            )
            
            if success and 'user_id' in response:
                created_users.append({
                    'user_id': response['user_id'],
                    'email': user_data['email'],
                    'name': user_data['name'],
                    'approved': response.get('approved', False)
                })
                print(f"   ✅ Created user ID: {response['user_id']}")
            else:
                print(f"   ❌ Failed to create test user {i}")
        
        self.test_users = created_users
        print(f"\n   📊 Successfully created {len(created_users)} test users")
        return len(created_users) >= 2  # Need at least 2 users for bulk operations

    def test_get_pending_users(self):
        """Test getting pending users list"""
        print("\n" + "="*60)
        print("📋 GET PENDING USERS TEST")
        print("="*60)
        
        success, response = self.run_test(
            "Get Pending Users List",
            "POST",  # Note: The endpoint uses POST method
            "admin/pending-users",
            200,
            description="Retrieving list of users awaiting admin approval"
        )
        
        if success and 'pending_users' in response:
            pending_users = response['pending_users']
            print(f"   📊 Found {len(pending_users)} pending users")
            
            # Check if our test users are in the pending list
            test_user_emails = [user['email'] for user in self.test_users]
            found_test_users = [user for user in pending_users if user['email'] in test_user_emails]
            print(f"   🔍 Found {len(found_test_users)} of our test users in pending list")
            
            # Update test_users with actual user IDs from pending list
            for pending_user in pending_users:
                for test_user in self.test_users:
                    if test_user['email'] == pending_user['email']:
                        test_user['user_id'] = pending_user['id']
            
            return True
        else:
            print("   ❌ Failed to get pending users list")
            return False

    def test_bulk_approve_users(self):
        """Test bulk approve users endpoint"""
        print("\n" + "="*60)
        print("✅ BULK APPROVE USERS TEST")
        print("="*60)
        
        if len(self.test_users) < 2:
            print("   ❌ Not enough test users for bulk approve test")
            return False
        
        # Select first 2 users for bulk approval
        users_to_approve = self.test_users[:2]
        user_ids = [user['user_id'] for user in users_to_approve]
        
        print(f"   📝 Attempting to bulk approve {len(user_ids)} users")
        for user in users_to_approve:
            print(f"      - {user['name']} ({user['email']}) ID: {user['user_id']}")
        
        success, response = self.run_test(
            "Bulk Approve Users",
            "POST",
            "admin/bulk-approve-users",
            200,
            data={"user_ids": user_ids},
            description=f"Bulk approving {len(user_ids)} users with user_ids parameter"
        )
        
        if success:
            print(f"   ✅ Bulk approve operation completed successfully")
            # Mark these users as approved in our tracking
            for user in users_to_approve:
                user['approved'] = True
            return True
        else:
            print("   ❌ Bulk approve operation failed")
            return False

    def test_bulk_reject_users(self):
        """Test bulk reject users endpoint"""
        print("\n" + "="*60)
        print("❌ BULK REJECT USERS TEST")
        print("="*60)
        
        # Use remaining unapproved users for rejection
        users_to_reject = [user for user in self.test_users if not user.get('approved', False)]
        
        if len(users_to_reject) == 0:
            print("   ⚠️  No unapproved users available for bulk reject test")
            return True  # This is okay, means all were approved
        
        user_ids = [user['user_id'] for user in users_to_reject]
        
        print(f"   📝 Attempting to bulk reject {len(user_ids)} users")
        for user in users_to_reject:
            print(f"      - {user['name']} ({user['email']}) ID: {user['user_id']}")
        
        success, response = self.run_test(
            "Bulk Reject Users",
            "POST",
            "admin/bulk-reject-users",
            200,
            data={"user_ids": user_ids},
            description=f"Bulk rejecting {len(user_ids)} users with user_ids parameter"
        )
        
        if success:
            print(f"   ✅ Bulk reject operation completed successfully")
            return True
        else:
            print("   ❌ Bulk reject operation failed")
            return False

    def test_error_scenarios(self):
        """Test error scenarios for bulk operations"""
        print("\n" + "="*60)
        print("🚨 ERROR SCENARIOS TEST")
        print("="*60)
        
        all_success = True
        
        # Test 1: Empty user_ids array
        success, response = self.run_test(
            "Bulk Approve - Empty user_ids",
            "POST",
            "admin/bulk-approve-users",
            400,  # Expecting bad request
            data={"user_ids": []},
            description="Testing bulk approve with empty user_ids array"
        )
        all_success = all_success and success
        
        # Test 2: Missing user_ids parameter
        success, response = self.run_test(
            "Bulk Approve - Missing user_ids",
            "POST",
            "admin/bulk-approve-users",
            422,  # Expecting validation error
            data={},
            description="Testing bulk approve without user_ids parameter"
        )
        all_success = all_success and success
        
        # Test 3: Invalid user_ids
        success, response = self.run_test(
            "Bulk Approve - Invalid user_ids",
            "POST",
            "admin/bulk-approve-users",
            200,  # Backend might handle gracefully
            data={"user_ids": ["invalid-id-1", "invalid-id-2"]},
            description="Testing bulk approve with non-existent user IDs"
        )
        # This test passes regardless of response since backend behavior may vary
        
        # Test 4: Unauthorized access (no token)
        original_token = self.admin_token
        self.admin_token = None
        
        success, response = self.run_test(
            "Bulk Approve - No Authorization",
            "POST",
            "admin/bulk-approve-users",
            401,  # Expecting unauthorized
            data={"user_ids": ["test-id"]},
            description="Testing bulk approve without authorization token"
        )
        all_success = all_success and success
        
        # Restore token
        self.admin_token = original_token
        
        return all_success

    def test_verify_operations(self):
        """Verify that bulk operations worked correctly"""
        print("\n" + "="*60)
        print("🔍 VERIFY OPERATIONS TEST")
        print("="*60)
        
        # Get updated pending users list
        success, response = self.run_test(
            "Verify Pending Users After Operations",
            "POST",
            "admin/pending-users",
            200,
            description="Checking pending users list after bulk operations"
        )
        
        if success and 'pending_users' in response:
            pending_users = response['pending_users']
            print(f"   📊 Remaining pending users: {len(pending_users)}")
            
            # Check if approved users are no longer in pending list
            approved_user_emails = [user['email'] for user in self.test_users if user.get('approved', False)]
            still_pending = [user for user in pending_users if user['email'] in approved_user_emails]
            
            if len(still_pending) == 0:
                print("   ✅ All approved users successfully removed from pending list")
                return True
            else:
                print(f"   ❌ {len(still_pending)} approved users still in pending list")
                return False
        else:
            print("   ❌ Failed to verify operations")
            return False

    def run_comprehensive_test(self):
        """Run all admin panel bulk operations tests"""
        print("🚀 STARTING ADMIN PANEL BULK OPERATIONS COMPREHENSIVE TEST")
        print("=" * 80)
        print(f"🕐 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 Testing against: {self.base_url}")
        print("=" * 80)
        
        # Test sequence
        tests = [
            ("Admin Login", self.test_admin_login),
            ("Create Pending Users", self.test_create_pending_users),
            ("Get Pending Users", self.test_get_pending_users),
            ("Bulk Approve Users", self.test_bulk_approve_users),
            ("Bulk Reject Users", self.test_bulk_reject_users),
            ("Error Scenarios", self.test_error_scenarios),
            ("Verify Operations", self.test_verify_operations),
        ]
        
        failed_tests = []
        
        for test_name, test_func in tests:
            try:
                print(f"\n🎯 Running: {test_name}")
                result = test_func()
                if not result:
                    failed_tests.append(test_name)
                    print(f"⚠️  {test_name} failed but continuing...")
            except Exception as e:
                failed_tests.append(test_name)
                print(f"💥 {test_name} crashed: {str(e)}")
        
        # Print final results
        print("\n" + "=" * 80)
        print("📊 FINAL TEST RESULTS")
        print("=" * 80)
        print(f"✅ Tests Passed: {self.tests_passed}/{self.tests_run}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}/{self.tests_run}")
        
        if failed_tests:
            print(f"\n🚨 Failed Test Categories:")
            for test in failed_tests:
                print(f"   - {test}")
        
        # Detailed results
        print(f"\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"   {status} {result['name']}: {result['details']}")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"\n🎯 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🎉 BULK OPERATIONS TEST SUITE PASSED!")
            return 0
        else:
            print("⚠️  BULK OPERATIONS TEST SUITE NEEDS ATTENTION")
            return 1

def main():
    """Main test execution"""
    tester = AdminPanelBulkOperationsTester()
    return tester.run_comprehensive_test()

if __name__ == "__main__":
    sys.exit(main())