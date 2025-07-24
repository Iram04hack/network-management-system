"""
Configuration centralisée pour les tests api_clients.
Résout les problèmes de dépendances Django et optimise l'environnement de test.
"""

import os
import sys
from pathlib import Path

# Configuration des chemins
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
API_CLIENTS_DIR = Path(__file__).resolve().parent.parent

class TestConfig:
    """Configuration centralisée pour les tests api_clients."""
    
    # Configuration Django pour tests
    DJANGO_SETTINGS = {
        'DEBUG': True,
        'SECRET_KEY': 'api-clients-test-key-for-coverage-90-percent',
        
        # Base de données de test (SQLite pour simplicité et rapidité)
        'DATABASES': {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
                'OPTIONS': {
                    'timeout': 20,
                }
            }
        },
        
        # Applications minimales pour api_clients
        'INSTALLED_APPS': [
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'rest_framework',
            'drf_yasg',
            'api_clients',
        ],
        
        # Configuration REST Framework
        'REST_FRAMEWORK': {
            'DEFAULT_PERMISSION_CLASSES': [
                'rest_framework.permissions.AllowAny',
            ],
            'DEFAULT_RENDERER_CLASSES': [
                'rest_framework.renderers.JSONRenderer',
            ],
            'DEFAULT_PARSER_CLASSES': [
                'rest_framework.parsers.JSONParser',
            ],
        },
        
        # Configuration Swagger
        'SWAGGER_SETTINGS': {
            'SECURITY_DEFINITIONS': {},
            'USE_SESSION_AUTH': False,
            'JSON_EDITOR': True,
        },
        
        # Timezone et internationalisation
        'USE_TZ': True,
        'TIME_ZONE': 'UTC',
        'USE_I18N': True,
        'USE_L10N': True,
        'LANGUAGE_CODE': 'fr-fr',
        
        # Logging optimisé pour tests
        'LOGGING': {
            'version': 1,
            'disable_existing_loggers': False,
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': 'WARNING',  # Réduire le bruit pendant les tests
                },
            },
            'root': {
                'handlers': ['console'],
                'level': 'WARNING',
            },
            'loggers': {
                'api_clients': {
                    'handlers': ['console'],
                    'level': 'INFO',
                    'propagate': False,
                },
            },
        },
        
        # Désactiver les migrations pour les tests (plus rapide)
        'MIGRATION_MODULES': {
            'auth': None,
            'contenttypes': None,
            'sessions': None,
        },
        
        # Configuration de test
        'TESTING': True,
        'PASSWORD_HASHERS': [
            'django.contrib.auth.hashers.MD5PasswordHasher',  # Plus rapide pour les tests
        ],
    }
    
    # Configuration des services de test
    TEST_SERVICES = {
        'postgresql': {
            'host': 'localhost',
            'port': 5433,
            'database': 'nms_test',
            'user': 'nms_user',
            'password': 'nms_password'
        },
        'gns3': {
            'host': 'localhost',
            'ports': [3080, 3081, 3082],
            'timeout': 5
        },
        'prometheus': {
            'host': 'localhost',
            'port': 9091,
            'timeout': 5
        },
        'grafana': {
            'host': 'localhost',
            'port': 3002,
            'timeout': 5
        },
        'elasticsearch': {
            'host': 'localhost',
            'port': 9201,
            'timeout': 5
        },
        'snmp': {
            'host': 'localhost',
            'port': 1162,
            'community': 'public',
            'timeout': 3
        },
        'netflow': {
            'host': 'localhost',
            'port': 9996,
            'timeout': 5
        }
    }
    
    # Configuration de couverture
    COVERAGE_CONFIG = {
        'source': ['api_clients'],
        'omit': [
            '*/tests/*',
            '*/migrations/*', 
            '*/__pycache__/*',
            '*/venv/*',
            '*/testing/*'  # Exclure les outils de test
        ],
        'target_coverage': 90.0,
        'html_report_dir': 'htmlcov_api_clients'
    }
    
    # Configuration des tests prioritaires
    PRIORITY_TESTS = {
        'views': {
            'module': 'api_clients.views',
            'lines': 416,
            'expected_impact': 40,
            'priority': 'HAUTE'
        },
        'base': {
            'module': 'api_clients.base',
            'lines': 97,
            'expected_impact': 25,
            'priority': 'HAUTE'
        },
        'infrastructure': {
            'module': 'api_clients.infrastructure',
            'lines': 200,
            'expected_impact': 15,
            'priority': 'MOYENNE'
        },
        'clients': {
            'module': 'api_clients.network',
            'lines': 717,
            'expected_impact': 10,
            'priority': 'MOYENNE'
        }
    }
    
    @classmethod
    def configure_django(cls):
        """Configure Django pour les tests."""
        import django
        from django.conf import settings
        
        if not settings.configured:
            settings.configure(**cls.DJANGO_SETTINGS)
            django.setup()
        
        return settings
    
    @classmethod
    def setup_test_environment(cls):
        """Configure l'environnement de test complet."""
        # Configuration Django
        settings = cls.configure_django()
        
        # Ajouter le chemin du module
        if str(API_CLIENTS_DIR) not in sys.path:
            sys.path.insert(0, str(API_CLIENTS_DIR))
        
        print("✅ Environnement de test api_clients configuré")
        return settings
    
    @classmethod
    def get_service_config(cls, service_name):
        """Retourne la configuration d'un service de test."""
        return cls.TEST_SERVICES.get(service_name, {})
    
    @classmethod
    def get_coverage_config(cls):
        """Retourne la configuration de couverture."""
        return cls.COVERAGE_CONFIG.copy()
    
    @classmethod
    def get_priority_tests_config(cls):
        """Retourne la configuration des tests prioritaires."""
        return cls.PRIORITY_TESTS.copy()


# Configuration pour pytest
def pytest_configure():
    """Configuration automatique pour pytest."""
    TestConfig.configure_django()


# Configuration pour unittest
if __name__ == "__main__":
    TestConfig.setup_test_environment()
    print("Configuration de test api_clients prête !")
    print(f"Services configurés: {list(TestConfig.TEST_SERVICES.keys())}")
    print(f"Objectif de couverture: {TestConfig.COVERAGE_CONFIG['target_coverage']}%")
