from datetime import datetime
from sqlalchemy import and_

from sqlalchemy.orm import Session

from src.data.models import Note, Score
from src.config.config import Config
from src.data.models.quizzes import Quiz
from src.data.models.flashcards import Flashcard
from src.utils.llm_api import check_user_answer_with_llm



class QuizService:
    def __init__(self, db_session: Session):
        """
        Initializes the QuizService with a given database session.

        Args:
            db_session (Session): SQLAlchemy database session.
        """
        self.db = db_session

    def start_or_get_active_quiz(self, user_id: int, note_id: int) -> Quiz:
        """
        Finds an active quiz session for the user and note or creates a new one.

        Args:
            user_id (int): ID of the current user.
            note_id (int): ID of the note for which to start or get a quiz.

        Returns:
            Quiz: An active Quiz instance.
        """
        quiz = (
            self.db.query(Quiz)
            .filter(and_(Quiz.user_id == user_id, Quiz.note_id == note_id, Quiz.completed.is_(False)))
            .order_by(Quiz.created_at.desc())
            .first()
        )
        if quiz:
            return quiz # type: ignore

        quiz = Quiz(user_id=user_id, note_id=note_id, completed=False, created_at=Config.UTC)
        self.db.add(quiz)
        self.db.commit()
        self.db.refresh(quiz)
        return quiz

    def get_flashcards_for_quiz(self, user_id: int, note_id: int) -> list[dict]:
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
            .join(Flashcard.note)
            .filter(and_(Flashcard.note_id == note_id, Note.user_id == user_id))
            .all()
        )
        return [{"card_id": fc.card_id, "question": fc.question, "type": fc.type or "text"} for fc in flashcards]

    def get_next_flashcard_for_quiz(self, quiz_id: int, note_id: int) -> dict | None:
        """
        Returns the next flashcard that has not yet been answered in the given quiz.

        Args:
            quiz_id (int): ID of the quiz session.
            note_id (int): ID of the note from which to fetch flashcards.

        Returns:
            dict | None: The next flashcard as a dict with keys 'card_id', 'question', 'type', or None if all are answered.
        """
        answered_card_ids = (
            self.db.query(Score.card_id)
            .filter(and_(Score.quiz_id == quiz_id))
            .all()
        )
        answered_card_ids = {c[0] for c in answered_card_ids}

        all_flashcards = (
            self.db.query(Flashcard)
            .filter(and_(Flashcard.note_id == note_id))
            .all()
        )

        for card in all_flashcards:
            if card.card_id not in answered_card_ids:
                return {
                    "card_id": card.card_id,
                    "question": card.question,
                    "type": card.type or "text",
                }
        return None

    def submit_answer(self, user_id: int, quiz_id: int, card_id: int, user_answer: str) -> dict:
        """
        Submits a user's answer for a flashcard question and evaluates it using the LLM.

        Args:
            user_id (int): ID of the current user.
            quiz_id (int): ID of the quiz session.
            card_id (int): ID of the flashcard being answered.
            user_answer (str): The answer submitted by the user.

        Returns:
            dict: Feedback from the LLM evaluation on the user's answer.

        Raises:
            ValueError: If the flashcard or quiz session is not found.
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

        quiz = self.db.query(Quiz).filter_by(quiz_id=quiz_id).first()
        if not quiz:
            raise ValueError("Quiz session not found")

        quiz.answer = user_answer
        quiz.ai_feedback = feedback.get("evaluation", "")
        quiz.answered = True

        self.db.add(quiz)
        self.db.commit()

        return feedback

    def save_user_answer(self, quiz_id: int, card_id: int, correct: bool):
        """
        Saves the correctness of a user's answer to the database.

        Args:
            quiz_id (int): ID of the quiz session.
            card_id (int): ID of the flashcard.
            correct (bool): Whether the user's answer was correct.
        """
        score = Score(
            quiz_id=quiz_id,
            card_id=card_id,
            checked_answer=correct,
            answered=Config.UTC
        )
        self.db.add(score)
        self.db.commit()

    def get_progress(self, user_id: int, note_id: int) -> dict:
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
