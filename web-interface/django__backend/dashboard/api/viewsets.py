"""
ViewSets CRUD complets pour le module Dashboard.

Ce fichier contient les ViewSets Django REST Framework qui fournissent
toutes les opérations CRUD (Create, Read, Update, Delete) pour les modèles
du module Dashboard.
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..models import UserDashboardConfig, DashboardWidget, DashboardPreset, CustomDashboard
from .serializers import (
    UserDashboardConfigSerializer,
    DashboardWidgetSerializer,
    DashboardPresetSerializer,
    CustomDashboardSerializer
)


class UserDashboardConfigViewSet(viewsets.ModelViewSet):
    """
    ViewSet CRUD complet pour les configurations de tableau de bord utilisateur.

    Fournit toutes les opérations CRUD pour la personnalisation des tableaux de bord.
    Chaque utilisateur peut avoir une configuration unique pour personnaliser
    l'apparence et le comportement de son tableau de bord.
    """

    serializer_class = UserDashboardConfigSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['theme', 'layout']
    search_fields = ['user__username']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-updated_at']
    
    def get_queryset(self):
        """Retourne seulement les configurations de l'utilisateur connecté."""
        # Gestion du cas où request est None (génération de schéma Swagger)
        if getattr(self, 'swagger_fake_view', False) or not hasattr(self.request, 'user'):
            return UserDashboardConfig.objects.none()
        return UserDashboardConfig.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Associe automatiquement l'utilisateur connecté lors de la création."""
        serializer.save(user=self.request.user)

    @swagger_auto_schema(
        operation_summary="Liste des configurations de tableau de bord",
        operation_description="Récupère la liste des configurations de tableau de bord de l'utilisateur connecté.",
        responses={
            200: openapi.Response('Liste des configurations', UserDashboardConfigSerializer),
            401: "Non authentifié"
        },
        tags=['Dashboard']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Créer une configuration de tableau de bord",
        operation_description="Crée une nouvelle configuration de tableau de bord pour l'utilisateur connecté.",
        request_body=UserDashboardConfigSerializer,
        responses={
            201: UserDashboardConfigSerializer,
            400: "Données invalides",
            401: "Non authentifié"
        },
        tags=['Dashboard']
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Détails d'une configuration",
        operation_description="Récupère les détails d'une configuration de tableau de bord spécifique.",
        responses={
            200: UserDashboardConfigSerializer,
            404: "Configuration non trouvée",
            401: "Non authentifié"
        },
        tags=['Dashboard']
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Modifier une configuration",
        operation_description="Met à jour complètement une configuration de tableau de bord.",
        request_body=UserDashboardConfigSerializer,
        responses={
            200: UserDashboardConfigSerializer,
            400: "Données invalides",
            404: "Configuration non trouvée",
            401: "Non authentifié"
        },
        tags=['Dashboard']
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Modification partielle d'une configuration",
        operation_description="Met à jour partiellement une configuration de tableau de bord.",
        request_body=UserDashboardConfigSerializer,
        responses={
            200: UserDashboardConfigSerializer,
            400: "Données invalides",
            404: "Configuration non trouvée",
            401: "Non authentifié"
        },
        tags=['Dashboard']
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Supprimer une configuration",
        operation_description="Supprime une configuration de tableau de bord.",
        responses={
            204: "Configuration supprimée avec succès",
            404: "Configuration non trouvée",
            401: "Non authentifié"
        },
        tags=['Dashboard']
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Configuration par défaut",
        operation_description="Récupère ou crée la configuration par défaut de l'utilisateur connecté.",
        responses={200: "Configuration par défaut récupérée ou créée"},
        tags=['Dashboard']
    )
    @action(detail=False, methods=['get'])
    def default(self, request):
        """Récupère ou crée la configuration par défaut de l'utilisateur."""
        config, created = UserDashboardConfig.objects.get_or_create(
            user=request.user,
            defaults={
                'theme': 'light',
                'layout': 'grid',
                'refresh_interval': 60
            }
        )
        serializer = self.get_serializer(config)
        return Response({
            'status': 'success',
            'data': serializer.data,
            'created': created
        })


