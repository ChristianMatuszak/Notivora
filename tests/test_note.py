from src.data.models.notes import Note
from src.data.models.users import User


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

def test_note_validation(login_auth_client):
    """
    Tests validation behavior when creating notes with invalid input data.

    Sends multiple POST requests to the note creation endpoint using missing fields, empty strings,
    and values that exceed defined maximum lengths (as configured in `config.py`).
    Verifies that the API returns a 400 Bad Request and appropriate error messages.

    Args:
        login_auth_client (FlaskClient): Authenticated test client for making requests.
    """

    response = login_auth_client.post('/note/store-note', json={
        "content": "Valid content"
    })
    assert response.status_code == 400
    assert "title" in response.get_json().get("error", "").lower()

    response = login_auth_client.post('/note/store-note', json={
        "title": "Valid title"
    })
    assert response.status_code == 400
    assert "content" in response.get_json().get("error", "").lower()

    response = login_auth_client.post('/note/store-note', json={
        "title": "",
        "content": ""
    })
    assert response.status_code == 400
    assert "title" in response.get_json().get("error", "").lower()

    response = login_auth_client.post('/note/store-note', json={
        "title": "T" * 101,
        "content": "Valid content"
    })
    assert response.status_code == 400
    assert "title" in response.get_json().get("error", "").lower()

    response = login_auth_client.post('/note/store-note', json={
        "title": "Valid title",
        "content": "C" * 1001
    })
    assert response.status_code == 400
    assert "content" in response.get_json().get("error", "").lower()

