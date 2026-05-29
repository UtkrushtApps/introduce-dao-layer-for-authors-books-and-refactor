import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

# Path to the SQLite database file. Can be overridden with the
# BOOKSTORE_DB_PATH environment variable.
DATABASE_PATH = os.getenv("BOOKSTORE_DB_PATH", str(BASE_DIR / "bookstore.db"))
