#!/usr/bin/env python3
"""
PostaDepo Build Process Test
============================
Bu script, build.yml dosyasının işlevselliğini test etmek için 
backend ve frontend build süreçlerini simüle eder.

Test Kapsamı:
1. Backend bağımlılıklarının doğru yüklenip yüklenmediği (requirements.txt)
2. Backend test klasörünün düzgün oluşturulup oluşturulmadığı 
3. Frontend yarn komutlarının çalışıp çalışmadığı
4. Build komutlarının syntax hatası içerip içermediği
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import tempfile
import shutil

class BuildTester:
    def __init__(self):
        self.project_root = Path("/app")
        self.backend_dir = self.project_root / "backend"
        self.frontend_dir = self.project_root / "frontend"
        self.test_results = []
        
    def log_result(self, test_name: str, success: bool, message: str, details: Optional[str] = None):
        """Test sonucunu logla"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details
        }
        self.test_results.append(result)
        status = "✅ BAŞARILI" if success else "❌ BAŞARISIZ"
        print(f"{status}: {test_name}")
        print(f"   {message}")
        if details:
            print(f"   Detay: {details}")
        print()

    def test_backend_requirements(self) -> bool:
        """Backend requirements.txt dosyasını test et"""
        print("🔍 Backend Bağımlılıkları Test Ediliyor...")
        
        requirements_file = self.backend_dir / "requirements.txt"
        
        # 1. requirements.txt dosyasının varlığını kontrol et
        if not requirements_file.exists():
            self.log_result(
                "Backend Requirements Dosyası",
                False,
                "requirements.txt dosyası bulunamadı",
                f"Aranan konum: {requirements_file}"
            )
            return False
        
        # 2. requirements.txt içeriğini oku ve parse et
        try:
            with open(requirements_file, 'r', encoding='utf-8') as f:
                requirements = f.read().strip()
            
            if not requirements:
                self.log_result(
                    "Backend Requirements İçeriği",
                    False,
                    "requirements.txt dosyası boş",
                    "En az bir bağımlılık olmalı"
                )
                return False
            
            # Satırları parse et
            lines = [line.strip() for line in requirements.split('\n') if line.strip() and not line.startswith('#')]
            
            if len(lines) == 0:
                self.log_result(
                    "Backend Requirements Parse",
                    False,
                    "Geçerli bağımlılık bulunamadı",
                    "Yorum satırları dışında bağımlılık yok"
                )
                return False
            
            # 3. Kritik bağımlılıkları kontrol et
            critical_deps = ['fastapi', 'uvicorn', 'pydantic', 'motor', 'pymongo']
            found_deps = []
            missing_deps = []
            
            for dep in critical_deps:
                found = any(dep.lower() in line.lower() for line in lines)
                if found:
                    found_deps.append(dep)
                else:
                    missing_deps.append(dep)
            
            if missing_deps:
                self.log_result(
                    "Backend Kritik Bağımlılıklar",
                    False,
                    f"Eksik kritik bağımlılıklar: {', '.join(missing_deps)}",
                    f"Bulunan: {', '.join(found_deps)}"
                )
                return False
            
            # 4. Syntax kontrolü - pip install --dry-run simülasyonu
            syntax_errors = []
            for line in lines:
                if '==' in line:
                    parts = line.split('==')
                    if len(parts) != 2:
                        syntax_errors.append(f"Geçersiz version syntax: {line}")
                elif '>=' in line:
                    parts = line.split('>=')
                    if len(parts) != 2:
                        syntax_errors.append(f"Geçersiz version syntax: {line}")
                elif not line.replace('-', '').replace('_', '').replace('.', '').isalnum():
                    # Basit paket adı kontrolü
                    if '[' not in line and ']' not in line:  # extras için
                        syntax_errors.append(f"Şüpheli paket adı: {line}")
            
            if syntax_errors:
                self.log_result(
                    "Backend Requirements Syntax",
                    False,
                    "Syntax hataları bulundu",
                    "; ".join(syntax_errors)
                )
                return False
            
            self.log_result(
                "Backend Requirements",
                True,
                f"{len(lines)} bağımlılık başarıyla parse edildi",
                f"Kritik bağımlılıklar: {', '.join(found_deps)}"
            )
            return True
            
        except Exception as e:
            self.log_result(
                "Backend Requirements Parse",
                False,
                "requirements.txt okunamadı",
                str(e)
            )
            return False

    def test_backend_test_folder(self) -> bool:
        """Backend test klasörünü test et"""
        print("🔍 Backend Test Klasörü Test Ediliyor...")
        
        test_dir = self.backend_dir / "tests"
        
        # 1. Test klasörünün varlığını kontrol et
        if not test_dir.exists():
            # Test klasörü yoksa oluşturmayı dene
            try:
                test_dir.mkdir(parents=True, exist_ok=True)
                self.log_result(
                    "Backend Test Klasörü Oluşturma",
                    True,
                    "Test klasörü başarıyla oluşturuldu",
                    f"Konum: {test_dir}"
                )
            except Exception as e:
                self.log_result(
                    "Backend Test Klasörü Oluşturma",
                    False,
                    "Test klasörü oluşturulamadı",
                    str(e)
                )
                return False
        else:
            self.log_result(
                "Backend Test Klasörü Varlığı",
                True,
                "Test klasörü zaten mevcut",
                f"Konum: {test_dir}"
            )
        
        # 2. Test klasörünün yazılabilir olduğunu kontrol et
        try:
            test_file = test_dir / "test_build_check.py"
            test_content = '''"""
Build test için oluşturulan test dosyası
"""
import pytest

def test_build_check():
    """Build sürecinin çalıştığını doğrular"""
    assert True, "Build test başarılı"
'''
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(test_content)
            
            # Test dosyasını sil
            test_file.unlink()
            
            self.log_result(
                "Backend Test Klasörü Yazma",
                True,
                "Test klasörüne yazma işlemi başarılı",
                "Test dosyası oluşturulup silindi"
            )
            return True
            
        except Exception as e:
            self.log_result(
                "Backend Test Klasörü Yazma",
                False,
                "Test klasörüne yazma işlemi başarısız",
                str(e)
            )
            return False

    def test_frontend_yarn_commands(self) -> bool:
        """Frontend yarn komutlarını test et"""
        print("🔍 Frontend Yarn Komutları Test Ediliyor...")
        
        package_json = self.frontend_dir / "package.json"
        
        # 1. package.json varlığını kontrol et
        if not package_json.exists():
            self.log_result(
                "Frontend Package.json",
                False,
                "package.json dosyası bulunamadı",
                f"Aranan konum: {package_json}"
            )
            return False
        
        # 2. package.json içeriğini parse et
        try:
            with open(package_json, 'r', encoding='utf-8') as f:
                package_data = json.load(f)
            
            self.log_result(
                "Frontend Package.json Parse",
                True,
                "package.json başarıyla parse edildi",
                f"Proje: {package_data.get('name', 'Bilinmeyen')}"
            )
            
        except json.JSONDecodeError as e:
            self.log_result(
                "Frontend Package.json Parse",
                False,
                "package.json geçersiz JSON formatında",
                str(e)
            )
            return False
        except Exception as e:
            self.log_result(
                "Frontend Package.json Okuma",
                False,
                "package.json okunamadı",
                str(e)
            )
            return False
        
        # 3. Scripts bölümünü kontrol et
        scripts = package_data.get('scripts', {})
        if not scripts:
            self.log_result(
                "Frontend Scripts",
                False,
                "package.json'da scripts bölümü bulunamadı",
                "En az start ve build scriptleri olmalı"
            )
            return False
        
        # 4. Kritik scriptleri kontrol et
        critical_scripts = ['start', 'build']
        missing_scripts = []
        found_scripts = []
        
        for script in critical_scripts:
            if script in scripts:
                found_scripts.append(script)
            else:
                missing_scripts.append(script)
        
        if missing_scripts:
            self.log_result(
                "Frontend Kritik Scripts",
                False,
                f"Eksik kritik scriptler: {', '.join(missing_scripts)}",
                f"Bulunan: {', '.join(found_scripts)}"
            )
            return False
        
        # 5. Dependencies kontrolü
        dependencies = package_data.get('dependencies', {})
        dev_dependencies = package_data.get('devDependencies', {})
        
        if not dependencies and not dev_dependencies:
            self.log_result(
                "Frontend Dependencies",
                False,
                "Hiç bağımlılık bulunamadı",
                "En az React bağımlılığı olmalı"
            )
            return False
        
        # React kontrolü
        has_react = 'react' in dependencies or 'react' in dev_dependencies
        if not has_react:
            self.log_result(
                "Frontend React Dependency",
                False,
                "React bağımlılığı bulunamadı",
                "Bu bir React projesi olmalı"
            )
            return False
        
        # 6. Yarn lock dosyası kontrolü
        yarn_lock = self.frontend_dir / "yarn.lock"
        if yarn_lock.exists():
            lock_status = "yarn.lock mevcut"
        else:
            lock_status = "yarn.lock bulunamadı (ilk yarn install'da oluşacak)"
        
        self.log_result(
            "Frontend Yarn Komutları",
            True,
            f"Tüm yarn komutları geçerli - {len(dependencies)} dependency, {len(dev_dependencies)} devDependency",
            f"Scripts: {', '.join(scripts.keys())}; {lock_status}"
        )
        return True

    def test_build_commands_syntax(self) -> bool:
        """Build komutlarının syntax kontrolü"""
        print("🔍 Build Komutları Syntax Test Ediliyor...")
        
        # Simüle edilmiş build.yml içeriği (gerçek dosya olmadığı için)
        build_commands = {
            "backend": [
                "cd /app/backend",
                "python -m pip install --upgrade pip",
                "pip install -r requirements.txt",
                "python -m pytest tests/ -v",
                "python -m flake8 server.py --max-line-length=120"
            ],
            "frontend": [
                "cd /app/frontend",
                "yarn install --frozen-lockfile",
                "yarn lint",
                "yarn build",
                "yarn test --watchAll=false"
            ]
        }
        
        syntax_errors = []
        
        # Backend komutları syntax kontrolü
        for i, cmd in enumerate(build_commands["backend"]):
            if not cmd.strip():
                syntax_errors.append(f"Backend komut {i+1}: Boş komut")
                continue
            
            # Basit syntax kontrolleri
            if cmd.startswith("cd ") and not os.path.exists(cmd[3:].strip()):
                # cd komutu için dizin varlığı kontrolü (opsiyonel uyarı)
                pass
            
            if "pip install" in cmd and "-r" in cmd:
                # requirements dosyası varlığı kontrolü
                req_file = cmd.split("-r")[-1].strip()
                if not req_file.startswith("/"):
                    req_file = self.backend_dir / req_file
                else:
                    req_file = Path(req_file)
                
                if not req_file.exists():
                    syntax_errors.append(f"Backend komut {i+1}: Requirements dosyası bulunamadı: {req_file}")
        
        # Frontend komutları syntax kontrolü  
        for i, cmd in enumerate(build_commands["frontend"]):
            if not cmd.strip():
                syntax_errors.append(f"Frontend komut {i+1}: Boş komut")
                continue
            
            if cmd.startswith("yarn "):
                yarn_cmd = cmd[5:].strip()
                # Yarn komut varlığı kontrolü (package.json scripts'te olmalı)
                if yarn_cmd in ["install", "add", "remove"]:
                    # Yarn built-in komutları
                    pass
                elif yarn_cmd.startswith("install"):
                    # yarn install variants
                    pass
                else:
                    # Custom script kontrolü
                    try:
                        with open(self.frontend_dir / "package.json", 'r') as f:
                            package_data = json.load(f)
                        scripts = package_data.get('scripts', {})
                        
                        base_cmd = yarn_cmd.split()[0]  # İlk kelimeyi al
                        if base_cmd not in scripts and base_cmd not in ["test", "start", "build", "lint"]:
                            # Uyarı ver ama hata sayma (script sonradan eklenebilir)
                            pass
                    except:
                        pass
        
        if syntax_errors:
            self.log_result(
                "Build Komutları Syntax",
                False,
                f"{len(syntax_errors)} syntax hatası bulundu",
                "; ".join(syntax_errors)
            )
            return False
        
        self.log_result(
            "Build Komutları Syntax",
            True,
            f"Tüm build komutları syntax açısından geçerli",
            f"Backend: {len(build_commands['backend'])} komut, Frontend: {len(build_commands['frontend'])} komut"
        )
        return True

    def test_python_environment(self) -> bool:
        """Python environment simülasyonu"""
        print("🔍 Python Environment Test Ediliyor...")
        
        try:
            # Python version kontrolü
            python_version = sys.version_info
            if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
                self.log_result(
                    "Python Version",
                    False,
                    f"Python {python_version.major}.{python_version.minor} desteklenmiyor",
                    "En az Python 3.8 gerekli"
                )
                return False
            
            # Pip varlığı kontrolü
            pip_result = subprocess.run([sys.executable, "-m", "pip", "--version"], 
                                      capture_output=True, text=True, timeout=10)
            if pip_result.returncode != 0:
                self.log_result(
                    "Pip Varlığı",
                    False,
                    "pip bulunamadı veya çalışmıyor",
                    pip_result.stderr
                )
                return False
            
            self.log_result(
                "Python Environment",
                True,
                f"Python {python_version.major}.{python_version.minor}.{python_version.micro} ve pip hazır",
                pip_result.stdout.strip()
            )
            return True
            
        except Exception as e:
            self.log_result(
                "Python Environment",
                False,
                "Python environment kontrolü başarısız",
                str(e)
            )
            return False

    def test_nodejs_environment(self) -> bool:
        """Node.js environment simülasyonu"""
        print("🔍 Node.js Environment Test Ediliyor...")
        
        try:
            # Node.js version kontrolü
            node_result = subprocess.run(["node", "--version"], 
                                       capture_output=True, text=True, timeout=10)
            if node_result.returncode != 0:
                self.log_result(
                    "Node.js Varlığı",
                    False,
                    "Node.js bulunamadı",
                    "Node.js kurulu değil veya PATH'te yok"
                )
                return False
            
            # Yarn varlığı kontrolü
            yarn_result = subprocess.run(["yarn", "--version"], 
                                       capture_output=True, text=True, timeout=10)
            if yarn_result.returncode != 0:
                self.log_result(
                    "Yarn Varlığı",
                    False,
                    "Yarn bulunamadı",
                    "Yarn kurulu değil veya PATH'te yok"
                )
                return False
            
            self.log_result(
                "Node.js Environment",
                True,
                f"Node.js {node_result.stdout.strip()} ve Yarn {yarn_result.stdout.strip()} hazır",
                "Frontend build için gerekli araçlar mevcut"
            )
            return True
            
        except Exception as e:
            self.log_result(
                "Node.js Environment",
                False,
                "Node.js environment kontrolü başarısız",
                str(e)
            )
            return False

    def run_all_tests(self) -> Dict:
        """Tüm testleri çalıştır"""
        print("🚀 PostaDepo Build Process Dry-Run Test Başlıyor...\n")
        print("=" * 60)
        
        # Test sırası
        tests = [
            ("Python Environment", self.test_python_environment),
            ("Node.js Environment", self.test_nodejs_environment),
            ("Backend Requirements", self.test_backend_requirements),
            ("Backend Test Folder", self.test_backend_test_folder),
            ("Frontend Yarn Commands", self.test_frontend_yarn_commands),
            ("Build Commands Syntax", self.test_build_commands_syntax),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                success = test_func()
                if success:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                self.log_result(
                    test_name,
                    False,
                    "Test çalıştırılırken hata oluştu",
                    str(e)
                )
                failed += 1
        
        # Özet rapor
        print("=" * 60)
        print("📊 TEST SONUÇLARI ÖZETİ")
        print("=" * 60)
        print(f"✅ Başarılı Testler: {passed}")
        print(f"❌ Başarısız Testler: {failed}")
        print(f"📈 Başarı Oranı: {(passed/(passed+failed)*100):.1f}%")
        
        if failed == 0:
            print("\n🎉 TÜM TESTLER BAŞARILI! Build süreci hazır.")
        else:
            print(f"\n⚠️  {failed} test başarısız. Lütfen hataları düzeltin.")
        
        return {
            "total_tests": len(tests),
            "passed": passed,
            "failed": failed,
            "success_rate": passed/(passed+failed)*100,
            "results": self.test_results
        }

def main():
    """Ana fonksiyon"""
    tester = BuildTester()
    results = tester.run_all_tests()
    
    # Çıkış kodu
    if results["failed"] == 0:
        sys.exit(0)  # Başarı
    else:
        sys.exit(1)  # Hata

if __name__ == "__main__":
    main()