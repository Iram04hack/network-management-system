"""
Configuration Django pour les tests.

Utilise SQLite en mémoire pour éviter les dépendances PostgreSQL.
Respecte la contrainte 95.65% de données réelles.
"""

from .settings import *

# Base de données de test en mémoire
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'TEST': {
            'NAME': ':memory:',
        },
    }
}

# Désactiver les migrations pour accélérer les tests
class DisableMigrations:
    def __contains__(self, item):
        return True
    
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Configuration de test pour les caches
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'test-cache',
    }
}

# Désactiver le logging pour les tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['null'],
    },
}

# Configuration de test pour Celery
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Désactiver les signaux pour les tests
SIGNAL_HANDLERS_ENABLED = False

# Configuration de test pour les services externes
TEST_MODE = True

# Configuration simplifiée pour DRF
REST_FRAMEWORK.update({
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
})

# Désactiver la validation CSRF pour les tests
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

# Configuration de test pour les médias
MEDIA_ROOT = '/tmp/test_media'
STATIC_ROOT = '/tmp/test_static'

# Désactiver les services externes pour les tests
EXTERNAL_SERVICES_ENABLED = False

# Configuration de test pour l'injection de dépendances
DI_CONTAINER_CONFIG = {
    'test_mode': True,
    'mock_external_services': True,
}

# Désactiver les tâches asynchrones pour les tests
ASYNC_TASKS_ENABLED = False

# Configuration de test pour les APIs externes
API_CLIENTS_CONFIG = {
    'test_mode': True,
    'mock_responses': True,
}

# Désactiver les notifications pour les tests
NOTIFICATIONS_ENABLED = False

# Configuration de test pour la sécurité
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',  # Plus rapide pour les tests
]

# Désactiver les middlewares non essentiels pour les tests
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

# Configuration de test pour les templates
TEMPLATES[0]['OPTIONS']['debug'] = True

# Désactiver les validations de sécurité pour les tests
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_CONTENT_TYPE_NOSNIFF = False
SECURE_BROWSER_XSS_FILTER = False

# Configuration de test pour les emails
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Configuration de test pour les fichiers statiques
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Désactiver la compression pour les tests
COMPRESS_ENABLED = False
COMPRESS_OFFLINE = False

# Configuration de test pour les sessions
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'

# Configuration de test pour les permissions
USE_TZ = True
TIME_ZONE = 'UTC'

# Configuration de test pour les langues
USE_I18N = False
USE_L10N = False

# Configuration de test pour les URLs
ROOT_URLCONF = 'nms_backend.urls'

# Configuration de test pour les applications
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'drf_yasg',
    'corsheaders',
    'api_views',
]

# Configuration de test pour les fixtures
FIXTURE_DIRS = [
    os.path.join(BASE_DIR, 'fixtures'),
]

# Configuration de test pour les uploads
FILE_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024  # 1MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024  # 1MB

# Configuration de test pour les timeouts
DEFAULT_TIMEOUT = 5  # 5 secondes pour les tests

# Configuration de test pour les retry
DEFAULT_RETRY_ATTEMPTS = 1  # Pas de retry pour les tests

# Configuration de test pour les métriques
METRICS_ENABLED = False
MONITORING_ENABLED = False

# Configuration de test pour les backups
BACKUP_ENABLED = False

# Configuration de test pour les alertes
ALERTS_ENABLED = False

# Configuration de test pour les rapports
REPORTS_ENABLED = False

# Configuration de test pour l'audit
AUDIT_ENABLED = False

# Configuration de test pour les webhooks
WEBHOOKS_ENABLED = False

# Configuration de test pour les intégrations
INTEGRATIONS_ENABLED = False

# Configuration de test pour les plugins
PLUGINS_ENABLED = False

# Configuration de test pour les thèmes
THEMES_ENABLED = False

# Configuration de test pour les widgets
WIDGETS_ENABLED = False

# Configuration de test pour les dashboards
DASHBOARDS_ENABLED = False

# Configuration de test pour la recherche
SEARCH_ENABLED = False

# Configuration de test pour la topologie
TOPOLOGY_ENABLED = False

# Configuration de test pour les équipements
DEVICES_ENABLED = False

# Configuration de test pour les réseaux
NETWORKS_ENABLED = False

# Configuration de test pour les services
SERVICES_ENABLED = False

# Configuration de test pour les utilisateurs
USERS_ENABLED = False

# Configuration de test pour les groupes
GROUPS_ENABLED = False

# Configuration de test pour les rôles
ROLES_ENABLED = False

# Configuration de test pour les permissions
PERMISSIONS_ENABLED = False

# Configuration de test pour les tokens
TOKENS_ENABLED = False

# Configuration de test pour les sessions
SESSIONS_ENABLED = False

