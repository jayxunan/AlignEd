#!/usr/bin/env bash
# Exit if any command fails
set -o errexit  

pip install -r requirements.txt

python manage.py migrate --noinput
python manage.py collectstatic --noinput
