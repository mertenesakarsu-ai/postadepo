#!/usr/bin/env python3
"""
reCAPTCHA Doğrulama Sistemi Test Scripti
PostaDepo Backend API - reCAPTCHA Endpoint Testi

Test Senaryoları:
1. reCAPTCHA endpoint'i çalışıyor mu? (/api/verify-recaptcha)
2. Geçersiz token ile test
3. Boş token ile test  
4. Backend'de httpx kütüphanesi çalışıyor mu?
5. Environment variables doğru şekilde yükleniyor mu? (RECAPTCHA_SECRET_KEY)
"""

import requests
import json
import sys
import os
from datetime import datetime

class RecaptchaAPITester:
    def __init__(self, base_url="https://yaml-doctor.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test_result(self, test_name, success, details=""):
        """Test sonucunu kaydet"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        result = {
            'test_name': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ BAŞARILI" if success else "❌ BAŞARISIZ"
        print(f"\n🔍 Test: {test_name}")
        print(f"   Sonuç: {status}")
        if details:
            print(f"   Detay: {details}")

    def test_recaptcha_empty_token(self):
        """Test 1: Boş token ile reCAPTCHA doğrulama"""
        print("\n" + "="*60)
        print("TEST 1: BOŞ TOKEN İLE reCAPTCHA DOĞRULAMA")
        print("="*60)
        
        url = f"{self.base_url}/verify-recaptcha"
        headers = {'Content-Type': 'application/json'}
        data = {"recaptcha_token": ""}
        
        try:
            print(f"📡 İstek gönderiliyor: POST {url}")
            print(f"📋 Payload: {json.dumps(data, indent=2)}")
            
            response = requests.post(url, json=data, headers=headers, timeout=10)
            
            print(f"📊 Response Status: {response.status_code}")
            print(f"📄 Response Headers: {dict(response.headers)}")
            
            try:
                response_json = response.json()
                print(f"📝 Response Body: {json.dumps(response_json, indent=2, ensure_ascii=False)}")
            except:
                print(f"📝 Response Body (text): {response.text}")
            
            # Boş token için 400 Bad Request bekliyoruz
            if response.status_code == 400:
                self.log_test_result(
                    "Boş Token Testi", 
                    True, 
                    f"Boş token doğru şekilde reddedildi (HTTP {response.status_code})"
                )
                return True
            else:
                self.log_test_result(
                    "Boş Token Testi", 
                    False, 
                    f"Beklenmeyen status code: {response.status_code} (beklenen: 400)"
                )
                return False
                
        except requests.exceptions.Timeout:
            self.log_test_result("Boş Token Testi", False, "Request timeout (10 saniye)")
            return False
        except requests.exceptions.ConnectionError:
            self.log_test_result("Boş Token Testi", False, "Bağlantı hatası - Backend erişilemez")
            return False
        except Exception as e:
            self.log_test_result("Boş Token Testi", False, f"Beklenmeyen hata: {str(e)}")
            return False

    def test_recaptcha_invalid_token(self):
        """Test 2: Geçersiz token ile reCAPTCHA doğrulama"""
        print("\n" + "="*60)
        print("TEST 2: GEÇERSİZ TOKEN İLE reCAPTCHA DOĞRULAMA")
        print("="*60)
        
        url = f"{self.base_url}/verify-recaptcha"
        headers = {'Content-Type': 'application/json'}
        data = {"recaptcha_token": "invalid_token"}
        
        try:
            print(f"📡 İstek gönderiliyor: POST {url}")
            print(f"📋 Payload: {json.dumps(data, indent=2)}")
            
            response = requests.post(url, json=data, headers=headers, timeout=10)
            
            print(f"📊 Response Status: {response.status_code}")
            print(f"📄 Response Headers: {dict(response.headers)}")
            
            try:
                response_json = response.json()
                print(f"📝 Response Body: {json.dumps(response_json, indent=2, ensure_ascii=False)}")
                
                # Geçersiz token için success: false bekliyoruz
                if response.status_code == 200:
                    success_field = response_json.get('success', True)
                    if success_field == False:
                        self.log_test_result(
                            "Geçersiz Token Testi", 
                            True, 
                            f"Geçersiz token doğru şekilde reddedildi (success: false)"
                        )
                        return True
                    else:
                        self.log_test_result(
                            "Geçersiz Token Testi", 
                            False, 
                            f"Geçersiz token kabul edildi (success: {success_field})"
                        )
                        return False
                else:
                    self.log_test_result(
                        "Geçersiz Token Testi", 
                        False, 
                        f"Beklenmeyen status code: {response.status_code} (beklenen: 200)"
                    )
                    return False
                    
            except:
                print(f"📝 Response Body (text): {response.text}")
                self.log_test_result("Geçersiz Token Testi", False, "JSON parse hatası")
                return False
                
        except requests.exceptions.Timeout:
            self.log_test_result("Geçersiz Token Testi", False, "Request timeout (10 saniye)")
            return False
        except requests.exceptions.ConnectionError:
            self.log_test_result("Geçersiz Token Testi", False, "Bağlantı hatası - Backend erişilemez")
            return False
        except Exception as e:
            self.log_test_result("Geçersiz Token Testi", False, f"Beklenmeyen hata: {str(e)}")
            return False

    def test_recaptcha_test_token(self):
        """Test 3: Test token ile reCAPTCHA doğrulama"""
        print("\n" + "="*60)
        print("TEST 3: TEST TOKEN İLE reCAPTCHA DOĞRULAMA")
        print("="*60)
        
        url = f"{self.base_url}/verify-recaptcha"
        headers = {'Content-Type': 'application/json'}
        data = {"recaptcha_token": "test_token"}
        
        try:
            print(f"📡 İstek gönderiliyor: POST {url}")
            print(f"📋 Payload: {json.dumps(data, indent=2)}")
            
            response = requests.post(url, json=data, headers=headers, timeout=10)
            
            print(f"📊 Response Status: {response.status_code}")
            print(f"📄 Response Headers: {dict(response.headers)}")
            
            try:
                response_json = response.json()
                print(f"📝 Response Body: {json.dumps(response_json, indent=2, ensure_ascii=False)}")
                
                # Test token için de success: false bekliyoruz (Google API'den geçersiz dönecek)
                if response.status_code == 200:
                    success_field = response_json.get('success', True)
                    message = response_json.get('message', '')
                    
                    self.log_test_result(
                        "Test Token Testi", 
                        True, 
                        f"Test token işlendi (success: {success_field}, message: '{message}')"
                    )
                    return True
                else:
                    self.log_test_result(
                        "Test Token Testi", 
                        False, 
                        f"Beklenmeyen status code: {response.status_code} (beklenen: 200)"
                    )
                    return False
                    
            except:
                print(f"📝 Response Body (text): {response.text}")
                self.log_test_result("Test Token Testi", False, "JSON parse hatası")
                return False
                
        except requests.exceptions.Timeout:
            self.log_test_result("Test Token Testi", False, "Request timeout (10 saniye)")
            return False
        except requests.exceptions.ConnectionError:
            self.log_test_result("Test Token Testi", False, "Bağlantı hatası - Backend erişilemez")
            return False
        except Exception as e:
            self.log_test_result("Test Token Testi", False, f"Beklenmeyen hata: {str(e)}")
            return False

    def test_recaptcha_missing_field(self):
        """Test 4: recaptcha_token field'ı eksik"""
        print("\n" + "="*60)
        print("TEST 4: RECAPTCHA_TOKEN FIELD'I EKSİK")
        print("="*60)
        
        url = f"{self.base_url}/verify-recaptcha"
        headers = {'Content-Type': 'application/json'}
        data = {}  # recaptcha_token field'ı yok
        
        try:
            print(f"📡 İstek gönderiliyor: POST {url}")
            print(f"📋 Payload: {json.dumps(data, indent=2)}")
            
            response = requests.post(url, json=data, headers=headers, timeout=10)
            
            print(f"📊 Response Status: {response.status_code}")
            print(f"📄 Response Headers: {dict(response.headers)}")
            
            try:
                response_json = response.json()
                print(f"📝 Response Body: {json.dumps(response_json, indent=2, ensure_ascii=False)}")
            except:
                print(f"📝 Response Body (text): {response.text}")
            
            # Eksik field için 400 veya 422 bekliyoruz
            if response.status_code in [400, 422]:
                self.log_test_result(
                    "Eksik Field Testi", 
                    True, 
                    f"Eksik field doğru şekilde reddedildi (HTTP {response.status_code})"
                )
                return True
            else:
                self.log_test_result(
                    "Eksik Field Testi", 
                    False, 
                    f"Beklenmeyen status code: {response.status_code} (beklenen: 400 veya 422)"
                )
                return False
                
        except requests.exceptions.Timeout:
            self.log_test_result("Eksik Field Testi", False, "Request timeout (10 saniye)")
            return False
        except requests.exceptions.ConnectionError:
            self.log_test_result("Eksik Field Testi", False, "Bağlantı hatası - Backend erişilemez")
            return False
        except Exception as e:
            self.log_test_result("Eksik Field Testi", False, f"Beklenmeyen hata: {str(e)}")
            return False

    def test_backend_logs_check(self):
        """Test 5: Backend loglarını kontrol et"""
        print("\n" + "="*60)
        print("TEST 5: BACKEND LOGLARI KONTROLÜ")
        print("="*60)
        
        try:
            # Backend loglarını kontrol et
            import subprocess
            
            print("📋 Backend loglarını kontrol ediliyor...")
            
            # Supervisor backend loglarını kontrol et
            log_files = [
                "/var/log/supervisor/backend.out.log",
                "/var/log/supervisor/backend.err.log"
            ]
            
            log_found = False
            for log_file in log_files:
                if os.path.exists(log_file):
                    print(f"📄 Log dosyası bulundu: {log_file}")
                    
                    # Son 50 satırı oku
                    try:
                        result = subprocess.run(['tail', '-n', '50', log_file], 
                                              capture_output=True, text=True, timeout=5)
                        if result.stdout:
                            print(f"📝 Son 50 satır ({log_file}):")
                            print("-" * 40)
                            print(result.stdout)
                            print("-" * 40)
                            log_found = True
                            
                            # reCAPTCHA ile ilgili logları ara
                            if 'recaptcha' in result.stdout.lower() or 'verify-recaptcha' in result.stdout.lower():
                                print("✅ reCAPTCHA ile ilgili log kayıtları bulundu")
                            else:
                                print("⚠️  reCAPTCHA ile ilgili log kayıtları bulunamadı")
                                
                    except subprocess.TimeoutExpired:
                        print(f"⚠️  Log okuma timeout: {log_file}")
                    except Exception as e:
                        print(f"⚠️  Log okuma hatası: {str(e)}")
                else:
                    print(f"❌ Log dosyası bulunamadı: {log_file}")
            
            if log_found:
                self.log_test_result("Backend Logları Kontrolü", True, "Backend logları erişilebilir")
                return True
            else:
                self.log_test_result("Backend Logları Kontrolü", False, "Backend logları erişilemez")
                return False
                
        except Exception as e:
            self.log_test_result("Backend Logları Kontrolü", False, f"Log kontrol hatası: {str(e)}")
            return False

    def test_environment_variables(self):
        """Test 6: Environment variables kontrolü"""
        print("\n" + "="*60)
        print("TEST 6: ENVIRONMENT VARIABLES KONTROLÜ")
        print("="*60)
        
        try:
            # Backend .env dosyasını kontrol et
            env_file = "/app/backend/.env"
            
            if os.path.exists(env_file):
                print(f"📄 .env dosyası bulundu: {env_file}")
                
                with open(env_file, 'r') as f:
                    env_content = f.read()
                
                print("📝 .env dosyası içeriği:")
                print("-" * 40)
                print(env_content)
                print("-" * 40)
                
                # RECAPTCHA_SECRET_KEY var mı kontrol et
                if 'RECAPTCHA_SECRET_KEY' in env_content:
                    # Secret key değerini al
                    for line in env_content.split('\n'):
                        if line.startswith('RECAPTCHA_SECRET_KEY'):
                            secret_key = line.split('=', 1)[1].strip().strip('"')
                            if secret_key:
                                print(f"✅ RECAPTCHA_SECRET_KEY bulundu: {secret_key[:10]}...")
                                self.log_test_result(
                                    "Environment Variables Kontrolü", 
                                    True, 
                                    f"RECAPTCHA_SECRET_KEY mevcut ve dolu"
                                )
                                return True
                            else:
                                print("❌ RECAPTCHA_SECRET_KEY boş")
                                self.log_test_result(
                                    "Environment Variables Kontrolü", 
                                    False, 
                                    "RECAPTCHA_SECRET_KEY boş"
                                )
                                return False
                else:
                    print("❌ RECAPTCHA_SECRET_KEY bulunamadı")
                    self.log_test_result(
                        "Environment Variables Kontrolü", 
                        False, 
                        "RECAPTCHA_SECRET_KEY .env dosyasında yok"
                    )
                    return False
            else:
                print(f"❌ .env dosyası bulunamadı: {env_file}")
                self.log_test_result(
                    "Environment Variables Kontrolü", 
                    False, 
                    ".env dosyası bulunamadı"
                )
                return False
                
        except Exception as e:
            self.log_test_result("Environment Variables Kontrolü", False, f"Env kontrol hatası: {str(e)}")
            return False

    def test_httpx_library_check(self):
        """Test 7: httpx kütüphanesi kontrolü"""
        print("\n" + "="*60)
        print("TEST 7: HTTPX KÜTÜPHANESİ KONTROLÜ")
        print("="*60)
        
        try:
            # Backend requirements.txt dosyasını kontrol et
            requirements_file = "/app/backend/requirements.txt"
            
            if os.path.exists(requirements_file):
                print(f"📄 requirements.txt dosyası bulundu: {requirements_file}")
                
                with open(requirements_file, 'r') as f:
                    requirements_content = f.read()
                
                print("📝 requirements.txt içeriği:")
                print("-" * 40)
                print(requirements_content)
                print("-" * 40)
                
                # httpx var mı kontrol et
                if 'httpx' in requirements_content.lower():
                    print("✅ httpx kütüphanesi requirements.txt'de bulundu")
                    
                    # Python'da httpx import edilebilir mi kontrol et
                    try:
                        import subprocess
                        result = subprocess.run([
                            'python3', '-c', 'import httpx; print(f"httpx version: {httpx.__version__}")'
                        ], capture_output=True, text=True, timeout=10)
                        
                        if result.returncode == 0:
                            print(f"✅ httpx başarıyla import edildi: {result.stdout.strip()}")
                            self.log_test_result(
                                "httpx Kütüphanesi Kontrolü", 
                                True, 
                                f"httpx mevcut ve çalışıyor: {result.stdout.strip()}"
                            )
                            return True
                        else:
                            print(f"❌ httpx import hatası: {result.stderr}")
                            self.log_test_result(
                                "httpx Kütüphanesi Kontrolü", 
                                False, 
                                f"httpx import edilemiyor: {result.stderr}"
                            )
                            return False
                            
                    except subprocess.TimeoutExpired:
                        print("⚠️  httpx import test timeout")
                        self.log_test_result("httpx Kütüphanesi Kontrolü", False, "httpx test timeout")
                        return False
                    except Exception as e:
                        print(f"⚠️  httpx test hatası: {str(e)}")
                        self.log_test_result("httpx Kütüphanesi Kontrolü", False, f"httpx test hatası: {str(e)}")
                        return False
                else:
                    print("❌ httpx kütüphanesi requirements.txt'de bulunamadı")
                    self.log_test_result(
                        "httpx Kütüphanesi Kontrolü", 
                        False, 
                        "httpx requirements.txt'de yok"
                    )
                    return False
            else:
                print(f"❌ requirements.txt dosyası bulunamadı: {requirements_file}")
                self.log_test_result(
                    "httpx Kütüphanesi Kontrolü", 
                    False, 
                    "requirements.txt dosyası bulunamadı"
                )
                return False
                
        except Exception as e:
            self.log_test_result("httpx Kütüphanesi Kontrolü", False, f"httpx kontrol hatası: {str(e)}")
            return False

    def test_google_recaptcha_api_connectivity(self):
        """Test 8: Google reCAPTCHA API bağlantısı"""
        print("\n" + "="*60)
        print("TEST 8: GOOGLE reCAPTCHA API BAĞLANTISI")
        print("="*60)
        
        try:
            # Google reCAPTCHA API'sine doğrudan bağlantı testi
            google_api_url = "https://www.google.com/recaptcha/api/siteverify"
            
            print(f"📡 Google reCAPTCHA API'sine test isteği gönderiliyor: {google_api_url}")
            
            # Test verisi ile POST isteği
            test_data = {
                "secret": "test_secret_key",
                "response": "test_response_token"
            }
            
            response = requests.post(google_api_url, data=test_data, timeout=10)
            
            print(f"📊 Response Status: {response.status_code}")
            print(f"📄 Response Headers: {dict(response.headers)}")
            
            try:
                response_json = response.json()
                print(f"📝 Response Body: {json.dumps(response_json, indent=2, ensure_ascii=False)}")
                
                # Google API'den 200 response bekliyoruz (success: false olsa bile)
                if response.status_code == 200:
                    success_field = response_json.get('success', None)
                    error_codes = response_json.get('error-codes', [])
                    
                    print(f"✅ Google reCAPTCHA API'sine erişim başarılı")
                    print(f"   Success: {success_field}")
                    print(f"   Error codes: {error_codes}")
                    
                    self.log_test_result(
                        "Google reCAPTCHA API Bağlantısı", 
                        True, 
                        f"Google API erişilebilir (success: {success_field}, errors: {error_codes})"
                    )
                    return True
                else:
                    self.log_test_result(
                        "Google reCAPTCHA API Bağlantısı", 
                        False, 
                        f"Google API beklenmeyen status: {response.status_code}"
                    )
                    return False
                    
            except:
                print(f"📝 Response Body (text): {response.text}")
                self.log_test_result("Google reCAPTCHA API Bağlantısı", False, "Google API JSON parse hatası")
                return False
                
        except requests.exceptions.Timeout:
            self.log_test_result("Google reCAPTCHA API Bağlantısı", False, "Google API timeout (10 saniye)")
            return False
        except requests.exceptions.ConnectionError:
            self.log_test_result("Google reCAPTCHA API Bağlantısı", False, "Google API bağlantı hatası")
            return False
        except Exception as e:
            self.log_test_result("Google reCAPTCHA API Bağlantısı", False, f"Google API test hatası: {str(e)}")
            return False

    def run_all_tests(self):
        """Tüm testleri çalıştır"""
        print("🚀 reCAPTCHA DOĞRULAMA SİSTEMİ TEST BAŞLADI")
        print("=" * 80)
        print(f"📅 Test Zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 Backend URL: {self.base_url}")
        print("=" * 80)
        
        # Test sırası
        tests = [
            ("Environment Variables Kontrolü", self.test_environment_variables),
            ("httpx Kütüphanesi Kontrolü", self.test_httpx_library_check),
            ("Google reCAPTCHA API Bağlantısı", self.test_google_recaptcha_api_connectivity),
            ("Boş Token ile reCAPTCHA Testi", self.test_recaptcha_empty_token),
            ("Geçersiz Token ile reCAPTCHA Testi", self.test_recaptcha_invalid_token),
            ("Test Token ile reCAPTCHA Testi", self.test_recaptcha_test_token),
            ("Eksik Field ile reCAPTCHA Testi", self.test_recaptcha_missing_field),
            ("Backend Logları Kontrolü", self.test_backend_logs_check),
        ]
        
        for test_name, test_func in tests:
            try:
                print(f"\n🔄 {test_name} başlatılıyor...")
                test_func()
            except Exception as e:
                self.log_test_result(test_name, False, f"Test exception: {str(e)}")
                print(f"💥 {test_name} crashed: {str(e)}")
        
        # Final sonuçlar
        self.print_final_results()

    def print_final_results(self):
        """Final test sonuçlarını yazdır"""
        print("\n" + "=" * 80)
        print("📊 reCAPTCHA DOĞRULAMA SİSTEMİ TEST SONUÇLARI")
        print("=" * 80)
        
        print(f"📈 Toplam Test: {self.tests_run}")
        print(f"✅ Başarılı: {self.tests_passed}")
        print(f"❌ Başarısız: {self.tests_run - self.tests_passed}")
        print(f"📊 Başarı Oranı: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        print("\n📋 DETAYLI SONUÇLAR:")
        print("-" * 80)
        
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test_name']}")
            if result['details']:
                print(f"   └─ {result['details']}")
        
        print("\n🎯 ÖNEMLİ BULGULAR:")
        print("-" * 80)
        
        # Kritik testlerin durumunu kontrol et
        critical_tests = {
            'Environment Variables Kontrolü': False,
            'httpx Kütüphanesi Kontrolü': False,
            'Boş Token ile reCAPTCHA Testi': False,
            'Geçersiz Token ile reCAPTCHA Testi': False
        }
        
        for result in self.test_results:
            if result['test_name'] in critical_tests:
                critical_tests[result['test_name']] = result['success']
        
        all_critical_passed = all(critical_tests.values())
        
        if all_critical_passed:
            print("🎉 TÜM KRİTİK TESTLER BAŞARILI!")
            print("   ✅ reCAPTCHA endpoint'i çalışıyor")
            print("   ✅ Environment variables doğru yükleniyor")
            print("   ✅ httpx kütüphanesi çalışıyor")
            print("   ✅ Token doğrulama sistemi çalışıyor")
        else:
            print("⚠️  BAZI KRİTİK TESTLER BAŞARISIZ:")
            for test_name, passed in critical_tests.items():
                status = "✅" if passed else "❌"
                print(f"   {status} {test_name}")
        
        print("\n💡 TAVSİYELER:")
        print("-" * 80)
        
        if not critical_tests.get('Environment Variables Kontrolü', False):
            print("🔧 RECAPTCHA_SECRET_KEY environment variable'ını kontrol edin")
        
        if not critical_tests.get('httpx Kütüphanesi Kontrolü', False):
            print("📦 httpx kütüphanesini yükleyin: pip install httpx")
        
        if not critical_tests.get('Boş Token ile reCAPTCHA Testi', False):
            print("🛡️  Boş token validation'ını kontrol edin")
        
        if not critical_tests.get('Geçersiz Token ile reCAPTCHA Testi', False):
            print("🔍 Token doğrulama logic'ini kontrol edin")
        
        print("\n" + "=" * 80)
        
        return all_critical_passed

def main():
    """Ana test fonksiyonu"""
    tester = RecaptchaAPITester()
    success = tester.run_all_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())