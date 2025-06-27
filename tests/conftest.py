import pytest

from src.app import create_app
from src.config.config import DevelopmentConfig
from src.data.db import Base, get_engine, get_session_local
from src.data.models import Note
from src.data.models.users import User

class TestConfig(DevelopmentConfig):
    TESTING = True
    DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="module")
def test_engine():
    """
    Provides a SQLAlchemy engine connected to a temporary SQLite database for testing.

    The database schema is created before the tests in the module run and dropped afterward.
    This ensures a clean database state for the entire module's tests.

    Yields:
        sqlalchemy.engine.Engine: The SQLAlchemy engine connected to the test database.
    """
    engine = get_engine(TestConfig.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="module")
def test_app(test_engine):
    """
    Creates and configures a Flask application instance for testing.

    Uses the test SQLite database and enables testing mode.
    Pushes the application context before yielding and pops it afterward to manage
    application state correctly during tests.

    Yields:
        flask.Flask: The Flask application configured for testing.
    """
    app = create_app(TestConfig)
    app.config['ENGINE'] = test_engine
    app.config['SESSION_LOCAL'] = get_session_local(test_engine)

    ctx = app.app_context()
    ctx.push()
    yield app
    ctx.pop()

@pytest.fixture(scope="module")
def test_client(test_app):
    """
    Provides a Flask test client for sending HTTP requests to the test application.

    Relies on the 'test_app' fixture for the application context.

    Returns:
        flask.testing.FlaskClient: A test client for the Flask application.
    """
    return test_app.test_client()

@pytest.fixture()
def session(test_engine):
    """
    Provides a SQLAlchemy database session scoped to a single test function.

    The session is rolled back and closed after each test to ensure no changes persist
    between tests, maintaining test isolation.

    Args:
        test_engine (sqlalchemy.engine.Engine): The SQLAlchemy engine from 'test_engine' fixture.

    Yields:
        sqlalchemy.orm.Session: A SQLAlchemy session bound to the test engine.
    """
    SessionLocal = get_session_local(test_engine)
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()

@pytest.fixture()
def new_user():
    """
    Supplies a dictionary representing a new user for testing purposes.

    The dictionary contains a valid username, email, and password, useful for
    creating or registering users in tests.

    Returns:
        dict: A dictionary with keys 'username', 'email', and 'password' representing user data.
    """
    return {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpassword123"
    }

@pytest.fixture()
def create_user(session):
    """
    Creates and persists a new user in the test database.

    Ensures any existing users are deleted before creation to avoid conflicts.
    After the test finishes, deletes the user to clean up the database.

    Args:
        session (sqlalchemy.orm.Session): The SQLAlchemy session for database operations.

    Yields:
        User: The newly created User ORM instance.
    """
    session.query(User).delete()
    session.commit()

    user = User(username="testuser", email="testuser@example.com")
    user.set_password("testpassword123")
    session.add(user)
    session.commit()
    yield user
    session.delete(user)
    session.commit()

@pytest.fixture()
def login_auth_client(test_client, create_user):
    """
    Provides a test client authenticated as the created user.

    Performs a login request with valid credentials and asserts successful authentication
    before yielding the authenticated client for use in tests requiring authorization.

    Args:
        test_client (flask.testing.FlaskClient): The Flask test client.
        create_user (User): The user instance created by the 'create_user' fixture.

    Yields:
        flask.testing.FlaskClient: An authenticated Flask test client.
    """
    with test_client:
        response = test_client.post('/user/login', json={
            "username": "testuser",
            "password": "testpassword123"
        })
        assert response.status_code == 200
        yield test_client

@pytest.fixture()
def create_note(session, create_user):
    """
    Creates and persists a Note associated with the created user in the test database.

    Adds a note with predefined title and content linked to the test user.
    After the test completes, deletes the note to maintain database cleanliness.

    Args:
        session (sqlalchemy.orm.Session): The SQLAlchemy session for database operations.
        create_user (User): The user instance to associate the note with.

    Yields:
        Note: The newly created Note ORM instance.
    """
    note = Note(title="AI Note", original="This is original content.", user_id=create_user.id)
    session.add(note)
    session.commit()
    yield note
    session.delete(note)
    session.commit()
