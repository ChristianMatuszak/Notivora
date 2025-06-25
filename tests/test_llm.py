import pytest
from unittest.mock import patch

from src.app import create_app
from src.data.db import Base, get_engine
from src.data.models.notes import Note
from src.data.models.users import User

def reset_database(database_url: str):
    """
    Resets the database by dropping all existing tables and recreating them.

    This function is typically used before tests to ensure a clean and consistent
    database state.

    Args:
        database_url (str): The URL of the database to reset.
    """

    engine = get_engine(database_url)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    engine.dispose()

reset_database("sqlite:///./test.sqlite")

@pytest.fixture(scope="module")
def test_app():
    """
    Pytest fixture that initializes and provides a Flask application instance
    configured for testing.

    Pushes the app context so that Flask globals (like `current_app`) are accessible.
    Cleans up the context after tests are done.

    Yields:
        Flask: The initialized Flask application.
    """

    app = create_app(database_url="sqlite:///./test.sqlite", testing=True)
    ctx = app.app_context()
    ctx.push()
    yield app
    ctx.pop()

@pytest.fixture(scope="module")
def test_client(test_app):
    """
    Pytest fixture that provides a Flask test client for making HTTP requests
    to the test application.

    Relies on the `test_app` fixture to create the application context.

    Yields:
        FlaskClient: A client to simulate HTTP requests in tests.
    """

    return test_app.test_client()

@pytest.fixture(scope="module")
def test_engine():
    """
    Pytest fixture that sets up and tears down a test database engine.

    Drops all existing tables, recreates the schema for a clean test environment,
    and disposes the engine after tests complete.

    Yields:
        Engine: SQLAlchemy engine connected to the SQLite test database.
    """

    engine = get_engine("sqlite:///./test.sqlite")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()

@pytest.fixture()
def session(test_engine):
    """
    Pytest fixture that creates and manages a database session for tests.

    Ensures that any changes made to the database during a test are rolled back
    after the test completes to preserve isolation.

    Yields:
        Session: SQLAlchemy session object for performing database operations.
    """

    from src.data.db import get_session_local
    SessionLocal = get_session_local(test_engine)
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()

@pytest.fixture()
def create_user(session):
    """
    Pytest fixture that creates a test user in the database.

    Commits the user before yielding, and ensures the user is removed after the test.

    Yields:
        User: The created User object available for use in tests.
    """

    user = User(username="testuser", email="testuser@example.com")
    user.set_password("testpassword")
    session.add(user)
    session.commit()
    yield user
    session.delete(user)
    session.commit()

@pytest.fixture()
def login_auth_client(test_client, create_user):
    """
    Pytest fixture that logs in a previously created test user and returns
    an authenticated test client.

    Performs a POST request to the login endpoint and asserts successful authentication.

    Yields:
        FlaskClient: A test client with an active login session.
    """

    with test_client:
        response = test_client.post('/user/login', json={
            "username": "testuser",
            "password": "testpassword"
        })
        assert response.status_code == 200
        yield test_client

@pytest.fixture()
def create_note(session, create_user):
    """
    Pytest fixture that creates a test note associated with the created test user.

    The note is committed before yielding, and deleted after the test finishes.

    Yields:
        Note: The created Note object ready for use in test functions.
    """

    note = Note(title="AI Note", original="This is original content.", user_id=create_user.id)
    session.add(note)
    session.commit()
    yield note
    session.delete(note)
    session.commit()

def test_generate_summary(login_auth_client, create_note):
    """
    Tests the `/llm/generate-summary/<note_id>` endpoint for generating a note summary using an LLM.

    Mocks the LLM summary generation to return a predefined summary and language.
    Asserts that the endpoint returns a 200 status and includes the expected summary text.

    Args:
        login_auth_client (FlaskClient): Authenticated client with an active user session.
        create_note (Note): The note for which the summary will be generated.
    """

    with patch("src.app.routes.llm.generate_summary_from_note") as mock_summary:
        mock_summary.return_value = ("This is a summary.", "en")
        response = login_auth_client.post(f"/llm/generate-summary/{create_note.note_id}")
        assert response.status_code == 200
        data = response.get_json()
        assert "ai_summary" in data
        assert data["ai_summary"] == "This is a summary."

def test_generate_flashcards(login_auth_client, create_note, session):
    """
    Tests the `/llm/generate-flashcard/<note_id>` endpoint for generating flashcards from a summary.

    Updates the test note with a mock summary and language. Mocks the flashcard generation logic
    to return predefined cards. Asserts successful response and message.

    Args:
        login_auth_client (FlaskClient): Authenticated client with user session.
        create_note (Note): Note object with predefined summary and language.
        session (Session): SQLAlchemy session used to commit changes to the note.
    """

    create_note.ai_summary = "This is a summary."
    create_note.language = "en"
    session.commit()
    with patch("src.app.routes.llm.generate_flashcards_from_summary", return_value=[
        {"question": "What is this?", "answer": "A test flashcard."}
    ]):
        response = login_auth_client.post(f"/llm/generate-flashcard/{create_note.note_id}")
        assert response.status_code == 201
        data = response.get_json()
        assert data["message"] == "Flashcards generated successfully"

def test_check_answer(login_auth_client):
    """
    Tests the `/llm/check-answer` endpoint which uses an LLM to evaluate a user's answer.

    Mocks the answer-checking logic and posts a test payload. Verifies the correct
    result is returned from the mocked LLM logic.

    Args:
        login_auth_client (FlaskClient): Authenticated client with user session.
    """

    payload = {
        "question": "What is AI?",
        "correct_answer": "Artificial Intelligence",
        "user_answer": "AI",
        "language": "en"
    }
    with patch("src.app.routes.llm.check_user_answer_with_llm") as mock_check:
        mock_check.return_value = {"result": "Close enough!"}
        response = login_auth_client.post("/llm/check-answer", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert "result" in data
        assert data["result"] == "Close enough!"
