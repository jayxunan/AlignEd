#!/usr/bin/env bash
# Exit if any command fails
set -o errexit  

pip install -r requirements.txt

python manage.py migrate --noinput
python manage.py collectstatic --noinput
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('alignedadmin', 'gyulfreak@gmail.com', 'y23adr4amnw0')" | python manage.py shell