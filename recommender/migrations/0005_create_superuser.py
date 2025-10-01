from django.db import migrations
import os

def create_superuser(apps, schema_editor):
    """
    Creates a superuser account from environment variables if it doesn't exist.
    """
    User = apps.get_model('auth', 'User')

    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME')
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')

    # Only create the superuser if all three environment variables are provided
    # and the user does not already exist.
    if ADMIN_USERNAME and ADMIN_EMAIL and ADMIN_PASSWORD:
        if not User.objects.filter(username=ADMIN_USERNAME).exists():
            print(f"Creating superuser '{ADMIN_USERNAME}'...")
            User.objects.create_superuser(
                username=ADMIN_USERNAME,
                email=ADMIN_EMAIL,
                password=ADMIN_PASSWORD
            )
        else:
            print(f"Superuser '{ADMIN_USERNAME}' already exists. Skipping.")
    else:
        print("Superuser credentials not found in environment variables. Skipping.")


class Migration(migrations.Migration):

    dependencies = [
        # --- THIS IS THE FIX ---
        # It now correctly points to your previous migration file.
        ('recommender', '0004_assessment_feedback_rating_1_and_more'), 
    ]

    operations = [
        migrations.RunPython(create_superuser),
    ]

