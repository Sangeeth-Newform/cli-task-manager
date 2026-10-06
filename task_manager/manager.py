"""TaskManager handling task operations and async file persistence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import aiofiles

from task_manager.models import Task, filter_items


class TaskManager:
    """Create, read, update and delete tasks stored in a local JSON file."""

    def __init__(self, file_path: Path) -> None:
        """Store the location of the JSON file.

        Args:
            file_path: Path to the JSON file that holds the tasks.

        """
        self.file_path = file_path

    async def load_tasks(self) -> list[Task]:
        """Read tasks from the local JSON file asynchronously.

        Returns:
            All saved tasks, or an empty list if the file is missing or empty.

        Raises:
            json.JSONDecodeError: If the file contains invalid JSON.

        """
        if not self.file_path.exists():
            return []

        async with aiofiles.open(self.file_path, mode="r", encoding="utf-8") as f:
            content = await f.read()

        if not content.strip():
            return []

        data = json.loads(content)
        return [Task.from_dict(item) for item in data]

    async def save_tasks(self, all_tasks: list[Task]) -> None:
        """Write all tasks to the JSON file asynchronously.

        Args:
            all_tasks: The complete list of tasks to save. It replaces the file contents.

        """
        async with aiofiles.open(self.file_path, mode="w", encoding="utf-8") as f:
            text = json.dumps([t.to_dict() for t in all_tasks], indent=2)
            await f.write(text)

    async def add_task(
        self,
        title: str,
        description: Optional[str] = None,
        priority: str = "medium",
    ) -> Task:
        """Create a new task and save it.

        Args:
            title: Short name of the task.
            description: Optional extra notes.
            priority: Task priority. It is stored in lowercase.

        Returns:
            The newly created task.

        """
        all_tasks = await self.load_tasks()
        task = Task(title=title, description=description, priority=priority.lower())
        all_tasks.append(task)
        await self.save_tasks(all_tasks)
        return task

    async def find_task(self, task_id: str) -> Optional[Task]:
        """Find a task by its full ID or by the start of its ID.

        Args:
            task_id: The full task ID or a prefix of it (not case sensitive).

        Returns:
            The first matching task, or None if nothing matches.

        """
        all_tasks = await self.load_tasks()
        clean_id = task_id.strip().lower()
        for task in all_tasks:
            if task.id.lower() == clean_id or task.id.lower().startswith(clean_id):
                return task
        return None

    async def list_tasks(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> list[Task]:
        """List tasks, optionally filtered by status, priority and keyword.

        Args:
            status: Keep only tasks with this status.
            priority: Keep only tasks with this priority.
            keyword: Keep only tasks whose title or description contains this text.

        Returns:
            The tasks that match every filter that was given.

        """
        all_tasks = await self.load_tasks()

        if status:
            all_tasks = filter_items(all_tasks, lambda t: t.status.lower() == status.lower())

        if priority:
            all_tasks = filter_items(all_tasks, lambda t: t.priority.lower() == priority.lower())

        if keyword:
            kw = keyword.lower()
            all_tasks = filter_items(
                all_tasks,
                lambda t: (
                    kw in t.title.lower()
                    or (t.description is not None and kw in t.description.lower())
                ),
            )

        return all_tasks

    async def update_task(
        self,
        task_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> Optional[Task]:
        """Update the fields of an existing task and save the change.

        Only the fields that are not None are changed.

        Args:
            task_id: The full task ID or a prefix of it.
            title: New title.
            description: New description.
            status: New status. It is stored in lowercase.
            priority: New priority. It is stored in lowercase.

        Returns:
            The updated task, or None if no task matches the ID.

        """
        all_tasks = await self.load_tasks()
        target_task = None

        clean_id = task_id.strip().lower()
        for task in all_tasks:
            if task.id.lower() == clean_id or task.id.lower().startswith(clean_id):
                target_task = task
                break

        if target_task is None:
            return None

        if title is not None:
            target_task.title = title
        if description is not None:
            target_task.description = description
        if status is not None:
            target_task.status = status.lower()
        if priority is not None:
            target_task.priority = priority.lower()

        await self.save_tasks(all_tasks)
        return target_task

    async def complete_task(self, task_id: str) -> Optional[Task]:
        """Mark a task as completed.

        Args:
            task_id: The full task ID or a prefix of it.

        Returns:
            The updated task, or None if no task matches the ID.

        """
        return await self.update_task(task_id, status="completed")

    async def delete_task(self, task_id: str) -> bool:
        """Delete every task whose ID matches the given ID or prefix.

        Args:
            task_id: The full task ID or a prefix of it.

        Returns:
            True if a task was deleted, False if nothing matched.

        """
        all_tasks = await self.load_tasks()
        clean_id = task_id.strip().lower()
        kept_tasks = [
            t
            for t in all_tasks
            if not (t.id.lower() == clean_id or t.id.lower().startswith(clean_id))
        ]

        if len(kept_tasks) == len(all_tasks):
            return False

        await self.save_tasks(kept_tasks)
        return True
