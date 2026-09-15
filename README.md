# CLI Task Manager

A production-grade, asynchronous command-line task manager built with Python 3.12, `asyncio`, and `argparse`. Tasks are persisted locally as JSON, with a fully async I/O layer, comprehensive type hints, and a complete automated test suite.

## Features

- Create, list, update, complete, and delete tasks
- Filter and search tasks by status, priority, and keyword
- Async file I/O (non-blocking JSON persistence via `asyncio.to_thread`)
- Configurable storage location via environment variable
- Fully type-hinted, modern Python 3.12 codebase
- Automated linting/formatting via Ruff, enforced by pre-commit hooks
- 12-test pytest suite covering async behavior, parameterization, and mocking

## Requirements

- Python 3.12 (managed automatically via [`uv`](https://docs.astral.sh/uv/))
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/) installed
- `make` (on Windows, install via `winget install GnuWin32.Make` or similar)

## Installation

```bash
git clone <repo-url>
cd cli-task-manager
make install
```

This runs `uv sync`, which creates a virtual environment, installs all dependencies (pinned exactly via `uv.lock`), and installs this package itself in editable mode.

### Optional: enable pre-commit hooks (for contributors)

```bash
uv run pre-commit install
```

## Configuration

By default, tasks are stored at:

- Windows: `C:\Users\<you>\.task_manager\tasks.json`
- macOS/Linux: `~/.task_manager/tasks.json`

To use a custom location, set the `TASK_MANAGER_DB_PATH` environment variable:

```bash
# Windows (cmd)
set TASK_MANAGER_DB_PATH=C:\path\to\my_tasks.json

# macOS/Linux
export TASK_MANAGER_DB_PATH=/path/to/my_tasks.json
```

## Usage

### Add a task

```bash
uv run task-manager add "Buy milk" --priority high
uv run task-manager add "Write report" --description "Q3 summary for the team"
```

### List tasks

```bash
uv run task-manager list
uv run task-manager list --status pending
uv run task-manager list --priority high
uv run task-manager list --keyword report
```

### Update a task

You can reference a task by its full ID or just the short prefix shown in `list` output:

```bash
uv run task-manager update <task_id> --title "New title" --priority low
```

### Complete a task

```bash
uv run task-manager complete <task_id>
```

### Delete a task

```bash
uv run task-manager delete <task_id>
```

## Development

```bash
make install   # install all dependencies
make lint      # run Ruff lint + format
make test      # run the full pytest suite
make run       # run the CLI directly (equivalent to `uv run task-manager`)
```

## Architecture