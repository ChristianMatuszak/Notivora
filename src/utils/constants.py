
class ErrorMessages:
    """
    Centralized collection of predefined error messages used throughout the application.

    This class provides standardized, reusable error message constants for common user-related,
    authentication, and note-related failures. By consolidating these messages in one place,
    the application ensures consistency in client responses and simplifies future maintenance,
    localization (i18n), and testing.

    Categories include:
    - User-related errors (e.g., not found, already exists, invalid credentials)
    - Authentication and password reset errors
    - Note-related validation and retrieval errors
    - Request format and data validation errors

    Usage:
        return jsonify({"error": ErrorMessages.USER_NOT_FOUND}), HttpStatus.NOT_FOUND

    Attributes:
        USER_NOT_FOUND (str): Error when a user cannot be found.
        USER_ALREADY_EXISTS (str): Error when attempting to create a user that already exists.
        INVALID_CREDENTIALS (str): Error for incorrect username or password.
        EMAIL_ALREADY_EXISTS (str): Error when the email is already in use.
        UNAUTHORIZED_ACCESS (str): Error for unauthorized or unauthenticated access.
        USERNAME_EMAIL_PASSWORD_REQUIRED (str): Error when one or more required fields are missing during registration.
        USERNAME_PASSWORD_REQUIRED (str): Error when username or password fields are missing.
        CURRENT_NEW_PASSWORD_REQUIRED (str): Error when updating a password without both current and new values.
        PASSWORD_MISMATCH (str): Error when new and confirmation passwords do not match.
        PASSWORD_INCORRECT (str): Error when the current password is incorrect.
        EMAIL_REQUIRED (str): Error when email field is missing.
        TOKEN_PASSWORD_FIELDS_REQUIRED (str): Error when resetting password without token or password fields.
        EXPIRED_INVALID_TOKEN (str): Error when the password reset token is expired or invalid.

        NOTE_NOT_FOUND (str): Error when a requested note cannot be found.
        TITLE_CONTENT_REQUIRED (str): Error when both title and content are missing in note creation.
        TITLE_REQUIRED (str): Error when title is not provided.
        EMPTY_NOTE_CONTENT (str): Error when note content is empty.

        NO_SUMMARY_AVAILABLE (str): Error when attempting to summarize a note without a summary.
        MISSING_ANSWER_FIELD (str): Error when the answer field is absent in the request body.
        MISSING_LANGUAGE (str): Error when the language field is missing from the request.
    """
    USER_NOT_FOUND = "User not found."
    USER_ALREADY_EXISTS = "User already exists."
    INVALID_CREDENTIALS = "Invalid username or password."
    EMAIL_ALREADY_EXISTS = "Email already exists."
    UNAUTHORIZED_ACCESS = "Unauthorized access."
    USERNAME_EMAIL_PASSWORD_REQUIRED = "Username, email, and password are required."
    USERNAME_PASSWORD_REQUIRED = "Username and password are required."
    CURRENT_NEW_PASSWORD_REQUIRED = "Current password and new password are required."
    PASSWORD_MISMATCH = "New password and confirm password do not match."
    PASSWORD_INCORRECT = "Current password is incorrect."
    EMAIL_REQUIRED = "Email is required."
    TOKEN_PASSWORD_FIELDS_REQUIRED  = "Token and both password fields are required"
    EXPIRED_INVALID_TOKEN = "The provided token is either expired or invalid."

    NOTE_NOT_FOUND = "Note not found."
    TITLE_CONTENT_REQUIRED = "Title and content are required for creating a note."
    TITLE_REQUIRED = "Title is required."
    EMPTY_NOTE_CONTENT = "Note content cannot be empty."

    NO_SUMMARY_AVAILABLE = "No summary available for this note."
    MISSING_ANSWER_FIELD = "Answer field is missing in the request."
    MISSING_LANGUAGE = "Missing Language"

class HttpStatus:
    """
   Collection of standard HTTP status codes used throughout the application.

   This class defines constant integer values representing common HTTP response
   status codes. These codes are used to standardize responses across routes,
   services, and exception handling mechanisms, ensuring proper communication
   with clients and APIs.

   Attributes:
       OK (int): HTTP 200 — Standard response for successful HTTP requests.
       CREATED (int): HTTP 201 — Indicates that a resource has been successfully created.
       NO_CONTENT (int): HTTP 204 — Successful request that returns no content.

       BAD_REQUEST (int): HTTP 400 — The request was invalid or cannot be otherwise served.
       UNAUTHORIZED (int): HTTP 401 — Authentication is required and has failed or has not been provided.
       FORBIDDEN (int): HTTP 403 — The request is understood but it has been refused or access is not allowed.
       NOT_FOUND (int): HTTP 404 — The requested resource could not be found.
       CONFLICT (int): HTTP 409 — The request could not be completed due to a conflict with the current state of the resource.
       INTERNAL_SERVER_ERROR (int): HTTP 500 — A generic error occurred on the server.
   """
    OK = 200
    CREATED = 201
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    INTERNAL_SERVER_ERROR = 500