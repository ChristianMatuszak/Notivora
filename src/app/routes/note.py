from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from src.data.models.notes import Note
from src.data.db import SessionLocal

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
    session = SessionLocal()

    title = data.get('title')
    content = data.get('content')

    if not title or not content:
        return jsonify({"error": "Title and content are required"}), 400

    note = Note(
        title=title,
        original=content,
        user_id=current_user.id
    )

    try:
        session.add(note)
        session.commit()
        return jsonify({'message': 'Note created', 'note_id': note.note_id}), 201

    except Exception as error:
        session.rollback()
        return jsonify({"error": str(error)}), 500

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

    session = SessionLocal()

    try:
        note = session.query(Note).filter(Note.note_id == note_id, Note.user_id == current_user.id).first()
        if not note:
            return jsonify({"error": "Note not found"}), 404

        return jsonify({"ai_summary": note.ai_summary, })

    except Exception as error:
        return jsonify({"error": str(error)}), 500
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

    session = SessionLocal()
    try:
        notes = session.query(Note).filter(Note.user_id == current_user.id).all()
        result = []
        for note in notes:
            result.append({
                "note_id": note.note_id,
                "title": note.title,
            })
        return jsonify(result), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500
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

    session = SessionLocal()
    data = request.get_json()

    title = data.get('title')
    content = data.get('content')

    try:
        note = session.query(Note).filter(Note.note_id == note_id, Note.user_id == current_user.id).first()
        if not note:
            return jsonify({"error": "Note not found"}), 404

        if title:
            note.title = title
        if content:
            note.original = content

        session.commit()
        return jsonify({"message": "Note updated successfully"}), 200

    except Exception as error:
        session.rollback()
        return jsonify({"error": str(error)}), 500
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

    session = SessionLocal()
    try:
        note = session.query(Note).filter(Note.note_id == note_id, Note.user_id == current_user.id).first()
        if not note:
            return jsonify({"error": "Note not found"}), 404

        session.delete(note)
        session.commit()
        return jsonify({"message": "Note deleted successfully"}), 200

    except Exception as error:
        session.rollback()
        return jsonify({"error": str(error)}), 500
    finally:
        session.close()


