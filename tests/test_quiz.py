import pytest
from src.data.models.flashcards import Flashcard
from src.app.services.quiz_service import QuizService


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


def test_quiz_progress(login_auth_client, create_note, create_flashcards, session, create_user):
    """
    Tests the /quiz/progress/<note_id> endpoint.

    This test checks:
    1. That initially, no flashcards have been answered and progress is 0%.
    2. That submitting one answer correctly updates progress to 33.33%.

    Args:
        login_auth_client: Authenticated Flask test client.
        create_note: The note the quiz is based on.
        create_flashcards: The list of flashcards under that note.
        session: SQLAlchemy session to manually trigger a service call.
        create_user: The user submitting the answer.
    """
    response = login_auth_client.get(f"/quiz/progress/{create_note.note_id}")
    assert response.status_code == 200
    progress = response.get_json()
    assert progress["total_flashcards"] == 3
    assert progress["answered_flashcards"] == 0
    assert progress["progress_percent"] == 0.0

    quiz_service = QuizService(session)
    quiz_service.submit_answer(
        user_id=create_user.id,
        card_id=create_flashcards[0].card_id,
        user_answer="Artificial Intelligence"
    )

    response = login_auth_client.get(f"/quiz/progress/{create_note.note_id}")
    assert response.status_code == 200
    progress = response.get_json()
    assert progress["answered_flashcards"] == 1
    assert progress["progress_percent"] == pytest.approx(33.33, 0.1)
