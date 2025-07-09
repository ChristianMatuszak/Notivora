from flask import Blueprint, jsonify, current_app
from flask_login import login_required, current_user
from src.app.services.quiz_service import QuizService
from src.utils.constants import HttpStatus

quiz_bp = Blueprint("quiz", __name__, url_prefix="/quiz")

@quiz_bp.route("/start/<int:note_id>", methods=["POST"])
@login_required
def start_quiz(note_id):
    """
    Starts a quiz by returning all flashcards of the note for the current user.

    Args:
        note_id (int): ID of the note to start quiz for.

    Returns:
        JSON containing the flashcards for the quiz and HTTP status 200.

    Raises:
        404 Not Found if no flashcards found or note doesn't belong to user.
        500 Internal Server Error on unexpected failures.
    """
    session = current_app.config['SESSION_LOCAL']()
    service = QuizService(session)

    try:
        flashcards = service.get_flashcards_for_quiz(current_user.id, note_id)
        if not flashcards:
            return jsonify({"error": "No flashcards found for this note"}), HttpStatus.NOT_FOUND
        return jsonify({"flashcards": flashcards}), HttpStatus.OK
    except Exception as error:
        session.rollback()
        return jsonify({"error": str(error)}), HttpStatus.INTERNAL_SERVER_ERROR
    finally:
        session.close()

@quiz_bp.route("/progress/<int:note_id>", methods=["GET"])
@login_required
def get_progress(note_id):
    """
    Returns quiz progress for a note by the current user.

    Args:
        note_id (int): ID of the note to get quiz progress for.

    Returns:
        JSON containing progress data and HTTP status 200.

    Raises:
        404 Not Found if progress data is unavailable.
        500 Internal Server Error on unexpected failures.
    """
    session = current_app.config['SESSION_LOCAL']()
    service = QuizService(session)

    try:
        progress = service.get_progress(current_user.id, note_id)
        if progress is None:
            return jsonify({"error": "Progress data not found"}), HttpStatus.NOT_FOUND
        return jsonify(progress), HttpStatus.OK
    except Exception as error:
        session.rollback()
        return jsonify({"error": str(error)}), HttpStatus.INTERNAL_SERVER_ERROR
    finally:
        session.close()
