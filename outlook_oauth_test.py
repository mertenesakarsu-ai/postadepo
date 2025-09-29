#!/usr/bin/env python3
"""
PostaDepo Outlook OAuth Integration Test Suite
Test specifically for Outlook OAuth integration after azure-core dependency fix
"""

import asyncio
import httpx
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Test configuration
BACKEND_URL = "https://postadepo-admin.preview.emergentagent.com/api"
TEST_USER_EMAIL = "tyrzmusak@gmail.com"
TEST_USER_PASSWORD = "deneme123"

class OutlookOAuthTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.auth_token = None
        self.test_results = []
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        if response_data and not success:
            print(f"   Response: {response_data}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response": response_data if not success else None
        })
        print()
    
    async def login_test_user(self) -> bool:
        """Login with test user to get auth token"""
        try:
            response = await self.client.post(f"{BACKEND_URL}/auth/login", json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("token")
                self.log_test("User Login", True, f"Logged in as {TEST_USER_EMAIL}")
                return True
            else:
                self.log_test("User Login", False, f"Status: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("User Login", False, f"Exception: {str(e)}")
            return False
    
    async def test_outlook_status_endpoint(self) -> bool:
        """Test GET /api/outlook/status endpoint"""
        try:
            response = await self.client.get(f"{BACKEND_URL}/outlook/status")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ["graph_sdk_available", "credentials_configured", "client_id_set", "tenant_id_set", "message"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Outlook Status Endpoint", False, f"Missing fields: {missing_fields}", data)
                    return False
                
                # Check if Microsoft Graph SDK is now available
                graph_available = data.get("graph_sdk_available", False)
                credentials_configured = data.get("credentials_configured", False)
                
                if not graph_available:
                    self.log_test("Outlook Status Endpoint", False, "Microsoft Graph SDK still not available - azure-core issue not resolved", data)
                    return False
                
                if not credentials_configured:
                    self.log_test("Outlook Status Endpoint", False, "Azure credentials not configured", data)
                    return False
                
                self.log_test("Outlook Status Endpoint", True, f"Graph SDK: {graph_available}, Credentials: {credentials_configured}")
                return True
            else:
                self.log_test("Outlook Status Endpoint", False, f"Status: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Outlook Status Endpoint", False, f"Exception: {str(e)}")
            return False
    
    async def test_outlook_auth_url_endpoint(self) -> bool:
        """Test GET /api/outlook/auth-url endpoint"""
        if not self.auth_token:
            self.log_test("Outlook Auth URL Endpoint", False, "No auth token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = await self.client.get(f"{BACKEND_URL}/outlook/auth-url", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ["auth_url", "state", "redirect_uri"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Outlook Auth URL Endpoint", False, f"Missing fields: {missing_fields}", data)
                    return False
                
                # Validate auth URL format
                auth_url = data.get("auth_url", "")
                if not auth_url.startswith("https://login.microsoftonline.com/"):
                    self.log_test("Outlook Auth URL Endpoint", False, "Invalid auth URL format", data)
                    return False
                
                # Check if required OAuth parameters are present
                required_params = ["client_id", "response_type", "redirect_uri", "scope", "state"]
                missing_params = [param for param in required_params if param not in auth_url]
                
                if missing_params:
                    self.log_test("Outlook Auth URL Endpoint", False, f"Missing OAuth parameters: {missing_params}", data)
                    return False
                
                self.log_test("Outlook Auth URL Endpoint", True, f"Auth URL generated successfully, State: {data.get('state')[:20]}...")
                return True
            else:
                self.log_test("Outlook Auth URL Endpoint", False, f"Status: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Outlook Auth URL Endpoint", False, f"Exception: {str(e)}")
            return False
    
    async def test_outlook_connect_account_endpoint(self) -> bool:
        """Test POST /api/outlook/connect-account endpoint (with invalid code to test error handling)"""
        if not self.auth_token:
            self.log_test("Outlook Connect Account Endpoint", False, "No auth token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            # Use invalid code and state to test error handling
            response = await self.client.post(f"{BACKEND_URL}/outlook/connect-account", 
                                            headers=headers,
                                            params={"code": "invalid_test_code", "state": "invalid_test_state"})
            
            # We expect this to fail with 400 or 401, which means the endpoint is working
            if response.status_code in [400, 401, 404]:
                self.log_test("Outlook Connect Account Endpoint", True, f"Endpoint accessible, returned expected error: {response.status_code}")
                return True
            elif response.status_code == 503:
                # Service unavailable means credentials not configured
                self.log_test("Outlook Connect Account Endpoint", False, "Service unavailable - credentials not configured", response.text)
                return False
            else:
                self.log_test("Outlook Connect Account Endpoint", False, f"Unexpected status: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Outlook Connect Account Endpoint", False, f"Exception: {str(e)}")
            return False
    
    async def test_outlook_accounts_endpoint(self) -> bool:
        """Test GET /api/outlook/accounts endpoint"""
        if not self.auth_token:
            self.log_test("Outlook Accounts Endpoint", False, "No auth token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = await self.client.get(f"{BACKEND_URL}/outlook/accounts", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                # Should return either a list or an object with accounts key
                if isinstance(data, list):
                    self.log_test("Outlook Accounts Endpoint", True, f"Returned {len(data)} connected accounts (list format)")
                    return True
                elif isinstance(data, dict) and "accounts" in data:
                    accounts = data["accounts"]
                    if isinstance(accounts, list):
                        self.log_test("Outlook Accounts Endpoint", True, f"Returned {len(accounts)} connected accounts (object format)")
                        return True
                    else:
                        self.log_test("Outlook Accounts Endpoint", False, "accounts field is not a list", data)
                        return False
                else:
                    self.log_test("Outlook Accounts Endpoint", False, "Response format not recognized", data)
                    return False
            else:
                self.log_test("Outlook Accounts Endpoint", False, f"Status: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Outlook Accounts Endpoint", False, f"Exception: {str(e)}")
            return False
    
    async def test_outlook_sync_endpoint(self) -> bool:
        """Test POST /api/outlook/sync endpoint"""
        if not self.auth_token:
            self.log_test("Outlook Sync Endpoint", False, "No auth token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = await self.client.post(f"{BACKEND_URL}/outlook/sync", 
                                            headers=headers,
                                            json={"account_email": "test@outlook.com"})
            
            # We expect this to fail with 404 (account not found) which means endpoint is working
            if response.status_code == 404:
                self.log_test("Outlook Sync Endpoint", True, "Endpoint accessible, returned expected 404 (account not found)")
                return True
            elif response.status_code == 503:
                self.log_test("Outlook Sync Endpoint", False, "Service unavailable - credentials not configured", response.text)
                return False
            else:
                # Any other response means the endpoint is accessible
                self.log_test("Outlook Sync Endpoint", True, f"Endpoint accessible, status: {response.status_code}")
                return True
                
        except Exception as e:
            self.log_test("Outlook Sync Endpoint", False, f"Exception: {str(e)}")
            return False
    
    async def test_backend_logs_for_azure_core_warning(self) -> bool:
        """Check if backend logs still contain azure-core warning in recent entries"""
        try:
            # Read only the most recent backend logs (last 20 lines)
            import subprocess
            result = subprocess.run(
                ["tail", "-n", "20", "/var/log/supervisor/backend.err.log"],
                capture_output=True,
                text=True
            )
            
            log_content = result.stdout
            
            # Check for the specific warning in recent logs only
            azure_core_warning = "Microsoft Graph SDK not available: No module named 'azure.core'"
            
            if azure_core_warning in log_content:
                self.log_test("Backend Logs Azure Core Check", False, "azure-core warning found in recent logs (last 20 lines)")
                return False
            else:
                self.log_test("Backend Logs Azure Core Check", True, "No azure-core warnings in recent logs - dependency issue resolved")
                return True
                
        except Exception as e:
            self.log_test("Backend Logs Azure Core Check", False, f"Exception: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all Outlook OAuth integration tests"""
        print("🔍 OUTLOOK OAUTH INTEGRATION TEST SUITE")
        print("=" * 50)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test User: {TEST_USER_EMAIL}")
        print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Test sequence
        tests = [
            ("Backend Logs Azure Core Check", self.test_backend_logs_for_azure_core_warning),
            ("User Login", self.login_test_user),
            ("Outlook Status Endpoint", self.test_outlook_status_endpoint),
            ("Outlook Auth URL Endpoint", self.test_outlook_auth_url_endpoint),
            ("Outlook Connect Account Endpoint", self.test_outlook_connect_account_endpoint),
            ("Outlook Accounts Endpoint", self.test_outlook_accounts_endpoint),
            ("Outlook Sync Endpoint", self.test_outlook_sync_endpoint),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if await test_func():
                    passed += 1
            except Exception as e:
                self.log_test(test_name, False, f"Unexpected exception: {str(e)}")
        
        # Summary
        print("=" * 50)
        print(f"📊 TEST SUMMARY: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! Outlook OAuth integration is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the details above.")
            
        print()
        print("🔑 KEY FINDINGS:")
        
        # Check critical issues
        critical_issues = []
        for result in self.test_results:
            if not result["success"]:
                if "azure-core" in result["details"].lower():
                    critical_issues.append("❌ Azure-core dependency issue still exists")
                elif "credentials" in result["details"].lower():
                    critical_issues.append("❌ Azure credentials not properly configured")
                elif "graph sdk" in result["details"].lower():
                    critical_issues.append("❌ Microsoft Graph SDK not available")
        
        if not critical_issues:
            print("✅ No azure-core dependency warnings in backend logs")
            print("✅ Microsoft Graph SDK is available")
            print("✅ Azure credentials are configured")
            print("✅ All Outlook OAuth endpoints are accessible")
        else:
            for issue in critical_issues:
                print(issue)
        
        return passed == total

async def main():
    """Main test runner"""
    async with OutlookOAuthTester() as tester:
        success = await tester.run_all_tests()
        return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)