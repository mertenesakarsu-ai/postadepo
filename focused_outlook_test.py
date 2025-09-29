#!/usr/bin/env python3
"""
Focused Outlook OAuth Integration Test
Tests the specific requirements from the user request
"""

import requests
import sys
import json
import subprocess
from datetime import datetime

class FocusedOutlookTester:
    def __init__(self):
        self.base_url = "https://mail-sync-issue-1.preview.emergentagent.com/api"
        self.token = None
        self.user = None
        self.tests_passed = 0
        self.tests_total = 0

    def log_test(self, test_name, success, details="", response_data=None):
        """Log test result"""
        self.tests_total += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name}")
        else:
            print(f"❌ {test_name}")
        
        if details:
            print(f"   {details}")
        if response_data and not success:
            print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
        print()

    def test_demo_login(self):
        """1. Demo kullanıcısı ile login olabilmeyi test et (demo@postadepo.com / demo123)"""
        print("🎯 TEST 1: Demo kullanıcısı login testi")
        print("-" * 50)
        
        try:
            response = requests.post(f"{self.base_url}/auth/login", json={
                "email": "demo@postadepo.com",
                "password": "demo123"
            })
            
            if response.status_code == 200:
                data = response.json()
                if 'token' in data and 'user' in data:
                    self.token = data['token']
                    self.user = data['user']
                    self.log_test("Demo User Login", True, 
                                f"Successfully logged in as {self.user.get('email')}")
                    return True
                else:
                    self.log_test("Demo User Login", False, 
                                "Response missing token or user", data)
                    return False
            else:
                self.log_test("Demo User Login", False, 
                            f"HTTP {response.status_code}", response.json())
                return False
                
        except Exception as e:
            self.log_test("Demo User Login", False, f"Exception: {str(e)}")
            return False

    def test_outlook_status(self):
        """2. GET /api/outlook/status endpoint'ini test et - graph_sdk_available true olmalı"""
        print("🎯 TEST 2: Outlook Status Endpoint")
        print("-" * 50)
        
        try:
            response = requests.get(f"{self.base_url}/outlook/status")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check critical fields
                graph_sdk_available = data.get('graph_sdk_available', False)
                credentials_configured = data.get('credentials_configured', False)
                
                details = []
                details.append(f"graph_sdk_available: {graph_sdk_available}")
                details.append(f"credentials_configured: {credentials_configured}")
                
                # Show all response fields
                for key, value in data.items():
                    if key not in ['graph_sdk_available', 'credentials_configured']:
                        details.append(f"{key}: {value}")
                
                if graph_sdk_available:
                    self.log_test("Outlook Status - Graph SDK Available", True, 
                                "\n   ".join(details))
                    return True
                else:
                    self.log_test("Outlook Status - Graph SDK Available", False, 
                                f"graph_sdk_available is {graph_sdk_available}\n   " + "\n   ".join(details))
                    return False
            else:
                self.log_test("Outlook Status - Graph SDK Available", False, 
                            f"HTTP {response.status_code}", response.json())
                return False
                
        except Exception as e:
            self.log_test("Outlook Status - Graph SDK Available", False, f"Exception: {str(e)}")
            return False

    def test_outlook_auth_url(self):
        """3. GET /api/outlook/auth-url endpoint'ini test et - OAuth URL generate edilmeli"""
        print("🎯 TEST 3: Outlook Auth URL Generation")
        print("-" * 50)
        
        if not self.token:
            self.log_test("Outlook Auth URL Generation", False, "No auth token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.base_url}/outlook/auth-url", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                auth_url = data.get('auth_url', '')
                state = data.get('state', '')
                
                details = []
                details.append(f"auth_url length: {len(auth_url)} characters")
                details.append(f"state: {state}")
                
                if auth_url:
                    details.append(f"auth_url preview: {auth_url[:100]}...")
                    
                    # Validate OAuth URL components
                    required_components = [
                        'login.microsoftonline.com',
                        'oauth2/v2.0/authorize',
                        'client_id=',
                        'response_type=code',
                        'redirect_uri=',
                        'scope=',
                        'state='
                    ]
                    
                    missing_components = [comp for comp in required_components if comp not in auth_url]
                    
                    if not missing_components:
                        details.append("✅ All required OAuth components present")
                        self.log_test("Outlook Auth URL Generation", True, "\n   ".join(details))
                        return True
                    else:
                        details.append(f"❌ Missing components: {missing_components}")
                        self.log_test("Outlook Auth URL Generation", False, "\n   ".join(details))
                        return False
                else:
                    self.log_test("Outlook Auth URL Generation", False, "No auth_url in response", data)
                    return False
            else:
                self.log_test("Outlook Auth URL Generation", False, 
                            f"HTTP {response.status_code}", response.json())
                return False
                
        except Exception as e:
            self.log_test("Outlook Auth URL Generation", False, f"Exception: {str(e)}")
            return False

    def test_connected_accounts(self):
        """4. Mevcut connected accounts'u kontrol et"""
        print("🎯 TEST 4: Connected Accounts Check")
        print("-" * 50)
        
        if not self.token:
            self.log_test("Connected Accounts Check", False, "No auth token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.base_url}/connected-accounts", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                accounts = data.get('accounts', [])
                
                details = []
                details.append(f"Found {len(accounts)} connected accounts")
                
                if accounts:
                    for i, account in enumerate(accounts, 1):
                        details.append(f"Account {i}:")
                        details.append(f"  Email: {account.get('email', 'Unknown')}")
                        details.append(f"  Name: {account.get('name', 'Unknown')}")
                        details.append(f"  Type: {account.get('type', 'Unknown')}")
                        details.append(f"  Connected: {account.get('connected_at', 'Unknown')}")
                else:
                    details.append("No connected accounts found (normal for new users)")
                
                self.log_test("Connected Accounts Check", True, "\n   ".join(details))
                return True
            else:
                self.log_test("Connected Accounts Check", False, 
                            f"HTTP {response.status_code}", response.json())
                return False
                
        except Exception as e:
            self.log_test("Connected Accounts Check", False, f"Exception: {str(e)}")
            return False

    def test_backend_logs(self):
        """5. Backend loglarında artık MSAL veya Graph SDK warning'i olmamalı"""
        print("🎯 TEST 5: Backend Logs Check")
        print("-" * 50)
        
        try:
            # Check supervisor backend logs - only check the most recent 15 lines after restart
            log_files = [
                "/var/log/supervisor/backend.out.log",
                "/var/log/supervisor/backend.err.log"
            ]
            
            warnings_found = []
            recent_logs = []
            
            for log_file in log_files:
                try:
                    result = subprocess.run(
                        ["tail", "-n", "15", log_file], 
                        capture_output=True, 
                        text=True, 
                        timeout=10
                    )
                    
                    if result.returncode == 0:
                        log_content = result.stdout
                        
                        # Only check logs after the most recent "Application startup complete"
                        lines = log_content.strip().split('\n')
                        
                        # Find the last startup complete line
                        startup_index = -1
                        for i in range(len(lines) - 1, -1, -1):
                            if "Application startup complete" in lines[i]:
                                startup_index = i
                                break
                        
                        # Only check lines after the startup (current session)
                        if startup_index >= 0:
                            current_session_lines = lines[startup_index:]
                        else:
                            current_session_lines = lines[-5:]  # fallback to last 5 lines
                        
                        current_session_content = '\n'.join(current_session_lines)
                        
                        # Check for specific warnings in current session only
                        warning_patterns = [
                            "Microsoft Graph SDK not available",
                            "No module named azure.core",
                            "No module named 'azure.core'",
                            "No module named 'msal'",
                            "MSAL",
                            "Graph SDK not available"
                        ]
                        
                        for pattern in warning_patterns:
                            if pattern in current_session_content:
                                warnings_found.append(f"{pattern} found in current session of {log_file}")
                        
                        # Collect recent log entries for display
                        if current_session_lines:
                            recent_logs.extend([f"From {log_file} (current session):"] + current_session_lines[-5:])
                            
                except subprocess.TimeoutExpired:
                    recent_logs.append(f"Timeout reading {log_file}")
                except Exception as e:
                    recent_logs.append(f"Error reading {log_file}: {str(e)}")
            
            details = []
            if warnings_found:
                details.append("❌ Warnings found in current session:")
                details.extend([f"  - {warning}" for warning in warnings_found])
            else:
                details.append("✅ No MSAL or Graph SDK warnings found in current session logs")
            
            if recent_logs:
                details.append("\nCurrent session log entries:")
                details.extend([f"  {log}" for log in recent_logs[-10:]])
            
            success = len(warnings_found) == 0
            self.log_test("Backend Logs - No MSAL/Graph SDK Warnings", success, "\n   ".join(details))
            return success
                
        except Exception as e:
            self.log_test("Backend Logs - No MSAL/Graph SDK Warnings", False, f"Exception: {str(e)}")
            return False

def main():
    print("🚀 FOCUSED OUTLOOK OAUTH INTEGRATION TEST")
    print("=" * 60)
    print("Kullanıcı şikayeti: 'OAuth akışı başlıyor ama sonra hata veriyor'")
    print("Bu test backend'in hazır olduğundan emin olmak için yapılıyor.")
    print("=" * 60)
    print()
    
    tester = FocusedOutlookTester()
    
    # Run all tests in sequence
    test_functions = [
        tester.test_demo_login,
        tester.test_outlook_status,
        tester.test_outlook_auth_url,
        tester.test_connected_accounts,
        tester.test_backend_logs
    ]
    
    for test_func in test_functions:
        test_func()
    
    # Final Results
    print("=" * 60)
    print("📊 FINAL RESULTS")
    print("=" * 60)
    
    success_rate = (tester.tests_passed / tester.tests_total) * 100 if tester.tests_total > 0 else 0
    
    print(f"Tests Passed: {tester.tests_passed}/{tester.tests_total} ({success_rate:.1f}%)")
    print()
    
    if tester.tests_passed == tester.tests_total:
        print("🎉 TÜM TESTLER BAŞARILI!")
        print("✅ Demo kullanıcısı login çalışıyor")
        print("✅ Outlook status endpoint: graph_sdk_available = true")
        print("✅ OAuth URL generation çalışıyor")
        print("✅ Connected accounts endpoint erişilebilir")
        print("✅ Backend loglarında MSAL/Graph SDK warning'i yok")
        print()
        print("💡 SONUÇ: Backend tamamen hazır! Kullanıcı Outlook hesabını bağlamayı deneyebilir.")
        return 0
    else:
        print("❌ BAZI TESTLER BAŞARISIZ!")
        failed_count = tester.tests_total - tester.tests_passed
        print(f"❌ {failed_count} test başarısız oldu")
        print()
        print("🔧 Backend'de hala düzeltilmesi gereken sorunlar var.")
        print("   Yukarıdaki detayları kontrol edin ve gerekli düzeltmeleri yapın.")
        return 1

if __name__ == "__main__":
    sys.exit(main())