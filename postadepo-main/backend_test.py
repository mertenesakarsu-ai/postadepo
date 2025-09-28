import requests
import sys
import json
from datetime import datetime

class PostaDepoAPITester:
    def __init__(self, base_url="https://userdepo-panel.preview.emergentagent.com/api"):
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
        ("Sync Emails", tester.test_sync_emails),
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