from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from src.data.db import Base

class Flashcard(Base):
    """
    Represents a flashcard used for learning and review.

    Attributes:
        card_id (int): Primary key, unique identifier for the flashcard.
        question (str): The question or prompt shown to the user.
        answer (str): The correct answer or explanation.
        type (str, optional): Category or tag for the flashcard.
        note_id (int, optional): Foreign key linking to a related note.
        learned (bool): Flag indicating if the flashcard has been marked as learned.
        last_studied (datetime, optional): Timestamp when the flashcard was last reviewed.
        times_reviewed (int): Count of how many times the flashcard has been reviewed.
    """
    __tablename__ = "flashcards"

    card_id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    type = Column(String(50), nullable=True)
    note_id = Column(Integer, ForeignKey("notes.note_id"), nullable=True)
    learned = Column(Boolean, default=False)
    last_studied = Column(DateTime, nullable=True)
    times_reviewed = Column(Integer, default=0)

    note = relationship("Note", back_populates="flashcards")
    quizzes = relationship("Quiz", back_populates="flashcard", cascade="all, delete-orphan")
    scores = relationship("Score", back_populates="flashcard", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Flashcard(card_id={self.card_id}, question={self.question})>"