class DashboardWidgetViewSet(viewsets.ModelViewSet):
    """
    ViewSet CRUD complet pour les widgets de tableau de bord.

    Gère tous les widgets qui peuvent être placés sur les tableaux de bord.
    Chaque widget a un type spécifique (santé système, alertes, graphiques, etc.)
    et peut être positionné et configuré individuellement.
    """

    queryset = DashboardWidget.objects.all()
    serializer_class = DashboardWidgetSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['widget_type', 'config', 'preset', 'is_active']
    search_fields = ['widget_type']
    ordering_fields = ['widget_type', 'position_x', 'position_y']
    ordering = ['position_y', 'position_x']

    @swagger_auto_schema(
        operation_summary="Liste des widgets",
        operation_description="Récupère la liste de tous les widgets de tableau de bord avec filtrage et recherche.",
        responses={
            200: openapi.Response('Liste des widgets', DashboardWidgetSerializer),
            401: "Non authentifié"
        },
        tags=['Dashboard']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Créer un widget",
        operation_description="Crée un nouveau widget de tableau de bord avec le type et la position spécifiés.",
        request_body=DashboardWidgetSerializer,
        responses={
            201: DashboardWidgetSerializer,
            400: "Données invalides",
            401: "Non authentifié"
        },
        tags=['Dashboard']
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Détails d'un widget",
        operation_description="Récupère les détails d'un widget spécifique.",
        responses={
            200: DashboardWidgetSerializer,
            404: "Widget non trouvé",
            401: "Non authentifié"
        },
        tags=['Dashboard']
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Modifier un widget",
        operation_description="Met à jour complètement un widget de tableau de bord.",
        request_body=DashboardWidgetSerializer,
        responses={
            200: DashboardWidgetSerializer,
            400: "Données invalides",
            404: "Widget non trouvé",
            401: "Non authentifié"
        },
        tags=['Dashboard']
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Modification partielle d'un widget",
        operation_description="Met à jour partiellement un widget de tableau de bord.",
        request_body=DashboardWidgetSerializer,
        responses={
            200: DashboardWidgetSerializer,
            400: "Données invalides",
            404: "Widget non trouvé",
            401: "Non authentifié"
        },
        tags=['Dashboard']
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Supprimer un widget",
        operation_description="Supprime un widget de tableau de bord.",
        responses={
            204: "Widget supprimé avec succès",
            404: "Widget non trouvé",
            401: "Non authentifié"
        },
        tags=['Dashboard']
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Dupliquer un widget",
        operation_description="Crée une copie d'un widget existant avec une position légèrement décalée.",
        responses={200: "Widget dupliqué avec succès"},
        tags=['Dashboard']
    )
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Duplique un widget existant avec une position décalée."""
        widget = self.get_object()
        widget.pk = None  # Créer une nouvelle instance
        widget.position_x += 50  # Décaler légèrement
        widget.position_y += 50
        widget.save()

        serializer = self.get_serializer(widget)
        return Response({
            'status': 'success',
            'message': 'Widget dupliqué avec succès',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_summary="Types de widgets disponibles",
        operation_description="Récupère la liste des types de widgets disponibles avec leurs descriptions et configurations par défaut.",
        responses={200: "Liste des types de widgets disponibles"},
        tags=['Dashboard']
    )
    @action(detail=False, methods=['get'])
    def widget_types(self, request):
        """Récupère la liste des types de widgets disponibles avec leurs métadonnées."""
        from ..models import DashboardWidget

        widget_types_info = []
        for widget_type, display_name in DashboardWidget.WIDGET_TYPES:
            info = {
                'type': widget_type,
                'name': display_name,
                'description': self._get_widget_description(widget_type),
                'default_settings': self._get_default_settings(widget_type),
                'default_size': self._get_default_size(widget_type)
            }
            widget_types_info.append(info)

        return Response({
            'status': 'success',
            'widget_types': widget_types_info
        })

    def _get_widget_description(self, widget_type):
        """Retourne la description d'un type de widget."""
        descriptions = {
            'system_health': 'Affiche les métriques de santé du système (CPU, mémoire, disque)',
            'network_overview': 'Vue d\'ensemble du réseau avec statistiques globales',
            'alerts': 'Liste des alertes actives du système',
            'device_status': 'État des équipements réseau',
            'interface_status': 'État des interfaces réseau',
            'performance_chart': 'Graphiques de performance en temps réel',
            'topology': 'Carte de topologie réseau interactive',
            'custom_chart': 'Graphique personnalisable'
        }
        return descriptions.get(widget_type, 'Widget personnalisé')

    def _get_default_settings(self, widget_type):
        """Retourne les paramètres par défaut d'un type de widget."""
        defaults = {
            'system_health': {'refresh_interval': 30, 'show_details': True},
            'network_overview': {'show_topology': True, 'show_stats': True},
            'alerts': {'limit': 10, 'severity_filter': ['critical', 'warning']},
            'device_status': {'show_offline': True, 'group_by_type': False},
            'interface_status': {'show_down': True, 'show_utilization': True},
            'performance_chart': {'time_range': '1h', 'auto_refresh': True},
            'topology': {'layout': 'force', 'show_labels': True},
            'custom_chart': {'chart_type': 'line', 'data_source': 'custom'}
        }
        return defaults.get(widget_type, {})

    def _get_default_size(self, widget_type):
        """Retourne la taille par défaut d'un type de widget."""
        sizes = {
            'system_health': {'width': 4, 'height': 2},
            'network_overview': {'width': 6, 'height': 4},
            'alerts': {'width': 8, 'height': 3},
            'device_status': {'width': 6, 'height': 3},
            'interface_status': {'width': 6, 'height': 3},
            'performance_chart': {'width': 8, 'height': 4},
            'topology': {'width': 12, 'height': 8},
            'custom_chart': {'width': 6, 'height': 4}
        }
        return sizes.get(widget_type, {'width': 4, 'height': 2})


