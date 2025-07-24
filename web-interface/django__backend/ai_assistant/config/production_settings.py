"""
Configuration de production pour le module AI Assistant.
Ce fichier contient les paramètres recommandés pour un déploiement en production.
"""

import os
from django.conf import settings

# Configuration des fournisseurs IA
AI_PROVIDERS = {
    'openai': {
        'name': 'OpenAI',
        'api_key_env': 'OPENAI_API_KEY',
        'default_model': 'gpt-3.5-turbo',
        'supported_models': [
            'gpt-3.5-turbo',
            'gpt-4',
            'gpt-4-turbo-preview'
        ],
        'max_tokens': 4096,
        'rate_limit': {
            'requests_per_minute': 60,
            'tokens_per_minute': 100000
        }
    },
    'anthropic': {
        'name': 'Anthropic Claude',
        'api_key_env': 'ANTHROPIC_API_KEY',
        'default_model': 'claude-3-sonnet-20240229',
        'supported_models': [
            'claude-3-haiku-20240307',
            'claude-3-sonnet-20240229',
            'claude-3-opus-20240229'
        ],
        'max_tokens': 4096,
        'rate_limit': {
            'requests_per_minute': 50,
            'tokens_per_minute': 80000
        }
    },
    'huggingface': {
        'name': 'HuggingFace',
        'api_key_env': 'HUGGINGFACE_API_TOKEN',
        'default_model': 'mistralai/Mistral-7B-Instruct-v0.1',
        'supported_models': [
            'mistralai/Mistral-7B-Instruct-v0.1',
            'microsoft/DialoGPT-medium',
            'facebook/blenderbot-400M-distill'
        ],
        'max_tokens': 2048,
        'rate_limit': {
            'requests_per_minute': 30,
            'tokens_per_minute': 50000
        }
    }
}

# Configuration par défaut si aucun modèle n'est configuré
DEFAULT_AI_CONFIG = {
    'provider': os.environ.get('AI_PROVIDER', 'openai'),
    'model': os.environ.get('AI_MODEL', 'gpt-3.5-turbo'),
    'temperature': float(os.environ.get('AI_TEMPERATURE', '0.7')),
    'max_tokens': int(os.environ.get('AI_MAX_TOKENS', '1000')),
    'system_message': os.environ.get(
        'AI_SYSTEM_MESSAGE',
        "Tu es un assistant IA spécialisé dans la gestion de réseaux informatiques. "
        "Tu fournis des réponses précises, sécurisées et basées sur les bonnes pratiques."
    )
}

# Validation de configuration en production
def validate_production_config():
    """
    Valide que la configuration production est complète et sécurisée.
    
    Raises:
        ValueError: Si la configuration est invalide pour la production
    """
    errors = []
    
    # Vérifier que l'environnement est défini
    environment = getattr(settings, 'ENVIRONMENT', os.environ.get('ENVIRONMENT', 'development'))
    
    if environment == 'production':
        # En production, au moins une clé API doit être définie
        has_api_key = False
        
        for provider, config in AI_PROVIDERS.items():
            api_key_env = config['api_key_env']
            if os.environ.get(api_key_env):
                has_api_key = True
                break
        
        if not has_api_key:
            errors.append(
                "Aucune clé API définie. Au moins une des variables suivantes doit être définie: " +
                ", ".join([config['api_key_env'] for config in AI_PROVIDERS.values()])
            )
        
        # Vérifier que le fournisseur par défaut est supporté
        default_provider = DEFAULT_AI_CONFIG['provider']
        if default_provider not in AI_PROVIDERS:
            errors.append(f"Fournisseur par défaut non supporté: {default_provider}")
        
        # Vérifier que le modèle par défaut est supporté par le fournisseur
        if default_provider in AI_PROVIDERS:
            default_model = DEFAULT_AI_CONFIG['model']
            supported_models = AI_PROVIDERS[default_provider]['supported_models']
            if default_model not in supported_models:
                errors.append(
                    f"Modèle {default_model} non supporté pour le fournisseur {default_provider}. "
                    f"Modèles supportés: {', '.join(supported_models)}"
                )
        
        # Vérifier les paramètres de base
        if not (0 <= DEFAULT_AI_CONFIG['temperature'] <= 2):
            errors.append("La température doit être entre 0 et 2")
        
        if not (1 <= DEFAULT_AI_CONFIG['max_tokens'] <= 8192):
            errors.append("max_tokens doit être entre 1 et 8192")
    
    if errors:
        raise ValueError("Configuration production invalide:\n" + "\n".join(f"- {error}" for error in errors))

