"""
Command-line interface for the Task Manager.

This file is the ONLY place that touches argparse. It parses terminal
input, bridges into the async TaskManager via asyncio.run(), and
formats results for human-readable terminal output.
"""

from __future__ import annotations

import argparse
import asyncio

from task_manager.models import Task, TaskPriority, TaskStatus
from task_manager.task_manager import TaskManager, TaskNotFoundError

# ----------------------------------------------------------------------
# Output formatting helpers
# ----------------------------------------------------------------------


def format_task(task: Task) -> str:
    """Render a single Task as a clean, human-readable line."""
    short_id = task.id[:8]  # show only the first 8 chars — full UUIDs are noisy to read
    return (
        f"[{short_id}] {task.title}  (status={task.status.value}, priority={task.priority.value})"
    )


def print_task_list(tasks: list[Task]) -> None:
    """Print a list of tasks, or a friendly message if there are none."""
    if not tasks:
        print("No tasks found.")
        return
    for task in tasks:
        print(format_task(task))


# ----------------------------------------------------------------------
# Async command handlers — one per subcommand
# ----------------------------------------------------------------------


async def cmd_add(args: argparse.Namespace, manager: TaskManager) -> None:
    task = await manager.add_task(
        title=args.title,
        description=args.description,
        priority=TaskPriority(args.priority),
    )
    print(f"Created task: {format_task(task)}")


async def cmd_list(args: argparse.Namespace, manager: TaskManager) -> None:
    tasks = await manager.list_tasks(
        status=TaskStatus(args.status) if args.status else None,
        priority=TaskPriority(args.priority) if args.priority else None,
        keyword=args.keyword,
    )
    print_task_list(tasks)


async def cmd_update(args: argparse.Namespace, manager: TaskManager) -> None:
    task = await manager.update_task(
        task_id=args.task_id,
        title=args.title,
        description=args.description,
        priority=TaskPriority(args.priority) if args.priority else None,
    )
    print(f"Updated task: {format_task(task)}")


async def cmd_complete(args: argparse.Namespace, manager: TaskManager) -> None:
    task = await manager.complete_task(args.task_id)
    print(f"Completed task: {format_task(task)}")


async def cmd_delete(args: argparse.Namespace, manager: TaskManager) -> None:
    await manager.delete_task(args.task_id)
    print(f"Deleted task: {args.task_id}")


# ----------------------------------------------------------------------
# Argument parser construction
# ----------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the full argparse parser with all subcommands."""
    parser = argparse.ArgumentParser(
        prog="task-manager",
        description="A simple async CLI task manager.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- add ---
    add_parser = subparsers.add_parser("add", help="Create a new task")
    add_parser.add_argument("title", help="Title of the task")
    add_parser.add_argument("--description", default=None, help="Optional description")
    add_parser.add_argument(
        "--priority",
        choices=[p.value for p in TaskPriority],
        default=TaskPriority.MEDIUM.value,
        help="Task priority (default: medium)",
    )
    add_parser.set_defaults(func=cmd_add)

    # --- list ---
    list_parser = subparsers.add_parser("list", help="List tasks, with optional filters")
    list_parser.add_argument(
        "--status",
        choices=[s.value for s in TaskStatus],
        default=None,
        help="Filter by status",
    )
    list_parser.add_argument(
        "--priority",
        choices=[p.value for p in TaskPriority],
        default=None,
        help="Filter by priority",
    )
    list_parser.add_argument(
        "--keyword",
        default=None,
        help="Filter by keyword found in title or description",
    )
    list_parser.set_defaults(func=cmd_list)

    # --- update ---
    update_parser = subparsers.add_parser("update", help="Update an existing task")
    update_parser.add_argument("task_id", help="ID of the task to update")
    update_parser.add_argument("--title", default=None, help="New title")
    update_parser.add_argument("--description", default=None, help="New description")
    update_parser.add_argument(
        "--priority",
        choices=[p.value for p in TaskPriority],
        default=None,
        help="New priority",
    )
    update_parser.set_defaults(func=cmd_update)

    # --- complete ---
    complete_parser = subparsers.add_parser("complete", help="Mark a task as completed")
    complete_parser.add_argument("task_id", help="ID of the task to complete")
    complete_parser.set_defaults(func=cmd_complete)

    # --- delete ---
    delete_parser = subparsers.add_parser("delete", help="Delete a task")
    delete_parser.add_argument("task_id", help="ID of the task to delete")
    delete_parser.set_defaults(func=cmd_delete)

    return parser


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------


async def _run(args: argparse.Namespace) -> None:
    """The single async entry point — this is where asyncio.run() lands."""
    manager = TaskManager()  # uses env var / default path, as designed in Step 3
    try:
        await args.func(args, manager)
    except TaskNotFoundError as error:
        # Catch our custom exception here, at the top level, and print a
        # clean error message instead of a scary Python traceback.
        print(f"Error: {error}")


def main() -> None:
    """
    Synchronous entry point — this is what pyproject.toml's
    [project.scripts] points to. It stays sync on purpose: argparse
    itself is sync, and this is the ONE place we call asyncio.run().
    """
    parser = build_parser()
    args = parser.parse_args()
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
