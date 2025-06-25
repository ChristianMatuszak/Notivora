from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user, logout_user, login_user

from src.utils.constants import HttpStatus, ErrorMessages
from src.data.models.flashcards import Flashcard
from src.data.models.notes import Note
from src.data.models.users import User
from src.utils.email import send_reset_email
from src.utils.token import generate_reset_token, verify_reset_token

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route("/create-user", methods=["POST"])
def create_user():
    """
    Create a new user account.

    Accepts a JSON payload with `username`, `email`, and `password`. Ensures both
    username and email are unique before creating a new user record.

    Request JSON:
        {
            "username": "string",
            "email": "string",
            "password": "string"
        }

    Returns:
        201 Created: On successful creation. Includes user ID.
        400 Bad Request: If required fields are missing or already exist.
        500 Internal Server Error: If an unexpected error occurs.
    """
    data = request.get_json()
    session = current_app.config['SESSION_LOCAL']()

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({"error": ErrorMessages.USERNAME_EMAIL_PASSWORD_REQUIRED}), HttpStatus.BAD_REQUEST

    if session.query(User).filter_by(username=username).first():
        return jsonify({"error": ErrorMessages.USER_ALREADY_EXISTS}), HttpStatus.BAD_REQUEST

    if session.query(User).filter_by(email=email).first():
        return jsonify({"error": ErrorMessages.EMAIL_ALREADY_EXISTS}), HttpStatus.BAD_REQUEST

    try:
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        session.add(new_user)
        session.commit()
        return jsonify({"message": "User created successfully", "user_id": new_user.id}), HttpStatus.CREATED
    except Exception as error:
        session.rollback()
        return jsonify({"error": str(error)}), HttpStatus.INTERNAL_SERVER_ERROR
    finally:
        session.close()


@user_bp.route("/get-user/<int:user_id>", methods=["GET"])
@login_required
def get_user(user_id):
    """
    Retrieves the profile details of the specified user if authorized.

    Only the user themselves can access their data.
    Returns user info (id, username, email).

    Args:
        user_id (int): ID of the user to retrieve.

    Returns:
        JSON object with user data and HTTP 200 on success.
        403 Forbidden if accessing another user's data.
        404 Not Found if user doesn't exist.
        500 Internal Server Error on unexpected errors.
    """
    session = current_app.config['SESSION_LOCAL']()
    user = session.query(User).filter_by(id=user_id).first()

    if not user:
        return jsonify({"error": ErrorMessages.USER_NOT_FOUND}), HttpStatus.NOT_FOUND

    if user.id != current_user.id:
        return jsonify({"error": ErrorMessages.UNAUTHORIZED_ACCESS}), HttpStatus.FORBIDDEN

    try:
        user_data = {"id": user.id, "username": user.username, "email": user.email}
        return jsonify(user_data), HttpStatus.OK
    except Exception as error:
        return jsonify({"error": str(error)}), HttpStatus.INTERNAL_SERVER_ERROR
    finally:
        session.close()

@user_bp.route("/update-user/<int:user_id>", methods=["PUT"])
@login_required
def update_user(user_id):
    """
    Updates username and/or email of the authenticated user.

    Validates uniqueness of new username and email if provided.

    Args:
        user_id (int): ID of the user to update.
        JSON body may contain "username" (str) and/or "email" (str).

    Returns:
        JSON success message on HTTP 200.
        400 Bad Request if username/email already exist or invalid input.
        403 Forbidden if user tries to update another user's data.
        404 Not Found if user doesn't exist.
        500 Internal Server Error on unexpected errors.
    """
    session = current_app.config['SESSION_LOCAL']()
    data = request.get_json()
    user = session.query(User).filter_by(id=user_id).first()

    if not user:
        return jsonify({"error": ErrorMessages.USER_NOT_FOUND}), HttpStatus.NOT_FOUND

    if user.id != current_user.id:
        return jsonify({"error": ErrorMessages.UNAUTHORIZED_ACCESS}), HttpStatus.FORBIDDEN

    username = data.get("username")
    email = data.get("email")

    if username:
        if session.query(User).filter(User.username == username, User.id != user.id).first():
            return jsonify({"error": ErrorMessages.USER_ALREADY_EXISTS}), HttpStatus.BAD_REQUEST
        user.username = username

    if email:
        if session.query(User).filter(User.email == email, User.id != user.id).first():
            return jsonify({"error": ErrorMessages.EMAIL_ALREADY_EXISTS}), HttpStatus.BAD_REQUEST
        user.email = email

    try:
        session.commit()
        return jsonify({"message": "User updated successfully"}), HttpStatus.OK
    except Exception as error:
        session.rollback()
        return jsonify({"error": str(error)}), HttpStatus.INTERNAL_SERVER_ERROR
    finally:
        session.close()

