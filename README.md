## Bookstore Inventory API

This project is a small REST API for managing a bookstore's inventory, built with Flask and SQLite. It exposes endpoints for managing authors and books, including support for basic CRUD operations and simple querying.

The codebase is intentionally straightforward and suitable for developers with 1–2 years of Python experience. It uses direct SQL queries via `sqlite3` (no ORM) and keeps a clear separation of concerns between routes, models, database utilities, and helper functions.

---

### Features

- Manage authors (create, list, retrieve)
- Manage books (create, list, retrieve, update, delete)
- Input validation for book and author payloads
- Safe, parameterized SQL queries to prevent SQL injection
- Simple SQLite database with automatic initialization
- Utility functions covered by pytest unit tests

---

### Project Structure

```text
.
├── app.py              # Flask application and HTTP route handlers
├── config.py           # Basic configuration (database path)
├── db.py               # Database connection and initialization helpers
├── models.py           # Dataclasses for Author and Book
├── utils.py            # Validation and formatting helpers
├── requirements.txt    # Python dependencies
├── pytest.ini          # pytest configuration
├── tests/
│   ├── __init__.py
│   └── test_utils.py  # Unit tests for utility functions
└── README.md
```

---

### Requirements

- Python 3.9+
- pip (Python package manager)

---

### Setup & Installation

1. **Clone the repository** (or copy the files into a project directory).

2. **Create and activate a virtual environment** (recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate      # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:

   ```bash
   export FLASK_APP=app.py       # On Windows: set FLASK_APP=app.py
   flask run                     # Or: python app.py
   ```

   By default, the app starts on `http://127.0.0.1:5000`.

5. **Database initialization**:

   The SQLite database is initialized automatically on the first request. It creates `authors` and `books` tables if they do not already exist.

   The database file is stored at `bookstore.db` in the project root by default. You can override this with the `BOOKSTORE_DB_PATH` environment variable.

---

### API Overview

#### Health Check

- `GET /health`

  Returns a simple JSON payload indicating that the service is running.

#### Authors

- `GET /authors`

  List all authors.

- `GET /authors/<id>`

  Retrieve a single author by ID.

- `POST /authors`

  Create a new author.

  **Request body (JSON):**

  ```json
  {
    "name": "Jane Austen",
    "biography": "English novelist known for..."  // optional
  }
  ```

#### Books

- `GET /books`

  List books. Supports optional query parameters:

  - `author_id` – filter by author ID
  - `q` – case-insensitive search in book title

- `GET /books/<id>`

  Retrieve a single book by ID.

- `POST /books`

  Create a new book.

  **Request body (JSON):**

  ```json
  {
    "title": "Pride and Prejudice",
    "author_id": 1,
    "isbn": "9780141199078",   // optional
    "quantity": 5,              // optional, defaults to 0 if omitted
    "price": 14.99              // optional, defaults to 0.0 if omitted
  }
  ```

  - `title` and `author_id` are required.
  - `quantity` and `price` are optional, and default to `0` and `0.0` respectively if not provided in a full payload.

- `PATCH /books/<id>`

  Partially update a book. Only the provided fields are validated and updated.

  **Request body (JSON):** any subset of these fields:

  ```json
  {
    "title": "New Title",   // optional
    "author_id": 2,          // optional
    "isbn": "1234567890",   // optional
    "quantity": 10,          // optional
    "price": 19.99           // optional
  }
  ```

- `DELETE /books/<id>`

  Delete a book by ID.

---

### Validation Behavior

Book payloads are validated by `utils.validate_book_payload`:

- For **full payloads** (e.g. `POST /books`):
  - `title` (non-empty string) and `author_id` (positive integer) are required.
  - `isbn` is optional; if provided, it is converted to a trimmed string.
  - `quantity` is optional; if omitted, it defaults to `0`. If provided, it must be a non-negative integer.
  - `price` is optional; if omitted, it defaults to `0.0`. If provided, it must be a non-negative number.

- For **partial payloads** (e.g. `PATCH /books/<id>`):
  - No fields are required.
  - Only fields that are present are validated and returned.
  - At least one valid field must be provided; otherwise the update is rejected.

This behavior is covered by the unit tests in `tests/test_utils.py` and ensures that minimal full-payload inputs are handled gracefully while still enforcing reasonable constraints.

---

### Running Tests

With the virtual environment activated and dependencies installed, run:

```bash
pytest
```

This will run the tests defined in the `tests/` directory, focusing on the validation and formatting utilities.

---

### Configuration

Configuration is intentionally minimal:

- `BOOKSTORE_DB_PATH` – optional environment variable that sets the path to the SQLite database file. If not set, the default is `bookstore.db` in the project root.

You can set it before running the app:

```bash
export BOOKSTORE_DB_PATH=/tmp/bookstore.db
flask run
```

---

### Notes

- Error responses are returned as JSON with an `error` field and appropriate HTTP status codes.
- All SQL queries use parameterized placeholders (`?`) to avoid SQL injection.
- The code targets clarity and maintainability over advanced patterns, making it a solid baseline for future improvements.
