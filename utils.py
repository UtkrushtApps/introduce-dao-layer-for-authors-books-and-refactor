from typing import Any, Dict, Mapping


class ValidationError(ValueError):
    """Custom exception raised when input validation fails."""


def _ensure_dict_payload(payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValidationError("Payload must be a JSON object")
    return payload


def validate_author_payload(payload: Any) -> Dict[str, Any]:
    """Validate and normalize an author payload.

    Expected input (JSON):
    {
        "name": "Required non-empty string",
        "biography": "Optional string"
    }

    Returns a sanitized dict containing the fields to persist.
    Raises ValidationError if the payload is invalid.
    """
    data = _ensure_dict_payload(payload)

    allowed_keys = {"name", "biography"}
    unknown_keys = set(data.keys()) - allowed_keys
    if unknown_keys:
        raise ValidationError(
            f"Unknown field(s): {', '.join(sorted(unknown_keys))}"
        )

    if "name" not in data:
        raise ValidationError("Field 'name' is required")

    name_raw = data.get("name")
    if not isinstance(name_raw, str):
        raise ValidationError("Field 'name' must be a string")

    name = name_raw.strip()
    if not name:
        raise ValidationError("Field 'name' cannot be empty")

    result: Dict[str, Any] = {"name": name}

    if "biography" in data and data["biography"] is not None:
        bio_raw = data["biography"]
        if not isinstance(bio_raw, str):
            raise ValidationError("Field 'biography' must be a string")
        biography = bio_raw.strip()
        result["biography"] = biography if biography else None

    return result


def validate_book_payload(payload: Any, partial: bool = False) -> Dict[str, Any]:
    """Validate and normalize a book payload.

    For full payloads (partial=False), this is typically used when creating a
    book. For partial payloads (partial=True), it is used for PATCH updates.

    Full payload behavior (partial=False):
      - Required: 'title' (non-empty string), 'author_id' (positive int)
      - Optional: 'isbn' (string), 'quantity' (non-negative int, defaults to 0
        if missing), 'price' (non-negative float, defaults to 0.0 if missing)

    Partial payload behavior (partial=True):
      - No required fields.
      - Only provided fields are validated and returned.
      - At least one valid field must be provided.

    Raises ValidationError if validation fails.
    """
    data = _ensure_dict_payload(payload)

    allowed_keys = {"title", "author_id", "isbn", "quantity", "price"}
    unknown_keys = set(data.keys()) - allowed_keys
    if unknown_keys:
        raise ValidationError(
            f"Unknown field(s): {', '.join(sorted(unknown_keys))}"
        )

    result: Dict[str, Any] = {}

    if not partial:
        # For full payloads, enforce required fields.
        required = ["title", "author_id"]
        for field in required:
            if field not in data:
                raise ValidationError(f"Field '{field}' is required")

    # Title
    if "title" in data:
        title_raw = data["title"]
        if not isinstance(title_raw, str):
            raise ValidationError("Field 'title' must be a string")
        title = title_raw.strip()
        if not title:
            raise ValidationError("Field 'title' cannot be empty")
        result["title"] = title
    elif not partial:
        # Full payload but no title was provided (already checked above), this
        # branch is defensive and should not be reachable.
        raise ValidationError("Field 'title' is required")

    # Author ID
    if "author_id" in data:
        author_id_raw = data["author_id"]
        try:
            author_id = int(author_id_raw)
        except (TypeError, ValueError) as exc:
            raise ValidationError("Field 'author_id' must be an integer") from exc
        if author_id <= 0:
            raise ValidationError("Field 'author_id' must be a positive integer")
        result["author_id"] = author_id
    elif not partial:
        raise ValidationError("Field 'author_id' is required")

    # ISBN (optional string)
    if "isbn" in data and data["isbn"] is not None:
        isbn_raw = data["isbn"]
        if not isinstance(isbn_raw, str):
            raise ValidationError("Field 'isbn' must be a string")
        isbn = isbn_raw.strip()
        # Empty string is normalized to None to avoid storing empty values.
        result["isbn"] = isbn or None

    # Quantity (optional non-negative int; defaults for full payloads)
    if "quantity" in data:
        # For both full and partial payloads, an explicit null is treated as
        # "missing" only for full payloads; for partial payloads it is
        # considered invalid because it would not be a meaningful update.
        if data["quantity"] is None:
            if partial:
                raise ValidationError("Field 'quantity' cannot be null")
            # full payload null -> use default
            quantity = 0
        else:
            try:
                quantity = int(data["quantity"])
            except (TypeError, ValueError) as exc:
                raise ValidationError("Field 'quantity' must be an integer") from exc
            if quantity < 0:
                raise ValidationError("Field 'quantity' must be non-negative")
        result["quantity"] = quantity
    elif not partial:
        # Full payload and quantity not provided -> use default
        result["quantity"] = 0

    # Price (optional non-negative float; defaults for full payloads)
    if "price" in data:
        if data["price"] is None:
            if partial:
                raise ValidationError("Field 'price' cannot be null")
            price = 0.0
        else:
            try:
                price = float(data["price"])
            except (TypeError, ValueError) as exc:
                raise ValidationError("Field 'price' must be a number") from exc
            if price < 0:
                raise ValidationError("Field 'price' must be non-negative")
        result["price"] = price
    elif not partial:
        result["price"] = 0.0

    if partial and not result:
        # For partial updates we require that at least one valid field is
        # supplied; otherwise the operation is a no-op.
        raise ValidationError("No valid fields provided for update")

    return result


def format_author_record(row: Mapping[str, Any]) -> Dict[str, Any]:
    """Convert a DB author row into a JSON-serializable dict."""
    return {
        "id": row["id"],
        "name": row["name"],
        "biography": row.get("biography"),
        "created_at": row.get("created_at"),
    }


def format_book_record(row: Mapping[str, Any]) -> Dict[str, Any]:
    """Convert a DB book row into a JSON-serializable dict."""
    return {
        "id": row["id"],
        "title": row["title"],
        "author_id": row["author_id"],
        "isbn": row.get("isbn"),
        "quantity": row.get("quantity"),
        "price": row.get("price"),
        "created_at": row.get("created_at"),
    }
