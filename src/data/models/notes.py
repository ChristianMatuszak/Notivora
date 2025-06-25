from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from datetime import datetime, UTC

from src.data.db import Base

class Note(Base):
    """
    Represents a user-created note and its AI-generated summary.

    Attributes:
        note_id (int): Primary key identifier for the note.
        original (str): The original text content provided by the user.
        ai_summary (str): AI-generated summary of the original content.
        created_at (datetime): Timestamp indicating when the note was created.
        user_id (int): Foreign key referencing the associated user.
        language (str): Language of the note content, default is "en".
    """
    __tablename__ = "notes"

    note_id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=True)
    original = Column(Text, nullable=False)
    ai_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now(UTC), nullable=False)
    language = Column(String, nullable=True, default="en")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    user = relationship("User", back_populates="notes")
    flashcards = relationship("Flashcard", back_populates="note")

    def __repr__(self):
        return f"<Note(note_id={self.note_id}, user_id={self.user_id})>"