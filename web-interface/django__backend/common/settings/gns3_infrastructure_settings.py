"""
Configuration Django pour l'infrastructure GNS3 Central Service.

Ce fichier contient toutes les configurations nécessaires pour le bon fonctionnement
du service central GNS3, incluant Django Channels, Redis, WebSocket et les APIs.
"""

import os
from pathlib import Path

# Configuration de base pour l'infrastructure GNS3
GNS3_INFRASTRUCTURE_CONFIG = {
    # Service Central GNS3
    'GNS3_CENTRAL_SERVICE': {
        'ENABLED': True,
        'AUTO_START': True,
        'INITIALIZATION_TIMEOUT': 60,  # secondes
        'HEALTH_CHECK_INTERVAL': 300,  # 5 minutes
    },
    
    # Serveur GNS3
    'GNS3_SERVER': {
        'HOST': os.environ.get('GNS3_HOST', 'localhost'),
        'PORT': int(os.environ.get('GNS3_PORT', 3080)),
        'PROTOCOL': os.environ.get('GNS3_PROTOCOL', 'http'),
        'USERNAME': os.environ.get('GNS3_USERNAME', ''),
        'PASSWORD': os.environ.get('GNS3_PASSWORD', ''),
        'VERIFY_SSL': os.environ.get('GNS3_VERIFY_SSL', 'true').lower() == 'true',
        'TIMEOUT': int(os.environ.get('GNS3_TIMEOUT', 30)),
        'MAX_RETRIES': 3,
        'RETRY_DELAY': 2,
    },
    
    # Cache Redis
    'REDIS_CACHE': {
        'ENABLED': True,
        'HOST': os.environ.get('REDIS_HOST', 'localhost'),
        'PORT': int(os.environ.get('REDIS_PORT', 6379)),
        'DB': int(os.environ.get('REDIS_DB', 0)),
        'PASSWORD': os.environ.get('REDIS_PASSWORD', None),
        'MAX_CONNECTIONS': 50,
        'CONNECTION_POOL_KWARGS': {
            'max_connections': 50,
            'retry_on_timeout': True,
        },
    },
    
    # Système d'événements temps réel
    'REALTIME_EVENTS': {
        'ENABLED': True,
        'MAX_EVENT_HISTORY': 10000,
        'EVENT_TTL_HOURS': 24,
        'RETRY_MAX_ATTEMPTS': 3,
        'RETRY_BACKOFF_FACTOR': 2,
        'BATCH_SIZE': 100,
        'PROCESSING_INTERVAL': 0.1,  # secondes
    },
    
    # WebSocket Configuration
    'WEBSOCKET': {
        'ENABLED': True,
        'MAX_CONNECTIONS_PER_IP': 10,
        'HEARTBEAT_INTERVAL': 30,  # secondes
        'CONNECTION_TIMEOUT': 300,  # 5 minutes
        'MESSAGE_SIZE_LIMIT': 1024 * 1024,  # 1MB
        'ALLOWED_ORIGINS': ['*'],  # À restreindre en production
    },
    
    # API Configuration
    'API': {
        'RATE_LIMITING': {
            'BURST': 60,  # requêtes par minute
            'SUSTAINED': 1000,  # requêtes par heure
        },
        'PAGINATION': {
            'PAGE_SIZE': 50,
            'MAX_PAGE_SIZE': 200,
        },
        'SWAGGER': {
            'ENABLED': True,
            'USE_SESSION_AUTH': True,
            'PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
        },
    },
    
    # Logging spécialisé
    'LOGGING': {
        'LEVEL': os.environ.get('GNS3_LOG_LEVEL', 'INFO'),
        'ENABLE_PERFORMANCE_LOGGING': True,
        'ENABLE_EVENT_LOGGING': True,
        'LOG_ROTATION': {
            'MAX_BYTES': 10 * 1024 * 1024,  # 10MB
            'BACKUP_COUNT': 5,
        },
    },
    
    # Monitoring et métriques
    'MONITORING': {
        'ENABLED': True,
        'METRICS_COLLECTION_INTERVAL': 60,  # secondes
        'ALERT_THRESHOLDS': {
            'ERROR_RATE_PERCENT': 5,
            'RESPONSE_TIME_MS': 1000,
            'MEMORY_USAGE_PERCENT': 80,
        },
    },
}

# Configuration Django Channels pour WebSocket
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [(
                GNS3_INFRASTRUCTURE_CONFIG['REDIS_CACHE']['HOST'],
                GNS3_INFRASTRUCTURE_CONFIG['REDIS_CACHE']['PORT']
            )],
            'capacity': 300,
            'expiry': 60,
        },
    },
}

