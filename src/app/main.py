from src.app import create_app
from src.data.db import init_db

app = create_app()

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
    print("Database initialized and tables created.")
