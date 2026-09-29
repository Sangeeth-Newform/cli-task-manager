"""Test suite for CLI Task Manager."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from task_manager.manager import TaskManager
from task_manager.models import Task, filter_items


@pytest.fixture
def manager(tmp_path: Path) -> TaskManager:
    return TaskManager(tmp_path / "test_tasks.json")


# 1. Test Task creation and defaults
def test_task_creation() -> None:
    task = Task(title="Read Python tutorial")
    assert task.title == "Read Python tutorial"
    assert len(task.id) == 8
    assert task.status == "pending"
    assert task.priority == "medium"
    assert task.created_at != ""


# 2. Test generic filter function
def test_generic_filter_items() -> None:
    numbers = [10, 20, 30, 40]
    result = filter_items(numbers, lambda x: x > 25)
    assert result == [30, 40]


# 3. Test async add and load
@pytest.mark.asyncio
async def test_async_add_and_load(manager: TaskManager) -> None:
    task = await manager.add_task("Submit report", priority="high")
    all_tasks = await manager.load_tasks()

    assert len(all_tasks) == 1
    assert all_tasks[0].id == task.id
    assert all_tasks[0].title == "Submit report"


# 4. Test async complete task
@pytest.mark.asyncio
async def test_async_complete_task(manager: TaskManager) -> None:
    task = await manager.add_task("Clean bedroom")
    assert task.status == "pending"

    updated = await manager.complete_task(task.id)
    assert updated is not None
    assert updated.status == "completed"


# 5. Test async update task
@pytest.mark.asyncio
async def test_async_update_task(manager: TaskManager) -> None:
    task = await manager.add_task("Initial title", priority="low")

    updated = await manager.update_task(task.id, title="Updated title", priority="high")
    assert updated is not None
    assert updated.title == "Updated title"
    assert updated.priority == "high"


# 6. Test async delete task
@pytest.mark.asyncio
async def test_async_delete_task(manager: TaskManager) -> None:
    task = await manager.add_task("One-time task")
    assert await manager.delete_task(task.id) is True

    all_tasks = await manager.load_tasks()
    assert len(all_tasks) == 0


# 7. Parametrized test: filter by priority
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("priority", "expected_count"),
    [
        ("high", 1),
        ("medium", 1),
        ("low", 1),
    ],
)
async def test_filter_by_priority(manager: TaskManager, priority: str, expected_count: int) -> None:
    await manager.add_task("Task 1", priority="high")
    await manager.add_task("Task 2", priority="medium")
    await manager.add_task("Task 3", priority="low")

    matches = await manager.list_tasks(priority=priority)
    assert len(matches) == expected_count


# 8. Mocking test: verify file saving using AsyncMock
@pytest.mark.asyncio
async def test_mock_file_save(tmp_path: Path) -> None:
    fake_path = tmp_path / "mocked_tasks.json"
    manager = TaskManager(fake_path)

    mock_file = AsyncMock()
    with patch("aiofiles.open", return_value=mock_file):
        await manager.save_tasks([Task(title="Mocked task")])
        mock_file.__aenter__.assert_called_once()
