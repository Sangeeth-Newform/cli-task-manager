Step 1
mkdir cli-task-manager
cd cli-task-manager

uv --version
uv python install 3.12
uv python pin 3.12

uv init --package --name task-manager .

mkdir tests
type nul > tests\__init__.py
type nul > tests\test_task_manager.py
type nul > src\task_manager\models.py
type nul > src\task_manager\task_manager.py
type nul > src\task_manager\cli.py

tree /F

git init
git add .
git commit -m "chore: initial project scaffold with uv and pyproject.toml"

git log --oneline
git status


Step 2: The Task Model (models.py)
Why we're doing this before anything else

The Task is the atomic unit of our entire application — the CLI, the manager, and the JSON file all revolve around it. Get this model right, and everything above it becomes easy. Get it wrong, and you'll be refactoring every layer later. So we spend real care here.

Key design decisions (and why, since you're on probation and reviewers will ask "why," not just "what")
1. dataclass instead of a plain class

A plain class needs a hand-written __init__ for every field, plus manual __repr__ and __eq__ if you want readable debugging and comparisons. @dataclass generates all of that for you from type-annotated fields. It's still 100% OOP — just less boilerplate for the same rigor.

2. Enum for status and priority — not raw strings

If we used a raw string like task.status = "compelted" (typo), Python won't complain — it'll just silently store a wrong value, and your list --status completed filter will quietly miss that task. With an Enum, TaskStatus.COMPELTED would fail immediately at the point of the typo, because that name doesn't exist. This is called "making illegal states unrepresentable" — a core idea in typed software design.

3. uuid.uuid4() for IDs, not auto-incrementing integers

Auto-increment (1, 2, 3...) requires a central counter, which gets complicated once multiple people or processes touch the file. A uuid4() is generated locally, is virtually guaranteed unique, and needs no coordination. It's the standard choice for local-first tools like this.

4. datetime with timezone-aware timestamps

A very common junior mistake is datetime.now(), which returns a "naive" datetime with no timezone attached — this causes subtle bugs the moment your data is compared across machines or timezones. We'll use datetime.now(timezone.utc) everywhere, so every timestamp is unambiguous.

5. to_dict() / from_dict() as the only serialization boundary

The Task object itself never touches JSON or files directly — that's the TaskManager's job (Step 3). to_dict()/from_dict() are the translation layer between "a rich Python object with Enums and datetimes" and "a flat dictionary that json.dump can actually write to disk." Keeping this boundary explicit and in one place means if we ever swap JSON for SQLite later, only this one boundary changes — nothing else in the app needs to know.

Code: src/task_manager/models.py


"""
Data model for a single Task.

This module defines the Task entity and its related enums.
It has NO knowledge of files, JSON, or the CLI — it only knows
how to represent a task and convert itself to/from a plain dict.
"""

from __future__ import annotations  # allows using "Task" as a type hint inside the Task class itself

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4


class TaskStatus(str, Enum):
    """
    The lifecycle states a task can be in.

    Inherits from `str` as well as `Enum` so that TaskStatus.PENDING
    behaves like the string "pending" when saved to JSON or printed —
    this makes serialization trivial (no custom encoder needed).
    """
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TaskPriority(str, Enum):
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
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM

    # default_factory is used (not a plain default) because uuid4() and
    # datetime.now() must be called FRESH for every new Task instance —
    # a plain default would be computed once and shared by every task (a classic Python gotcha).
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def mark_updated(self) -> None:
        """Call this any time a task's fields change, to refresh its timestamp."""
        self.updated_at = datetime.now(timezone.utc)

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

        