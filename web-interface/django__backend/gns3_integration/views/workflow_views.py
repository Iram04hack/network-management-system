"""
Vues REST pour les workflows GNS3.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from django.core.exceptions import ObjectDoesNotExist

from ..di_container import gns3_container
from ..serializers import WorkflowSerializer, WorkflowExecutionSerializer
from ..domain.exceptions import GNS3Exception, GNS3ConnectionError


class WorkflowViewSet(viewsets.ViewSet):
    """
    API pour la gestion des workflows GNS3.
    """
    
    @property
    def workflow_service(self):
        """Récupère le service de gestion des workflows depuis le conteneur DI."""
        try:
            return gns3_container.workflow_service()
        except Exception:
            # Fallback en cas d'échec du conteneur DI
            from ..application.workflow_service import WorkflowService
            from ..infrastructure.gns3_client_impl import GNS3ClientImpl
            from ..infrastructure.gns3_repository_impl import GNS3RepositoryImpl
            return WorkflowService(GNS3ClientImpl(), GNS3RepositoryImpl())

    @swagger_auto_schema(
        operation_summary="Liste tous les workflows GNS3",
        operation_description="Retourne la liste de tous les workflows GNS3 disponibles",
        
        tags=['GNS3 Integration'],responses={
            200: openapi.Response(
                description="Liste des workflows GNS3",
                schema=WorkflowSerializer
            ),
            500: "Erreur interne du serveur"
        }
    )
    def list(self, request):
        """
        Liste tous les workflows GNS3 disponibles.
        """
        try:
            workflows = self.workflow_service.list_workflows()
            serializer = WorkflowSerializer(workflows, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Crée un nouveau workflow GNS3",
        operation_description="Crée un nouveau workflow GNS3 avec les étapes définies",
        
        tags=['GNS3 Integration'],request_body=WorkflowSerializer,
        responses={
            201: openapi.Response(
                description="Workflow GNS3 créé avec succès",
                schema=WorkflowSerializer()
            ),
            400: "Données invalides",
            500: "Erreur interne du serveur"
        }
    )
    def create(self, request):
        """
        Crée un nouveau workflow GNS3.
        """
        serializer = WorkflowSerializer(data=request.data)
        if serializer.is_valid():
            try:
                workflow = self.workflow_service.create_workflow(
                    serializer.validated_data.get('name'),
                    serializer.validated_data.get('description', ''),
                    serializer.validated_data.get('steps', []),
                    serializer.validated_data.get('is_template', False),
                    serializer.validated_data.get('template_variables', {}),
                    request.user if request.user.is_authenticated else None
                )
                return Response(
                    WorkflowSerializer(workflow).data,
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WorkflowExecutionViewSet(viewsets.ViewSet):
    """
    API pour la gestion des exécutions de workflows GNS3.
    """
    
    @property
    def workflow_service(self):
        """Récupère le service de gestion des workflows depuis le conteneur DI."""
        try:
            return gns3_container.workflow_service()
        except Exception:
            # Fallback en cas d'échec du conteneur DI
            from ..application.workflow_service import WorkflowService
            from ..infrastructure.gns3_client_impl import GNS3ClientImpl
            from ..infrastructure.gns3_repository_impl import GNS3RepositoryImpl
            return WorkflowService(GNS3ClientImpl(), GNS3RepositoryImpl())

    @swagger_auto_schema(
        operation_summary="Liste toutes les exécutions de workflows",
        operation_description="Retourne l'historique de toutes les exécutions de workflows",
        
        tags=['GNS3 Integration'],responses={
            200: openapi.Response(
                description="Liste des exécutions de workflows",
                schema=WorkflowExecutionSerializer
            ),
            500: "Erreur interne du serveur"
        }
    )
    def list(self, request):
        """
        Liste toutes les exécutions de workflows.
        """
        try:
            executions = self.workflow_service.list_executions()
            serializer = WorkflowExecutionSerializer(executions, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