# Configuration ASGI pour Django Channels
ASGI_APPLICATION = 'common.infrastructure.websocket_routing.application'

# Configuration du cache Django avec Redis
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f"redis://{GNS3_INFRASTRUCTURE_CONFIG['REDIS_CACHE']['HOST']}:{GNS3_INFRASTRUCTURE_CONFIG['REDIS_CACHE']['PORT']}/0",
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': GNS3_INFRASTRUCTURE_CONFIG['REDIS_CACHE']['CONNECTION_POOL_KWARGS'],
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
        },
        'TIMEOUT': 300,  # 5 minutes par défaut
        'KEY_PREFIX': 'gns3_central',
        'VERSION': 1,
    },
    
    # Cache séparé pour les événements
    'events': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f"redis://{GNS3_INFRASTRUCTURE_CONFIG['REDIS_CACHE']['HOST']}:{GNS3_INFRASTRUCTURE_CONFIG['REDIS_CACHE']['PORT']}/1",
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'TIMEOUT': 3600,  # 1 heure pour les événements
        'KEY_PREFIX': 'gns3_events',
    },
    
    # Cache pour les sessions WebSocket
    'sessions': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f"redis://{GNS3_INFRASTRUCTURE_CONFIG['REDIS_CACHE']['HOST']}:{GNS3_INFRASTRUCTURE_CONFIG['REDIS_CACHE']['PORT']}/2",
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'TIMEOUT': 1800,  # 30 minutes pour les sessions
        'KEY_PREFIX': 'gns3_sessions',
    },
}

# Configuration du logging pour l'infrastructure GNS3
GNS3_LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{levelname}] {name}: {message}',
            'style': '{',
        },
        'json': {
            'format': '{"timestamp": "{asctime}", "level": "{levelname}", "logger": "{name}", "message": "{message}"}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file_gns3': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/tmp/gns3_central_service.log',
            'maxBytes': GNS3_INFRASTRUCTURE_CONFIG['LOGGING']['LOG_ROTATION']['MAX_BYTES'],
            'backupCount': GNS3_INFRASTRUCTURE_CONFIG['LOGGING']['LOG_ROTATION']['BACKUP_COUNT'],
            'formatter': 'verbose',
        },
        'file_events': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/tmp/gns3_events.log',
            'maxBytes': GNS3_INFRASTRUCTURE_CONFIG['LOGGING']['LOG_ROTATION']['MAX_BYTES'],
            'backupCount': GNS3_INFRASTRUCTURE_CONFIG['LOGGING']['LOG_ROTATION']['BACKUP_COUNT'],
            'formatter': 'json',
        },
    },
    'loggers': {
        'common.infrastructure.gns3_central_service': {
            'handlers': ['console', 'file_gns3'],
            'level': GNS3_INFRASTRUCTURE_CONFIG['LOGGING']['LEVEL'],
            'propagate': False,
        },
        'common.infrastructure.realtime_event_system': {
            'handlers': ['console', 'file_events'],
            'level': GNS3_INFRASTRUCTURE_CONFIG['LOGGING']['LEVEL'],
            'propagate': False,
        },
        'common.api.gns3_central_viewsets': {
            'handlers': ['console', 'file_gns3'],
            'level': GNS3_INFRASTRUCTURE_CONFIG['LOGGING']['LEVEL'],
            'propagate': False,
        },
        'common.api.gns3_module_interface': {
            'handlers': ['console', 'file_gns3'],
            'level': GNS3_INFRASTRUCTURE_CONFIG['LOGGING']['LEVEL'],
            'propagate': False,
        },
    },
}

# Configuration REST Framework pour les APIs GNS3
REST_FRAMEWORK_GNS3 = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': GNS3_INFRASTRUCTURE_CONFIG['API']['PAGINATION']['PAGE_SIZE'],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': f"{GNS3_INFRASTRUCTURE_CONFIG['API']['RATE_LIMITING']['BURST']}/min",
        'user': f"{GNS3_INFRASTRUCTURE_CONFIG['API']['RATE_LIMITING']['SUSTAINED']}/hour"
    },
    'EXCEPTION_HANDLER': 'common.api.exception_handlers.gns3_exception_handler',
}

