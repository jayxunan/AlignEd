import os
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-local-dev-key-for-aligned")
DEBUG = os.environ.get("DEBUG", "False") == "True"

ALLOWED_HOSTS_str = os.environ.get("ALLOWED_HOSTS")
ALLOWED_HOSTS = []
if ALLOWED_HOSTS_str:
    ALLOWED_HOSTS.extend([host.strip() for host in ALLOWED_HOSTS_str.split(",")])

if DEBUG:
    ALLOWED_HOSTS.extend(['127.0.0.1', 'localhost'])
else:
    # fallback if not set in environment
    ALLOWED_HOSTS.append("aligned.onrender.com")

CSRF_TRUSTED_ORIGINS_str = os.environ.get("CSRF_TRUSTED_ORIGINS")
CSRF_TRUSTED_ORIGINS = []
if CSRF_TRUSTED_ORIGINS_str:
    CSRF_TRUSTED_ORIGINS.extend([origin.strip() for origin in CSRF_TRUSTED_ORIGINS_str.split(",")])

if DEBUG:
    CSRF_TRUSTED_ORIGINS.append("http://127.0.0.1:8000")
else:
    CSRF_TRUSTED_ORIGINS.append("https://aligned.onrender.com")

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

INSTALLED_APPS = [
    'recommender',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'aligned.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
WSGI_APPLICATION = 'aligned.wsgi.application'

# db
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 2fa
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True") == "True"
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL")

LOGIN_URL = 'login'
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}
