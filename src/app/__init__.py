import logging
import os
from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager
from src.app.routes.llm import llm_bp
from src.app.routes.note import note_bp
from src.app.routes.ping import ping_bp
from src.app.routes.user import user_bp
from src.data.db import get_engine, init_db, get_session_local

login_manager = LoginManager()

def create_app(log_file='app.log', database_url=None, testing=False):
    """
    Application factory function for creating and configuring a Flask app instance.

    This function:
    - Loads environment variables using `dotenv`
    - Initializes the Flask app and its secret key
    - Sets up the SQLAlchemy engine and session handling
    - Initializes Flask-Login
    - Registers all application blueprints (ping, user, llm, note)
    - Enables testing and debugging flags if specified
    - Configures basic logging to a file

    If required environment variables (`SECRET_KEY`, `DATABASE_URL`) are missing,
    a `ValueError` is raised. Any other exception during initialization is logged
    and results in the function returning `None`.

    Args:
        log_file (str): Name of the file where logs should be written. Defaults to `'app.log'`.
        database_url (str, optional): Optional override for the database connection URL.
                                      If not provided, it will be loaded from environment variables.
        testing (bool): If True, enables Flask testing and debug mode.

    Returns:
        Flask or None: A configured Flask application instance, or `None` if initialization fails.
    """

    try:
        load_dotenv()

        app = Flask(__name__)

        app.secret_key = os.getenv("SECRET_KEY")
        if not app.secret_key:
            raise ValueError("SECRET_KEY is not set in environment variables!")

        database_url = database_url or os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL is not set in environment variables!")

        engine = get_engine(database_url)
        init_db(engine)

        app.config['ENGINE'] = engine
        app.config['SESSION_LOCAL'] = get_session_local(engine)

        login_manager.init_app(app)

        if testing:
            app.config["TESTING"] = True
            app.config["DEBUG"] = True

        app.register_blueprint(ping_bp)
        app.register_blueprint(user_bp)
        app.register_blueprint(llm_bp)
        app.register_blueprint(note_bp)

        logging.basicConfig(
            filename=log_file,
            level=logging.ERROR,
            format='%(asctime)s %(levelname)s: %(message)s'
        )

        return app

    except Exception as error:
        logging.error("Error while creating app", exc_info=error)
        return None
