"""
ViewSets REST pour la gestion de projets GNS3 multiples avec basculement automatique.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from ..di_container import gns3_container, init_di_container
from ..domain.exceptions import GNS3ProjectError, GNS3ConnectionError, GNS3ResourceNotFoundError
from ..application.multi_project_service import MultiProjectService, ProjectSelection

import logging

logger = logging.getLogger(__name__)


class MultiProjectViewSet(viewsets.ViewSet):
    """
    API pour la gestion de projets GNS3 multiples avec basculement automatique.
    
    Cette API permet de :
    - Sélectionner plusieurs projets GNS3 pour surveillance
    - Gérer le basculement automatique entre projets
    - Surveiller le trafic réseau et démarrer automatiquement le travail
    - Configurer les priorités et options de chaque projet
    """
    
    @property
    def multi_project_service(self) -> MultiProjectService:
        """Récupère le service de gestion multi-projets depuis le conteneur DI."""
        try:
            # Initialiser le conteneur si nécessaire
            if not hasattr(gns3_container, 'multi_project_service'):
                init_di_container()
            return gns3_container.multi_project_service()
        except Exception as e:
            # Fallback : créer un service temporaire sans DI
            from ..application.project_service import ProjectService
            from ..infrastructure.gns3_client_impl import DefaultGNS3Client
            from ..infrastructure.gns3_repository_impl import DjangoGNS3Repository
            
            logger.warning(f"Using fallback for multi_project_service: {e}")
            client = DefaultGNS3Client()
            repository = DjangoGNS3Repository()
            project_service = ProjectService(client, repository)
            return MultiProjectService(project_service, client, repository)

    @swagger_auto_schema(
        operation_summary="Liste les projets sélectionnés",
        operation_description="Retourne la liste de tous les projets GNS3 sélectionnés pour la surveillance automatique",
        
        tags=['GNS3 Multi-Project Management'],
        responses={
            200: openapi.Response(
                description="Liste des projets sélectionnés avec leurs statuts",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'selected_projects': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'project_id': openapi.Schema(type=openapi.TYPE_STRING),
                                    'project_name': openapi.Schema(type=openapi.TYPE_STRING),
                                    'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'priority': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'auto_start_on_traffic': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'traffic_detected': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'selected_at': openapi.Schema(type=openapi.TYPE_STRING, format='datetime'),
                                    'last_traffic': openapi.Schema(type=openapi.TYPE_STRING, format='datetime'),
                                    'metadata': openapi.Schema(type=openapi.TYPE_OBJECT)
                                }
                            )
                        ),
                        'total_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'active_project_id': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            500: "Erreur interne du serveur"
        }
    )
    def list(self, request):
        """
        Liste tous les projets GNS3 sélectionnés pour la surveillance.
        """
        try:
            selected_projects = self.multi_project_service.get_selected_projects()
            active_project = self.multi_project_service.get_active_project()
            
            projects_data = []
            for selection in selected_projects:
                projects_data.append({
                    'project_id': selection.project_id,
                    'project_name': selection.project_name,
                    'is_active': selection.is_active,
                    'priority': selection.priority,
                    'auto_start_on_traffic': selection.auto_start_on_traffic,
                    'traffic_detected': selection.traffic_detected,
                    'selected_at': selection.selected_at.isoformat(),
                    'last_traffic': selection.last_traffic.isoformat() if selection.last_traffic else None,
                    'metadata': selection.metadata
                })
            
            return Response({
                'selected_projects': projects_data,
                'total_count': len(projects_data),
                'active_project_id': active_project.project_id if active_project else None
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des projets sélectionnés: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Ajoute un projet à la sélection",
        operation_description="Ajoute un projet GNS3 à la liste des projets surveillés avec ses configurations",
        
        tags=['GNS3 Multi-Project Management'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['project_id'],
            properties={
                'project_id': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description='ID du projet GNS3 à ajouter'
                ),
                'priority': openapi.Schema(
                    type=openapi.TYPE_INTEGER, 
                    description='Priorité du projet (1 = haute, 5 = basse)',
                    default=1,
                    minimum=1,
                    maximum=5
                ),
                'auto_start_on_traffic': openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, 
                    description='Démarrer automatiquement le projet quand du trafic est détecté',
                    default=True
                ),
                'metadata': openapi.Schema(
                    type=openapi.TYPE_OBJECT, 
                    description='Métadonnées supplémentaires pour le projet'
                )
            }
        ),
        responses={
            201: openapi.Response(
                description="Projet ajouté à la sélection avec succès",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'project_selection': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'project_id': openapi.Schema(type=openapi.TYPE_STRING),
                                'project_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'priority': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'auto_start_on_traffic': openapi.Schema(type=openapi.TYPE_BOOLEAN)
                            }
                        )
                    }
                )
            ),
            400: "Données invalides",
            404: "Projet non trouvé",
            500: "Erreur interne du serveur"
        }
    )
    @action(detail=False, methods=['post'])
    def add_project(self, request):
        """
        Ajoute un projet à la sélection pour surveillance automatique.
        """
        try:
            project_id = request.data.get('project_id')
            priority = request.data.get('priority', 1)
            auto_start_on_traffic = request.data.get('auto_start_on_traffic', True)
            metadata = request.data.get('metadata', {})
            
            if not project_id:
                return Response(
                    {"error": "Le paramètre 'project_id' est requis"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Valider la priorité
            if not (1 <= priority <= 5):
                return Response(
                    {"error": "La priorité doit être entre 1 (haute) et 5 (basse)"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            selection = self.multi_project_service.add_project_selection(
                project_id=project_id,
                priority=priority,
                auto_start_on_traffic=auto_start_on_traffic,
                metadata=metadata
            )
            
            return Response({
                'status': 'success',
                'message': f'Projet {project_id} ajouté à la sélection avec succès',
                'project_selection': {
                    'project_id': selection.project_id,
                    'project_name': selection.project_name,
                    'priority': selection.priority,
                    'auto_start_on_traffic': selection.auto_start_on_traffic,
                    'selected_at': selection.selected_at.isoformat(),
                    'metadata': selection.metadata
                }
            }, status=status.HTTP_201_CREATED)
            
        except GNS3ResourceNotFoundError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout du projet à la sélection: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Retire un projet de la sélection",
        operation_description="Retire un projet GNS3 de la liste des projets surveillés",
        
        tags=['GNS3 Multi-Project Management'],
        manual_parameters=[
            openapi.Parameter(
                'project_id',
                openapi.IN_PATH,
                description="ID du projet à retirer",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Projet retiré de la sélection avec succès",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING),
                        'message': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            404: "Projet non trouvé dans la sélection",
            500: "Erreur interne du serveur"
        }
    )
    @action(detail=True, methods=['delete'])
    def remove_project(self, request, pk=None):
        """
        Retire un projet de la sélection.
        """
        try:
            success = self.multi_project_service.remove_project_selection(pk)
            
            if success:
                return Response({
                    'status': 'success',
                    'message': f'Projet {pk} retiré de la sélection avec succès'
                })
            else:
                return Response(
                    {"error": f"Projet {pk} non trouvé dans la sélection"},
                    status=status.HTTP_404_NOT_FOUND
                )
                
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du projet {pk} de la sélection: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Définit le projet actif",
        operation_description="Active un projet spécifique ou désactive tous les projets",
        
        tags=['GNS3 Multi-Project Management'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'project_id': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description='ID du projet à activer (null pour désactiver tous)'
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Projet actif défini avec succès",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'active_project_id': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: "Données invalides",
            404: "Projet non trouvé",
            500: "Erreur interne du serveur"
        }
    )
    @action(detail=False, methods=['post'])
    def set_active(self, request):
        """
        Définit le projet actif pour la surveillance.
        """
        try:
            project_id = request.data.get('project_id')
            
            success = self.multi_project_service.set_active_project(project_id)
            
            if success:
                if project_id:
                    message = f'Projet {project_id} défini comme actif'
                else:
                    message = 'Aucun projet actif'
                
                return Response({
                    'status': 'success',
                    'message': message,
                    'active_project_id': project_id
                })
            else:
                return Response(
                    {"error": "Impossible de définir le projet actif"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except GNS3ResourceNotFoundError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Erreur lors de la définition du projet actif: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Bascule vers le projet suivant",
        operation_description="Bascule automatiquement vers le projet suivant selon la priorité",
        
        tags=['GNS3 Multi-Project Management'],
        responses={
            200: openapi.Response(
                description="Basculement effectué avec succès",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'previous_project_id': openapi.Schema(type=openapi.TYPE_STRING),
                        'current_project_id': openapi.Schema(type=openapi.TYPE_STRING),
                        'current_project_name': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            404: "Aucun projet sélectionné",
            500: "Erreur interne du serveur"
        }
    )
    @action(detail=False, methods=['post'])
    def switch_next(self, request):
        """
        Bascule vers le projet suivant selon la priorité.
        """
        try:
            current_active = self.multi_project_service.get_active_project()
            previous_project_id = current_active.project_id if current_active else None
            
            next_project = self.multi_project_service.switch_to_next_priority_project()
            
            if next_project:
                return Response({
                    'status': 'success',
                    'message': f'Basculement vers le projet {next_project.project_name}',
                    'previous_project_id': previous_project_id,
                    'current_project_id': next_project.project_id,
                    'current_project_name': next_project.project_name
                })
            else:
                return Response(
                    {"error": "Aucun projet disponible pour basculement"},
                    status=status.HTTP_404_NOT_FOUND
                )
                
        except Exception as e:
            logger.error(f"Erreur lors du basculement de projet: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Détecte le trafic sur un projet",
        operation_description="Détecte manuellement le trafic réseau sur un projet spécifique",
        
        tags=['GNS3 Multi-Project Management'],
        manual_parameters=[
            openapi.Parameter(
                'project_id',
                openapi.IN_PATH,
                description="ID du projet à analyser",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Statut de trafic détecté",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'project_id': openapi.Schema(type=openapi.TYPE_STRING),
                        'has_traffic': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'traffic_level': openapi.Schema(type=openapi.TYPE_STRING),
                        'detected_at': openapi.Schema(type=openapi.TYPE_STRING, format='datetime'),
                        'interface_stats': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            ),
            404: "Projet non trouvé",
            500: "Erreur interne du serveur"
        }
    )
    @action(detail=True, methods=['get'])
    def detect_traffic(self, request, pk=None):
        """
        Détecte le trafic réseau sur un projet spécifique.
        """
        try:
            traffic_status = self.multi_project_service.detect_traffic_on_project(pk)
            
            return Response({
                'project_id': traffic_status.project_id,
                'has_traffic': traffic_status.has_traffic,
                'traffic_level': traffic_status.traffic_level,
                'detected_at': traffic_status.detected_at.isoformat(),
                'interface_stats': traffic_status.interface_stats
            })
            
        except GNS3ResourceNotFoundError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Erreur lors de la détection de trafic pour le projet {pk}: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Démarre la surveillance automatique",
        operation_description="Active la surveillance automatique de tous les projets sélectionnés",
        
        tags=['GNS3 Multi-Project Management'],
        responses={
            200: openapi.Response(
                description="Surveillance automatique démarrée",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'monitoring_enabled': openapi.Schema(type=openapi.TYPE_BOOLEAN)
                    }
                )
            ),
            500: "Erreur interne du serveur"
        }
    )
    @action(detail=False, methods=['post'])
    def start_monitoring(self, request):
        """
        Démarre la surveillance automatique des projets sélectionnés.
        """
        try:
            success = self.multi_project_service.start_automatic_monitoring()
            
            if success:
                return Response({
                    'status': 'success',
                    'message': 'Surveillance automatique démarrée avec succès',
                    'monitoring_enabled': True
                })
            else:
                return Response(
                    {"error": "Impossible de démarrer la surveillance automatique"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            logger.error(f"Erreur lors du démarrage de la surveillance: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Arrête la surveillance automatique",
        operation_description="Désactive la surveillance automatique de tous les projets",
        
        tags=['GNS3 Multi-Project Management'],
        responses={
            200: openapi.Response(
                description="Surveillance automatique arrêtée",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'monitoring_enabled': openapi.Schema(type=openapi.TYPE_BOOLEAN)
                    }
                )
            ),
            500: "Erreur interne du serveur"
        }
    )
    @action(detail=False, methods=['post'])
    def stop_monitoring(self, request):
        """
        Arrête la surveillance automatique des projets.
        """
        try:
            success = self.multi_project_service.stop_automatic_monitoring()
            
            if success:
                return Response({
                    'status': 'success',
                    'message': 'Surveillance automatique arrêtée avec succès',
                    'monitoring_enabled': False
                })
            else:
                return Response(
                    {"error": "Impossible d'arrêter la surveillance automatique"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            logger.error(f"Erreur lors de l'arrêt de la surveillance: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Résumé du statut de trafic",
        operation_description="Retourne un résumé complet du statut de trafic pour tous les projets sélectionnés",
        
        tags=['GNS3 Multi-Project Management'],
        responses={
            200: openapi.Response(
                description="Résumé du statut de trafic",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'total_projects': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'active_project': openapi.Schema(type=openapi.TYPE_STRING),
                        'projects_with_traffic': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'monitoring_enabled': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'last_check': openapi.Schema(type=openapi.TYPE_STRING, format='datetime'),
                        'projects': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'project_id': openapi.Schema(type=openapi.TYPE_STRING),
                                    'project_name': openapi.Schema(type=openapi.TYPE_STRING),
                                    'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'priority': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'traffic_detected': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'traffic_status': openapi.Schema(type=openapi.TYPE_OBJECT)
                                }
                            )
                        )
                    }
                )
            ),
            500: "Erreur interne du serveur"
        }
    )
    @action(detail=False, methods=['get'])
    def traffic_status(self, request):
        """
        Récupère un résumé du statut de trafic pour tous les projets sélectionnés.
        """
        try:
            summary = self.multi_project_service.get_traffic_status_summary()
            return Response(summary)
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du résumé de trafic: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )