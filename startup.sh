#!/bin/bash
set -e

echo "🔄 Running database migrations..."
alembic upgrade head

echo "🚀 Starting Uncle Ron Bot..."
exec uv run python -m app.main