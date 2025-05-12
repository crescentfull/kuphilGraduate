#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Add the project directory to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Collect static files


# Run database migrations
python manage.py migrate 