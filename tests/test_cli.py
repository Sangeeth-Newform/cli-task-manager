"""Tests for the Typer command-line interface."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import pytest
from typer.testing import CliRunner

from task_manager.cli import app
from task_manager.manager import TaskManager
from task_manager.models import Priority, Status, Task

runner = CliRunner()


@pytest.fixture
def tasks_file(tmp_path: Path) -> Path:
    """Provide the path of a temporary tasks file."""
    return tmp_path / "cli_tasks.json"


def _add_task(path: Path, title: str, priority: Priority = Priority.MEDIUM) -> Task:
    """Add a task to the file (synchronous helper for the tests)."""
    return asyncio.run(TaskManager(path).add_task(title, priority=priority))


def _load_tasks(path: Path) -> list[Task]:
    """Load all tasks from the file (synchronous helper for the tests)."""
    return asyncio.run(TaskManager(path).load_tasks())


def test_add_command_creates_task(tasks_file: Path) -> None:
    """The add command saves a task and accepts any letter case for the priority."""
    result = runner.invoke(app, ["add", "Buy milk", "-p", "HIGH", "--file", str(tasks_file)])

    assert result.exit_code == 0
    tasks = _load_tasks(tasks_file)
    assert len(tasks) == 1
    assert tasks[0].priority == Priority.HIGH


def test_add_command_rejects_unknown_priority(tasks_file: Path) -> None:
    """An invalid priority is refused and nothing is saved."""
    result = runner.invoke(app, ["add", "Buy milk", "-p", "urgent", "--file", str(tasks_file)])

    assert result.exit_code == 2
    assert not tasks_file.exists()


@pytest.mark.parametrize(
    ("answer", "expected_count"),
    [("y\n", 0), ("n\n", 1)],
)
def test_delete_asks_for_confirmation(tasks_file: Path, answer: str, expected_count: int) -> None:
    """The delete command deletes the task only when the answer is yes."""
    task = _add_task(tasks_file, "Old task")

    result = runner.invoke(app, ["delete", task.id, "--file", str(tasks_file)], input=answer)

    assert result.exit_code == 0
    assert "Delete task" in result.output
    assert len(_load_tasks(tasks_file)) == expected_count


def test_delete_with_yes_flag_skips_question(tasks_file: Path) -> None:
    """The --yes flag deletes the task without asking."""
    task = _add_task(tasks_file, "Old task")

    result = runner.invoke(app, ["delete", task.id, "--yes", "--file", str(tasks_file)])

    assert result.exit_code == 0
    assert "Delete task" not in result.output
    assert _load_tasks(tasks_file) == []


def test_delete_unknown_id_fails(tasks_file: Path, caplog: pytest.LogCaptureFixture) -> None:
    """Deleting an unknown ID logs an error and exits with code 1."""
    caplog.set_level(logging.INFO)

    result = runner.invoke(app, ["delete", "nope", "--yes", "--file", str(tasks_file)])

    assert result.exit_code == 1
    assert "Could not find task" in caplog.text


@pytest.mark.parametrize(
    ("answer", "expected_title"),
    [("y\n", "New title"), ("n\n", "Old title")],
)
def test_update_asks_for_confirmation(tasks_file: Path, answer: str, expected_title: str) -> None:
    """The update command changes the task only when the answer is yes."""
    task = _add_task(tasks_file, "Old title")

    result = runner.invoke(
        app,
        ["update", task.id, "-t", "New title", "--file", str(tasks_file)],
        input=answer,
    )

    assert result.exit_code == 0
    assert _load_tasks(tasks_file)[0].title == expected_title


def test_update_changes_status_and_priority(tasks_file: Path) -> None:
    """The update command accepts enum values for status and priority."""
    task = _add_task(tasks_file, "Some task")

    result = runner.invoke(
        app,
        ["update", task.id, "-s", "completed", "-p", "low", "--yes", "--file", str(tasks_file)],
    )

    assert result.exit_code == 0
    updated = _load_tasks(tasks_file)[0]
    assert updated.status == Status.COMPLETED
    assert updated.priority == Priority.LOW


def test_list_filters_by_priority(tasks_file: Path, caplog: pytest.LogCaptureFixture) -> None:
    """The list command shows only the tasks that match the priority filter."""
    caplog.set_level(logging.INFO)
    _add_task(tasks_file, "Urgent report", Priority.HIGH)
    _add_task(tasks_file, "Water plants", Priority.LOW)

    result = runner.invoke(app, ["list", "--priority", "high", "--file", str(tasks_file)])

    assert result.exit_code == 0
    assert "Urgent report" in caplog.text
    assert "Water plants" not in caplog.text


def test_complete_command_marks_task_completed(tasks_file: Path) -> None:
    """The complete command sets the status to completed."""
    task = _add_task(tasks_file, "Finish report")

    result = runner.invoke(app, ["complete", task.id, "--file", str(tasks_file)])

    assert result.exit_code == 0
    assert _load_tasks(tasks_file)[0].status == Status.COMPLETED
