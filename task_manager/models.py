"""Data models and generic utilities."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Optional, TypeVar

# Generic filter function

T = TypeVar("T")


def filter_items(items: list[T], condition: Optional[Callable[[T], bool]] = None) -> list[T]:
    """Filter a list of items using an optional condition.

    Args:
        items: The list to filter.
        condition: A function that returns True for items to keep. If None, nothing is removed.

    Returns:
        The items that satisfy the condition, or the original list if no condition is given.

    """
    if condition is None:
        return items
    return [item for item in items if condition(item)]


def validate_title(title: str) -> str:
    """Check that a task title is not blank.

    Args:
        title: The title to check.

    Returns:
        The title without leading and trailing spaces.

    Raises:
        ValueError: If the title is empty or contains only spaces.

    """
    cleaned = title.strip()
    if not cleaned:
        raise ValueError("Task title cannot be blank.")
    return cleaned


class Status(StrEnum):
    """Allowed states of a task."""

    PENDING = "pending"
    COMPLETED = "completed"


class Priority(StrEnum):
    """Allowed priorities of a task."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# Task model


@dataclass
class Task:
    """A single task stored by the task manager.

    Attributes:
        title: Short name of the task.
        id: Unique 8-character identifier, generated automatically.
        description: Optional extra notes.
        status: Current state of the task.
        priority: How important the task is.
        created_at: UTC creation time formatted as "YYYY-MM-DD HH:MM".

    """

    title: str
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    description: Optional[str] = None
    status: Status = Status.PENDING
    priority: Priority = Priority.MEDIUM
    created_at: str = field(default_factory=lambda: datetime.now(UTC).strftime("%Y-%m-%d %H:%M"))

    def __post_init__(self) -> None:
        """Clean the title, convert status and priority to enums and reject invalid values.

        Raises:
            ValueError: If the title is blank, or status or priority is not an allowed value.

        """
        self.title = validate_title(self.title)
        self.status = Status(self.status)
        self.priority = Priority(self.priority)

    def to_dict(self) -> dict[str, Any]:
        """Convert the task to a plain dictionary for JSON storage.

        Returns:
            A dictionary containing every task field.

        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Task:
        """Build a task from a dictionary read from the JSON file.

        Args:
            data: A dictionary with at least the "id" and "title" keys. Other missing
                keys fall back to their default values.

        Returns:
            A new Task instance.

        Raises:
            ValueError: If the title is blank, or the status or priority is not an allowed value.

        """
        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description"),
            status=data.get("status", Status.PENDING),
            priority=data.get("priority", Priority.MEDIUM),
            created_at=data.get("created_at", ""),
        )
