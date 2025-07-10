import os
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    SECRET_KEY = os.getenv("SECRET_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL")

    NOTE_TITLE_MAX_LENGTH = 100
    NOTE_CONTENT_MAX_LENGTH = 1000

    UTC = timezone.utc

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False