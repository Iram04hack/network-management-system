from django.apps import AppConfig

class GNS3IntegrationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gns3_integration'
    verbose_name = "Intégration GNS3"
    
    def ready(self):
        """
        Initialisation de l'application lors du démarrage.
        """
        try:
            # Import des signaux pour les enregistrer
            import gns3_integration.signals
            
            # Initialiser le conteneur d'injection de dépendances
            from .di_container import init_di_container
            init_di_container()
            
        except Exception as e:
            print(f"Warning: Could not initialize GNS3 integration: {e}") 