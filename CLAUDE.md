# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MAID LSP is a Language Server Protocol implementation for validating MAID (Manifest-driven AI Development) manifests in real-time. It wraps the `maid-runner` CLI to provide validation feedback in editors like VS Code, JetBrains IDEs, and Claude Code.

**Status**: v0.1.2 - Core implementation complete. All 10 tasks implemented and tested.

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

**Document validation flow**: User edits `.manifest.json` → Debouncer delays (100ms) → `maid validate <path> --use-manifest-chain --json-output` → Parse JSON to LSP diagnostics → Push to editor

### Key Modules

| Module | Purpose |
|--------|---------|
| `maid_lsp/server.py` | Main `MaidLanguageServer` class with handler registration |
| `maid_lsp/__main__.py` | CLI entry point with argparse |
| `maid_lsp/validation/models.py` | Data classes: `ValidationError`, `ValidationResult`, `ValidationMode` |
| `maid_lsp/validation/runner.py` | `MaidRunner` async CLI wrapper |
| `maid_lsp/validation/parser.py` | Converts validation results to LSP diagnostics |
| `maid_lsp/capabilities/diagnostics.py` | `DiagnosticsHandler` with debouncing |
| `maid_lsp/capabilities/code_actions.py` | `CodeActionsHandler` for quick fixes |
| `maid_lsp/capabilities/hover.py` | `HoverHandler` for artifact info |
| `maid_lsp/utils/debounce.py` | `Debouncer` class (100ms default) |

### LSP Capabilities

- `textDocument/didOpen` - Initial validation on file open
- `textDocument/didChange` - Incremental sync with debouncing
- `textDocument/didClose` - Diagnostics cleanup
- `textDocument/codeAction` - Quick fixes for validation errors
- `textDocument/hover` - Artifact information on hover

## Development Methodology

This project uses MAID methodology for implementation. Manifests are in `manifests/` directory and follow the naming pattern `task-NNN-description.manifest.json`.

When implementing new features:
1. Create a manifest in `manifests/`
2. Use `/maid-run` skill for the full MAID workflow
3. Tests go in `tests/` with corresponding `test_task_NNN_*.py` naming

### Implemented Tasks

All 10 core tasks are complete:

- task-001: Package initialization
- task-002: Debouncer utility
- task-003: Validation models
- task-004: MaidRunner CLI wrapper
- task-005: Validation parser
- task-006: Diagnostics handler
- task-007: Code actions handler
- task-008: Hover handler
- task-009: Main server
- task-010: CLI entry point

## Key Dependencies

- `pygls>=1.3.0` - LSP server framework
- `lsprotocol>=2023.0.1` - LSP type definitions
- `maid-runner>=0.8.0` - Manifest validation (called via CLI subprocess)

## Code Quality

- **Type checking**: mypy with strict settings
- **Linting**: ruff with E, W, F, I, B, C4, UP, ARG, SIM rules
- **Formatting**: black with 100 char line length
- **Testing**: pytest with asyncio support
