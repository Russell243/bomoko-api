from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Development convenience
CORS_ALLOW_ALL_ORIGINS = True

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Celery Development Config
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Email backend for dev
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Static files for dev
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
