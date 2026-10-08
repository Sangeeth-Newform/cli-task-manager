# CLI Task Manager

A command-line task manager built with Python 3.12, Typer and async file I/O.
Tasks are stored in a local JSON file.

## Project Structure

```
cli-task-manager/
├── task_manager/             # Main package
│   ├── __init__.py           # Package definition
│   ├── config.py             # Storage path and env config
│   ├── models.py             # Task dataclass, Status and Priority enums, filter helper
│   ├── manager.py            # TaskManager with async file I/O
│   └── cli.py                # Typer CLI subcommands
├── tests/
│   ├── test_tasks.py         # Model and TaskManager tests (async, parametrize, mock)
│   └── test_cli.py           # Command-line tests (confirmations, enum options)
├── main.py                   # Entry point
├── pyproject.toml            # Project config, dependencies and tool settings
├── Makefile                  # install, lint, format, test, run
├── .pre-commit-config.yaml   # ruff, isort, flake8 and vulture hooks
├── .flake8                   # flake8 settings
└── README.md
```

## How to Run

1. Install dependencies:
   ```bash
   make install
   ```

2. Add a new task (priority is `low`, `medium` or `high`):
   ```bash
   uv run python main.py add "Finish Python assignment" -p high
   ```

3. View all tasks:
   ```bash
   uv run python main.py list
   ```

4. Filter tasks (status is `pending` or `completed`):
   ```bash
   uv run python main.py list --priority high
   uv run python main.py list --status pending
   uv run python main.py list --keyword "assignment"
   ```

5. Complete a task:
   ```bash
   uv run python main.py complete <task-id>
   ```

6. Update a task (asks for confirmation, add `--yes` to skip the question):
   ```bash
   uv run python main.py update <task-id> --title "Updated task title"
   ```

7. Delete a task (asks for confirmation, add `--yes` to skip the question):
   ```bash
   uv run python main.py delete <task-id>
   ```

You can use the start of a task ID instead of the full ID.

## Configuration

By default tasks are saved in `tasks.json`. Set the `TASK_FILE_PATH` environment
variable to use another file, or pass `--file <path>` to any command.

## Development Commands

- `make install` - Set up virtual environment and install packages
- `make lint` - Run ruff, isort, flake8 and vulture
- `make format` - Auto-fix formatting and import order
- `make test` - Run pytest (extra options: `make test ARGS="-k filter"`)
- `make run` - Show CLI help, or run a command: `make run ARGS="list --status pending"`

## Tech Stack

- **Python 3.12** with full type hints (generics and `Optional`)
- **Typer** — CLI interface
- **aiofiles + asyncio** — async file I/O
- **pytest + pytest-asyncio** — 24 test cases with async, parametrize and mocking
- **Ruff, isort, flake8, vulture** — linting, formatting, import sorting and dead-code checks
- **pre-commit** — runs the checks before every commit
- **uv** — dependency management