#!/usr/bin/env python3
"""
Focused test for PostaDepo account connection functionality
Tests the specific endpoints requested in the review.
"""

import requests
import sys
import json
from datetime import datetime

class AccountConnectionTester:
    def __init__(self, base_url="https://mongodb-auth-fix-2.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.user = None
        self.tests_run = 0
        self.tests_passed = 0
        self.connected_accounts = []

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
                try:
                    return False, response.json()
                except:
                    return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def login_demo_user(self):
        """Login with demo user credentials"""
        print("\n🔐 Logging in with demo user...")
        success, response = self.run_test(
            "Demo User Login",
            "POST",
            "auth/login",
            200,
            data={"email": "demo@postadepo.com", "password": "demo123"}
        )
        
        if success and 'token' in response and 'user' in response:
            self.token = response['token']
            self.user = response['user']
            print(f"   ✅ Logged in as: {self.user.get('email')}")
            return True
        else:
            print("   ❌ Login failed!")
            return False

    def clear_existing_accounts(self):
        """Clear any existing connected accounts for clean testing"""
        print("\n🧹 Clearing existing connected accounts...")
        success, response = self.run_test(
            "Get Existing Connected Accounts",
            "GET",
            "connected-accounts",
            200
        )
        
        if success:
            accounts = response.get('accounts', [])
            print(f"   Found {len(accounts)} existing accounts")
            
            for account in accounts:
                account_id = account.get('id')
                if account_id:
                    print(f"   Removing account: {account.get('email')} ({account.get('type')})")
                    self.run_test(
                        f"Remove {account.get('type')} Account",
                        "DELETE",
                        f"connected-accounts/{account_id}",
                        200
                    )

    def test_connect_outlook_account(self):
        """Test connecting Outlook account"""
        print("\n📧 Testing Outlook Account Connection...")
        success, response = self.run_test(
            "Connect Outlook Account",
            "POST",
            "connect-account",
            200,
            data={"type": "outlook"}
        )
        
        if success:
            account = response.get('account', {})
            print(f"   ✅ Connected: {account.get('email')} ({account.get('type')})")
            print(f"   Account ID: {account.get('id')}")
            self.connected_accounts.append(account)
            return True
        return False

    def test_connect_gmail_account(self):
        """Test connecting Gmail account"""
        print("\n📧 Testing Gmail Account Connection...")
        success, response = self.run_test(
            "Connect Gmail Account",
            "POST",
            "connect-account",
            200,
            data={"type": "gmail"}
        )
        
        if success:
            account = response.get('account', {})
            print(f"   ✅ Connected: {account.get('email')} ({account.get('type')})")
            print(f"   Account ID: {account.get('id')}")
            self.connected_accounts.append(account)
            return True
        return False

    def test_list_connected_accounts(self):
        """Test listing connected accounts"""
        print("\n📋 Testing List Connected Accounts...")
        success, response = self.run_test(
            "List Connected Accounts",
            "GET",
            "connected-accounts",
            200
        )
        
        if success:
            accounts = response.get('accounts', [])
            print(f"   ✅ Found {len(accounts)} connected accounts:")
            for account in accounts:
                print(f"     - {account.get('email')} ({account.get('type')}) - ID: {account.get('id')}")
            return True
        return False

    def test_sync_emails(self):
        """Test email synchronization"""
        print("\n🔄 Testing Email Synchronization...")
        success, response = self.run_test(
            "Sync Emails",
            "POST",
            "sync-emails",
            200
        )
        
        if success:
            new_emails = response.get('new_emails', 0)
            print(f"   ✅ Synchronized {new_emails} new emails")
            return True
        return False

    def test_disconnect_accounts(self):
        """Test disconnecting accounts"""
        print("\n🔌 Testing Account Disconnection...")
        success_count = 0
        
        for account in self.connected_accounts:
            account_id = account.get('id')
            account_email = account.get('email')
            account_type = account.get('type')
            
            if account_id:
                print(f"\n   Disconnecting {account_email} ({account_type})...")
                success, response = self.run_test(
                    f"Disconnect {account_type} Account",
                    "DELETE",
                    f"connected-accounts/{account_id}",
                    200
                )
                if success:
                    success_count += 1
                    print(f"   ✅ Successfully disconnected {account_email}")
        
        return success_count == len(self.connected_accounts)

    def test_sync_without_accounts(self):
        """Test sync when no accounts are connected"""
        print("\n🔄 Testing Sync Without Connected Accounts...")
        success, response = self.run_test(
            "Sync Without Accounts",
            "POST",
            "sync-emails",
            200
        )
        
        if success:
            new_emails = response.get('new_emails', 0)
            print(f"   ✅ Demo sync added {new_emails} emails (expected behavior)")
            return True
        return False

    def test_duplicate_connection(self):
        """Test connecting duplicate account (should fail)"""
        print("\n🚫 Testing Duplicate Account Connection...")
        
        # First connect an account
        self.test_connect_outlook_account()
        
        # Try to connect the same type again
        success, response = self.run_test(
            "Connect Duplicate Outlook Account",
            "POST",
            "connect-account",
            400,
            data={"type": "outlook"}
        )
        
        if success:
            print("   ✅ Correctly rejected duplicate connection")
            return True
        return False

    def test_invalid_account_type(self):
        """Test connecting invalid account type"""
        print("\n🚫 Testing Invalid Account Type...")
        success, response = self.run_test(
            "Connect Invalid Account Type",
            "POST",
            "connect-account",
            400,
            data={"type": "yahoo"}
        )
        
        if success:
            print("   ✅ Correctly rejected invalid account type")
            return True
        return False

def main():
    print("🚀 PostaDepo Account Connection API Tests")
    print("=" * 60)
    
    tester = AccountConnectionTester()
    
    # Test sequence following the review requirements
    test_results = []
    
    # 1. Login with demo user
    if not tester.login_demo_user():
        print("❌ Cannot proceed without login")
        return 1
    
    # 2. Clear existing accounts for clean testing
    tester.clear_existing_accounts()
    
    # 3. Test connecting Outlook account
    test_results.append(("Connect Outlook Account", tester.test_connect_outlook_account()))
    
    # 4. Test connecting Gmail account  
    test_results.append(("Connect Gmail Account", tester.test_connect_gmail_account()))
    
    # 5. Test listing connected accounts
    test_results.append(("List Connected Accounts", tester.test_list_connected_accounts()))
    
    # 6. Test email synchronization with accounts
    test_results.append(("Sync Emails (With Accounts)", tester.test_sync_emails()))
    
    # 7. Test disconnecting accounts
    test_results.append(("Disconnect Accounts", tester.test_disconnect_accounts()))
    
    # 8. Test sync without accounts
    test_results.append(("Sync Without Accounts", tester.test_sync_without_accounts()))
    
    # 9. Test error scenarios
    test_results.append(("Duplicate Connection Test", tester.test_duplicate_connection()))
    test_results.append(("Invalid Account Type Test", tester.test_invalid_account_type()))
    
    # Print final results
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 Overall: {passed}/{len(test_results)} tests passed")
    print(f"🔧 API Tests: {tester.tests_passed}/{tester.tests_run} individual API calls passed")
    
    if passed == len(test_results):
        print("🎉 All account connection tests passed!")
        return 0
    else:
        print(f"⚠️  {len(test_results) - passed} test scenarios failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())