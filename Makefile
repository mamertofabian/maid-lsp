.PHONY: all install dev lint format type-check test test-cov clean help

# Default target
all: lint type-check test

# Install dependencies
install:
	uv sync

# Install development dependencies
dev:
	uv sync --all-extras

# Lint code with ruff
lint:
	uv run ruff check maid_lsp tests

# Fix linting issues automatically
lint-fix:
	uv run ruff check --fix maid_lsp tests

# Format code with black
format:
	uv run black maid_lsp tests

# Check formatting without making changes
format-check:
	uv run black --check maid_lsp tests

# Type check with mypy
type-check:
	uv run mypy maid_lsp

# Run tests
test:
	uv run pytest

# Run tests with coverage
test-cov:
	uv run pytest --cov=maid_lsp --cov-report=term-missing --cov-report=html

# Run the LSP server (for testing)
run:
	uv run maid-lsp --stdio

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Pre-commit hooks
pre-commit:
	uv run pre-commit run --all-files

# Install pre-commit hooks
pre-commit-install:
	uv run pre-commit install

# Build package
build:
	uv build

# Help
help:
	@echo "Available targets:"
	@echo "  install          - Install dependencies"
	@echo "  dev              - Install development dependencies"
	@echo "  lint             - Run ruff linter"
	@echo "  lint-fix         - Fix linting issues automatically"
	@echo "  format           - Format code with black"
	@echo "  format-check     - Check formatting without changes"
	@echo "  type-check       - Run mypy type checker"
	@echo "  test             - Run tests"
	@echo "  test-cov         - Run tests with coverage"
	@echo "  run              - Run the LSP server"
	@echo "  clean            - Clean build artifacts"
	@echo "  pre-commit       - Run pre-commit hooks"
	@echo "  pre-commit-install - Install pre-commit hooks"
	@echo "  build            - Build package"
	@echo "  all              - Run lint, type-check, and test"
