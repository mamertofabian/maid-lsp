"""Behavioral tests for Task 010: CLI Entry Point.

These tests verify that the CLI entry point (maid_lsp/__main__.py) provides
a properly functioning command-line interface with argparse for configuration
and stdio transport support for the LSP server.
"""

from unittest.mock import MagicMock, patch

import pytest

from maid_lsp.__main__ import main, start_server


class TestMainFunction:
    """Test main() function - CLI entry point."""

    def test_main_exists_and_callable(self) -> None:
        """main function should exist and be callable."""
        assert main is not None
        assert callable(main)

    def test_main_help_flag(self, capsys: pytest.CaptureFixture[str]) -> None:
        """main should handle --help flag and print usage information."""
        with patch("sys.argv", ["maid-lsp", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            # --help should exit with code 0
            assert exc_info.value.code == 0

        captured = capsys.readouterr()
        # Help output should contain usage information
        assert "usage:" in captured.out.lower() or "maid-lsp" in captured.out.lower()

    def test_main_version_flag(self, capsys: pytest.CaptureFixture[str]) -> None:
        """main should handle --version flag and print version information."""
        with patch("sys.argv", ["maid-lsp", "--version"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            # --version should exit with code 0
            assert exc_info.value.code == 0

        captured = capsys.readouterr()
        # Version output should contain version string
        output = captured.out + captured.err
        assert len(output.strip()) > 0, "Version output should not be empty"

    def test_main_stdio_mode_option(self) -> None:
        """main should accept --stdio mode option."""
        with (
            patch("sys.argv", ["maid-lsp", "--stdio"]),
            patch(
                "maid_lsp.__main__.start_server", return_value=None
            ) as mock_start,
        ):
            main()

            # start_server should be called with stdio mode
            mock_start.assert_called_once()
            call_kwargs = mock_start.call_args
            # Check that mode is "stdio" either as positional or keyword arg
            if call_kwargs.args:
                assert call_kwargs.args[0] == "stdio"
            elif call_kwargs.kwargs:
                assert call_kwargs.kwargs.get("mode") == "stdio"

    def test_main_calls_start_server(self) -> None:
        """main should call start_server when run without help/version flags."""
        with (
            patch("sys.argv", ["maid-lsp", "--stdio"]),
            patch(
                "maid_lsp.__main__.start_server", return_value=None
            ) as mock_start,
        ):
            main()

            mock_start.assert_called_once()


class TestStartServerFunction:
    """Test start_server() function - Server startup."""

    def test_start_server_exists_and_callable(self) -> None:
        """start_server function should exist and be callable."""
        assert start_server is not None
        assert callable(start_server)

    def test_start_server_accepts_mode_parameter(self) -> None:
        """start_server should accept a mode parameter."""
        mock_server = MagicMock()
        mock_server.start_io = MagicMock()

        with patch(
            "maid_lsp.__main__.create_server", return_value=mock_server
        ) as mock_create:
            start_server(mode="stdio")

            # create_server should be called
            mock_create.assert_called_once()

    def test_start_server_default_mode_is_stdio(self) -> None:
        """start_server should default to stdio mode."""
        mock_server = MagicMock()
        mock_server.start_io = MagicMock()

        with patch(
            "maid_lsp.__main__.create_server", return_value=mock_server
        ) as mock_create:
            # Call without mode argument
            start_server()

            # Server should be created
            mock_create.assert_called_once()
            # start_io should be called for stdio mode
            mock_server.start_io.assert_called_once()

    def test_start_server_calls_create_server(self) -> None:
        """start_server should call create_server to create the LSP server."""
        mock_server = MagicMock()
        mock_server.start_io = MagicMock()

        with patch(
            "maid_lsp.__main__.create_server", return_value=mock_server
        ) as mock_create:
            start_server(mode="stdio")

            mock_create.assert_called_once()

    def test_start_server_starts_io_for_stdio_mode(self) -> None:
        """start_server should call server.start_io() for stdio mode."""
        mock_server = MagicMock()
        mock_server.start_io = MagicMock()

        with patch(
            "maid_lsp.__main__.create_server", return_value=mock_server
        ):
            start_server(mode="stdio")

            mock_server.start_io.assert_called_once()


class TestCLIIntegration:
    """Integration tests for CLI behavior."""

    def test_cli_module_is_main_module(self) -> None:
        """__main__.py should be usable as entry point."""
        # The module should define main and start_server
        from maid_lsp.__main__ import main, start_server

        assert main is not None
        assert start_server is not None

    def test_main_with_mocked_server(self) -> None:
        """main should work end-to-end with mocked server."""
        mock_server = MagicMock()
        mock_server.start_io = MagicMock()

        with (
            patch("sys.argv", ["maid-lsp", "--stdio"]),
            patch(
                "maid_lsp.__main__.create_server", return_value=mock_server
            ),
        ):
            main()

            # Server should have been started
            mock_server.start_io.assert_called_once()

    def test_default_execution_starts_stdio(self) -> None:
        """Running main with no args should default to stdio mode."""
        mock_server = MagicMock()
        mock_server.start_io = MagicMock()

        with (
            patch("sys.argv", ["maid-lsp"]),
            patch(
                "maid_lsp.__main__.create_server", return_value=mock_server
            ),
        ):
            main()

            # Default should start stdio server
            mock_server.start_io.assert_called_once()
