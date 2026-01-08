"""CLI entry point for maid-lsp.

This module provides the command-line interface for the MAID LSP server,
supporting argparse for configuration and stdio transport.
"""

import argparse

from maid_lsp import __version__
from maid_lsp.server import create_server


def main() -> None:
    """CLI entry point with argparse.

    Parses command-line arguments and starts the LSP server with the
    appropriate configuration.
    """
    parser = argparse.ArgumentParser(
        prog="maid-lsp",
        description="MAID Language Server Protocol implementation",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"maid-lsp {__version__}",
    )
    parser.add_argument(
        "--stdio",
        action="store_true",
        help="Use stdio transport (default)",
    )

    parser.parse_args()

    # Default to stdio mode
    start_server(mode="stdio")


def start_server(mode: str = "stdio") -> None:
    """Start the LSP server.

    Creates the LSP server using create_server() and starts it with
    the specified transport mode.

    Args:
        mode: The transport mode. Currently supports "stdio" (default).
    """
    server = create_server()

    if mode == "stdio":
        server.start_io()


if __name__ == "__main__":
    main()