@user_bp.route("/delete-user/<int:user_id>", methods=["DELETE"])
@login_required
def delete_user(user_id):
    """
    Deletes the authenticated user's account along with associated notes and flashcards.

    Logs out the user after successful deletion.

    Args:
        user_id (int): ID of the user to delete.

    Returns:
        JSON success message on HTTP 200.
        403 Forbidden if trying to delete another user's account.
        404 Not Found if user doesn't exist.
        500 Internal Server Error on unexpected errors.
    """
    session = current_app.config['SESSION_LOCAL']()
    user = session.query(User).filter_by(id=user_id).first()

    if not user:
        return jsonify({"error": ErrorMessages.USER_NOT_FOUND}), HttpStatus.NOT_FOUND

    if user.id != current_user.id:
        return jsonify({"error": ErrorMessages.UNAUTHORIZED_ACCESS}), HttpStatus.FORBIDDEN

    try:
        logout_user()
        session.query(Note).filter_by(user_id=user.id).delete()
        session.query(Flashcard).filter_by(user_id=user.id).delete()
        session.delete(user)
        session.commit()
        return jsonify({"message": "User deleted successfully"}), HttpStatus.OK
    except Exception as error:
        session.rollback()
        return jsonify({"error": str(error)}), HttpStatus.INTERNAL_SERVER_ERROR
    finally:
        session.close()

@user_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    """
    Logs out the currently authenticated user.

    Returns:
        JSON success message on HTTP 200.
    """
    logout_user()
    return jsonify({"message": "Logged out successfully"}), HttpStatus.OK

@user_bp.route("/list-users", methods=["GET"])
@login_required
def list_users():
    """
    List all registered users (admin-only).

    Only accessible by authenticated users with `is_admin = True`. Returns
    a list of users including their ID, username, and email.

    Returns:
        200 OK: List of user objects.
        403 Forbidden: If the authenticated user is not an admin.
        500 Internal Server Error: On unexpected failure.
    """
    session = current_app.config['SESSION_LOCAL']()
    try:
        if not current_user.is_admin:
            return jsonify({"error": ErrorMessages.UNAUTHORIZED_ACCESS}), HttpStatus.FORBIDDEN
        users = session.query(User).all()
        user_list = [{"id": user.id, "username": user.username, "email": user.email} for user in users]
        return jsonify(user_list), HttpStatus.OK
    except Exception as error:
        return jsonify({"error": str(error)}), HttpStatus.INTERNAL_SERVER_ERROR
    finally:
        session.close()

@user_bp.route("/fetch-flashcards/<int:user_id>", methods=["GET"])
@login_required
def fetch_flashcards(user_id):
    """
    Retrieves all flashcards belonging to the authenticated user.

    Args:
        user_id (int): ID of the user whose flashcards to retrieve.

    Returns:
        JSON list of flashcards (id, question, answer) on HTTP 200.
        403 Forbidden if user requests flashcards of another user.
        404 Not Found if user doesn't exist.
        500 Internal Server Error on unexpected errors.
    """
    session = current_app.config['SESSION_LOCAL']()
    user = session.query(User).filter_by(id=user_id).first()

    if not user:
        return jsonify({"error": ErrorMessages.USER_NOT_FOUND}), HttpStatus.NOT_FOUND

    if user.id != current_user.id:
        return jsonify({"error": ErrorMessages.UNAUTHORIZED_ACCESS}), HttpStatus.FORBIDDEN

    try:
        flashcards = session.query(Flashcard).filter_by(user_id=user.id).all()
        flashcard_list = [{"id": fc.id, "question": fc.question, "answer": fc.answer} for fc in flashcards]
        return jsonify(flashcard_list), HttpStatus.OK
    except Exception as error:
        return jsonify({"error": str(error)}), HttpStatus.INTERNAL_SERVER_ERROR
    finally:
        session.close()

