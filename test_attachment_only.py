#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class AttachmentTester:
    def __init__(self, base_url="https://mail-connect-2.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.user = None

    def login(self):
        """Login as demo user"""
        url = f"{self.base_url}/auth/login"
        response = requests.post(url, json={"email": "demo@postadepo.com", "password": "demo123"})
        
        if response.status_code == 200:
            data = response.json()
            self.token = data['token']
            self.user = data['user']
            print(f"✅ Logged in as: {self.user.get('email')}")
            return True
        else:
            print(f"❌ Login failed: {response.status_code}")
            return False

    def test_attachment_download_fix(self):
        """Test the attachment download fix for Unicode filenames"""
        print("\n🎯 TESTING ATTACHMENT DOWNLOAD FIX")
        print("=" * 50)
        
        # Get emails with attachments
        url = f"{self.base_url}/emails?folder=inbox"
        headers = {'Authorization': f'Bearer {self.token}'}
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print("❌ Failed to get emails")
            return False
        
        emails = response.json().get('emails', [])
        
        # Find an attachment with Unicode characters
        unicode_attachment = None
        regular_attachment = None
        
        for email in emails:
            for attachment in email.get('attachments', []):
                att_name = attachment.get('name', '')
                if any(ord(c) > 127 for c in att_name):  # Contains non-ASCII characters
                    unicode_attachment = attachment
                    print(f"📎 Found Unicode attachment: {att_name}")
                elif not regular_attachment:
                    regular_attachment = attachment
                    print(f"📎 Found regular attachment: {att_name}")
                
                if unicode_attachment and regular_attachment:
                    break
            if unicode_attachment and regular_attachment:
                break
        
        success_count = 0
        total_tests = 0
        
        # Test Unicode attachment
        if unicode_attachment:
            total_tests += 1
            print(f"\n🔤 Testing Unicode attachment: {unicode_attachment['name']}")
            if self.test_single_download(unicode_attachment['id'], unicode_attachment['name']):
                success_count += 1
        
        # Test regular attachment
        if regular_attachment:
            total_tests += 1
            print(f"\n📄 Testing regular attachment: {regular_attachment['name']}")
            if self.test_single_download(regular_attachment['id'], regular_attachment['name']):
                success_count += 1
        
        # Test error cases
        total_tests += 2
        print(f"\n🚫 Testing invalid attachment ID...")
        if self.test_error_case("invalid-id", 404):
            success_count += 1
            
        print(f"\n🚫 Testing non-existent attachment ID...")
        if self.test_error_case("00000000-0000-0000-0000-000000000000", 404):
            success_count += 1
        
        print(f"\n📊 RESULTS: {success_count}/{total_tests} tests passed")
        return success_count == total_tests

    def test_single_download(self, attachment_id, expected_name):
        """Test downloading a single attachment"""
        try:
            url = f"{self.base_url}/attachments/download/{attachment_id}"
            headers = {'Authorization': f'Bearer {self.token}'}
            
            response = requests.get(url, headers=headers, stream=True)
            
            if response.status_code != 200:
                print(f"   ❌ HTTP {response.status_code}: {response.text[:100]}")
                return False
            
            # Check response headers
            content_disposition = response.headers.get('Content-Disposition', '')
            content_type = response.headers.get('Content-Type', '')
            content_length = response.headers.get('Content-Length', '')
            
            print(f"   📋 Response headers:")
            print(f"      Content-Type: {content_type}")
            print(f"      Content-Disposition: {content_disposition}")
            print(f"      Content-Length: {content_length}")
            
            # Read content
            content = response.content
            actual_size = len(content)
            
            print(f"   📊 Content size: {actual_size} bytes")
            
            if actual_size == 0:
                print(f"   ❌ Empty content received")
                return False
            
            print(f"   ✅ Download successful")
            return True
            
        except Exception as e:
            print(f"   ❌ Download error: {str(e)}")
            return False

    def test_error_case(self, attachment_id, expected_status):
        """Test error scenarios"""
        try:
            url = f"{self.base_url}/attachments/download/{attachment_id}"
            headers = {'Authorization': f'Bearer {self.token}'}
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == expected_status:
                print(f"   ✅ Error test passed: HTTP {response.status_code}")
                return True
            else:
                print(f"   ❌ Error test failed: Expected {expected_status}, got {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error test exception: {str(e)}")
            return False

def main():
    tester = AttachmentTester()
    
    if not tester.login():
        return 1
    
    if tester.test_attachment_download_fix():
        print("\n🎉 All attachment download tests passed!")
        return 0
    else:
        print("\n❌ Some attachment download tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())