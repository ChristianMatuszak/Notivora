import pytest

from src.data.models import Flashcard
from src.data.models.notes import Note
from src.app.services.llm_service import LLMService
from src.utils.constants import ErrorMessages
from src.data.models.users import User
from src.utils.llm_api import check_user_answer_with_llm


@pytest.fixture(autouse=True)
def cleanup_llm_data(session):
    session.query(Flashcard).delete()
    session.query(Note).delete()
    session.commit()

def test_generate_summary(login_auth_client, session, create_user):
    """
    Tests the `/llm/generate-summary/<note_id>` endpoint for generating a note summary using an LLM.

    Mocks the LLM summary generation to return a predefined summary and language.
    Asserts that the endpoint returns a 200 status and includes the expected summary text.

    Args:
        login_auth_client (FlaskClient): Authenticated client with an active user session.
        create_note (Note): The note for which the summary will be generated.
    """

    long_content = (
        "Artificial intelligence (AI) is intelligence demonstrated by machines, "
        "unlike the natural intelligence displayed by humans and animals. "
        "Leading AI textbooks define the field as the study of 'intelligent agents': "
        "any device that perceives its environment and takes actions that maximize "
        "its chance of successfully achieving its goals. AI applications include "
        "advanced web search engines, recommendation systems, understanding human speech, "
        "self-driving cars, automated decision-making, and competing at the highest level "
        "in strategic game systems. Despite the progress, AI faces challenges including "
        "ensuring ethical use, addressing bias in data, and creating systems that can "
        "reason and understand context deeply. The future of AI depends heavily on "
        "ongoing research and the integration of AI into diverse domains."
    )

    note = Note(
        title="AI Content",
        original=long_content,
        user_id=create_user.id
    )
    session.add(note)
    session.commit()

    response = login_auth_client.post(f"/llm/generate-summary/{note.note_id}")
    assert response.status_code == 200

    data = response.get_json()
    assert "ai_summary" in data
    assert isinstance(data["ai_summary"], str)
    assert "intelligence" in data["ai_summary"].lower()

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

    create_note.ai_summary = "AI is the field of creating intelligent agents."
    create_note.language = "en"
    session.commit()

    response = login_auth_client.post(f"/llm/generate-flashcard/{create_note.note_id}")
    assert response.status_code == 201

    from src.data.models.flashcards import Flashcard
    flashcards = session.query(Flashcard).filter_by(note_id=create_note.note_id).all()
    assert len(flashcards) >= 1

def test_check_answer(login_auth_client):
    """
    Tests the `/llm/check-answer` endpoint which uses an LLM to evaluate a user's answer.

    Mocks the answer-checking logic and posts a test payload. Verifies the correct
    result is returned from the mocked LLM logic.

    Args:
        login_auth_client (FlaskClient): Authenticated client with user session.
    """

    question = "What is AI?"
    correct_answer = "Artificial Intelligence"
    user_answer = "AI"
    language = "en"

    feedback = check_user_answer_with_llm(question, correct_answer, user_answer, language)

    assert isinstance(feedback, dict)
    assert "evaluation" in feedback

    print("Question:", question)
    print("User answer:", user_answer)
    print("Feedback:", feedback["evaluation"])

def test_llm_service_error_handling(session, create_user):
    """
    Tests error handling in the LLMService methods.

    Verifies that the service raises ValueErrors when attempting to operate on missing or invalid data,
    such as non-existent notes, empty content, or missing input parameters.

    Args:
        session (Session): SQLAlchemy session for database access.
        create_user (User): User who owns the notes.
    """
    service = LLMService(session)

    with pytest.raises(ValueError) as exc1:
        service.generate_summary(note_id=9999, user_id=create_user.id, generate_summary_from_note=lambda x: ("summary", "en"))
    assert str(exc1.value) == ErrorMessages.NOTE_NOT_FOUND

    empty_note = Note(title="Empty", original="", user_id=create_user.id)
    session.add(empty_note)
    session.commit()

    with pytest.raises(ValueError) as exc2:
        service.generate_summary(note_id=empty_note.note_id, user_id=create_user.id, generate_summary_from_note=lambda x: ("summary", "en"))
    assert str(exc2.value) == ErrorMessages.EMPTY_NOTE_CONTENT

    with pytest.raises(ValueError) as exc3:
        service.generate_flashcards(note_id=9999, user_id=create_user.id, generate_flashcards_from_summary=lambda x, y: [], flashcard_service=None)
    assert str(exc3.value) == ErrorMessages.NOTE_NOT_FOUND

    no_summary_note = Note(title="No Summary", original="Real content", user_id=create_user.id)
    session.add(no_summary_note)
    session.commit()

    with pytest.raises(ValueError) as exc4:
        service.generate_flashcards(
            note_id=no_summary_note.note_id,
            user_id=create_user.id,
            generate_flashcards_from_summary=lambda x, y: [],
            flashcard_service=None
        )
    assert str(exc4.value) == ErrorMessages.NO_SUMMARY_AVAILABLE

    with pytest.raises(ValueError) as exc5:
        service.check_answer(
            question="What is AI?",
            correct_answer="Artificial Intelligence",
            user_answer="",
            language="en",
            check_user_answer_with_llm=lambda q, c, u, l: {}
        )
    assert "Missing required fields" in str(exc5.value)