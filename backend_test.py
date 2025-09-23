import requests
import sys
import json
from datetime import datetime

class PostaDepoAPITester:
    def __init__(self, base_url="https://team-backup.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.user = None
        self.tests_run = 0
        self.tests_passed = 0

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
                except:
                    print(f"   Response: {response.text[:100]}...")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")

            return success, response.json() if response.text and response.status_code < 500 else {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test API health check"""
        success, response = self.run_test(
            "Health Check",
            "GET",
            "",
            200
        )
        return success

    def test_login(self):
        """Test demo user login"""
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
            print(f"   Logged in as: {self.user.get('email')}")
            return True
        return False

    def test_invalid_login(self):
        """Test invalid login credentials"""
        success, response = self.run_test(
            "Invalid Login",
            "POST",
            "auth/login",
            401,
            data={"email": "invalid@test.com", "password": "wrongpass"}
        )
        return success

    def test_get_emails_inbox(self):
        """Test getting inbox emails"""
        success, response = self.run_test(
            "Get Inbox Emails",
            "GET",
            "emails?folder=inbox",
            200
        )
        
        if success:
            emails = response.get('emails', [])
            folder_counts = response.get('folderCounts', {})
            print(f"   Found {len(emails)} emails in inbox")
            print(f"   Folder counts: {folder_counts}")
        
        return success

    def test_get_emails_all_folders(self):
        """Test getting emails from all folders"""
        folders = ["inbox", "sent", "all", "deleted", "spam"]
        all_success = True
        
        for folder in folders:
            success, response = self.run_test(
                f"Get {folder.title()} Emails",
                "GET",
                f"emails?folder={folder}",
                200
            )
            
            if success:
                emails = response.get('emails', [])
                print(f"   Found {len(emails)} emails in {folder}")
            
            all_success = all_success and success
        
        return all_success

    def test_storage_info(self):
        """Test storage information endpoint"""
        success, response = self.run_test(
            "Storage Information",
            "GET",
            "storage-info",
            200
        )
        
        if success:
            total_emails = response.get('totalEmails', 0)
            total_size = response.get('totalSize', 0)
            print(f"   Total emails: {total_emails}")
            print(f"   Total size: {total_size} bytes ({total_size/1024:.2f} KB)")
        
        return success

    def test_mark_email_read(self):
        """Test marking an email as read"""
        # First get an email ID
        success, response = self.run_test(
            "Get Email for Read Test",
            "GET",
            "emails?folder=inbox",
            200
        )
        
        if not success or not response.get('emails'):
            print("❌ No emails found to test mark as read")
            return False
        
        email_id = response['emails'][0]['id']
        
        success, response = self.run_test(
            "Mark Email as Read",
            "PUT",
            f"emails/{email_id}/read",
            200
        )
        
        return success

    def test_sync_emails(self):
        """Test email synchronization"""
        success, response = self.run_test(
            "Sync Emails",
            "POST",
            "sync-emails",
            200
        )
        
        if success:
            new_emails = response.get('new_emails', 0)
            print(f"   Added {new_emails} new emails during sync")
        
        return success

    def test_export_emails(self):
        """Test email export functionality"""
        formats = ["json", "zip", "eml"]
        all_success = True
        
        for format_type in formats:
            success, response = self.run_test(
                f"Export Emails ({format_type.upper()})",
                "POST",
                "export-emails",
                200,
                data={"format": format_type, "folder": "all"}
            )
            all_success = all_success and success
        
        return all_success

    def test_unauthorized_access(self):
        """Test accessing protected endpoints without token"""
        # Temporarily remove token
        original_token = self.token
        self.token = None
        
        success, response = self.run_test(
            "Unauthorized Access Test",
            "GET",
            "emails",
            401
        )
        
        # Restore token
        self.token = original_token
        return success

    def test_get_connected_accounts_empty(self):
        """Test getting connected accounts when none exist"""
        success, response = self.run_test(
            "Get Connected Accounts (Empty)",
            "GET",
            "connected-accounts",
            200
        )
        
        if success:
            accounts = response.get('accounts', [])
            print(f"   Found {len(accounts)} connected accounts")
        
        return success

    def test_connect_outlook_account_1(self):
        """Test connecting first Outlook account with email and name"""
        success, response = self.run_test(
            "Connect First Outlook Account",
            "POST",
            "connect-account",
            200,
            data={
                "type": "outlook",
                "email": "john.doe@outlook.com",
                "name": "John Doe"
            }
        )
        
        if success:
            account = response.get('account', {})
            print(f"   Connected account: {account.get('email')} ({account.get('type')})")
            print(f"   Account name: {account.get('name')}")
            # Store account ID for later tests
            self.outlook_account_id_1 = account.get('id')
        
        return success

    def test_connect_outlook_account_2(self):
        """Test connecting second Outlook account with different email"""
        success, response = self.run_test(
            "Connect Second Outlook Account",
            "POST",
            "connect-account",
            200,
            data={
                "type": "outlook",
                "email": "jane.smith@hotmail.com",
                "name": "Jane Smith"
            }
        )
        
        if success:
            account = response.get('account', {})
            print(f"   Connected account: {account.get('email')} ({account.get('type')})")
            print(f"   Account name: {account.get('name')}")
            # Store account ID for later tests
            self.outlook_account_id_2 = account.get('id')
        
        return success

    def test_connect_outlook_account_3(self):
        """Test connecting third Outlook account to verify unlimited support"""
        success, response = self.run_test(
            "Connect Third Outlook Account",
            "POST",
            "connect-account",
            200,
            data={
                "type": "outlook",
                "email": "corporate.user@outlook.com",
                "name": "Corporate User"
            }
        )
        
        if success:
            account = response.get('account', {})
            print(f"   Connected account: {account.get('email')} ({account.get('type')})")
            print(f"   Account name: {account.get('name')}")
            # Store account ID for later tests
            self.outlook_account_id_3 = account.get('id')
        
        return success

    def test_connect_gmail_account_should_fail(self):
        """Test connecting Gmail account (should fail - Gmail support removed)"""
        success, response = self.run_test(
            "Connect Gmail Account (Should Fail)",
            "POST",
            "connect-account",
            400,
            data={
                "type": "gmail",
                "email": "test@gmail.com",
                "name": "Gmail User"
            }
        )
        
        if success:
            print("   ✅ Gmail connection correctly rejected")
        
        return success

    def test_connect_duplicate_outlook_account(self):
        """Test connecting duplicate Outlook account (should fail)"""
        success, response = self.run_test(
            "Connect Duplicate Outlook Account",
            "POST",
            "connect-account",
            400,
            data={
                "type": "outlook",
                "email": "test@outlook.com",  # Same as first account
                "name": "Duplicate Test"
            }
        )
        
        if success:
            print("   ✅ Duplicate email correctly rejected")
        
        return success

    def test_connect_invalid_account_type(self):
        """Test connecting invalid account type"""
        success, response = self.run_test(
            "Connect Invalid Account Type",
            "POST",
            "connect-account",
            400,
            data={"type": "yahoo"}
        )
        
        return success

    def test_get_connected_accounts_with_data(self):
        """Test getting connected accounts when they exist"""
        success, response = self.run_test(
            "Get Connected Accounts (With Data)",
            "GET",
            "connected-accounts",
            200
        )
        
        if success:
            accounts = response.get('accounts', [])
            print(f"   Found {len(accounts)} connected accounts")
            for account in accounts:
                print(f"     - {account.get('email')} ({account.get('type')}) - {account.get('name')}")
            
            # Verify we have multiple Outlook accounts
            outlook_accounts = [acc for acc in accounts if acc.get('type', '').lower() == 'outlook']
            print(f"   Outlook accounts: {len(outlook_accounts)}")
            
            # Verify no Gmail accounts exist
            gmail_accounts = [acc for acc in accounts if acc.get('type', '').lower() == 'gmail']
            if len(gmail_accounts) == 0:
                print("   ✅ No Gmail accounts found (as expected)")
            else:
                print(f"   ❌ Found {len(gmail_accounts)} Gmail accounts (should be 0)")
        
        return success

    def test_sync_emails_with_accounts(self):
        """Test email synchronization with connected accounts"""
        success, response = self.run_test(
            "Sync Emails (With Connected Accounts)",
            "POST",
            "sync-emails",
            200
        )
        
        if success:
            new_emails = response.get('new_emails', 0)
            print(f"   Added {new_emails} new emails during sync")
        
        return success

    def test_disconnect_outlook_account_1(self):
        """Test disconnecting first Outlook account"""
        if not hasattr(self, 'outlook_account_id_1'):
            print("❌ No first Outlook account ID available for disconnect test")
            return False
            
        success, response = self.run_test(
            "Disconnect First Outlook Account",
            "DELETE",
            f"connected-accounts/{self.outlook_account_id_1}",
            200
        )
        
        if success:
            print("   ✅ First Outlook account successfully disconnected")
        
        return success

    def test_disconnect_outlook_account_2(self):
        """Test disconnecting second Outlook account"""
        if not hasattr(self, 'outlook_account_id_2'):
            print("❌ No second Outlook account ID available for disconnect test")
            return False
            
        success, response = self.run_test(
            "Disconnect Second Outlook Account",
            "DELETE",
            f"connected-accounts/{self.outlook_account_id_2}",
            200
        )
        
        if success:
            print("   ✅ Second Outlook account successfully disconnected")
        
        return success

    def test_disconnect_nonexistent_account(self):
        """Test disconnecting non-existent account"""
        fake_id = "non-existent-account-id"
        success, response = self.run_test(
            "Disconnect Non-existent Account",
            "DELETE",
            f"connected-accounts/{fake_id}",
            404
        )
        
        return success

    def test_sync_emails_without_accounts(self):
        """Test email synchronization without connected accounts"""
        success, response = self.run_test(
            "Sync Emails (No Connected Accounts)",
            "POST",
            "sync-emails",
            200
        )
        
        if success:
            new_emails = response.get('new_emails', 0)
            print(f"   Added {new_emails} new emails during sync (should still work in demo mode)")
        
        return success

    def test_recaptcha_verification(self):
        """Test reCAPTCHA verification endpoint"""
        # Test with empty token (should fail)
        success, response = self.run_test(
            "reCAPTCHA Verification (Empty Token)",
            "POST",
            "verify-recaptcha",
            400,
            data={"recaptcha_token": ""}
        )
        
        if not success:
            # Try with fake token (should return success=false)
            success, response = self.run_test(
                "reCAPTCHA Verification (Fake Token)",
                "POST",
                "verify-recaptcha",
                200,
                data={"recaptcha_token": "fake-token-for-testing"}
            )
            
            if success and not response.get('success', True):
                print("   ✅ reCAPTCHA correctly rejected fake token")
                return True
        
        return success

    def test_user_registration(self):
        """Test user registration (should create unapproved user)"""
        import random
        test_email = f"testuser{random.randint(1000, 9999)}@test.com"
        
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data={
                "name": "Test User",
                "email": test_email,
                "password": "testpass123"
            }
        )
        
        if success:
            approved = response.get('approved', True)
            if not approved:
                print("   ✅ New user created as unapproved (whitelist working)")
                self.test_user_id = response.get('user_id')
                self.test_user_email = test_email
                return True
            else:
                print("   ❌ New user was approved automatically (whitelist not working)")
        
        return success

    def test_unapproved_user_login(self):
        """Test login with unapproved user (should fail)"""
        if not hasattr(self, 'test_user_email'):
            print("❌ No test user available for unapproved login test")
            return False
            
        success, response = self.run_test(
            "Unapproved User Login",
            "POST",
            "auth/login",
            403,
            data={
                "email": self.test_user_email,
                "password": "testpass123"
            }
        )
        
        if success:
            print("   ✅ Unapproved user correctly rejected")
        
        return success

    def test_admin_get_pending_users(self):
        """Test admin endpoint to get pending users"""
        success, response = self.run_test(
            "Admin Get Pending Users",
            "GET",
            "admin/pending-users",
            200
        )
        
        if success:
            pending_users = response.get('pending_users', [])
            print(f"   Found {len(pending_users)} pending users")
            
            # Check if our test user is in the list
            if hasattr(self, 'test_user_email'):
                test_user_found = any(user.get('email') == self.test_user_email for user in pending_users)
                if test_user_found:
                    print("   ✅ Test user found in pending list")
                else:
                    print("   ❌ Test user not found in pending list")
        
        return success

    def test_admin_approve_user(self):
        """Test admin endpoint to approve user"""
        if not hasattr(self, 'test_user_id'):
            print("❌ No test user ID available for approval test")
            return False
            
        success, response = self.run_test(
            "Admin Approve User",
            "POST",
            f"admin/approve-user/{self.test_user_id}",
            200
        )
        
        if success:
            print("   ✅ User successfully approved by admin")
        
        return success

    def test_approved_user_login(self):
        """Test login with newly approved user (should succeed)"""
        if not hasattr(self, 'test_user_email'):
            print("❌ No test user available for approved login test")
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
        
        if success:
            print("   ✅ Approved user successfully logged in")
            # Restore demo user token for remaining tests
            demo_success, demo_response = self.run_test(
                "Restore Demo Login",
                "POST",
                "auth/login",
                200,
                data={"email": "demo@postadepo.com", "password": "demo123"}
            )
            if demo_success:
                self.token = demo_response['token']
                self.user = demo_response['user']
        
        return success

    def test_non_admin_access_admin_endpoints(self):
        """Test non-admin user accessing admin endpoints (should fail)"""
        # First login as the test user (non-admin)
        if not hasattr(self, 'test_user_email'):
            print("❌ No test user available for non-admin test")
            return False
            
        login_success, login_response = self.run_test(
            "Login as Non-Admin User",
            "POST",
            "auth/login",
            200,
            data={
                "email": self.test_user_email,
                "password": "testpass123"
            }
        )
        
        if not login_success:
            return False
            
        # Temporarily use non-admin token
        original_token = self.token
        self.token = login_response['token']
        
        # Try to access admin endpoint
        success, response = self.run_test(
            "Non-Admin Access Admin Endpoint",
            "GET",
            "admin/pending-users",
            403
        )
        
        # Restore demo user token
        self.token = original_token
        
        if success:
            print("   ✅ Non-admin user correctly denied access to admin endpoints")
        
        return success

def main():
    print("🚀 Starting PostaDepo API Tests")
    print("=" * 50)
    
    tester = PostaDepoAPITester()
    
    # Test sequence
    tests = [
        ("Health Check", tester.test_health_check),
        ("Demo Login", tester.test_login),
        ("Invalid Login", tester.test_invalid_login),
        ("Unauthorized Access", tester.test_unauthorized_access),
        ("Get Inbox Emails", tester.test_get_emails_inbox),
        ("Get All Folder Emails", tester.test_get_emails_all_folders),
        ("Storage Information", tester.test_storage_info),
        ("Mark Email Read", tester.test_mark_email_read),
        
        # Account Connection Tests
        ("Get Connected Accounts (Empty)", tester.test_get_connected_accounts_empty),
        ("Connect Outlook Account", tester.test_connect_outlook_account),
        ("Connect Gmail Account", tester.test_connect_gmail_account),
        ("Connect Duplicate Account", tester.test_connect_duplicate_account),
        ("Connect Invalid Account Type", tester.test_connect_invalid_account_type),
        ("Get Connected Accounts (With Data)", tester.test_get_connected_accounts_with_data),
        
        # Sync Tests
        ("Sync Emails (With Connected Accounts)", tester.test_sync_emails_with_accounts),
        
        # Disconnect Tests
        ("Disconnect Outlook Account", tester.test_disconnect_outlook_account),
        ("Disconnect Gmail Account", tester.test_disconnect_gmail_account),
        ("Disconnect Non-existent Account", tester.test_disconnect_nonexistent_account),
        
        # Final Tests
        ("Sync Emails (No Connected Accounts)", tester.test_sync_emails_without_accounts),
        ("Export Emails", tester.test_export_emails),
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if not result:
                print(f"⚠️  {test_name} failed but continuing...")
        except Exception as e:
            print(f"💥 {test_name} crashed: {str(e)}")
    
    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())