"""Data models and generic utilities."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Optional, TypeVar

# ── Generic Filter Function ───────────────────────────────────────────────────

T = TypeVar("T")


def filter_items(items: list[T], condition: Optional[Callable[[T], bool]] = None) -> list[T]:
    """Filter a list of items using an optional condition."""
    if condition is None:
        return items
    return [item for item in items if condition(item)]


# ── Task Model ────────────────────────────────────────────────────────────────


@dataclass
class Task:
    title: str
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    description: Optional[str] = None
    status: str = "pending"
    priority: str = "medium"
    created_at: str = field(default_factory=lambda: datetime.now(UTC).strftime("%Y-%m-%d %H:%M"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Task:
        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description"),
            status=data.get("status", "pending"),
            priority=data.get("priority", "medium"),
            created_at=data.get("created_at", ""),
        )