class DashboardPresetViewSet(viewsets.ModelViewSet):
    """
    ViewSet CRUD complet pour les préréglages de tableau de bord.

    Gère des configurations prédéfinies de tableaux de bord que les utilisateurs
    peuvent appliquer rapidement. Chaque préréglage contient un thème, une disposition
    et un ensemble de widgets préconfigurés.
    """

    queryset = DashboardPreset.objects.all()
    serializer_class = DashboardPresetSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_default', 'theme']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    @swagger_auto_schema(
        operation_summary="Liste des préréglages",
        operation_description="Récupère la liste de tous les préréglages de tableau de bord disponibles.",
        responses={
            200: openapi.Response('Liste des presets', DashboardPresetSerializer),
            401: "Non authentifié"
        },
        tags=['Dashboard']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Créer un préréglage",
        operation_description="Crée un nouveau préréglage de tableau de bord.",
        request_body=DashboardPresetSerializer,
        responses={
            201: DashboardPresetSerializer,
            400: "Données invalides",
            401: "Non authentifié"
        },
        tags=['Dashboard']
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Détails d'un préréglage",
        operation_description="Récupère les détails d'un préréglage spécifique.",
        responses={
            200: DashboardPresetSerializer,
            404: "Préréglage non trouvé",
            401: "Non authentifié"
        },
        tags=['Dashboard']
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Modifier un préréglage",
        operation_description="Met à jour complètement un préréglage de tableau de bord.",
        request_body=DashboardPresetSerializer,
        responses={
            200: DashboardPresetSerializer,
            400: "Données invalides",
            404: "Préréglage non trouvé",
            401: "Non authentifié"
        },
        tags=['Dashboard']
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Modification partielle d'un préréglage",
        operation_description="Met à jour partiellement un préréglage de tableau de bord.",
        request_body=DashboardPresetSerializer,
        responses={
            200: DashboardPresetSerializer,
            400: "Données invalides",
            404: "Préréglage non trouvé",
            401: "Non authentifié"
        },
        tags=['Dashboard']
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Supprimer un préréglage",
        operation_description="Supprime un préréglage de tableau de bord.",
        responses={
            204: "Préréglage supprimé avec succès",
            404: "Préréglage non trouvé",
            401: "Non authentifié"
        },
        tags=['Dashboard']
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Appliquer un préréglage",
        operation_description="Applique un préréglage à la configuration de tableau de bord de l'utilisateur connecté.",
        responses={200: "Préréglage appliqué avec succès"},
        tags=['Dashboard']
    )
    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        """Applique un préréglage à la configuration de l'utilisateur."""
        preset = self.get_object()
        
        # Récupérer ou créer la configuration utilisateur
        config, created = UserDashboardConfig.objects.get_or_create(
            user=request.user,
            defaults={
                'theme': preset.theme,
                'layout': preset.layout,
                'refresh_interval': preset.refresh_interval
            }
        )
        
        # Appliquer les paramètres du préréglage
        if not created:
            config.theme = preset.theme
            config.layout = preset.layout
            config.refresh_interval = preset.refresh_interval
            config.save()
        
        return Response({
            'status': 'success',
            'message': f'Préréglage "{preset.name}" appliqué avec succès',
            'config': UserDashboardConfigSerializer(config).data
        })


