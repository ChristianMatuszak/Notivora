import datetime
from sqlalchemy import Column, Integer, String, DateTime
from email_validator import validate_email, EmailNotValidError
from sqlalchemy.orm import relationship

from src.data.db import Base
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    """
    Database model for a user account.

    Attributes:
        id (int): Primary key, unique user identifier.
        username (str): Unique username chosen by the user.
        email (str): Unique email address of the user, validated for correctness.
        password_hash (str): Hashed password for authentication.
        created_at (datetime): Timestamp of user account creation in UTC.

    Methods:
        set_password(password: str) -> None:
            Hashes the given plaintext password and stores it.

        verify_password(password: str) -> bool:
            Verifies a plaintext password against the stored password hash.

        validate_user_email(email: str) -> str:
            Validates the format of an email address and returns the normalized form.
            Raises ValueError if the email is invalid.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    notes = relationship("Note", back_populates="user", cascade="all, delete-orphan")
    flashcards = relationship("Flashcard", back_populates="user", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="user", cascade="all, delete-orphan")
    scores = relationship("Score", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password: str):
        """Hashes and sets the user's password."""
        self.password_hash = pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        """Checks if the provided password matches the stored hash."""
        return pwd_context.verify(password, self.password_hash)

    @staticmethod
    def validate_user_email(email: str) -> str:
        """
        Validates and normalizes an email address.

        Args:
            email (str): Email address to validate.

        Returns:
            str: Normalized email address.

        Raises:
            ValueError: If the email is not valid.
        """
        try:
            valid = validate_email(email)
            return valid.normalized
        except EmailNotValidError as error:
            raise ValueError(f"Invalid email address: {error}")

    def __repr__(self):
        return f"<User(username={self.username}, email={self.email})>"


