"""
Conteneur d'injection de dépendances pour le module GNS3 Integration.
"""
from dependency_injector import containers, providers


class GNS3Container(containers.DeclarativeContainer):
    """Conteneur d'injection de dépendances pour les services GNS3."""
    
    # Configuration
    config = providers.Configuration()


# Instance du conteneur
gns3_container = GNS3Container()

def init_di_container():
    """
    Initialise le conteneur d'injection de dépendances.
    
    Cette fonction configure et initialise le conteneur GNS3
    avec les dépendances nécessaires.
    
    Returns:
        GNS3Container: Le conteneur initialisé
    """
    try:
        # Import tardif pour éviter les problèmes circulaires
        from gns3_integration.application.project_service import ProjectService
        from gns3_integration.application.multi_project_service import MultiProjectService
        from gns3_integration.application.node_service import NodeService
        from gns3_integration.application.link_service import LinkService
        from gns3_integration.application.template_service import TemplateService
        from gns3_integration.application.server_service import ServerService
        from gns3_integration.application.snapshot_service import SnapshotService
        from gns3_integration.application.script_service import ScriptService
        from gns3_integration.application.workflow_service import WorkflowService
        from gns3_integration.infrastructure.gns3_client_impl import DefaultGNS3Client
        from gns3_integration.infrastructure.gns3_repository_impl import DjangoGNS3Repository
        
        # Configuration des services d'infrastructure
        gns3_container.gns3_client = providers.Singleton(DefaultGNS3Client)
        gns3_container.gns3_repository = providers.Singleton(DjangoGNS3Repository)
        
        # Configuration des services métier
        gns3_container.server_service = providers.Singleton(
            ServerService,
            gns3_client=gns3_container.gns3_client,
            gns3_repository=gns3_container.gns3_repository
        )
        
        gns3_container.project_service = providers.Singleton(
            ProjectService,
            gns3_client=gns3_container.gns3_client,
            gns3_repository=gns3_container.gns3_repository
        )
        
        gns3_container.multi_project_service = providers.Singleton(
            MultiProjectService,
            project_service=gns3_container.project_service,
            gns3_client=gns3_container.gns3_client,
            gns3_repository=gns3_container.gns3_repository
        )
        
        gns3_container.node_service = providers.Singleton(
            NodeService,
            gns3_client=gns3_container.gns3_client,
            gns3_repository=gns3_container.gns3_repository
        )
        
        gns3_container.link_service = providers.Singleton(
            LinkService,
            gns3_client=gns3_container.gns3_client,
            gns3_repository=gns3_container.gns3_repository
        )
        
        gns3_container.template_service = providers.Singleton(
            TemplateService,
            gns3_client=gns3_container.gns3_client,
            gns3_repository=gns3_container.gns3_repository
        )
        
        # Nouveaux services ajoutés
        gns3_container.snapshot_service = providers.Singleton(
            SnapshotService,
            gns3_client=gns3_container.gns3_client,
            gns3_repository=gns3_container.gns3_repository
        )
        
        gns3_container.script_service = providers.Singleton(
            ScriptService,
            gns3_client=gns3_container.gns3_client,
            gns3_repository=gns3_container.gns3_repository
        )
        
        gns3_container.workflow_service = providers.Singleton(
            WorkflowService,
            gns3_client=gns3_container.gns3_client,
            gns3_repository=gns3_container.gns3_repository
        )
        
        # Configuration du conteneur avec initialisation forcée
        gns3_container.config.from_dict({
            'debug': True,
        })
        
        # Forcer l'initialisation du conteneur
        gns3_container.wire(modules=[])
        
        print("GNS3 Container initialized successfully")
        
    except ImportError as e:
        print(f"Warning: Could not initialize GNS3 container: {e}")
    except Exception as e:
        print(f"Error initializing GNS3 container: {e}")
    
    return gns3_container


def resolve(service_name: str):
    """
    Résout une dépendance à partir du conteneur.

    Args:
        service_name: Nom du service à résoudre

    Returns:
        Instance du service demandé
    """
    if not hasattr(gns3_container, service_name):
        raise ValueError(f"Service '{service_name}' not found in container")

    return getattr(gns3_container, service_name)() 