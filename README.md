# 📝 Notivora  
### *Feed your mind.*

**Notivora** is an AI-powered note-taking web application currently under development.  
It helps users capture and better understand information by automatically generating summaries and flashcards from their notes.  
Users can review material using a quiz mode, where AI provides real-time feedback on their answers.  
The goal is to create an interactive, intelligent learning experience that evolves with the user.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-Web_Framework-lightgrey?logo=flask)
![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-336791?logo=postgresql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/ORM-SQLAlchemy-red?logo=sqlalchemy)
![AI Powered](https://img.shields.io/badge/AI-Powered-brightgreen?logo=openai)
![WIP](https://img.shields.io/badge/Status-In_Development-orange?logo=github)

> ⚠️ This project is a work in progress. Core features are being actively developed and tested.

---

# 🚀 Features (Work in Progress)

- **Automatic Summaries**: Generate AI-powered summaries from your notes.
- **Flashcards**: Create flashcards based on the summaries.
- **Quiz Mode**: Test your knowledge with an interactive quiz that offers AI feedback.
- **User Management**: Secure login and note management.
- **Database Integration**: Store notes and flashcards in a relational database.

# 🛠️ Technology Stack

- **Backend**: Flask – Lightweight Python web framework.
- **Database**: SQLAlchemy – Python ORM.
- **Authentication**: Flask-Login – User session management.
- **AI Integration**: OpenAI API – For generating summaries and feedback.
- **Database**: SQLite (development) or PostgreSQL (production).

---

## ⚙️ Installation Guide

### 1. Clone the repository

```bash
git clone https://github.com/ChristianMatuszak/Notivora.git
cd Notivora
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

🔐 Environment Configuration

To run the project, create a `.env` file in the root directory based on the provided `.env.template`.

Here's a description of the required environment variables:

```env
# OpenAI API Key for Access to OpenAI Systems
OPENAI_API_KEY=your_openai_api_key_here

# OpenAI API Base URL (Default: https://api.openai.com/v1)
OPENAI_API_BASE=https://api.openai.com/v1

# Secret Key for Flask Sessions
SECRET_KEY=your_secret_key_here

# Database URL (example: sqlite:///./app.sqlite)
DATABASE_URL=your_database_url_here
```

```bash
cp .env.template .env
```

Edit `.env` and add your OpenAI API keys and other required environment variables.

### 4. Run the application

```bash
python app.py
```

The app will be accessible at `http://localhost:5000`.
