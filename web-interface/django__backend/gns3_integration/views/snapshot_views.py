"""
Vues REST pour les snapshots GNS3.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from django.core.exceptions import ObjectDoesNotExist

from ..di_container import gns3_container
from ..serializers import SnapshotSerializer
from ..domain.exceptions import GNS3Exception, GNS3ConnectionError


class SnapshotViewSet(viewsets.ViewSet):
    """
    API pour la gestion des snapshots GNS3.
    """
    
    @property
    def snapshot_service(self):
        """Récupère le service de gestion des snapshots depuis le conteneur DI."""
        try:
            return gns3_container.snapshot_service()
        except Exception:
            # Fallback en cas d'échec du conteneur DI
            from ..application.snapshot_service import SnapshotService
            from ..infrastructure.gns3_client_impl import GNS3ClientImpl
            from ..infrastructure.gns3_repository_impl import GNS3RepositoryImpl
            return SnapshotService(GNS3ClientImpl(), GNS3RepositoryImpl())

    @swagger_auto_schema(
        operation_summary="Liste tous les snapshots d'un projet GNS3",
        operation_description="Retourne la liste de tous les snapshots d'un projet GNS3 spécifique",
        
        tags=['GNS3 Integration'],manual_parameters=[
            openapi.Parameter(
                'project_id',
                openapi.IN_QUERY,
                description="ID du projet GNS3",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Liste des snapshots GNS3",
                schema=SnapshotSerializer
            ),
            400: "ID du projet non fourni",
            404: "Projet non trouvé",
            500: "Erreur interne du serveur"
        }
    )
    def list(self, request):
        """
        Liste tous les snapshots d'un projet GNS3 spécifique.
        """
        project_id = request.query_params.get('project_id')
        if not project_id:
            return Response(
                {"error": "Le paramètre 'project_id' est requis"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            snapshots = self.snapshot_service.list_snapshots(project_id)
            serializer = SnapshotSerializer(snapshots, many=True)
            return Response(serializer.data)
        except ObjectDoesNotExist:
            return Response(
                {"error": f"Projet avec l'ID {project_id} non trouvé"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Récupère un snapshot GNS3 spécifique",
        operation_description="Retourne les détails d'un snapshot GNS3 spécifique",
        
        tags=['GNS3 Integration'],manual_parameters=[
            openapi.Parameter(
                'project_id',
                openapi.IN_QUERY,
                description="ID du projet GNS3",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Détails du snapshot GNS3",
                schema=SnapshotSerializer()
            ),
            400: "ID du projet non fourni",
            404: "Snapshot ou projet non trouvé",
            500: "Erreur interne du serveur"
        }
    )
    def retrieve(self, request, pk=None):
        """
        Récupère les détails d'un snapshot GNS3 spécifique.
        """
        project_id = request.query_params.get('project_id')
        if not project_id:
            return Response(
                {"error": "Le paramètre 'project_id' est requis"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            snapshot = self.snapshot_service.get_snapshot(project_id, pk)
            serializer = SnapshotSerializer(snapshot)
            return Response(serializer.data)
        except ObjectDoesNotExist as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Crée un nouveau snapshot GNS3",
        operation_description="Crée un nouveau snapshot d'un projet GNS3 spécifique",
        
        tags=['GNS3 Integration'],request_body=SnapshotSerializer,
        manual_parameters=[
            openapi.Parameter(
                'project_id',
                openapi.IN_QUERY,
                description="ID du projet GNS3",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            201: openapi.Response(
                description="Snapshot GNS3 créé avec succès",
                schema=SnapshotSerializer()
            ),
            400: "Données invalides ou ID du projet non fourni",
            404: "Projet non trouvé",
            500: "Erreur interne du serveur"
        }
    )
    def create(self, request):
        """
        Crée un nouveau snapshot d'un projet GNS3 spécifique.
        """
        project_id = request.query_params.get('project_id')
        if not project_id:
            return Response(
                {"error": "Le paramètre 'project_id' est requis"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        serializer = SnapshotSerializer(data=request.data)
        if serializer.is_valid():
            try:
                snapshot = self.snapshot_service.create_snapshot(
                    project_id, 
                    serializer.validated_data.get('name'),
                    serializer.validated_data.get('description', ''),
                    request.user if request.user.is_authenticated else None
                )
                return Response(
                    SnapshotSerializer(snapshot).data,
                    status=status.HTTP_201_CREATED
                )
            except ObjectDoesNotExist:
                return Response(
                    {"error": f"Projet avec l'ID {project_id} non trouvé"},
                    status=status.HTTP_404_NOT_FOUND
                )
            except GNS3ConnectionError as e:
                return Response(
                    {"error": f"Impossible de se connecter au serveur GNS3: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Supprime un snapshot GNS3",
        operation_description="Supprime un snapshot GNS3 existant",
        
        tags=['GNS3 Integration'],manual_parameters=[
            openapi.Parameter(
                'project_id',
                openapi.IN_QUERY,
                description="ID du projet GNS3",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            204: "Snapshot supprimé avec succès",
            400: "ID du projet non fourni",
            404: "Snapshot ou projet non trouvé",
            500: "Erreur interne du serveur"
        }
    )
    def destroy(self, request, pk=None):
        """
        Supprime un snapshot GNS3 existant.
        """
        project_id = request.query_params.get('project_id')
        if not project_id:
            return Response(
                {"error": "Le paramètre 'project_id' est requis"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            self.snapshot_service.delete_snapshot(project_id, pk)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ObjectDoesNotExist as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Restaure un snapshot GNS3",
        operation_description="Restaure un projet à partir d'un snapshot spécifique",
        
        tags=['GNS3 Integration'],manual_parameters=[
            openapi.Parameter(
                'project_id',
                openapi.IN_QUERY,
                description="ID du projet GNS3",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: "Snapshot restauré avec succès",
            400: "ID du projet non fourni",
            404: "Snapshot ou projet non trouvé",
            500: "Erreur interne du serveur"
        }
    )
    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """
        Restaure un projet à partir d'un snapshot spécifique.
        """
        project_id = request.query_params.get('project_id')
        if not project_id:
            return Response(
                {"error": "Le paramètre 'project_id' est requis"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            result = self.snapshot_service.restore_snapshot(project_id, pk)
            return Response({
                "status": "success", 
                "message": f"Snapshot {pk} restauré avec succès",
                "project_id": project_id
            })
        except ObjectDoesNotExist as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 