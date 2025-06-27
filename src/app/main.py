import os

from dotenv import load_dotenv

from src.app import create_app
from src.config.config import DevelopmentConfig, ProductionConfig

load_dotenv()

env = os.getenv("APP_ENV", "development")

if env == "production":
    config_class = ProductionConfig
else:
    config_class = DevelopmentConfig

app = create_app(config_class)

if __name__ == "__main__":
    app.run(debug=app.config['DEBUG'])

