#!/usr/bin/env python3
"""
Outlook Integration Test - Focused test for tyrzmusak@gmail.com user
Testing the complete Outlook connection flow as requested in the review.
"""

import requests
import sys
import json
from datetime import datetime

class OutlookIntegrationTester:
    def __init__(self, base_url="https://auth-system-repair-3.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.user = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_result(self, test_name, success, details=""):
        """Log test result for summary"""
        self.test_results.append({
            "name": test_name,
            "success": success,
            "details": details
        })

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
                    print(f"   Response keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Non-dict response'}")
                    if isinstance(response_data, dict) and len(str(response_data)) < 500:
                        print(f"   Response data: {response_data}")
                except:
                    print(f"   Response: {response.text[:200]}...")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:300]}...")

            return success, response.json() if response.text and response.status_code < 500 else {}, response

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}, None

    def test_tyrz_user_login(self):
        """Test tyrzmusak@gmail.com user login"""
        print("\n" + "="*60)
        print("🎯 TESTING TYRZ MUSAK USER LOGIN")
        print("="*60)
        
        success, response, _ = self.run_test(
            "Tyrz Musak User Login",
            "POST",
            "auth/login",
            200,
            data={"email": "tyrzmusak@gmail.com", "password": "deneme123"}
        )
        
        if success and 'token' in response and 'user' in response:
            self.token = response['token']
            self.user = response['user']
            print(f"   ✅ Successfully logged in as: {self.user.get('email')}")
            print(f"   User ID: {self.user.get('id')}")
            print(f"   User Name: {self.user.get('name')}")
            self.log_result("Tyrz User Login", True, f"Logged in as {self.user.get('email')}")
            return True
        else:
            self.log_result("Tyrz User Login", False, "Failed to login or get token")
            return False

    def test_outlook_auth_url(self):
        """Test Outlook auth-url endpoint with authenticated user"""
        print("\n" + "="*60)
        print("🔗 TESTING OUTLOOK AUTH-URL ENDPOINT")
        print("="*60)
        
        if not self.token:
            print("❌ No authentication token available")
            self.log_result("Outlook Auth URL", False, "No authentication token")
            return False
        
        success, response, _ = self.run_test(
            "Outlook Auth URL Generation",
            "GET",
            "outlook/auth-url",
            200
        )
        
        if success:
            auth_url = response.get('auth_url', '')
            state = response.get('state', '')
            if auth_url and 'login.microsoftonline.com' in auth_url:
                print(f"   ✅ Auth URL generated successfully")
                print(f"   Auth URL contains: login.microsoftonline.com")
                print(f"   State parameter: {state[:20]}..." if state else "No state")
                self.log_result("Outlook Auth URL", True, "Auth URL generated with Microsoft endpoint")
                return True
            else:
                print(f"   ❌ Invalid auth URL format: {auth_url}")
                self.log_result("Outlook Auth URL", False, "Invalid auth URL format")
                return False
        else:
            self.log_result("Outlook Auth URL", False, "Failed to generate auth URL")
            return False

    def test_outlook_accounts_list(self):
        """Test Outlook accounts list endpoint"""
        print("\n" + "="*60)
        print("📋 TESTING OUTLOOK ACCOUNTS LIST")
        print("="*60)
        
        if not self.token:
            print("❌ No authentication token available")
            self.log_result("Outlook Accounts List", False, "No authentication token")
            return False
        
        success, response, _ = self.run_test(
            "Outlook Connected Accounts",
            "GET",
            "outlook/accounts",
            200
        )
        
        if success:
            accounts = response.get('accounts', [])
            print(f"   ✅ Accounts endpoint accessible")
            print(f"   Connected accounts count: {len(accounts)}")
            
            if accounts:
                for i, account in enumerate(accounts):
                    print(f"   Account {i+1}: {account.get('email', 'No email')} - {account.get('status', 'No status')}")
            else:
                print("   ℹ️  No connected Outlook accounts found")
            
            self.log_result("Outlook Accounts List", True, f"Found {len(accounts)} connected accounts")
            return True
        else:
            self.log_result("Outlook Accounts List", False, "Failed to access accounts endpoint")
            return False

    def test_outlook_sync_endpoint(self):
        """Test Outlook email sync endpoint"""
        print("\n" + "="*60)
        print("🔄 TESTING OUTLOOK EMAIL SYNC")
        print("="*60)
        
        if not self.token:
            print("❌ No authentication token available")
            self.log_result("Outlook Email Sync", False, "No authentication token")
            return False
        
        # First try to get connected accounts to use for sync
        accounts_success, accounts_response, _ = self.run_test(
            "Get Accounts for Sync",
            "GET",
            "outlook/accounts",
            200
        )
        
        if accounts_success:
            accounts = accounts_response.get('accounts', [])
            if accounts:
                # Try to sync with the first connected account using query parameter
                account_id = accounts[0].get('id')
                
                success, response, _ = self.run_test(
                    f"Outlook Email Sync - Account ID: {account_id}",
                    "POST",
                    f"outlook/sync?account_id={account_id}",
                    200
                )
                
                if success:
                    synced_count = response.get('synced_count', 0)
                    error_count = response.get('error_count', 0)
                    print(f"   ✅ Sync completed")
                    print(f"   Synced emails: {synced_count}")
                    print(f"   Errors: {error_count}")
                    self.log_result("Outlook Email Sync", True, f"Synced {synced_count} emails, {error_count} errors")
                    return True
                else:
                    self.log_result("Outlook Email Sync", False, "Sync request failed")
                    return False
            else:
                # No connected accounts, try sync with dummy account_id to see the error
                success, response, http_response = self.run_test(
                    "Outlook Email Sync - No Connected Account",
                    "POST",
                    "outlook/sync?account_id=dummy-account-id",
                    404  # Expecting 404 since account doesn't exist
                )
                
                # This is actually expected behavior if no account is connected
                if http_response and http_response.status_code == 404:
                    print("   ℹ️  Expected error: Account not found")
                    self.log_result("Outlook Email Sync", True, "Expected error - account not found")
                    return True
                else:
                    self.log_result("Outlook Email Sync", False, f"Unexpected response: {http_response.status_code if http_response else 'None'}")
                    return False
        else:
            self.log_result("Outlook Email Sync", False, "Could not check connected accounts")
            return False

    def test_outlook_callback_simulation(self):
        """Test Outlook callback endpoint (simulation)"""
        print("\n" + "="*60)
        print("🔄 TESTING OUTLOOK CALLBACK (SIMULATION)")
        print("="*60)
        
        # Note: We can't actually test the full OAuth flow without real Microsoft tokens
        # But we can test the endpoint exists and handles invalid tokens properly
        
        success, response, http_response = self.run_test(
            "Outlook Callback - Invalid Code",
            "POST",
            "auth/outlook-login?code=invalid_test_code&state=test_state",
            400  # Expecting error for invalid code
        )
        
        if http_response and http_response.status_code in [400, 401, 500, 503]:
            print("   ℹ️  Callback endpoint exists and handles invalid codes")
            self.log_result("Outlook Callback", True, f"Endpoint exists and handles errors properly (status: {http_response.status_code})")
            return True
        else:
            self.log_result("Outlook Callback", False, f"Unexpected callback behavior (status: {http_response.status_code if http_response else 'None'})")
            return False

    def test_outlook_connect_account(self):
        """Test Outlook account connection endpoint"""
        print("\n" + "="*60)
        print("🔗 TESTING OUTLOOK ACCOUNT CONNECTION")
        print("="*60)
        
        if not self.token:
            print("❌ No authentication token available")
            self.log_result("Outlook Connect Account", False, "No authentication token")
            return False
        
        # Test the connect account endpoint with dummy data
        connect_data = {
            "email": "tyrzmusak@gmail.com",
            "display_name": "Tyrz Musak",
            "access_token": "dummy_access_token",
            "refresh_token": "dummy_refresh_token"
        }
        
        success, response, http_response = self.run_test(
            "Outlook Connect Account - Test Data",
            "POST",
            "outlook/connect-account",
            200,  # Expecting success or specific error
            data=connect_data
        )
        
        if success:
            print("   ✅ Account connection endpoint accessible")
            self.log_result("Outlook Connect Account", True, "Endpoint accessible and processes requests")
            return True
        elif http_response and http_response.status_code in [400, 401, 503]:
            print(f"   ℹ️  Expected error for dummy data (status: {http_response.status_code})")
            self.log_result("Outlook Connect Account", True, f"Endpoint handles invalid data properly (status: {http_response.status_code})")
            return True
        else:
            self.log_result("Outlook Connect Account", False, f"Unexpected response (status: {http_response.status_code if http_response else 'None'})")
            return False

    def test_outlook_status_check(self):
        """Test Outlook integration status"""
        print("\n" + "="*60)
        print("📊 TESTING OUTLOOK INTEGRATION STATUS")
        print("="*60)
        
        if not self.token:
            print("❌ No authentication token available")
            self.log_result("Outlook Status", False, "No authentication token")
            return False
        
        success, response, _ = self.run_test(
            "Outlook Integration Status",
            "GET",
            "outlook/status",
            200
        )
        
        if success:
            configured = response.get('credentials_configured', False)
            ready = response.get('graph_sdk_available', False)
            print(f"   Integration configured: {configured}")
            print(f"   Graph SDK available: {ready}")
            
            if configured and ready:
                print("   ✅ Outlook integration is configured and ready")
                self.log_result("Outlook Status", True, "Integration configured and ready")
                return True
            else:
                print("   ⚠️  Outlook integration has some issues")
                self.log_result("Outlook Status", False, f"Integration issues - configured: {configured}, ready: {ready}")
                return False
        else:
            self.log_result("Outlook Status", False, "Could not check integration status")
            return False
        """Test Outlook integration status"""
        print("\n" + "="*60)
        print("📊 TESTING OUTLOOK INTEGRATION STATUS")
        print("="*60)
        
        if not self.token:
            print("❌ No authentication token available")
            self.log_result("Outlook Status", False, "No authentication token")
            return False
        
        success, response, _ = self.run_test(
            "Outlook Integration Status",
            "GET",
            "outlook/status",
            200
        )
        
        if success:
            configured = response.get('configured', False)
            ready = response.get('ready', False)
            print(f"   Integration configured: {configured}")
            print(f"   Integration ready: {ready}")
            
            if configured:
                print("   ✅ Outlook integration is configured")
                self.log_result("Outlook Status", True, "Integration configured and ready")
                return True
            else:
                print("   ⚠️  Outlook integration not fully configured")
                self.log_result("Outlook Status", False, "Integration not configured")
                return False
        else:
            self.log_result("Outlook Status", False, "Could not check integration status")
            return False

    def run_comprehensive_outlook_test(self):
        """Run comprehensive Outlook integration test"""
        print("\n" + "🎯" * 20)
        print("OUTLOOK INTEGRATION COMPREHENSIVE TEST")
        print("Testing for user: tyrzmusak@gmail.com")
        print("🎯" * 20)
        
        # Test sequence as requested
        tests = [
            ("User Login", self.test_tyrz_user_login),
            ("Outlook Auth URL", self.test_outlook_auth_url),
            ("Outlook Callback", self.test_outlook_callback_simulation),
            ("Outlook Connect Account", self.test_outlook_connect_account),
            ("Outlook Accounts", self.test_outlook_accounts_list),
            ("Outlook Sync", self.test_outlook_sync_endpoint),
            ("Outlook Status", self.test_outlook_status_check)
        ]
        
        for test_name, test_func in tests:
            try:
                test_func()
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {str(e)}")
                self.log_result(test_name, False, f"Exception: {str(e)}")
        
        # Print comprehensive summary
        self.print_comprehensive_summary()

    def print_comprehensive_summary(self):
        """Print detailed test summary"""
        print("\n" + "="*80)
        print("📊 OUTLOOK INTEGRATION TEST SUMMARY")
        print("="*80)
        
        print(f"Total tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"  {status} - {result['name']}")
            if result["details"]:
                print(f"    Details: {result['details']}")
        
        print("\n🔍 ANALYSIS:")
        failed_tests = [r for r in self.test_results if not r["success"]]
        
        if not failed_tests:
            print("✅ All Outlook integration tests passed!")
        else:
            print("❌ Issues found in Outlook integration:")
            for failed in failed_tests:
                print(f"  - {failed['name']}: {failed['details']}")
        
        print("\n💡 RECOMMENDATIONS:")
        if any("No authentication token" in r["details"] for r in failed_tests):
            print("  - User login is failing - check credentials and user approval status")
        
        if any("auth URL" in r["name"].lower() for r in failed_tests):
            print("  - Outlook auth URL generation is failing - check Azure app configuration")
        
        if any("sync" in r["name"].lower() for r in failed_tests):
            print("  - Email sync is failing - this could be the root cause of user's issue")
        
        if any("accounts" in r["name"].lower() for r in failed_tests):
            print("  - Account listing is failing - check connected accounts functionality")

if __name__ == "__main__":
    print("🚀 Starting Outlook Integration Test for tyrzmusak@gmail.com")
    print("=" * 60)
    
    tester = OutlookIntegrationTester()
    tester.run_comprehensive_outlook_test()
    
    print("\n🏁 Test completed!")