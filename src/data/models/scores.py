from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey
from datetime import datetime

from sqlalchemy.orm import relationship

from src.data.db import Base

class Score(Base):
    """
    Represents the scoring and review data for a user's quiz attempt on a flashcard.

    Attributes:
        score_id (int): Primary key identifier for the score entry.
        card_id (int): Foreign key referencing the associated flashcard.
        quiz_id (int): Foreign key referencing the associated quiz attempt.
        checked_answer (bool): Whether the user's answer was checked/correct.
        answered (datetime): Timestamp when the answer was submitted.
    """

    __tablename__ = "scores"

    score_id = Column(Integer, primary_key=True, index=True)
    card_id = Column(Integer, ForeignKey("flashcards.card_id"), nullable=False)
    quiz_id = Column(Integer, ForeignKey("quizzes.quiz_id"), nullable=False)
    checked_answer = Column(Boolean, default=False)
    answered = Column(DateTime, default=datetime.utcnow, nullable=False)

    flashcard = relationship("Flashcard", back_populates="scores")
    quiz = relationship("Quiz", back_populates="scores")


    def __repr__(self):
        return (f"<Score(score_id={self.score_id}, card_id={self.card_id}, "
                f"quiz_id={self.quiz_id}, checked_answer={self.checked_answer}, "
                f"answered={self.answered})>")