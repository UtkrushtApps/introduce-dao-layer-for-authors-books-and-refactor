import sqlite3
from typing import Any, Dict, List, Optional

from flask import Flask, jsonify, request

from dao import AuthorDAO, BookDAO
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
        author_dao = AuthorDAO(conn)
        rows = author_dao.get_all()
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
        author_dao = AuthorDAO(conn)
        row = author_dao.get_by_id(author_id)
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
        author_dao = AuthorDAO(conn)
        row = author_dao.create(validated)
        author = format_author_record(row)
        return jsonify(author), 201
    except sqlite3.Error:
        return jsonify({"error": "Database error while creating author"}), 500
    finally:
        close_connection(conn)


@app.route("/authors/<int:author_id>", methods=["DELETE"])
def delete_author(author_id: int) -> Any:
    conn: Optional[sqlite3.Connection] = None
    try:
        conn = get_connection()
        author_dao = AuthorDAO(conn)

        row = author_dao.get_by_id(author_id)
        if row is None:
            return jsonify({"error": "Author not found"}), 404

        author_dao.delete(author_id)
        return jsonify({"status": "deleted"}), 200
    except sqlite3.Error:
        return jsonify({"error": "Database error while deleting author"}), 500
    finally:
        close_connection(conn)


# -------------------------- Book Endpoints --------------------------


@app.route("/books", methods=["GET"])
def list_books() -> Any:
    author_id = request.args.get("author_id")
    query = request.args.get("q")

    conn: Optional[sqlite3.Connection] = None
    try:
        conn = get_connection()
        book_dao = BookDAO(conn)
        rows = book_dao.get_all(author_id=author_id, query=query)
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
        book_dao = BookDAO(conn)
        row = book_dao.get_by_id(book_id)
        if row is None:
            return jsonify({"error": "Book not found"}), 404

        book = format_book_record(row)
        return jsonify(book)
    except sqlite3.Error:
        return jsonify({"error": "Database error while fetching book"}), 500
    finally:
        close_connection(conn)


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
        author_dao = AuthorDAO(conn)
        if author_dao.get_by_id(validated["author_id"]) is None:
            return jsonify({"error": "Author does not exist"}), 400

        book_dao = BookDAO(conn)
        row = book_dao.create(validated)
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
        book_dao = BookDAO(conn)
        existing = book_dao.get_by_id(book_id)
        if existing is None:
            return jsonify({"error": "Book not found"}), 404

        if "author_id" in validated:
            author_dao = AuthorDAO(conn)
            if author_dao.get_by_id(validated["author_id"]) is None:
                return jsonify({"error": "Author does not exist"}), 400

        updated_book = book_dao.update(book_id, validated)
        return jsonify(updated_book)
    except sqlite3.Error:
        return jsonify({"error": "Database error while updating book"}), 500
    finally:
        close_connection(conn)


@app.route("/books/<int:book_id>", methods=["DELETE"])
def delete_book(book_id: int) -> Any:
    conn: Optional[sqlite3.Connection] = None
    try:
        conn = get_connection()
        book_dao = BookDAO(conn)

        existing = book_dao.get_by_id(book_id)
        if existing is None:
            return jsonify({"error": "Book not found"}), 404

        book_dao.delete(book_id)
        return jsonify({"status": "deleted"}), 200
    except sqlite3.Error:
        return jsonify({"error": "Database error while deleting book"}), 500
    finally:
        close_connection(conn)


if __name__ == "__main__":
    # Running directly with `python app.py` is convenient during development.
    app.run(host="0.0.0.0", port=5000, debug=True)
