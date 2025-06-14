#!/bin/bash
set -e

echo "Running Python linters..."

# Run black (code formatter)
echo "Running black..."
python -m black .

# Run ruff (fast linter)
echo "Running ruff..."
python -m ruff check .

# Run mypy (static type checker)
echo "Running mypy..."
python -m mypy .

echo "All linters completed successfully!"
