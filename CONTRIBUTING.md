# Contributing to CLI Task Manager

Thanks for your interest in contributing! This document covers the workflow and conventions used in this project.

## Development Setup

```bash
git clone https://github.com/Sangeeth-Newform/cli-task-manager.git
cd cli-task-manager
make install
uv run pre-commit install
```

## Git Workflow

1. Create a feature branch from `main`:
```bash
   git checkout -b <type>/<short-description>
```
   Branch prefixes used in this project:
   - `feat/` — new functionality
   - `fix/` — bug fixes
   - `docs/` — documentation changes
   - `chore/` — tooling, config, dependency updates
   - `test/` — test additions or changes

2. Make your changes, committing in small, logical units.

3. Push your branch and open a Pull Request against `main`:
```bash
   git push -u origin <your-branch-name>
```

4. Ensure all checks pass before requesting review:
```bash
   make lint
   make test
```

## Commit Message Convention

This project follows [Conventional Commits](https://www.conventionalcommits.org/):