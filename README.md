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

## 1. Prerequisites
- Python 3.10 or higher
- pip (Python Package Manager)
- SQLite or PostgreSQL
- OpenAI API Key


## 2. Installation Guide ⚙️
   
 ### 1. Clone the repository
 ```bash
 git clone https://github.com/ChristianMatuszak/Notivora.git
 cd Notivora
 ```
 
 ### 2. Create virtual environment
 ```bash
 python -m venv venv
 source venv/bin/activate  # Linux/Mac
 # or
 venv\Scripts\activate     # Windows
 ```
 
 ### 3. Install dependencies
 ```bash
 pip install -r requirements.txt
 ```

 ### 4. Configure environment variables
  
  🔐 Environment Configuration
  
  To run the project, create a `.env` file in the root directory based on the provided `.env.template`.
  
  Here's a description of the required environment variables:
  
  ```env
  # OpenAI
  OPENAI_API_KEY=your_openai_api_key_here
  OPENAI_API_BASE=https://api.openai.com/v1
    
  # Flask / App
  SECRET_KEY=your_secret_key_here
  APP_ENV=development
    
  # Database
  DATABASE_URL=your_database_url_here
    
  # Email (SMTP)
  SMTP_SERVER=smtp.example.com
  SMTP_PORT=587
  SMTP_USERNAME=name
  SMTP_PASSWORD=password
  FROM_EMAIL=user@email.com
    
  # JWT / Auth
  JWT_SECRET_KEY=your_jwt_secret_key
  ALGORITHM=HS256
  EXPIRES_MINUTES=30
  ```
  
  ```bash
  cp .env.template .env
  ```
  
  Edit `.env` and add your OpenAI API keys and other required environment variables.

---

## 3. **API Documentation**
   
   ### User Management
   - `POST /user/create-user` - Create new user account
   - `POST /user/login` - Authenticate user
   - `GET /user/get-user/<id>` - Get user details
   - `PUT /user/update-user/<id>` - Update user information
   - `DELETE /user/delete-user/<id>` - Delete user account
   
   ### Notes Management
   - `POST /note/store-note` - Create new note
   - `GET /note/get-notes` - Get all user notes
   - `GET /note/get-note/<id>` - Get specific note
   - `PUT /note/update-note/<id>` - Update note
   - `DELETE /note/delete-note/<id>` - Delete note
   
   ### AI Features
   - `POST /llm/generate-summary/<note_id>` - Generate AI summary
   - `POST /llm/generate-flashcard/<note_id>` - Create flashcards
   - `POST /llm/check-answer` - Evaluate quiz answers

   ### Quiz Features
   - `POST /start/<note_id>` - Start quiz for a flashcard set
   - `GET /progress/<note_id>` - Get quiz progress
--- 

## 4. Project Structure

   ```
  src/
  ├── app/
  │   ├── __init__.py              # Flask App Factory
  │   ├── main.py                  # Main entry point
  │   ├── routes/                  # API routes
  │       ├── user.py              # User management endpoints
  │       ├── note.py              # Note management endpoints
  │       ├── llm.py               # AI/LLM integration endpoints
  │       ├── quiz.py              # Quiz endpoints
  │       └── ping.py              # Health check endpoint
  │   └── services/                # Business logic
  │       ├── flashcard_Service.py # Flashcard business logic
  │       ├── note_service.py      # Note business logic
  │       ├── llm_service.py       # AI/LLM business logic
  │       ├── quiz_service.py      # Quiz business logic
  │       └── user_service.py      # User busniess logic
  ├── config/
      └── config.py                # Configuration settings
  ├── data/
  │   ├── db.py                    # Database connection setup
  │   └── models/                  # SQLAlchemy models
  │       ├── init.py              # Initialize models
  │       ├── users.py             # User model
  │       ├── notes.py             # Note model
  │       ├── flashcards.py        # Flashcard model
  │       ├── quizzes.py           # Quiz model
  │       └── scores.py            # Score model
  ├── utils/                       # Utility functions
  |   ├── constants.py             # Centralized error and status messages
  │   ├── llm_api.py               # OpenAI API integration
  │   ├── email.py                 # Email functionality
  │   └── token.py                 # Token management
  └── tests/                       # Test files from endpoints to workflow
  ```

---

## 5. Troubleshooting

   ### OpenAI API Errors
   - Ensure your API key is valid and has sufficient credits
   - Check if the API base URL is correct
   - Verify your OpenAI account status
   
   ### Database Errors
   - Delete the database file and restart the application
   - Check the DATABASE_URL in your .env file
   - Ensure proper database permissions
   
   ### Authentication Issues
   - Clear browser cookies and try again
   - Check if Flask-Login is properly configured
   - Verify session management setup

---

## 6. Usage Examples

   ## Usage Examples
   
   ### Creating a User
   ```bash
   curl -X POST http://localhost:5000/user/create-user \
     -H "Content-Type: application/json" \
     -d '{"username": "testuser", "email": "test@example.com", "password": "securepassword"}'
   ```
   
   ### Creating a Note
   ```bash
   curl -X POST http://localhost:5000/note/store-note \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <your-session-token>" \
     -d '{"title": "My Note", "content": "This is my note content"}'
   ```


## 7. Run the application

```bash
python app.py
```

The app will be accessible at `http://localhost:5000`.
