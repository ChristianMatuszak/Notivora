import logging
from flask import Flask
from src.app.routes.ping import ping_bp


def create_app(log_file='app.log'):
    try:
        app = Flask(__name__)
        app.register_blueprint(ping_bp)

        logging.basicConfig(
            filename=log_file,
            level=logging.ERROR,
            format='%(asctime)s %(levelname)s: %(message)s'
        )

        return app

    except Exception as error:
        logging.error("Error while creating app", exc_info=error)
        return None