from dataclasses import dataclass
from typing import Optional


@dataclass
class Author:
    """Dataclass representing an author record."""

    id: Optional[int]
    name: str
    biography: Optional[str] = None


@dataclass
class Book:
    """Dataclass representing a book record."""

    id: Optional[int]
    title: str
    author_id: int
    isbn: Optional[str] = None
    quantity: int = 0
    price: float = 0.0
