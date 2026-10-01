"""Command-Line Interface (CLI) subcommands using Typer."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

import typer

from task_manager.config import get_file_path
from task_manager.manager import TaskManager

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
    priority: str = typer.Option("medium", "-p", "--priority", help="low, medium, or high"),
    file: Optional[str] = typer.Option(None, "--file", help="Custom tasks file path"),
) -> None:
    """Create a new task."""
    manager = TaskManager(get_file_path(file))
    task = asyncio.run(manager.add_task(title, description, priority))
    logger.info("Task successfully created! (ID: %s)", task.id)


@app.command(name="list")
def list_tasks(
    status: Optional[str] = typer.Option(None, "-s", "--status", help="pending or completed"),
    priority: Optional[str] = typer.Option(None, "-p", "--priority", help="low, medium, high"),
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
    status: Optional[str] = typer.Option(None, "-s", "--status", help="New status"),
    priority: Optional[str] = typer.Option(None, "-p", "--priority", help="New priority"),
    file: Optional[str] = typer.Option(None, "--file", help="Custom tasks file path"),
) -> None:
    """Update an existing task."""
    manager = TaskManager(get_file_path(file))
    task = asyncio.run(manager.update_task(task_id, title, description, status, priority))
    if task:
        logger.info("Task '%s' successfully updated!", task.id)
    else:
        logger.error("Could not find task with ID '%s'.", task_id)


@app.command()
def complete(
    task_id: str = typer.Argument(..., help="ID or prefix of the task to complete"),
    file: Optional[str] = typer.Option(None, "--file", help="Custom tasks file path"),
) -> None:
    """Mark a task as completed."""
    manager = TaskManager(get_file_path(file))
    task = asyncio.run(manager.complete_task(task_id))
    if task:
        logger.info("Great job! Task '%s' marked as completed.", task.id)
    else:
        logger.error("Could not find task with ID '%s'.", task_id)


@app.command()
def delete(
    task_id: str = typer.Argument(..., help="ID or prefix of the task to delete"),
    file: Optional[str] = typer.Option(None, "--file", help="Custom tasks file path"),
) -> None:
    """Delete a task."""
    manager = TaskManager(get_file_path(file))
    success = asyncio.run(manager.delete_task(task_id))
    if success:
        logger.info("Task '%s' was deleted.", task_id)
    else:
        logger.error("Could not find task with ID '%s'.", task_id)