# Configuration Swagger/OpenAPI
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
    },
    'USE_SESSION_AUTH': GNS3_INFRASTRUCTURE_CONFIG['API']['SWAGGER']['USE_SESSION_AUTH'],
    'LOGIN_URL': '/admin/login/',
    'LOGOUT_URL': '/admin/logout/',
    'PERMISSIONS': GNS3_INFRASTRUCTURE_CONFIG['API']['SWAGGER']['PERMISSION_CLASSES'],
    'DOC_EXPANSION': 'none',
    'DEEP_LINKING': True,
    'SHOW_EXTENSIONS': True,
    'DEFAULT_MODEL_RENDERING': 'model',
}

# Configuration de sécurité
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Frontend React
    "http://localhost:8080",  # Frontend Vue
    "http://127.0.0.1:8000",  # Django dev server
]

CORS_ALLOW_CREDENTIALS = True

# Variables d'environnement spécifiques à l'infrastructure GNS3
def configure_gns3_environment():
    """Configure les variables d'environnement pour l'infrastructure GNS3."""
    
    # Export des configurations pour utilisation dans les modules
    os.environ.setdefault('GNS3_CENTRAL_ENABLED', 
                         str(GNS3_INFRASTRUCTURE_CONFIG['GNS3_CENTRAL_SERVICE']['ENABLED']))
    
    os.environ.setdefault('GNS3_REALTIME_EVENTS_ENABLED', 
                         str(GNS3_INFRASTRUCTURE_CONFIG['REALTIME_EVENTS']['ENABLED']))
    
    os.environ.setdefault('GNS3_WEBSOCKET_ENABLED', 
                         str(GNS3_INFRASTRUCTURE_CONFIG['WEBSOCKET']['ENABLED']))
    
    # Configuration Redis pour les autres services
    os.environ.setdefault('REDIS_URL', 
                         f"redis://{GNS3_INFRASTRUCTURE_CONFIG['REDIS_CACHE']['HOST']}:{GNS3_INFRASTRUCTURE_CONFIG['REDIS_CACHE']['PORT']}/0")

# Fonction d'initialisation pour l'infrastructure
def initialize_gns3_infrastructure():
    """Initialise l'infrastructure GNS3 au démarrage de Django."""
    
    # Configurer l'environnement
    configure_gns3_environment()
    
    # Configuration du logging
    import logging.config
    logging.config.dictConfig(GNS3_LOGGING_CONFIG)
    
    # Log d'initialisation
    logger = logging.getLogger('common.infrastructure.gns3_central_service')
    logger.info("Infrastructure GNS3 Central Service configurée")
    
    # Vérifications de sanité
    _validate_configuration()

def _validate_configuration():
    """Valide la configuration de l'infrastructure."""
    
    # Vérifier Redis
    try:
        import redis
        r = redis.Redis(
            host=GNS3_INFRASTRUCTURE_CONFIG['REDIS_CACHE']['HOST'],
            port=GNS3_INFRASTRUCTURE_CONFIG['REDIS_CACHE']['PORT'],
            db=GNS3_INFRASTRUCTURE_CONFIG['REDIS_CACHE']['DB'],
            socket_connect_timeout=5
        )
        r.ping()
        print("✅ Connexion Redis validée")
    except Exception as e:
        print(f"⚠️  Attention: Redis non accessible ({e})")
    
    # Vérifier la configuration GNS3
    gns3_host = GNS3_INFRASTRUCTURE_CONFIG['GNS3_SERVER']['HOST']
    gns3_port = GNS3_INFRASTRUCTURE_CONFIG['GNS3_SERVER']['PORT']
    
    if gns3_host == 'localhost' and gns3_port == 3080:
        print("ℹ️  Configuration GNS3 par défaut (localhost:3080)")
    else:
        print(f"✅ Configuration GNS3 personnalisée ({gns3_host}:{gns3_port})")

# Apps à ajouter à INSTALLED_APPS pour l'infrastructure GNS3
GNS3_INFRASTRUCTURE_APPS = [
    'channels',
    'django_redis',
    'corsheaders',
    'rest_framework',
    'drf_yasg',
    'common.api',
    'common.infrastructure',
]

# Middleware à ajouter pour l'infrastructure GNS3
GNS3_INFRASTRUCTURE_MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
]

# Export des configurations pour utilisation dans settings.py principal
__all__ = [
    'GNS3_INFRASTRUCTURE_CONFIG',
    'CHANNEL_LAYERS',
    'ASGI_APPLICATION', 
    'CACHES',
    'REST_FRAMEWORK_GNS3',
    'SWAGGER_SETTINGS',
    'GNS3_INFRASTRUCTURE_APPS',
    'GNS3_INFRASTRUCTURE_MIDDLEWARE',
    'initialize_gns3_infrastructure',
    'configure_gns3_environment',
]