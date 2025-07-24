"""
Configuration Django pour le projet NMS.

Ce module contient les paramètres de configuration pour l'application Django.
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-key-for-development')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Modules tiers
    'rest_framework',
    'drf_yasg',
    'channels',
    'corsheaders',
    'sslserver',
    'django_celery_beat',
    
    # Applications locales
    'api_clients',
    'api_views',
    'dashboard',
    'network_management',
    'monitoring',
    'qos_management',
    'security_management',
    'reporting',
    'gns3_integration',
    'plugins',
    'ai_assistant',
    'common',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'nms_backend.auth_middleware.TransparentAuthMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'nms_backend.urls'

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

WSGI_APPLICATION = 'nms_backend.wsgi.application'
ASGI_APPLICATION = 'nms_backend.asgi.application'

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# Configuration de base de données - utilise SQLite si PostgreSQL n'est pas disponible
if os.environ.get('USE_SQLITE', 'false').lower() == 'true':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('POSTGRES_DB', 'nms_db'),
            'USER': os.environ.get('POSTGRES_USER', 'nms_user'),
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'nms_password'),
            'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
            'PORT': os.environ.get('POSTGRES_PORT', '5432'),
        }
    }

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'fr-fr'

TIME_ZONE = 'Europe/Paris'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configuration CORS pour le développement
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

CORS_ALLOW_CREDENTIALS = True

# Configuration pour le module de reporting - Notifications EMAIL RÉELLES
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'  # SMTP RÉEL via Gmail
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'amiromalade@gmail.com'
EMAIL_HOST_PASSWORD = 'ohpd muwa cllb prek'
DEFAULT_FROM_EMAIL = 'Équipe NMS <equipe_nms@gmail.com>'

# Configuration console pour tests (décommentez pour tester)
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Destinataires par défaut pour les alertes de sécurité
SECURITY_ALERT_EMAILS = [
    'amiromalade@gmail.com',  # Adresse principale pour les rapports
    'equipe_nms@gmail.com'    # Adresse équipe (même si n'existe pas, pour les logs)
]

# Webhooks et Slack pour notifications
REPORTING_WEBHOOK_URL = os.environ.get('REPORTING_WEBHOOK_URL', '')
SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL', '')

# Telegram Bot pour les rapports de sécurité - CONFIGURATION RÉELLE
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '8049013662:AAFXhhW_7B9ZPz_IHpq4tb_AdU25JgEKj1k')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '1791851047')

# Configuration des services Docker pour les modules
# Services exposés par docker-compose.yml
ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL', 'http://localhost:9200')
SNMP_HOST = os.environ.get('SNMP_HOST', 'localhost')
SNMP_PORT = int(os.environ.get('SNMP_PORT', '161'))
NETFLOW_API_URL = os.environ.get('NETFLOW_API_URL', 'http://localhost:9995')
REDIS_URL = f"redis://{os.environ.get('REDIS_HOST', 'redis')}:6379/0"

CORS_ALLOW_ALL_ORIGINS = True  # Pour le développement uniquement

CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # Accès libre pour le développement
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
}

# Swagger settings
SWAGGER_SETTINGS = {
    'USE_SESSION_AUTH': True,
    'SECURITY_DEFINITIONS': {
        'basic': {
            'type': 'basic'
        }
    },
    'LOGIN_URL': '/admin/login/',
    'LOGOUT_URL': '/admin/logout/',
}

# Redis
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = os.environ.get('REDIS_PORT', '6379')

# Channels
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [(REDIS_HOST, int(REDIS_PORT))],
        },
    },
}

# Celery
CELERY_BROKER_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/0'
CELERY_RESULT_BACKEND = f'redis://{REDIS_HOST}:{REDIS_PORT}/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
    },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'api_clients': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Configuration HTTPS/SSL
if not DEBUG:
    # Configuration HTTPS pour la production
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1 an
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
else:
    # Configuration pour le développement (permet HTTP et HTTPS)
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

# Chemins des certificats SSL
SSL_CERTIFICATE = os.path.join(BASE_DIR, 'ssl', 'django.crt')
SSL_PRIVATE_KEY = os.path.join(BASE_DIR, 'ssl', 'django.key')

# Configuration GNS3 Integration
GNS3_HOST = os.environ.get('GNS3_HOST', 'localhost')
GNS3_PORT = int(os.environ.get('GNS3_PORT', '3080'))
GNS3_PROTOCOL = os.environ.get('GNS3_PROTOCOL', 'http')
GNS3_USERNAME = os.environ.get('GNS3_USERNAME', '')
GNS3_PASSWORD = os.environ.get('GNS3_PASSWORD', '')
GNS3_VERIFY_SSL = os.environ.get('GNS3_VERIFY_SSL', 'True').lower() == 'true'
GNS3_TIMEOUT = int(os.environ.get('GNS3_TIMEOUT', '30'))
GNS3_AUTO_MONITOR = os.environ.get('GNS3_AUTO_MONITOR', 'True').lower() == 'true'
GNS3_MONITOR_INTERVAL = int(os.environ.get('GNS3_MONITOR_INTERVAL', '30'))
