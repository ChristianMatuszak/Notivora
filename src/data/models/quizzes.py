from sqlalchemy import Column, Integer, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from src.data.db import Base

class Quiz(Base):
    """
    Represents a quiz attempt by a user on a flashcard, including user answer and AI feedback.

    Attributes:
        quiz_id (int): Primary key.
        answer (str): The user's answer text.
        ai_feedback (str): AI-generated feedback on the answer.
        answered (bool): Whether the flashcard has been answered.
        card_id (int): Foreign key linking to a flashcard.
        user_id (int): Foreign key linking to the user.
    """

    __tablename__ = "quizzes"

    quiz_id = Column(Integer, primary_key=True, index=True)
    answer = Column(Text, nullable=False)
    ai_feedback = Column(Text, nullable=True)
    answered = Column(Boolean, default=False)
    card_id = Column(Integer, ForeignKey("flashcards.card_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    flashcard = relationship("Flashcard", back_populates="quizzes")
    user = relationship("User", back_populates="quizzes")
    scores = relationship("Score", back_populates="quiz", cascade="all, delete-orphan")

    def __repr__(self):
        return (f"<Quiz(quiz_id={self.quiz_id}, user_id={self.user_id}, card_id={self.card_id}, "
                f"answered={self.answered})>")
