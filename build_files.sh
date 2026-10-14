#!/bin/bash
set -e

echo "Building FreelanceFlow for Vercel..."

# Ensure staticfiles output directory exists
mkdir -p staticfiles

# Set settings module for static asset compilation
export DJANGO_SETTINGS_MODULE=config.settings.prod

# Install dependencies in the build container environment using Python 3.12
if command -v uv &> /dev/null; then
    echo "Using uv to set up Python 3.12 and install dependencies..."
    uv venv --python 3.12 .build_venv
    source .build_venv/bin/activate
    uv pip install -r requirements.txt
    python manage.py collectstatic --noinput --clear
else
    echo "Using pip to install dependencies..."
    python3 -m pip install --break-system-packages -r requirements.txt || python3 -m pip install -r requirements.txt
    python3 manage.py collectstatic --noinput --clear
fi

echo "Build complete!"
