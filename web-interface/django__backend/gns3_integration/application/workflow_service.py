"""Service d'application pour la gestion des workflows GNS3."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from django.db import transaction
from django.contrib.auth.models import User
from gns3_integration.domain.interfaces import GNS3ClientPort, GNS3Repository
from gns3_integration.models import Workflow, WorkflowExecution, Project
from gns3_integration.domain.exceptions import (
    GNS3Exception, GNS3ConnectionError, GNS3ResourceNotFoundError,
    GNS3OperationError, GNS3RepositoryError
)

logger = logging.getLogger(__name__)

class WorkflowService:
    """Service pour la gestion des workflows d'automatisation GNS3."""
    
    def __init__(self, gns3_client: GNS3ClientPort, gns3_repository: GNS3Repository):
        self.client = gns3_client
        self.repository = gns3_repository
    
    def list_workflows(self, is_template: Optional[bool] = None) -> List[Workflow]:
        """Liste tous les workflows disponibles."""
        try:
            queryset = Workflow.objects.all()
            if is_template is not None:
                queryset = queryset.filter(is_template=is_template)
            return queryset.order_by('name')
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des workflows: {e}")
            raise GNS3Exception(f"Erreur lors de la récupération des workflows: {e}")
    
    def get_workflow(self, workflow_id: int) -> Optional[Workflow]:
        """Récupère les détails d'un workflow."""
        try:
            return Workflow.objects.get(id=workflow_id)
        except Workflow.DoesNotExist:
            raise GNS3ResourceNotFoundError(f"Workflow {workflow_id} non trouvé")
    
    @transaction.atomic
    def create_workflow(self, name: str, description: str = "", 
                       steps: List[Dict[str, Any]] = None,
                       is_template: bool = False,
                       template_variables: Dict[str, Any] = None,
                       created_by: Optional[User] = None) -> Workflow:
        """Crée un nouveau workflow."""
        try:
            workflow = Workflow.objects.create(
                name=name,
                description=description,
                steps=steps or [],
                is_template=is_template,
                template_variables=template_variables or {},
                created_by=created_by
            )
            logger.info(f"Workflow '{name}' créé avec succès")
            return workflow
        except Exception as e:
            logger.error(f"Erreur lors de la création du workflow: {e}")
            raise GNS3Exception(f"Erreur lors de la création du workflow: {e}")
    
    @transaction.atomic
    def update_workflow(self, workflow_id: int, **kwargs) -> Workflow:
        """Met à jour un workflow existant."""
        try:
            workflow = Workflow.objects.get(id=workflow_id)
            for field, value in kwargs.items():
                if hasattr(workflow, field):
                    setattr(workflow, field, value)
            workflow.save()
            return workflow
        except Workflow.DoesNotExist:
            raise GNS3ResourceNotFoundError(f"Workflow {workflow_id} non trouvé")
    
    @transaction.atomic
    def delete_workflow(self, workflow_id: int) -> bool:
        """Supprime un workflow."""
        try:
            workflow = Workflow.objects.get(id=workflow_id)
            workflow.delete()
            logger.info(f"Workflow {workflow_id} supprimé")
            return True
        except Workflow.DoesNotExist:
            raise GNS3ResourceNotFoundError(f"Workflow {workflow_id} non trouvé")
    
    @transaction.atomic
    def execute_workflow(self, workflow_id: int, project_id: str, 
                        parameters: Dict[str, Any] = None,
                        created_by: Optional[User] = None) -> WorkflowExecution:
        """Exécute un workflow sur un projet."""
        try:
            workflow = Workflow.objects.get(id=workflow_id)
            project = Project.objects.get(project_id=project_id)
            
            execution = WorkflowExecution.objects.create(
                workflow=workflow,
                project=project,
                status='pending',
                parameters=parameters or {},
                created_by=created_by
            )
            
            # TODO: Démarrer l'exécution asynchrone
            logger.info(f"Exécution de workflow {workflow_id} créée")
            return execution
        except (Workflow.DoesNotExist, Project.DoesNotExist):
            raise GNS3ResourceNotFoundError("Ressource non trouvée")
    
    def list_executions(self, workflow_id: Optional[int] = None, 
                       project_id: Optional[str] = None) -> List[WorkflowExecution]:
        """Liste les exécutions de workflows."""
        try:
            queryset = WorkflowExecution.objects.all()
            if workflow_id:
                queryset = queryset.filter(workflow_id=workflow_id)
            if project_id:
                queryset = queryset.filter(project__project_id=project_id)
            return queryset.order_by('-created_at')
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des exécutions: {e}")
            raise GNS3Exception(f"Erreur lors de la récupération des exécutions: {e}")
    
    def get_execution(self, execution_id: int) -> Optional[WorkflowExecution]:
        """Récupère les détails d'une exécution."""
        try:
            return WorkflowExecution.objects.get(id=execution_id)
        except WorkflowExecution.DoesNotExist:
            raise GNS3ResourceNotFoundError(f"Exécution {execution_id} non trouvée")
    
    @transaction.atomic
    def cancel_execution(self, execution_id: int) -> bool:
        """Annule une exécution de workflow."""
        try:
            execution = WorkflowExecution.objects.get(id=execution_id)
            if execution.status in ['completed', 'failed', 'cancelled']:
                raise GNS3OperationError(f"Impossible d'annuler une exécution {execution.status}")
            
            execution.status = 'cancelled'
            execution.end_time = datetime.now()
            execution.save()
            
            logger.info(f"Exécution {execution_id} annulée")
            return True
        except WorkflowExecution.DoesNotExist:
            raise GNS3ResourceNotFoundError(f"Exécution {execution_id} non trouvée") 