#!/bin/bash
# Auto-install maid-lsp if not already installed
set -e

if command -v maid-lsp &> /dev/null; then
    exit 0
fi

echo "Installing maid-lsp..."

if command -v uv &> /dev/null; then
    uv tool install maid-lsp 2>/dev/null || uv pip install --system maid-lsp
elif command -v pipx &> /dev/null; then
    pipx install maid-lsp
else
    pip install --user maid-lsp
fi

echo "maid-lsp installed successfully"
