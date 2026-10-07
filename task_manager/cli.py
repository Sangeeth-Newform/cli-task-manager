"""Command-Line Interface (CLI) subcommands using Typer."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

import typer

from task_manager.config import get_file_path
from task_manager.manager import UNSET, TaskManager, Unset
from task_manager.models import Priority, Status, validate_title

logger = logging.getLogger(__name__)

app = typer.Typer(help="My command-line task manager.", add_completion=False)


@app.callback()
def configure_logging() -> None:
    """Set up logging once, before any command runs."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


@app.command()
def add(
    title: str = typer.Argument(..., help="Short title for your task"),
    description: Optional[str] = typer.Option(None, "-d", "--description", help="Extra notes"),
    priority: Priority = typer.Option(
        Priority.MEDIUM, "-p", "--priority", case_sensitive=False, help="Task priority"
    ),
    file: Optional[str] = typer.Option(None, "--file", help="Custom tasks file path"),
) -> None:
    """Create a new task."""
    manager = TaskManager(get_file_path(file))
    try:
        task = asyncio.run(manager.add_task(title, description, priority))
    except ValueError as error:
        logger.error("%s", error)
        raise typer.Exit(code=1) from error
    logger.info("Task successfully created! (ID: %s)", task.id)


@app.command(name="list")
def list_tasks(
    status: Optional[Status] = typer.Option(
        None, "-s", "--status", case_sensitive=False, help="Show only this status"
    ),
    priority: Optional[Priority] = typer.Option(
        None, "-p", "--priority", case_sensitive=False, help="Show only this priority"
    ),
    keyword: Optional[str] = typer.Option(None, "-k", "--keyword", help="Search in text"),
    file: Optional[str] = typer.Option(None, "--file", help="Custom tasks file path"),
) -> None:
    """List tasks with optional search and filters."""
    manager = TaskManager(get_file_path(file))
    tasks = asyncio.run(manager.list_tasks(status, priority, keyword))

    if not tasks:
        logger.info("No tasks found matching your search.")
        return

    # Log a clean, formatted table
    logger.info("%-10s %-28s %-12s %-10s %s", "ID", "Title", "Status", "Priority", "Created At")
    logger.info("-" * 75)
    for task in tasks:
        title = task.title if len(task.title) <= 26 else task.title[:25] + ".."
        logger.info(
            "%-10s %-28s %-12s %-10s %s",
            task.id,
            title,
            task.status,
            task.priority,
            task.created_at,
        )


@app.command()
def update(
    task_id: str = typer.Argument(..., help="ID or prefix of the task to update"),
    title: Optional[str] = typer.Option(None, "-t", "--title", help="New title"),
    description: Optional[str] = typer.Option(None, "-d", "--description", help="New notes"),
    clear_description: bool = typer.Option(
        False, "--clear-description", help="Remove the notes from the task"
    ),
    status: Optional[Status] = typer.Option(
        None, "-s", "--status", case_sensitive=False, help="New status"
    ),
    priority: Optional[Priority] = typer.Option(
        None, "-p", "--priority", case_sensitive=False, help="New priority"
    ),
    yes: bool = typer.Option(False, "-y", "--yes", help="Skip the confirmation question"),
    file: Optional[str] = typer.Option(None, "--file", help="Custom tasks file path"),
) -> None:
    """Update an existing task after asking for confirmation."""
    if description is not None and clear_description:
        logger.error("Use either --description or --clear-description, not both.")
        raise typer.Exit(code=1)

    nothing_given = all(value is None for value in (title, description, status, priority))
    if nothing_given and not clear_description:
        logger.error(
            "Nothing to update. Give --title, --description, --clear-description, "
            "--status or --priority."
        )
        raise typer.Exit(code=1)

    if title is not None:
        try:
            validate_title(title)
        except ValueError as error:
            logger.error("%s", error)
            raise typer.Exit(code=1) from error

    manager = TaskManager(get_file_path(file))
    task = asyncio.run(manager.find_task(task_id))
    if task is None:
        logger.error("Could not find task with ID '%s'.", task_id)
        raise typer.Exit(code=1)

    if not yes and not typer.confirm(f"Update task '{task.id}' ({task.title})?"):
        logger.info("Cancelled. Nothing was changed.")
        return

    # Not given -> keep the old notes (UNSET). --clear-description -> remove them (None).
    new_description: str | None | Unset
    if clear_description:
        new_description = None
    elif description is None:
        new_description = UNSET
    else:
        new_description = description

    asyncio.run(manager.update_task(task.id, title, new_description, status, priority))
    logger.info("Task '%s' successfully updated!", task.id)


@app.command()
def complete(
    task_id: str = typer.Argument(..., help="ID or prefix of the task to complete"),
    file: Optional[str] = typer.Option(None, "--file", help="Custom tasks file path"),
) -> None:
    """Mark a task as completed."""
    manager = TaskManager(get_file_path(file))
    task = asyncio.run(manager.complete_task(task_id))
    if task is None:
        logger.error("Could not find task with ID '%s'.", task_id)
        raise typer.Exit(code=1)
    logger.info("Great job! Task '%s' marked as completed.", task.id)


@app.command()
def delete(
    task_id: str = typer.Argument(..., help="ID or prefix of the task to delete"),
    yes: bool = typer.Option(False, "-y", "--yes", help="Skip the confirmation question"),
    file: Optional[str] = typer.Option(None, "--file", help="Custom tasks file path"),
) -> None:
    """Delete a task after asking for confirmation."""
    manager = TaskManager(get_file_path(file))
    task = asyncio.run(manager.find_task(task_id))
    if task is None:
        logger.error("Could not find task with ID '%s'.", task_id)
        raise typer.Exit(code=1)

    if not yes and not typer.confirm(f"Delete task '{task.id}' ({task.title})?"):
        logger.info("Cancelled. Nothing was deleted.")
        return

    asyncio.run(manager.delete_task(task.id))
    logger.info("Task '%s' was deleted.", task.id)
