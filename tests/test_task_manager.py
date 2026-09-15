"""
Test suite for TaskManager.

Every test gets a fresh, isolated, temporary JSON file via the
`manager` fixture below — no test ever touches the real
~/.task_manager/tasks.json file on your machine.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from task_manager.models import TaskPriority, TaskStatus
from task_manager.task_manager import TaskManager, TaskNotFoundError

# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------


@pytest.fixture
def manager(tmp_path: Path) -> TaskManager:
    """
    Provide a TaskManager pointed at a temporary, throwaway JSON file.

    `tmp_path` is a built-in pytest fixture: it gives each test its own
    unique temporary directory that pytest automatically cleans up
    afterward. This is the formal, reusable version of the pattern we
    used manually in scratch_test.py back in Step 3.
    """
    db_path = tmp_path / "tasks.json"
    return TaskManager(db_path=db_path)


# ----------------------------------------------------------------------
# Basic CRUD tests
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_add_task_creates_task_with_defaults(manager: TaskManager) -> None:
    """A newly added task should default to PENDING status and MEDIUM priority."""
    task = await manager.add_task(title="Buy milk")

    assert task.title == "Buy milk"
    assert task.status == TaskStatus.PENDING
    assert task.priority == TaskPriority.MEDIUM
    assert task.id is not None  # a UUID was generated


@pytest.mark.asyncio
async def test_add_task_persists_to_disk(manager: TaskManager) -> None:
    """After adding a task, the JSON file should actually exist on disk."""
    assert not manager.db_path.exists()  # nothing written yet

    await manager.add_task(title="Write report")

    assert manager.db_path.exists()  # now it should be written


@pytest.mark.asyncio
async def test_list_tasks_returns_all_tasks(manager: TaskManager) -> None:
    """list_tasks() with no filters should return every task added."""
    await manager.add_task(title="Task 1")
    await manager.add_task(title="Task 2")

    all_tasks = await manager.list_tasks()

    assert len(all_tasks) == 2


# ----------------------------------------------------------------------
# Parameterized test — same logic, multiple inputs
# ----------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "priority",
    [TaskPriority.LOW, TaskPriority.MEDIUM, TaskPriority.HIGH],
)
async def test_list_tasks_filtered_by_priority(
    manager: TaskManager, priority: TaskPriority
) -> None:
    """
    Filtering by each priority level should return only tasks with
    that exact priority, regardless of which priority we test.

    This single test function runs 3 times automatically — once per
    value in the parametrize list above — instead of us writing
    test_filter_low(), test_filter_medium(), test_filter_high()
    as three separate, nearly-identical functions.
    """
    # Create one task at each priority level.
    await manager.add_task(title="Low task", priority=TaskPriority.LOW)
    await manager.add_task(title="Medium task", priority=TaskPriority.MEDIUM)
    await manager.add_task(title="High task", priority=TaskPriority.HIGH)

    filtered = await manager.list_tasks(priority=priority)

    assert len(filtered) == 1
    assert filtered[0].priority == priority


# ----------------------------------------------------------------------
# get_task: exact match, prefix match, and error path
# (These two prefix-related tests directly protect against the real
# bug you found and fixed in Step 4 — they must never regress.)
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_task_by_full_id(manager: TaskManager) -> None:
    """get_task() should find a task using its full UUID."""
    created = await manager.add_task(title="Find me")

    found = await manager.get_task(created.id)

    assert found.id == created.id


@pytest.mark.asyncio
async def test_get_task_by_short_prefix(manager: TaskManager) -> None:
    """
    get_task() should also find a task using just the first 8 chars
    of its ID — the exact scenario that broke in Step 4 when using
    the CLI's shortened display IDs.
    """
    created = await manager.add_task(title="Find me by prefix")
    short_id = created.id[:8]

    found = await manager.get_task(short_id)

    assert found.id == created.id


@pytest.mark.asyncio
async def test_get_task_raises_when_not_found(manager: TaskManager) -> None:
    """get_task() should raise TaskNotFoundError for a nonexistent ID."""
    with pytest.raises(TaskNotFoundError):
        await manager.get_task("nonexistent-id")


# ----------------------------------------------------------------------
# complete_task and delete_task
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_complete_task_updates_status(manager: TaskManager) -> None:
    """complete_task() should change status to COMPLETED and update timestamp."""
    created = await manager.add_task(title="Finish this")
    original_updated_at = created.updated_at

    completed = await manager.complete_task(created.id)

    assert completed.status == TaskStatus.COMPLETED
    assert completed.updated_at >= original_updated_at


@pytest.mark.asyncio
async def test_delete_task_removes_by_prefix(manager: TaskManager) -> None:
    """
    delete_task() should correctly remove a task even when given a
    short prefix ID — this is the exact bug from Step 4 where
    del self._tasks[task_id] used the raw short ID instead of the
    resolved full ID, causing a KeyError.
    """
    created = await manager.add_task(title="Delete me")
    short_id = created.id[:8]

    await manager.delete_task(short_id)

    remaining = await manager.list_tasks()
    assert len(remaining) == 0


# ----------------------------------------------------------------------
# Mocking example: verify _save() is called, without touching real disk
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_save_is_called_on_add_task(manager: TaskManager) -> None:
    """
    Use mocking to verify add_task() triggers a save, WITHOUT relying
    on actually reading the file back from disk afterward.

    `patch.object` temporarily replaces TaskManager._save with a fake
    (an AsyncMock, since _save is an async method) for the duration of
    this test only — the real _save is automatically restored after
    the `with` block ends, even if the test fails.

    This is a common real-world pattern: mocking lets you test "did my
    code correctly TRY to do X" separately from "does X actually work,"
    which is especially useful when X is slow, external, or costly
    (e.g. a real API call) rather than a fast local file write.
    """
    with patch.object(manager, "_save", new_callable=AsyncMock) as mock_save:
        await manager.add_task(title="Mocked save test")

        mock_save.assert_awaited_once()
