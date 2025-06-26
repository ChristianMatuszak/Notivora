from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user, logout_user, login_user

from src.app.services.user_service import UserService
from src.utils.constants import HttpStatus, ErrorMessages


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

    try:
        user_service = UserService(session)
        new_user = user_service.create_user(
            data.get("username"),
            data.get("email"),
            data.get("password")
        )
        return jsonify({"message": "User created successfully", "user_id": new_user.id}), HttpStatus.CREATED
    except ValueError as error:
        return jsonify({"error": str(error)}), HttpStatus.BAD_REQUEST
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

    try:
        user_service = UserService(session)
        user = user_service.get_user_if_authorized(user_id, current_user.id)

        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
        return jsonify(user_data), HttpStatus.OK

    except ValueError as error:
            return jsonify({"error": ErrorMessages.USER_NOT_FOUND}), HttpStatus.NOT_FOUND

    except PermissionError:
        return jsonify({"error": ErrorMessages.UNAUTHORIZED_ACCESS}), HttpStatus.FORBIDDEN

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

    try:
        user_service = UserService(session)
        user_service.update_user(
            user_id=user_id,
            requesting_user_id=current_user.id,
            username=data.get("username"),
            email=data.get("email")
        )
        return jsonify({"message": "User updated successfully"}), HttpStatus.OK

    except ValueError as error:
        return jsonify({"error": str(error)}), HttpStatus.BAD_REQUEST

    except PermissionError as error:
        return jsonify({"error": str(error)}), HttpStatus.FORBIDDEN

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

    try:
        user_service = UserService(session)
        user_service.delete_user(user_id, current_user.id)

        logout_user()
        return jsonify({"message": "User deleted successfully"}), HttpStatus.OK

    except ValueError as error:
        return jsonify({"error": str(error)}), HttpStatus.NOT_FOUND

    except PermissionError as error:
        return jsonify({"error": str(error)}), HttpStatus.FORBIDDEN

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
        user_service = UserService(session)
        user_list = user_service.get_all_users_if_admin(current_user)
        return jsonify(user_list), HttpStatus.OK

    except PermissionError as error:
        return jsonify({"error": str(error)}), HttpStatus.FORBIDDEN

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
    service = UserService(session)

    try:
        flashcard_list = service.fetch_flashcards_for_user(user_id, current_user.id)
        return jsonify(flashcard_list), HttpStatus.OK
    except ValueError as ve:
        return jsonify({"error": str(ve)}), HttpStatus.NOT_FOUND
    except PermissionError as pe:
        return jsonify({"error": str(pe)}), HttpStatus.FORBIDDEN
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

    try:
        user_service = UserService(session)
        user_service.change_password(
            user_id,
            current_user.id,
            data.get("current_password"),
            data.get("new_password"),
        )
        return jsonify({"message": "Password changed successfully"}), HttpStatus.OK

    except ValueError as error:
        return jsonify({"error": str(error)}), HttpStatus.BAD_REQUEST

    except PermissionError as error:
        return jsonify({"error": str(error)}), HttpStatus.FORBIDDEN

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

    try:
        user_service = UserService(session)
        user_service.request_password_reset(data.get("email"))
        return jsonify({
                           "message": "Password reset request received. Instructions will be sent to your email."}), HttpStatus.OK

    except ValueError as error:
        return jsonify({"error": str(error)}), HttpStatus.BAD_REQUEST

    except Exception as error:
        return jsonify({"error": str(error)}), HttpStatus.INTERNAL_SERVER_ERROR

    finally:
        session.close()

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

    try:
        user_service = UserService(session)
        user_service.reset_password(
            data.get("token"),
            data.get("new_password"),
            data.get("confirm_password")
        )
        return jsonify({"message": "Password has been reset successfully"}), HttpStatus.OK

    except ValueError as error:
        return jsonify({"error": str(error)}), HttpStatus.BAD_REQUEST

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
    session = current_app.config['SESSION_LOCAL']()

    try:
        user_service = UserService(session)
        user = user_service.authenticate_user(
            data.get("username"),
            data.get("password"),
        )
        login_user(user)
        return jsonify({"message": "Login successful", "user_id": user.id}), HttpStatus.OK

    except ValueError as error:
        return jsonify({"error": str(error)}), HttpStatus.UNAUTHORIZED

    finally:
        session.close()