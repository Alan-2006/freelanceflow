#!/bin/bash
set -e

echo "Building FreelanceFlow for Vercel..."

# Ensure staticfiles output directory exists
mkdir -p staticfiles

# Set settings module for static asset compilation
export DJANGO_SETTINGS_MODULE=config.settings.prod

# Find Python binary
if command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "Python not found in build container!"
    exit 1
fi

echo "Using Python binary: $($PYTHON_CMD --version)"

# Install dependencies required for collectstatic
$PYTHON_CMD -m pip install --break-system-packages -r requirements.txt || $PYTHON_CMD -m pip install -r requirements.txt

# Run collectstatic
$PYTHON_CMD manage.py collectstatic --noinput --clear

echo "FreelanceFlow static build complete!"