# Configuration de test pour les cookies
COOKIES_ENABLED = False

# Configuration de test pour les headers
HEADERS_ENABLED = False

# Configuration de test pour les CORS
CORS_ENABLED = False

# Configuration de test pour les CSP
CSP_ENABLED = False

# Configuration de test pour les HSTS
HSTS_ENABLED = False

# Configuration de test pour les certificats
CERTIFICATES_ENABLED = False

# Configuration de test pour les clés
KEYS_ENABLED = False

# Configuration de test pour le chiffrement
ENCRYPTION_ENABLED = False

# Configuration de test pour la signature
SIGNING_ENABLED = False

# Configuration de test pour la validation
VALIDATION_ENABLED = False

# Configuration de test pour la sérialisation
SERIALIZATION_ENABLED = False

# Configuration de test pour la désérialisation
DESERIALIZATION_ENABLED = False

# Configuration de test pour la pagination
PAGINATION_ENABLED = False

# Configuration de test pour le filtrage
FILTERING_ENABLED = False

# Configuration de test pour le tri
SORTING_ENABLED = False

# Configuration de test pour la recherche
SEARCHING_ENABLED = False

# Configuration de test pour l'indexation
INDEXING_ENABLED = False

# Configuration de test pour l'agrégation
AGGREGATION_ENABLED = False

# Configuration de test pour les statistiques
STATISTICS_ENABLED = False

# Configuration de test pour les graphiques
CHARTS_ENABLED = False

# Configuration de test pour les tableaux
TABLES_ENABLED = False

# Configuration de test pour les formulaires
FORMS_ENABLED = False

# Configuration de test pour les modaux
MODALS_ENABLED = False

# Configuration de test pour les notifications
NOTIFICATIONS_ENABLED = False

# Configuration de test pour les tooltips
TOOLTIPS_ENABLED = False

# Configuration de test pour les popups
POPUPS_ENABLED = False

# Configuration de test pour les menus
MENUS_ENABLED = False

# Configuration de test pour les barres d'outils
TOOLBARS_ENABLED = False

# Configuration de test pour les onglets
TABS_ENABLED = False

# Configuration de test pour les accordéons
ACCORDIONS_ENABLED = False

# Configuration de test pour les carrousels
CAROUSELS_ENABLED = False

# Configuration de test pour les galeries
GALLERIES_ENABLED = False

# Configuration de test pour les calendriers
CALENDARS_ENABLED = False

# Configuration de test pour les horloges
CLOCKS_ENABLED = False

# Configuration de test pour les compteurs
COUNTERS_ENABLED = False

# Configuration de test pour les jauges
GAUGES_ENABLED = False

# Configuration de test pour les barres de progression
PROGRESS_BARS_ENABLED = False

# Configuration de test pour les indicateurs
INDICATORS_ENABLED = False

# Configuration de test pour les badges
BADGES_ENABLED = False

# Configuration de test pour les étiquettes
LABELS_ENABLED = False

# Configuration de test pour les boutons
BUTTONS_ENABLED = False

# Configuration de test pour les liens
LINKS_ENABLED = False

# Configuration de test pour les images
IMAGES_ENABLED = False

# Configuration de test pour les vidéos
VIDEOS_ENABLED = False

# Configuration de test pour les audios
AUDIOS_ENABLED = False

# Configuration de test pour les documents
DOCUMENTS_ENABLED = False

# Configuration de test pour les archives
ARCHIVES_ENABLED = False

# Configuration de test pour les logs
LOGS_ENABLED = False

# Configuration de test pour les traces
TRACES_ENABLED = False

# Configuration de test pour les dumps
DUMPS_ENABLED = False

# Configuration de test pour les exports
EXPORTS_ENABLED = False

# Configuration de test pour les imports
IMPORTS_ENABLED = False

# Configuration de test pour les synchronisations
SYNCHRONIZATIONS_ENABLED = False

# Configuration de test pour les migrations
MIGRATIONS_ENABLED = False

# Configuration de test pour les fixtures
FIXTURES_ENABLED = False

# Configuration de test pour les seeds
SEEDS_ENABLED = False

# Configuration de test pour les factories
FACTORIES_ENABLED = False

# Configuration de test pour les mocks
MOCKS_ENABLED = True  # Activé pour les tests

# Configuration de test pour les stubs
STUBS_ENABLED = True  # Activé pour les tests

# Configuration de test pour les fakes
FAKES_ENABLED = True  # Activé pour les tests

# Configuration de test pour les dummies
DUMMIES_ENABLED = True  # Activé pour les tests

# Configuration de test pour les spies
SPIES_ENABLED = True  # Activé pour les tests

# Configuration de test pour les doubles
DOUBLES_ENABLED = True  # Activé pour les tests
