import pytest
import json

from flask import current_app

from src.app import create_app
from src.data.db import Base, get_engine, init_db
from src.data.models.users import User

def reset_database(database_url: str):
    """
    Drops and recreates all tables in the database, effectively resetting it.

    Used for ensuring a clean state before running tests. Disposes the engine after operations to free up resources.

    Args:
        database_url (str): The database URL used to connect to the test database.
    """

    engine = get_engine(database_url)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    engine.dispose()

@pytest.fixture(scope="module")
def test_engine():
    """
    Pytest fixture that sets up a test database engine with initialized schema.

    Creates all tables defined by the SQLAlchemy models before tests run.
    Cleans up by dropping all tables after the module's tests are complete.

    Yields:
        Engine: A SQLAlchemy engine connected to the test SQLite database.
    """

    engine = get_engine("sqlite:///./test.sqlite")
    init_db(engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="module")
def test_client():
    """
    Pytest fixture that provides a Flask test client for making HTTP requests during tests.

    Creates a Flask app with test configuration and pushes the app context so that Flask globals
    are available during the tests.

    Yields:
        FlaskClient: A Flask test client instance used to simulate HTTP requests.
    """

    app = create_app(database_url="sqlite:///./test.sqlite", testing=True)
    client = app.test_client()
    ctx = app.app_context()
    ctx.push()
    yield client
    ctx.pop()

@pytest.fixture
def new_user():
    """
    Pytest fixture that provides a dictionary representing a new user.

    The user data includes a username, email, and password. This fixture is reusable
    for creating and logging in test users.

    Returns:
        dict: A dictionary containing test user credentials and metadata.
    """

    return {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpassword123"
    }

def test_create_user(test_client, new_user):
    """
    Tests the user registration endpoint by creating a new user.

    Sends a POST request with valid user data and expects a 201 Created status in response.

    Args:
        test_client (FlaskClient): The test client for sending HTTP requests.
        new_user (dict): Dictionary containing the new user's registration data.
    """

    response = test_client.post(
        "/user/create-user",
        data=json.dumps(new_user),
        content_type="application/json"
    )
    if response.status_code != 201:
        print(response.data.decode())
    assert response.status_code == 201

def test_create_user_duplicate_username(test_client, new_user):
    """
    Tests that registering a user with an existing username results in a failure.

    Sends a POST request with a duplicate username but a different email.
    Asserts that the response status is 400 and the error message indicates a duplicate username.

    Args:
        test_client (FlaskClient): The test client used for sending HTTP requests.
        new_user (dict): A valid user whose username is duplicated in the test.
    """

    new_user_dup = new_user.copy()
    new_user_dup["email"] = "otheremail@example.com"
    response = test_client.post(
        "/user/create-user",
        data=json.dumps(new_user_dup),
        content_type="application/json"
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "Username already exists" in data["error"]

def test_create_user_duplicate_email(test_client, new_user):
    """
    Tests that registering a user with an existing email address results in a failure.

    Sends a POST request with a different username but a duplicate email.
    Asserts that the response status is 400 and the error message indicates a duplicate email.

    Args:
        test_client (FlaskClient): The test client used for sending HTTP requests.
        new_user (dict): A valid user whose email is duplicated in the test.
    """

    new_user_dup = new_user.copy()
    new_user_dup["username"] = "otheruser"
    response = test_client.post(
        "/user/create-user",
        data=json.dumps(new_user_dup),
        content_type="application/json"
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "Email already exists" in data["error"]

@pytest.fixture
def login(test_client, new_user):
    """
    Pytest fixture that creates and logs in a test user, returning an authenticated client.

    Registers the user using the `/user/create-user` endpoint and logs them in via `/user/login`.
    Returns the authenticated test client for use in subsequent authenticated requests.

    Args:
        test_client (FlaskClient): The test client for performing registration and login.
        new_user (dict): Dictionary containing credentials for the user to log in.

    Returns:
        FlaskClient: A client with an active session for the authenticated user.
    """

    test_client.post(
        "/user/create-user",
        data=json.dumps(new_user),
        content_type="application/json"
    )
    login_data = {"username": new_user["username"], "password": new_user["password"]}
    response = test_client.post(
        "/user/login",
        data=json.dumps(login_data),
        content_type="application/json"
    )
    assert response.status_code == 200
    return test_client

def test_get_user(login):
    """
    Tests the endpoint that retrieves user information by user ID.

    After authenticating via the `login` fixture, this test retrieves the user
    from the database and sends a GET request to fetch their public data.
    Asserts that the returned data matches the expected username and email.

    Args:
        login (FlaskClient): An authenticated Flask test client.
    """

    session = current_app.config['SESSION_LOCAL']()
    user = session.query(User).filter_by(username="testuser").first()
    session.close()
    response = login.get(f"/user/get-user/{user.id}")
    assert response.status_code == 200
    data = response.get_json()
    assert data["username"] == "testuser"
    assert data["email"] == "testuser@example.com"
