# MAID LSP Capabilities

This document defines the LSP capabilities provided by the MAID Language Server.

## Overview

The MAID LSP server implements a subset of the Language Server Protocol focused on manifest validation and developer assistance.

## Supported Capabilities

### Document Synchronization

| Feature | Support | Notes |
|---------|---------|-------|
| `textDocument/didOpen` | ✅ | Triggers initial validation |
| `textDocument/didChange` | ✅ | Incremental sync, debounced |
| `textDocument/didClose` | ✅ | Clears diagnostics |
| `textDocument/didSave` | ❌ | Not needed with change events |

### Diagnostics

| Feature | Support | Notes |
|---------|---------|-------|
| `textDocument/publishDiagnostics` | ✅ | Push model |
| `textDocument/diagnostic` (pull) | ❌ | Not implemented |
| `workspace/diagnostic` | ❌ | Future enhancement |

### Language Features

| Feature | Support | Notes |
|---------|---------|-------|
| `textDocument/codeAction` | ✅ | Quick fixes |
| `textDocument/hover` | ✅ | Artifact information |
| `textDocument/definition` | ✅ | Bidirectional navigation (manifest ↔ source) |
| `textDocument/references` | ✅ | Find references across manifests, tests, and source files |
| `textDocument/completion` | ❌ | Future enhancement |

## Diagnostic Codes

The MAID LSP uses structured error codes to categorize validation errors.

### Error Codes

