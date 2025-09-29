#!/usr/bin/env python3
"""
Outlook OAuth Redirect URI Tutarlılık Testi
Bu test, Outlook OAuth redirect URI'larının tutarlı olduğunu doğrular.

Test Edilen Alanlar:
1. GET /api/outlook/auth-url endpoint'inin döndürdüğü redirect_uri değeri
2. OAuth URL generation'da kullanılan redirect URI ile return edilen redirect URI'nin aynı olması
3. Token exchange fonksiyonunda kullanılan redirect URI tutarlılığı
4. Environment variable REDIRECT_URI kullanımı
5. Kod tutarlılığı

Önceki Sorun: Line 2376'da yanlış default değer kullanılıyordu
Fix: Tüm yerler aynı default değeri kullanıyor
"""

import requests
import sys
import json
import os
import re
from datetime import datetime
from urllib.parse import urlparse, parse_qs

class OutlookRedirectURITester:
    def __init__(self, base_url="https://data-dashboard-bug.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.user = None
        self.tests_run = 0
        self.tests_passed = 0
        self.expected_redirect_uri = "https://data-dashboard-bug.preview.emergentagent.com/auth/callback"
        
    def log_test(self, name, success, details=""):
        """Test sonucunu logla"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
            if details:
                print(f"   {details}")
        else:
            print(f"❌ {name}")
            if details:
                print(f"   {details}")
    
    def login_test_user(self):
        """Test kullanıcısı ile giriş yap"""
        print("🔐 Test kullanıcısı ile giriş yapılıyor...")
        
        login_data = {
            "email": "tyrzmusak@gmail.com",
            "password": "deneme123"
        }
        
        try:
            response = requests.post(f"{self.base_url}/auth/login", json=login_data)
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("token")
                self.user = data.get("user")
                print(f"✅ Giriş başarılı - User ID: {self.user.get('id', 'N/A')}")
                return True
            else:
                print(f"❌ Giriş başarısız - Status: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Giriş hatası: {str(e)}")
            return False
    
    def test_outlook_auth_url_endpoint(self):
        """GET /api/outlook/auth-url endpoint'ini test et"""
        print("\n🔍 Outlook Auth URL Endpoint Testi...")
        
        if not self.token:
            self.log_test("Auth URL Endpoint", False, "Token bulunamadı, önce giriş yapın")
            return False
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        try:
            response = requests.get(f"{self.base_url}/outlook/auth-url", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Response'da redirect_uri field'ı var mı?
                if "redirect_uri" not in data:
                    self.log_test("Auth URL Response - redirect_uri field", False, "Response'da redirect_uri field'ı yok")
                    return False
                
                returned_redirect_uri = data["redirect_uri"]
                
                # Dönen redirect URI beklenen değer mi?
                if returned_redirect_uri == self.expected_redirect_uri:
                    self.log_test("Auth URL Response - redirect_uri değeri", True, f"Doğru: {returned_redirect_uri}")
                else:
                    self.log_test("Auth URL Response - redirect_uri değeri", False, 
                                f"Beklenen: {self.expected_redirect_uri}, Dönen: {returned_redirect_uri}")
                    return False
                
                # Auth URL'de redirect_uri parametresi var mı?
                if "auth_url" not in data:
                    self.log_test("Auth URL Response - auth_url field", False, "Response'da auth_url field'ı yok")
                    return False
                
                auth_url = data["auth_url"]
                
                # Auth URL'den redirect_uri parametresini çıkar
                parsed_url = urlparse(auth_url)
                query_params = parse_qs(parsed_url.query)
                
                if "redirect_uri" not in query_params:
                    self.log_test("Auth URL - redirect_uri parametresi", False, "Auth URL'de redirect_uri parametresi yok")
                    return False
                
                auth_url_redirect_uri = query_params["redirect_uri"][0]
                
                # Auth URL'deki redirect_uri ile response'daki redirect_uri aynı mı?
                if auth_url_redirect_uri == returned_redirect_uri:
                    self.log_test("Auth URL vs Response redirect_uri tutarlılığı", True, 
                                f"İkisi de aynı: {auth_url_redirect_uri}")
                else:
                    self.log_test("Auth URL vs Response redirect_uri tutarlılığı", False,
                                f"Auth URL: {auth_url_redirect_uri}, Response: {returned_redirect_uri}")
                    return False
                
                # Auth URL'deki redirect_uri beklenen değer mi?
                if auth_url_redirect_uri == self.expected_redirect_uri:
                    self.log_test("Auth URL - redirect_uri parametresi değeri", True, 
                                f"Doğru: {auth_url_redirect_uri}")
                else:
                    self.log_test("Auth URL - redirect_uri parametresi değeri", False,
                                f"Beklenen: {self.expected_redirect_uri}, Auth URL'de: {auth_url_redirect_uri}")
                    return False
                
                # Auth URL uzunluğu ve formatı kontrol et
                if len(auth_url) > 400:  # Reasonable length check
                    self.log_test("Auth URL - format ve uzunluk", True, f"Auth URL uzunluğu: {len(auth_url)} karakter")
                else:
                    self.log_test("Auth URL - format ve uzunluk", False, f"Auth URL çok kısa: {len(auth_url)} karakter")
                    return False
                
                # State parametresi var mı?
                if "state" in query_params and len(query_params["state"][0]) > 10:
                    self.log_test("Auth URL - state parametresi", True, f"State: {query_params['state'][0][:20]}...")
                else:
                    self.log_test("Auth URL - state parametresi", False, "State parametresi eksik veya çok kısa")
                    return False
                
                print(f"   📋 Auth URL Detayları:")
                print(f"      - URL Uzunluğu: {len(auth_url)} karakter")
                print(f"      - Redirect URI: {auth_url_redirect_uri}")
                print(f"      - State: {query_params.get('state', ['N/A'])[0][:30]}...")
                print(f"      - Client ID: {query_params.get('client_id', ['N/A'])[0][:20]}...")
                
                return True
                
            else:
                self.log_test("Auth URL Endpoint - HTTP Status", False, 
                            f"Beklenen: 200, Dönen: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                return False
                
        except Exception as e:
            self.log_test("Auth URL Endpoint - Exception", False, f"Hata: {str(e)}")
            return False
    
    def test_outlook_status_endpoint(self):
        """GET /api/outlook/status endpoint'ini test et"""
        print("\n🔍 Outlook Status Endpoint Testi...")
        
        if not self.token:
            self.log_test("Outlook Status", False, "Token bulunamadı")
            return False
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        try:
            response = requests.get(f"{self.base_url}/outlook/status", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Graph SDK available kontrolü
                graph_available = data.get("graph_sdk_available", False)
                credentials_configured = data.get("credentials_configured", False)
                
                self.log_test("Outlook Status - Graph SDK Available", graph_available, 
                            f"Graph SDK: {'Mevcut' if graph_available else 'Eksik'}")
                
                self.log_test("Outlook Status - Credentials Configured", credentials_configured,
                            f"Credentials: {'Configured' if credentials_configured else 'Missing'}")
                
                print(f"   📋 Outlook Status Detayları:")
                print(f"      - Graph SDK Available: {graph_available}")
                print(f"      - Credentials Configured: {credentials_configured}")
                print(f"      - Message: {data.get('message', 'N/A')}")
                
                return graph_available and credentials_configured
                
            else:
                self.log_test("Outlook Status - HTTP Status", False, 
                            f"Beklenen: 200, Dönen: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Outlook Status - Exception", False, f"Hata: {str(e)}")
            return False
    
    def test_environment_variable_consistency(self):
        """Environment variable tutarlılığını test et"""
        print("\n🔍 Environment Variable Tutarlılık Testi...")
        
        # Backend .env dosyasını oku
        try:
            with open('/app/backend/.env', 'r') as f:
                env_content = f.read()
            
            # REDIRECT_URI değerini bul
            redirect_uri_match = re.search(r'REDIRECT_URI="([^"]*)"', env_content)
            
            if redirect_uri_match:
                env_redirect_uri = redirect_uri_match.group(1)
                
                if env_redirect_uri == self.expected_redirect_uri:
                    self.log_test("Environment Variable - REDIRECT_URI değeri", True, 
                                f"Doğru: {env_redirect_uri}")
                else:
                    self.log_test("Environment Variable - REDIRECT_URI değeri", False,
                                f"Beklenen: {self.expected_redirect_uri}, .env'de: {env_redirect_uri}")
                    return False
            else:
                self.log_test("Environment Variable - REDIRECT_URI varlığı", False, 
                            "REDIRECT_URI .env dosyasında bulunamadı")
                return False
            
            # Diğer Azure credentials'ları kontrol et
            azure_client_id = re.search(r'AZURE_CLIENT_ID="([^"]*)"', env_content)
            azure_client_secret = re.search(r'AZURE_CLIENT_SECRET="([^"]*)"', env_content)
            azure_tenant_id = re.search(r'AZURE_TENANT_ID="([^"]*)"', env_content)
            
            credentials_ok = all([azure_client_id, azure_client_secret, azure_tenant_id])
            
            self.log_test("Environment Variable - Azure Credentials", credentials_ok,
                        f"Client ID: {'✓' if azure_client_id else '✗'}, "
                        f"Client Secret: {'✓' if azure_client_secret else '✗'}, "
                        f"Tenant ID: {'✓' if azure_tenant_id else '✗'}")
            
            return credentials_ok
            
        except Exception as e:
            self.log_test("Environment Variable - Dosya Okuma", False, f"Hata: {str(e)}")
            return False
    
    def test_code_consistency_in_server_py(self):
        """server.py dosyasındaki kod tutarlılığını test et"""
        print("\n🔍 Kod Tutarlılığı Testi (server.py)...")
        
        try:
            with open('/app/backend/server.py', 'r') as f:
                server_content = f.read()
            
            # Tüm redirect_uri kullanımlarını bul
            redirect_uri_patterns = [
                r"redirect_uri = os\.getenv\('REDIRECT_URI', '([^']*)'\)",
                r'"redirect_uri": os\.getenv\(\'REDIRECT_URI\', \'([^\']*)\'\)',
                r"redirect_uri.*=.*'([^']*auth/callback[^']*)'",
                r'"redirect_uri".*:.*"([^"]*auth/callback[^"]*)"'
            ]
            
            found_uris = []
            
            for pattern in redirect_uri_patterns:
                matches = re.findall(pattern, server_content)
                found_uris.extend(matches)
            
            # Unique URI'ları al
            unique_uris = list(set(found_uris))
            
            if len(unique_uris) == 1 and unique_uris[0] == self.expected_redirect_uri:
                self.log_test("Kod Tutarlılığı - Redirect URI Default Değerleri", True,
                            f"Tüm default değerler aynı: {unique_uris[0]}")
            elif len(unique_uris) == 1:
                self.log_test("Kod Tutarlılığı - Redirect URI Default Değerleri", False,
                            f"Tutarlı ama yanlış değer: {unique_uris[0]}, Beklenen: {self.expected_redirect_uri}")
                return False
            else:
                self.log_test("Kod Tutarlılığı - Redirect URI Default Değerleri", False,
                            f"Tutarsız değerler bulundu: {unique_uris}")
                return False
            
            # Line 2376 özelinde kontrol et (önceki sorunlu satır)
            lines = server_content.split('\n')
            if len(lines) > 2375:  # 0-indexed, so 2375 is line 2376
                line_2376 = lines[2375].strip()
                if self.expected_redirect_uri in line_2376:
                    self.log_test("Kod Tutarlılığı - Line 2376 Fix", True,
                                f"Line 2376 düzeltilmiş: {line_2376[:60]}...")
                else:
                    self.log_test("Kod Tutarlılığı - Line 2376 Fix", False,
                                f"Line 2376 hala sorunlu: {line_2376}")
                    return False
            
            # os.getenv('REDIRECT_URI') kullanımlarını say
            redirect_uri_getenv_count = len(re.findall(r"os\.getenv\(['\"]REDIRECT_URI['\"]", server_content))
            
            if redirect_uri_getenv_count >= 2:  # Auth URL generation ve token exchange'de
                self.log_test("Kod Tutarlılığı - Environment Variable Kullanımı", True,
                            f"{redirect_uri_getenv_count} yerde os.getenv('REDIRECT_URI') kullanılıyor")
            else:
                self.log_test("Kod Tutarlılığı - Environment Variable Kullanımı", False,
                            f"Sadece {redirect_uri_getenv_count} yerde os.getenv('REDIRECT_URI') kullanılıyor")
                return False
            
            return True
            
        except Exception as e:
            self.log_test("Kod Tutarlılığı - Dosya Okuma", False, f"Hata: {str(e)}")
            return False
    
    def test_token_exchange_consistency(self):
        """Token exchange fonksiyonundaki redirect URI tutarlılığını test et"""
        print("\n🔍 Token Exchange Redirect URI Tutarlılığı...")
        
        try:
            with open('/app/backend/server.py', 'r') as f:
                server_content = f.read()
            
            # exchange_code_for_tokens fonksiyonunu bul
            exchange_function_match = re.search(
                r'async def exchange_code_for_tokens.*?(?=async def|\Z)', 
                server_content, 
                re.DOTALL
            )
            
            if not exchange_function_match:
                self.log_test("Token Exchange - Fonksiyon Varlığı", False, 
                            "exchange_code_for_tokens fonksiyonu bulunamadı")
                return False
            
            exchange_function = exchange_function_match.group(0)
            
            # Fonksiyon içindeki redirect_uri kullanımını kontrol et
            redirect_uri_in_exchange = re.search(
                r"redirect_uri = os\.getenv\('REDIRECT_URI', '([^']*)'\)", 
                exchange_function
            )
            
            if redirect_uri_in_exchange:
                exchange_default_uri = redirect_uri_in_exchange.group(1)
                
                if exchange_default_uri == self.expected_redirect_uri:
                    self.log_test("Token Exchange - Redirect URI Default", True,
                                f"Doğru default değer: {exchange_default_uri}")
                else:
                    self.log_test("Token Exchange - Redirect URI Default", False,
                                f"Yanlış default: {exchange_default_uri}, Beklenen: {self.expected_redirect_uri}")
                    return False
            else:
                self.log_test("Token Exchange - Redirect URI Kullanımı", False,
                            "Token exchange'de redirect_uri kullanımı bulunamadı")
                return False
            
            # Alternative URIs listesini kontrol et (fallback mechanism)
            alternative_uris_match = re.search(
                r'alternative_uris = \[(.*?)\]', 
                exchange_function, 
                re.DOTALL
            )
            
            if alternative_uris_match:
                alternatives_text = alternative_uris_match.group(1)
                if self.expected_redirect_uri in alternatives_text:
                    self.log_test("Token Exchange - Alternative URIs", True,
                                "Expected URI alternative listesinde mevcut")
                else:
                    self.log_test("Token Exchange - Alternative URIs", False,
                                "Expected URI alternative listesinde yok")
                    return False
            
            return True
            
        except Exception as e:
            self.log_test("Token Exchange - Analiz", False, f"Hata: {str(e)}")
            return False
    
    def run_comprehensive_test(self):
        """Kapsamlı redirect URI tutarlılık testini çalıştır"""
        print("🚀 OUTLOOK OAUTH REDIRECT URI TUTARLILIK TESTİ BAŞLADI")
        print("=" * 60)
        print(f"📋 Test Edilen Redirect URI: {self.expected_redirect_uri}")
        print(f"🌐 Backend URL: {self.base_url}")
        print(f"👤 Test Kullanıcısı: tyrzmusak@gmail.com")
        print("=" * 60)
        
        # 1. Kullanıcı girişi
        if not self.login_test_user():
            print("\n❌ Kullanıcı girişi başarısız, testler durduruluyor")
            return False
        
        # 2. Environment variable tutarlılığı
        env_test = self.test_environment_variable_consistency()
        
        # 3. Kod tutarlılığı
        code_test = self.test_code_consistency_in_server_py()
        
        # 4. Token exchange tutarlılığı
        token_test = self.test_token_exchange_consistency()
        
        # 5. Outlook status endpoint
        status_test = self.test_outlook_status_endpoint()
        
        # 6. Auth URL endpoint (ana test)
        auth_url_test = self.test_outlook_auth_url_endpoint()
        
        # Sonuçları özetle
        print("\n" + "=" * 60)
        print("📊 TEST SONUÇLARI")
        print("=" * 60)
        print(f"✅ Başarılı Testler: {self.tests_passed}")
        print(f"❌ Başarısız Testler: {self.tests_run - self.tests_passed}")
        print(f"📈 Başarı Oranı: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        all_critical_tests_passed = all([
            env_test, code_test, token_test, status_test, auth_url_test
        ])
        
        if all_critical_tests_passed:
            print("\n🎉 TÜM KRİTİK TESTLER BAŞARILI!")
            print("✅ Outlook OAuth redirect URI tutarlılığı sağlandı")
            print("✅ Environment variable doğru kullanılıyor")
            print("✅ Kod tutarlılığı mevcut")
            print("✅ Token exchange tutarlı")
            print("✅ Auth URL generation çalışıyor")
        else:
            print("\n⚠️  BAZI KRİTİK TESTLER BAŞARISIZ!")
            print("❌ Redirect URI tutarlılığında sorunlar var")
        
        return all_critical_tests_passed

def main():
    """Ana test fonksiyonu"""
    tester = OutlookRedirectURITester()
    success = tester.run_comprehensive_test()
    
    if success:
        print("\n🎯 SONUÇ: Outlook OAuth redirect URI düzeltmesi başarıyla doğrulandı!")
        sys.exit(0)
    else:
        print("\n🚨 SONUÇ: Redirect URI tutarlılığında sorunlar tespit edildi!")
        sys.exit(1)

if __name__ == "__main__":
    main()