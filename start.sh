#!/usr/bin/env bash
set -e

echo "Installing uv..."
curl -LsSf https://astral.sh/uv/install.sh | sh

echo "Setting up Python environment..."
~/.cargo/bin/uv sync

echo "Running tests..."
~/.cargo/bin/uv run pytest -q

echo "Starting server..."
~/.cargo/bin/uv run python -m src.web_server
