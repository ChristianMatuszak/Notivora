import json

from flask import current_app

from src.utils.constants import ErrorMessages
from src.data.models.users import User


def test_create_user_duplicate_username(test_client, new_user):
    """
    Tests that registering a user with an existing username results in a failure.

    Sends a POST request with a duplicate username but a different email.
    Asserts that the response status is 400 and the error message indicates a duplicate username.

    Args:
        test_client (FlaskClient): The test client used for sending HTTP requests.
        new_user (dict): A valid user whose username is duplicated in the test.
    """

    response = test_client.post(
        "/user/create-user",
        data=json.dumps(new_user),
        content_type="application/json"
    )
    assert response.status_code == 201

    new_user_dup = new_user.copy()
    new_user_dup["email"] = "otheremail@example.com"
    response = test_client.post(
        "/user/create-user",
        data=json.dumps(new_user_dup),
        content_type="application/json"
    )
    assert response.status_code == 400
    data = response.get_json()
    assert ErrorMessages.USER_ALREADY_EXISTS in data["error"]

def test_create_user_duplicate_email(test_client, session,  new_user):
    """
    Tests that registering a user with an existing email address results in a failure.

    Sends a POST request with a different username but a duplicate email.
    Asserts that the response status is 400 and the error message indicates a duplicate email.

    Args:
        test_client (FlaskClient): The test client used for sending HTTP requests.
        new_user (dict): A valid user whose email is duplicated in the test.
    """

    session.query(User).filter_by(email=new_user["email"]).delete()
    session.commit()

    response = test_client.post(
        "/user/create-user",
        data=json.dumps(new_user),
        content_type="application/json"
    )
    assert response.status_code == 201

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


def test_get_user(login_auth_client):
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
    response = login_auth_client.get(f"/user/get-user/{user.id}")
    assert response.status_code == 200
    data = response.get_json()
    assert data["username"] == "testuser"
    assert data["email"] == "testuser@example.com"
