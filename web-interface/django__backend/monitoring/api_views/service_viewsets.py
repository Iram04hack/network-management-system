"""
ViewSets API pour les services de surveillance.
Ces ViewSets gèrent les opérations CRUD pour les modèles de vérification de service.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Count, Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from datetime import timedelta
import logging

from ..models import (
    ServiceCheck, DeviceServiceCheck, CheckResult, MonitoringTemplate
)
from ..serializers import (
    ServiceCheckSerializer, DeviceServiceCheckSerializer, 
    CheckResultSerializer, MonitoringTemplateSerializer
)
from ..domain.interfaces.repositories import (
    IServiceCheckRepository, IDeviceServiceCheckRepository, 
    ICheckResultRepository
)

# Configuration du logger
logger = logging.getLogger(__name__)


class ServiceCheckViewSet(viewsets.ModelViewSet):
    """
    API ViewSet pour les vérifications de service.
    """
    queryset = ServiceCheck.objects.all()
    serializer_class = ServiceCheckSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['name', 'check_type', 'enabled']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']

    def get_queryset(self):
        """
        Filtre les vérifications de service en fonction des paramètres de requête.
        """
        queryset = self.queryset
        
        # Filtre par catégorie
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
            
        # Filtre par modèle d'équipement compatible
        device_model = self.request.query_params.get('device_model', None)
        if device_model:
            queryset = queryset.filter(
                Q(compatible_device_types__isnull=True) |  # Compatible avec tous les types
                Q(compatible_device_types__contains=[device_model])
            )
        
        return queryset

    @swagger_auto_schema(
        method='get',
        operation_summary="Vérifications d'équipement",
        operation_description="Récupère les instances de vérification pour les équipements",
        manual_parameters=[
            openapi.Parameter('device_id', openapi.IN_QUERY, description='ID équipement', type=openapi.TYPE_INTEGER),
            openapi.Parameter('is_active', openapi.IN_QUERY, description='Statut d\'activation', type=openapi.TYPE_BOOLEAN)
        ],
        responses={
            200: DeviceServiceCheckSerializer(many=True)
        },
        tags=['Monitoring']
    )
    @action(detail=True, methods=['get'])
    def device_checks(self, request, pk=None):
        """
        Récupère les instances de vérification pour les équipements.
        """
        service_check = self.get_object()
        device_checks = DeviceServiceCheck.objects.filter(service_check=service_check)
        
        # Filtrer par équipement (optionnel)
        device_id = request.query_params.get('device_id')
        if device_id:
            device_checks = device_checks.filter(device_id=device_id)
            
        # Filtrer par statut d'activation
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            is_active = is_active.lower() in ['true', '1', 't', 'y', 'yes']
            device_checks = device_checks.filter(is_active=is_active)
        
        serializer = DeviceServiceCheckSerializer(device_checks, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def update_check_config(self, request, pk=None):
        """
        Met à jour la configuration de vérification.
        """
        service_check = self.get_object()
        
        # Mise à jour de la configuration de vérification
        check_config = request.data.get('check_config', {})
        if not isinstance(check_config, dict):
            return Response(
                {"error": "La configuration de vérification doit être un dictionnaire"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Fusionner avec la configuration existante
            if service_check.check_config:
                service_check.check_config.update(check_config)
            else:
                service_check.check_config = check_config
                
            service_check.save()
            
            return Response({
                "message": "Configuration de vérification mise à jour",
                "check_config": service_check.check_config
            })
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de la configuration: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DeviceServiceCheckViewSet(viewsets.ModelViewSet):
    """
    API ViewSet pour les vérifications de service d'équipement.
    """
    queryset = DeviceServiceCheck.objects.all()
    serializer_class = DeviceServiceCheckSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['device', 'service_check', 'is_active']
    search_fields = ['name', 'device__name', 'service_check__name']
    ordering_fields = ['name', 'last_check']

    def get_queryset(self):
        """
        Filtre les vérifications de service d'équipement en fonction des paramètres de requête.
        """
        queryset = self.queryset
        
        # Filtre par équipement
        device_id = self.request.query_params.get('device_id', None)
        if device_id:
            queryset = queryset.filter(device_id=device_id)
            
        # Filtre par type de vérification
        check_type = self.request.query_params.get('check_type', None)
        if check_type:
            queryset = queryset.filter(service_check__check_type=check_type)
            
        # Filtre par catégorie
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(service_check__category=category)
            
        # Filtre par statut de vérification
        check_status = self.request.query_params.get('check_status', None)
        if check_status:
            # Récupérer les derniers résultats de vérification
            latest_results = CheckResult.objects.filter(
                device_service_check=queryset.values('id')
            ).values('device_service_check_id').annotate(
                max_id=Count('id')
            )
            
            # Filtrer par le statut de la dernière vérification
            if latest_results.exists():
                if check_status == 'ok':
                    queryset = queryset.filter(
                        checkresult__status='ok',
                        checkresult__id__in=[r['max_id'] for r in latest_results]
                    )
                elif check_status == 'warning':
                    queryset = queryset.filter(
                        checkresult__status='warning',
                        checkresult__id__in=[r['max_id'] for r in latest_results]
                    )
                elif check_status == 'critical':
                    queryset = queryset.filter(
                        checkresult__status='critical',
                        checkresult__id__in=[r['max_id'] for r in latest_results]
                    )
                elif check_status == 'unknown':
                    queryset = queryset.filter(
                        checkresult__status='unknown',
                        checkresult__id__in=[r['max_id'] for r in latest_results]
                    )
        
        return queryset

    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """
        Récupère l'historique des résultats pour une vérification de service d'équipement.
        """
        device_check = self.get_object()
        
        # Paramètres de requête pour la plage de temps
        from_time = request.query_params.get('from', None)
        to_time = request.query_params.get('to', None)
        limit = request.query_params.get('limit', 20)
        
        # Convertir les paramètres
        try:
            limit = int(limit)
        except (ValueError, TypeError):
            limit = 20
        
        # Limiter à 1000 maximum
        limit = min(limit, 100)
        
        # Construire la requête
        results_query = CheckResult.objects.filter(device_service_check=device_check)
        
        if from_time:
            try:
                from_time = timezone.datetime.fromisoformat(from_time)
                results_query = results_query.filter(timestamp__gte=from_time)
            except ValueError:
                return Response(
                    {"error": "Format de date invalide pour 'from'. Utilisez ISO 8601."},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        if to_time:
            try:
                to_time = timezone.datetime.fromisoformat(to_time)
                results_query = results_query.filter(timestamp__lte=to_time)
            except ValueError:
                return Response(
                    {"error": "Format de date invalide pour 'to'. Utilisez ISO 8601."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Par défaut, obtenir les dernières 24 heures si aucune plage n'est spécifiée
        if not from_time and not to_time:
            from_time = timezone.now() - timedelta(days=1)
            results_query = results_query.filter(timestamp__gte=from_time)
        
        # Trier et limiter
        results = results_query.order_by('-timestamp')[:limit]
        
        serializer = CheckResultSerializer(results, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """
        Exécute la vérification de service pour un équipement spécifique.
        """
        device_check = self.get_object()
        
        try:
            from ..di_container import resolve
            check_service_use_case = resolve('CheckServiceUseCase')
            
            result = check_service_use_case.execute(device_service_check_id=device_check.id)
            
            if result.get('success', False):
                return Response({
                    "message": "Vérification exécutée avec succès",
                    "result": result
                })
            else:
                return Response({
                    "error": "Échec de la vérification",
                    "details": result.get('error', 'Erreur inconnue')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution de la vérification {device_check.id}: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def update_check_config(self, request, pk=None):
        """
        Met à jour la configuration spécifique de cette vérification.
        """
        device_check = self.get_object()
        
        # Mise à jour de la configuration spécifique
        specific_config = request.data.get('specific_config', {})
        if not isinstance(specific_config, dict):
            return Response(
                {"error": "La configuration spécifique doit être un dictionnaire"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Fusionner avec la configuration existante
            if device_check.specific_config:
                device_check.specific_config.update(specific_config)
            else:
                device_check.specific_config = specific_config
                
            device_check.save()
            
            return Response({
                "message": "Configuration spécifique mise à jour",
                "specific_config": device_check.specific_config
            })
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de la configuration spécifique: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MonitoringTemplateViewSet(viewsets.ModelViewSet):
    """
    API ViewSet pour les modèles de surveillance.
    """
    queryset = MonitoringTemplate.objects.all()
    serializer_class = MonitoringTemplateSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['name', 'is_active', 'device_type']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']

    def get_queryset(self):
        """
        Filtre les modèles de surveillance en fonction des paramètres de requête.
        """
        queryset = self.queryset
        
        # Filtre par type d'équipement
        device_type = self.request.query_params.get('device_type', None)
        if device_type:
            queryset = queryset.filter(device_type=device_type)
            
        # Filtre par capacité (peut contenir des métriques ou des vérifications)
        has_metrics = self.request.query_params.get('has_metrics')
        if has_metrics is not None:
            has_metrics = has_metrics.lower() in ['true', '1', 't', 'y', 'yes']
            if has_metrics:
                queryset = queryset.filter(metrics_definitions__isnull=False).distinct()
            else:
                queryset = queryset.filter(metrics_definitions__isnull=True)
                
        has_checks = self.request.query_params.get('has_checks')
        if has_checks is not None:
            has_checks = has_checks.lower() in ['true', '1', 't', 'y', 'yes']
            if has_checks:
                queryset = queryset.filter(service_checks__isnull=False).distinct()
            else:
                queryset = queryset.filter(service_checks__isnull=True)
        
        return queryset

    @action(detail=True, methods=['get'])
    def included_checks(self, request, pk=None):
        """
        Récupère les vérifications de service incluses dans ce modèle.
        """
        template = self.get_object()
        checks = template.service_checks.all()
        
        serializer = ServiceCheckSerializer(checks, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def included_metrics(self, request, pk=None):
        """
        Récupère les définitions de métriques incluses dans ce modèle.
        """
        template = self.get_object()
        metrics = template.metrics_definitions.all()
        
        from ..serializers import MetricsDefinitionSerializer
        serializer = MetricsDefinitionSerializer(metrics, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def apply_to_device(self, request, pk=None):
        """
        Applique ce modèle de surveillance à un équipement.
        """
        template = self.get_object()
        device_id = request.data.get('device_id')
        
        if not device_id:
            return Response(
                {"error": "L'ID de l'équipement est requis"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from ..di_container import resolve
            apply_template_use_case = resolve('ApplyMonitoringTemplateUseCase')
            
            result = apply_template_use_case.execute(
                template_id=template.id,
                device_id=device_id
            )
            
            if result.get('success', False):
                return Response({
                    "message": "Modèle appliqué avec succès",
                    "details": result
                })
            else:
                return Response({
                    "error": "Échec de l'application du modèle",
                    "details": result.get('error', 'Erreur inconnue')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Erreur lors de l'application du modèle {template.id}: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 