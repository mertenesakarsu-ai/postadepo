import requests
import json

class FocusedEmailTester:
    def __init__(self):
        self.base_url = "https://outlook-connect.preview.emergentagent.com/api"
        self.token = None
        
    def login(self):
        response = requests.post(f"{self.base_url}/auth/login", json={
            "email": "demo@postadepo.com",
            "password": "demo123"
        })
        if response.status_code == 200:
            self.token = response.json()['token']
            return True
        return False
    
    def get_headers(self):
        return {'Authorization': f'Bearer {self.token}'}
    
    def test_new_email_features(self):
        print("🔍 TESTING NEW EMAIL FEATURES")
        print("=" * 50)
        
        if not self.login():
            print("❌ Login failed")
            return
        
        # Test 1: Email Model New Fields
        print("\n1. Testing Email Model New Fields (account_id, thread_id, attachments)")
        response = requests.get(f"{self.base_url}/emails?folder=inbox", headers=self.get_headers())
        
        if response.status_code == 200:
            emails = response.json()['emails']
            print(f"   ✅ Found {len(emails)} emails")
            
            # Check new fields
            fields_stats = {'account_id': 0, 'thread_id': 0, 'attachments': 0, 'account_info': 0}
            attachment_count = 0
            
            for email in emails[:10]:
                if email.get('account_id'):
                    fields_stats['account_id'] += 1
                if email.get('thread_id'):
                    fields_stats['thread_id'] += 1
                if 'attachments' in email:
                    fields_stats['attachments'] += 1
                    attachment_count += len(email['attachments'])
                if email.get('account_info'):
                    fields_stats['account_info'] += 1
            
            print(f"   📊 Field Statistics (first 10 emails):")
            print(f"      account_id: {fields_stats['account_id']}/10")
            print(f"      thread_id: {fields_stats['thread_id']}/10")
            print(f"      attachments field: {fields_stats['attachments']}/10")
            print(f"      account_info: {fields_stats['account_info']}/10")
            print(f"      Total attachments: {attachment_count}")
        
        # Test 2: Thread Endpoint
        print("\n2. Testing Thread Endpoint")
        if emails:
            thread_id = None
            for email in emails:
                if email.get('thread_id'):
                    thread_id = email['thread_id']
                    break
            
            if thread_id:
                response = requests.get(f"{self.base_url}/emails/thread/{thread_id}", headers=self.get_headers())
                if response.status_code == 200:
                    thread_data = response.json()
                    thread_emails = thread_data.get('emails', [])
                    print(f"   ✅ Thread endpoint working - found {len(thread_emails)} emails in thread")
                    print(f"   📧 Thread ID: {thread_data.get('thread_id')}")
                    
                    # Check if thread emails have account_info
                    with_account_info = sum(1 for e in thread_emails if e.get('account_info'))
                    print(f"   📊 Emails with account_info in thread: {with_account_info}/{len(thread_emails)}")
                else:
                    print(f"   ❌ Thread endpoint failed: {response.status_code}")
            else:
                print("   ❌ No thread_id found in emails")
        
        # Test 3: Attachment Variety
        print("\n3. Testing Attachment Variety")
        attachment_types = set()
        attachment_extensions = set()
        emails_with_attachments = 0
        
        for email in emails:
            attachments = email.get('attachments', [])
            if attachments:
                emails_with_attachments += 1
                for att in attachments:
                    if att.get('type'):
                        attachment_types.add(att['type'])
                    if att.get('name') and '.' in att['name']:
                        ext = att['name'].split('.')[-1].lower()
                        attachment_extensions.add(ext)
        
        print(f"   ✅ Emails with attachments: {emails_with_attachments}")
        print(f"   📎 Attachment types: {len(attachment_types)}")
        print(f"   📎 Extensions found: {sorted(attachment_extensions)}")
        
        expected_extensions = {'pdf', 'docx', 'xlsx', 'png', 'jpg', 'pptx'}
        found_expected = attachment_extensions.intersection(expected_extensions)
        print(f"   ✅ Expected extensions found: {sorted(found_expected)}")
        
        # Test 4: Connect Account and Test Integration
        print("\n4. Testing Account Integration")
        
        # Connect a test account
        connect_response = requests.post(f"{self.base_url}/connect-account", 
                                       json={
                                           "type": "outlook",
                                           "email": "test.integration@outlook.com",
                                           "name": "Test Integration"
                                       }, 
                                       headers=self.get_headers())
        
        if connect_response.status_code == 200:
            account = connect_response.json()['account']
            print(f"   ✅ Connected test account: {account['email']}")
            
            # Sync emails to generate new ones with this account
            sync_response = requests.post(f"{self.base_url}/sync-emails", headers=self.get_headers())
            if sync_response.status_code == 200:
                new_emails = sync_response.json().get('new_emails', 0)
                print(f"   ✅ Synced {new_emails} new emails")
                
                # Check if new emails have account_info
                emails_response = requests.get(f"{self.base_url}/emails?folder=inbox", headers=self.get_headers())
                if emails_response.status_code == 200:
                    updated_emails = emails_response.json()['emails']
                    recent_sync_emails = [e for e in updated_emails if 'Senkronizasyon' in e.get('subject', '')][:new_emails]
                    
                    with_account_info = sum(1 for e in recent_sync_emails if e.get('account_info'))
                    print(f"   ✅ New sync emails with account_info: {with_account_info}/{len(recent_sync_emails)}")
                    
                    if recent_sync_emails and recent_sync_emails[0].get('account_info'):
                        account_info = recent_sync_emails[0]['account_info']
                        print(f"   📧 Sample account_info: {account_info['name']} ({account_info['email']})")
        
        # Test 5: Duplicate Account Prevention
        print("\n5. Testing Duplicate Account Prevention")
        duplicate_response = requests.post(f"{self.base_url}/connect-account", 
                                         json={
                                             "type": "outlook",
                                             "email": "test.integration@outlook.com",  # Same email
                                             "name": "Duplicate Test"
                                         }, 
                                         headers=self.get_headers())
        
        if duplicate_response.status_code == 400:
            print("   ✅ Duplicate account correctly rejected")
        else:
            print(f"   ❌ Duplicate account not rejected: {duplicate_response.status_code}")
        
        print("\n" + "=" * 50)
        print("🎯 NEW EMAIL FEATURES TEST COMPLETE")

if __name__ == "__main__":
    tester = FocusedEmailTester()
    tester.test_new_email_features()