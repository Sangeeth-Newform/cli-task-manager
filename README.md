# CLI Task Manager

A simple command-line task manager built with Python 3.12, Typer, and Async I/O.
This is my first Python portfolio project.

## Project Structure

```
Project3/
├── task_manager/        # Main package
│   ├── __init__.py      # Package definition
│   ├── config.py        # Storage path and env config
│   ├── models.py        # Task dataclass and filter helper
│   ├── manager.py       # TaskManager with async file I/O
│   └── cli.py           # Typer CLI subcommands
├── tests/
│   └── test_tasks.py    # Full pytest suite (8 tests)
├── main.py              # Entry point
├── pyproject.toml       # Project config and dependencies
├── Makefile             # install, lint, test, run
└── README.md
```

## How to Run

1. Install dependencies:
   ```bash
   make install
   ```

2. Add a new task:
   ```bash
   uv run python main.py add "Finish Python assignment" -p high
   ```

3. View all tasks:
   ```bash
   uv run python main.py list
   ```

4. Filter tasks:
   ```bash
   uv run python main.py list --priority high
   uv run python main.py list --status pending
   uv run python main.py list --keyword "assignment"
   ```

5. Complete a task:
   ```bash
   uv run python main.py complete <task-id>
   ```

6. Update a task:
   ```bash
   uv run python main.py update <task-id> --title "Updated task title"
   ```

7. Delete a task:
   ```bash
   uv run python main.py delete <task-id>
   ```

## Development Commands

- `make install` - Set up virtual environment and install packages
- `make lint` - Check code style with Ruff
- `make test` - Run pytest test suite
- `make run` - Show CLI help menu

## Tech Stack

- **Python 3.12** with full type hints
- **Typer** — CLI interface
- **aiofiles + asyncio** — async file I/O
- **pytest** — test suite with async, parametrize, and mocking
- **Ruff** — linting and formatting
- **uv** — dependency management
