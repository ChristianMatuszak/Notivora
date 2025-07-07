from src.data.models.notes import Note
from src.utils.constants import ErrorMessages

class LLMService:
    def __init__(self, session):
        """
        Initializes the LLMService with a database session.

        Args:
            session: A SQLAlchemy session for performing database operations.
        """
        self.session = session

    def generate_flashcards(self, note_id: int, user_id: int, generate_flashcards_from_summary, flashcard_service) -> None:
        """
        Generates flashcards from the AI summary of a specified note and saves them using the flashcard service.

        Args:
            note_id (int): The ID of the note for which flashcards should be generated.
            user_id (int): The ID of the user owning the note.
            generate_flashcards_from_summary (callable): Function generating flashcards from a summary.
            flashcard_service (FlashcardService): Service to handle flashcard DB operations.

        Raises:
            ValueError: If the note does not exist or no AI summary is available.
        """
        note = self.session.query(Note).filter(Note.note_id == note_id, Note.user_id == user_id).first()
        if not note:
            raise ValueError(ErrorMessages.NOTE_NOT_FOUND)
        if not note.ai_summary:
            raise ValueError(ErrorMessages.NO_SUMMARY_AVAILABLE)

        flashcards_data = generate_flashcards_from_summary(note.ai_summary, note.language)
        if not flashcards_data:
            return

        flashcard_service.save_flashcards(note_id, flashcards_data)
        self.session.commit()

    def generate_summary(self, note_id: int, user_id: int, generate_summary_from_note) -> tuple[
        str, str]:
        """
        Generates an AI summary for the original content of a specified note and updates the note in the database.

        Args:
            note_id (int): The ID of the note to summarize.
            user_id (int): The ID of the user who owns the note.
            generate_summary_from_note (callable): A function that generates a summary and language from note content.

        Returns:
            tuple[str, str]: The generated summary and the detected language.

        Raises:
            ValueError: If the note does not exist or the original content is empty.
        """
        note = self.session.query(Note).filter(Note.note_id == note_id,
                                               Note.user_id == user_id).first()
        if not note:
            raise ValueError(ErrorMessages.NOTE_NOT_FOUND)
        if not note.original:
            raise ValueError(ErrorMessages.EMPTY_NOTE_CONTENT)

        summary, language = generate_summary_from_note(note.original)
        note.ai_summary = summary
        note.language = language
        self.session.commit()

        return summary, language

    def check_answer(self, question: str, correct_answer: str, user_answer: str, language: str,
                     check_user_answer_with_llm) -> dict:
        """
        Evaluates a user's answer against the correct answer using the LLM.

        Args:
            question (str): The original flashcard question.
            correct_answer (str): The expected correct answer.
            user_answer (str): The user's submitted answer.
            language (str): The language of the content for evaluation.
            check_user_answer_with_llm (callable): A function that interfaces with the LLM to evaluate the answer.

        Returns:
            dict: A dictionary containing the evaluation result or feedback.

        Raises:
            ValueError: If any of the required fields are missing.
        """
        if not all([question, correct_answer, user_answer, language]):
            raise ValueError("Missing required fields")
        return check_user_answer_with_llm(question, correct_answer, user_answer, language)