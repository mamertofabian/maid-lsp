# MAID LSP

Language Server Protocol implementation for MAID (Manifest-driven AI Development) methodology validation.

> **Status**: Architecture Design Complete (Issue #37). Implementation pending using MAID methodology.

## Overview

MAID LSP will provide real-time validation of MAID manifests in code editors and IDEs, including:

- **VS Code** (via extension)
- **JetBrains IDEs** (via plugin)
- **Claude Code** (native LSP support)
- Any LSP-compatible editor

## Planned Features

- **Real-time Diagnostics**: Instant validation feedback as you edit manifests
- **Code Actions**: Quick fixes for common validation errors
- **Hover Information**: Detailed artifact information on hover
- **Push Diagnostics**: Server pushes validation results on document changes

## Architecture

See the [docs/](docs/) directory for detailed architecture documentation:

- [Architecture](docs/architecture.md) - System design and components
- [Capabilities](docs/capabilities.md) - LSP features and diagnostic codes
- [Integration](docs/integration.md) - maid-runner CLI integration
- [Performance](docs/performance.md) - Performance specifications
- [Claude Code](docs/claude-code.md) - Claude Code integration guide

## Development

This project uses the **MAID methodology** for all implementation. Each feature will be developed following the MAID workflow:

1. **Phase 1**: Goal Definition
2. **Phase 2**: Planning Loop (manifest + behavioral tests)
3. **Phase 3**: Implementation (code to pass tests)
4. **Phase 4**: Integration

### Prerequisites

- Python 3.10+
- maid-runner >= 0.8.0
- uv (package manager)

### Setup

```bash
# Clone the repository
git clone https://github.com/mamertofabian/maid-lsp.git
cd maid-lsp

# Install dependencies
uv sync --all-extras

# Run tests
make test

# Run linting
make lint

# Run type checking
make type-check
```

### Project Structure (Planned)

```
maid-lsp/
├── maid_lsp/
│   ├── __init__.py
│   ├── server.py           # Main LSP server
│   ├── capabilities/       # LSP capability handlers
│   │   ├── diagnostics.py
│   │   ├── code_actions.py
│   │   └── hover.py
│   ├── validation/         # maid-runner integration
│   │   ├── runner.py
│   │   └── parser.py
│   └── utils/
│       └── debounce.py
├── tests/
├── docs/
├── manifests/              # MAID manifests (dogfooding)
├── .claude-plugin/
│   └── plugin.json
└── .lsp.json
```

## Diagnostic Codes (Planned)

| Code | Description |
|------|-------------|
| `MAID-001` | Schema validation errors |
| `MAID-002` | Missing required fields |
| `MAID-003` | File reference errors |
| `MAID-004` | Artifact validation errors |
| `MAID-005` | Behavioral validation errors |
| `MAID-006` | Implementation validation errors |
| `MAID-007` | Manifest chain errors |
| `MAID-008` | Coherence validation warnings |

## Related Projects

- [maid-runner](https://github.com/mamertofabian/maid-runner) - MAID CLI validation tool
- [vscode-maid](https://github.com/mamertofabian/vscode-maid) - VS Code extension (planned)

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- [pygls](https://github.com/openlawlibrary/pygls) - Python LSP framework
- [lsprotocol](https://github.com/microsoft/lsprotocol) - LSP type definitions
