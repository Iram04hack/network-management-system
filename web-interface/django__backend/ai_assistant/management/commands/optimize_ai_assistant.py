"""
Commande Django pour optimiser le module AI Assistant (Phase 3).

Cette commande configure les optimisations de performance du module AI Assistant,
notamment la mise en cache, le streaming et les embeddings vectoriels.
"""

import logging
import time
import redis
import os
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.conf import settings
from django.core.cache import cache
from elasticsearch import Elasticsearch

from ai_assistant.models import AIModel
from ai_assistant.config import settings as ai_settings

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Configure les optimisations de performance du module AI Assistant (Phase 3)"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--enable-cache',
            action='store_true',
            help='Active la mise en cache des réponses'
        )
        parser.add_argument(
            '--disable-cache',
            action='store_true',
            help='Désactive la mise en cache des réponses'
        )
        parser.add_argument(
            '--enable-streaming',
            action='store_true',
            help='Active le streaming des réponses'
        )
        parser.add_argument(
            '--disable-streaming',
            action='store_true',
            help='Désactive le streaming des réponses'
        )
        parser.add_argument(
            '--enable-embeddings',
            action='store_true',
            help='Active les embeddings vectoriels pour la recherche sémantique'
        )
        parser.add_argument(
            '--disable-embeddings',
            action='store_true',
            help='Désactive les embeddings vectoriels'
        )
        parser.add_argument(
            '--setup-elasticsearch',
            action='store_true',
            help='Configure Elasticsearch pour les embeddings vectoriels'
        )
        parser.add_argument(
            '--clear-cache',
            action='store_true',
            help='Vide le cache des réponses'
        )
        parser.add_argument(
            '--redis-host',
            type=str,
            default='172.18.0.3',  # Adresse IP du conteneur Redis par défaut
            help='Hôte Redis pour la configuration'
        )
        parser.add_argument(
            '--redis-port',
            type=int,
            default=6379,
            help='Port Redis pour la configuration'
        )
    
    def handle(self, *args, **options):
        start_time = time.time()
        self.stdout.write(self.style.NOTICE("Configuration des optimisations du module AI Assistant..."))
        
        # Stocker les options Redis pour les utiliser dans les méthodes
        self.redis_host = options.get('redis_host')
        self.redis_port = options.get('redis_port')
        
        # Vérifier les options contradictoires
        if options.get('enable_cache') and options.get('disable_cache'):
            self.stdout.write(self.style.ERROR("Vous ne pouvez pas activer et désactiver le cache en même temps."))
            return
        
        if options.get('enable_streaming') and options.get('disable_streaming'):
            self.stdout.write(self.style.ERROR("Vous ne pouvez pas activer et désactiver le streaming en même temps."))
            return
        
        if options.get('enable_embeddings') and options.get('disable_embeddings'):
            self.stdout.write(self.style.ERROR("Vous ne pouvez pas activer et désactiver les embeddings en même temps."))
            return
        
        # Configuration du cache
        if options.get('enable_cache'):
            self._enable_cache()
        elif options.get('disable_cache'):
            self._disable_cache()
        
        # Configuration du streaming
        if options.get('enable_streaming'):
            self._enable_streaming()
        elif options.get('disable_streaming'):
            self._disable_streaming()
        
        # Configuration des embeddings
        if options.get('enable_embeddings'):
            self._enable_embeddings()
        elif options.get('disable_embeddings'):
            self._disable_embeddings()
        
        # Configuration d'Elasticsearch pour les embeddings
        if options.get('setup_elasticsearch'):
            self._setup_elasticsearch_embeddings()
        
        # Vider le cache
        if options.get('clear_cache'):
            self._clear_cache()
        
        # Si aucune option spécifique n'est fournie, configurer toutes les optimisations
        if not any([
            options.get('enable_cache'), options.get('disable_cache'),
            options.get('enable_streaming'), options.get('disable_streaming'),
            options.get('enable_embeddings'), options.get('disable_embeddings'),
            options.get('setup_elasticsearch'), options.get('clear_cache')
        ]):
            self._configure_all_optimizations()
        
        execution_time = time.time() - start_time
        self.stdout.write(self.style.SUCCESS(
            f"Configuration des optimisations terminée en {execution_time:.2f} secondes!"
        ))
    
    def _get_redis_connection(self):
        """Obtient une connexion Redis."""
        try:
            r = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                password=os.environ.get('REDIS_PASSWORD', ''),
                db=int(os.environ.get('REDIS_DB_DEFAULT', '0')),
                decode_responses=True
            )
            # Tester la connexion
            r.ping()
            return r
        except Exception as e:
            logger.exception(f"Erreur de connexion à Redis: {e}")
            self.stdout.write(self.style.ERROR(f"Erreur de connexion à Redis: {e}"))
            return None
    
    def _enable_cache(self):
        """Active la mise en cache des réponses."""
        self.stdout.write("Activation de la mise en cache des réponses...")
        
        try:
            # Mettre à jour la configuration dans la base de données
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO django_settings (key, value) 
                        VALUES ('AI_ASSISTANT_CACHE_ENABLED', 'True')
                        ON CONFLICT (key) DO UPDATE SET value = 'True'
                    """)
            
            # Mettre à jour la configuration dans Redis
            r = self._get_redis_connection()
            if r:
                r.set('AI_ASSISTANT_CACHE_ENABLED', 'True')
                self.stdout.write("Configuration Redis mise à jour.")
            
            # Mettre à jour le fichier de configuration
            self._update_config_file('CACHE_ENABLED', True)
            
            self.stdout.write(self.style.SUCCESS("Mise en cache activée avec succès"))
        except Exception as e:
            logger.exception(f"Erreur lors de l'activation du cache: {e}")
            self.stdout.write(self.style.ERROR(f"Erreur lors de l'activation du cache: {e}"))
    
    def _disable_cache(self):
        """Désactive la mise en cache des réponses."""
        self.stdout.write("Désactivation de la mise en cache des réponses...")
        
        try:
            # Mettre à jour la configuration dans la base de données
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO django_settings (key, value) 
                        VALUES ('AI_ASSISTANT_CACHE_ENABLED', 'False')
                        ON CONFLICT (key) DO UPDATE SET value = 'False'
                    """)
            
            # Mettre à jour la configuration dans Redis
            r = self._get_redis_connection()
            if r:
                r.set('AI_ASSISTANT_CACHE_ENABLED', 'False')
                self.stdout.write("Configuration Redis mise à jour.")
            
            # Mettre à jour le fichier de configuration
            self._update_config_file('CACHE_ENABLED', False)
            
            self.stdout.write(self.style.SUCCESS("Mise en cache désactivée avec succès"))
        except Exception as e:
            logger.exception(f"Erreur lors de la désactivation du cache: {e}")
            self.stdout.write(self.style.ERROR(f"Erreur lors de la désactivation du cache: {e}"))
    
    def _enable_streaming(self):
        """Active le streaming des réponses."""
        self.stdout.write("Activation du streaming des réponses...")
        
        try:
            # Mettre à jour la configuration dans la base de données
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO django_settings (key, value) 
                        VALUES ('AI_ASSISTANT_ENABLE_STREAMING', 'True')
                        ON CONFLICT (key) DO UPDATE SET value = 'True'
                    """)
            
            # Mettre à jour la configuration dans Redis
            r = self._get_redis_connection()
            if r:
                r.set('AI_ASSISTANT_ENABLE_STREAMING', 'True')
                self.stdout.write("Configuration Redis mise à jour.")
            
            # Mettre à jour le fichier de configuration
            self._update_config_file('ENABLE_STREAMING', True)
            
            # Mettre à jour les modèles pour le streaming
            self._update_models_for_streaming()
            
            self.stdout.write(self.style.SUCCESS("Streaming activé avec succès"))
        except Exception as e:
            logger.exception(f"Erreur lors de l'activation du streaming: {e}")
            self.stdout.write(self.style.ERROR(f"Erreur lors de l'activation du streaming: {e}"))
    
    def _disable_streaming(self):
        """Désactive le streaming des réponses."""
        self.stdout.write("Désactivation du streaming des réponses...")
        
        try:
            # Mettre à jour la configuration dans la base de données
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO django_settings (key, value) 
                        VALUES ('AI_ASSISTANT_ENABLE_STREAMING', 'False')
                        ON CONFLICT (key) DO UPDATE SET value = 'False'
                    """)
            
            # Mettre à jour la configuration dans Redis
            r = self._get_redis_connection()
            if r:
                r.set('AI_ASSISTANT_ENABLE_STREAMING', 'False')
                self.stdout.write("Configuration Redis mise à jour.")
            
            # Mettre à jour le fichier de configuration
            self._update_config_file('ENABLE_STREAMING', False)
            
            self.stdout.write(self.style.SUCCESS("Streaming désactivé avec succès"))
        except Exception as e:
            logger.exception(f"Erreur lors de la désactivation du streaming: {e}")
            self.stdout.write(self.style.ERROR(f"Erreur lors de la désactivation du streaming: {e}"))
    
    def _enable_embeddings(self):
        """Active les embeddings vectoriels."""
        self.stdout.write("Activation des embeddings vectoriels...")
        
        try:
            # Mettre à jour la configuration dans la base de données
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO django_settings (key, value) 
                        VALUES ('AI_ASSISTANT_ENABLE_EMBEDDINGS', 'True')
                        ON CONFLICT (key) DO UPDATE SET value = 'True'
                    """)
            
            # Mettre à jour la configuration dans Redis
            r = self._get_redis_connection()
            if r:
                r.set('AI_ASSISTANT_ENABLE_EMBEDDINGS', 'True')
                self.stdout.write("Configuration Redis mise à jour.")
            
            # Mettre à jour le fichier de configuration
            self._update_config_file('ENABLE_EMBEDDINGS', True)
            
            self.stdout.write(self.style.SUCCESS("Embeddings vectoriels activés avec succès"))
        except Exception as e:
            logger.exception(f"Erreur lors de l'activation des embeddings: {e}")
            self.stdout.write(self.style.ERROR(f"Erreur lors de l'activation des embeddings: {e}"))
    
    def _disable_embeddings(self):
        """Désactive les embeddings vectoriels."""
        self.stdout.write("Désactivation des embeddings vectoriels...")
        
        try:
            # Mettre à jour la configuration dans la base de données
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO django_settings (key, value) 
                        VALUES ('AI_ASSISTANT_ENABLE_EMBEDDINGS', 'False')
                        ON CONFLICT (key) DO UPDATE SET value = 'False'
                    """)
            
            # Mettre à jour la configuration dans Redis
            r = self._get_redis_connection()
            if r:
                r.set('AI_ASSISTANT_ENABLE_EMBEDDINGS', 'False')
                self.stdout.write("Configuration Redis mise à jour.")
            
            # Mettre à jour le fichier de configuration
            self._update_config_file('ENABLE_EMBEDDINGS', False)
            
            self.stdout.write(self.style.SUCCESS("Embeddings vectoriels désactivés avec succès"))
        except Exception as e:
            logger.exception(f"Erreur lors de la désactivation des embeddings: {e}")
            self.stdout.write(self.style.ERROR(f"Erreur lors de la désactivation des embeddings: {e}"))
    
    def _setup_elasticsearch_embeddings(self):
        """Configure Elasticsearch pour les embeddings vectoriels."""
        self.stdout.write("Configuration d'Elasticsearch pour les embeddings vectoriels...")
        
        try:
            # Vérifier si Elasticsearch est activé
            if not ai_settings.ENABLE_KNOWLEDGE_BASE:
                self.stdout.write("La base de connaissances est désactivée, ignoré.")
                return
            
            # Connexion à Elasticsearch
            es_host = ai_settings.ELASTICSEARCH_HOST
            es_port = ai_settings.ELASTICSEARCH_PORT
            es_user = ai_settings.ELASTICSEARCH_USER
            es_password = ai_settings.ELASTICSEARCH_PASSWORD
            es_index = ai_settings.ELASTICSEARCH_INDEX
            
            # Construire l'URL de connexion
            es_url = f"http://{es_host}:{es_port}"
            if es_user and es_password:
                es_url = f"http://{es_user}:{es_password}@{es_host}:{es_port}"
            
            # Connexion à Elasticsearch
            es = Elasticsearch([es_url])
            
            # Vérifier la connexion
            if not es.ping():
                self.stdout.write(self.style.ERROR(f"Impossible de se connecter à Elasticsearch à {es_url}"))
                return
            
            # Créer l'index pour les embeddings vectoriels
            if not es.indices.exists(index=es_index):
                # Configuration de l'index avec support des embeddings vectoriels
                index_settings = {
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 0
                    },
                    "mappings": {
                        "properties": {
                            "content": {
                                "type": "text"
                            },
                            "embedding": {
                                "type": "dense_vector",
                                "dims": 384  # Dimension des embeddings (dépend du modèle)
                            },
                            "metadata": {
                                "type": "object"
                            }
                        }
                    }
                }
                
                # Créer l'index
                es.indices.create(index=es_index, body=index_settings)
                self.stdout.write(f"Index '{es_index}' créé avec succès")
            else:
                self.stdout.write(f"L'index '{es_index}' existe déjà")
            
            self.stdout.write(self.style.SUCCESS("Configuration d'Elasticsearch terminée avec succès"))
        except Exception as e:
            logger.exception(f"Erreur lors de la configuration d'Elasticsearch: {e}")
            self.stdout.write(self.style.ERROR(f"Erreur lors de la configuration d'Elasticsearch: {e}"))
    
    def _clear_cache(self):
        """Vide le cache des réponses."""
        self.stdout.write("Vidage du cache des réponses...")
        
        try:
            # Vider le cache Django
            cache.clear()
            
            # Vider le cache Redis
            r = self._get_redis_connection()
            if r:
                # Supprimer uniquement les clés liées à l'AI Assistant
                keys = r.keys('ai_assistant:*')
                if keys:
                    r.delete(*keys)
                self.stdout.write(f"{len(keys)} clés supprimées du cache Redis")
            
            self.stdout.write(self.style.SUCCESS("Cache vidé avec succès"))
        except Exception as e:
            logger.exception(f"Erreur lors du vidage du cache: {e}")
            self.stdout.write(self.style.ERROR(f"Erreur lors du vidage du cache: {e}"))
    
    def _configure_all_optimizations(self):
        """Configure toutes les optimisations."""
        self.stdout.write("Configuration de toutes les optimisations...")
        
        # Créer les fichiers de configuration
        self._create_config_files()
        
        # Activer le cache
        self._enable_cache()
        
        # Activer le streaming
        self._enable_streaming()
        
        # Activer les embeddings
        self._enable_embeddings()
        
        # Configurer Elasticsearch
        self._setup_elasticsearch_embeddings()
        
        self.stdout.write(self.style.SUCCESS("Toutes les optimisations ont été configurées avec succès"))
    
    def _update_models_for_streaming(self):
        """Met à jour les modèles AI pour supporter le streaming."""
        self.stdout.write("Mise à jour des modèles AI pour le streaming...")
        
        try:
            # Récupérer tous les modèles qui supportent le streaming
            streaming_models = AIModel.objects.filter(supports_streaming=True)
            
            # Activer le streaming pour ces modèles
            for model in streaming_models:
                model.streaming_enabled = True
                model.save()
            
            self.stdout.write(f"{streaming_models.count()} modèles mis à jour pour le streaming")
        except Exception as e:
            logger.exception(f"Erreur lors de la mise à jour des modèles: {e}")
            self.stdout.write(self.style.ERROR(f"Erreur lors de la mise à jour des modèles: {e}"))
    
    def _create_config_files(self):
        """Crée les fichiers de configuration pour les optimisations."""
        self.stdout.write("Création des fichiers de configuration...")
        
        try:
            # Chemin des fichiers de configuration
            config_dir = Path(__file__).resolve().parent.parent.parent / 'config'
            config_file = config_dir / 'optimizations.py'
            init_file = config_dir / '__init__.py'
            settings_file = config_dir / 'settings.py'
            
            # Créer le répertoire si nécessaire
            config_dir.mkdir(exist_ok=True)
            
            # Contenu du fichier optimizations.py
            optimizations_content = """
# Configuration des optimisations de l'AI Assistant
# Ce fichier est généré automatiquement

# Mise en cache des réponses
CACHE_ENABLED = True
CACHE_TIMEOUT = 3600  # 1 heure

# Streaming des réponses
ENABLE_STREAMING = True
STREAMING_CHUNK_SIZE = 50

# Embeddings vectoriels
ENABLE_EMBEDDINGS = True
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384
"""
            
            # Contenu du fichier __init__.py
            init_content = """
# Module de configuration des optimisations de l'AI Assistant

from .optimizations import *

# Configuration des paramètres par défaut
AI_ASSISTANT_CACHE_ENABLED = True
AI_ASSISTANT_CACHE_TIMEOUT = 3600
AI_ASSISTANT_ENABLE_STREAMING = True
AI_ASSISTANT_ENABLE_EMBEDDINGS = True
"""
            
            # Contenu du fichier settings.py
            settings_content = """
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
REDIS_HOST = "172.18.0.3"  # Adresse IP du conteneur Redis
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
"""
            
            # Écrire les fichiers
            with open(config_file, 'w') as f:
                f.write(optimizations_content)
            
            with open(init_file, 'w') as f:
                f.write(init_content)
            
            with open(settings_file, 'w') as f:
                f.write(settings_content)
            
            self.stdout.write(f"Fichiers de configuration créés: {config_file}, {init_file}, {settings_file}")
        except Exception as e:
            logger.exception(f"Erreur lors de la création des fichiers de configuration: {e}")
            self.stdout.write(self.style.ERROR(f"Erreur lors de la création des fichiers de configuration: {e}"))
    
    def _update_config_file(self, key, value):
        """Met à jour une valeur dans le fichier de configuration."""
        try:
            # Chemin du fichier de configuration
            config_dir = Path(__file__).resolve().parent.parent.parent / 'config'
            config_file = config_dir / 'optimizations.py'
            
            # Vérifier si le fichier existe
            if not config_file.exists():
                self._create_config_files()
                return
            
            # Lire le contenu du fichier
            with open(config_file, 'r') as f:
                content = f.read()
            
            # Convertir la valeur en chaîne
            str_value = str(value)
            if isinstance(value, bool):
                str_value = 'True' if value else 'False'
            
            # Mettre à jour la valeur
            import re
            pattern = rf"{key}\s*=\s*.*"
            replacement = f"{key} = {str_value}"
            new_content = re.sub(pattern, replacement, content)
            
            # Écrire le contenu mis à jour
            with open(config_file, 'w') as f:
                f.write(new_content)
            
            self.stdout.write(f"Fichier de configuration mis à jour: {key} = {str_value}")
        except Exception as e:
            logger.exception(f"Erreur lors de la mise à jour du fichier de configuration: {e}")
            self.stdout.write(self.style.ERROR(f"Erreur lors de la mise à jour du fichier de configuration: {e}")) 