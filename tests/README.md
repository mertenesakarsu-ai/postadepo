# PostaDepo Test Suite

Bu klasör genel integration testleri için kullanılır.

## Test Yapısı
- `/backend/tests/` - Backend unit testleri
- `/frontend/src/__tests__/` - Frontend component testleri  
- `/tests/` - Integration ve end-to-end testler

## Çalıştırma
```bash
# Backend testleri
cd backend && python -m pytest tests/

# Frontend testleri  
cd frontend && yarn test

# Integration testleri
python -m pytest tests/
```