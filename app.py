import sqlite3
from typing import Any, Dict, List, Optional

from flask import Flask, jsonify, request

from db import close_connection, get_connection, init_db
from models import Author, Book
from utils import (
    ValidationError,
    format_author_record,
    format_book_record,
    validate_author_payload,
    validate_book_payload,
)


app = Flask(__name__)


@app.before_first_request
def setup_database() -> None:
    """Initialize the database schema on first request."""
    init_db()


@app.route("/health", methods=["GET"])
def health() -> Any:
    return jsonify({"status": "ok"})


# ------------------------- Author Endpoints -------------------------


@app.route("/authors", methods=["GET"])
def list_authors() -> Any:
    conn: Optional[sqlite3.Connection] = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, biography, created_at FROM authors ORDER BY name ASC"
        )
        rows = cursor.fetchall()
        authors: List[Dict[str, Any]] = [format_author_record(row) for row in rows]
        return jsonify({"authors": authors})
    except sqlite3.Error:
        return jsonify({"error": "Database error while listing authors"}), 500
    finally:
        close_connection(conn)


@app.route("/authors/<int:author_id>", methods=["GET"])
def get_author(author_id: int) -> Any:
    conn: Optional[sqlite3.Connection] = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, biography, created_at FROM authors WHERE id = ?",
            (author_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return jsonify({"error": "Author not found"}), 404

        author = format_author_record(row)
        return jsonify(author)
    except sqlite3.Error:
        return jsonify({"error": "Database error while fetching author"}), 500
    finally:
        close_connection(conn)


@app.route("/authors", methods=["POST"])
def create_author() -> Any:
    try:
        payload = request.get_json(silent=True)
        if payload is None:
            return jsonify({"error": "Request body must be JSON"}), 400

        validated = validate_author_payload(payload)
    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400

    conn: Optional[sqlite3.Connection] = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO authors (name, biography) VALUES (?, ?)",
            (validated.get("name"), validated.get("biography")),
        )
        conn.commit()

        author_id = cursor.lastrowid
        cursor.execute(
            "SELECT id, name, biography, created_at FROM authors WHERE id = ?",
            (author_id,),
        )
        row = cursor.fetchone()
        author = format_author_record(row)
        return jsonify(author), 201
    except sqlite3.Error:
        return jsonify({"error": "Database error while creating author"}), 500
    finally:
        close_connection(conn)


# -------------------------- Book Endpoints --------------------------


@app.route("/books", methods=["GET"])
def list_books() -> Any:
    author_id = request.args.get("author_id")
    query = request.args.get("q")

    sql = (
        "SELECT id, title, author_id, isbn, quantity, price, created_at "
        "FROM books "
    )
    conditions: List[str] = []
    params: List[Any] = []

    if author_id is not None:
        conditions.append("author_id = ?")
        params.append(author_id)

    if query:
        conditions.append("LOWER(title) LIKE ?")
        params.append(f"%{query.lower()}%")

    if conditions:
        sql += "WHERE " + " AND ".join(conditions) + " "

    sql += "ORDER BY created_at DESC, id DESC"

    conn: Optional[sqlite3.Connection] = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        books: List[Dict[str, Any]] = [format_book_record(row) for row in rows]
        return jsonify({"books": books})
    except sqlite3.Error:
        return jsonify({"error": "Database error while listing books"}), 500
    finally:
        close_connection(conn)


@app.route("/books/<int:book_id>", methods=["GET"])
def get_book(book_id: int) -> Any:
    conn: Optional[sqlite3.Connection] = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, title, author_id, isbn, quantity, price, created_at "
            "FROM books WHERE id = ?",
            (book_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return jsonify({"error": "Book not found"}), 404

        book = format_book_record(row)
        return jsonify(book)
    except sqlite3.Error:
        return jsonify({"error": "Database error while fetching book"}), 500
    finally:
        close_connection(conn)


def _author_exists(conn: sqlite3.Connection, author_id: int) -> bool:
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM authors WHERE id = ?", (author_id,))
    return cursor.fetchone() is not None


@app.route("/books", methods=["POST"])
def create_book() -> Any:
    try:
        payload = request.get_json(silent=True)
        if payload is None:
            return jsonify({"error": "Request body must be JSON"}), 400

        validated = validate_book_payload(payload, partial=False)
    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400

    conn: Optional[sqlite3.Connection] = None
    try:
        conn = get_connection()
        if not _author_exists(conn, validated["author_id"]):
            return jsonify({"error": "Author does not exist"}), 400

        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO books (title, author_id, isbn, quantity, price)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                validated.get("title"),
                validated.get("author_id"),
                validated.get("isbn"),
                validated.get("quantity", 0),
                validated.get("price", 0.0),
            ),
        )
        conn.commit()

        book_id = cursor.lastrowid
        cursor.execute(
            "SELECT id, title, author_id, isbn, quantity, price, created_at "
            "FROM books WHERE id = ?",
            (book_id,),
        )
        row = cursor.fetchone()
        book = format_book_record(row)
        return jsonify(book), 201
    except sqlite3.Error:
        return jsonify({"error": "Database error while creating book"}), 500
    finally:
        close_connection(conn)


@app.route("/books/<int:book_id>", methods=["PATCH"])
def update_book(book_id: int) -> Any:
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"error": "Request body must be JSON"}), 400

    try:
        validated = validate_book_payload(payload, partial=True)
    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400

    conn: Optional[sqlite3.Connection] = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Ensure book exists
        cursor.execute("SELECT id FROM books WHERE id = ?", (book_id,))
        if cursor.fetchone() is None:
            return jsonify({"error": "Book not found"}), 404

        # If author_id is being updated, ensure the new author exists
        if "author_id" in validated:
            if not _author_exists(conn, validated["author_id"]):
                return jsonify({"error": "Author does not exist"}), 400

        # Dynamically build the UPDATE statement based on validated keys
        set_clauses: List[str] = []
        params: List[Any] = []
        for field in ("title", "author_id", "isbn", "quantity", "price"):
            if field in validated:
                set_clauses.append(f"{field} = ?")
                params.append(validated[field])

        if not set_clauses:
            return jsonify({"error": "No valid fields provided for update"}), 400

        params.append(book_id)

        sql = f"UPDATE books SET {', '.join(set_clauses)} WHERE id = ?"
        cursor.execute(sql, params)
        conn.commit()

        cursor.execute(
            "SELECT id, title, author_id, isbn, quantity, price, created_at "
            "FROM books WHERE id = ?",
            (book_id,),
        )
        row = cursor.fetchone()
        book = format_book_record(row)
        return jsonify(book)
    except sqlite3.Error:
        return jsonify({"error": "Database error while updating book"}), 500
    finally:
        close_connection(conn)


@app.route("/books/<int:book_id>", methods=["DELETE"])
def delete_book(book_id: int) -> Any:
    conn: Optional[sqlite3.Connection] = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM books WHERE id = ?", (book_id,))
        if cursor.fetchone() is None:
            return jsonify({"error": "Book not found"}), 404

        cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
        conn.commit()
        return jsonify({"status": "deleted"}), 200
    except sqlite3.Error:
        return jsonify({"error": "Database error while deleting book"}), 500
    finally:
        close_connection(conn)


if __name__ == "__main__":
    # Running directly with `python app.py` is convenient during development.
    app.run(host="0.0.0.0", port=5000, debug=True)
