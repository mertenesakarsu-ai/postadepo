#!/usr/bin/env python3
"""
Outlook Integration Issue Test - Based on user review request
Testing the specific issue: "Outlook bağlandı" diyor ama sonra hata veriyor

Test sequence as requested:
1. Demo kullanıcısı (demo@postadepo.com / demo123) ile giriş yap
2. GET /api/outlook/status endpoint'ini kontrol et - Azure credentials configured mi?
3. GET /api/outlook/auth-url endpoint'ini test et - auth URL generation çalışıyor mu?
4. GET /api/outlook/accounts endpoint'ini kontrol et - kaç connected account var?
5. Database'de connected_accounts collection'ını kontrol et - hiç kayıt var mı?
6. oauth_states collection'ını kontrol et - OAuth state'ler oluşuyor mu?
"""

import requests
import sys
import json
from datetime import datetime

class OutlookIssueTester:
    def __init__(self, base_url="https://msgraph-oauth-fix.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.user = None
        self.tests_run = 0
        self.tests_passed = 0
        self.critical_issues = []
        self.findings = []

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
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:300]}...")

            try:
                response_data = response.json()
                return success, response_data, response
            except:
                return success, {}, response

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}, None

    def test_demo_user_login(self):
        """1. Demo kullanıcısı (demo@postadepo.com / demo123) ile giriş yap"""
        print("\n" + "="*70)
        print("🎯 STEP 1: Demo kullanıcısı girişi (demo@postadepo.com / demo123)")
        print("="*70)
        
        success, response, _ = self.run_test(
            "Demo User Login",
            "POST",
            "auth/login",
            200,
            data={"email": "demo@postadepo.com", "password": "demo123"}
        )
        
        if success and 'token' in response and 'user' in response:
            self.token = response['token']
            self.user = response['user']
            print(f"   ✅ Demo kullanıcısı başarıyla giriş yaptı: {self.user.get('email')}")
            print(f"   🔑 JWT token alındı: {self.token[:30]}...")
            print(f"   👤 User ID: {self.user.get('id')}")
            print(f"   📧 User Type: {self.user.get('user_type', 'email')}")
            self.findings.append("✅ Demo user login successful")
            return True
        else:
            print("   ❌ Demo kullanıcısı girişi başarısız!")
            self.critical_issues.append("Demo user login failed - cannot proceed with Outlook tests")
            self.findings.append("❌ Demo user login failed")
            return False

    def test_outlook_status(self):
        """2. GET /api/outlook/status endpoint'ini kontrol et - Azure credentials configured mi?"""
        print("\n" + "="*70)
        print("🎯 STEP 2: Outlook Status - Azure credentials configured mi?")
        print("="*70)
        
        if not self.token:
            print("   ❌ No authentication token available")
            return False
        
        success, response, _ = self.run_test(
            "Outlook Status Check",
            "GET",
            "outlook/status",
            200
        )
        
        if success:
            print("   📊 Outlook Status Response:")
            for key, value in response.items():
                print(f"      {key}: {value}")
            
            # Check critical configuration
            graph_available = response.get('graph_sdk_available', False)
            credentials_configured = response.get('credentials_configured', False)
            client_id_set = response.get('client_id_set', False)
            tenant_id_set = response.get('tenant_id_set', False)
            message = response.get('message', '')
            
            print(f"\n   🔍 Critical Configuration Check:")
            print(f"      Microsoft Graph SDK Available: {graph_available}")
            print(f"      Azure Credentials Configured: {credentials_configured}")
            print(f"      Client ID Set: {client_id_set}")
            print(f"      Tenant ID Set: {tenant_id_set}")
            print(f"      Status Message: {message}")
            
            if graph_available and credentials_configured and client_id_set and tenant_id_set:
                print("   ✅ Tüm Azure credentials configured!")
                self.findings.append("✅ Azure credentials fully configured")
                return True
            else:
                issues = []
                if not graph_available:
                    issues.append("Microsoft Graph SDK not available")
                    self.critical_issues.append("Microsoft Graph SDK not available - OAuth token processing will fail")
                if not credentials_configured:
                    issues.append("Azure credentials not configured")
                if not client_id_set:
                    issues.append("Client ID not set")
                if not tenant_id_set:
                    issues.append("Tenant ID not set")
                
                print(f"   ❌ Configuration issues: {', '.join(issues)}")
                self.findings.append(f"❌ Configuration issues: {', '.join(issues)}")
                return False
        else:
            self.critical_issues.append("Outlook status endpoint not accessible")
            self.findings.append("❌ Outlook status endpoint failed")
            return False

    def test_outlook_auth_url(self):
        """3. GET /api/outlook/auth-url endpoint'ini test et - auth URL generation çalışıyor mu?"""
        print("\n" + "="*70)
        print("🎯 STEP 3: Auth URL Generation - çalışıyor mu?")
        print("="*70)
        
        if not self.token:
            print("   ❌ No authentication token available")
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
            
            print(f"   📋 Auth URL Details:")
            print(f"      URL Length: {len(auth_url)} characters")
            print(f"      State Parameter: {state}")
            print(f"      URL Preview: {auth_url[:100]}...")
            
            if auth_url and len(auth_url) > 100:
                print(f"   ✅ OAuth URL generation çalışıyor!")
                
                # Check OAuth parameters
                required_params = ['client_id', 'response_type', 'redirect_uri', 'scope', 'state']
                missing_params = []
                
                for param in required_params:
                    if param not in auth_url:
                        missing_params.append(param)
                
                if missing_params:
                    print(f"   ⚠️  Missing OAuth parameters: {missing_params}")
                    self.findings.append(f"⚠️ OAuth URL missing parameters: {missing_params}")
                else:
                    print("   ✅ Tüm gerekli OAuth parametreleri mevcut")
                
                # Check Microsoft endpoint
                if 'login.microsoftonline.com' in auth_url:
                    print("   ✅ Microsoft OAuth endpoint doğru")
                    self.findings.append("✅ OAuth URL generation working with Microsoft endpoint")
                    return True
                else:
                    print("   ❌ Microsoft OAuth endpoint değil!")
                    self.findings.append("❌ OAuth URL not pointing to Microsoft endpoint")
                    return False
            else:
                print("   ❌ OAuth URL generation başarısız!")
                self.findings.append("❌ OAuth URL generation failed")
                return False
        else:
            self.critical_issues.append("Auth URL generation failed")
            self.findings.append("❌ Auth URL generation endpoint failed")
            return False

    def test_outlook_accounts(self):
        """4. GET /api/outlook/accounts endpoint'ini kontrol et - kaç connected account var?"""
        print("\n" + "="*70)
        print("🎯 STEP 4: Connected Accounts - kaç connected account var?")
        print("="*70)
        
        if not self.token:
            print("   ❌ No authentication token available")
            return False
        
        success, response, _ = self.run_test(
            "Get Connected Outlook Accounts",
            "GET",
            "outlook/accounts",
            200
        )
        
        if success:
            accounts = response.get('accounts', [])
            print(f"   📊 Connected Accounts Count: {len(accounts)}")
            
            if len(accounts) == 0:
                print("   ⚠️  Hiç connected Outlook account yok!")
                print("   💡 Bu kullanıcının sorununu açıklıyor:")
                print("      - OAuth akışı başlıyor (kullanıcı 'bağlandı' mesajı görüyor)")
                print("      - Ama account storage başarısız oluyor")
                print("      - Bu yüzden hiç connected account kaydedilmiyor")
                print("      - Sonraki işlemler 'Account not found' hatası veriyor")
                self.critical_issues.append("No connected accounts found - OAuth flow starts but account storage fails")
                self.findings.append("❌ No connected accounts - explains user's issue")
                return True  # This is expected based on the user's issue
            else:
                print("   📋 Connected Accounts:")
                for i, account in enumerate(accounts):
                    print(f"      {i+1}. {account.get('email', 'No email')} ({account.get('type', 'Unknown type')})")
                    print(f"         ID: {account.get('id', 'No ID')}")
                    print(f"         Connected: {account.get('connected_at', 'Unknown time')}")
                self.findings.append(f"✅ Found {len(accounts)} connected accounts")
                return True
        else:
            self.critical_issues.append("Outlook accounts endpoint not accessible")
            self.findings.append("❌ Outlook accounts endpoint failed")
            return False

    def test_database_connected_accounts(self):
        """5. Database'de connected_accounts collection'ını kontrol et - hiç kayıt var mı?"""
        print("\n" + "="*70)
        print("🎯 STEP 5: Database Connected Accounts - hiç kayıt var mı?")
        print("="*70)
        
        if not self.token:
            print("   ❌ No authentication token available")
            return False
        
        # Use the general connected-accounts endpoint to check database
        success, response, _ = self.run_test(
            "Database Connected Accounts Check",
            "GET",
            "connected-accounts",
            200
        )
        
        if success:
            accounts = response.get('accounts', [])
            print(f"   📊 Database Connected Accounts Count: {len(accounts)}")
            
            if len(accounts) == 0:
                print("   ❌ Database'de hiç connected_accounts kaydı yok!")
                print("   💡 Bu kullanıcının sorununu doğruluyor:")
                print("      - OAuth akışı başlıyor")
                print("      - Ama account bilgileri database'e kaydedilmiyor")
                print("      - Token exchange veya account storage aşamasında hata var")
                print("      - Bu yüzden sonraki işlemler başarısız oluyor")
                self.critical_issues.append("Database connected_accounts collection is empty - OAuth flow starts but account storage fails")
                self.findings.append("❌ Database empty - confirms OAuth storage failure")
                return True  # This is expected based on the issue
            else:
                print("   ✅ Database'de connected accounts mevcut:")
                for account in accounts:
                    print(f"      - {account.get('email', 'No email')} (Type: {account.get('type', 'Unknown')})")
                    print(f"        ID: {account.get('id', 'No ID')}")
                    print(f"        Connected: {account.get('connected_at', 'Unknown time')}")
                self.findings.append(f"✅ Database has {len(accounts)} connected accounts")
                return True
        else:
            self.critical_issues.append("Connected accounts database check failed")
            self.findings.append("❌ Database connected accounts check failed")
            return False

    def test_oauth_states(self):
        """6. oauth_states collection'ını kontrol et - OAuth state'ler oluşuyor mu?"""
        print("\n" + "="*70)
        print("🎯 STEP 6: OAuth States - OAuth state'ler oluşuyor mu?")
        print("="*70)
        
        if not self.token:
            print("   ❌ No authentication token available")
            return False
        
        # Generate multiple auth URLs to create states
        print("   📝 OAuth state'ler oluşturmak için auth URL'ler generate ediliyor...")
        
        states_created = []
        for i in range(3):
            success, response, _ = self.run_test(
                f"Generate Auth URL #{i+1} for State Test",
                "GET",
                "outlook/auth-url",
                200
            )
            
            if success:
                state = response.get('state', '')
                if state:
                    states_created.append(state)
                    print(f"      State #{i+1}: {state}")
        
        print(f"   📊 OAuth States Created: {len(states_created)}")
        
        if len(states_created) > 0:
            print("   ✅ OAuth state'ler başarıyla oluşturuluyor!")
            print("   💡 Bu gösteriyor ki:")
            print("      - OAuth akışının ilk aşaması çalışıyor")
            print("      - State parameter'lar generate ediliyor")
            print("      - Kullanıcı auth URL'e yönlendiriliyor")
            print("      - Bu yüzden kullanıcı 'bağlandı' mesajı görüyor")
            print("      - Sorun muhtemelen callback/token exchange aşamasında")
            self.findings.append("✅ OAuth states generating successfully")
            
            # Check if states are unique
            unique_states = set(states_created)
            if len(unique_states) == len(states_created):
                print("   ✅ Tüm state'ler unique (güvenlik OK)")
                self.findings.append("✅ OAuth states are unique")
            else:
                print("   ⚠️  Duplicate state'ler var (güvenlik riski)")
                self.findings.append("⚠️ Duplicate OAuth states detected")
            
            return True
        else:
            print("   ❌ OAuth state oluşturulamıyor!")
            self.critical_issues.append("OAuth state generation failed")
            self.findings.append("❌ OAuth state generation failed")
            return False

    def test_backend_logs_analysis(self):
        """Backend loglarını kontrol et (simulated through API calls)"""
        print("\n" + "="*70)
        print("🎯 STEP 7: Backend Logs Analysis (API-based)")
        print("="*70)
        
        if not self.token:
            print("   ❌ No authentication token available")
            return False
        
        print("   📋 Backend log analizi için test endpoint'leri çağrılıyor...")
        
        # Test OAuth callback with invalid data to see backend behavior
        print("   🔄 OAuth callback simulation (invalid data)...")
        
        callback_success, callback_response, callback_http = self.run_test(
            "OAuth Callback Simulation",
            "GET",
            "outlook/callback?code=invalid_test_code&state=invalid_test_state",
            400  # Expected to fail with invalid code
        )
        
        if callback_http:
            print(f"   📊 Callback Response Status: {callback_http.status_code}")
            print(f"   📝 Callback Response: {callback_http.text[:200]}...")
            
            if callback_http.status_code == 400:
                print("   ✅ OAuth callback endpoint erişilebilir ve invalid code'ları handle ediyor")
                self.findings.append("✅ OAuth callback endpoint accessible and handles errors")
            elif callback_http.status_code == 503:
                print("   ⚠️  OAuth callback endpoint service unavailable")
                self.findings.append("⚠️ OAuth callback service unavailable")
            else:
                print(f"   ⚠️  Unexpected callback response: {callback_http.status_code}")
                self.findings.append(f"⚠️ Unexpected callback response: {callback_http.status_code}")
        
        # Test email sync to see what error occurs
        print("   📧 Email sync test (should fail without connected accounts)...")
        
        sync_success, sync_response, sync_http = self.run_test(
            "Email Sync Without Connected Accounts",
            "POST",
            "outlook/sync",
            404  # Should fail with "Account not found"
        )
        
        if sync_http:
            print(f"   📊 Sync Response Status: {sync_http.status_code}")
            print(f"   📝 Sync Response: {sync_http.text[:200]}...")
            
            if sync_http.status_code == 404:
                print("   ✅ Email sync doğru şekilde 404 Account not found hatası veriyor")
                print("   💡 Bu kullanıcının gördüğü hatayı açıklıyor!")
                self.findings.append("✅ Email sync correctly returns 404 Account not found")
            else:
                print(f"   ⚠️  Unexpected sync response: {sync_http.status_code}")
                self.findings.append(f"⚠️ Unexpected sync response: {sync_http.status_code}")
        
        return True

    def run_comprehensive_test(self):
        """Run all tests in the requested sequence"""
        print("🚀 OUTLOOK ENTEGRASYON SORUNU KAPSAMLI TEST")
        print("=" * 80)
        print("Kullanıcı sorunu: 'Outlook bağlandı' diyor ama sonra hata veriyor")
        print("=" * 80)
        
        # Test sequence as requested in the review
        tests = [
            ("Demo kullanıcısı girişi", self.test_demo_user_login),
            ("Outlook Status - Azure credentials", self.test_outlook_status),
            ("Auth URL Generation", self.test_outlook_auth_url),
            ("Connected Accounts Check", self.test_outlook_accounts),
            ("Database Connected Accounts", self.test_database_connected_accounts),
            ("OAuth States Generation", self.test_oauth_states),
            ("Backend Logs Analysis", self.test_backend_logs_analysis),
        ]
        
        for test_name, test_func in tests:
            try:
                test_func()
            except Exception as e:
                print(f"💥 {test_name} crashed: {str(e)}")
                self.critical_issues.append(f"{test_name}: Exception - {str(e)}")
        
        # Print comprehensive diagnosis
        self.print_diagnosis()

    def print_diagnosis(self):
        """Print comprehensive diagnosis of the Outlook integration issue"""
        print("\n" + "=" * 80)
        print("🔍 OUTLOOK ENTEGRASYON SORUNU TANI RAPORU")
        print("=" * 80)
        
        print(f"📊 Test Sonuçları: {self.tests_passed}/{self.tests_run} başarılı")
        print(f"📈 Başarı Oranı: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        print(f"\n📋 TEST BULGULARI:")
        for finding in self.findings:
            print(f"   {finding}")
        
        if self.critical_issues:
            print(f"\n🚨 KRİTİK SORUNLAR ({len(self.critical_issues)}):")
            for i, issue in enumerate(self.critical_issues, 1):
                print(f"   {i}. {issue}")
        
        print(f"\n💡 KULLANICI SORUNUNUN KÖK NEDENİ ANALİZİ:")
        print("=" * 60)
        
        # Analyze the root cause based on test results
        if any("Microsoft Graph SDK not available" in issue for issue in self.critical_issues):
            print("🚨 KRİTİK SORUN TESPİT EDİLDİ:")
            print("   ROOT CAUSE: Microsoft Graph SDK mevcut değil")
            print("   IMPACT:")
            print("   - OAuth akışı başlıyor (kullanıcı 'Outlook bağlandı' mesajı görüyor)")
            print("   - Ama Microsoft Graph SDK olmadığı için token processing başarısız oluyor")
            print("   - Account bilgileri database'e kaydedilmiyor")
            print("   - Sonraki işlemler 404 Account not found hatası veriyor")
            print("   - Kullanıcı hata mesajı görüyor")
            
            print(f"\n🔧 ÖNERİLEN ÇÖZÜM:")
            print("   1. Microsoft Graph SDK bağımlılıklarını yükle:")
            print("      pip install azure-core azure-identity msgraph-core")
            print("   2. Backend'i restart et")
            print("   3. Outlook OAuth entegrasyonunu tekrar test et")
            
        elif any("No connected accounts" in issue for issue in self.critical_issues):
            print("⚠️  SORUN TESPİT EDİLDİ:")
            print("   ROOT CAUSE: OAuth akışı başlıyor ama account storage başarısız")
            print("   IMPACT:")
            print("   - Kullanıcı OAuth URL'e yönlendiriliyor ('bağlandı' mesajı)")
            print("   - Token exchange veya account kaydetme aşamasında hata oluyor")
            print("   - Database'de hiç connected account kaydedilmiyor")
            print("   - Email sync ve diğer işlemler başarısız oluyor")
            
            print(f"\n🔧 ÖNERİLEN ÇÖZÜM:")
            print("   1. Backend loglarını kontrol et (OAuth callback errors)")
            print("   2. Microsoft Graph API çağrılarını debug et")
            print("   3. Database connection ve write permissions kontrol et")
            print("   4. Azure app registration settings kontrol et")
        
        else:
            print("✅ TEMEL OUTLOOK API ENDPOINT'LERİ ÇALIŞIYOR")
            print("   - Azure credentials configured")
            print("   - Auth URL generation çalışıyor")
            print("   - OAuth akışı başlayabiliyor")
            print("   - Sorun muhtemelen token exchange aşamasında")
            
            print(f"\n🔧 ÖNERİLEN ÇÖZÜM:")
            print("   1. OAuth callback endpoint'ini detaylı debug et")
            print("   2. Microsoft Graph API token exchange'i kontrol et")
            print("   3. Account storage logic'ini kontrol et")

        print(f"\n🎯 SONUÇ:")
        if len(self.critical_issues) == 0:
            print("✅ Outlook entegrasyonu temel olarak çalışıyor")
            print("   Kullanıcı sorunu muhtemelen geçici bir durum")
        else:
            print("❌ Outlook entegrasyonunda kritik sorunlar var")
            print("   Kullanıcının şikayeti haklı - sistem düzeltilmeli")

def main():
    print("🎯 OUTLOOK ENTEGRASYON SORUNU TEST BAŞLATIYOR")
    print("Kullanıcı şikayeti: 'Outlook bağlandı' diyor ama sonra hata veriyor")
    print("=" * 80)
    
    tester = OutlookIssueTester()
    tester.run_comprehensive_test()
    
    print(f"\n🏁 TEST TAMAMLANDI")
    return 0

if __name__ == "__main__":
    sys.exit(main())