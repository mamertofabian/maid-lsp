# MAID LSP

Language Server Protocol implementation for MAID (Manifest-driven AI Development) methodology validation.

> **Status**: v0.1.0 - Core implementation complete. All LSP capabilities functional.

## Overview

MAID LSP provides real-time validation of MAID manifests in code editors and IDEs, including:

- **VS Code** (via extension)
- **JetBrains IDEs** (via plugin)
- **Claude Code** (native LSP support)
- Any LSP-compatible editor

## Features

- **Real-time Diagnostics**: Instant validation feedback as you edit manifests
- **Code Actions**: Quick fixes for common validation errors (add missing fields, create referenced files)
- **Hover Information**: Detailed artifact information on hover (functions, classes, attributes)
- **Push Diagnostics**: Server pushes validation results on document changes with 100ms debouncing

## Installation

### Prerequisites

- Python 3.10+
- maid-runner >= 0.8.0
- uv (package manager)

### From Source

```bash
# Clone the repository
git clone https://github.com/mamertofabian/maid-lsp.git
cd maid-lsp

# Install dependencies
uv sync --all-extras

# Run the server
uv run maid-lsp --stdio
```

## Usage

### Running the Server

```bash
# Start in stdio mode (default)
maid-lsp --stdio

# Or via make
make run

# Check version
maid-lsp --version
```

### Editor Integration

The server communicates via stdio and validates files matching `*.manifest.json`.

**Claude Code**: Configure `.lsp.json` in your project root (see `.lsp.json` in this repo for example).

**VS Code**: Use the vscode-maid extension (planned).

## Architecture

See the [docs/](docs/) directory for detailed architecture documentation:

- [Architecture](docs/architecture.md) - System design and components
- [Capabilities](docs/capabilities.md) - LSP features and diagnostic codes
- [Integration](docs/integration.md) - maid-runner CLI integration
- [Performance](docs/performance.md) - Performance specifications
- [Claude Code](docs/claude-code.md) - Claude Code integration guide

### Three-Layer Design

```
┌─────────────────────────────────────────────────────────┐
│                    Protocol Layer                        │
│                   (maid_lsp/server.py)                  │
│                    pygls + LSP handlers                  │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                  Capabilities Layer                      │
│              (maid_lsp/capabilities/)                   │
│         diagnostics.py │ code_actions.py │ hover.py     │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                  Validation Layer                        │
│               (maid_lsp/validation/)                    │
│           runner.py │ parser.py │ models.py             │
└─────────────────────────────────────────────────────────┘
```

**Key design decision**: The server wraps `maid-runner` CLI via subprocess rather than importing modules directly. This keeps validation logic separate and uses CLI output as a stable API contract.

### Project Structure

```
maid-lsp/
├── maid_lsp/
│   ├── __init__.py           # Package init with version
│   ├── __main__.py           # CLI entry point
│   ├── server.py             # Main LSP server
│   ├── capabilities/         # LSP capability handlers
│   │   ├── diagnostics.py    # Diagnostic publishing
│   │   ├── code_actions.py   # Quick fix actions
│   │   └── hover.py          # Hover information
│   ├── validation/           # maid-runner integration
│   │   ├── models.py         # Data models
│   │   ├── runner.py         # CLI wrapper
│   │   └── parser.py         # Result to diagnostic conversion
│   └── utils/
│       └── debounce.py       # Async debouncer
├── tests/                    # Behavioral tests
├── docs/                     # Architecture documentation
├── manifests/                # MAID manifests (dogfooding)
├── .claude-plugin/
│   └── plugin.json           # Claude Code plugin config
└── .lsp.json                 # LSP server configuration
```

## Diagnostic Codes

| Code | Severity | Description |
|------|----------|-------------|
| `MAID-001` | Error | Schema validation errors |
| `MAID-002` | Error | Missing required fields |
| `MAID-003` | Error | File reference errors |
| `MAID-004` | Error | Artifact validation errors |
| `MAID-005` | Error | Behavioral validation errors |
| `MAID-006` | Error | Implementation validation errors |
| `MAID-007` | Error | Manifest chain errors |
| `MAID-008` | Warning | Coherence validation warnings |

## Development

### Commands

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

# Run a single test
uv run pytest tests/test_task_002_debounce.py -v
```

### MAID Methodology

This project uses the **MAID methodology** for all implementation. Each feature was developed following the MAID workflow with manifests in the `manifests/` directory.

| Task | Component | Status |
|------|-----------|--------|
| task-001 | Package initialization | Complete |
| task-002 | Async debouncer | Complete |
| task-003 | Validation models | Complete |
| task-004 | MaidRunner CLI wrapper | Complete |
| task-005 | Validation parser | Complete |
| task-006 | Diagnostics handler | Complete |
| task-007 | Code actions handler | Complete |
| task-008 | Hover handler | Complete |
| task-009 | Main server | Complete |
| task-010 | CLI entry point | Complete |

## Related Projects

- [maid-runner](https://github.com/mamertofabian/maid-runner) - MAID CLI validation tool
- [vscode-maid](https://github.com/mamertofabian/vscode-maid) - VS Code extension (planned)

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- [pygls](https://github.com/openlawlibrary/pygls) - Python LSP framework
- [lsprotocol](https://github.com/microsoft/lsprotocol) - LSP type definitions
