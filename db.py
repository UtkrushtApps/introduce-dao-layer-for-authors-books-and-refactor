import sqlite3
from typing import Optional

from config import DATABASE_PATH


def get_connection() -> sqlite3.Connection:
    """Create and return a new SQLite connection.

    The connection uses `sqlite3.Row` as row factory so rows can be accessed
    like dictionaries by column name.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def close_connection(conn: Optional[sqlite3.Connection]) -> None:
    """Safely close a SQLite connection.

    This helper is defensive and can be called with `None`.
    """
    if conn is not None:
        try:
            conn.close()
        except sqlite3.Error:
            # Intentionally ignore close errors; connection is being discarded.
            pass


def init_db() -> None:
    """Initialize the database schema if it does not already exist.

    Creates the `authors` and `books` tables with a simple relational
    structure suitable for the bookstore domain.
    """
    schema = """
    PRAGMA foreign_keys = ON;

    CREATE TABLE IF NOT EXISTS authors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        biography TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author_id INTEGER NOT NULL,
        isbn TEXT,
        quantity INTEGER NOT NULL DEFAULT 0,
        price REAL NOT NULL DEFAULT 0.0,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE RESTRICT
    );

    CREATE INDEX IF NOT EXISTS idx_books_author_id ON books(author_id);
    CREATE INDEX IF NOT EXISTS idx_books_title ON books(title);
    """

    conn: Optional[sqlite3.Connection] = None
    try:
        conn = get_connection()
        conn.executescript(schema)
        conn.commit()
    finally:
        close_connection(conn)
