from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

def get_engine(database_url: str):
    """
    Creates and returns a SQLAlchemy engine for the given database URL.

    The engine is configured to allow connections from multiple threads, which is
    necessary for SQLite in testing environments.

    Args:
        database_url (str): The database connection string.

    Returns:
        Engine: A SQLAlchemy engine instance connected to the specified database.
    """

    return create_engine(database_url, connect_args={"check_same_thread": False})

def get_session_local(engine):
    """
    Creates and returns a configured SQLAlchemy sessionmaker bound to the given engine.

    The sessionmaker disables autocommit and autoflush for explicit control over transactions.

    Args:
        engine (Engine): SQLAlchemy engine to bind the session to.

    Returns:
        sessionmaker: A configured session factory.
    """

    return sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db(engine_to_use):
    """
    Initializes the database schema by importing all model modules and creating their tables.

    This function ensures all ORM models are registered with SQLAlchemy's Base metadata
    before invoking table creation on the provided engine.

    Args:
        engine_to_use (Engine): SQLAlchemy engine used to apply the schema creation.
    """

    import src.data.models.users
    import src.data.models.flashcards
    import src.data.models.notes
    import src.data.models.quizzes
    import src.data.models.scores

    Base.metadata.create_all(bind=engine_to_use)