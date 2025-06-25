from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user

from src.data.models.notes import Note
from src.data.models.flashcards import Flashcard
from src.utils.constants import HttpStatus, ErrorMessages
from src.utils.llm_api import generate_flashcards_from_summary, generate_summary_from_note, \
    check_user_answer_with_llm

llm_bp = Blueprint('llm', __name__, url_prefix='/llm')

@llm_bp.route('/generate-flashcard/<int:note_id>', methods=['POST'])
@login_required
def generate_flashcard(note_id):
    """
    Generates flashcards from the AI summary of a specified note.

    Args:
        note_id (int): The ID of the note for which flashcards should be generated.

    This endpoint verifies that the note exists and belongs to the current user,
    and that an AI summary is available. Existing flashcards for the note are deleted
    before new ones are generated and stored.

    Returns:
        JSON with a success message and HTTP status 201 (Created).

    Raises:
        404 Not Found if the note does not exist, does not belong to the user,
        or if there is no AI summary available.
        500 Internal Server Error if flashcard generation or database operations fail.
    """
    session = current_app.config['SESSION_LOCAL']()
    try:
        note = session.query(Note).filter(Note.note_id == note_id, Note.user_id == current_user.id).first()
        if not note:
            return jsonify({"error": ErrorMessages.NOTE_NOT_FOUND}), HttpStatus.NOT_FOUND

        if not note.ai_summary:
            return jsonify({"error": ErrorMessages.NO_SUMMARY_AVAILABLE}), HttpStatus.NOT_FOUND

        existing_cards = session.query(Flashcard).filter(Flashcard.note_id == note_id).all()
        flashcards_data = generate_flashcards_from_summary(note.ai_summary, note.language)

        for card in existing_cards:
            session.delete(card)

        for card in flashcards_data:
            flashcard = Flashcard(
                question=card['question'],
                answer=card['answer'],
                type='',
                note_id=note_id,
                learned=False,
                last_studied=None,
                times_reviewed=0
            )
            session.add(flashcard)

        session.commit()

        return jsonify({"message": "Flashcards generated successfully"}), HttpStatus.CREATED

    except Exception as error:
        session.rollback()
        return jsonify({"error": str(error)}), HttpStatus.INTERNAL_SERVER_ERROR

    finally:
        session.close()

@llm_bp.route('/generate-summary/<int:note_id>', methods=['POST'])
@login_required
def generate_summary(note_id):
    """
    Generates an AI summary for the original content of a specified note.

    Args:
        note_id (int): The ID of the note to summarize.

    This endpoint checks that the note exists, belongs to the current user,
    and contains original content. The summary is generated via the LLM
    and saved to the note's `ai_summary` field.

    Returns:
        JSON containing the generated summary and HTTP status 200 (OK).

    Raises:
        404 Not Found if the note does not exist or is not owned by the user.
        400 Bad Request if the original content is missing.
        500 Internal Server Error if summary generation or database operations fail.
    """

    session = current_app.config['SESSION_LOCAL']()
    try:

        note = session.query(Note).filter(Note.note_id == note_id, Note.user_id == current_user.id).first()
        if not note:
            return jsonify({"error": ErrorMessages.NOTE_NOT_FOUND}), HttpStatus.NOT_FOUND

        if not note.original:
            return jsonify({"error": ErrorMessages.EMPTY_NOTE_CONTENT}), HttpStatus.BAD_REQUEST


        summary, language = generate_summary_from_note(note.original)

        note.ai_summary = summary
        note.language = language
        session.commit()

        return jsonify({"ai_summary": summary}), HttpStatus.OK

    except Exception as error:
        session.rollback()
        return jsonify({"error": str(error)}), HttpStatus.INTERNAL_SERVER_ERROR

    finally:
        session.close()

@llm_bp.route('/check-answer', methods=['POST'])
@login_required
def check_answer():
    """
    Evaluates a user's answer to a flashcard question using the LLM.

    Expects JSON payload with:
    - 'question': The original flashcard question.
    - 'correct_answer': The expected correct answer.
    - 'user_answer': The user's submitted answer.

    Returns:
        JSON containing feedback on the user's answer with HTTP status 200 (OK).

    Raises:
        400 Bad Request if any required fields are missing.
        500 Internal Server Error if answer evaluation or LLM interaction fails.
    """

    data = request.get_json()
    question = data.get('question')
    correct_answer = data.get('correct_answer')
    user_answer = data.get('user_answer')

    if not all([question, correct_answer, user_answer]):
        return jsonify({"error": ErrorMessages.MISSING_ANSWER_FIELD}), HttpStatus.BAD_REQUEST

    try:
        language = data.get('language')
        if not language:
            return jsonify({"error": ErrorMessages.MISSING_LANGUAGE}), HttpStatus.BAD_REQUEST

        result = check_user_answer_with_llm(question, correct_answer, user_answer, language)

        return jsonify(result), HttpStatus.OK

    except Exception as error:
        return jsonify({"error": str(error)}), HttpStatus.INTERNAL_SERVER_ERROR
