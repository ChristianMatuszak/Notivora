from src.data.models.flashcards import Flashcard

class FlashcardService:
    def __init__(self, session):
        self.session = session

    def save_flashcards(self, note_id: int, flashcards_data: list[dict]) -> None:
        """
        Speichert neue Flashcards für eine Note und löscht vorherige.

        Args:
            note_id (int): ID der Note, zu der die Flashcards gehören.
            flashcards_data (list[dict]): Liste mit Flashcard-Daten (question, answer).

        """
        existing_cards = self.session.query(Flashcard).filter(Flashcard.note_id == note_id).all()
        for card in existing_cards:
            self.session.delete(card)

        for card in flashcards_data:
            flashcard = Flashcard(
                question=card['question'],
                answer=card['answer'],
                type=card.get('type', ''),
                note_id=note_id,
                learned=False,
                last_studied=None,
                times_reviewed=0
            )
            self.session.add(flashcard)

        self.session.commit()

    def get_flashcards_for_note(self, note_id: int) -> list[Flashcard]:
        """
        Liefert alle Flashcards zu einer Note.

        Args:
            note_id (int): Note-ID

        Returns:
            list[Flashcard]: Liste der Flashcards (leer, wenn keine)
        """
        return self.session.query(Flashcard).filter(Flashcard.note_id == note_id).all()

    def delete_flashcards_for_note(self, note_id: int) -> None:
        """
        Löscht alle Flashcards zu einer Note.

        Args:
            note_id (int): Note-ID
        """
        cards = self.session.query(Flashcard).filter(Flashcard.note_id == note_id).all()
        for c in cards:
            self.session.delete(c)
        self.session.commit()
