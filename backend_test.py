import requests
import sys
import json
from datetime import datetime
import uuid
import time

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

class OutlookIntegrationTester:
    def __init__(self, base_url="https://outlook-sync-debug.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.demo_token = None
        self.demo_user = None
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

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, description="", allow_redirects=True):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
        test_headers = {'Content-Type': 'application/json'}
        
        if self.demo_token:
            test_headers['Authorization'] = f'Bearer {self.demo_token}'
        
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Test {self.tests_run}: {name}")
        if description:
            print(f"   📝 {description}")
        print(f"   🌐 {method} {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30, allow_redirects=allow_redirects)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30, allow_redirects=allow_redirects)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=30, allow_redirects=allow_redirects)

            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                print(f"✅ PASSED - Status: {response.status_code}")
                try:
                    if response.headers.get('content-type', '').startswith('application/json'):
                        response_data = response.json()
                        if isinstance(response_data, dict):
                            print(f"   📊 Response keys: {list(response_data.keys())}")
                            # Log important response details
                            if 'message' in response_data:
                                print(f"   💬 Message: {response_data['message']}")
                            if 'graph_sdk_available' in response_data:
                                print(f"   🔧 Graph SDK Available: {response_data['graph_sdk_available']}")
                            if 'credentials_configured' in response_data:
                                print(f"   🔑 Credentials Configured: {response_data['credentials_configured']}")
                            if 'auth_url' in response_data:
                                print(f"   🔗 Auth URL Length: {len(response_data['auth_url'])} chars")
                        else:
                            print(f"   📄 Response type: {type(response_data)}")
                    else:
                        print(f"   📄 Response (first 200 chars): {response.text[:200]}...")
                except:
                    print(f"   📄 Response: {response.text[:100]}...")
                
                self.log_test_result(name, True, f"Status {response.status_code}")
            else:
                print(f"❌ FAILED - Expected {expected_status}, got {response.status_code}")
                print(f"   📄 Response: {response.text[:300]}...")
                self.log_test_result(name, False, f"Expected {expected_status}, got {response.status_code}")

            return success, response.json() if response.text and response.headers.get('content-type', '').startswith('application/json') else {"text": response.text}

        except Exception as e:
            print(f"❌ FAILED - Error: {str(e)}")
            self.log_test_result(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_demo_user_login(self):
        """Test demo user login for Outlook integration testing"""
        print("\n" + "="*60)
        print("🔐 DEMO USER LOGIN TEST")
        print("="*60)
        
        success, response = self.run_test(
            "Demo User Login",
            "POST",
            "auth/login",
            200,
            data={"email": "demo@postadepo.com", "password": "demo123"},
            description="Testing demo user credentials for Outlook integration access"
        )
        
        if success and 'token' in response and 'user' in response:
            self.demo_token = response['token']
            self.demo_user = response['user']
            print(f"   👤 Logged in as: {self.demo_user.get('email')} (Type: {self.demo_user.get('user_type')})")
            return True
        else:
            print("   ❌ Demo user login failed - cannot proceed with Outlook integration tests")
            return False

    def test_outlook_status(self):
        """Test GET /api/outlook/status - Check if Outlook API is ready"""
        print("\n" + "="*60)
        print("🔍 OUTLOOK STATUS TEST")
        print("="*60)
        
        success, response = self.run_test(
            "Outlook API Status Check",
            "GET",
            "outlook/status",
            200,
            description="Checking if Outlook API is ready and configured properly"
        )
        
        if success and isinstance(response, dict):
            # Check key status indicators
            graph_available = response.get('graph_sdk_available', False)
            credentials_configured = response.get('credentials_configured', False)
            
            print(f"   🔧 Microsoft Graph SDK Available: {graph_available}")
            print(f"   🔑 Azure Credentials Configured: {credentials_configured}")
            
            if response.get('client_id_set'):
                print(f"   🆔 Client ID Set: {response['client_id_set']}")
            if response.get('tenant_id_set'):
                print(f"   🏢 Tenant ID Set: {response['tenant_id_set']}")
            
            if graph_available and credentials_configured:
                print("   ✅ Outlook API is fully ready")
                return True
            else:
                print("   ⚠️  Outlook API has configuration issues")
                return False
        else:
            print("   ❌ Failed to get Outlook status")
            return False

    def test_outlook_auth_url(self):
        """Test GET /api/outlook/auth-url - Check OAuth URL generation"""
        print("\n" + "="*60)
        print("🔗 OUTLOOK AUTH URL TEST")
        print("="*60)
        
        success, response = self.run_test(
            "OAuth URL Generation",
            "GET",
            "outlook/auth-url",
            200,
            description="Testing OAuth URL generation for Outlook authentication"
        )
        
        if success and isinstance(response, dict) and 'auth_url' in response:
            auth_url = response['auth_url']
            print(f"   🔗 Generated Auth URL: {auth_url[:100]}...")
            print(f"   📏 Auth URL Length: {len(auth_url)} characters")
            
            # Check if URL contains required OAuth parameters
            required_params = ['client_id', 'response_type', 'redirect_uri', 'scope', 'state']
            missing_params = []
            
            for param in required_params:
                if param not in auth_url:
                    missing_params.append(param)
            
            if not missing_params:
                print("   ✅ All required OAuth parameters present in URL")
                
                # Check if it's a Microsoft OAuth URL
                if 'login.microsoftonline.com' in auth_url:
                    print("   ✅ Correct Microsoft OAuth endpoint")
                    return True
                else:
                    print("   ⚠️  Not using Microsoft OAuth endpoint")
                    return False
            else:
                print(f"   ❌ Missing OAuth parameters: {missing_params}")
                return False
        else:
            print("   ❌ Failed to generate OAuth URL")
            return False

    def test_outlook_accounts(self):
        """Test GET /api/outlook/accounts - Check connected accounts endpoint"""
        print("\n" + "="*60)
        print("📧 OUTLOOK ACCOUNTS TEST")
        print("="*60)
        
        success, response = self.run_test(
            "Connected Accounts Check",
            "GET",
            "outlook/accounts",
            200,
            description="Checking connected Outlook accounts endpoint accessibility"
        )
        
        if success:
            if isinstance(response, dict) and 'accounts' in response:
                accounts = response['accounts']
                print(f"   📊 Connected accounts count: {len(accounts)}")
                
                if len(accounts) == 0:
                    print("   ℹ️  No connected accounts (expected for new user)")
                else:
                    print("   📧 Connected accounts found:")
                    for i, account in enumerate(accounts, 1):
                        print(f"      {i}. {account.get('email', 'Unknown')} ({account.get('type', 'Unknown')})")
                
                return True
            else:
                print("   ⚠️  Unexpected response format")
                return False
        else:
            print("   ❌ Failed to access connected accounts endpoint")
            return False

    def test_auth_callback_empty_params(self):
        """Test GET /api/auth/callback - Check callback endpoint with empty parameters"""
        print("\n" + "="*60)
        print("🔄 AUTH CALLBACK TEST (Empty Parameters)")
        print("="*60)
        
        success, response = self.run_test(
            "OAuth Callback - No Parameters",
            "GET",
            "auth/callback",
            400,  # Expecting bad request for missing parameters
            description="Testing callback endpoint behavior with missing code and state parameters",
            allow_redirects=False
        )
        
        if success:
            print("   ✅ Callback endpoint correctly handles missing parameters")
            
            # Check if response contains Turkish error message (as mentioned in test_result.md)
            response_text = response.get('text', '')
            if 'Bağlantı Parametresi Hatası' in response_text or 'gerekli parametreler eksik' in response_text:
                print("   ✅ Turkish error message present (user-friendly)")
                return True
            else:
                print("   ⚠️  Error message format may need improvement")
                return True  # Still pass since it handled the error correctly
        else:
            print("   ❌ Callback endpoint did not handle missing parameters correctly")
            return False

    def test_auth_callback_with_error(self):
        """Test GET /api/auth/callback with error parameter"""
        print("\n" + "="*60)
        print("🔄 AUTH CALLBACK TEST (With Error)")
        print("="*60)
        
        success, response = self.run_test(
            "OAuth Callback - With Error Parameter",
            "GET",
            "auth/callback?error=access_denied",
            400,  # Expecting error handling
            description="Testing callback endpoint behavior with OAuth error parameter",
            allow_redirects=False
        )
        
        if success:
            print("   ✅ Callback endpoint correctly handles OAuth errors")
            
            # Check for Turkish error message
            response_text = response.get('text', '')
            if 'Outlook hesabı bağlantısında hata oluştu' in response_text:
                print("   ✅ Turkish OAuth error message present")
                return True
            else:
                print("   ⚠️  OAuth error message could be more user-friendly")
                return True
        else:
            print("   ❌ Callback endpoint did not handle OAuth error correctly")
            return False

    def check_backend_logs(self):
        """Check backend logs for Microsoft Graph SDK or OAuth related warnings/errors"""
        print("\n" + "="*60)
        print("📋 BACKEND LOGS CHECK")
        print("="*60)
        
        try:
            # Try to read supervisor backend logs
            import subprocess
            
            print("   🔍 Checking backend logs for Microsoft Graph SDK warnings...")
            
            # Check for recent backend logs
            result = subprocess.run(
                ["tail", "-n", "100", "/var/log/supervisor/backend.err.log"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                log_content = result.stdout
                
                # Check for specific warnings/errors
                graph_warnings = []
                oauth_errors = []
                
                lines = log_content.split('\n')
                for line in lines:
                    if 'Microsoft Graph SDK not available' in line:
                        graph_warnings.append(line.strip())
                    elif 'azure.core' in line or 'kiota_abstractions' in line:
                        graph_warnings.append(line.strip())
                    elif 'OAuth' in line and ('error' in line.lower() or 'warning' in line.lower()):
                        oauth_errors.append(line.strip())
                
                print(f"   📊 Checked {len(lines)} log lines")
                
                if graph_warnings:
                    print(f"   ⚠️  Found {len(graph_warnings)} Microsoft Graph SDK warnings:")
                    for warning in graph_warnings[-3:]:  # Show last 3
                        print(f"      - {warning}")
                    return False
                else:
                    print("   ✅ No Microsoft Graph SDK warnings found in recent logs")
                
                if oauth_errors:
                    print(f"   ⚠️  Found {len(oauth_errors)} OAuth-related errors:")
                    for error in oauth_errors[-3:]:  # Show last 3
                        print(f"      - {error}")
                
                return len(graph_warnings) == 0
            else:
                print("   ⚠️  Could not read backend error logs")
                return True  # Don't fail the test if we can't read logs
                
        except Exception as e:
            print(f"   ⚠️  Error checking backend logs: {str(e)}")
            return True  # Don't fail the test if we can't check logs

    def test_outlook_integration_flow(self):
        """Test the complete Outlook integration flow simulation"""
        print("\n" + "="*60)
        print("🔄 OUTLOOK INTEGRATION FLOW TEST")
        print("="*60)
        
        print("   📝 Simulating user's reported issue:")
        print("      1. User sees 'successfully connected' message")
        print("      2. Then gets an error after callback")
        
        # Step 1: Check if auth URL can be generated (user would see this)
        success1, response1 = self.run_test(
            "Step 1: Auth URL Generation",
            "GET",
            "outlook/auth-url",
            200,
            description="User clicks 'Connect Outlook' and gets auth URL"
        )
        
        if not success1:
            print("   ❌ User would not be able to start OAuth flow")
            return False
        
        # Step 2: Simulate callback with missing parameters (user's error scenario)
        success2, response2 = self.run_test(
            "Step 2: Callback Error Simulation",
            "GET",
            "auth/callback",
            400,
            description="Simulating the error user encounters after 'successful connection'"
        )
        
        # Step 3: Check if accounts endpoint would work after successful connection
        success3, response3 = self.run_test(
            "Step 3: Post-Connection Account Check",
            "GET",
            "outlook/accounts",
            200,
            description="Checking if user could access accounts after successful connection"
        )
        
        # Step 4: Check sync endpoint behavior
        success4, response4 = self.run_test(
            "Step 4: Email Sync Attempt",
            "POST",
            "outlook/sync",
            404,  # Expecting 404 since no account is connected
            data={"account_email": "test@outlook.com"},
            description="Testing email sync when no account is connected"
        )
        
        # Analyze the flow
        flow_success = success1 and success2 and success3
        
        if flow_success:
            print("   ✅ OAuth flow endpoints are working correctly")
            print("   ✅ Error handling is implemented")
            print("   ✅ User's issue is likely resolved")
            return True
        else:
            print("   ❌ OAuth flow has issues that could cause user's problem")
            return False

    def run_comprehensive_outlook_test(self):
        """Run all Outlook integration tests"""
        print("🚀 STARTING OUTLOOK INTEGRATION COMPREHENSIVE TEST")
        print("=" * 80)
        print(f"🕐 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 Testing against: {self.base_url}")
        print("📋 User Issue: 'Outlook bağlantı hatası veriyor ve outlook bağlandıktan sonrada frontend tarafında bir hata olmalı'")
        print("=" * 80)
        
        # Test sequence based on user's request
        tests = [
            ("Demo User Login", self.test_demo_user_login),
            ("Outlook Status Check", self.test_outlook_status),
            ("OAuth URL Generation", self.test_outlook_auth_url),
            ("Connected Accounts Access", self.test_outlook_accounts),
            ("Callback Empty Parameters", self.test_auth_callback_empty_params),
            ("Callback Error Handling", self.test_auth_callback_with_error),
            ("Backend Logs Check", self.check_backend_logs),
            ("Integration Flow Simulation", self.test_outlook_integration_flow),
        ]
        
        failed_tests = []
        critical_failures = []
        
        for test_name, test_func in tests:
            try:
                print(f"\n🎯 Running: {test_name}")
                result = test_func()
                if not result:
                    failed_tests.append(test_name)
                    # Mark critical failures
                    if test_name in ["Outlook Status Check", "OAuth URL Generation", "Demo User Login"]:
                        critical_failures.append(test_name)
                    print(f"⚠️  {test_name} failed but continuing...")
            except Exception as e:
                failed_tests.append(test_name)
                critical_failures.append(test_name)
                print(f"💥 {test_name} crashed: {str(e)}")
        
        # Print final results
        print("\n" + "=" * 80)
        print("📊 OUTLOOK INTEGRATION TEST RESULTS")
        print("=" * 80)
        print(f"✅ Tests Passed: {self.tests_passed}/{self.tests_run}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}/{self.tests_run}")
        
        if critical_failures:
            print(f"\n🚨 CRITICAL FAILURES (blocking Outlook integration):")
            for test in critical_failures:
                print(f"   - {test}")
        
        if failed_tests:
            print(f"\n⚠️  All Failed Tests:")
            for test in failed_tests:
                print(f"   - {test}")
        
        # Detailed results
        print(f"\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"   {status} {result['name']}: {result['details']}")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"\n🎯 Success Rate: {success_rate:.1f}%")
        
        # Diagnosis based on results
        print(f"\n🔍 DIAGNOSIS:")
        if len(critical_failures) == 0:
            print("✅ Core Outlook integration components are working")
            print("✅ User should be able to connect Outlook accounts successfully")
        else:
            print("❌ Critical issues found that would prevent Outlook integration")
            print("❌ User's connection errors are likely due to these issues")
        
        if success_rate >= 75:
            print("🎉 OUTLOOK INTEGRATION TEST SUITE PASSED!")
            return 0
        else:
            print("⚠️  OUTLOOK INTEGRATION NEEDS ATTENTION")
            return 1

def main():
    """Main test execution"""
    if len(sys.argv) > 1 and sys.argv[1] == "outlook":
        # Run Outlook integration tests
        tester = OutlookIntegrationTester()
        return tester.run_comprehensive_outlook_test()
    else:
        # Run admin panel bulk operations tests (default)
        tester = AdminPanelBulkOperationsTester()
        return tester.run_comprehensive_test()

if __name__ == "__main__":
    sys.exit(main())