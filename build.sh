#!/usr/bin/env bash
# Exit if any command fails
set -o errexit  

# Install dependencies (Render already does pip install -r requirements.txt, but this is safe)
pip install -r requirements.txt

# Run database migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput
