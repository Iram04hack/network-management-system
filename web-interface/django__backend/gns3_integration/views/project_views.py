"""
Vues REST pour les projets GNS3.
"""

import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from django.core.exceptions import ObjectDoesNotExist

logger = logging.getLogger(__name__)

from ..di_container import gns3_container, init_di_container
from ..serializers import ProjectSerializer, ProjectDetailSerializer
from ..domain.exceptions import GNS3ProjectError, GNS3ConnectionError


class ProjectViewSet(viewsets.ViewSet):
    """
    API pour la gestion des projets GNS3.
    """
    
    @property
    def project_service(self):
        """Récupère le service de gestion des projets depuis le conteneur DI."""
        try:
            # Initialiser le conteneur si nécessaire
            if not hasattr(gns3_container, 'project_service'):
                init_di_container()
            return gns3_container.project_service()
        except Exception as e:
            # Fallback : créer un service temporaire sans DI
            from ..application.project_service import ProjectService
            from ..infrastructure.gns3_client_impl import DefaultGNS3Client
            from ..infrastructure.gns3_repository_impl import DjangoGNS3Repository
            
            print(f"Warning: Using fallback for project_service: {e}")
            client = DefaultGNS3Client()
            repository = DjangoGNS3Repository()
            return ProjectService(client, repository)

    @swagger_auto_schema(
        operation_summary="Liste tous les projets GNS3",
        operation_description="Retourne la liste de tous les projets GNS3 enregistrés. Si aucun projet n'est trouvé en base, synchronise automatiquement avec le serveur GNS3.",
        
        tags=['GNS3 Integration'],
        manual_parameters=[
            openapi.Parameter(
                'force_sync',
                openapi.IN_QUERY,
                description="Force la synchronisation avec le serveur GNS3",
                type=openapi.TYPE_BOOLEAN,
                required=False,
                default=False
            )
        ],
        responses={
            200: openapi.Response(
                description="Liste des projets GNS3",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID du projet'),
                        'name': openapi.Schema(type=openapi.TYPE_STRING, description='Nom du projet'),
                        'project_id': openapi.Schema(type=openapi.TYPE_STRING, description='ID GNS3'),
                        'status': openapi.Schema(type=openapi.TYPE_STRING, description='Statut du projet'),
                        'description': openapi.Schema(type=openapi.TYPE_STRING, description='Description'),
                        'nodes_count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Nombre de nœuds'),
                        'links_count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Nombre de liens'),
                        'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', description='Date de création'),
                        'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', description='Date de modification')
                    })
                )
            ),
            500: "Erreur interne du serveur"
        }
    )
    def list(self, request):
        """
        Liste tous les projets GNS3 enregistrés.
        Synchronise automatiquement avec GNS3 si aucun projet n'est trouvé ou si force_sync=true.
        """
        try:
            force_sync = request.query_params.get('force_sync', 'false').lower() == 'true'
            
            if force_sync:
                # Synchronisation forcée : utiliser le service pour synchroniser puis retourner les modèles Django
                self.project_service.sync_all_projects()
            
            # Retourner toujours les modèles Django pour la sérialisation
            from ..models import Project
            projects = Project.objects.all().order_by('-updated_at')
            
            # Si aucun projet et pas de force_sync, essayer une synchronisation automatique
            if not projects.exists() and not force_sync:
                logger.info("🔄 Aucun projet trouvé, synchronisation automatique...")
                self.project_service.sync_all_projects()
                projects = Project.objects.all().order_by('-updated_at')
            
            serializer = ProjectSerializer(projects, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Récupère un projet GNS3 spécifique",
        operation_description="Retourne les détails d'un projet GNS3 spécifique",
        
        tags=['GNS3 Integration'],
        responses={
            200: openapi.Response(
                description="Détails du projet GNS3",
                schema=ProjectDetailSerializer()
            ),
            404: "Projet non trouvé",
            500: "Erreur interne du serveur"
        }
    )
    def retrieve(self, request, pk=None):
        """
        Récupère les détails d'un projet GNS3 spécifique.
        """
        try:
            project = self.project_service.get_project(pk)
            serializer = ProjectDetailSerializer(project)
            return Response(serializer.data)
        except ObjectDoesNotExist:
            return Response(
                {"error": f"Projet avec l'ID {pk} non trouvé"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Crée un nouveau projet GNS3",
        operation_description="Crée un nouveau projet GNS3 avec les informations fournies",
        
        tags=['GNS3 Integration'],request_body=ProjectDetailSerializer,
        responses={
            201: openapi.Response(
                description="Projet GNS3 créé avec succès",
                schema=ProjectDetailSerializer()
            ),
            400: "Données invalides",
            500: "Erreur interne du serveur"
        }
    )
    def create(self, request):
        """
        Crée un nouveau projet GNS3.
        """
        serializer = ProjectDetailSerializer(data=request.data)
        if serializer.is_valid():
            try:
                project = self.project_service.create_project(serializer.validated_data)
                return Response(
                    ProjectDetailSerializer(project).data,
                    status=status.HTTP_201_CREATED
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
        operation_summary="Met à jour un projet GNS3 existant",
        operation_description="Met à jour les informations d'un projet GNS3 existant",
        
        tags=['GNS3 Integration'],request_body=ProjectDetailSerializer,
        responses={
            200: openapi.Response(
                description="Projet GNS3 mis à jour avec succès",
                schema=ProjectDetailSerializer()
            ),
            400: "Données invalides",
            404: "Projet non trouvé",
            500: "Erreur interne du serveur"
        }
    )
    def update(self, request, pk=None):
        """
        Met à jour un projet GNS3 existant.
        """
        try:
            project = self.project_service.get_project(pk)
        except ObjectDoesNotExist:
            return Response(
                {"error": f"Projet avec l'ID {pk} non trouvé"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProjectDetailSerializer(data=request.data)
        if serializer.is_valid():
            try:
                updated_project = self.project_service.update_project(
                    pk, serializer.validated_data
                )
                return Response(ProjectDetailSerializer(updated_project).data)
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
        operation_summary="Supprime un projet GNS3",
        operation_description="Supprime un projet GNS3 existant",
        
        tags=['GNS3 Integration'],
        responses={
            204: "Projet supprimé avec succès",
            404: "Projet non trouvé",
            500: "Erreur interne du serveur"
        }
    )
    def destroy(self, request, pk=None):
        """
        Supprime un projet GNS3 existant.
        """
        try:
            self.project_service.delete_project(pk)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ObjectDoesNotExist:
            return Response(
                {"error": f"Projet avec l'ID {pk} non trouvé"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Ouvre un projet GNS3",
        operation_description="Ouvre un projet GNS3 fermé pour permettre la modification",
        
        tags=['GNS3 Integration'],
        responses={
            200: "Projet ouvert avec succès",
            404: "Projet non trouvé",
            400: "Impossible d'ouvrir le projet",
            500: "Erreur interne du serveur"
        }
    )
    @action(detail=True, methods=['post'])
    def open_project(self, request, pk=None):
        """
        Ouvre un projet GNS3 fermé.
        """
        try:
            result = self.project_service.open_project(pk)
            if result:
                return Response({
                    "status": "success",
                    "message": f"Projet {pk} ouvert avec succès"
                })
            else:
                return Response(
                    {"error": "Impossible d'ouvrir le projet"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except ObjectDoesNotExist:
            return Response(
                {"error": f"Projet avec l'ID {pk} non trouvé"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Ferme un projet GNS3",
        operation_description="Ferme un projet GNS3 ouvert pour libérer les ressources",
        
        tags=['GNS3 Integration'],
        responses={
            200: "Projet fermé avec succès",
            404: "Projet non trouvé",
            400: "Impossible de fermer le projet",
            500: "Erreur interne du serveur"
        }
    )
    @action(detail=True, methods=['post'])
    def close_project(self, request, pk=None):
        """
        Ferme un projet GNS3 ouvert.
        """
        try:
            result = self.project_service.close_project(pk)
            if result:
                return Response({
                    "status": "success",
                    "message": f"Projet {pk} fermé avec succès"
                })
            else:
                return Response(
                    {"error": "Impossible de fermer le projet"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except ObjectDoesNotExist:
            return Response(
                {"error": f"Projet avec l'ID {pk} non trouvé"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Démarre tous les nœuds d'un projet",
        operation_description="Démarre tous les nœuds d'un projet GNS3",
        
        tags=['GNS3 Integration'],
        responses={
            200: "Tous les nœuds démarrés avec succès",
            404: "Projet non trouvé",
            400: "Impossible de démarrer les nœuds",
            500: "Erreur interne du serveur"
        }
    )
    @action(detail=True, methods=['post'])
    def start_all_nodes(self, request, pk=None):
        """
        Démarre tous les nœuds d'un projet GNS3.
        """
        try:
            result = self.project_service.start_all_nodes(pk)
            return Response({
                "status": "success",
                "message": f"Démarrage de tous les nœuds du projet {pk}",
                "started_nodes": result.get('started_nodes', []),
                "failed_nodes": result.get('failed_nodes', [])
            })
        except ObjectDoesNotExist:
            return Response(
                {"error": f"Projet avec l'ID {pk} non trouvé"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Arrête tous les nœuds d'un projet",
        operation_description="Arrête tous les nœuds d'un projet GNS3",
        
        tags=['GNS3 Integration'],
        responses={
            200: "Tous les nœuds arrêtés avec succès",
            404: "Projet non trouvé",
            400: "Impossible d'arrêter les nœuds",
            500: "Erreur interne du serveur"
        }
    )
    @action(detail=True, methods=['post'])
    def stop_all_nodes(self, request, pk=None):
        """
        Arrête tous les nœuds d'un projet GNS3.
        """
        try:
            result = self.project_service.stop_all_nodes(pk)
            return Response({
                "status": "success",
                "message": f"Arrêt de tous les nœuds du projet {pk}",
                "stopped_nodes": result.get('stopped_nodes', []),
                "failed_nodes": result.get('failed_nodes', [])
            })
        except ObjectDoesNotExist:
            return Response(
                {"error": f"Projet avec l'ID {pk} non trouvé"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Duplique un projet GNS3",
        operation_description="Crée une copie d'un projet GNS3 existant",
        
        tags=['GNS3 Integration'],request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Nom du nouveau projet'),
                'reset_mac_addresses': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Réinitialiser les adresses MAC')
            },
            required=['name']
        ),
        responses={
            201: openapi.Response(
                description="Projet dupliqué avec succès",
                schema=ProjectDetailSerializer()
            ),
            400: "Données invalides",
            404: "Projet non trouvé",
            500: "Erreur interne du serveur"
        }
    )
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """
        Duplique un projet GNS3 existant.
        """
        try:
            new_name = request.data.get('name')
            reset_mac_addresses = request.data.get('reset_mac_addresses', True)
            
            if not new_name:
                return Response(
                    {"error": "Le paramètre 'name' est requis"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            duplicated_project = self.project_service.duplicate_project(
                pk, new_name, reset_mac_addresses
            )
            return Response(
                ProjectDetailSerializer(duplicated_project).data,
                status=status.HTTP_201_CREATED
            )
        except ObjectDoesNotExist:
            return Response(
                {"error": f"Projet avec l'ID {pk} non trouvé"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Exporte un projet GNS3",
        operation_description="Exporte un projet GNS3 vers un fichier archive",
        
        tags=['GNS3 Integration'],
        responses={
            200: "Projet exporté avec succès",
            404: "Projet non trouvé",
            500: "Erreur interne du serveur"
        }
    )
    @action(detail=True, methods=['post'])
    def export_project(self, request, pk=None):
        """
        Exporte un projet GNS3 vers un fichier archive.
        """
        try:
            export_result = self.project_service.export_project(pk)
            return Response({
                "status": "success",
                "message": f"Projet {pk} exporté avec succès",
                "export_path": export_result.get('export_path'),
                "file_size": export_result.get('file_size')
            })
        except ObjectDoesNotExist:
            return Response(
                {"error": f"Projet avec l'ID {pk} non trouvé"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Récupère les statistiques d'un projet",
        operation_description="Retourne les statistiques détaillées d'un projet GNS3",
        
        tags=['GNS3 Integration'],
        responses={
            200: "Statistiques récupérées avec succès",
            404: "Projet non trouvé",
            500: "Erreur interne du serveur"
        }
    )
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """
        Récupère les statistiques d'un projet GNS3.
        """
        try:
            stats = self.project_service.get_project_statistics(pk)
            return Response(stats)
        except ObjectDoesNotExist:
            return Response(
                {"error": f"Projet avec l'ID {pk} non trouvé"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Synchronise tous les projets avec le serveur GNS3",
        operation_description="Force la synchronisation de tous les projets depuis le serveur GNS3 vers la base de données Django",
        
        tags=['GNS3 Integration'],
        responses={
            200: openapi.Response(
                description="Synchronisation réussie",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'synchronized_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'projects': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID du projet'),
                            'name': openapi.Schema(type=openapi.TYPE_STRING, description='Nom du projet'),
                            'project_id': openapi.Schema(type=openapi.TYPE_STRING, description='ID GNS3'),
                            'status': openapi.Schema(type=openapi.TYPE_STRING, description='Statut du projet'),
                            'description': openapi.Schema(type=openapi.TYPE_STRING, description='Description'),
                            'nodes_count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Nombre de nœuds'),
                            'links_count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Nombre de liens'),
                            'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', description='Date de création'),
                            'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', description='Date de modification')
                        }))
                    }
                )
            ),
            500: "Erreur interne du serveur"
        }
    )
    @action(detail=False, methods=['post'])
    def sync_all(self, request):
        """
        Synchronise tous les projets GNS3 depuis le serveur vers la base de données Django.
        """
        try:
            projects = self.project_service.sync_all_projects()
            serializer = ProjectSerializer(projects, many=True)
            return Response({
                "status": "success",
                "message": f"Synchronisation réussie: {len(projects)} projets synchronisés",
                "synchronized_count": len(projects),
                "projects": serializer.data
            })
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )