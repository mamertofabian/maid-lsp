# Testing the MAID LSP Server

This guide covers practical ways to test the LSP server in real environments.

## Quick Start: Manual Testing

### 1. Test in VS Code / Cursor

1. **Install the extension** (if available) or configure manually:
   ```json
   // .vscode/settings.json
   {
     "maid-lsp.serverPath": "/path/to/maid-lsp/venv/bin/maid-lsp",
     "maid-lsp.enable": true
   }
   ```

2. **Open a manifest file** from `manifests/` directory

3. **Verify features work**:
   - **Diagnostics**: Edit the manifest and see errors/warnings appear
   - **Hover**: Hover over artifact references to see information
   - **Go to Definition**: Ctrl+Click (Cmd+Click on Mac) on references
   - **Find References**: Right-click → "Find All References"
   - **Code Actions**: Click the lightbulb icon on errors

### 2. Test via Command Line (stdio)

You can manually test the server by sending LSP messages:

```bash
# Start the server
uv run maid-lsp --stdio

# In another terminal, use a tool like `lsp-test` or create a simple client
```

### 3. Test with Real Manifest Files

Use the existing manifests in `manifests/` directory:

```bash
# Test with a valid manifest
cat manifests/task-001-package-init.manifest.json | # send to server

# Test with an invalid manifest (introduce errors)
# Edit a manifest to have missing fields, then test
```

## Automated Integration Testing

### Using pytest with LSP Client

Run the integration tests:

```bash
uv run pytest tests/test_lsp_integration.py -v
```

### Testing Individual Features

```bash
# Test diagnostics
uv run pytest tests/test_task_006_diagnostics.py -v

# Test hover
uv run pytest tests/test_task_008_hover.py -v

# Test definition
uv run pytest tests/test_task_013_definition.py -v

# Test references
uv run pytest tests/test_task_014_references.py -v
```

## Testing Checklist

When testing new features or changes:

- [ ] **Diagnostics appear** when opening a manifest file
- [ ] **Diagnostics update** when editing the file (with debouncing)
- [ ] **Diagnostics clear** when closing the file
- [ ] **Hover works** on artifact references
- [ ] **Go to Definition** navigates to correct location
- [ ] **Find References** shows all usages
- [ ] **Code Actions** appear for fixable errors
- [ ] **Code Actions execute** correctly when applied
- [ ] **Server handles errors** gracefully (invalid JSON, missing files, etc.)
- [ ] **Performance** is acceptable (validation completes in <1s for typical manifests)

## Testing with Different Manifest Scenarios

### Valid Manifest
```json
{
  "goal": "Test valid manifest",
  "taskType": "create",
  "creatableFiles": ["test.py"],
  "expectedArtifacts": {
    "file": "test.py",
    "contains": [{"type": "function", "name": "test"}]
  }
}
```

### Invalid Manifest (Missing Fields)
```json
{
  "goal": "Test invalid manifest"
}
```

### Manifest with File References
```json
{
  "goal": "Test file references",
  "editableFiles": ["src/main.py"],
  "readonlyFiles": ["src/utils.py"]
}
```

## Debugging Tips

### Enable Logging

Set environment variable for verbose logging:

```bash
MAID_LSP_LOG_LEVEL=DEBUG uv run maid-lsp --stdio
```

### Check Server Output

When running via stdio, the server logs to stderr. Capture it:

```bash
uv run maid-lsp --stdio 2> server.log
```

### Test with Minimal Setup

Create a minimal test manifest:

```bash
# Create test manifest
cat > /tmp/test.manifest.json <<EOF
{
  "goal": "Minimal test",
  "taskType": "create",
  "creatableFiles": ["test.py"],
  "expectedArtifacts": {
    "file": "test.py",
    "contains": []
  }
}
EOF

# Test with it
# (Open in editor or use LSP client)
```

## Performance Testing

### Measure Validation Time

```python
import time
from maid_lsp.validation.runner import MaidRunner, ValidationMode
from pathlib import Path

runner = MaidRunner()
start = time.time()
result = await runner.validate(
    Path("manifests/task-001-package-init.manifest.json"),
    ValidationMode.IMPLEMENTATION
)
elapsed = time.time() - start
print(f"Validation took {elapsed:.3f}s")
```

### Test Debouncing

1. Make rapid edits to a manifest
2. Verify that validation doesn't run on every keystroke
3. Verify that validation runs after typing stops (100ms delay)

## Integration with CI/CD

Add to your CI pipeline:

```yaml
# .github/workflows/test.yml
- name: Run LSP integration tests
  run: |
    uv run pytest tests/test_lsp_integration.py -v
```

## Troubleshooting

### Server doesn't start
- Check `maid-runner` is installed: `which maid`
- Check Python version: `python --version` (needs 3.10+)
- Check dependencies: `uv sync --all-extras`

### Diagnostics don't appear
- Verify manifest file matches `*.manifest.json` pattern
- Check server logs for errors
- Verify `maid-runner` can validate the file manually:
  ```bash
  maid validate manifests/task-001-package-init.manifest.json --json-output
  ```

### Features don't work
- Check that handlers are registered in `server.py`
- Verify capability registration in LSP initialization
- Check server logs for handler errors
