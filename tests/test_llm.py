from unittest.mock import patch

from src.data.models.notes import Note

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
        assert data["result"] == "Close enough!"
