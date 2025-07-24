"""
Commande Django pour mettre à niveau le module AI Assistant.

Cette commande effectue les mises à niveau nécessaires pour le module AI Assistant,
notamment la création des tables pour les nouvelles fonctionnalités et la migration
des données existantes.
"""

import logging
import time
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.conf import settings
from elasticsearch import Elasticsearch

from ai_assistant.models import AIModel, Conversation, Message
from ai_assistant.config import settings as ai_settings

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Met à niveau le module AI Assistant avec les nouvelles fonctionnalités"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force la mise à niveau même si elle a déjà été effectuée'
        )
        parser.add_argument(
            '--skip-elasticsearch',
            action='store_true',
            help='Ignore la mise à niveau de la base de connaissances Elasticsearch'
        )
        parser.add_argument(
            '--skip-database',
            action='store_true',
            help='Ignore la mise à niveau de la base de données'
        )
    
    def handle(self, *args, **options):
        start_time = time.time()
        self.stdout.write(self.style.NOTICE("Démarrage de la mise à niveau du module AI Assistant..."))
        
        force = options.get('force', False)
        skip_elasticsearch = options.get('skip_elasticsearch', False)
        skip_database = options.get('skip_database', False)
        
        # Vérifier si la mise à niveau a déjà été effectuée
        if not force and self._is_already_upgraded():
            self.stdout.write(self.style.SUCCESS("Le module AI Assistant est déjà à jour. Utilisez --force pour forcer la mise à niveau."))
            return
        
        # Mise à niveau de la base de données
        if not skip_database:
            self._upgrade_database()
        
        # Mise à niveau de la base de connaissances Elasticsearch
        if not skip_elasticsearch:
            self._upgrade_elasticsearch()
        
        # Mise à niveau des modèles AI par défaut
        self._upgrade_ai_models()
        
        # Mise à jour de la version
        self._update_version()
        
        execution_time = time.time() - start_time
        self.stdout.write(self.style.SUCCESS(
            f"Mise à niveau terminée avec succès en {execution_time:.2f} secondes!"
        ))
    
    def _is_already_upgraded(self):
        """Vérifie si la mise à niveau a déjà été effectuée."""
        try:
            # Vérifier si la table de version existe
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_name = 'ai_assistant_version'
                """)
                if not cursor.fetchone():
                    return False
                
                # Vérifier la version actuelle
                cursor.execute("SELECT version FROM ai_assistant_version")
                row = cursor.fetchone()
                if row and row[0] >= "3.0.0":
                    return True
                
            return False
        except Exception as e:
            logger.exception(f"Erreur lors de la vérification de la version: {e}")
            return False
    
    def _upgrade_database(self):
        """Met à niveau la base de données."""
        self.stdout.write(self.style.NOTICE("Mise à niveau de la base de données..."))
        
        try:
            with transaction.atomic():
                # Créer la table de version si elle n'existe pas
                with connection.cursor() as cursor:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS ai_assistant_version (
                            id SERIAL PRIMARY KEY,
                            version VARCHAR(20) NOT NULL,
                            upgraded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                        )
                    """)
                
                # Vérifier et mettre à jour la structure des tables existantes
                self._update_conversations_table()
                self._update_messages_table()
                self._update_ai_models_table()
                
                self.stdout.write(self.style.SUCCESS("Base de données mise à niveau avec succès"))
        except Exception as e:
            logger.exception(f"Erreur lors de la mise à niveau de la base de données: {e}")
            self.stdout.write(self.style.ERROR(f"Erreur lors de la mise à niveau de la base de données: {e}"))
            raise
    
    def _update_conversations_table(self):
        """Met à jour la structure de la table des conversations."""
        self.stdout.write("Mise à jour de la table des conversations...")
        
        with connection.cursor() as cursor:
            # Vérifier si la colonne 'metadata' existe
            cursor.execute("""
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'ai_assistant_conversation' AND column_name = 'metadata'
            """)
            
            if not cursor.fetchone():
                # Ajouter la colonne 'metadata'
                cursor.execute("""
                    ALTER TABLE ai_assistant_conversation
                    ADD COLUMN metadata JSONB DEFAULT '{}'
                """)
                self.stdout.write("Colonne 'metadata' ajoutée à la table des conversations")
            
            # Vérifier si la colonne 'is_active' existe
            cursor.execute("""
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'ai_assistant_conversation' AND column_name = 'is_active'
            """)
            
            if not cursor.fetchone():
                # Ajouter la colonne 'is_active'
                cursor.execute("""
                    ALTER TABLE ai_assistant_conversation
                    ADD COLUMN is_active BOOLEAN DEFAULT TRUE
                """)
                self.stdout.write("Colonne 'is_active' ajoutée à la table des conversations")
    
    def _update_messages_table(self):
        """Met à jour la structure de la table des messages."""
        self.stdout.write("Mise à jour de la table des messages...")
        
        with connection.cursor() as cursor:
            # Vérifier si la colonne 'tokens' existe
            cursor.execute("""
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'ai_assistant_message' AND column_name = 'tokens'
            """)
            
            if not cursor.fetchone():
                # Ajouter la colonne 'tokens'
                cursor.execute("""
                    ALTER TABLE ai_assistant_message
                    ADD COLUMN tokens INTEGER DEFAULT 0
                """)
                self.stdout.write("Colonne 'tokens' ajoutée à la table des messages")
            
            # Vérifier si la colonne 'processing_time' existe
            cursor.execute("""
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'ai_assistant_message' AND column_name = 'processing_time'
            """)
            
            if not cursor.fetchone():
                # Ajouter la colonne 'processing_time'
                cursor.execute("""
                    ALTER TABLE ai_assistant_message
                    ADD COLUMN processing_time FLOAT DEFAULT 0
                """)
                self.stdout.write("Colonne 'processing_time' ajoutée à la table des messages")
    
    def _update_ai_models_table(self):
        """Met à jour la structure de la table des modèles AI."""
        self.stdout.write("Mise à jour de la table des modèles AI...")
        
        with connection.cursor() as cursor:
            # Vérifier si la colonne 'endpoint' existe
            cursor.execute("""
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'ai_assistant_aimodel' AND column_name = 'endpoint'
            """)
            
            if not cursor.fetchone():
                # Ajouter la colonne 'endpoint'
                cursor.execute("""
                    ALTER TABLE ai_assistant_aimodel
                    ADD COLUMN endpoint VARCHAR(255) DEFAULT ''
                """)
                self.stdout.write("Colonne 'endpoint' ajoutée à la table des modèles AI")
            
            # Vérifier si la colonne 'token_limit' existe
            cursor.execute("""
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'ai_assistant_aimodel' AND column_name = 'token_limit'
            """)
            
            if not cursor.fetchone():
                # Ajouter la colonne 'token_limit'
                cursor.execute("""
                    ALTER TABLE ai_assistant_aimodel
                    ADD COLUMN token_limit INTEGER DEFAULT 4096
                """)
                self.stdout.write("Colonne 'token_limit' ajoutée à la table des modèles AI")
    
    def _upgrade_elasticsearch(self):
        """Met à niveau la base de connaissances Elasticsearch."""
        self.stdout.write(self.style.NOTICE("Mise à niveau de la base de connaissances Elasticsearch..."))
        
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
            es_url = f"http://{es_host}:{es_port}"
            
            # Configuration de l'authentification si nécessaire
            es_params = {}
            if es_user and es_password:
                es_params['basic_auth'] = (es_user, es_password)
                
            es = Elasticsearch(es_url, **es_params)
            
            # Vérifier la connexion
            if not es.ping():
                self.stdout.write(self.style.WARNING(
                    f"Impossible de se connecter à Elasticsearch à {es_url}. "
                    "La mise à niveau de la base de connaissances sera ignorée."
                ))
                return
            
            # Vérifier si l'index existe
            index_name = ai_settings.ELASTICSEARCH_INDEX
            if es.indices.exists(index=index_name):
                # Mettre à jour le mapping pour ajouter le support des embeddings
                if ai_settings.ENABLE_EMBEDDINGS:
                    self._update_elasticsearch_mapping(es, index_name)
            else:
                # Créer l'index avec le mapping complet
                self._create_elasticsearch_index(es, index_name)
            
            self.stdout.write(self.style.SUCCESS("Base de connaissances Elasticsearch mise à niveau avec succès"))
        except Exception as e:
            logger.exception(f"Erreur lors de la mise à niveau d'Elasticsearch: {e}")
            self.stdout.write(self.style.WARNING(
                f"Erreur lors de la mise à niveau d'Elasticsearch: {e}. "
                "La mise à niveau de la base de connaissances sera ignorée."
            ))
    
    def _update_elasticsearch_mapping(self, es, index_name):
        """Met à jour le mapping Elasticsearch pour ajouter le support des embeddings."""
        self.stdout.write(f"Mise à jour du mapping de l'index {index_name}...")
        
        try:
            # Vérifier si le champ embedding existe déjà
            mapping = es.indices.get_mapping(index=index_name)
            properties = mapping[index_name]['mappings'].get('properties', {})
            
            if 'embedding' not in properties:
                # Ajouter le champ embedding
                update_mapping = {
                    "properties": {
                        "embedding": {
                            "type": "dense_vector",
                            "dims": ai_settings.EMBEDDING_DIMENSION
                        }
                    }
                }
                
                es.indices.put_mapping(index=index_name, body=update_mapping)
                self.stdout.write(f"Champ 'embedding' ajouté à l'index {index_name}")
        except Exception as e:
            logger.exception(f"Erreur lors de la mise à jour du mapping: {e}")
            self.stdout.write(self.style.WARNING(f"Erreur lors de la mise à jour du mapping: {e}"))
    
    def _create_elasticsearch_index(self, es, index_name):
        """Crée un nouvel index Elasticsearch avec le mapping complet."""
        self.stdout.write(f"Création de l'index {index_name}...")
        
        # Définir le mapping avec support pour les embeddings
        mapping = {
            "mappings": {
                "properties": {
                    "title": {"type": "text", "analyzer": "standard"},
                    "content": {"type": "text", "analyzer": "standard"},
                    "metadata": {"type": "object"},
                    "created_at": {"type": "date"},
                    "updated_at": {"type": "date"}
                }
            },
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "analysis": {
                    "analyzer": {
                        "standard": {
                            "type": "standard",
                            "stopwords": "_french_"
                        }
                    }
                }
            }
        }
        
        # Ajouter le champ embedding si activé
        if ai_settings.ENABLE_EMBEDDINGS:
            mapping["mappings"]["properties"]["embedding"] = {
                "type": "dense_vector",
                "dims": ai_settings.EMBEDDING_DIMENSION
            }
        
        # Créer l'index
        es.indices.create(index=index_name, body=mapping)
        self.stdout.write(f"Index {index_name} créé avec succès")
    
    def _upgrade_ai_models(self):
        """Met à niveau les modèles AI par défaut."""
        self.stdout.write(self.style.NOTICE("Mise à niveau des modèles AI par défaut..."))
        
        try:
            # Vérifier si des modèles existent déjà
            if AIModel.objects.exists():
                # Mettre à jour les modèles existants
                default_model = AIModel.objects.filter(is_active=True).first()
                if default_model:
                    # Mettre à jour les paramètres du modèle par défaut
                    default_model.parameters = {
                        'temperature': 0.7,
                        'max_tokens': ai_settings.MAX_RESPONSE_TOKENS,
                        'system_message': "Tu es un assistant IA spécialisé dans la gestion de réseaux informatiques."
                    }
                    default_model.token_limit = 4096  # Valeur par défaut pour GPT-3.5
                    default_model.save()
                    self.stdout.write(f"Modèle par défaut '{default_model.name}' mis à jour")
            else:
                # Créer un modèle par défaut
                default_model = AIModel.objects.create(
                    name="gpt-3.5-turbo",
                    provider="openai",
                    model_name="gpt-3.5-turbo",
                    api_key=ai_settings.DEFAULT_AI_API_KEY,
                    is_active=True,
                    token_limit=4096,
                    parameters={
                        'temperature': 0.7,
                        'max_tokens': ai_settings.MAX_RESPONSE_TOKENS,
                        'system_message': "Tu es un assistant IA spécialisé dans la gestion de réseaux informatiques."
                    }
                )
                self.stdout.write(f"Modèle par défaut '{default_model.name}' créé")
                
                # Créer un modèle GPT-4 (désactivé par défaut)
                gpt4_model = AIModel.objects.create(
                    name="gpt-4",
                    provider="openai",
                    model_name="gpt-4",
                    api_key=ai_settings.DEFAULT_AI_API_KEY,
                    is_active=False,
                    token_limit=8192,
                    parameters={
                        'temperature': 0.7,
                        'max_tokens': 1500,
                        'system_message': "Tu es un assistant IA avancé spécialisé dans la gestion de réseaux informatiques complexes."
                    }
                )
                self.stdout.write(f"Modèle '{gpt4_model.name}' créé (désactivé par défaut)")
            
            self.stdout.write(self.style.SUCCESS("Modèles AI mis à niveau avec succès"))
        except Exception as e:
            logger.exception(f"Erreur lors de la mise à niveau des modèles AI: {e}")
            self.stdout.write(self.style.ERROR(f"Erreur lors de la mise à niveau des modèles AI: {e}"))
    
    def _update_version(self):
        """Met à jour la version du module AI Assistant."""
        try:
            with connection.cursor() as cursor:
                # Supprimer les anciennes versions
                cursor.execute("DELETE FROM ai_assistant_version")
                
                # Insérer la nouvelle version
                cursor.execute(
                    "INSERT INTO ai_assistant_version (version) VALUES (%s)",
                    ["3.0.0"]
                )
                
            self.stdout.write(self.style.SUCCESS("Version mise à jour vers 3.0.0"))
        except Exception as e:
            logger.exception(f"Erreur lors de la mise à jour de la version: {e}")
            self.stdout.write(self.style.ERROR(f"Erreur lors de la mise à jour de la version: {e}")) 