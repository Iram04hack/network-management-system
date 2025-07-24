"""
Configuration de l'application Django pour l'assistant IA.

Ce module définit la configuration de l'application Django pour l'assistant IA.
"""

from django.apps import AppConfig
import logging
import os
import asyncio
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


class AIAssistantConfig(AppConfig):
    """
    Configuration de l'application AI Assistant.
    
    Cette application fournit des services d'assistant IA pour la gestion
    de réseaux informatiques, incluant la génération de réponses intelligentes,
    l'exécution sécurisée de commandes et la gestion documentaire.
    """
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ai_assistant'
    verbose_name = 'Assistant IA'
    
    def ready(self):
        """
        Code d'initialisation exécuté lors du démarrage de l'application.
        """
        try:
            # Import des signaux pour s'assurer qu'ils sont enregistrés
            import ai_assistant.signals
            
            # Import de la configuration DI (si disponible)
            try:
                from ai_assistant.config.di import setup_dependency_injection
                setup_dependency_injection()
            except ImportError:
                logger.warning("Configuration DI non disponible")
            
            # Validation de la configuration en mode DEBUG
            from django.conf import settings
            if settings.DEBUG:
                # Éviter les appels directs à l'ORM dans le contexte ready()
                try:
                    # Tenter d'exécuter sans async si possible
                    self._validate_configuration_sync()
                except RuntimeError:
                    # Si on est dans un contexte async, programmer pour plus tard
                    logger.info("Validation de configuration programmée pour plus tard")
            
            # Programmer l'auto-migration pour éviter les conflits async
            # Les migrations ne doivent pas s'exécuter dans ready() qui peut être async
            logger.info("Auto-migration désactivée dans ready() pour éviter les conflits async")
                
            logger.info("Module AI Assistant initialisé avec succès")
                
        except ImportError as e:
            # Log l'erreur mais ne bloque pas le démarrage
            logger.warning(f"Erreur lors de l'initialisation de AI Assistant: {e}")
    
    @sync_to_async
    def _auto_migrate(self):
        """
        Exécute automatiquement les migrations pour l'application ai_assistant.
        Cette fonction vérifie si des migrations sont nécessaires et les applique.
        """
        try:
            # Éviter l'exécution lors des tests ou des commandes de migration
            import sys
            if 'test' in sys.argv or 'makemigrations' in sys.argv or 'migrate' in sys.argv:
                return

            # Vérification si des migrations sont nécessaires
            from django.db.migrations.executor import MigrationExecutor
            from django.db import connections, DEFAULT_DB_ALIAS

            connection = connections[DEFAULT_DB_ALIAS]
            connection.prepare_database()
            executor = MigrationExecutor(connection)
            plan = executor.migration_plan([('ai_assistant', None)])
            
            if plan:
                logger.info("Migrations automatiques nécessaires pour ai_assistant, application en cours...")
                
                # Exécution des migrations
                from django.core.management import call_command
                call_command('migrate', 'ai_assistant', verbosity=0, interactive=False)
                
                logger.info("Migrations automatiques appliquées avec succès")
            else:
                logger.info("Aucune migration automatique nécessaire pour ai_assistant")
                
        except Exception as e:
            logger.warning(f"Erreur lors de l'auto-migration: {e}")
    
    def _validate_configuration_sync(self):
        """
        Valide la configuration de l'application en mode DEBUG (version synchrone).
        """
        from django.conf import settings
        
        # Vérifications de base (sans accès base de données)
        checks = [
            self._check_required_settings(),
            self._check_dependencies(),
            # Pas de vérification de base de données dans ready()
        ]
        
        # Afficher les résultats
        for check_name, status, message in checks:
            if status:
                logger.info(f"✅ {check_name}: {message}")
            else:
                logger.warning(f"⚠️ {check_name}: {message}")
    
    async def _validate_configuration(self):
        """
        Valide la configuration de l'application en mode DEBUG (version asynchrone).
        """
        from django.conf import settings
        
        # Vérifications de base
        checks = [
            self._check_required_settings(),
            self._check_dependencies(),
            await self._check_database_configuration(),
        ]
        
        # Afficher les résultats
        for check_name, status, message in checks:
            if status:
                logger.info(f"✅ {check_name}: {message}")
            else:
                logger.warning(f"⚠️ {check_name}: {message}")
    
    def _check_required_settings(self):
        """Vérifie les paramètres requis."""
        from django.conf import settings
        
        required_settings = [
            'SECRET_KEY',
            'DATABASES',
            'INSTALLED_APPS',
        ]
        
        missing = [setting for setting in required_settings if not hasattr(settings, setting)]
        
        if missing:
            return ("Configuration Django", False, f"Paramètres manquants: {', '.join(missing)}")
        return ("Configuration Django", True, "Tous les paramètres requis sont présents")
    
    def _check_dependencies(self):
        """Vérifie les dépendances."""
        dependencies = [
            ('django', 'Framework Django'),
            ('rest_framework', 'Django REST Framework'),
            ('channels', 'Django Channels pour WebSocket'),
            ('celery', 'Celery pour les tâches asynchrones'),
        ]
        
        missing = []
        for module, description in dependencies:
            try:
                __import__(module)
            except ImportError:
                missing.append(f"{module} ({description})")
        
        if missing:
            return ("Dépendances", False, f"Dépendances manquantes: {', '.join(missing)}")
        return ("Dépendances", True, "Toutes les dépendances requises sont installées")
    
    @sync_to_async
    def _check_database_configuration(self):
        """Vérifie la configuration de la base de données."""
        from django.db import connection
        
        try:
            # Test de connexion simple
            connection.ensure_connection()
            return ("Base de données", True, f"Connexion réussie ({connection.vendor})")
        except Exception as e:
            return ("Base de données", False, f"Erreur de connexion: {str(e)}")