| Code | Severity | Description |
|------|----------|-------------|
| `MAID-001` | Error | Schema validation errors (invalid JSON structure) |
| `MAID-002` | Error | Missing required fields (goal, expectedArtifacts, etc.) |
| `MAID-003` | Error | File reference errors (files not found) |
| `MAID-004` | Error | Artifact validation errors (missing/extra artifacts) |
| `MAID-005` | Error | Behavioral validation errors (tests don't USE artifacts) |
| `MAID-006` | Error | Implementation validation errors (code doesn't DEFINE artifacts) |
| `MAID-007` | Error | Manifest chain errors (supersedes conflicts) |
| `MAID-008` | Warning | Coherence validation warnings |

### Diagnostic Structure

Each diagnostic includes:

```typescript
interface MaidDiagnostic {
  range: Range;           // Location in the document
  message: string;        // Human-readable error message
  severity: DiagnosticSeverity;  // Error or Warning
  code: string;           // MAID-XXX code
  source: "maid-lsp";     // Always "maid-lsp"
  relatedInformation?: DiagnosticRelatedInformation[];
}
```

### Example Diagnostics

**Schema Error (MAID-001):**
```json
{
  "range": {"start": {"line": 0, "character": 0}, "end": {"line": 0, "character": 1}},
  "message": "Invalid JSON: Unexpected token at position 0",
  "severity": 1,
  "code": "MAID-001",
  "source": "maid-lsp"
}
```

**Missing Field (MAID-002):**
```json
{
  "range": {"start": {"line": 1, "character": 0}, "end": {"line": 1, "character": 1}},
  "message": "Missing required field: 'goal'",
  "severity": 1,
  "code": "MAID-002",
  "source": "maid-lsp"
}
```

**Artifact Error (MAID-004):**
```json
{
  "range": {"start": {"line": 15, "character": 4}, "end": {"line": 15, "character": 20}},
  "message": "Missing artifact: function 'get_user' not found in src/service.py",
  "severity": 1,
  "code": "MAID-004",
  "source": "maid-lsp",
  "relatedInformation": [
    {
      "location": {"uri": "file:///project/src/service.py", "range": {...}},
      "message": "Expected artifact location"
    }
  ]
}
```

## Code Actions

### Quick Fixes

| Diagnostic | Action | Description |
|------------|--------|-------------|
| `MAID-002` | Add missing field | Inserts template for required field |
| `MAID-003` | Create file | Creates missing referenced file |
| `MAID-004` | Generate stub | Creates artifact stub in target file |

### Code Action Structure

```typescript
interface MaidCodeAction {
  title: string;          // Display text in UI
  kind: CodeActionKind;   // "quickfix"
  diagnostics: Diagnostic[];
  edit: WorkspaceEdit;    // Changes to apply
}
```

### Example Code Action

**Add missing 'goal' field:**
```json
{
  "title": "Add missing 'goal' field",
  "kind": "quickfix",
  "diagnostics": [/* MAID-002 diagnostic */],
  "edit": {
    "changes": {
      "file:///project/manifests/task-001.manifest.json": [
        {
          "range": {"start": {"line": 1, "character": 0}, "end": {"line": 1, "character": 0}},
          "newText": "  \"goal\": \"TODO: Describe the task goal\",\n"
        }
      ]
    }
  }
}
```

## Hover Information

### Supported Hover Targets

| Target | Information Provided |
|--------|---------------------|
| Artifact name | Type, parameters, return type |
| File path | Existence status, full path |
| `taskType` | Description of task type |
| `expectedArtifacts` | Validation mode explanation |

### Hover Content Format

Hover content uses Markdown formatting:

```markdown
**function: get_user**

Retrieves a user by their ID.

| Property | Value |
|----------|-------|
| Type | function |
| Parameters | user_id: int |
| Returns | User |
| Defined in | src/service.py:42 |
```

## Document Types

### Supported File Patterns

| Pattern | Language ID | Features |
|---------|-------------|----------|
| `*.manifest.json` | `maid-manifest` | Full validation |
| `manifests/**/*.json` | `maid-manifest` | Full validation |

### Language Configuration

The server registers for the `maid-manifest` language ID with the following file associations:

```json
{
  "files.associations": {
    "*.manifest.json": "maid-manifest"
  }
}
```

## Server Capabilities Declaration

The server advertises the following capabilities during initialization:

```json
{
  "capabilities": {
    "textDocumentSync": {
      "openClose": true,
      "change": 2,
      "save": false
    },
    "codeActionProvider": {
      "codeActionKinds": ["quickfix"]
    },
    "hoverProvider": true,
    "definitionProvider": true,
    "referencesProvider": true,
    "diagnosticProvider": {
      "interFileDependencies": false,
      "workspaceDiagnostics": false
    }
  }
}
```

## Go-to-Definition

### Supported Navigation

The definition provider supports bidirectional navigation:

- **Manifest → Source File**: Click on an artifact name in a manifest to jump to its definition in the source file
- **Source File → Manifest**: Click on an artifact name in a source file to jump to its definition in the manifest

### Supported Artifact Types

- Functions (module-level and class methods)
- Classes
- Attributes (module-level)

### Example Usage

**From Manifest:**
1. Open a manifest file (e.g., `manifests/task-001.manifest.json`)
2. Position cursor on an artifact name (e.g., `"my_function"`)
3. Use "Go to Definition" (F12 or Ctrl+Click)
4. Editor jumps to the function definition in the source file

**From Source File:**
1. Open a Python source file
2. Position cursor on an artifact name (e.g., `my_function`)
3. Use "Go to Definition" (F12 or Ctrl+Click)
4. Editor jumps to the artifact definition in the manifest file

## Find References

### Supported Search Locations

The references provider searches for artifact references across:

- **Manifest Files**: All manifests that reference the artifact
- **Test Files**: Test files that import or use the artifact
- **Source Files**: Source files that import or use the artifact

### Example Usage

1. Position cursor on an artifact name (in manifest or source file)
2. Use "Find References" (Shift+F12)
3. Editor shows all locations where the artifact is referenced

### Reference Types Detected

- Artifact definitions in manifests
- Function/method calls
- Import statements
- Attribute access
- Name references (excluding definitions)

## Future Capabilities

### Planned for v2.1

- **Completion Provider**: Suggest field names, artifact types, file paths
- **Workspace Diagnostics**: Validate all manifests in workspace
- **Semantic Tokens**: Syntax highlighting for manifest structure

### Under Consideration

- **Rename Provider**: Rename artifacts across manifest and source
- **Document Symbols**: Outline view of manifest structure
- **Folding Range**: Collapse sections of large manifests