class CustomDashboardViewSet(viewsets.ModelViewSet):
    """
    ViewSet CRUD complet pour les tableaux de bord personnalisés.

    Permet aux utilisateurs de créer, modifier et gérer leurs propres
    tableaux de bord avec des configurations personnalisées. Chaque utilisateur
    peut avoir plusieurs dashboards et en définir un comme défaut.
    """

    serializer_class = CustomDashboardSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_default']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['-updated_at']

    def get_queryset(self):
        """Retourne seulement les dashboards de l'utilisateur connecté."""
        # Gestion du cas où request est None (génération de schéma Swagger)
        if getattr(self, 'swagger_fake_view', False) or not hasattr(self.request, 'user'):
            return CustomDashboard.objects.none()
        return CustomDashboard.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        """Associe automatiquement l'utilisateur connecté comme propriétaire."""
        serializer.save(owner=self.request.user)

    @swagger_auto_schema(
        operation_summary="Liste des dashboards personnalisés",
        operation_description="Récupère la liste des dashboards personnalisés de l'utilisateur connecté.",
        responses={
            200: openapi.Response('Liste des dashboards custom', CustomDashboardSerializer),
            401: "Non authentifié"
        },
        tags=['Dashboard']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Créer un dashboard personnalisé",
        operation_description="Crée un nouveau dashboard personnalisé pour l'utilisateur connecté.",
        request_body=CustomDashboardSerializer,
        responses={
            201: CustomDashboardSerializer,
            400: "Données invalides",
            401: "Non authentifié"
        },
        tags=['Dashboard']
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Détails d'un dashboard personnalisé",
        operation_description="Récupère les détails d'un dashboard personnalisé spécifique.",
        responses={
            200: CustomDashboardSerializer,
            404: "Dashboard non trouvé",
            401: "Non authentifié"
        },
        tags=['Dashboard']
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Modifier un dashboard personnalisé",
        operation_description="Met à jour complètement un dashboard personnalisé.",
        request_body=CustomDashboardSerializer,
        responses={
            200: CustomDashboardSerializer,
            400: "Données invalides",
            404: "Dashboard non trouvé",
            401: "Non authentifié"
        },
        tags=['Dashboard']
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Modification partielle d'un dashboard",
        operation_description="Met à jour partiellement un dashboard personnalisé.",
        request_body=CustomDashboardSerializer,
        responses={
            200: CustomDashboardSerializer,
            400: "Données invalides",
            404: "Dashboard non trouvé",
            401: "Non authentifié"
        },
        tags=['Dashboard']
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Supprimer un dashboard personnalisé",
        operation_description="Supprime un dashboard personnalisé.",
        responses={
            204: "Dashboard supprimé avec succès",
            404: "Dashboard non trouvé",
            401: "Non authentifié"
        },
        tags=['Dashboard']
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Définir comme dashboard par défaut",
        operation_description="Définit ce dashboard comme dashboard par défaut pour l'utilisateur connecté.",
        responses={200: "Dashboard défini comme défaut avec succès"},
        tags=['Dashboard']
    )
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """Définit ce dashboard comme dashboard par défaut pour l'utilisateur."""
        dashboard = self.get_object()
        
        # Désactiver tous les autres dashboards par défaut
        CustomDashboard.objects.filter(
            owner=request.user, 
            is_default=True
        ).update(is_default=False)
        
        # Activer celui-ci comme défaut
        dashboard.is_default = True
        dashboard.save()
        
        return Response({
            'status': 'success',
            'message': f'Dashboard "{dashboard.name}" défini comme défaut'
        })
