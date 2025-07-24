
# Configuration du module AI Assistant
# Ce fichier est généré automatiquement

# Paramètres généraux
ENABLE_AI_ASSISTANT = True
DEFAULT_MODEL = "gpt-3.5-turbo"
MAX_TOKENS = 2000
TEMPERATURE = 0.7

# Paramètres de la base de connaissances
ENABLE_KNOWLEDGE_BASE = True
ELASTICSEARCH_HOST = "172.18.0.2"  # Adresse IP du conteneur Elasticsearch (à ajuster si nécessaire)
ELASTICSEARCH_PORT = 9200
ELASTICSEARCH_USER = ""
ELASTICSEARCH_PASSWORD = ""
ELASTICSEARCH_INDEX = "ai_assistant_knowledge"

# Paramètres Redis
REDIS_HOST = "172.18.0.2"  # Adresse IP du conteneur Redis
REDIS_PORT = 6379
REDIS_PASSWORD = ""
REDIS_DB_DEFAULT = 0
REDIS_DB_CACHE = 1
REDIS_DB_SESSIONS = 2

# Paramètres des optimisations
CACHE_ENABLED = True
CACHE_TIMEOUT = 3600
ENABLE_STREAMING = True
ENABLE_EMBEDDINGS = True
EMBEDDING_DIMENSION = 384