@user_bp.route("/change-password/<int:user_id>", methods=["POST"])
@login_required
def change_password(user_id):
    """
    Changes the password for the authenticated user after verifying current password.

    Args:
        user_id (int): ID of the user changing the password.
        JSON body containing "current_password" and "new_password".

    Returns:
        JSON success message on HTTP 200.
        400 Bad Request if passwords are missing or current password is incorrect.
        403 Forbidden if user tries to change another user's password.
        404 Not Found if user doesn't exist.
        500 Internal Server Error on unexpected errors.
    """
    session = current_app.config['SESSION_LOCAL']()
    data = request.get_json()
    user = session.query(User).filter_by(id=user_id).first()

    if not user:
        return jsonify({"error": ErrorMessages.USER_NOT_FOUND}), HttpStatus.NOT_FOUND

    if user.id != current_user.id:
        return jsonify({"error": ErrorMessages.UNAUTHORIZED_ACCESS}), HttpStatus.FORBIDDEN

    new_password = data.get("new_password")
    current_password = data.get("current_password")

    if not current_password or not new_password:
        return jsonify({"error": ErrorMessages.CURRENT_NEW_PASSWORD_REQUIRED}), HttpStatus.BAD_REQUEST

    if not user.verify_password(current_password):
        return jsonify({"error": ErrorMessages.PASSWORD_INCORRECT}), HttpStatus.BAD_REQUEST

    try:
        user.set_password(new_password)
        session.commit()
        return jsonify({"message": "Password changed successfully"}), HttpStatus.OK
    except Exception as error:
        session.rollback()
        return jsonify({"error": str(error)}), HttpStatus.INTERNAL_SERVER_ERROR
    finally:
        session.close()

@user_bp.route("/request-password-reset", methods=["POST"])
def request_password_reset():
    """
    Initiates a password reset request by sending an email with a reset token link.

    Args:
        JSON body containing "email".

    Returns:
        JSON success message on HTTP 200.
        400 Bad Request if email is missing.
        404 Not Found if no user matches the email.
    """
    data = request.get_json()
    session = current_app.config['SESSION_LOCAL']()
    email = data.get("email")

    if not email:
        return jsonify({"error": ErrorMessages.EMAIL_REQUIRED}), HttpStatus.BAD_REQUEST

    user = session.query(User).filter_by(email=email).first()
    if not user:
        return jsonify({"error": ErrorMessages.USER_NOT_FOUND}), HttpStatus.NOT_FOUND

    token = generate_reset_token(user.id)
    reset_url = f"https://in-development.com/reset-password?token={token}"
    send_reset_email(user.email, reset_url)

    session.close()
    return jsonify({"message": "Password reset request received. Instructions will be sent to your email."}), HttpStatus.OK

@user_bp.route("/password-reset", methods=["POST"])
def password_reset():
    """
    Reset a user's password using a reset token.

    Accepts a token (usually sent via email) along with a new password and confirmation.

    Request JSON:
        {
            "token": "string",
            "new_password": "string",
            "confirm_password": "string"
        }

    Returns:
        200 OK: If the password was reset successfully.
        400 Bad Request: If fields are missing, passwords do not match, or token is invalid.
        404 Not Found: If the user linked to the token does not exist.
        500 Internal Server Error: If an unexpected error occurs.
    """
    data = request.get_json()
    session = current_app.config['SESSION_LOCAL']()
    token = data.get("token")
    new_password = data.get("new_password")
    confirm_password = data.get("confirm_password")

    if not token or not new_password or not confirm_password:
        return jsonify({"error": ErrorMessages.TOKEN_PASSWORD_FIELDS_REQUIRED}), HttpStatus.BAD_REQUEST

    if new_password != confirm_password:
        return jsonify({"error": ErrorMessages.PASSWORD_MISMATCH}), HttpStatus.BAD_REQUEST

    user_id = verify_reset_token(token)
    if not user_id:
        return jsonify({"error": ErrorMessages.EXPIRED_INVALID_TOKEN}), HttpStatus.BAD_REQUEST

    user = session.query(User).filter_by(id=user_id).first()
    if not user:
        return jsonify({"error": ErrorMessages.USER_NOT_FOUND}), HttpStatus.NOT_FOUND

    try:
        user.set_password(new_password)
        session.commit()
        return jsonify({"message": "Password has been reset successfully"}), HttpStatus.OK
    except Exception as error:
        session.rollback()
        return jsonify({"error": str(error)}), HttpStatus.INTERNAL_SERVER_ERROR
    finally:
        session.close()

@user_bp.route("/login", methods=["POST"])
def login():
    """
    Authenticates a user and creates a session.

    Expects JSON body with "username" and "password".
    Verifies credentials and logs in the user if valid.

    Returns:
        200 OK with user ID and success message on successful login.
        400 Bad Request if username or password is missing.
        401 Unauthorized if credentials are invalid.
    """
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": ErrorMessages.USERNAME_PASSWORD_REQUIRED}), HttpStatus.BAD_REQUEST

    session = current_app.config['SESSION_LOCAL']()
    user = session.query(User).filter_by(username=username).first()
    session.close()

    if user is None or not user.verify_password(password):
        return jsonify({"error": ErrorMessages.INVALID_CREDENTIALS}), HttpStatus.UNAUTHORIZED

    login_user(user)
    return jsonify({"message": "Login successful", "user_id": user.id}), HttpStatus.OK