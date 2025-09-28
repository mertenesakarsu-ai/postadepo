#!/usr/bin/env python3
"""
PostaDepo Homepage Routing and Features Test
Test edilecek özellikler:
1. Ana sayfa (/) erişimi - Ana sayfa bileşeni yükleniyor mu?
2. Login sayfası (/login) erişimi - Giriş sayfası çalışıyor mu?
3. Mevcut API endpoint'leri hala çalışıyor mu?
4. Demo giriş fonksiyonları çalışıyor mu?
"""

import requests
import sys
import json
from datetime import datetime

class PostaDepoHomepageRoutingTester:
    def __init__(self):
        # Frontend URL from .env file
        self.frontend_url = "https://userdepo-panel.preview.emergentagent.com"
        # Backend API URL from .env file  
        self.backend_url = "https://userdepo-panel.preview.emergentagent.com/api"
        self.token = None
        self.user = None
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, test_func):
        """Run a single test with error handling"""
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            success = test_func()
            if success:
                self.tests_passed += 1
                print(f"✅ {name}: PASSED")
            else:
                print(f"❌ {name}: FAILED")
            return success
        except Exception as e:
            print(f"💥 {name}: CRASHED - {str(e)}")
            return False

    def test_homepage_access(self):
        """Test 1: Ana sayfa (/) erişimi - Ana sayfa bileşeni yükleniyor mu?"""
        try:
            print(f"   Testing homepage access: {self.frontend_url}/")
            response = requests.get(f"{self.frontend_url}/", timeout=10)
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                content = response.text
                
                # Check for React app indicators
                react_indicators = [
                    'id="root"',
                    'react',
                    'PostaDepo',
                    'div',
                    'script'
                ]
                
                found_indicators = []
                for indicator in react_indicators:
                    if indicator.lower() in content.lower():
                        found_indicators.append(indicator)
                
                print(f"   Found React indicators: {found_indicators}")
                print(f"   Content length: {len(content)} characters")
                
                # Check if it's a proper HTML page
                if '<html' in content.lower() and '</html>' in content.lower():
                    print("   ✅ Valid HTML page structure found")
                    return True
                else:
                    print("   ❌ Invalid HTML structure")
                    return False
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            print("   ❌ Request timeout")
            return False
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return False

    def test_login_page_access(self):
        """Test 2: Login sayfası (/login) erişimi - Giriş sayfası çalışıyor mu?"""
        try:
            print(f"   Testing login page access: {self.frontend_url}/login")
            response = requests.get(f"{self.frontend_url}/login", timeout=10)
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                content = response.text
                
                # Check for login page indicators
                login_indicators = [
                    'login',
                    'email',
                    'password',
                    'giriş',
                    'form',
                    'input'
                ]
                
                found_indicators = []
                for indicator in login_indicators:
                    if indicator.lower() in content.lower():
                        found_indicators.append(indicator)
                
                print(f"   Found login indicators: {found_indicators}")
                print(f"   Content length: {len(content)} characters")
                
                # Check if it's a proper HTML page
                if '<html' in content.lower() and '</html>' in content.lower():
                    print("   ✅ Valid HTML login page structure found")
                    return True
                else:
                    print("   ❌ Invalid HTML structure")
                    return False
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            print("   ❌ Request timeout")
            return False
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return False

    def test_demo_login_function(self):
        """Test 4: Demo giriş fonksiyonları çalışıyor mu?"""
        try:
            print(f"   Testing demo login: {self.backend_url}/auth/login")
            
            login_data = {
                "email": "demo@postadepo.com",
                "password": "demo123"
            }
            
            headers = {'Content-Type': 'application/json'}
            response = requests.post(
                f"{self.backend_url}/auth/login", 
                json=login_data, 
                headers=headers,
                timeout=10
            )
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    print(f"   Response keys: {list(response_data.keys())}")
                    
                    if 'token' in response_data and 'user' in response_data:
                        self.token = response_data['token']
                        self.user = response_data['user']
                        
                        user_email = self.user.get('email', 'Unknown')
                        user_name = self.user.get('name', 'Unknown')
                        
                        print(f"   ✅ Demo login successful!")
                        print(f"   User: {user_name} ({user_email})")
                        print(f"   Token length: {len(self.token)} characters")
                        return True
                    else:
                        print("   ❌ Missing token or user in response")
                        return False
                        
                except json.JSONDecodeError:
                    print("   ❌ Invalid JSON response")
                    return False
            else:
                print(f"   ❌ Login failed with status {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error text: {response.text[:200]}")
                return False
                
        except requests.exceptions.Timeout:
            print("   ❌ Request timeout")
            return False
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return False

    def test_emails_api_endpoint(self):
        """Test 3: GET /api/emails (E-postalar çekiliyor mu?)"""
        if not self.token:
            print("   ❌ No authentication token available")
            return False
            
        try:
            print(f"   Testing emails API: {self.backend_url}/emails")
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.token}'
            }
            
            response = requests.get(
                f"{self.backend_url}/emails", 
                headers=headers,
                timeout=10
            )
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    print(f"   Response keys: {list(response_data.keys())}")
                    
                    emails = response_data.get('emails', [])
                    folder_counts = response_data.get('folderCounts', {})
                    
                    print(f"   ✅ Emails API working!")
                    print(f"   Total emails: {len(emails)}")
                    print(f"   Folder counts: {folder_counts}")
                    
                    # Check email structure
                    if emails:
                        first_email = emails[0]
                        email_keys = list(first_email.keys())
                        print(f"   Email fields: {email_keys}")
                        
                        # Check for important fields
                        required_fields = ['id', 'subject', 'sender', 'content', 'date']
                        missing_fields = [field for field in required_fields if field not in email_keys]
                        
                        if missing_fields:
                            print(f"   ⚠️  Missing fields: {missing_fields}")
                        else:
                            print(f"   ✅ All required email fields present")
                    
                    return True
                    
                except json.JSONDecodeError:
                    print("   ❌ Invalid JSON response")
                    return False
            else:
                print(f"   ❌ API failed with status {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error text: {response.text[:200]}")
                return False
                
        except requests.exceptions.Timeout:
            print("   ❌ Request timeout")
            return False
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return False

    def test_additional_api_endpoints(self):
        """Test additional API endpoints to ensure they're still working"""
        if not self.token:
            print("   ❌ No authentication token available")
            return False
            
        endpoints_to_test = [
            ("Storage Info", "storage-info", "GET"),
            ("Connected Accounts", "connected-accounts", "GET"),
        ]
        
        all_success = True
        
        for endpoint_name, endpoint_path, method in endpoints_to_test:
            try:
                print(f"   Testing {endpoint_name}: {self.backend_url}/{endpoint_path}")
                
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.token}'
                }
                
                if method == "GET":
                    response = requests.get(
                        f"{self.backend_url}/{endpoint_path}", 
                        headers=headers,
                        timeout=10
                    )
                
                print(f"     Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        response_data = response.json()
                        print(f"     ✅ {endpoint_name} working - Keys: {list(response_data.keys())}")
                    except json.JSONDecodeError:
                        print(f"     ⚠️  {endpoint_name} returned non-JSON response")
                        all_success = False
                else:
                    print(f"     ❌ {endpoint_name} failed with status {response.status_code}")
                    all_success = False
                    
            except Exception as e:
                print(f"     ❌ {endpoint_name} error: {str(e)}")
                all_success = False
        
        return all_success

    def test_invalid_login(self):
        """Test invalid login to ensure security is working"""
        try:
            print(f"   Testing invalid login: {self.backend_url}/auth/login")
            
            login_data = {
                "email": "invalid@test.com",
                "password": "wrongpassword"
            }
            
            headers = {'Content-Type': 'application/json'}
            response = requests.post(
                f"{self.backend_url}/auth/login", 
                json=login_data, 
                headers=headers,
                timeout=10
            )
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 401:
                print("   ✅ Invalid login correctly rejected")
                return True
            else:
                print(f"   ❌ Expected 401, got {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return False

def main():
    print("🚀 PostaDepo Homepage Routing and Features Test")
    print("=" * 60)
    print("Test edilecek özellikler:")
    print("1. Ana sayfa (/) erişimi - Ana sayfa bileşeni yükleniyor mu?")
    print("2. Login sayfası (/login) erişimi - Giriş sayfası çalışıyor mu?")
    print("3. Mevcut API endpoint'leri hala çalışıyor mu?")
    print("4. Demo giriş fonksiyonları çalışıyor mu?")
    print("=" * 60)
    
    tester = PostaDepoHomepageRoutingTester()
    
    # Test sequence based on Turkish requirements
    tests = [
        ("1. Ana Sayfa (/) Erişimi", tester.test_homepage_access),
        ("2. Login Sayfası (/login) Erişimi", tester.test_login_page_access),
        ("4. Demo Giriş Fonksiyonu", tester.test_demo_login_function),
        ("3a. E-postalar API Endpoint'i", tester.test_emails_api_endpoint),
        ("3b. Diğer API Endpoint'leri", tester.test_additional_api_endpoints),
        ("Bonus: Geçersiz Giriş Testi", tester.test_invalid_login),
    ]
    
    # Run all tests
    for test_name, test_func in tests:
        tester.run_test(test_name, test_func)
    
    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 Test Sonuçları: {tester.tests_passed}/{tester.tests_run} test başarılı")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 Tüm testler başarılı!")
        success_rate = 100
    else:
        failed_tests = tester.tests_run - tester.tests_passed
        success_rate = (tester.tests_passed / tester.tests_run) * 100
        print(f"⚠️  {failed_tests} test başarısız")
    
    print(f"📈 Başarı Oranı: {success_rate:.1f}%")
    
    # Detailed summary
    print("\n📋 ÖZET:")
    if tester.tests_passed >= 4:  # At least 4 core tests should pass
        print("✅ Ana sayfa routing ve temel özellikler çalışıyor")
    else:
        print("❌ Ana sayfa routing veya temel özelliklerde sorunlar var")
    
    return 0 if success_rate >= 80 else 1

if __name__ == "__main__":
    sys.exit(main())