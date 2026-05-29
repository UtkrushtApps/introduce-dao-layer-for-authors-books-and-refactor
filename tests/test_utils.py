import pytest

from utils import (
    ValidationError,
    format_author_record,
    format_book_record,
    validate_author_payload,
    validate_book_payload,
)


class TestValidateAuthorPayload:
    def test_valid_author_payload(self) -> None:
        payload = {"name": "Jane Austen", "biography": "English novelist"}
        result = validate_author_payload(payload)
        assert result["name"] == "Jane Austen"
        assert result["biography"] == "English novelist"

    def test_author_requires_name(self) -> None:
        payload = {"biography": "Missing name"}
        with pytest.raises(ValidationError) as exc:
            validate_author_payload(payload)
        assert "Field 'name' is required" in str(exc.value)

    def test_author_unknown_field_rejected(self) -> None:
        payload = {"name": "Author", "unknown": "field"}
        with pytest.raises(ValidationError) as exc:
            validate_author_payload(payload)
        assert "Unknown field(s): unknown" in str(exc.value)


class TestValidateBookPayloadFull:
    def test_full_payload_with_required_fields_only_uses_defaults(self) -> None:
        payload = {"title": "Test Book", "author_id": 1}
        result = validate_book_payload(payload, partial=False)
        assert result["title"] == "Test Book"
        assert result["author_id"] == 1
        # Optional fields should default
        assert result["quantity"] == 0
        assert result["price"] == 0.0
        # isbn was not provided
        assert "isbn" not in result

    def test_full_payload_with_all_fields(self) -> None:
        payload = {
            "title": "Complete Book",
            "author_id": 2,
            "isbn": "1234567890",
            "quantity": 10,
            "price": 19.99,
        }
        result = validate_book_payload(payload, partial=False)
        assert result["title"] == "Complete Book"
        assert result["author_id"] == 2
        assert result["isbn"] == "1234567890"
        assert result["quantity"] == 10
        assert result["price"] == pytest.approx(19.99)

    def test_full_payload_missing_required_field(self) -> None:
        payload = {"title": "No Author"}
        with pytest.raises(ValidationError) as exc:
            validate_book_payload(payload, partial=False)
        assert "Field 'author_id' is required" in str(exc.value)

    def test_full_payload_with_negative_quantity_rejected(self) -> None:
        payload = {"title": "Bad Quantity", "author_id": 1, "quantity": -1}
        with pytest.raises(ValidationError) as exc:
            validate_book_payload(payload, partial=False)
        assert "must be non-negative" in str(exc.value)

    def test_full_payload_with_negative_price_rejected(self) -> None:
        payload = {"title": "Bad Price", "author_id": 1, "price": -0.01}
        with pytest.raises(ValidationError) as exc:
            validate_book_payload(payload, partial=False)
        assert "must be non-negative" in str(exc.value)


class TestValidateBookPayloadPartial:
    def test_partial_payload_updates_only_provided_fields(self) -> None:
        payload = {"quantity": 5}
        result = validate_book_payload(payload, partial=True)
        assert result == {"quantity": 5}

    def test_partial_payload_rejects_empty_body(self) -> None:
        with pytest.raises(ValidationError) as exc:
            validate_book_payload({}, partial=True)
        assert "No valid fields provided for update" in str(exc.value)

    def test_partial_payload_unknown_field_rejected(self) -> None:
        payload = {"unknown": "value"}
        with pytest.raises(ValidationError) as exc:
            validate_book_payload(payload, partial=True)
        assert "Unknown field(s): unknown" in str(exc.value)

    def test_partial_payload_type_validation(self) -> None:
        payload = {"quantity": "not-an-int"}
        with pytest.raises(ValidationError) as exc:
            validate_book_payload(payload, partial=True)
        assert "must be an integer" in str(exc.value)


class TestFormatRecordHelpers:
    def test_format_author_record(self) -> None:
        row = {"id": 1, "name": "Author", "biography": "Bio", "created_at": "ts"}
        formatted = format_author_record(row)
        assert formatted == row

    def test_format_book_record(self) -> None:
        row = {
            "id": 1,
            "title": "Book",
            "author_id": 2,
            "isbn": "123",
            "quantity": 3,
            "price": 9.99,
            "created_at": "ts",
        }
        formatted = format_book_record(row)
        assert formatted == row
