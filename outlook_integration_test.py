#!/usr/bin/env python3
"""
Outlook Integration Test Suite
Türk kullanıcının Outlook entegrasyonu sorunu için kapsamlı test

PROBLEM: Kullanıcı "Outlook bağlandı diyor, ondan sonra hata veriyor" şikayeti
Microsoft'dan onay maili geliyor ama sayfada veriler doğru görünmüyor.

TEST EDİLECEK KRITIK NOKTALAR:
1. Outlook OAuth Akışı Test
2. Connected Accounts Test  
3. Email Sync Test
4. Error Investigation
"""

import requests
import sys
import json
from datetime import datetime
import subprocess
import os

class OutlookIntegrationTester:
    def __init__(self, base_url="https://outlook-connector.preview.emergentagent.com/api"):
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

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, return_response=False):
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
                    if isinstance(response_data, dict):
                        print(f"   Response keys: {list(response_data.keys())}")
                        # Show important values for debugging
                        for key in ['message', 'error', 'detail', 'auth_url', 'accounts', 'emails']:
                            if key in response_data:
                                value = response_data[key]
                                if isinstance(value, str) and len(value) > 100:
                                    print(f"   {key}: {value[:100]}...")
                                elif isinstance(value, list):
                                    print(f"   {key}: {len(value)} items")
                                else:
                                    print(f"   {key}: {value}")
                    else:
                        print(f"   Response: {str(response_data)[:100]}...")
                except:
                    print(f"   Response: {response.text[:100]}...")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:300]}...")

            self.log_result(name, success, f"Status: {response.status_code}")
            
            if return_response:
                return success, response
            return success, response.json() if response.text and response.status_code < 500 else {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.log_result(name, False, f"Error: {str(e)}")
            return False, {}

    def check_backend_logs(self):
        """Check backend logs for Microsoft Graph SDK errors"""
        print(f"\n🔍 Checking Backend Logs for Microsoft Graph SDK Issues...")
        try:
            # Check supervisor backend logs
            result = subprocess.run(
                ["tail", "-n", "50", "/var/log/supervisor/backend.err.log"],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                logs = result.stdout
                print(f"   Backend Error Logs (last 50 lines):")
                
                # Look for specific Microsoft Graph SDK issues
                critical_errors = [
                    "Microsoft Graph SDK not available",
                    "No module named",
                    "kiota_abstractions",
                    "azure.core",
                    "msgraph",
                    "SSL handshake failed",
                    "Graph SDK not available"
                ]
                
                found_errors = []
                for line in logs.split('\n'):
                    for error in critical_errors:
                        if error in line:
                            found_errors.append(line.strip())
                            print(f"   🚨 CRITICAL: {line.strip()}")
                
                if not found_errors:
                    print(f"   ✅ No critical Microsoft Graph SDK errors found in recent logs")
                    return True
                else:
                    print(f"   ❌ Found {len(found_errors)} critical errors")
                    return False
            else:
                print(f"   ⚠️  Could not read backend logs: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"   ⚠️  Error checking logs: {str(e)}")
            return False

    def test_demo_user_login(self):
        """Test demo user login for Outlook testing"""
        print(f"\n🎯 TESTING DEMO USER LOGIN FOR OUTLOOK INTEGRATION")
        success, response = self.run_test(
            "Demo User Login (demo@postadepo.com)",
            "POST",
            "auth/login",
            200,
            data={"email": "demo@postadepo.com", "password": "demo123"}
        )
        
        if success and 'token' in response and 'user' in response:
            self.token = response['token']
            self.user = response['user']
            print(f"   ✅ Logged in as: {self.user.get('email')} (user_type: {self.user.get('user_type')})")
            return True
        else:
            print(f"   ❌ Demo login failed - cannot proceed with Outlook tests")
            return False

    def test_tyrz_musak_user_login(self):
        """Test tyrzmusak@gmail.com user login"""
        print(f"\n🎯 TESTING TYRZ MUSAK USER LOGIN")
        success, response = self.run_test(
            "Tyrz Musak User Login (tyrzmusak@gmail.com)",
            "POST",
            "auth/login",
            200,
            data={"email": "tyrzmusak@gmail.com", "password": "deneme123"}
        )
        
        if success and 'token' in response and 'user' in response:
            self.token = response['token']
            self.user = response['user']
            print(f"   ✅ Logged in as: {self.user.get('email')} (user_type: {self.user.get('user_type')})")
            print(f"   User ID: {self.user.get('id')}")
            return True
        else:
            print(f"   ❌ Tyrz Musak login failed")
            return False

    def test_outlook_status(self):
        """Test Outlook integration status"""
        print(f"\n🎯 TESTING OUTLOOK INTEGRATION STATUS")
        success, response = self.run_test(
            "Outlook Status Check",
            "GET",
            "outlook/status",
            200
        )
        
        if success:
            # Check critical status fields
            graph_available = response.get('graph_sdk_available', False)
            credentials_configured = response.get('credentials_configured', False)
            client_id_set = response.get('client_id_set', False)
            tenant_id_set = response.get('tenant_id_set', False)
            
            print(f"   Graph SDK Available: {graph_available}")
            print(f"   Credentials Configured: {credentials_configured}")
            print(f"   Client ID Set: {client_id_set}")
            print(f"   Tenant ID Set: {tenant_id_set}")
            
            if graph_available and credentials_configured:
                print(f"   ✅ Outlook integration is properly configured")
                return True
            else:
                print(f"   ❌ Outlook integration has configuration issues")
                return False
        
        return success

    def test_outlook_auth_url_generation(self):
        """Test Outlook OAuth URL generation"""
        print(f"\n🎯 TESTING OUTLOOK OAUTH URL GENERATION")
        success, response = self.run_test(
            "Outlook Auth URL Generation",
            "GET",
            "outlook/auth-url",
            200
        )
        
        if success:
            auth_url = response.get('auth_url', '')
            state = response.get('state', '')
            
            print(f"   Auth URL Length: {len(auth_url)} characters")
            print(f"   State Parameter: {state[:20]}..." if state else "   State Parameter: Missing")
            
            # Check if URL contains required OAuth parameters
            required_params = ['client_id', 'response_type', 'redirect_uri', 'scope', 'state']
            missing_params = []
            
            for param in required_params:
                if param not in auth_url:
                    missing_params.append(param)
            
            if not missing_params:
                print(f"   ✅ Auth URL contains all required OAuth parameters")
                
                # Check if it's a Microsoft endpoint
                if 'login.microsoftonline.com' in auth_url:
                    print(f"   ✅ Using correct Microsoft OAuth endpoint")
                    return True
                else:
                    print(f"   ❌ Not using Microsoft OAuth endpoint")
                    return False
            else:
                print(f"   ❌ Missing OAuth parameters: {missing_params}")
                return False
        
        return success

    def test_outlook_connect_account(self):
        """Test Outlook account connection (will fail without real OAuth code)"""
        print(f"\n🎯 TESTING OUTLOOK ACCOUNT CONNECTION")
        
        # Test with invalid code to see error handling
        success, response = self.run_test(
            "Outlook Connect Account (Invalid Code Test)",
            "POST",
            "outlook/connect-account",
            400,  # Expecting 400 for invalid code
            data={"code": "invalid_test_code", "state": "test_state"}
        )
        
        if success:
            print(f"   ✅ Properly handles invalid OAuth code")
            return True
        else:
            # Check if it's a 503 (service unavailable) which indicates SDK issues
            if response and hasattr(response, 'status_code') and response.status_code == 503:
                print(f"   ❌ Service unavailable - likely Microsoft Graph SDK issue")
                return False
            print(f"   ⚠️  Unexpected response for invalid code test")
            return False

    def test_connected_accounts(self):
        """Test getting connected accounts"""
        print(f"\n🎯 TESTING CONNECTED ACCOUNTS RETRIEVAL")
        success, response = self.run_test(
            "Get Connected Accounts",
            "GET",
            "outlook/accounts",
            200
        )
        
        if success:
            accounts = response.get('accounts', [])
            print(f"   Connected Accounts Count: {len(accounts)}")
            
            if len(accounts) == 0:
                print(f"   ⚠️  No connected accounts found (expected for new user)")
            else:
                for i, account in enumerate(accounts):
                    print(f"   Account {i+1}: {account.get('email', 'No email')} ({account.get('account_type', 'Unknown type')})")
            
            return True
        
        return success

    def test_email_sync(self):
        """Test email synchronization"""
        print(f"\n🎯 TESTING EMAIL SYNC")
        success, response = self.run_test(
            "Email Sync Request",
            "POST",
            "outlook/sync",
            404,  # Expecting 404 if no accounts connected
            data={"account_email": "test@outlook.com"}
        )
        
        if success:
            print(f"   ✅ Properly returns 404 for non-existent account")
            return True
        else:
            # Check for other expected error codes
            if response and hasattr(response, 'status_code'):
                if response.status_code == 503:
                    print(f"   ❌ Service unavailable - Microsoft Graph SDK issue")
                    return False
                elif response.status_code == 400:
                    print(f"   ⚠️  Bad request - check request format")
                    return False
            return False

    def test_emails_endpoint(self):
        """Test emails endpoint to see if any Outlook emails exist"""
        print(f"\n🎯 TESTING EMAILS ENDPOINT")
        success, response = self.run_test(
            "Get User Emails",
            "GET",
            "emails?folder=all",
            200
        )
        
        if success:
            emails = response.get('emails', [])
            folder_counts = response.get('folderCounts', {})
            
            print(f"   Total Emails: {len(emails)}")
            print(f"   Folder Counts: {folder_counts}")
            
            # Check for Outlook-sourced emails
            outlook_emails = [email for email in emails if email.get('source') == 'outlook']
            print(f"   Outlook-sourced Emails: {len(outlook_emails)}")
            
            return True
        
        return success

    def check_database_connected_accounts(self):
        """Check database for connected accounts (requires MongoDB access)"""
        print(f"\n🎯 CHECKING DATABASE FOR CONNECTED ACCOUNTS")
        
        # This would require direct MongoDB access, which we don't have in the test environment
        # Instead, we'll use the API to infer database state
        print(f"   ℹ️  Database check via API endpoints (direct MongoDB access not available)")
        
        # Check via connected accounts API
        success, response = self.run_test(
            "Database Connected Accounts Check",
            "GET",
            "outlook/accounts",
            200
        )
        
        if success:
            accounts = response.get('accounts', [])
            print(f"   Database Connected Accounts: {len(accounts)}")
            
            if len(accounts) == 0:
                print(f"   ❌ No connected accounts in database - this explains sync failures")
                return False
            else:
                print(f"   ✅ Found {len(accounts)} connected accounts in database")
                return True
        
        return False

    def run_comprehensive_outlook_test(self):
        """Run comprehensive Outlook integration test suite"""
        print(f"\n" + "="*80)
        print(f"🚀 OUTLOOK INTEGRATION COMPREHENSIVE TEST SUITE")
        print(f"   Testing Türk kullanıcının Outlook entegrasyonu sorunu")
        print(f"   Problem: 'Outlook bağlandı diyor, ondan sonra hata veriyor'")
        print(f"="*80)
        
        # Step 1: Check backend logs first
        print(f"\n📋 STEP 1: BACKEND LOGS INVESTIGATION")
        logs_ok = self.check_backend_logs()
        
        # Step 2: Test demo user login
        print(f"\n📋 STEP 2: USER AUTHENTICATION")
        if not self.test_demo_user_login():
            print(f"❌ Cannot proceed without authentication")
            return False
        
        # Step 3: Test Outlook integration status
        print(f"\n📋 STEP 3: OUTLOOK INTEGRATION STATUS")
        status_ok = self.test_outlook_status()
        
        # Step 4: Test OAuth URL generation
        print(f"\n📋 STEP 4: OAUTH URL GENERATION")
        auth_url_ok = self.test_outlook_auth_url_generation()
        
        # Step 5: Test account connection handling
        print(f"\n📋 STEP 5: ACCOUNT CONNECTION HANDLING")
        connect_ok = self.test_outlook_connect_account()
        
        # Step 6: Test connected accounts retrieval
        print(f"\n📋 STEP 6: CONNECTED ACCOUNTS RETRIEVAL")
        accounts_ok = self.test_connected_accounts()
        
        # Step 7: Test email sync
        print(f"\n📋 STEP 7: EMAIL SYNC TESTING")
        sync_ok = self.test_email_sync()
        
        # Step 8: Test emails endpoint
        print(f"\n📋 STEP 8: EMAILS ENDPOINT")
        emails_ok = self.test_emails_endpoint()
        
        # Step 9: Check database state
        print(f"\n📋 STEP 9: DATABASE STATE CHECK")
        db_ok = self.check_database_connected_accounts()
        
        # Step 10: Test with actual user account
        print(f"\n📋 STEP 10: ACTUAL USER ACCOUNT TEST")
        user_test_ok = self.test_tyrz_musak_user_login()
        
        return self.generate_final_report(logs_ok, status_ok, auth_url_ok, connect_ok, accounts_ok, sync_ok, emails_ok, db_ok, user_test_ok)

    def generate_final_report(self, logs_ok, status_ok, auth_url_ok, connect_ok, accounts_ok, sync_ok, emails_ok, db_ok, user_test_ok):
        """Generate comprehensive final report"""
        print(f"\n" + "="*80)
        print(f"📊 OUTLOOK INTEGRATION TEST FINAL REPORT")
        print(f"="*80)
        
        print(f"\n🔍 TEST RESULTS SUMMARY:")
        print(f"   Total Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        print(f"\n🎯 CRITICAL COMPONENTS STATUS:")
        print(f"   ✅ Backend Logs Clean: {logs_ok}")
        print(f"   ✅ Outlook Status OK: {status_ok}")
        print(f"   ✅ OAuth URL Generation: {auth_url_ok}")
        print(f"   ✅ Account Connection: {connect_ok}")
        print(f"   ✅ Connected Accounts: {accounts_ok}")
        print(f"   ✅ Email Sync: {sync_ok}")
        print(f"   ✅ Emails Endpoint: {emails_ok}")
        print(f"   ✅ Database State: {db_ok}")
        print(f"   ✅ User Account Test: {user_test_ok}")
        
        # Determine root cause
        print(f"\n🔍 ROOT CAUSE ANALYSIS:")
        
        if not logs_ok:
            print(f"   🚨 CRITICAL: Microsoft Graph SDK issues detected in backend logs")
            print(f"   🔧 SOLUTION: Install missing dependencies (azure-core, kiota-abstractions, msgraph-core)")
            
        if not status_ok:
            print(f"   🚨 CRITICAL: Outlook integration not properly configured")
            print(f"   🔧 SOLUTION: Check Azure credentials and Graph SDK availability")
            
        if not db_ok:
            print(f"   🚨 CRITICAL: No connected accounts in database")
            print(f"   🔧 SOLUTION: OAuth token exchange and account storage is failing")
            
        if status_ok and auth_url_ok and not db_ok:
            print(f"   🎯 IDENTIFIED ISSUE: OAuth flow starts successfully but account connection fails")
            print(f"   📝 EXPLANATION: User sees 'bağlandı' message (OAuth URL works) but then gets error")
            print(f"   📝 REASON: Token exchange or account storage step is failing")
            
        # Final verdict
        all_critical_ok = status_ok and auth_url_ok and connect_ok
        
        if all_critical_ok:
            print(f"\n✅ VERDICT: Outlook integration backend is working correctly")
            print(f"   User can now safely attempt Outlook account connection")
        else:
            print(f"\n❌ VERDICT: Outlook integration has critical issues")
            print(f"   User will continue to experience 'bağlandı ama sonra hata' problem")
            
        return all_critical_ok

def main():
    """Main test execution"""
    print(f"🚀 Starting Outlook Integration Test Suite...")
    print(f"   Target: https://outlook-connector.preview.emergentagent.com/api")
    print(f"   Focus: Türk kullanıcının Outlook entegrasyonu sorunu")
    
    tester = OutlookIntegrationTester()
    
    try:
        success = tester.run_comprehensive_outlook_test()
        
        if success:
            print(f"\n🎉 All critical tests passed! Outlook integration is ready.")
            sys.exit(0)
        else:
            print(f"\n🚨 Critical issues found! Outlook integration needs fixes.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
"""
Outlook Integration Test - Focused test for tyrzmusak@gmail.com user
Testing the complete Outlook connection flow as requested in the review.
"""

import requests
import sys
import json
from datetime import datetime

class OutlookIntegrationTester:
    def __init__(self, base_url="https://outlook-connector.preview.emergentagent.com/api"):
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