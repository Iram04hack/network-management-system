"""
Service d'application pour la gestion des templates GNS3.

Ce module contient les services d'application qui orchestrent les opérations
liées aux templates GNS3 entre les interfaces de domaine et l'extérieur.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from django.db import transaction
from django.contrib.auth.models import User

from gns3_integration.domain.interfaces import GNS3ClientPort, GNS3Repository
from gns3_integration.domain.models import Template
from gns3_integration.domain.exceptions import (
    GNS3Exception, GNS3ConnectionError, GNS3ResourceNotFoundError,
    GNS3OperationError, GNS3RepositoryError
)

logger = logging.getLogger(__name__)

class TemplateService:
    """
    Service pour la gestion des templates GNS3.
    
    Ce service orchestre les opérations entre le client GNS3,
    le repository et les entités du domaine pour la gestion des templates.
    """
    
    def __init__(self, gns3_client: GNS3ClientPort, gns3_repository: GNS3Repository):
        """
        Initialise le service.
        
        Args:
            gns3_client: Client GNS3
            gns3_repository: Repository GNS3
        """
        self.client = gns3_client
        self.repository = gns3_repository
    
    def list_templates(self) -> List[Template]:
        """
        Liste tous les templates GNS3.
        
        Returns:
            Liste des templates
            
        Raises:
            GNS3ConnectionError: Erreur de connexion au serveur GNS3
            GNS3RepositoryError: Erreur avec le repository
        """
        try:
            # Récupération des templates depuis le repository
            return self.repository.list_templates()
        except GNS3RepositoryError as e:
            logger.error(f"Erreur repository lors de la récupération des templates: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la récupération des templates: {e}")
            raise GNS3Exception(f"Erreur lors de la récupération des templates: {e}")
    
    def get_template(self, template_id: str) -> Optional[Template]:
        """
        Récupère les détails d'un template GNS3.
        
        Args:
            template_id: ID du template
            
        Returns:
            Template ou None si non trouvé
            
        Raises:
            GNS3ConnectionError: Erreur de connexion au serveur GNS3
            GNS3ResourceNotFoundError: Template non trouvé
            GNS3RepositoryError: Erreur avec le repository
        """
        try:
            # Récupération du template depuis le repository
            template = self.repository.get_template(template_id)
            
            if not template:
                logger.warning(f"Template {template_id} non trouvé dans le repository")
                raise GNS3ResourceNotFoundError(f"Template {template_id} non trouvé")
                
            return template
        except GNS3ResourceNotFoundError:
            raise
        except GNS3RepositoryError as e:
            logger.error(f"Erreur repository lors de la récupération du template {template_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la récupération du template {template_id}: {e}")
            raise GNS3Exception(f"Erreur lors de la récupération du template: {e}")
    
    @transaction.atomic
    def sync_templates(self) -> List[Template]:
        """
        Synchronise tous les templates entre GNS3 et le repository.
        
        Cette méthode récupère tous les templates du serveur GNS3 et
        les synchronise avec le repository.
        
        Returns:
            Liste des templates synchronisés
            
        Raises:
            GNS3ConnectionError: Erreur de connexion au serveur GNS3
            GNS3RepositoryError: Erreur avec le repository
        """
        try:
            # Récupération de tous les templates depuis le serveur GNS3
            gns3_templates = self.client.list_templates()
            
            templates = []
            for gns3_template in gns3_templates:
                # Recherche du template dans le repository
                template = self.repository.get_template(gns3_template["template_id"])
                
                if not template:
                    # Création d'une nouvelle entité Template si elle n'existe pas
                    template = Template(
                        id=gns3_template["template_id"],
                        name=gns3_template["name"],
                        template_type=gns3_template.get("template_type", ""),
                        compute_id=gns3_template.get("compute_id", "local"),
                        console_type=gns3_template.get("console_type", ""),
                        symbol=gns3_template.get("symbol", ""),
                        image=gns3_template.get("image", ""),
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                else:
                    # Mise à jour de l'entité Template existante
                    template.name = gns3_template["name"]
                    template.template_type = gns3_template.get("template_type", template.template_type)
                    template.compute_id = gns3_template.get("compute_id", template.compute_id)
                    template.console_type = gns3_template.get("console_type", template.console_type)
                    template.symbol = gns3_template.get("symbol", template.symbol)
                    template.image = gns3_template.get("image", template.image)
                    template.updated_at = datetime.now()
                
                # Sauvegarde dans le repository
                templates.append(self.repository.save_template(template))
            
            return templates
        except GNS3ConnectionError as e:
            logger.error(f"Erreur de connexion lors de la synchronisation des templates: {e}")
            raise
        except GNS3RepositoryError as e:
            logger.error(f"Erreur repository lors de la synchronisation des templates: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la synchronisation des templates: {e}")
            raise GNS3Exception(f"Erreur lors de la synchronisation des templates: {e}")
    
    @transaction.atomic
    def sync_template(self, template_id: str) -> Template:
        """
        Synchronise un template entre GNS3 et le repository.
        
        Cette méthode récupère les informations à jour du template sur le serveur GNS3
        et les synchronise avec le repository.
        
        Args:
            template_id: ID du template
            
        Returns:
            Template synchronisé
            
        Raises:
            GNS3ConnectionError: Erreur de connexion au serveur GNS3
            GNS3ResourceNotFoundError: Template non trouvé
            GNS3RepositoryError: Erreur avec le repository
        """
        try:
            # Récupération des informations à jour sur le serveur GNS3
            gns3_template = self.client.get_template(template_id)
            
            # Recherche du template dans le repository
            template = self.repository.get_template(template_id)
            
            if not template:
                # Création d'une nouvelle entité Template si elle n'existe pas
                template = Template(
                    id=gns3_template["template_id"],
                    name=gns3_template["name"],
                    template_type=gns3_template.get("template_type", ""),
                    compute_id=gns3_template.get("compute_id", "local"),
                    console_type=gns3_template.get("console_type", ""),
                    symbol=gns3_template.get("symbol", ""),
                    image=gns3_template.get("image", ""),
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
            else:
                # Mise à jour de l'entité Template existante
                template.name = gns3_template["name"]
                template.template_type = gns3_template.get("template_type", template.template_type)
                template.compute_id = gns3_template.get("compute_id", template.compute_id)
                template.console_type = gns3_template.get("console_type", template.console_type)
                template.symbol = gns3_template.get("symbol", template.symbol)
                template.image = gns3_template.get("image", template.image)
                template.updated_at = datetime.now()
            
            # Sauvegarde dans le repository
            return self.repository.save_template(template)
        except GNS3ResourceNotFoundError:
            raise
        except GNS3ConnectionError as e:
            logger.error(f"Erreur de connexion lors de la synchronisation du template {template_id}: {e}")
            raise
        except GNS3RepositoryError as e:
            logger.error(f"Erreur repository lors de la mise à jour du template {template_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la synchronisation du template {template_id}: {e}")
            raise GNS3Exception(f"Erreur lors de la synchronisation du template: {e}")
    
    def list_available_node_types(self) -> List[Dict[str, Any]]:
        """
        Liste tous les types de nœuds disponibles sur le serveur GNS3.
        
        Returns:
            Liste des types de nœuds disponibles
            
        Raises:
            GNS3ConnectionError: Erreur de connexion au serveur GNS3
        """
        try:
            return self.client.list_node_types()
        except GNS3ConnectionError as e:
            logger.error(f"Erreur de connexion lors de la récupération des types de nœuds: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la récupération des types de nœuds: {e}")
            raise GNS3Exception(f"Erreur lors de la récupération des types de nœuds: {e}")
    
    def filter_templates_by_type(self, template_type: str) -> List[Template]:
        """
        Filtre les templates par type.
        
        Args:
            template_type: Type de template (ex: "qemu", "docker", "vpcs", etc.)
            
        Returns:
            Liste des templates du type spécifié
            
        Raises:
            GNS3RepositoryError: Erreur avec le repository
        """
        try:
            templates = self.list_templates()
            return [t for t in templates if t.template_type == template_type]
        except GNS3RepositoryError as e:
            logger.error(f"Erreur repository lors du filtrage des templates par type {template_type}: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors du filtrage des templates par type {template_type}: {e}")
            raise GNS3Exception(f"Erreur lors du filtrage des templates: {e}") 