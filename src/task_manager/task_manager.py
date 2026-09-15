"""
TaskManager: the async CRUD engine that owns all task persistence.

This is the ONLY class in the project allowed to read/write the JSON
file directly. Every other layer (CLI, tests) talks to this class,
never to the file on disk.
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from task_manager.models import Task, TaskPriority, TaskStatus

# Default location if the user hasn't set TASK_MANAGER_DB_PATH themselves.
# Path.home() resolves to the user's home directory on any OS
# (e.g. C:\Users\geeth on Windows, /home/geeth on Linux).
DEFAULT_DB_PATH = Path.home() / ".task_manager" / "tasks.json"


class TaskNotFoundError(Exception):
    """Raised when an operation targets a task ID that doesn't exist.

    We raise this instead of silently returning None/False so that a
    caller CANNOT accidentally ignore a failed update/delete/complete —
    Python will crash loudly unless they explicitly handle it.
    """


class TaskManager:
    """
    Owns the full lifecycle of tasks: loading, saving, and all CRUD
    operations. Keeps an in-memory dict as a fast-access cache, and
    writes through to disk on every mutation.
    """

    def __init__(self, db_path: Path | None = None) -> None:
        # Resolution order: explicit constructor arg > env var > default.
        # This lets tests inject a temp path without touching env vars,
        # while normal CLI usage relies on the env var or the default.
        if db_path is not None:
            self.db_path = db_path
        else:
            env_path = os.getenv("TASK_MANAGER_DB_PATH")
            self.db_path = Path(env_path) if env_path else DEFAULT_DB_PATH

        # In-memory cache: task_id -> Task. A dict (not a list) gives us
        # O(1) lookup by ID for update/delete/complete, instead of O(n)
        # scanning through a list every time.
        self._tasks: dict[str, Task] = {}
        self._loaded = False  # tracks whether we've loaded from disk yet

    # ------------------------------------------------------------------
    # Internal persistence helpers (private — leading underscore)
    # ------------------------------------------------------------------

    def _read_file_sync(self) -> list[dict]:
        """
        Blocking, synchronous file read. This is the actual disk I/O.

        It's a plain function (not async) because file I/O in Python's
        standard library is not truly non-blocking — we run THIS
        function inside a background thread via asyncio.to_thread()
        so it doesn't freeze the rest of the program while it runs.
        """
        if not self.db_path.exists():
            return []
        raw_text = self.db_path.read_text(encoding="utf-8")
        if not raw_text.strip():
            return []
        return json.loads(raw_text)

    def _write_file_sync(self, tasks_as_dicts: list[dict]) -> None:
        """Blocking, synchronous file write (same reasoning as above)."""
        # Ensure the parent folder exists (e.g. ~/.task_manager/)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path.write_text(
            json.dumps(tasks_as_dicts, indent=2),
            encoding="utf-8",
        )

    async def _load(self) -> None:
        """Load tasks from disk into the in-memory cache, once."""
        if self._loaded:
            return  # already loaded — avoid redundant disk reads
        raw_list = await asyncio.to_thread(self._read_file_sync)
        self._tasks = {item["id"]: Task.from_dict(item) for item in raw_list}
        self._loaded = True

    async def _save(self) -> None:
        """Persist the current in-memory state to disk."""
        tasks_as_dicts = [task.to_dict() for task in self._tasks.values()]
        await asyncio.to_thread(self._write_file_sync, tasks_as_dicts)

    # ------------------------------------------------------------------
    # Public CRUD API
    # ------------------------------------------------------------------

    async def add_task(
        self,
        title: str,
        description: str | None = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
    ) -> Task:
        """Create a new task, persist it, and return it."""
        await self._load()
        task = Task(title=title, description=description, priority=priority)
        self._tasks[task.id] = task
        await self._save()
        return task

    async def list_tasks(
        self,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        keyword: str | None = None,
    ) -> list[Task]:
        """
        Return tasks, optionally filtered by status, priority, and/or
        a case-insensitive keyword match against the title/description.

        All three filters are optional and combine with AND logic —
        e.g. status=COMPLETED + priority=HIGH returns only tasks
        matching BOTH conditions.
        """
        await self._load()
        results = list(self._tasks.values())

        if status is not None:
            results = [t for t in results if t.status == status]

        if priority is not None:
            results = [t for t in results if t.priority == priority]

        if keyword is not None:
            keyword_lower = keyword.lower()
            results = [
                t for t in results
                if keyword_lower in t.title.lower()
                or (t.description and keyword_lower in t.description.lower())
            ]

        return results

    async def get_task(self, task_id: str) -> Task:
        """Fetch a single task by ID, or raise TaskNotFoundError."""
        await self._load()
        task = self._tasks.get(task_id)
        if task is None:
            raise TaskNotFoundError(f"No task found with id={task_id!r}")
        return task

    async def update_task(
        self,
        task_id: str,
        title: str | None = None,
        description: str | None = None,
        priority: TaskPriority | None = None,
    ) -> Task:
        """
        Update one or more fields of an existing task.
        Only fields explicitly passed (not None) are changed.
        """
        task = await self.get_task(task_id)  # raises TaskNotFoundError if missing

        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if priority is not None:
            task.priority = priority

        task.mark_updated()
        await self._save()
        return task

    async def complete_task(self, task_id: str) -> Task:
        """Mark a task as completed. A thin, explicit wrapper around
        update logic — kept separate from update_task() because
        'completing' is a distinct, common action worth its own method."""
        task = await self.get_task(task_id)
        task.status = TaskStatus.COMPLETED
        task.mark_updated()
        await self._save()
        return task

    async def delete_task(self, task_id: str) -> None:
        """Delete a task by ID. Raises TaskNotFoundError if it doesn't exist."""
        await self.get_task(task_id)  # validates existence, raises if missing
        del self._tasks[task_id]
        await self._save()