#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py migrate --noinput
python manage.py collectstatic --noinput

python - <<END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='alignedadmin').exists():
    User.objects.create_superuser('alignedadmin', 'gyulfreak@gmail.com', 'y23adr4amnw0')
END
