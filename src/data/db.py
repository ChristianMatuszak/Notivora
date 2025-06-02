from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./app.sqlite"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    import src.data.models.users
    import src.data.models.flashcards
    import src.data.models.notes
    import src.data.models.quizzes
    import src.data.models.scores

    Base.metadata.create_all(bind=engine)