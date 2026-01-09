# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.7] - 2026-01-10

### Fixed
- Informational diagnostics (I103) now correctly display as informational messages instead of errors
- Diagnostic codes starting with "I" are now properly mapped to Information severity level

## [0.1.6] - 2026-01-10

### Fixed
- Run maid validate from project root containing manifests directory for proper path resolution
- Merge auto-release into publish workflow and add branch cleanup for cleaner CI/CD

## [0.1.5] - 2026-01-09

### Changed
- Bump maid-runner dependency from >=0.9.1 to >=0.9.2


## [0.1.4] - 2026-01-09

### Changed
- Bump maid-runner dependency to >=0.9.1 for latest features and fixes

### Removed
- Claude Code plugin auto-install script (users should use LSP directly)
- Claude Code plugin files (streamlined to LSP-only support)

### Fixed
- Use .json extension for manifest files to ensure LSP compatibility with Claude Code

## [0.1.3] - 2026-01-09

### Changed
- Always use `--use-manifest-chain` flag for all validation commands to ensure manifest chain validation is consistently applied

### Fixed
- Validation now properly validates using the manifest chain for all validation operations

## [0.1.2] - 2025-12-XX

### Added
- Core LSP implementation with diagnostics, code actions, and hover support
- Real-time validation of MAID manifests
- Debouncing for document changes (100ms delay)
- Support for VS Code, JetBrains IDEs, and Claude Code

[Unreleased]: https://github.com/mamertofabian/maid-lsp/compare/v0.1.7...HEAD
[0.1.7]: https://github.com/mamertofabian/maid-lsp/compare/v0.1.6...v0.1.7
[0.1.6]: https://github.com/mamertofabian/maid-lsp/compare/v0.1.5...v0.1.6
[0.1.5]: https://github.com/mamertofabian/maid-lsp/compare/v0.1.4...v0.1.5
[0.1.4]: https://github.com/mamertofabian/maid-lsp/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/mamertofabian/maid-lsp/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/mamertofabian/maid-lsp/compare/v0.1.0...v0.1.2
