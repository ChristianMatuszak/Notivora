from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user

from src.app.services.llm_service import LLMService
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
    service = LLMService(session)

    try:
        service.generate_flashcards(note_id, current_user.id, generate_flashcards_from_summary)
        return jsonify({"message": "Flashcards generated successfully"}), HttpStatus.CREATED
    except ValueError as error:
        return jsonify({"error": str(error)}), HttpStatus.NOT_FOUND
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
    service = LLMService(session)

    try:
        summary, _ = service.generate_summary(note_id, current_user.id, generate_summary_from_note)
        return jsonify({"ai_summary": summary}), HttpStatus.OK
    except ValueError as ve:
        code = HttpStatus.NOT_FOUND if str(
            ve) == ErrorMessages.NOTE_NOT_FOUND else HttpStatus.BAD_REQUEST
        return jsonify({"error": str(ve)}), code
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
    language = data.get('language')

    session = current_app.config['SESSION_LOCAL']()
    service = LLMService(session)

    if not all([question, correct_answer, user_answer]):
        return jsonify({"error": ErrorMessages.MISSING_ANSWER_FIELD}), HttpStatus.BAD_REQUEST
    if not language:
        return jsonify({"error": ErrorMessages.MISSING_LANGUAGE}), HttpStatus.BAD_REQUEST

    try:
        result = service.check_answer(question, correct_answer, user_answer, language,
                                      check_user_answer_with_llm)
        return jsonify(result), HttpStatus.OK
    except ValueError as ve:
        return jsonify({"error": str(ve)}), HttpStatus.BAD_REQUEST
    except Exception as error:
        return jsonify({"error": str(error)}), HttpStatus.INTERNAL_SERVER_ERROR
    finally:
        session.close()
