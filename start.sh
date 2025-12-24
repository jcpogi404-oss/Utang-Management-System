#!/bin/bash
# Startup script for Render deployment

echo "Starting Utang Management System..."
echo "Using app_sqlite.py with SQLite database"

# Set default port if not provided
export PORT=${PORT:-10000}

# Ensure DB directory exists
mkdir -p /opt/render/project/src

# Start the application
exec gunicorn app_sqlite:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
