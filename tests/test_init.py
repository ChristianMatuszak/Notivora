import os
import logging
import pytest
import time
from src.app import create_app

@pytest.fixture
def app():
    """
    Creates and returns a Flask application instance for testing.

    This fixture initializes the Flask app using the factory method
    `create_app`. It is used by tests that require the app context or
    the test client.

    Returns:
        flask.Flask: The Flask application instance.
    """
    app = create_app()
    return app

@pytest.fixture
def client(app):
    """
    Provides a test client for the Flask application.

    The test client simulates HTTP requests to the Flask app without
    running the server. It depends on the `app` fixture.

    Args:
        app (flask.Flask): The Flask application instance.

    Returns:
        flask.testing.FlaskClient: The Flask test client.
    """
    return app.test_client()

def test_create_app(app):
    """
    Verify that the Flask application is created correctly.

    This test ensures the factory function `create_app` returns a valid
    Flask app instance and that the app's name matches the expected value.

    Args:
        app (flask.Flask): The Flask application instance from the fixture.
    """
    assert app is not None
    assert app.name == "src.app"

def test_ping_route(client):
    """
    Test the `/api/v1/ping` endpoint for correct response.

    Sends a GET request to the `/api/v1/ping` route and verifies that
    the response status code is 200 (OK), and the response data is exactly
    `pong` in bytes.

    Args:
        client (flask.testing.FlaskClient): The Flask test client.
    """
    response = client.get("/api/v1/ping")
    assert response.status_code == 200
    assert response.data == b"pong"

def test_create_app_raises(monkeypatch):
    """
    Simulate an exception during Flask app initialization.

    Patches `flask.Flask.__init__` to raise an Exception, forcing `create_app`
    to handle the error and return None. Tests that the app creation fails gracefully.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture to patch objects.
    """
    def fake_flask_init(*args, **kwargs):
        raise Exception("Fake error")

    monkeypatch.setattr("flask.Flask.__init__", fake_flask_init)

    app = create_app()
    assert app is None

@pytest.fixture
def test_log_file():
    """
    Provides the absolute path to a temporary log file used during testing.

    This fixture ensures the test uses a dedicated log file to avoid
    interfering with production or development logs.

    Returns:
        str: Absolute path to the test log file.
    """
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "test_app.log"))


def test_log_file_creation(monkeypatch, test_log_file):
    """
    Verify error logging when Flask app initialization fails.

    This test:
    - Removes the test log file if it exists.
    - Configures logging to write errors to the test log file.
    - Patches `flask.Flask.__init__` to raise an Exception.
    - Calls `create_app` and expects it to return None.
    - Checks that the log file is created.
    - Validates the log file contains the error message from the exception.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture for patching.
        test_log_file (str): Path to the test log file.
    """
    if os.path.exists(test_log_file):
        os.remove(test_log_file)

    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(filename=test_log_file, level=logging.ERROR, format='%(asctime)s %(levelname)s: %(message)s')

    def fake_flask_init(self, *args, **kwargs):
        raise Exception("Forced error for test")

    monkeypatch.setattr("flask.Flask.__init__", fake_flask_init)

    app = create_app()
    assert app is None

    time.sleep(0.1)

    assert os.path.exists(test_log_file), "Log file wurde nicht erstellt"

    with open(test_log_file, "r") as f:
        content = f.read()
        assert "Forced error for test" in content