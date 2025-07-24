"""
Vues API pour la gestion des tableaux de bord.
"""

from typing import List, Dict, Any

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..domain.interfaces.repositories import (
    DashboardRepository,
    DashboardShareRepository
)
from ..use_cases.dashboard_use_cases import DashboardUseCase
from ..di_container import resolve
from ..serializers.dashboard_serializers import (
    DashboardSerializer,
    DashboardWidgetSerializer,
    DashboardShareSerializer
)


class DashboardViewSet(viewsets.ViewSet):
    """Vue API pour la gestion des tableaux de bord."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Résoudre l'instance du repository et créer le use case
        self.repository = resolve("dashboard_repository")()
        self.use_case = DashboardUseCase(self.repository)
    
    @swagger_auto_schema(
        operation_summary="Liste des tableaux de bord",
        operation_description="Récupère la liste des tableaux de bord accessibles par l'utilisateur connecté.",
        tags=['Monitoring'],
        manual_parameters=[
            openapi.Parameter('include_public', openapi.IN_QUERY, description="Inclure les tableaux de bord publics", type=openapi.TYPE_BOOLEAN, default=True),
        ],
        responses={
            200: openapi.Response(
                description='Liste des dashboards',
                schema=DashboardSerializer
            ),
            401: "Non authentifié"
        }
    )
    def list(self, request: Request) -> Response:
        """Liste les tableaux de bord accessibles par l'utilisateur."""
        user_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None
        include_public = request.query_params.get('include_public', 'true').lower() == 'true'
        
        dashboards = self.use_case.list_dashboards(user_id, include_public)
        serializer = DashboardSerializer(dashboards, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_summary="Détails d'un tableau de bord",
        operation_description="Récupère les détails d'un tableau de bord par son ID ou son UID.",
        tags=['Monitoring'],
        responses={
            200: openapi.Response(
                description='Détails du dashboard',
                schema=DashboardSerializer()
            ),
            404: "Tableau de bord non trouvé",
            401: "Non authentifié"
        }
    )
    def retrieve(self, request: Request, pk=None) -> Response:
        """Récupère un tableau de bord par son ID ou son UID."""
        try:
            # Vérifier si pk est un entier (ID) ou une chaîne (UID)
            try:
                dashboard_id = int(pk)
                dashboard = self.use_case.get_dashboard(dashboard_id=dashboard_id)
            except ValueError:
                # Si pk n'est pas un entier, c'est probablement un UID
                dashboard = self.use_case.get_dashboard(uid=pk)
            
            serializer = DashboardSerializer(dashboard)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    
    @swagger_auto_schema(
        operation_summary="Créer un tableau de bord",
        operation_description="Crée un nouveau tableau de bord pour l'utilisateur connecté.",
        tags=['Monitoring'],
        request_body=DashboardSerializer,
        responses={
            201: openapi.Response(
                description='Dashboard créé',
                schema=DashboardSerializer()
            ),
            400: "Données invalides",
            401: "Non authentifié"
        }
    )
    def create(self, request: Request) -> Response:
        """Crée un nouveau tableau de bord."""
        # Valider les données d'entrée
        serializer = DashboardSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Créer le tableau de bord
        try:
            owner_id = serializer.validated_data.get('owner_id')
            if not owner_id and hasattr(request, 'user') and request.user.is_authenticated:
                owner_id = request.user.id
            
            if not owner_id:
                return Response({"error": "Owner ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            dashboard = self.use_case.create_dashboard(
                title=serializer.validated_data['title'],
                owner_id=owner_id,
                description=serializer.validated_data.get('description'),
                is_public=serializer.validated_data.get('is_public', False),
                is_default=serializer.validated_data.get('is_default', False),
                layout_config=serializer.validated_data.get('layout_config')
            )
            
            response_serializer = DashboardSerializer(dashboard)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_summary="Modifier un tableau de bord",
        operation_description="Met à jour complètement un tableau de bord existant.",
        tags=['Monitoring'],
        request_body=DashboardSerializer,
        responses={
            200: openapi.Response(
                description='Dashboard mis à jour',
                schema=DashboardSerializer()
            ),
            400: "Données invalides",
            404: "Tableau de bord non trouvé",
            403: "Non autorisé",
            401: "Non authentifié"
        }
    )
    def update(self, request: Request, pk=None) -> Response:
        """Met à jour un tableau de bord."""
        # Valider les données d'entrée
        serializer = DashboardSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Mettre à jour le tableau de bord
        try:
            dashboard = self.use_case.update_dashboard(
                dashboard_id=int(pk),
                **serializer.validated_data
            )
            
            response_serializer = DashboardSerializer(dashboard)
            return Response(response_serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_summary="Supprimer un tableau de bord",
        operation_description="Supprime un tableau de bord (seul le propriétaire ou un administrateur peut le faire).",
        tags=['Monitoring'],
        responses={
            204: "Tableau de bord supprimé avec succès",
            404: "Tableau de bord non trouvé",
            403: "Non autorisé",
            401: "Non authentifié"
        }
    )
    def destroy(self, request: Request, pk=None) -> Response:
        """Supprime un tableau de bord."""
        try:
            # Vérifier que l'utilisateur est autorisé à supprimer le tableau de bord
            dashboard = self.use_case.get_dashboard(dashboard_id=int(pk))
            
            if hasattr(request, 'user') and request.user.is_authenticated:
                if dashboard.owner_id != request.user.id and not request.user.is_staff:
                    return Response({"error": "You are not authorized to delete this dashboard"}, status=status.HTTP_403_FORBIDDEN)
            
            result = self.use_case.delete_dashboard(int(pk))
            if result:
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({"error": "Failed to delete dashboard"}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_summary="Tableau de bord par défaut",
        operation_description="Récupère le tableau de bord par défaut de l'utilisateur connecté.",
        tags=['Monitoring'],
        responses={
            200: openapi.Response(
                description='Dashboard par défaut',
                schema=DashboardSerializer()
            ),
            404: "Aucun tableau de bord par défaut trouvé",
            401: "Authentification requise"
        }
    )
    @action(detail=False, methods=['get'])
    def default(self, request: Request) -> Response:
        """Récupère le tableau de bord par défaut de l'utilisateur."""
        user_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None
        
        if not user_id:
            return Response({"error": "User authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        
        dashboard = self.use_case.get_default_dashboard(user_id)
        if dashboard is None:
            return Response({"message": "No default dashboard found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = DashboardSerializer(dashboard)
        return Response(serializer.data)


class DashboardWidgetViewSet(viewsets.ViewSet):
    """Vue API pour la gestion des widgets de tableau de bord."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.repository = resolve("dashboard_repository")
        self.use_case = DashboardUseCase(self.repository)
    
    @swagger_auto_schema(
        operation_summary="Ajouter un widget",
        operation_description="Ajoute un nouveau widget à un tableau de bord.",
        tags=['Monitoring'],
        request_body=DashboardWidgetSerializer,
        responses={
            201: openapi.Response(
                description='Widget ajouté',
                schema=DashboardWidgetSerializer()
            ),
            400: "Données invalides",
            404: "Tableau de bord non trouvé",
            401: "Non authentifié"
        }
    )
    def create(self, request: Request) -> Response:
        """Ajoute un widget à un tableau de bord."""
        # Valider les données d'entrée
        serializer = DashboardWidgetSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Ajouter le widget
        try:
            widget = self.use_case.add_widget(
                dashboard_id=serializer.validated_data['dashboard_id'],
                title=serializer.validated_data['title'],
                widget_type=serializer.validated_data['widget_type'],
                position=serializer.validated_data['position'],
                size=serializer.validated_data['size'],
                data_source=serializer.validated_data.get('data_source'),
                config=serializer.validated_data.get('config')
            )
            
            response_serializer = DashboardWidgetSerializer(widget)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_summary="Modifier un widget",
        operation_description="Met à jour complètement un widget de tableau de bord.",
        tags=['Monitoring'],
        request_body=DashboardWidgetSerializer,
        responses={
            200: openapi.Response(
                description='Widget mis à jour',
                schema=DashboardWidgetSerializer()
            ),
            400: "Données invalides",
            404: "Widget non trouvé",
            401: "Non authentifié"
        }
    )
    def update(self, request: Request, pk=None) -> Response:
        """Met à jour un widget."""
        # Valider les données d'entrée
        serializer = DashboardWidgetSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Mettre à jour le widget
        try:
            widget = self.use_case.update_widget(
                widget_id=int(pk),
                **serializer.validated_data
            )
            
            response_serializer = DashboardWidgetSerializer(widget)
            return Response(response_serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_summary="Supprimer un widget",
        operation_description="Supprime un widget d'un tableau de bord.",
        tags=['Monitoring'],
        responses={
            204: "Widget supprimé avec succès",
            404: "Widget non trouvé",
            401: "Non authentifié"
        }
    )
    def destroy(self, request: Request, pk=None) -> Response:
        """Supprime un widget."""
        try:
            result = self.use_case.remove_widget(int(pk))
            if result:
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({"error": "Failed to remove widget"}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DashboardShareViewSet(viewsets.ViewSet):
    """Vue API pour la gestion des partages de tableau de bord."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.repository = resolve("dashboard_repository")
    
    @swagger_auto_schema(
        operation_summary="Liste des partages",
        operation_description="Récupère la liste des partages pour un tableau de bord donné.",
        tags=['Monitoring'],
        manual_parameters=[
            openapi.Parameter('dashboard_id', openapi.IN_QUERY, description="ID du tableau de bord", type=openapi.TYPE_INTEGER, required=True),
        ],
        responses={
            200: openapi.Response(
                description='Liste des dashboardshares',
                schema=DashboardShareSerializer
            ),
            400: "Paramètre dashboard_id requis",
            401: "Non authentifié"
        }
    )
    def list(self, request: Request) -> Response:
        """Liste les partages d'un tableau de bord."""
        dashboard_id = request.query_params.get('dashboard_id')
        if not dashboard_id:
            return Response({"error": "dashboard_id parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        shares = self.repository.get_by_dashboard(int(dashboard_id))
        serializer = DashboardShareSerializer(shares, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_summary="Partager un tableau de bord",
        operation_description="Partage un tableau de bord avec un utilisateur spécifique.",
        tags=['Monitoring'],
        request_body=DashboardShareSerializer,
        responses={
            201: openapi.Response(
                description='Partage créé',
                schema=DashboardShareSerializer()
            ),
            400: "Données invalides",
            401: "Non authentifié"
        }
    )
    def create(self, request: Request) -> Response:
        """Partage un tableau de bord avec un utilisateur."""
        # Valider les données d'entrée
        serializer = DashboardShareSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Créer le partage
        try:
            share = self.repository.create(
                dashboard_id=serializer.validated_data['dashboard_id'],
                user_id=serializer.validated_data['user_id'],
                can_edit=serializer.validated_data.get('can_edit', False)
            )
            
            response_serializer = DashboardShareSerializer(share)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_summary="Modifier un partage",
        operation_description="Met à jour les permissions d'un partage de tableau de bord.",
        tags=['Monitoring'],
        request_body=DashboardShareSerializer,
        responses={
            200: openapi.Response(
                description='Partage mis à jour',
                schema=DashboardShareSerializer()
            ),
            400: "Données invalides",
            404: "Partage non trouvé",
            401: "Non authentifié"
        }
    )
    def update(self, request: Request, pk=None) -> Response:
        """Met à jour un partage de tableau de bord."""
        # Valider les données d'entrée
        serializer = DashboardShareSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Mettre à jour le partage
        try:
            share = self.repository.update(int(pk), **serializer.validated_data)
            
            response_serializer = DashboardShareSerializer(share)
            return Response(response_serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_summary="Supprimer un partage",
        operation_description="Supprime un partage de tableau de bord.",
        tags=['Monitoring'],
        responses={
            204: "Partage supprimé avec succès",
            404: "Partage non trouvé",
            401: "Non authentifié"
        }
    )
    def destroy(self, request: Request, pk=None) -> Response:
        """Supprime un partage de tableau de bord."""
        try:
            result = self.repository.delete(int(pk))
            if result:
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({"error": "Failed to delete share"}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST) 