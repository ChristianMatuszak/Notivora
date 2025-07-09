from sqlalchemy import and_

from src.data.models.quizzes import Quiz
from src.data.models.flashcards import Flashcard
from sqlalchemy.orm import Session
from src.utils.llm_api import check_user_answer_with_llm

class QuizService:
    def __init__(self, db_session: Session):
        """
        Initializes the QuizService with a given database session.

        Args:
            db_session (Session): SQLAlchemy database session.
        """
        self.db = db_session

    def get_flashcards_for_quiz(self, user_id: int, note_id: int):
        """
        Retrieves all flashcards for a specific note to build a quiz.

        Args:
            user_id (int): ID of the current user.
            note_id (int): ID of the note to fetch flashcards from.

        Returns:
            list[dict]: A list of flashcards with their card_id, question, and type.
        """
        flashcards = (
            self.db.query(Flashcard)
            .filter_by(note_id=note_id)
            .all()
        )
        return [{"card_id": fc.card_id, "question": fc.question, "type": fc.type or "text"} for fc in flashcards]

    def submit_answer(self, user_id: int, card_id: int, user_answer: str) -> dict:
        """
        Submits a user's answer for a flashcard question and evaluates it using the LLM.

        Args:
            user_id (int): ID of the current user.
            card_id (int): ID of the flashcard being answered.
            user_answer (str): The answer submitted by the user.

        Returns:
            dict: Feedback from the LLM evaluation on the user's answer.

        Raises:
            ValueError: If the flashcard is not found.
        """
        flashcard = self.db.query(Flashcard).filter_by(card_id=card_id).first()
        if not flashcard:
            raise ValueError("Flashcard not found")

        language = flashcard.note.language if flashcard.note else "en"

        feedback = check_user_answer_with_llm(
            flashcard.question,
            flashcard.answer,
            user_answer,
            language
        )

        quiz = Quiz(
            user_id=user_id,
            card_id=card_id,
            answer=user_answer,
            ai_feedback=feedback.get("result", ""),
            answered=True
        )
        self.db.add(quiz)
        self.db.commit()

        return feedback

    def get_progress(self, user_id: int, note_id: int):
        """
        Calculates quiz progress for a user on a given note.

        Args:
            user_id (int): ID of the current user.
            note_id (int): ID of the note.

        Returns:
            dict: Contains total flashcards, answered flashcards, and progress percentage.
        """
        total = (
            self.db.query(Flashcard)
            .filter_by(note_id=note_id)
            .count()
        )
        answered = (
            self.db.query(Quiz)
            .join(Quiz.flashcard)
            .filter(and_(
                Quiz.user_id == user_id,
                Flashcard.note_id == note_id,
                Quiz.answered.is_(True)
            ))
            .count()
        )
        return {
            "total_flashcards": total,
            "answered_flashcards": answered,
            "progress_percent": round((answered / total * 100), 2) if total else 0
        }
