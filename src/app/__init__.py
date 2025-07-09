import logging
from flask_login import LoginManager
from flask import Flask, current_app

from src.data.models import User
from src.app.routes.quiz import quiz_bp
from src.app.routes.llm import llm_bp
from src.app.routes.note import note_bp
from src.app.routes.ping import ping_bp
from src.app.routes.user import user_bp
from src.data.db import get_engine, init_db, get_session_local

login_manager = LoginManager()

def create_app(config_class, log_file='app.log'):
    """
    Application factory function for creating and configuring a Flask app instance.

    This function:
    - Loads environment variables using `dotenv`
    - Initializes the Flask app and loads configuration from a Config class
    - Sets up the SQLAlchemy engine and session handling based on the config
    - Initializes Flask-Login
    - Registers all application blueprints (ping, user, llm, note) — add them where indicated
    - Configures basic logging to a file

    If required configuration values (`SECRET_KEY`, `DATABASE_URL`) are missing,
    a `ValueError` is raised. Any other exception during initialization is logged
    and results in the function returning `None`.

    Args:
        config_class (class): A Config class (e.g., DevelopmentConfig or ProductionConfig)
        log_file (str): Name of the file where logs should be written. Defaults to `'app.log'`.

    Returns:
        Flask or None: A configured Flask application instance, or `None` if initialization fails.
    """

    try:

        app = Flask(__name__)
        app.config.from_object(config_class)

        if not app.config.get("SECRET_KEY"):
            raise ValueError("SECRET_KEY is not set!")
        if not app.config.get("DATABASE_URL"):
            raise ValueError("DATABASE_URL is not set!")

        engine = get_engine(app.config["DATABASE_URL"])
        init_db(engine)

        app.config['ENGINE'] = engine
        app.config['SESSION_LOCAL'] = get_session_local(engine)

        login_manager.init_app(app)

        @login_manager.user_loader
        def load_user(user_id):
            session = current_app.config['SESSION_LOCAL']()
            try:
                return session.query(User).get(int(user_id))
            finally:
                session.close()

        app.register_blueprint(ping_bp)
        app.register_blueprint(user_bp)
        app.register_blueprint(llm_bp)
        app.register_blueprint(note_bp)
        app.register_blueprint(quiz_bp)

        logging.basicConfig(
            filename=log_file,
            level=logging.ERROR,
            format='%(asctime)s %(levelname)s: %(message)s'
        )

        return app

    except Exception as error:
        logging.error("Error while creating app", exc_info=error)
        return None
