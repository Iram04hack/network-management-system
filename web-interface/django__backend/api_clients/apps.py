"""
Configuration de l'application api_clients.

Ce module contient la classe de configuration pour l'application api_clients.
"""

from django.apps import AppConfig


class ApiClientsConfig(AppConfig):
    """
    Classe de configuration pour l'application api_clients.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api_clients'
    verbose_name = 'API Clients'
    
    def ready(self):
        """
        Initialisation de l'application.
        Cette méthode est appelée lorsque l'application est prête.
        """
        # Importer les vues pour s'assurer que les décorateurs Swagger sont appliqués
        try:
            # Désactivé temporairement pour résoudre les problèmes de syntaxe
            print("✅ API Clients: Documentation Swagger temporairement désactivée")
        except Exception as e:
            print(f"❌ API Clients: Erreur lors de la génération de la documentation Swagger: {str(e)}")
            print("Documentation Swagger pour api_clients: Documentation Swagger temporairement désactivée")
        
        # Import des signaux pour les enregistrer
        try:
            import api_clients.signals  # noqa 
        except Exception as e:
            print(f"❌ API Clients: Erreur lors de l'import des signaux: {str(e)}")
        
        # Génération des fichiers JSON de documentation Swagger
        try:
            import os
            import django
            if os.environ.get('DJANGO_SETTINGS_MODULE') and not os.environ.get('DISABLE_SWAGGER_GEN'):
                # Uniquement en mode développement ou lorsqu'explicitement demandé
                try:
                    from .docs.generate_all_swagger import generate_swagger_for_all_clients
                    generate_swagger_for_all_clients()
                    print("Fichiers JSON Swagger générés dans le répertoire docs/swagger_output/")
                except Exception as e:
                    print(f"❌ API Clients: Erreur lors de la génération des fichiers Swagger: {str(e)}")
        except Exception as e:
            print(f"❌ API Clients: Erreur lors de la génération des fichiers JSON Swagger: {str(e)}")
            import sys
            print(f"Erreur lors de la génération de la documentation Swagger: {e}", file=sys.stderr) 