# maid-runner Integration

This document describes how the MAID LSP server integrates with the maid-runner CLI.

## Integration Strategy

### CLI Wrapper Approach

The MAID LSP server wraps the maid-runner CLI rather than importing its modules directly. This approach provides:

1. **Stability**: CLI output is a stable API contract
2. **Simplicity**: No need to understand maid-runner internals
3. **Maintainability**: Clear separation of concerns
4. **Compatibility**: Works with any maid-runner version >=0.8.0

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     MAID LSP Server                      │
│  ┌───────────────────────────────────────────────────┐  │
│  │              MaidRunner (wrapper)                  │  │
│  │  - Executes CLI commands via subprocess           │  │
│  │  - Parses JSON output                             │  │
│  │  - Handles timeouts and errors                    │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
                          │ async subprocess
                          ▼
┌─────────────────────────────────────────────────────────┐
│                    maid-runner CLI                       │
│  $ maid validate <manifest> --validation-mode impl      │
│                       --use-manifest-chain               │
│                       --json-output                      │
└─────────────────────────────────────────────────────────┘
```

## CLI Commands Used

### Primary Validation

```bash
maid validate <manifest-path> --validation-mode <mode> --use-manifest-chain --json-output
```

| Parameter | Values | Description |
|-----------|--------|-------------|
| `manifest-path` | Path to manifest | The manifest file to validate |
| `--validation-mode` | `behavioral`, `implementation` | Validation mode |
| `--use-manifest-chain` | Flag | Validate using manifest chain (always enabled) |
| `--json-output` | Flag | Output in JSON format |

### Supporting Commands

```bash
# Find manifests for a file
maid manifests <file-path> --json-output

# Generate snapshot info
maid snapshot <file-path> --json-output
```

## JSON Output Format

### Validation Result

The `--json-output` flag produces structured JSON that the LSP server parses:

```json
{
  "success": false,
  "errors": [
    {
      "code": "MAID-004",
      "message": "Missing artifact: function 'get_user'",
      "file": "src/service.py",
      "line": 15,
      "column": 1,
      "severity": "error",
      "source": "maid-validate"
    }
  ],
  "warnings": [
    {
      "code": "MAID-008",
      "message": "Coherence check: Duplicate artifact name in manifest chain",
      "file": null,
      "line": null,
      "column": null,
      "severity": "warning",
      "source": "maid-coherence"
    }
  ],
  "metadata": {
    "validation_mode": "implementation",
    "manifest": "manifests/task-001.manifest.json",
    "duration_ms": 45,
    "maid_runner_version": "0.8.0"
  }
}
```

### Error Object Structure

| Field | Type | Description |
|-------|------|-------------|
| `code` | string | Error code (MAID-XXX) |
| `message` | string | Human-readable error message |
| `file` | string? | Path to file with error |
| `line` | int? | 1-based line number |
| `column` | int? | 1-based column number |
| `severity` | string | "error" or "warning" |
| `source` | string | Source component |

## MaidRunner Class

### Initialization

```python
from maid_lsp.validation.runner import MaidRunner, ValidationMode

# Use maid from PATH
runner = MaidRunner()

# Or specify path
runner = MaidRunner(maid_runner_path="/usr/local/bin/maid")

# With custom timeout
runner = MaidRunner(timeout=30.0)
```

### Validation

```python
from pathlib import Path

result = await runner.validate(
    manifest_path=Path("manifests/task-001.manifest.json"),
    mode=ValidationMode.IMPLEMENTATION,
)

if result.success:
    print("Validation passed!")
else:
    for error in result.errors:
        print(f"{error.code}: {error.message}")
```

### Error Handling

The runner handles various error conditions:

| Condition | Handling |
|-----------|----------|
| maid-runner not found | `RuntimeError` on initialization |
| Validation timeout | Returns `ValidationResult` with timeout error |
| Invalid JSON output | Returns `ValidationResult` with parse error |
| Process failure | Returns `ValidationResult` with error message |

## Conversion to LSP Diagnostics

The `parser.py` module converts validation results to LSP diagnostics:

```python
from maid_lsp.validation.parser import validation_result_to_diagnostics

diagnostics = validation_result_to_diagnostics(
    result=validation_result,
    default_uri="file:///project/manifests/task-001.manifest.json",
)

# Publish to client
server.text_document_publish_diagnostics(
    PublishDiagnosticsParams(
        uri=document_uri,
        diagnostics=diagnostics,
    )
)
```

### Error Code Mapping

Validation errors are mapped to MAID diagnostic codes:

| maid-runner Error | LSP Diagnostic Code |
|-------------------|---------------------|
| Schema errors | `MAID-001` |
| Missing fields | `MAID-002` |
| File not found | `MAID-003` |
| Artifact errors | `MAID-004` |
| Behavioral errors | `MAID-005` |
| Implementation errors | `MAID-006` |
| Chain errors | `MAID-007` |
| Coherence warnings | `MAID-008` |

## Prerequisites

### maid-runner Installation

The maid-runner CLI must be installed and accessible in PATH:

```bash
# Using pip
pip install maid-runner

# Using uv
uv tool install maid-runner

# Using pipx
pipx install maid-runner
```

### Version Requirements

| Component | Minimum Version | Notes |
|-----------|-----------------|-------|
| maid-runner | 0.8.0 | For `--json-output` support |
| Python | 3.10 | For LSP server |

### JSON Output Feature

**Note:** The `--json-output` flag needs to be added to maid-runner as a prerequisite for LSP integration. This is tracked as a dependency in the implementation plan.

## Performance Considerations

### Debouncing

Document changes are debounced to avoid excessive validation:

```python
from maid_lsp.utils.debounce import validation_debouncer

async def on_document_change(uri: str):
    await validation_debouncer.debounce(
        key=uri,
        func=lambda: validate_and_publish(uri),
    )
```

Default debounce delay: 100ms

### Async Execution

All validation runs asynchronously to keep the LSP server responsive:

```python
# Non-blocking validation
result = await runner.validate(manifest_path, mode)
```

### Timeouts

Default timeout: 10 seconds

Configurable via server initialization options:

```json
{
  "initializationOptions": {
    "maid.validation.timeout": 15000
  }
}
```

## Troubleshooting

### Common Issues

**maid-runner not found:**
```
RuntimeError: maid-runner not found in PATH. Install it with: pip install maid-runner
```
Solution: Install maid-runner and ensure it's in PATH.

**Validation timeout:**
```
MAID-TIMEOUT: Validation timed out after 10s
```
Solution: Increase timeout or check for complex manifest chains.

**JSON parse error:**
```
MAID-PARSE-ERROR: Failed to parse validation output
```
Solution: Ensure maid-runner version supports `--json-output`.

### Debug Logging

Enable verbose logging for troubleshooting:

```bash
maid-lsp --stdio --verbose
```

Or set environment variable:
```bash
MAID_LSP_LOG_LEVEL=DEBUG maid-lsp --stdio
```
