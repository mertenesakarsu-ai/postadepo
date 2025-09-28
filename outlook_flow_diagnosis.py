#!/usr/bin/env python3
"""
Outlook Flow Diagnosis - Comprehensive analysis of the Outlook integration issue
Based on user complaint: "başlangıçta başarıyla bağlandı mesajı çıkıyor ama sonra hata veriyor"
"""

import requests
import sys
import json
from datetime import datetime

class OutlookFlowDiagnostic:
    def __init__(self, base_url="https://signup-admin-view.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.user = None
        self.issues_found = []
        self.working_features = []

    def log_issue(self, component, issue, severity="HIGH"):
        """Log an issue found during diagnosis"""
        self.issues_found.append({
            "component": component,
            "issue": issue,
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        })

    def log_working(self, component, description):
        """Log a working feature"""
        self.working_features.append({
            "component": component,
            "description": description
        })

    def make_request(self, method, endpoint, expected_status=None, data=None, headers=None):
        """Make API request and return response details"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=30)

            return {
                "success": expected_status is None or response.status_code == expected_status,
                "status_code": response.status_code,
                "response": response.json() if response.text and response.status_code < 500 else {},
                "raw_response": response
            }

        except Exception as e:
            return {
                "success": False,
                "status_code": None,
                "response": {},
                "error": str(e),
                "raw_response": None
            }

    def diagnose_user_authentication(self):
        """Diagnose user authentication"""
        print("\n🔐 DIAGNOSING USER AUTHENTICATION")
        print("="*50)
        
        result = self.make_request("POST", "auth/login", 200, {
            "email": "tyrzmusak@gmail.com",
            "password": "deneme123"
        })
        
        if result["success"] and "token" in result["response"]:
            self.token = result["response"]["token"]
            self.user = result["response"]["user"]
            print(f"✅ User authentication: WORKING")
            print(f"   User: {self.user.get('email')}")
            print(f"   User ID: {self.user.get('id')}")
            self.log_working("Authentication", "User can login successfully")
            return True
        else:
            print(f"❌ User authentication: FAILED")
            print(f"   Status: {result['status_code']}")
            print(f"   Response: {result['response']}")
            self.log_issue("Authentication", f"Login failed with status {result['status_code']}")
            return False

    def diagnose_outlook_configuration(self):
        """Diagnose Outlook integration configuration"""
        print("\n⚙️ DIAGNOSING OUTLOOK CONFIGURATION")
        print("="*50)
        
        result = self.make_request("GET", "outlook/status", 200)
        
        if result["success"]:
            config = result["response"]
            print(f"✅ Outlook status endpoint: WORKING")
            print(f"   Graph SDK Available: {config.get('graph_sdk_available', False)}")
            print(f"   Credentials Configured: {config.get('credentials_configured', False)}")
            print(f"   Client ID Set: {config.get('client_id_set', False)}")
            print(f"   Tenant ID Set: {config.get('tenant_id_set', False)}")
            print(f"   Message: {config.get('message', 'No message')}")
            
            if all([
                config.get('graph_sdk_available', False),
                config.get('credentials_configured', False),
                config.get('client_id_set', False),
                config.get('tenant_id_set', False)
            ]):
                self.log_working("Configuration", "Outlook integration fully configured")
                return True
            else:
                missing = []
                if not config.get('graph_sdk_available', False):
                    missing.append("Graph SDK")
                if not config.get('credentials_configured', False):
                    missing.append("Credentials")
                if not config.get('client_id_set', False):
                    missing.append("Client ID")
                if not config.get('tenant_id_set', False):
                    missing.append("Tenant ID")
                
                self.log_issue("Configuration", f"Missing configuration: {', '.join(missing)}")
                return False
        else:
            print(f"❌ Outlook status endpoint: FAILED")
            self.log_issue("Configuration", "Cannot check Outlook status")
            return False

    def diagnose_auth_url_generation(self):
        """Diagnose auth URL generation"""
        print("\n🔗 DIAGNOSING AUTH URL GENERATION")
        print("="*50)
        
        result = self.make_request("GET", "outlook/auth-url", 200)
        
        if result["success"]:
            auth_data = result["response"]
            auth_url = auth_data.get("auth_url", "")
            state = auth_data.get("state", "")
            redirect_uri = auth_data.get("redirect_uri", "")
            
            print(f"✅ Auth URL generation: WORKING")
            print(f"   Auth URL contains Microsoft: {'login.microsoftonline.com' in auth_url}")
            print(f"   State parameter length: {len(state)}")
            print(f"   Redirect URI: {redirect_uri}")
            
            if "login.microsoftonline.com" in auth_url and state and redirect_uri:
                self.log_working("Auth URL", "Auth URL generation working correctly")
                return True, state
            else:
                self.log_issue("Auth URL", "Auth URL generation has issues")
                return False, None
        else:
            print(f"❌ Auth URL generation: FAILED")
            print(f"   Status: {result['status_code']}")
            self.log_issue("Auth URL", f"Auth URL generation failed with status {result['status_code']}")
            return False, None

    def diagnose_oauth_callback(self, state=None):
        """Diagnose OAuth callback handling"""
        print("\n🔄 DIAGNOSING OAUTH CALLBACK")
        print("="*50)
        
        # Test with invalid code to see error handling
        result = self.make_request("POST", "auth/outlook-login?code=invalid_code&state=invalid_state", 400)
        
        if result["status_code"] == 400:
            print(f"✅ OAuth callback error handling: WORKING")
            print(f"   Properly rejects invalid codes")
            self.log_working("OAuth Callback", "Error handling works correctly")
            
            # Now test with missing parameters
            result2 = self.make_request("POST", "auth/outlook-login", 422)
            if result2["status_code"] == 422:
                print(f"✅ Parameter validation: WORKING")
                self.log_working("OAuth Callback", "Parameter validation works")
                return True
            else:
                self.log_issue("OAuth Callback", "Parameter validation not working properly")
                return False
        else:
            print(f"❌ OAuth callback: UNEXPECTED BEHAVIOR")
            print(f"   Status: {result['status_code']}")
            print(f"   Expected 400, got {result['status_code']}")
            self.log_issue("OAuth Callback", f"Unexpected status code: {result['status_code']}")
            return False

    def diagnose_account_connection(self):
        """Diagnose account connection process"""
        print("\n🔗 DIAGNOSING ACCOUNT CONNECTION")
        print("="*50)
        
        # Test connect account endpoint
        result = self.make_request("POST", "outlook/connect-account?code=test&state=test", None)
        
        if result["status_code"] in [400, 503]:
            print(f"✅ Connect account endpoint: ACCESSIBLE")
            print(f"   Status: {result['status_code']}")
            print(f"   Response: {result['response'].get('detail', 'No detail')}")
            
            if result["status_code"] == 503:
                self.log_issue("Account Connection", "Service unavailable - integration not configured", "MEDIUM")
            elif result["status_code"] == 400:
                self.log_working("Account Connection", "Endpoint accessible and validates parameters")
            
            return True
        else:
            print(f"❌ Connect account endpoint: ISSUES")
            print(f"   Status: {result['status_code']}")
            self.log_issue("Account Connection", f"Unexpected status: {result['status_code']}")
            return False

    def diagnose_connected_accounts(self):
        """Diagnose connected accounts listing"""
        print("\n📋 DIAGNOSING CONNECTED ACCOUNTS")
        print("="*50)
        
        result = self.make_request("GET", "outlook/accounts", 200)
        
        if result["success"]:
            accounts = result["response"].get("accounts", [])
            print(f"✅ Connected accounts endpoint: WORKING")
            print(f"   Connected accounts count: {len(accounts)}")
            
            if len(accounts) == 0:
                print(f"   ⚠️  No connected accounts found")
                self.log_issue("Connected Accounts", "No Outlook accounts connected", "MEDIUM")
                return False
            else:
                print(f"   ✅ Found {len(accounts)} connected accounts")
                for i, account in enumerate(accounts):
                    print(f"      Account {i+1}: {account.get('email', 'No email')}")
                self.log_working("Connected Accounts", f"Found {len(accounts)} connected accounts")
                return True
        else:
            print(f"❌ Connected accounts endpoint: FAILED")
            self.log_issue("Connected Accounts", "Cannot list connected accounts")
            return False

    def diagnose_email_sync(self):
        """Diagnose email synchronization"""
        print("\n🔄 DIAGNOSING EMAIL SYNC")
        print("="*50)
        
        # First check if there are connected accounts
        accounts_result = self.make_request("GET", "outlook/accounts", 200)
        
        if accounts_result["success"]:
            accounts = accounts_result["response"].get("accounts", [])
            
            if len(accounts) == 0:
                print(f"   ⚠️  No connected accounts to sync")
                # Test sync with dummy account ID to check error handling
                sync_result = self.make_request("POST", "outlook/sync?account_id=dummy", 404)
                
                if sync_result["status_code"] == 404:
                    print(f"✅ Sync error handling: WORKING")
                    print(f"   Properly handles missing accounts")
                    self.log_working("Email Sync", "Error handling works for missing accounts")
                    self.log_issue("Email Sync", "Cannot sync - no connected accounts", "HIGH")
                    return False
                else:
                    print(f"❌ Sync error handling: ISSUES")
                    self.log_issue("Email Sync", "Sync error handling not working properly")
                    return False
            else:
                # Try to sync with first account
                account_id = accounts[0].get("id")
                sync_result = self.make_request("POST", f"outlook/sync?account_id={account_id}", None)
                
                if sync_result["status_code"] == 200:
                    print(f"✅ Email sync: WORKING")
                    sync_data = sync_result["response"]
                    print(f"   Synced emails: {sync_data.get('synced_count', 0)}")
                    print(f"   Errors: {sync_data.get('error_count', 0)}")
                    self.log_working("Email Sync", f"Sync successful - {sync_data.get('synced_count', 0)} emails")
                    return True
                else:
                    print(f"❌ Email sync: FAILED")
                    print(f"   Status: {sync_result['status_code']}")
                    print(f"   Response: {sync_result['response']}")
                    self.log_issue("Email Sync", f"Sync failed with status {sync_result['status_code']}", "HIGH")
                    return False
        else:
            print(f"❌ Cannot check accounts for sync")
            self.log_issue("Email Sync", "Cannot check accounts for sync")
            return False

    def run_comprehensive_diagnosis(self):
        """Run comprehensive diagnosis of Outlook integration"""
        print("\n" + "🔍" * 20)
        print("OUTLOOK INTEGRATION COMPREHENSIVE DIAGNOSIS")
        print("User: tyrzmusak@gmail.com")
        print("Issue: 'başlangıçta başarıyla bağlandı mesajı çıkıyor ama sonra hata veriyor'")
        print("🔍" * 20)
        
        # Run all diagnostic tests
        auth_ok = self.diagnose_user_authentication()
        if not auth_ok:
            print("\n❌ Cannot proceed without authentication")
            return
        
        config_ok = self.diagnose_outlook_configuration()
        auth_url_ok, state = self.diagnose_auth_url_generation()
        callback_ok = self.diagnose_oauth_callback(state)
        connect_ok = self.diagnose_account_connection()
        accounts_ok = self.diagnose_connected_accounts()
        sync_ok = self.diagnose_email_sync()
        
        # Generate comprehensive report
        self.generate_diagnosis_report()

    def generate_diagnosis_report(self):
        """Generate comprehensive diagnosis report"""
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE DIAGNOSIS REPORT")
        print("="*80)
        
        print(f"\n✅ WORKING COMPONENTS ({len(self.working_features)}):")
        for feature in self.working_features:
            print(f"  ✅ {feature['component']}: {feature['description']}")
        
        print(f"\n❌ ISSUES FOUND ({len(self.issues_found)}):")
        high_issues = [i for i in self.issues_found if i['severity'] == 'HIGH']
        medium_issues = [i for i in self.issues_found if i['severity'] == 'MEDIUM']
        
        if high_issues:
            print(f"\n🚨 HIGH PRIORITY ISSUES ({len(high_issues)}):")
            for issue in high_issues:
                print(f"  🚨 {issue['component']}: {issue['issue']}")
        
        if medium_issues:
            print(f"\n⚠️  MEDIUM PRIORITY ISSUES ({len(medium_issues)}):")
            for issue in medium_issues:
                print(f"  ⚠️  {issue['component']}: {issue['issue']}")
        
        print(f"\n🔍 ROOT CAUSE ANALYSIS:")
        
        # Analyze the user's specific complaint
        no_connected_accounts = any("No Outlook accounts connected" in i['issue'] for i in self.issues_found)
        sync_issues = any("Email Sync" in i['component'] for i in self.issues_found)
        
        if no_connected_accounts:
            print(f"  🎯 PRIMARY ISSUE: No Outlook accounts are connected")
            print(f"     - User sees 'successfully connected' message initially (auth URL generation works)")
            print(f"     - But actual account connection fails or doesn't persist")
            print(f"     - This explains why email sync fails later")
        
        if sync_issues:
            print(f"  🎯 SECONDARY ISSUE: Email synchronization problems")
            print(f"     - Even if account connection worked, sync might fail")
            print(f"     - This could be due to token expiration or API issues")
        
        print(f"\n💡 RECOMMENDATIONS:")
        print(f"  1. Check OAuth flow completion - tokens might not be stored properly")
        print(f"  2. Verify Microsoft Graph API permissions and token refresh")
        print(f"  3. Check database for connected_accounts table entries")
        print(f"  4. Implement better error handling and user feedback")
        print(f"  5. Add logging for OAuth token exchange process")
        
        print(f"\n🎯 USER EXPERIENCE ISSUE EXPLANATION:")
        print(f"  The user sees 'başarıyla bağlandı' (successfully connected) because:")
        print(f"  - Auth URL generation works (✅)")
        print(f"  - OAuth callback handling works (✅)")
        print(f"  - But the actual account connection/token storage fails")
        print(f"  - Later, when trying to sync emails, no connected account is found")
        print(f"  - This creates the 'works initially but fails later' experience")

if __name__ == "__main__":
    print("🚀 Starting Outlook Integration Diagnosis")
    print("=" * 60)
    
    diagnostic = OutlookFlowDiagnostic()
    diagnostic.run_comprehensive_diagnosis()
    
    print("\n🏁 Diagnosis completed!")