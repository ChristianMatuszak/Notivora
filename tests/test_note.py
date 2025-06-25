import pytest

from src.app import create_app
from src.data.db import Base, get_engine
from src.data.models.notes import Note
from src.data.models.users import User

@pytest.fixture(scope="module")
def test_app():
    """
    Pytest fixture that creates and configures a Flask application instance
    for testing purposes.

    This fixture sets up the Flask application with a SQLite test database and
    enables the testing configuration. The application context is pushed
    before yielding the app so that other parts of the test suite can operate
    within the Flask application context. Once the tests using this fixture
    are complete, the application context is popped to clean up resources.

    Returns:
        Flask: A configured Flask application instance with testing mode enabled.
    """

    app = create_app(database_url="sqlite:///./test.sqlite", testing=True)
    ctx = app.app_context()
    ctx.push()
    yield app
    ctx.pop()

@pytest.fixture(scope="module")
def test_client(test_app):
    """
    Pytest fixture that provides a test client for the Flask application.

    Uses the `test_app` fixture to retrieve the application and returns its test client,
    which can be used to simulate HTTP requests to the application routes.

    Args:
        test_app (Flask): The test application instance.

    Returns:
        FlaskClient: A client to send test requests to the Flask app.
    """

    return test_app.test_client()

@pytest.fixture(scope="module")
def test_engine():
    """
    Pytest fixture that sets up and tears down the database engine for testing.

    Creates all tables defined in SQLAlchemy models on a SQLite test database before the test run.
    After all tests using this fixture are complete, it drops all tables to clean up.

    Yields:
        Engine: The SQLAlchemy engine connected to the test database.
    """

    engine = get_engine("sqlite:///./test.sqlite")
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture()
def session(test_engine):
    """
    Pytest fixture that provides a SQLAlchemy session bound to the test database.

    This fixture is responsible for creating a transactional scope for each test,
    ensuring any database changes are rolled back after the test completes to maintain isolation.

    Args:
        test_engine (Engine): The SQLAlchemy engine for the test database.

    Yields:
        Session: A SQLAlchemy session object for interacting with the database.
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

    The user is created with a predefined username, email, and password for authentication tests.
    The user is removed from the database after the test completes.

    Args:
        session (Session): A SQLAlchemy session for database interaction.

    Yields:
        User: The newly created user instance.
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
    Pytest fixture that logs in the test user and returns an authenticated test client.

    Performs a login operation using the test client's POST method and asserts successful authentication.
    The authenticated client can then be used to test protected endpoints.

    Args:
        test_client (FlaskClient): The test client instance.
        create_user (User): The test user created for authentication.

    Yields:
        FlaskClient: The authenticated test client.
    """

    with test_client:
        response = test_client.post('/user/login', json={
            "username": "testuser",
            "password": "testpassword"
        })
        assert response.status_code == 200
        yield test_client

def test_store_note(login_auth_client, session, create_user):
    """
    Tests the endpoint for creating (storing) a new note.

    Sends a POST request with a note title and content. Asserts that the response is successful
    and that a `note_id` is returned in the response payload.

    Args:
        login_auth_client (FlaskClient): Authenticated client.
        session (Session): SQLAlchemy session.
        create_user (User): The user associated with the note.
    """

    response = login_auth_client.post('/note/store-note', json={
        "title": "Test Note",
        "content": "This is the original content."
    })
    assert response.status_code == 201
    data = response.get_json()
    assert "note_id" in data

def test_get_notes(login_auth_client, session, create_user):
    """
    Tests the endpoint for retrieving all notes for the authenticated user.

    Sends a GET request to the notes listing endpoint and verifies that the response
    is successful and returns a list of notes.

    Args:
        login_auth_client (FlaskClient): Authenticated client.
        session (Session): SQLAlchemy session.
        create_user (User): The user requesting their notes.
    """

    response = login_auth_client.get('/note/get-notes')
    assert response.status_code == 200
    notes = response.get_json()
    assert isinstance(notes, list)

def test_get_single_note(login_auth_client, session, create_user):
    """
    Tests the endpoint for retrieving a single note by its ID.

    Creates a note in the database, then retrieves it using a GET request.
    Asserts the response is successful and contains expected fields like `ai_summary`.

    Args:
        login_auth_client (FlaskClient): Authenticated client.
        session (Session): SQLAlchemy session.
        create_user (User): Owner of the note being retrieved.
    """

    note = Note(title="Note1", original="Content1", user_id=create_user.id)
    session.add(note)
    session.commit()

    response = login_auth_client.get(f'/note/get-note/{note.note_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert "ai_summary" in data

def test_update_note(login_auth_client, session, create_user):
    """
    Tests the endpoint for updating an existing note.

    Creates a note, sends a PUT request with updated title and content, and
    verifies the note is updated in the database accordingly.

    Args:
        login_auth_client (FlaskClient): Authenticated client.
        session (Session): SQLAlchemy session.
        create_user (User): Owner of the note being updated.
    """

    note = Note(title="Old Title", original="Old Content", user_id=create_user.id)
    session.add(note)
    session.commit()

    response = login_auth_client.put(f'/note/update-note/{note.note_id}', json={
        "title": "New Title",
        "content": "New Content"
    })
    assert response.status_code == 200
    session.refresh(note)
    assert note.title == "New Title"
    assert note.original == "New Content"

def test_delete_note(login_auth_client, session, create_user):
    """
    Tests the endpoint for deleting a note.

    Creates a note, sends a DELETE request, and verifies that the note is removed
    from the database after the operation.

    Args:
        login_auth_client (FlaskClient): Authenticated client.
        session (Session): SQLAlchemy session.
        create_user (User): Owner of the note being deleted.
    """

    note = Note(title="To be deleted", original="Delete me", user_id=create_user.id)
    session.add(note)
    session.commit()

    response = login_auth_client.delete(f'/note/delete-note/{note.note_id}')
    assert response.status_code == 200

    deleted = session.query(Note).filter_by(note_id=note.note_id).first()
    assert deleted is None

def test_access_foreign_note_denied(test_client, session, create_user):
    """
    Tests that a user cannot access another user's note.

    Creates a note for one user and logs in as a different user.
    Attempts to access the note and verifies that the response returns a 404,
    indicating proper access restriction.

    Args:
        test_client (FlaskClient): Flask test client.
        session (Session): SQLAlchemy session.
        create_user (User): The original owner of the note.
    """

    note = Note(title="Foreign Note", original="Secret", user_id=create_user.id)
    session.add(note)
    session.commit()

    other_user = User(username="otheruser", email="other@example.com")
    other_user.set_password("otherpassword")
    session.add(other_user)
    session.commit()

    response = test_client.post('/user/login', json={
        "username": "otheruser",
        "password": "otherpassword"
    })
    assert response.status_code == 200

    response = test_client.get(f'/note/get-note/{note.note_id}')
    assert response.status_code == 404
