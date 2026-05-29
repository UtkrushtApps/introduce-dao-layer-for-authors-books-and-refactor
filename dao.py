import json
import sqlite3
from typing import Any, Dict, List, Optional


class AuthorDAO:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def get_all(self) -> List[sqlite3.Row]:
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT id, name, biography, created_at FROM authors ORDER BY name ASC"
        )
        return cursor.fetchall()

    def get_by_id(self, author_id: int) -> Optional[sqlite3.Row]:
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT id, name, biography, created_at FROM authors WHERE id = ?",
            (author_id,),
        )
        return cursor.fetchone()

    def create(self, data: Dict[str, Any]) -> sqlite3.Row:
        cursor = self._conn.cursor()
        cursor.execute(
            "INSERT INTO authors (name, biography) VALUES (?, ?)",
            (data.get("name"), data.get("biography")),
        )
        self._conn.commit()
        author_id = cursor.lastrowid
        cursor.execute(
            "SELECT id, name, biography, created_at FROM authors WHERE id = ?",
            (author_id,),
        )
        return cursor.fetchone()

    def update(self, author_id: int, data: Dict[str, Any]) -> Optional[sqlite3.Row]:
        set_clauses: List[str] = []
        params: List[Any] = []

        if "name" in data:
            set_clauses.append("name = ?")
            params.append(data["name"])
        if "biography" in data:
            set_clauses.append("biography = ?")
            params.append(data["biography"])

        if not set_clauses:
            return self.get_by_id(author_id)

        params.append(author_id)
        sql = f"UPDATE authors SET {', '.join(set_clauses)} WHERE id = ?"

        cursor = self._conn.cursor()
        cursor.execute(sql, params)
        self._conn.commit()

        return self.get_by_id(author_id)

    def delete(self, author_id: int) -> None:
        cursor = self._conn.cursor()
        cursor.execute("DELETE FROM authors WHERE id = ?", (author_id,))
        self._conn.commit()


class BookDAO:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def get_all(
        self,
        author_id: Optional[int] = None,
        query: Optional[str] = None,
    ) -> List[sqlite3.Row]:
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

        cursor = self._conn.cursor()
        cursor.execute(sql, params)

        # NOTE: currently only returns the first row instead of all matches
        first_row = cursor.fetchone()
        if first_row is None:
            return []
        return [first_row]

    def get_by_id(self, book_id: int) -> Optional[sqlite3.Row]:
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT id, title, author_id, isbn, quantity, price, created_at "
            "FROM books WHERE id = ?",
            (book_id,),
        )
        return cursor.fetchone()

    def create(self, data: Dict[str, Any]) -> sqlite3.Row:
        title = data["title"]
        author_id = data["author_id"]
        isbn = data.get("isbn")
        quantity = data.get("quantity", 0)
        price = data.get("price", 0.0)

        if isbn is None:
            isbn_literal = "NULL"
        else:
            isbn_literal = f"'{isbn}'"

        # Build the INSERT using string interpolation for now
        sql = (
            "INSERT INTO books (title, author_id, isbn, quantity, price) "
            f"VALUES ('{title}', {author_id}, {isbn_literal}, {quantity}, {price})"
        )

        cursor = self._conn.cursor()
        cursor.execute(sql)
        self._conn.commit()

        book_id = cursor.lastrowid
        cursor.execute(
            "SELECT id, title, author_id, isbn, quantity, price, created_at "
            "FROM books WHERE id = ?",
            (book_id,),
        )
        return cursor.fetchone()

    def update(self, book_id: int, data: Dict[str, Any]) -> None:
        set_clauses: List[str] = []
        params: List[Any] = []

        for field in ("title", "author_id", "isbn", "quantity", "price"):
            if field in data:
                set_clauses.append(f"{field} = ?")
                params.append(data[field])

        if not set_clauses:
            return None

        params.append(book_id)
        sql = f"UPDATE books SET {', '.join(set_clauses)} WHERE id = ?"

        cursor = self._conn.cursor()
        cursor.execute(sql, params)
        self._conn.commit()

        # Intentionally not returning the updated row here

    def delete(self, book_id: int) -> None:
        cursor = self._conn.cursor()
        cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
        self._conn.commit()
