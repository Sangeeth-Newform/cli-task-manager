"""
Data model for a single Task.

This module defines the Task entity and its related enums.
It has NO knowledge of files, JSON, or the CLI — it only knows
how to represent a task and convert itself to/from a plain dict.
"""

from __future__ import (
    annotations,  # allows using "Task" as a type hint inside the Task class itself
)

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4


class TaskStatus(StrEnum):
    """
    The lifecycle states a task can be in.

    Inherits from `str` as well as `Enum` so that TaskStatus.PENDING
    behaves like the string "pending" when saved to JSON or printed —
    this makes serialization trivial (no custom encoder needed).
    """

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TaskPriority(StrEnum):
    """The urgency level of a task. Same str+Enum trick as TaskStatus."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class Task:
    """
    Represents a single task in the task manager.

    Using @dataclass auto-generates __init__, __repr__, and __eq__
    based on the fields below, so we don't write that boilerplate by hand.
    """

    title: str
    description: str | None = None
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM

    # default_factory is used (not a plain default) because uuid4() and
    # datetime.now() must be called FRESH for every new Task instance —
    # a plain default would be computed once and shared by every task (a classic Python gotcha).
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def mark_updated(self) -> None:
        """Call this any time a task's fields change, to refresh its timestamp."""
        self.updated_at = datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert this Task into a plain dict of JSON-safe primitives.

        Enums become their .value (plain string), and datetimes become
        ISO-8601 strings (e.g. "2026-09-15T10:30:00+00:00") — the
        standard, unambiguous, human-readable timestamp format.
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Task:
        """
        Reconstruct a Task from a plain dict (the reverse of to_dict()).

        This is a classmethod (takes `cls`, not `self`) because it builds
        a NEW Task rather than operating on an existing one — this is the
        standard Python pattern for an "alternate constructor."
        """
        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description"),
            status=TaskStatus(data["status"]),
            priority=TaskPriority(data["priority"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )
