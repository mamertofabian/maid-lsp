# Claude Code Integration

This document describes how to integrate the MAID LSP server with Claude Code.

## Overview

Claude Code has native support for Language Server Protocol (LSP) servers through its plugin system. The MAID LSP server can be configured as a Claude Code plugin to provide real-time manifest validation during AI-assisted development.

## Plugin Structure

The MAID LSP plugin is bundled within the `maid-lsp` repository:

```
maid-lsp/
├── .claude-plugin/
│   └── plugin.json      # Plugin manifest
├── .lsp.json            # LSP server configuration
└── maid_lsp/            # Server implementation
```

## Installation

### Step 1: Install maid-lsp

```bash
# Using pip
pip install maid-lsp

# Using uv
uv tool install maid-lsp

# Using pipx
pipx install maid-lsp
```

### Step 2: Verify Installation

```bash
# Check that maid-lsp is in PATH
which maid-lsp

# Test server startup
maid-lsp --version
```

### Step 3: Enable Plugin in Claude Code

The plugin can be enabled in several ways:

**Option A: Project-level plugin**
```bash
# In your project directory
mkdir -p .claude-plugin
cp /path/to/maid-lsp/.claude-plugin/plugin.json .claude-plugin/
cp /path/to/maid-lsp/.lsp.json .
```

**Option B: Global plugin (coming soon)**
```bash
# Install from Claude Code plugin registry
claude plugin install maid-lsp
```

## Configuration Files

### Plugin Manifest (`.claude-plugin/plugin.json`)

```json
{
  "name": "maid-lsp",
  "version": "0.1.0",
  "description": "MAID methodology validation for Claude Code",
  "author": "MAID Team",
  "homepage": "https://github.com/mamertofabian/maid-lsp",
  "lspServers": "see .lsp.json"
}
```

### LSP Configuration (`.lsp.json`)

```json
{
  "maid": {
    "command": "maid-lsp",
    "args": ["--stdio"],
    "extensionToLanguage": {
      ".manifest.json": "maid-manifest"
    },
    "initializationOptions": {
      "maid.validation.debounceMs": 100,
      "maid.validation.timeout": 10000
    },
    "transport": "stdio",
    "startupTimeout": 5000,
    "restartOnCrash": true,
    "maxRestarts": 3
  }
}
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `command` | string | required | LSP server executable |
| `args` | string[] | `[]` | Command-line arguments |
| `extensionToLanguage` | object | required | File extension mappings |
| `initializationOptions` | object | `{}` | Server initialization options |
| `transport` | string | `"stdio"` | Transport method |
| `startupTimeout` | number | `5000` | Startup timeout (ms) |
| `restartOnCrash` | boolean | `true` | Auto-restart on crash |
| `maxRestarts` | number | `3` | Max restart attempts |

## Features in Claude Code

### Real-time Diagnostics

When you open or edit a `.manifest.json` file, Claude Code receives validation diagnostics from the MAID LSP server:

- **Errors**: Schema violations, missing fields, artifact mismatches
- **Warnings**: Coherence issues, best practice suggestions

Diagnostics appear:
- In the editor as underlined text
- In the Problems panel
- In Claude's context when discussing the file

### Code Actions

Quick fixes are available for common issues:

1. **Add missing field**: Inserts template for required manifest fields
2. **Create file**: Creates missing referenced files
3. **Generate stub**: Creates artifact stub in target file

### Hover Information

Hover over manifest elements to see:

- **Artifact names**: Type, parameters, return type
- **File paths**: Existence status, full path
- **Field names**: Documentation and examples

## Integration with Claude AI

### Diagnostic Sharing

Claude automatically sees LSP diagnostics, enabling it to:

- Understand validation errors in context
- Suggest fixes based on error messages
- Validate its own manifest modifications

### Workflow Integration

The MAID LSP enhances Claude's workflow:

```
1. User: "Create a manifest for adding user authentication"
2. Claude: Creates manifest file
3. LSP: Validates manifest, reports any issues
4. Claude: Sees diagnostics, adjusts manifest
5. LSP: Confirms validation passes
6. Claude: Proceeds with implementation
```

## Troubleshooting

### Server Not Starting

**Symptom**: No diagnostics appear in editor

**Checks**:
1. Verify maid-lsp is installed: `which maid-lsp`
2. Check Claude Code logs for errors
3. Verify `.lsp.json` syntax is valid

**Solution**:
```bash
# Test server manually
maid-lsp --stdio --verbose
```

### Diagnostics Not Appearing

**Symptom**: Server starts but no diagnostics

**Checks**:
1. Verify file has `.manifest.json` extension
2. Check that maid-runner is installed
3. Review server logs

**Solution**:
```bash
# Enable debug logging
MAID_LSP_LOG_LEVEL=DEBUG maid-lsp --stdio
```

### Slow Validation

**Symptom**: Long delay before diagnostics appear

**Checks**:
1. Complex manifest chain
2. Large project directory
3. maid-runner performance

**Solution**:
```json
// Increase timeout in .lsp.json
{
  "maid": {
    "initializationOptions": {
      "maid.validation.timeout": 30000
    }
  }
}
```

## Debug Logging

Enable detailed logging for troubleshooting:

### Server-side Logging

```json
{
  "maid": {
    "loggingConfig": {
      "args": ["--verbose"],
      "env": {
        "MAID_LSP_LOG_FILE": "${CLAUDE_PLUGIN_LSP_LOG_FILE}"
      }
    }
  }
}
```

Logs are written to `~/.claude/debug/` when Claude Code is started with `--enable-lsp-logging`.

### Log Levels

| Level | Content |
|-------|---------|
| ERROR | Server errors, crashes |
| WARN | Validation timeouts, unexpected states |
| INFO | Validation results, lifecycle events |
| DEBUG | All messages, subprocess output |

## Best Practices

### 1. Install maid-runner First

The LSP server requires maid-runner:
```bash
pip install maid-runner maid-lsp
```

### 2. Use Project-level Configuration

Place `.lsp.json` in project root for consistent behavior:
```
my-project/
├── .lsp.json
├── manifests/
└── src/
```

### 3. Configure Appropriate Timeouts

For large projects, increase validation timeout:
```json
{
  "initializationOptions": {
    "maid.validation.timeout": 30000
  }
}
```

### 4. Enable Auto-restart

Keep `restartOnCrash: true` for resilience:
```json
{
  "restartOnCrash": true,
  "maxRestarts": 5
}
```

## Related Documentation

- [Architecture](architecture.md) - System design
- [Capabilities](capabilities.md) - LSP features
- [Integration](integration.md) - maid-runner integration
- [Performance](performance.md) - Performance specs
