# PostaDepo

<p align="center">
    <img width="450" alt="PostaDepo Logo" src="https://github.com/mertenesakarsu-ai/postadepo/blob/main/readmelogo.png" /><br />
    <a href="https://github.com/mertenesakarsu-ai/postadepo/releases"><img src="https://img.shields.io/github/release/mertenesakarsu-ai/postadepo" alt="Latest Release"></a>
    <a href="https://github.com/mertenesakarsu-ai/postadepo/actions"><img src="https://github.com/mertenesakarsu-ai/postadepo/actions/workflows/build.yml/badge.svg" alt="Build Status"></a>
</p>

PostaDepo, kullanıcıların Outlook maillerini kolayca yedeklemelerine ve gerektiğinde geri yüklemelerine olanak tanıyan modern bir web uygulamasıdır. Proje, React.js ile hazırlanmış bir frontend ve Node.js/Express tabanlı bir backend içerir.

---

## Öne Çıkan Özellikler

* **Mail Yedekleme** – Outlook maillerinizi `.pst` ve `.ost` formatlarında yedekleyin.
* **İçe/Dışa Aktarım** – Oluşturduğunuz yedekleri kolayca geri yükleyin.
* **Güvenli Saklama** – Yedekler güvenli şekilde depolanır; erişim JWT ile korunur.
* **Modern, Responsive Arayüz** – React + Tailwind ile kullanıcı dostu tasarım.
* **OAuth & Outlook Entegrasyonu** – Outlook hesaplarıyla güvenli bağlantı ve yetkilendirme.

---

## Teknolojiler

### Backend

* **Node.js**: Sunucu tarafı uygulama çalıştırmak için.
* **Express.js**: HTTP server ve API route yönetimi.
* **MongoDB**: Veritabanı.
* **bcrypt**: Şifre hashleme işlemleri.

### Frontend

* **React.js**: Kullanıcı arayüzü geliştirmek için.
* **TailwindCSS**: Stil ve responsive tasarım.
* **Vanilla JS**: Form geçişleri, pop-up gösterimleri ve diğer dinamik işlemler.

---

## Hızlı Kurulum

**Gereksinimler**

* Node.js (v16 veya üzeri)
* MongoDB (yerel ya da Atlas)

**Adımlar**

```bash
# 1. Depoyu klonlayın
git clone https://github.com/mertenesakarsu-ai/postadepo.git

# 2. Backend bağımlılıklarını yükleyin
cd postadepo/backend
npm install

# 3. Frontend bağımlılıklarını yükleyin (ayrı terminal)
cd ../frontend
npm install

# 4. Backend'i başlatın (backend klasöründe)
npm start

# 5. Frontend'i başlatın (frontend klasöründe)
npm start
```

---

## Ortam Değişkenleri (örnek)

Backend çalışması için aşağıdaki ortam değişkenlerini `.env` dosyasında tanımlayın:

```
PORT=3000
MONGODB_URI=mongodb+srv://<username>:<password>@cluster0.mongodb.net/postadepo
JWT_SECRET=çok-gizli-bir-anahtar
OUTLOOK_CLIENT_ID=<azure-app-client-id>
OUTLOOK_CLIENT_SECRET=<azure-app-client-secret>
OUTLOOK_REDIRECT_URI=https://yourdomain.com/api/auth/callback
```

> Not: Gerçek client secret ve Mongo bağlantı stringlerini asla herkese açık repoya eklemeyin.

---

## Çalışma Akışları (kullanıcı tarafı)

1. Kullanıcı Azure/Outlook hesabını OAuth ile bağlar.
2. Backend gerekli API ve Graph erişimini kullanarak e-postaları alır ve sunucuya yedekler.
3. Kullanıcı dashboard’dan yedekleri indirebilir veya geri yükleyebilir.

---

## Projeyi Yapan

Bu proje [@mertenesakarsu](https://github.com/mertenesakarsu) tarafından geliştirilmiştir.

---

## Katkıda Bulunma

Katkılar memnuniyetle kabul edilir:

1. Repo’yu fork’layın.
2. Yeni branch oluşturun: `git checkout -b feature/isim`
3. Değişiklikleri commit edin.
4. Branch’i push edin ve PR açın.

---

## Lisans

Bu proje MIT Lisansı ile lisanslanmıştır.

*README, repository içeriğine göre güncellenmiştir ve frontend/backend teknolojileri doğru şekilde belirtilmiştir.*
