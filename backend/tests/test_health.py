"""
Basit health check testleri
"""
import sys
import os

# Add parent directory to Python path to import server
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_server_imports():
    """Test that server module can be imported"""
    try:
        import server
        assert hasattr(server, 'app')
        print("✅ Server module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import server: {e}")
        raise

def test_fastapi_app_creation():
    """Test that FastAPI app is created properly"""
    try:
        import server
        from fastapi import FastAPI
        
        assert isinstance(server.app, FastAPI)
        print("✅ FastAPI app created successfully")
    except Exception as e:
        print(f"❌ Failed to create FastAPI app: {e}")
        raise

if __name__ == "__main__":
    test_server_imports()
    test_fastapi_app_creation()
    print("✅ All health checks passed!")