from src.data.models import User, Note, Flashcard
from  src.utils.constants import ErrorMessages
from src.utils.email import send_reset_email
from src.utils.token import generate_reset_token, verify_reset_token


class UserService:
    def __init__(self, session):
        """
        Initializes the UserService with a database session.

        Args:
            session: A SQLAlchemy session used for database operations.
        """
        self.session = session

    def create_user(self, username, email, password):
        """
        Creates a new user with the given username, email, and password.

        Args:
            username (str): The username for the new user.
            email (str): The email address for the new user.
            password (str): The password for the new user.

        Returns:
            JSON response with a success message and the new user's ID.

        Raises:
            ValueError: If required fields are missing or validation fails.
            Exception: For unexpected database errors.
        """

        if not username or not email or not password:
            raise ValueError("Username, email and password are required")

        if self.session.query(User).filter_by(username=username).first():
            raise ValueError(ErrorMessages.USER_ALREADY_EXISTS)

        if self.session.query(User).filter_by(email=email).first():
            raise ValueError(ErrorMessages.EMAIL_ALREADY_EXISTS)

        user = User(username=username, email=email)
        user.set_password(password)

        self.session.add(user)
        self.session.commit()

        return user

    def get_user_if_authorized(self, user_id, requesting_user_id):
        """
        Retrieves a user if the requesting user is authorized to access them.

        Args:
            user_id (int): ID of the user to retrieve.
            requesting_user_id (int): ID of the user making the request.

        Returns:
            User object if found and authorized.

        Raises:
            ValueError: If the user does not exist.
            PermissionError: If access is unauthorized.
        """

        user = self.session.query(User).filter_by(id=user_id).first()

        if not user:
            raise ValueError(ErrorMessages.USER_NOT_FOUND)

        if user.id != requesting_user_id:
            raise PermissionError(ErrorMessages.UNAUTHORIZED_ACCESS)

        return user

    def update_user(self, user_id, requesting_user_id, username=None, email=None):
        """
        Updates the username and/or email of a user if authorized.

        Args:
            user_id (int): ID of the user to update.
            requesting_user_id (int): ID of the user making the request.
            username (str, optional): New username.
            email (str, optional): New email address.

        Returns:
            Updated User object.

        Raises:
            ValueError: If the user does not exist or username/email already taken.
            PermissionError: If the requesting user is not authorized.
        """
        user = self.session.query(User).filter_by(id=user_id).first()

        if not user:
            raise ValueError(ErrorMessages.USER_NOT_FOUND)

        if user.id != requesting_user_id:
            raise PermissionError(ErrorMessages.UNAUTHORIZED_ACCESS)

        if username:
            if self.session.query(User).filter(User.username == username,
                                               User.id != user.id).first():
                raise ValueError(ErrorMessages.USER_ALREADY_EXISTS)
            user.username = username

        if email:
            if self.session.query(User).filter(User.email == email, User.id != user.id).first():
                raise ValueError(ErrorMessages.EMAIL_ALREADY_EXISTS)
            user.email = email

        self.session.commit()
        return user

    def delete_user(self, user_id, requesting_user_id):
        """
        Deletes a user and all related notes and flashcards if authorized.

        Args:
            user_id (int): ID of the user to delete.
            requesting_user_id (int): ID of the user making the request.

        Raises:
            ValueError: If the user does not exist.
            PermissionError: If the requesting user is not authorized.
        """
        user = self.session.query(User).filter_by(id=user_id).first()

        if not user:
            raise ValueError(ErrorMessages.USER_NOT_FOUND)

        if user.id != requesting_user_id:
            raise PermissionError(ErrorMessages.UNAUTHORIZED_ACCESS)

        self.session.query(Note).filter_by(user_id=user.id).delete()
        self.session.query(Flashcard).filter_by(user_id=user.id).delete()

        self.session.delete(user)
        self.session.commit()

    def get_all_users_if_admin(self, requesting_user):
        """
        Retrieves all users if the requesting user has admin privileges.

        Args:
            requesting_user (User): The user making the request.

        Returns:
            List of dicts containing user id, username, and email.

        Raises:
            PermissionError: If the requesting user is not an admin.
        """
        if not requesting_user.is_admin:
            raise PermissionError(ErrorMessages.UNAUTHORIZED_ACCESS)

        users = self.session.query(User).all()
        return [
            {"id": user.id, "username": user.username, "email": user.email}
            for user in users
        ]

    def fetch_flashcards_for_user(self, user_id: int, current_user_id: int) -> list[dict]:
        """
        Retrieves all flashcards belonging to the specified user if authorized.

        Args:
            user_id (int): ID of the user whose flashcards to fetch.
            current_user_id (int): ID of the user making the request.

        Returns:
            List of dictionaries representing flashcards with id, question, and answer.

        Raises:
            ValueError: If the user does not exist.
            PermissionError: If unauthorized access is attempted.
        """
        user = self.session.query(User).filter_by(id=user_id).first()
        if not user:
            raise ValueError(ErrorMessages.USER_NOT_FOUND)
        if user.id != current_user_id:
            raise PermissionError(ErrorMessages.UNAUTHORIZED_ACCESS)

        flashcards = self.session.query(Flashcard).filter_by(user_id=user.id).all()
        return [{"id": fc.id, "question": fc.question, "answer": fc.answer} for fc in flashcards]

    def change_password(self, user_id, requesting_user_id, current_password, new_password):
        """
        Changes a user's password if authorized and current password is correct.

        Args:
            user_id (int): ID of the user changing their password.
            requesting_user_id (int): ID of the user making the request.
            current_password (str): Current password for verification.
            new_password (str): New password to set.

        Returns:
            True if password changed successfully.

        Raises:
            ValueError: If user not found, fields missing, or current password incorrect.
            PermissionError: If unauthorized access is attempted.
        """

        user = self.session.query(User).filter_by(id=user_id).first()

        if not user:
            raise ValueError(ErrorMessages.USER_NOT_FOUND)

        if user.id != requesting_user_id:
            raise PermissionError(ErrorMessages.UNAUTHORIZED_ACCESS)

        if not current_password or not new_password:
            raise ValueError(ErrorMessages.CURRENT_NEW_PASSWORD_REQUIRED)

        if not user.verify_password(current_password):
            raise ValueError(ErrorMessages.PASSWORD_INCORRECT)

        user.set_password(new_password)
        self.session.commit()
        return True

    def request_password_reset(self, email):
        """
        Initiates a password reset process by sending a reset email with token.

        Args:
            email (str): Email address of the user requesting reset.

        Returns:
            True if reset email was sent successfully.

        Raises:
            ValueError: If email is missing or user with the email does not exist.
        """
        if not email:
            raise ValueError(ErrorMessages.EMAIL_REQUIRED)

        user = self.session.query(User).filter_by(email=email).first()
        if not user:
            raise ValueError(ErrorMessages.USER_NOT_FOUND)

        token = generate_reset_token(user.id)
        reset_url = f"https://in-development.com/reset-password?token={token}"
        send_reset_email(user.email, reset_url)

        return True

    def reset_password(self, token, new_password, confirm_password):
        """
        Resets a user's password given a valid reset token and matching new passwords.

        Args:
            token (str): Password reset token.
            new_password (str): New password to set.
            confirm_password (str): Confirmation of the new password.

        Returns:
            True if password reset was successful.

        Raises:
            ValueError: If any field is missing, passwords mismatch, token invalid/expired, or user not found.
        """
        if not token or not new_password or not confirm_password:
            raise ValueError(ErrorMessages.TOKEN_PASSWORD_FIELDS_REQUIRED)

        if new_password != confirm_password:
            raise ValueError(ErrorMessages.PASSWORD_MISMATCH)

        user_id = verify_reset_token(token)
        if not user_id:
            raise ValueError(ErrorMessages.EXPIRED_INVALID_TOKEN)

        user = self.session.query(User).filter_by(id=user_id).first()
        if not user:
            raise ValueError(ErrorMessages.USER_NOT_FOUND)

        user.set_password(new_password)
        self.session.commit()
        return True

    def authenticate_user(self, username, password):
        """
        Authenticates a user by verifying the username and password.

        Args:
            username (str): The username to authenticate.
            password (str): The password for the user.

        Returns:
            The authenticated User object.

        Raises:
            ValueError: If username or password is missing or invalid credentials.
        """

        if not username or not password:
            raise ValueError(ErrorMessages.USERNAME_PASSWORD_REQUIRED)

        user = self.session.query(User).filter_by(username=username).first()
        if user is None or not user.verify_password(password):
            raise ValueError(ErrorMessages.INVALID_CREDENTIALS)

        return user
