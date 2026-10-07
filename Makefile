.PHONY: install lint format test run

# Pass extra arguments to test and run with ARGS, for example:
#   make test ARGS="-k filter"
#   make run ARGS="list --status pending"
ARGS ?=

install:
	uv sync

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run isort --check-only .
	uv run flake8
	uv run vulture

format:
	uv run ruff check --fix .
	uv run ruff format .
	uv run isort .

test:
	uv run pytest -v $(ARGS)

run:
	uv run python main.py $(if $(ARGS),$(ARGS),--help)
