# MAID LSP Architecture

This document describes the architecture of the MAID Language Server Protocol (LSP) implementation.

## Overview

The MAID LSP server provides real-time validation of MAID manifests in code editors and IDEs. It integrates with the existing `maid-runner` CLI to leverage battle-tested validation logic while providing a responsive editing experience.

## Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────┐
│                          IDE / Editor                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │   VS Code    │  │  JetBrains   │  │      Claude Code         │  │
│  └──────┬───────┘  └──────┬───────┘  └───────────┬──────────────┘  │
└─────────┼─────────────────┼──────────────────────┼─────────────────┘
          │                 │                      │
          └────────────────┬┴──────────────────────┘
                           │ LSP Protocol (JSON-RPC over stdio)
                           ▼
┌────────────────────────────────────────────────────────────────────┐
│                        maid-lsp Server                              │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Protocol Layer (pygls)                    │   │
│  │  - Document sync  - Diagnostics  - Code actions  - Hover    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                   Validation Layer                           │   │
│  │  - Debounce      - Cache        - Error mapping              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                   Integration Layer                          │   │
│  │  - CLI wrapper   - JSON parser  - Process pool              │   │
│  └─────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────┘
                           │
                           │ subprocess (async)
                           ▼
┌────────────────────────────────────────────────────────────────────┐
│                       maid-runner CLI                               │
│  - Schema validation    - AST parsing       - Manifest merging     │
│  - Behavioral validation - Implementation validation               │
│  - Coherence checks     - Knowledge graph                          │
└────────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Protocol Layer (`maid_lsp/server.py`)

The Protocol Layer handles LSP protocol communication using the [pygls](https://github.com/openlawlibrary/pygls) library.

**Responsibilities:**
- Document synchronization (open, change, close)
- Publishing diagnostics to the client
- Handling code action requests
- Providing hover information

**Key Classes:**
- `MaidLanguageServer` - Main server class extending `LanguageServer`

### 2. Capabilities (`maid_lsp/capabilities/`)

Individual capability handlers for LSP features.

| Module | Capability | Description |
|--------|------------|-------------|
| `diagnostics.py` | `textDocument/publishDiagnostics` | Error/warning reporting |
| `code_actions.py` | `textDocument/codeAction` | Quick fixes |
| `hover.py` | `textDocument/hover` | Artifact information |

### 3. Validation Layer (`maid_lsp/validation/`)

Bridges the LSP server with the maid-runner CLI.

| Module | Purpose |
|--------|---------|
| `runner.py` | Async wrapper for maid-runner CLI |
| `parser.py` | Converts validation output to LSP diagnostics |

### 4. Utilities (`maid_lsp/utils/`)

Support utilities for the server.

| Module | Purpose |
|--------|---------|
| `debounce.py` | Debouncing for document changes |

## Data Flow

### Document Validation Flow

```
1. User opens/edits a .manifest.json file
                    ↓
2. LSP client sends textDocument/didOpen or didChange
                    ↓
3. MaidLanguageServer receives event
                    ↓
4. Debouncer delays validation (100ms)
                    ↓
5. MaidRunner executes: maid validate <path> --json-output
                    ↓
6. Parser converts JSON output to LSP Diagnostics
                    ↓
7. Server publishes diagnostics to client
                    ↓
8. IDE displays errors/warnings in editor
```

### Code Action Flow

```
1. User requests code actions (e.g., hover over error)
                    ↓
2. LSP client sends textDocument/codeAction
                    ↓
3. Server retrieves diagnostics for the range
                    ↓
4. Code action handler generates quick fixes
                    ↓
5. Server returns list of available actions
                    ↓
6. User selects an action
                    ↓
7. IDE applies the workspace edit
```

## Design Decisions

### CLI Wrapper vs Direct Integration

**Decision:** Wrap the maid-runner CLI rather than importing its modules directly.

**Rationale:**
- Leverages battle-tested validation logic without code duplication
- Clear separation of concerns between LSP and validation
- Easier to maintain version compatibility
- CLI output format is a stable API contract

### Push vs Pull Diagnostics

**Decision:** Use push diagnostics only (server pushes on document change).

**Rationale:**
- Simpler implementation for MVP
- Works with all LSP-compatible editors
- Sufficient for real-time validation needs

### Language Detection

**Decision:** Detect MAID manifests by file extension (`.manifest.json`).

**Rationale:**
- Simple and reliable
- Matches existing maid-runner conventions
- No content inspection required

## Extension Points

### Adding New Capabilities

1. Create a new module in `maid_lsp/capabilities/`
2. Implement the LSP handler function
3. Register the handler in `server.py` using `@server.feature()`

### Supporting New Validation Types

1. Add new `DiagnosticCode` in `capabilities/diagnostics.py`
2. Update `parser.py` to map new error codes
3. Optionally add code actions for the new type

## Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| `pygls` | >=1.3.0 | LSP server framework |
| `lsprotocol` | >=2023.0.1 | LSP type definitions |
| `maid-runner` | >=0.8.0 | Manifest validation |

## Future Considerations

### Planned Enhancements (v2.1+)
- Workspace-wide diagnostics
- Go to definition for artifact references
- Manifest completion suggestions
- Semantic tokens for syntax highlighting

### Performance Optimizations
- Process pooling for maid-runner instances
- Incremental validation for large manifests
- Caching of manifest chain results
