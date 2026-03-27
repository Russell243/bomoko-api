import os
import sys
from pathlib import Path
from datetime import timedelta
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR is bomoko-api/ (two levels up from base.py)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Add the apps directory to the Python path
sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))

# Initialize environ
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# Core runtime mode
DEBUG = env.bool('DEBUG', default=False)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY', default='')
if not SECRET_KEY:
    # Allow local bootstrapping without crashing, but keep a clear value
    SECRET_KEY = 'django-insecure-local-dev-key'

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

# Application definition
INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'channels',
    'django_filters',
    
    # Local apps (will be created in apps/)
    'users.apps.UsersConfig',
    'sos.apps.SosConfig',
    'chat.apps.ChatConfig',
    'medical.apps.MedicalConfig',
    'legal.apps.LegalConfig',
    'forum.apps.ForumConfig',
    'health.apps.HealthConfig',
    'notifications.apps.NotificationsConfig',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'bomoko.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'bomoko.wsgi.application'
ASGI_APPLICATION = 'bomoko.asgi.application'

# REST Framework configure
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_THROTTLE_RATES': {
        'auth_register': '5/hour',
        'auth_login': '10/hour',
        'auth_verify_otp': '10/hour',
        'public_tracking': '120/hour',
        'system_health': '120/hour',
    },
}

# Simple JWT configure
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# Internationalization
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Kinshasa'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS
CORS_ALLOW_ALL_ORIGINS = env.bool('CORS_ALLOW_ALL_ORIGINS', default=False)
CORS_ALLOWED_ORIGINS = env.list(
    'CORS_ALLOWED_ORIGINS',
    default=['http://localhost:8081', 'http://127.0.0.1:8081', 'http://localhost:19006']
)
CSRF_TRUSTED_ORIGINS = env.list(
    'CSRF_TRUSTED_ORIGINS',
    default=['http://localhost:8081', 'http://127.0.0.1:8081', 'http://localhost:19006']
)

# AI Services configuration
GEMINI_API_KEY = env('GEMINI_API_KEY', default='')
OPENAI_API_KEY = env('OPENAI_API_KEY', default='')
ANTHROPIC_API_KEY = env('ANTHROPIC_API_KEY', default='')

TWILIO_ACCOUNT_SID = env('TWILIO_ACCOUNT_SID', default='')
TWILIO_AUTH_TOKEN = env('TWILIO_AUTH_TOKEN', default='')
TWILIO_PHONE_NUMBER = env('TWILIO_PHONE_NUMBER', default='')
AFRICASTALKING_USERNAME = env('AFRICASTALKING_USERNAME', default='sandbox')
AFRICASTALKING_API_KEY = env('AFRICASTALKING_API_KEY', default='')
PUBLIC_TRACKING_BASE_URL = env('PUBLIC_TRACKING_BASE_URL', default='http://localhost:8000')
SOS_TRACKING_TOKEN_TTL_HOURS = env.int('SOS_TRACKING_TOKEN_TTL_HOURS', default=72)

# Debug-only OTP bypass code (must stay empty in production)
OTP_BYPASS_CODE = env('OTP_BYPASS_CODE', default='')
NOTIFICATIONS_ENABLE_PUSH = env.bool('NOTIFICATIONS_ENABLE_PUSH', default=True)
EXPO_PUSH_URL = env('EXPO_PUSH_URL', default='https://exp.host/--/api/v2/push/send')
SOS_MIN_CONTACTS_REQUIRED = env.int('SOS_MIN_CONTACTS_REQUIRED', default=3)
SOS_AUDIO_ENCRYPTION_ENABLED = env.bool('SOS_AUDIO_ENCRYPTION_ENABLED', default=True)
SOS_AUDIO_ENCRYPTION_KEY = env('SOS_AUDIO_ENCRYPTION_KEY', default='')
SOS_AUDIO_RETENTION_ENABLED = env.bool('SOS_AUDIO_RETENTION_ENABLED', default=True)
SOS_AUDIO_RETENTION_DAYS = env.int('SOS_AUDIO_RETENTION_DAYS', default=90)
SOS_AUDIO_MAX_UPLOAD_BYTES = env.int('SOS_AUDIO_MAX_UPLOAD_BYTES', default=5 * 1024 * 1024)
FORUM_BLOCKED_KEYWORDS = env.list('FORUM_BLOCKED_KEYWORDS', default=['viol', 'rape', 'porn', 'pornographie', 'pedophile'])
FORUM_FLAGGED_KEYWORDS = env.list('FORUM_FLAGGED_KEYWORDS', default=['harcelement', 'harcèlement', 'chantage', 'sexe contre points', 'agression'])

# ─── Infrastructure ───────────────────────────────────────────

# Redis / Channels
REDIS_URL = env('REDIS_URL', default='redis://localhost:6379/0')

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [REDIS_URL],
        },
    },
}

# Celery
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULE = {
    'retry-pending-sos-sms-every-minute': {
        'task': 'sos.tasks.retry_pending_sos_sms',
        'schedule': timedelta(minutes=1),
    },
    'send-medical-appointment-reminders-every-30-min': {
        'task': 'medical.tasks.send_due_appointment_reminders',
        'schedule': timedelta(minutes=30),
    },
    'purge-expired-sos-audio-every-day': {
        'task': 'sos.tasks.purge_expired_sos_audio_evidence',
        'schedule': timedelta(hours=24),
    },
}
