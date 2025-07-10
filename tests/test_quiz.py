import pytest

from src.data.models.flashcards import Flashcard


@pytest.fixture()
def create_flashcards(session, create_note):
    """
    Creates and inserts multiple flashcards into the test database,
    associated with the provided test note.

    This fixture is used to simulate a note with flashcards available
    for quizzing.

    Yields:
        list[Flashcard]: A list of flashcard ORM instances.
    """
    flashcards = [
        Flashcard(question="What is AI?", answer="Artificial Intelligence", note_id=create_note.note_id),
        Flashcard(question="Define ML.", answer="Machine Learning", note_id=create_note.note_id),
        Flashcard(question="What is NLP?", answer="Natural Language Processing", note_id=create_note.note_id),
    ]
    session.add_all(flashcards)
    session.commit()
    yield flashcards
    for fc in flashcards:
        session.delete(fc)
    session.commit()


def test_start_quiz_success(login_auth_client, create_note, create_flashcards):
    """
    Tests the /quiz/start/<note_id> endpoint for a valid request.

    Ensures that when a logged-in user starts a quiz for an existing note
    with flashcards, the correct number of flashcards are returned with the
    expected structure.

    Args:
        login_auth_client: Authenticated Flask test client.
        create_note: A test note associated with the user.
        create_flashcards: Flashcards tied to the note.
    """
    response = login_auth_client.post(f"/quiz/start/{create_note.note_id}")
    assert response.status_code == 200
    data = response.get_json()
    assert "flashcards" in data
    assert len(data["flashcards"]) == 3
    assert all("question" in fc and "card_id" in fc for fc in data["flashcards"])


def test_start_quiz_not_found(login_auth_client):
    """
    Tests the /quiz/start/<note_id> endpoint with an invalid note ID.

    Ensures the system returns a 404 error when the note does not exist
    or is not accessible by the user.

    Args:
        login_auth_client: Authenticated Flask test client.
    """
    response = login_auth_client.post("/quiz/start/9999")
    assert response.status_code == 404
    assert "error" in response.get_json()
