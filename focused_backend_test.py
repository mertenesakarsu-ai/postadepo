#!/usr/bin/env python3
"""
PostaDepo Backend Focused Test - Turkish Review Request
Özellikle uzun e-posta içerikleri, attachment download ve authentication sistemini test eder.
"""

import requests
import json
import sys
from datetime import datetime

class PostaDepoFocusedTester:
    def __init__(self, base_url="https://code-state-helper.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.user = None
        self.test_results = []

    def log_result(self, test_name, success, details=""):
        """Test sonucunu kaydet"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ BAŞARILI" if success else "❌ BAŞARISIZ"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Detay: {details}")
        print()

    def authenticate(self):
        """Demo kullanıcısı ile giriş yap"""
        print("🔐 Authentication Test - Demo Kullanıcısı Girişi")
        print("=" * 60)
        
        try:
            url = f"{self.base_url}/auth/login"
            data = {"email": "demo@postadepo.com", "password": "demo123"}
            
            response = requests.post(url, json=data)
            
            if response.status_code == 200:
                result = response.json()
                self.token = result.get('token')
                self.user = result.get('user')
                
                self.log_result(
                    "Demo Kullanıcısı Girişi", 
                    True, 
                    f"Kullanıcı: {self.user.get('email')}, Token alındı"
                )
                return True
            else:
                self.log_result(
                    "Demo Kullanıcısı Girişi", 
                    False, 
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Demo Kullanıcısı Girişi", False, f"Hata: {str(e)}")
            return False

    def test_demo_email_generation(self):
        """Demo e-posta üretim fonksiyonunu test et - uzun içerikli e-postaları kontrol et"""
        print("📧 Demo E-posta Üretim Testi - Uzun İçerik Kontrolü")
        print("=" * 60)
        
        if not self.token:
            self.log_result("Demo E-posta Üretimi", False, "Authentication gerekli")
            return False
        
        try:
            # Önce mevcut e-postaları al
            headers = {'Authorization': f'Bearer {self.token}'}
            url = f"{self.base_url}/emails?folder=all"
            
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                self.log_result("Demo E-posta Üretimi", False, f"HTTP {response.status_code}")
                return False
            
            data = response.json()
            emails = data.get('emails', [])
            
            print(f"📊 Toplam e-posta sayısı: {len(emails)}")
            
            # Uzun içerikli e-postaları analiz et
            long_content_emails = []
            short_content_emails = []
            total_content_length = 0
            
            for email in emails:
                content = email.get('content', '')
                content_length = len(content)
                total_content_length += content_length
                
                if content_length > 1000:  # 1000 karakterden uzun
                    long_content_emails.append({
                        'subject': email.get('subject', 'No subject')[:50],
                        'length': content_length,
                        'sender': email.get('sender', 'Unknown')[:30],
                        'preview': content[:100] + "..." if len(content) > 100 else content
                    })
                else:
                    short_content_emails.append({
                        'subject': email.get('subject', 'No subject')[:50],
                        'length': content_length
                    })
            
            avg_content_length = total_content_length / len(emails) if emails else 0
            
            print(f"📏 Ortalama içerik uzunluğu: {avg_content_length:.0f} karakter")
            print(f"📝 Uzun içerikli e-postalar (>1000 kar): {len(long_content_emails)}")
            print(f"📄 Kısa içerikli e-postalar (<1000 kar): {len(short_content_emails)}")
            
            # Uzun içerikli e-postaların detaylarını göster
            print("\n🔍 Uzun İçerikli E-posta Örnekleri:")
            for i, email in enumerate(long_content_emails[:5]):  # İlk 5 tanesi
                print(f"   {i+1}. {email['subject']}...")
                print(f"      Gönderen: {email['sender']}")
                print(f"      Uzunluk: {email['length']} karakter")
                print(f"      Önizleme: {email['preview']}")
                print()
            
            # Başarı kriterleri
            success_criteria = {
                'avg_length_ok': avg_content_length > 500,  # Ortalama 500+ karakter
                'long_emails_exist': len(long_content_emails) > 0,  # En az 1 uzun e-posta
                'variety_exists': len(long_content_emails) >= len(emails) * 0.3  # %30'u uzun
            }
            
            success = all(success_criteria.values())
            
            details = f"Ortalama: {avg_content_length:.0f} kar, Uzun: {len(long_content_emails)}/{len(emails)}"
            if not success:
                failed_criteria = [k for k, v in success_criteria.items() if not v]
                details += f", Başarısız kriterler: {failed_criteria}"
            
            self.log_result("Demo E-posta Üretimi - Uzun İçerik", success, details)
            return success
            
        except Exception as e:
            self.log_result("Demo E-posta Üretimi", False, f"Hata: {str(e)}")
            return False

    def test_email_list_endpoint(self):
        """E-posta listesi endpoint'ini test et ve uzun content field'larını verify et"""
        print("📋 E-posta Listesi Endpoint Testi")
        print("=" * 60)
        
        if not self.token:
            self.log_result("E-posta Listesi", False, "Authentication gerekli")
            return False
        
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            folders = ['inbox', 'sent', 'all', 'spam']
            
            all_tests_passed = True
            folder_results = {}
            
            for folder in folders:
                url = f"{self.base_url}/emails?folder={folder}"
                response = requests.get(url, headers=headers)
                
                if response.status_code != 200:
                    self.log_result(f"E-posta Listesi - {folder}", False, f"HTTP {response.status_code}")
                    all_tests_passed = False
                    continue
                
                data = response.json()
                emails = data.get('emails', [])
                folder_counts = data.get('folderCounts', {})
                
                # Content field analizi
                content_analysis = {
                    'total_emails': len(emails),
                    'with_content': 0,
                    'long_content': 0,
                    'avg_length': 0,
                    'max_length': 0
                }
                
                total_length = 0
                for email in emails:
                    content = email.get('content', '')
                    if content:
                        content_analysis['with_content'] += 1
                        length = len(content)
                        total_length += length
                        
                        if length > 1000:
                            content_analysis['long_content'] += 1
                        
                        if length > content_analysis['max_length']:
                            content_analysis['max_length'] = length
                
                if content_analysis['with_content'] > 0:
                    content_analysis['avg_length'] = total_length / content_analysis['with_content']
                
                folder_results[folder] = content_analysis
                
                print(f"📁 {folder.upper()} Klasörü:")
                print(f"   Toplam e-posta: {content_analysis['total_emails']}")
                print(f"   İçerikli e-posta: {content_analysis['with_content']}")
                print(f"   Uzun içerikli (>1000): {content_analysis['long_content']}")
                print(f"   Ortalama uzunluk: {content_analysis['avg_length']:.0f} karakter")
                print(f"   En uzun: {content_analysis['max_length']} karakter")
                print(f"   Klasör sayıları: {folder_counts}")
                print()
            
            # Genel başarı değerlendirmesi
            total_long_content = sum(r['long_content'] for r in folder_results.values())
            total_emails = sum(r['total_emails'] for r in folder_results.values())
            
            success = (
                all_tests_passed and 
                total_long_content > 0 and 
                total_emails > 0
            )
            
            details = f"Toplam: {total_emails} e-posta, Uzun içerikli: {total_long_content}"
            self.log_result("E-posta Listesi Endpoint", success, details)
            return success
            
        except Exception as e:
            self.log_result("E-posta Listesi Endpoint", False, f"Hata: {str(e)}")
            return False

    def test_email_detail_endpoints(self):
        """E-posta detay endpoint'lerini test et"""
        print("🔍 E-posta Detay Endpoint'leri Testi")
        print("=" * 60)
        
        if not self.token:
            self.log_result("E-posta Detay Endpoint'leri", False, "Authentication gerekli")
            return False
        
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            
            # Önce e-posta listesi al
            url = f"{self.base_url}/emails?folder=inbox"
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                self.log_result("E-posta Detay - Liste Alma", False, f"HTTP {response.status_code}")
                return False
            
            data = response.json()
            emails = data.get('emails', [])
            
            if not emails:
                self.log_result("E-posta Detay Endpoint'leri", False, "Test için e-posta bulunamadı")
                return False
            
            # Thread endpoint'ini test et
            thread_tests_passed = 0
            thread_tests_total = 0
            
            for email in emails[:5]:  # İlk 5 e-postayı test et
                thread_id = email.get('thread_id')
                if not thread_id:
                    continue
                
                thread_tests_total += 1
                
                # Thread endpoint'ini çağır
                thread_url = f"{self.base_url}/emails/thread/{thread_id}"
                thread_response = requests.get(thread_url, headers=headers)
                
                if thread_response.status_code == 200:
                    thread_data = thread_response.json()
                    thread_emails = thread_data.get('emails', [])
                    
                    print(f"🧵 Thread {thread_id[:8]}... : {len(thread_emails)} e-posta")
                    
                    # Thread'deki e-postaların içerik uzunluklarını kontrol et
                    for t_email in thread_emails:
                        content_length = len(t_email.get('content', ''))
                        subject = t_email.get('subject', 'No subject')[:30]
                        print(f"   - {subject}... ({content_length} karakter)")
                    
                    thread_tests_passed += 1
                else:
                    print(f"❌ Thread {thread_id[:8]}... test başarısız: HTTP {thread_response.status_code}")
            
            # Mark as read endpoint'ini test et
            read_tests_passed = 0
            read_tests_total = 0
            
            for email in emails[:3]:  # İlk 3 e-postayı test et
                email_id = email.get('id')
                if not email_id:
                    continue
                
                read_tests_total += 1
                
                # Mark as read endpoint'ini çağır
                read_url = f"{self.base_url}/emails/{email_id}/read"
                read_response = requests.put(read_url, headers=headers)
                
                if read_response.status_code == 200:
                    read_tests_passed += 1
                    subject = email.get('subject', 'No subject')[:30]
                    print(f"📖 E-posta okundu olarak işaretlendi: {subject}...")
                else:
                    print(f"❌ Read test başarısız: HTTP {read_response.status_code}")
            
            # Başarı değerlendirmesi
            success = (
                thread_tests_passed == thread_tests_total and
                read_tests_passed == read_tests_total and
                thread_tests_total > 0 and
                read_tests_total > 0
            )
            
            details = f"Thread: {thread_tests_passed}/{thread_tests_total}, Read: {read_tests_passed}/{read_tests_total}"
            self.log_result("E-posta Detay Endpoint'leri", success, details)
            return success
            
        except Exception as e:
            self.log_result("E-posta Detay Endpoint'leri", False, f"Hata: {str(e)}")
            return False

    def test_attachment_download_comprehensive(self):
        """Attachment download API'sini kapsamlı test et"""
        print("📎 Attachment Download API Kapsamlı Test")
        print("=" * 60)
        
        if not self.token:
            self.log_result("Attachment Download", False, "Authentication gerekli")
            return False
        
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            
            # E-postaları al ve attachment'ları bul
            url = f"{self.base_url}/emails?folder=all"
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                self.log_result("Attachment Download - E-posta Alma", False, f"HTTP {response.status_code}")
                return False
            
            data = response.json()
            emails = data.get('emails', [])
            
            # Attachment'lı e-postaları bul
            attachments_to_test = []
            
            for email in emails:
                attachments = email.get('attachments', [])
                for attachment in attachments:
                    if len(attachments_to_test) >= 10:  # En fazla 10 attachment test et
                        break
                    
                    att_info = {
                        'id': attachment.get('id'),
                        'name': attachment.get('name'),
                        'type': attachment.get('type'),
                        'size': attachment.get('size'),
                        'email_subject': email.get('subject', 'No subject')[:30]
                    }
                    
                    if att_info['id']:
                        attachments_to_test.append(att_info)
            
            if not attachments_to_test:
                self.log_result("Attachment Download", False, "Test için attachment bulunamadı")
                return False
            
            print(f"🎯 {len(attachments_to_test)} attachment test edilecek")
            
            # Attachment download testleri
            successful_downloads = 0
            failed_downloads = 0
            file_types_tested = set()
            
            for i, att in enumerate(attachments_to_test):
                print(f"\n📥 Test {i+1}/{len(attachments_to_test)}: {att['name']}")
                print(f"   E-posta: {att['email_subject']}...")
                print(f"   Tip: {att['type']}")
                print(f"   Boyut: {att['size']} bytes")
                
                # Download endpoint'ini çağır
                download_url = f"{self.base_url}/attachments/download/{att['id']}"
                download_response = requests.get(download_url, headers=headers)
                
                if download_response.status_code == 200:
                    successful_downloads += 1
                    
                    # Response header'larını kontrol et
                    content_type = download_response.headers.get('Content-Type', '')
                    content_disposition = download_response.headers.get('Content-Disposition', '')
                    content_length = len(download_response.content)
                    
                    print(f"   ✅ İndirme başarılı")
                    print(f"   📋 Content-Type: {content_type}")
                    print(f"   📋 Content-Length: {content_length} bytes")
                    print(f"   📋 Content-Disposition: {content_disposition[:50]}...")
                    
                    # Dosya tipini kaydet
                    if '.' in att['name']:
                        ext = att['name'].split('.')[-1].lower()
                        file_types_tested.add(ext)
                    
                    # Türkçe karakter testi
                    if any(char in att['name'] for char in 'çğıöşüÇĞIÖŞÜ'):
                        print(f"   🇹🇷 Türkçe karakter testi: BAŞARILI")
                    
                else:
                    failed_downloads += 1
                    print(f"   ❌ İndirme başarısız: HTTP {download_response.status_code}")
                    print(f"   📋 Hata: {download_response.text[:100]}")
            
            # Hata senaryoları testi
            print(f"\n🚫 Hata Senaryoları Testi:")
            
            # Geçersiz attachment ID
            invalid_url = f"{self.base_url}/attachments/download/invalid-id"
            invalid_response = requests.get(invalid_url, headers=headers)
            invalid_test_passed = invalid_response.status_code == 404
            
            print(f"   Geçersiz ID testi: {'✅' if invalid_test_passed else '❌'}")
            
            # Yetkilendirme olmadan
            if attachments_to_test:
                unauth_url = f"{self.base_url}/attachments/download/{attachments_to_test[0]['id']}"
                unauth_response = requests.get(unauth_url)  # Header yok
                unauth_test_passed = unauth_response.status_code in [401, 403]
                
                print(f"   Yetkilendirme testi: {'✅' if unauth_test_passed else '❌'}")
            else:
                unauth_test_passed = True
            
            # Sonuçları değerlendir
            success_rate = successful_downloads / len(attachments_to_test) if attachments_to_test else 0
            
            success = (
                success_rate >= 0.8 and  # %80 başarı oranı
                successful_downloads > 0 and
                invalid_test_passed and
                unauth_test_passed
            )
            
            print(f"\n📊 ATTACHMENT DOWNLOAD TEST SONUÇLARI:")
            print(f"   ✅ Başarılı indirmeler: {successful_downloads}/{len(attachments_to_test)}")
            print(f"   ❌ Başarısız indirmeler: {failed_downloads}")
            print(f"   📁 Test edilen dosya tipleri: {sorted(file_types_tested)}")
            print(f"   📈 Başarı oranı: {success_rate:.1%}")
            
            details = f"Başarı: {successful_downloads}/{len(attachments_to_test)} ({success_rate:.1%})"
            self.log_result("Attachment Download API", success, details)
            return success
            
        except Exception as e:
            self.log_result("Attachment Download API", False, f"Hata: {str(e)}")
            return False

    def test_authentication_system(self):
        """Authentication sisteminin çalışıp çalışmadığını kontrol et"""
        print("🔐 Authentication Sistemi Testi")
        print("=" * 60)
        
        try:
            # 1. Geçerli giriş testi (zaten yapıldı)
            valid_login_success = self.token is not None
            
            # 2. Geçersiz giriş testi
            invalid_url = f"{self.base_url}/auth/login"
            invalid_data = {"email": "invalid@test.com", "password": "wrongpass"}
            invalid_response = requests.post(invalid_url, json=invalid_data)
            invalid_login_test = invalid_response.status_code == 401
            
            print(f"❌ Geçersiz giriş testi: {'✅ BAŞARILI' if invalid_login_test else '❌ BAŞARISIZ'}")
            
            # 3. Token olmadan korumalı endpoint erişimi
            protected_url = f"{self.base_url}/emails"
            unauth_response = requests.get(protected_url)  # Token yok
            unauth_test = unauth_response.status_code in [401, 403]
            
            print(f"🚫 Yetkisiz erişim testi: {'✅ BAŞARILI' if unauth_test else '❌ BAŞARISIZ'}")
            
            # 4. Geçerli token ile erişim
            if self.token:
                auth_headers = {'Authorization': f'Bearer {self.token}'}
                auth_response = requests.get(protected_url, headers=auth_headers)
                auth_test = auth_response.status_code == 200
                
                print(f"✅ Yetkili erişim testi: {'✅ BAŞARILI' if auth_test else '❌ BAŞARISIZ'}")
            else:
                auth_test = False
                print(f"✅ Yetkili erişim testi: ❌ BAŞARISIZ (Token yok)")
            
            # 5. Kullanıcı kayıt testi
            import random
            test_email = f"testuser{random.randint(1000, 9999)}@test.com"
            register_data = {
                "name": "Test User",
                "email": test_email,
                "password": "testpass123"
            }
            
            register_url = f"{self.base_url}/auth/register"
            register_response = requests.post(register_url, json=register_data)
            register_test = register_response.status_code == 200
            
            if register_test:
                register_result = register_response.json()
                approved = register_result.get('approved', True)
                whitelist_test = not approved  # Yeni kullanıcı onaylanmamış olmalı
                
                print(f"📝 Kullanıcı kayıt testi: ✅ BAŞARILI")
                print(f"🔒 Whitelist testi: {'✅ BAŞARILI' if whitelist_test else '❌ BAŞARISIZ'}")
                
                # Onaylanmamış kullanıcı ile giriş denemesi
                unapproved_login_data = {"email": test_email, "password": "testpass123"}
                unapproved_response = requests.post(invalid_url, json=unapproved_login_data)
                unapproved_test = unapproved_response.status_code == 403
                
                print(f"🚫 Onaylanmamış giriş testi: {'✅ BAŞARILI' if unapproved_test else '❌ BAŞARISIZ'}")
            else:
                whitelist_test = False
                unapproved_test = False
                print(f"📝 Kullanıcı kayıt testi: ❌ BAŞARISIZ")
                print(f"🔒 Whitelist testi: ❌ BAŞARISIZ")
                print(f"🚫 Onaylanmamış giriş testi: ❌ BAŞARISIZ")
            
            # Genel başarı değerlendirmesi
            all_tests = [
                valid_login_success,
                invalid_login_test,
                unauth_test,
                auth_test,
                register_test,
                whitelist_test,
                unapproved_test
            ]
            
            passed_tests = sum(all_tests)
            total_tests = len(all_tests)
            
            success = passed_tests >= total_tests * 0.8  # %80 başarı oranı
            
            details = f"Geçen testler: {passed_tests}/{total_tests}"
            self.log_result("Authentication Sistemi", success, details)
            return success
            
        except Exception as e:
            self.log_result("Authentication Sistemi", False, f"Hata: {str(e)}")
            return False

    def run_all_tests(self):
        """Tüm testleri çalıştır"""
        print("🚀 PostaDepo Backend Focused Test Başlıyor")
        print("=" * 80)
        print("📋 Test Kapsamı:")
        print("   1. Demo e-posta üretim fonksiyonu (uzun içerik kontrolü)")
        print("   2. E-posta listesi endpoint'i (content field verification)")
        print("   3. E-posta detay endpoint'leri")
        print("   4. Attachment download API'si")
        print("   5. Authentication sistemi")
        print("=" * 80)
        print()
        
        # Test sırası
        tests = [
            ("Authentication", self.authenticate),
            ("Demo E-posta Üretimi", self.test_demo_email_generation),
            ("E-posta Listesi Endpoint", self.test_email_list_endpoint),
            ("E-posta Detay Endpoint'leri", self.test_email_detail_endpoints),
            ("Attachment Download API", self.test_attachment_download_comprehensive),
            ("Authentication Sistemi", self.test_authentication_system)
        ]
        
        successful_tests = 0
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                if result:
                    successful_tests += 1
            except Exception as e:
                print(f"💥 {test_name} testi çöktü: {str(e)}")
                self.log_result(test_name, False, f"Test çöktü: {str(e)}")
        
        # Final sonuçlar
        print("=" * 80)
        print("📊 TEST SONUÇLARI")
        print("=" * 80)
        
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}")
            if result['details']:
                print(f"   {result['details']}")
        
        print("=" * 80)
        print(f"🎯 GENEL SONUÇ: {successful_tests}/{len(tests)} test başarılı")
        
        if successful_tests == len(tests):
            print("🎉 TÜM TESTLER BAŞARILI!")
            return True
        else:
            failed_count = len(tests) - successful_tests
            print(f"⚠️  {failed_count} test başarısız")
            return False

def main():
    tester = PostaDepoFocusedTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())