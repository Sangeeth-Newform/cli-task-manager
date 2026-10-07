"""Test suite for CLI Task Manager."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from task_manager.manager import TaskManager
from task_manager.models import Priority, Status, Task, filter_items


@pytest.fixture
def manager(tmp_path: Path) -> TaskManager:
    """Provide a TaskManager that stores its tasks in a temporary file."""
    return TaskManager(tmp_path / "test_tasks.json")


def test_task_creation() -> None:
    """A new task gets an 8-character ID and the default status and priority."""
    task = Task(title="Read Python tutorial")
    assert task.title == "Read Python tutorial"
    assert len(task.id) == 8
    assert task.status == Status.PENDING
    assert task.priority == Priority.MEDIUM
    assert task.created_at != ""


def test_task_rejects_invalid_values() -> None:
    """A task with an unknown status or priority raises ValueError."""
    with pytest.raises(ValueError, match="not a valid Priority"):
        Task(title="Bad priority", priority="urgent")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="not a valid Status"):
        Task(title="Bad status", status="done")  # type: ignore[arg-type]


def test_generic_filter_items() -> None:
    """filter_items keeps only the items that satisfy the condition."""
    numbers = [10, 20, 30, 40]
    result = filter_items(numbers, lambda x: x > 25)
    assert result == [30, 40]


@pytest.mark.asyncio
async def test_async_add_and_load(manager: TaskManager) -> None:
    """A task that is added can be loaded back from the file."""
    task = await manager.add_task("Submit report", priority=Priority.HIGH)
    all_tasks = await manager.load_tasks()

    assert len(all_tasks) == 1
    assert all_tasks[0].id == task.id
    assert all_tasks[0].title == "Submit report"
    assert all_tasks[0].priority == Priority.HIGH


@pytest.mark.asyncio
async def test_async_complete_task(manager: TaskManager) -> None:
    """Completing a task changes its status to completed."""
    task = await manager.add_task("Clean bedroom")
    assert task.status == Status.PENDING

    updated = await manager.complete_task(task.id)
    assert updated is not None
    assert updated.status == Status.COMPLETED


@pytest.mark.asyncio
async def test_async_update_task(manager: TaskManager) -> None:
    """Updating a task changes only the fields that are given."""
    task = await manager.add_task("Initial title", priority=Priority.LOW)

    updated = await manager.update_task(task.id, title="Updated title", priority=Priority.HIGH)
    assert updated is not None
    assert updated.title == "Updated title"
    assert updated.priority == Priority.HIGH


@pytest.mark.asyncio
async def test_async_delete_task(manager: TaskManager) -> None:
    """Deleting a task removes it from the file."""
    task = await manager.add_task("One-time task")
    assert await manager.delete_task(task.id) is True

    all_tasks = await manager.load_tasks()
    assert len(all_tasks) == 0


@pytest.mark.asyncio
async def test_async_find_task_by_prefix(manager: TaskManager) -> None:
    """A task can be found by the start of its ID, and an unknown ID gives None."""
    task = await manager.add_task("Findable task")

    assert await manager.find_task(task.id[:3]) is not None
    assert await manager.find_task("zzzzzzzz") is None


@pytest.mark.asyncio
async def test_async_delete_removes_only_first_match(manager: TaskManager) -> None:
    """Deleting by a shared prefix removes only the first matching task."""
    await manager.save_tasks([Task(title="First", id="abc111"), Task(title="Second", id="abc222")])

    assert await manager.delete_task("abc") is True

    remaining = await manager.load_tasks()
    assert [t.id for t in remaining] == ["abc222"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("priority", "expected_count"),
    [
        (Priority.HIGH, 1),
        (Priority.MEDIUM, 1),
        (Priority.LOW, 1),
    ],
)
async def test_filter_by_priority(
    manager: TaskManager, priority: Priority, expected_count: int
) -> None:
    """Filtering by each priority returns exactly one matching task."""
    await manager.add_task("Task 1", priority=Priority.HIGH)
    await manager.add_task("Task 2", priority=Priority.MEDIUM)
    await manager.add_task("Task 3", priority=Priority.LOW)

    matches = await manager.list_tasks(priority=priority)
    assert len(matches) == expected_count


@pytest.mark.asyncio
async def test_mock_file_save(tmp_path: Path) -> None:
    """Saving tasks opens the file through aiofiles (checked with an AsyncMock)."""
    fake_path = tmp_path / "mocked_tasks.json"
    manager = TaskManager(fake_path)

    mock_file = AsyncMock()
    with patch("aiofiles.open", return_value=mock_file):
        await manager.save_tasks([Task(title="Mocked task")])
        mock_file.__aenter__.assert_called_once()
