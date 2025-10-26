.PHONY: help format lint test clean

help:
	@echo "Available commands:"
	@echo "  make format  - Format code with ruff and fix linting issues"
	@echo "  make lint    - Run ruff and mypy checks (no fixes)"
	@echo "  make test    - Run tests with pytest"
	@echo "  make clean   - Remove cache files"

format:
	uv run ruff format .
	uv run ruff check --fix .

lint:
	uv run ruff check .
	uv run mypy .

test:
	uv run pytest -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
