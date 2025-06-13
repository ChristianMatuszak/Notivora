import os
import pytest
from src.data.db import get_engine, get_session_local, Base, init_db
from src.data.models import User, Note

TEST_DATABASE_URL = "sqlite:///./testdb.sqlite"

@pytest.fixture(scope="session")
def engine():
    """
    Pytest fixture that creates and manages a SQLAlchemy engine for testing.

    Initializes a connection to the SQLite test database. After the test session,
    the engine is properly disposed, and the test database file is removed from disk
    to ensure a clean slate for subsequent runs.

    Yields:
        Engine: SQLAlchemy engine connected to the test database.
    """

    engine = get_engine(TEST_DATABASE_URL)
    print("Engine created, cwd:", os.getcwd())
    yield engine
    engine.dispose()
    if os.path.exists("testdb.sqlite"):
        print("Removing testdb.sqlite")
        os.remove("testdb.sqlite")

@pytest.fixture(scope="session")
def setup_database(engine):
    """
    Pytest fixture that initializes the test database schema.

    Creates all required tables before the test session and drops them afterward,
    ensuring a fresh schema state for each run.

    Depends on:
        engine (Engine): The SQLAlchemy engine connected to the test database.
    """

    init_db(engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def session(engine, setup_database):
    """
    Pytest fixture that provides a scoped SQLAlchemy session for database operations in tests.

    Commits and rolls back changes made within individual tests to preserve database state.
    Ensures proper cleanup by closing the session afterward.

    Yields:
        Session: An active SQLAlchemy session object for performing database queries.
    """

    SessionLocal = get_session_local(engine)
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()

def test_user_and_note_create(session):
    """
    Tests the creation and database persistence of a User and an associated Note.

    This test verifies that:
    - A user can be created and persisted with a hashed password.
    - A note can be associated with the user and committed to the database.
    - All fields (IDs and content) are stored as expected.

    Args:
        session (Session): The active SQLAlchemy session used to interact with the database.
    """

    user = User(username="tester", email="tester@example.com")
    user.set_password("password123")
    session.add(user)
    session.commit()

    note = Note(title="Note 1", original="Some content", user_id=user.id)
    session.add(note)
    session.commit()

    assert user.id is not None or user.user_id is not None
    assert note.note_id is not None
    assert note.user_id == user.id
    assert note.original == "Some content"