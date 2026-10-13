#!/bin/bash
set -e

echo "Building FreelanceFlow for Vercel..."

# Ensure staticfiles output directory exists
mkdir -p staticfiles

# Set settings module for static asset compilation
export DJANGO_SETTINGS_MODULE=config.settings.prod

# Install dependencies in the build container environment
if command -v uv &> /dev/null; then
    echo "Using uv to install dependencies..."
    uv pip install --system -r requirements.txt
else
    echo "Using pip to install dependencies..."
    python3 -m pip install --break-system-packages -r requirements.txt || python3 -m pip install -r requirements.txt
fi

# Run collectstatic to populate staticfiles directory
echo "Collecting static files..."
python3 manage.py collectstatic --noinput --clear

echo "Build complete!"
