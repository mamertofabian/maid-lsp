---
allowed-tools: Bash(git:*), Bash(python:*), Bash(uv:*), Bash(make:*), Bash(gh:*), Bash(rm:*), Bash(ls:*), Bash(tar:*), Bash(unzip:*), Bash(sleep:*), Edit, Read, TodoWrite, WebFetch
argument-hint: [version-type: patch|minor|major]
description: Prepare and publish a new PyPI release (project)
---

# PyPI Release Automation

Automate the complete PyPI release process including version bumping, changelog updates, building, and publishing via GitHub Actions.

## Your Task

Prepare and publish a new PyPI release for this project. Follow these steps:

1. **Determine Version Number**
   - Read current version from `pyproject.toml`
   - Check recent commits since last release: `git log --oneline -20`
   - Determine version bump type: $ARGUMENTS (default: patch)
     - **patch** (0.1.2 → 0.1.3): Bug fixes, documentation, minor changes
     - **minor** (0.1.2 → 0.2.0): New features, backward-compatible
     - **major** (0.1.2 → 1.0.0): Breaking changes
   - Calculate new version number

2. **Run Code Quality Checks**
   - Run all quality checks FIRST:
     ```bash
     make all          # Runs lint, type-check, and test
     # OR individually:
     make lint         # Fix any linting errors first
     make format       # Format code
     make type-check   # Run type checker
     make test         # Run all tests - MUST PASS
     ```
   - If any checks fail, STOP and report errors to user
   - Use `TodoWrite` to track progress

3. **Update Version and Changelog**
   - Update version in BOTH files:
     - `pyproject.toml` (project.version)
     - `maid_lsp/__init__.py` (__version__)
   - Update `CHANGELOG.md`:
     - If file doesn't exist, create it with proper header following [Keep a Changelog](https://keepachangelog.com/)
     - Add new version section with today's date (YYYY-MM-DD format)
     - Categorize changes under: Fixed, Added, Changed, Removed
     - Update comparison links at bottom (if applicable)
   - Review git commits to write accurate changelog entries

4. **Build Distribution Packages**
   - Clean old artifacts: `make clean` or `rm -rf dist/ build/ *.egg-info`
   - Build packages using uv: `uv build` (or `python -m build` if preferred)
   - Verify artifacts: `ls -lh dist/`
   - Check contents: `tar -tzf dist/*.tar.gz | head -30`
   - Validate with twine (if available): `uv run twine check dist/*` or `python -m twine check dist/*`

5. **Automated Release via GitHub Actions**
   - Stage and commit changes with descriptive title:
     ```bash
     git add pyproject.toml maid_lsp/__init__.py CHANGELOG.md
     # Parse the changelog to extract the main feature/change for this version
     # Use a descriptive title that summarizes what's in the release
     git commit -m "release: vX.Y.Z - [Main feature from changelog]

     - [Summary of key changes]
     - [One-line descriptions from changelog]"

     # Examples of good commit titles:
     # "release: v0.1.3 - Always use --use-manifest-chain for validation"
     # "release: v0.2.0 - Additional code actions support"
     # "release: v0.1.0 - Initial release"
     ```
   - Push to main: `git push origin main`
   - Create and push version tag:
     ```bash
     git tag vX.Y.Z
     git push origin vX.Y.Z
     ```
   - Monitor GitHub Actions workflow:
     ```bash
     gh run list --limit 2
     sleep 60 && gh run list --limit 2
     ```
   - Note: The workflow (`.github/workflows/publish.yml`) triggers on version tags (`v*`)
     - Runs tests on Python 3.10, 3.11, 3.12, 3.13
     - Builds packages using `python -m build`
     - Publishes to PyPI on tag push
     - Creates GitHub release with Sigstore-signed artifacts

6. **Verify Release**
   - Check GitHub release: `gh release view vX.Y.Z`
   - Verify PyPI publication: `WebFetch` to https://pypi.org/project/maid-lsp/
   - Confirm artifacts include Sigstore signatures

## Important Notes

- **NEVER skip tests**: All tests must pass before releasing
- **Version format**: Use semantic versioning (MAJOR.MINOR.PATCH)
- **Version sync**: Update version in BOTH `pyproject.toml` and `maid_lsp/__init__.py`
- **Changelog format**: Follow [Keep a Changelog](https://keepachangelog.com/)
- **Build tool**: Use `uv build` locally (or `python -m build`). CI uses `python -m build`
- **GitHub Actions**: The workflow (`.github/workflows/publish.yml`) automatically publishes to PyPI on version tags (`v*`)
- **Artifacts**: GitHub Actions signs artifacts with Sigstore for security
- **Package name**: `maid-lsp` (not `maid-runner`)

## Expected Outcomes

1. ✅ Version bumped in `pyproject.toml` and `maid_lsp/__init__.py`
2. ✅ Changelog updated with release notes (created if missing)
3. ✅ All tests passing (lint, type-check, test)
4. ✅ Distribution packages built and validated
5. ✅ Git commit and tag created
6. ✅ GitHub Actions workflow triggered
7. ✅ Package published to PyPI
8. ✅ GitHub release created with Sigstore-signed artifacts

## Error Handling

If any step fails:
- **Tests fail**: Fix issues before continuing. Run `make all` to see all failures
- **Build fails**: Check pyproject.toml configuration. Try `uv build` or `python -m build`
- **Version mismatch**: Ensure both `pyproject.toml` and `maid_lsp/__init__.py` have same version
- **GitHub Actions fails**: Check workflow logs with `gh run view <run-id>`
- **PyPI publish fails**: Verify PyPI token is configured in GitHub secrets (environment: pypi)
- **Changelog missing**: Create it following [Keep a Changelog](https://keepachangelog.com/) format

Report any errors to the user with specific failure details and suggested fixes.
