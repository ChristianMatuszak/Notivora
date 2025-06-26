from src.data.models.notes import Note
from src.utils.constants import ErrorMessages

class NoteService:
    def __init__(self, session):
        """
        Initializes the NoteService with a database session.

        Args:
            session: A SQLAlchemy session for database operations.
        """
        self.session = session

    def create_note(self, user_id: int, title: str, content: str) -> Note:
        """
        Creates a new note for a user with the given title and content.

        Args:
            user_id (int): The ID of the user owning the note.
            title (str): The title of the note. Must not be empty.
            content (str): The content of the note. Must not be empty.

        Returns:
            Note: The created Note object with its generated ID and data.

        Raises:
            ValueError: If title or content are empty.
            Exception: If database commit fails.
        """
        if not title or not content:
            raise ValueError(ErrorMessages.TITLE_CONTENT_REQUIRED)

        note = Note(
            title=title,
            original=content,
            user_id=user_id
        )

        try:
            self.session.add(note)
            self.session.commit()
            self.session.refresh(note)
            return note
        except Exception as error:
            self.session.rollback()
            raise error

    def get_note_by_id(self, note_id: int, user_id: int) -> Note | None:
        """
        Retrieves a single note by its ID and the owning user ID.

        Args:
            note_id (int): The ID of the requested note.
            user_id (int): The ID of the user who owns the note.

        Returns:
            Note | None: The Note object if found, otherwise None.
        """
        note = self.session.query(Note).filter(
            Note.note_id == note_id,
            Note.user_id == user_id
        ).first()
        return note

    def get_all_notes_for_user(self, user_id: int) -> list[Note]:
        """
        Retrieves all notes belonging to a specific user.

        Args:
            user_id (int): The ID of the user whose notes to retrieve.

        Returns:
            list[Note]: A list of all notes for the user (empty if none).
        """
        return self.session.query(Note).filter(Note.user_id == user_id).all()

    def update_note(self, note_id: int, user_id: int, title: str = None,
                    content: str = None) -> bool:
        """
        Updates the title and/or content of an existing note.

        Args:
            note_id (int): The ID of the note to update.
            user_id (int): The ID of the user who owns the note.
            title (str, optional): New title. If None, title remains unchanged.
            content (str, optional): New content. If None, content remains unchanged.

        Returns:
            bool: True if the note was found and updated, False otherwise.
        """
        note = self.session.query(Note).filter(Note.note_id == note_id,
                                               Note.user_id == user_id).first()
        if not note:
            return False

        if title:
            note.title = title
        if content:
            note.original = content

        self.session.commit()
        return True

    def delete_note(self, note_id: int, user_id: int) -> bool:
        """
        Deletes a note by its ID and owning user ID.

        Args:
            note_id (int): The ID of the note to delete.
            user_id (int): The ID of the user who owns the note.

        Returns:
            bool: True if the note was found and deleted, False otherwise.
        """
        note = self.session.query(Note).filter(Note.note_id == note_id,
                                               Note.user_id == user_id).first()
        if not note:
            return False

        self.session.delete(note)
        self.session.commit()
        return True