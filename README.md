# PostaDepo

<p align="center">
    <img width="450" alt="PostaDepo Logo" src="https://github.com/mertenesakarsu-ai/postadepo/blob/main/logo_ready.png" /><br />
    <a href="https://github.com/mertenesakarsu-ai/postadepo/releases"><img src="https://img.shields.io/github/release/mertenesakarsu-ai/postadepo" alt="Latest Release"></a>
    <a href="https://github.com/mertenesakarsu-ai/postadepo/actions"><img src="https://github.com/mertenesakarsu-ai/postadepo/actions/workflows/build.yml/badge.svg" alt="Build Status"></a>
</p>

<p align="center"><strong>PostaDepo</strong> is a modern web application that allows users to easily backup their<br /> <strong>Outlook emails</strong>, export them in different formats, and restore them when needed.<br /> The project includes a <strong>React.js frontend</strong> and a <strong>Node.js/Express backend</strong>. <br />Some backup and format conversion processes use <strong>Python</strong> scripts.</p>

---

## Key Features

* **Email Backup** – Backup your Outlook emails in `.pst` and `.ost` formats.
* **Import/Export** – Easily restore created backups.
  - ZIP Format (.zip) – All emails packaged together.
  - EML Format (.eml) – Individual email files.
  - JSON Format (.json) – Email contents structured in JSON.
* **Secure Storage** – Backups are stored securely; access is protected with JWT.
* **Modern, Responsive Interface** – User-friendly design with React + Tailwind.
* **OAuth & Outlook Integration** – Secure connection and authorization with Outlook accounts.

---

## Technologies

### Backend

* **Node.js**: To run server-side applications.
* **Express.js**: HTTP server and API route management.
* **MongoDB**: Database.
* **bcrypt**: Password hashing operations.
* **Python** – For processing email backups and converting them into different formats.

### Frontend

* **React.js**: To build the user interface.
* **TailwindCSS**: Styling and responsive design.
* **Vanilla JS**: Form transitions, pop-ups, and other dynamic operations.

---

## Quick Setup

**Requirements**

* Node.js (v16 or higher)
* Python (v3.10 or higher)
* MongoDB (local or Atlas)

**Steps**

```bash
# 1. Clone the repository
git clone https://github.com/mertenesakarsu-ai/postadepo.git

# 2. Install backend dependencies
cd postadepo/backend
npm install

# 3. Install frontend dependencies (in a separate terminal)
cd ../frontend
npm install

# 4. Install Python dependencies
cd ../backend
pip install -r requirements.txt

# 5. Start the backend
npm start

# 6. Start the frontend
cd ../frontend
npm start
```

---

## Environment Variables (example)

Define the following environment variables in the `.env` file for backend:

```
PORT=3000
MONGODB_URI=mongodb+srv://<username>:<password>@cluster0.mongodb.net/postadepo
JWT_SECRET=çok-gizli-bir-anahtar
OUTLOOK_CLIENT_ID=<azure-app-client-id>
OUTLOOK_CLIENT_SECRET=<azure-app-client-secret>
OUTLOOK_REDIRECT_URI=https://yourdomain.com/api/auth/callback
```

> [!WARNING] 
>  Never include real client secrets or Mongo connection strings in a public repository.

---

## Workflow (user side)

1. User connects their Azure/Outlook account via OAuth.
2. Backend retrieves emails using the necessary API and Graph access and stores backups on the server.
3. User can download or restore backups from the dashboard.

---

## Author

This project was developed                         
<a href="https://github.com/mertenesakarsu"><img width="100" height="100" alt="PostaDepo Logo" src="https://github.com/user-attachments/assets/80b54475-23c7-406b-a265-8e34f990f09a" /></a>
by [**@mertenesakarsu**](https://github.com/mertenesakarsu).  

---

## Contributing

Contributions are welcome:

Fork the repository.

Create a new branch: git checkout -b feature/your-feature

Commit your changes.

Push the branch and open a PR.

---

## License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE.md) file for details.

