# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MAID LSP is a Language Server Protocol implementation for validating MAID (Manifest-driven AI Development) manifests in real-time. It wraps the `maid-runner` CLI to provide validation feedback in editors like VS Code, JetBrains IDEs, and Claude Code.

**Status**: Early development. Architecture complete, implementation in progress using MAID methodology.

## Common Commands

```bash
# Install dependencies
uv sync --all-extras

# Run all quality checks (lint + type-check + test)
make all

# Individual commands
make lint           # Run ruff linter
make lint-fix       # Auto-fix linting issues
make type-check     # Run mypy type checker
make test           # Run pytest
make test-cov       # Run tests with coverage report
make format         # Format code with black
make format-check   # Check formatting without changes

# Run the LSP server
make run            # or: uv run maid-lsp --stdio

# Run a single test
uv run pytest tests/test_task_002_debounce.py -v
uv run pytest tests/test_task_002_debounce.py::test_specific_function -v
```

## Architecture

The server has three layers:

1. **Protocol Layer** (`maid_lsp/server.py`) - LSP communication via pygls
2. **Validation Layer** (`maid_lsp/validation/`) - CLI wrapper and error parsing
3. **Capabilities** (`maid_lsp/capabilities/`) - Individual LSP feature handlers (diagnostics, code actions, hover)

**Key design decision**: The server wraps `maid-runner` CLI via subprocess rather than importing modules directly. This keeps validation logic separate and uses CLI output as a stable API contract.

**Document validation flow**: User edits `.manifest.json` → Debouncer delays (100ms) → `maid validate <path> --json-output` → Parse JSON to LSP diagnostics → Push to editor

## Development Methodology

This project uses MAID methodology for implementation. Manifests are in `manifests/` directory and follow the naming pattern `task-NNN-description.manifest.json`.

When implementing features:
1. Check for existing manifest in `manifests/`
2. Use `/maid-run` skill for the full MAID workflow
3. Tests go in `tests/` with corresponding `test_task_NNN_*.py` naming

## Key Dependencies

- `pygls` - LSP server framework
- `lsprotocol` - LSP type definitions
- `maid-runner` - Manifest validation (called via CLI subprocess)
