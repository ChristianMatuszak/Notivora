from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user

from src.app.services.note_service import NoteService
from src.utils.constants import HttpStatus, ErrorMessages

note_bp = Blueprint('note', __name__, url_prefix='/note')

@note_bp.route('/store-note', methods=['POST'])
@login_required
def store_note():
    """
    Creates a new note associated with the currently authenticated user.

    This endpoint expects a JSON payload containing 'title' and 'content' fields.
    Both fields are mandatory, and if either is missing, a 400 Bad Request response will be returned.
    Upon successful creation, the note is persisted in the database with a link to the current user's ID.

    Returns:
        A JSON object containing a confirmation message and the unique identifier of the newly created note,
        along with HTTP status code 201 (Created).

    Raises:
        400 Bad Request if required fields are missing.
        500 Internal Server Error if any database operation fails.
    """
    data = request.get_json()
    session = current_app.config['SESSION_LOCAL']()
    service = NoteService(session)

    try:
        note = service.create_note(current_user.id, data.get('title'), data.get('content'))
        return jsonify({'message': 'Note created', 'note_id': note.note_id}), HttpStatus.CREATED
    except ValueError as err:
        return jsonify({"error": str(err)}), HttpStatus.BAD_REQUEST
    except Exception as error:
        return jsonify({"error": str(error)}), HttpStatus.INTERNAL_SERVER_ERROR
    finally:
        session.close()

@note_bp.route('/get-note/<int:note_id>', methods=['GET'])
@login_required
def get_note(note_id):
    """
    Retrieves the AI-generated summary of a note by its ID for the authenticated user.

    The endpoint ensures that the requested note belongs to the user making the request,
    preventing unauthorized access to other users' notes.
    If the note does not exist or is not owned by the current user, a 404 Not Found error is returned.

    Args:
        note_id (int): The unique identifier of the note to be retrieved.

    Returns:
        A JSON object containing the 'ai_summary' field of the note on success with HTTP 200 status.

    Raises:
        404 Not Found if no matching note is found for the current user.
        500 Internal Server Error if any unexpected error occurs during processing.
    """

    session = current_app.config['SESSION_LOCAL']()
    service = NoteService(session)

    try:
        note = service.get_note_by_id(note_id, current_user.id)
        if not note:
            return jsonify({"error": ErrorMessages.NOTE_NOT_FOUND}), HttpStatus.NOT_FOUND

        return jsonify({"ai_summary": note.ai_summary}), HttpStatus.OK

    except Exception as error:
        return jsonify({"error": str(error)}), HttpStatus.INTERNAL_SERVER_ERROR

    finally:
        session.close()

@note_bp.route('/get-notes', methods=['GET'])
@login_required
def get_notes():
    """
    Fetches a list of all notes that belong to the currently authenticated user.

    Each note returned includes its unique identifier and title,
    providing a summary view suitable for display in a notes list or dashboard.

    Returns:
        A JSON array of objects, where each object contains 'note_id' and 'title' keys,
        with an HTTP 200 status indicating successful retrieval.

    Raises:
        500 Internal Server Error if an unexpected error occurs during database interaction.
    """

    session = current_app.config['SESSION_LOCAL']()
    service = NoteService(session)

    try:
        notes = service.get_all_notes_for_user(current_user.id)
        result = [
            {"note_id": note.note_id, "title": note.title} for note in notes
        ]
        return jsonify(result), HttpStatus.OK

    except Exception as error:
        return jsonify({"error": str(error)}), HttpStatus.INTERNAL_SERVER_ERROR

    finally:
        session.close()

@note_bp.route('/update-note/<int:note_id>', methods=['PUT'])
@login_required
def update_note(note_id):
    """
    Updates the title and/or content of a note owned by the authenticated user.

    The client must provide the note's ID as a URL parameter.
    The request body may include 'title' and/or 'content' fields;
    only provided fields will be updated, allowing partial updates.

    Args:
        note_id (int): The unique identifier of the note to update.

    Returns:
        A JSON response confirming successful update with HTTP 200 status.

    Raises:
        404 Not Found if the note does not exist or is not owned by the current user.
        500 Internal Server Error if the update operation fails.
    """

    data = request.get_json()
    title = data.get('title')
    content = data.get('content')

    session = current_app.config['SESSION_LOCAL']()
    service = NoteService(session)

    try:
        success = service.update_note(note_id, current_user.id, title, content)
        if not success:
            return jsonify({"error": ErrorMessages.NOTE_NOT_FOUND}), HttpStatus.NOT_FOUND

        return jsonify({"message": "Note updated successfully"}), HttpStatus.OK

    except Exception as error:
        session.rollback()
        return jsonify({"error": str(error)}), HttpStatus.INTERNAL_SERVER_ERROR

    finally:
        session.close()

@note_bp.route('/delete-note/<int:note_id>', methods=['DELETE'])
@login_required
def delete_note(note_id):
    """
    Deletes a note identified by its ID, ensuring it belongs to the authenticated user.

    This operation permanently removes the note from the database.
    If the note is not found or does not belong to the user, a 404 Not Found error is returned.

    Args:
        note_id (int): The unique identifier of the note to delete.

    Returns:
        A JSON confirmation message upon successful deletion with HTTP 200 status.

    Raises:
        404 Not Found if the note cannot be located for the current user.
        500 Internal Server Error if deletion fails due to database errors.
    """

    session = current_app.config['SESSION_LOCAL']()
    service = NoteService(session)

    try:
        success = service.delete_note(note_id, current_user.id)
        if not success:
            return jsonify({"error": ErrorMessages.NOTE_NOT_FOUND}), HttpStatus.NOT_FOUND

        return jsonify({"message": "Note deleted successfully"}), HttpStatus.OK

    except Exception as error:
        session.rollback()
        return jsonify({"error": str(error)}), HttpStatus.INTERNAL_SERVER_ERROR

    finally:
        session.close()


