#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "🚀 Starting Bomoko API Production Entrypoint..."

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

# Run database migrations
echo "🗄️ Running database migrations..."
python manage.py migrate --noinput

# Start the application server
# Using Daphne for ASGI/WebSocket support
echo "🔥 Starting Daphne server..."
exec daphne -b 0.0.0.0 -p $PORT bomoko.asgi:application