# Configuration de sécurité
SECURITY_CONFIG = {
    # Commandes autorisées par type
    'allowed_commands': {
        'network': [
            'ping', 'traceroute', 'nslookup', 'dig', 'netstat', 'ss',
            'arp', 'route', 'ip', 'ifconfig', 'iwconfig'
        ],
        'system': [
            'ps', 'top', 'df', 'du', 'free', 'uname', 'whoami',
            'id', 'date', 'uptime', 'cat', 'tail', 'head', 'grep'
        ],
        'monitoring': [
            'sar', 'iostat', 'vmstat', 'mpstat', 'pidstat',
            'htop', 'iotop', 'tcpdump', 'netstat'
        ]
    },
    
    # Commandes interdites (pour sécurité)
    'forbidden_commands': [
        'rm', 'rmdir', 'del', 'deltree', 'format', 'fdisk',
        'dd', 'mkfs', 'shutdown', 'reboot', 'halt', 'poweroff',
        'passwd', 'su', 'sudo', 'chmod', 'chown', 'chgrp',
        'mount', 'umount', 'crontab', 'at', 'batch'
    ],
    
    # Patterns dangereux dans les commandes
    'dangerous_patterns': [
        r'rm\s+-rf', r'>\s*/dev/', r'\|\s*sh', r'\|\s*bash',
        r';\s*rm', r'&&\s*rm', r'`.*`', r'\$\(.*\)',
        r'eval\s*\(', r'exec\s*\(', r'--force', r'--recursive'
    ],
    
    # Limites de ressources
    'resource_limits': {
        'max_execution_time': 30,  # secondes
        'max_output_size': 1048576,  # 1MB
        'max_concurrent_commands': 5,
        'max_commands_per_hour': 100
    }
}

# Configuration de monitoring
MONITORING_CONFIG = {
    'log_all_requests': True,
    'log_failed_requests': True,
    'log_slow_requests': True,
    'slow_request_threshold': 5.0,  # secondes
    
    'metrics': {
        'enabled': True,
        'track_response_times': True,
        'track_error_rates': True,
        'track_usage_by_user': True,
        'track_command_usage': True
    },
    
    'alerts': {
        'high_error_rate_threshold': 0.05,  # 5%
        'slow_response_threshold': 10.0,  # secondes
        'unusual_activity_threshold': 50  # commandes/heure
    }
}

# Configuration de cache
CACHE_CONFIG = {
    'ai_responses': {
        'enabled': True,
        'ttl': 3600,  # 1 heure
        'max_size': 1000,
        'key_prefix': 'ai_response'
    },
    
    'command_results': {
        'enabled': True,
        'ttl': 300,  # 5 minutes
        'max_size': 500,
        'key_prefix': 'cmd_result'
    },
    
    'document_search': {
        'enabled': True,
        'ttl': 1800,  # 30 minutes
        'max_size': 200,
        'key_prefix': 'doc_search'
    }
}

# Configuration de base de données
DATABASE_CONFIG = {
    'connections': {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'OPTIONS': {
                'MAX_CONNS': 20,
                'MIN_CONNS': 5,
                'CONN_MAX_AGE': 3600,
                'AUTOCOMMIT': True
            }
        }
    },
    
    'migrations': {
        'run_on_startup': False,  # Désactivé en production
        'backup_before_migration': True
    }
}

def get_production_settings():
    """
    Retourne les paramètres complets pour la production.
    
    Returns:
        dict: Configuration complète pour la production
    """
    return {
        'AI_PROVIDERS': AI_PROVIDERS,
        'DEFAULT_AI_CONFIG': DEFAULT_AI_CONFIG,
        'SECURITY_CONFIG': SECURITY_CONFIG,
        'MONITORING_CONFIG': MONITORING_CONFIG,
        'CACHE_CONFIG': CACHE_CONFIG,
        'DATABASE_CONFIG': DATABASE_CONFIG
    }

def setup_production_logging():
    """Configure le logging pour la production."""
    import logging.config
    
    LOGGING_CONFIG = {
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
            'json': {
                'format': '{"level": "%(levelname)s", "time": "%(asctime)s", "module": "%(module)s", "message": "%(message)s"}',
            }
        },
        'handlers': {
            'file': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': '/var/log/ai_assistant/ai_assistant.log',
                'maxBytes': 1024*1024*10,  # 10MB
                'backupCount': 5,
                'formatter': 'verbose',
            },
            'error_file': {
                'level': 'ERROR',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': '/var/log/ai_assistant/errors.log',
                'maxBytes': 1024*1024*10,  # 10MB
                'backupCount': 5,
                'formatter': 'verbose',
            },
            'security_file': {
                'level': 'WARNING',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': '/var/log/ai_assistant/security.log',
                'maxBytes': 1024*1024*10,  # 10MB
                'backupCount': 10,
                'formatter': 'json',
            },
            'console': {
                'level': 'WARNING',
                'class': 'logging.StreamHandler',
                'formatter': 'simple',
            },
        },
        'loggers': {
            'ai_assistant': {
                'handlers': ['file', 'error_file', 'console'],
                'level': 'INFO',
                'propagate': False,
            },
            'ai_assistant.security': {
                'handlers': ['security_file', 'error_file'],
                'level': 'WARNING',
                'propagate': False,
            },
            'django': {
                'handlers': ['file', 'console'],
                'level': 'INFO',
                'propagate': False,
            },
        },
        'root': {
            'handlers': ['console'],
            'level': 'WARNING',
        }
    }
    
    logging.config.dictConfig(LOGGING_CONFIG)

# Auto-validation au chargement du module
if __name__ != '__main__':
    try:
        validate_production_config()
    except ValueError as e:
        import warnings
        warnings.warn(f"Configuration production invalide: {e}", UserWarning)