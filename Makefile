# Makefile for the CLI Task Manager project.
# Run these with: make <target-name>   (e.g. make install)

.PHONY: install lint test run

install:
	uv sync

lint:
	uv run ruff check . --fix
	uv run ruff format .

test:
	uv run pytest -v

run:
	uv run task-managermake install