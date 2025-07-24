"""
Service d'application pour la gestion des scripts GNS3.

Ce module contient les services d'application qui orchestrent les opérations
liées aux scripts d'automatisation GNS3 entre les interfaces de domaine et l'extérieur.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from django.db import transaction, models
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from gns3_integration.domain.interfaces import GNS3ClientPort, GNS3Repository
from gns3_integration.models import Script, ScriptExecution, Project, Node
from gns3_integration.domain.exceptions import (
    GNS3Exception, GNS3ConnectionError, GNS3ResourceNotFoundError,
    GNS3OperationError, GNS3RepositoryError
)

logger = logging.getLogger(__name__)

class ScriptService:
    """
    Service pour la gestion des scripts d'automatisation GNS3.
    
    Ce service orchestre les opérations entre le client GNS3,
    le repository et les entités du domaine pour la gestion des scripts.
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
    
    def list_scripts(self, script_type: Optional[str] = None) -> List[Script]:
        """
        Liste tous les scripts disponibles.
        
        Args:
            script_type: Type de script à filtrer (optional)
            
        Returns:
            Liste des scripts
            
        Raises:
            GNS3RepositoryError: Erreur avec le repository
        """
        try:
            queryset = Script.objects.all()
            
            if script_type:
                queryset = queryset.filter(script_type=script_type)
            
            return queryset.order_by('name')
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des scripts: {e}")
            raise GNS3Exception(f"Erreur lors de la récupération des scripts: {e}")
    
    def get_script(self, script_id: int) -> Optional[Script]:
        """
        Récupère les détails d'un script.
        
        Args:
            script_id: ID du script
            
        Returns:
            Script ou None si non trouvé
            
        Raises:
            GNS3ResourceNotFoundError: Script non trouvé
        """
        try:
            return Script.objects.get(id=script_id)
        except Script.DoesNotExist:
            logger.warning(f"Script {script_id} non trouvé")
            raise GNS3ResourceNotFoundError(f"Script {script_id} non trouvé")
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du script: {e}")
            raise GNS3Exception(f"Erreur lors de la récupération du script: {e}")
    
    @transaction.atomic
    def create_script(self, name: str, script_type: str, content: str, 
                     description: str = "", created_by: Optional[User] = None) -> Script:
        """
        Crée un nouveau script.
        
        Args:
            name: Nom du script
            script_type: Type de script
            content: Contenu du script
            description: Description du script
            created_by: Utilisateur créateur
            
        Returns:
            Script créé
            
        Raises:
            GNS3OperationError: Erreur lors de la création
        """
        try:
            script = Script.objects.create(
                name=name,
                script_type=script_type,
                content=content,
                description=description,
                created_by=created_by
            )
            
            logger.info(f"Script '{name}' créé avec succès")
            return script
        except Exception as e:
            logger.error(f"Erreur lors de la création du script: {e}")
            raise GNS3Exception(f"Erreur lors de la création du script: {e}")
    
    @transaction.atomic
    def update_script(self, script_id: int, **kwargs) -> Script:
        """
        Met à jour un script existant.
        
        Args:
            script_id: ID du script
            **kwargs: Champs à mettre à jour
            
        Returns:
            Script mis à jour
            
        Raises:
            GNS3ResourceNotFoundError: Script non trouvé
        """
        try:
            script = Script.objects.get(id=script_id)
            
            for field, value in kwargs.items():
                if hasattr(script, field):
                    setattr(script, field, value)
            
            script.save()
            logger.info(f"Script {script_id} mis à jour avec succès")
            return script
        except Script.DoesNotExist:
            logger.warning(f"Script {script_id} non trouvé pour mise à jour")
            raise GNS3ResourceNotFoundError(f"Script {script_id} non trouvé")
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du script: {e}")
            raise GNS3Exception(f"Erreur lors de la mise à jour du script: {e}")
    
    @transaction.atomic
    def delete_script(self, script_id: int) -> bool:
        """
        Supprime un script.
        
        Args:
            script_id: ID du script
            
        Returns:
            True si supprimé avec succès
            
        Raises:
            GNS3ResourceNotFoundError: Script non trouvé
        """
        try:
            script = Script.objects.get(id=script_id)
            script.delete()
            logger.info(f"Script {script_id} supprimé avec succès")
            return True
        except Script.DoesNotExist:
            logger.warning(f"Script {script_id} non trouvé pour suppression")
            raise GNS3ResourceNotFoundError(f"Script {script_id} non trouvé")
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du script: {e}")
            raise GNS3Exception(f"Erreur lors de la suppression du script: {e}")
    
    @transaction.atomic
    def execute_script(self, script_id: int, project_id: str, node_id: str, 
                      parameters: Dict[str, Any] = None) -> ScriptExecution:
        """
        Exécute un script sur un nœud.
        
        Args:
            script_id: ID du script
            project_id: ID du projet
            node_id: ID du nœud
            parameters: Paramètres d'exécution
            
        Returns:
            Exécution de script créée
            
        Raises:
            GNS3ResourceNotFoundError: Ressource non trouvée
            GNS3OperationError: Erreur lors de l'exécution
        """
        try:
            script = Script.objects.get(id=script_id)
            project = Project.objects.get(project_id=project_id)
            node = Node.objects.get(project=project, node_id=node_id)
            
            execution = ScriptExecution.objects.create(
                script=script,
                project=project,
                node=node,
                status='pending',
                parameters=parameters or {}
            )
            
            return execution
        except (Script.DoesNotExist, Project.DoesNotExist, Node.DoesNotExist):
            raise GNS3ResourceNotFoundError("Ressource non trouvée")
    
    def list_executions(self) -> List[ScriptExecution]:
        """
        Liste les exécutions de scripts.
        
        Returns:
            Liste des exécutions
        """
        return ScriptExecution.objects.all().order_by('-created_at')
    
    def get_execution(self, execution_id: int) -> Optional[ScriptExecution]:
        """
        Récupère les détails d'une exécution.
        
        Args:
            execution_id: ID de l'exécution
            
        Returns:
            Exécution ou None si non trouvée
        """
        try:
            return ScriptExecution.objects.get(id=execution_id)
        except ScriptExecution.DoesNotExist:
            logger.warning(f"Exécution {execution_id} non trouvée")
            raise GNS3ResourceNotFoundError(f"Exécution {execution_id} non trouvée")
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'exécution: {e}")
            raise GNS3Exception(f"Erreur lors de la récupération de l'exécution: {e}")
    
    @transaction.atomic
    def cancel_execution(self, execution_id: int) -> bool:
        """
        Annule une exécution de script.
        
        Args:
            execution_id: ID de l'exécution
            
        Returns:
            True si annulée avec succès
        """
        try:
            execution = ScriptExecution.objects.get(id=execution_id)
            
            if execution.status in ['completed', 'failed', 'cancelled']:
                raise GNS3OperationError(f"Impossible d'annuler une exécution {execution.status}")
            
            execution.status = 'cancelled'
            execution.end_time = datetime.now()
            execution.save()
            
            # TODO: Arrêter l'exécution en cours si nécessaire
            logger.info(f"Exécution {execution_id} annulée")
            return True
        except ScriptExecution.DoesNotExist:
            logger.warning(f"Exécution {execution_id} non trouvée pour annulation")
            raise GNS3ResourceNotFoundError(f"Exécution {execution_id} non trouvée")
        except Exception as e:
            logger.error(f"Erreur lors de l'annulation de l'exécution: {e}")
            raise GNS3Exception(f"Erreur lors de l'annulation de l'exécution: {e}") 