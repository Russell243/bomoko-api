from .base import *
from django.core.exceptions import ImproperlyConfigured

DEBUG = False

# Support for Cloud Run, Render and custom domains
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['bomoko.app', '.a.run.app', '.onrender.com', 'localhost', '127.0.0.1'])
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=['https://*.onrender.com', 'https://bomoko.app'])

# Database configuration: Optimized for Google Cloud SQL
# In Cloud Run, DATABASE_URL should look like:
# postgresql://USER:PASSWORD@/DB_NAME?host=/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME
# Support both DATABASE_URL and discrete variables
if env('DATABASE_URL', default=''):
    try:
        DATABASES = {
            'default': env.db('DATABASE_URL')
        }
    except Exception:
        # Fallback to discrete variables if URL parsing fails (e.g. Unicode/Special chars)
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': env('DB_NAME', default='postgres'),
                'USER': env('DB_USER', default='postgres'),
                'PASSWORD': env('DB_PASSWORD', default=''),
                'HOST': env('DB_HOST', default=''),
                'PORT': env('DB_PORT', default='5432'),
            }
        }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': env('DB_NAME', default='postgres'),
            'USER': env('DB_USER', default='postgres'),
            'PASSWORD': env('DB_PASSWORD', default=''),
            'HOST': env('DB_HOST', default=''),
            'PORT': env('DB_PORT', default='5432'),
        }
    }

# Celery Production Config
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')

# Sentry monitoring
import sentry_sdk
if env('SENTRY_DSN', default=''):
    sentry_sdk.init(
        dsn=env('SENTRY_DSN'),
        traces_sample_rate=0.2,
        profiles_sample_rate=0.2,
    )

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')

# Security headers
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=False)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_REFERRER_POLICY = 'same-origin'

# Hard fail if critical security values are unsafe in production
if SECRET_KEY == 'django-insecure-local-dev-key':
    raise ImproperlyConfigured("SECRET_KEY must be configured in production.")
if '*' in ALLOWED_HOSTS:
    raise ImproperlyConfigured("ALLOWED_HOSTS cannot contain '*' in production.")
if SOS_AUDIO_ENCRYPTION_ENABLED and not SOS_AUDIO_ENCRYPTION_KEY:
    raise ImproperlyConfigured("SOS_AUDIO_ENCRYPTION_KEY must be configured in production when audio encryption is enabled.")
CORS_ALLOW_ALL_ORIGINS = env.bool('CORS_ALLOW_ALL_ORIGINS', default=False)
