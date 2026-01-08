"""Behavioral tests for Task 001: Package initialization.

These tests verify that the maid_lsp package is properly initialized
with version information and public exports.
"""


class TestPackageInit:
    """Test maid_lsp package initialization."""

    def test_package_has_version(self) -> None:
        """Package should expose __version__ attribute."""
        import maid_lsp

        assert hasattr(maid_lsp, "__version__")
        assert isinstance(maid_lsp.__version__, str)
        assert len(maid_lsp.__version__) > 0

    def test_version_format(self) -> None:
        """Version should follow semantic versioning format."""
        import maid_lsp

        version = maid_lsp.__version__
        # Should be in format X.Y.Z (at minimum)
        parts = version.split(".")
        assert len(parts) >= 2, f"Version '{version}' should have at least major.minor"
        # First two parts should be numeric
        assert parts[0].isdigit(), f"Major version '{parts[0]}' should be numeric"
        assert parts[1].isdigit(), f"Minor version '{parts[1]}' should be numeric"

    def test_package_has_all(self) -> None:
        """Package should expose __all__ for explicit public API."""
        import maid_lsp

        assert hasattr(maid_lsp, "__all__")
        assert isinstance(maid_lsp.__all__, list)

    def test_all_contains_strings(self) -> None:
        """__all__ should contain only string names."""
        import maid_lsp

        for item in maid_lsp.__all__:
            assert isinstance(item, str), f"__all__ item '{item}' should be a string"

    def test_package_is_importable(self) -> None:
        """Package should be importable without errors."""
        # This test passes if the import succeeds
        import maid_lsp

        assert maid_lsp is not None
