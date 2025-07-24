"""
Vues Django pour le module monitoring.
Ces vues gèrent les pages web et les requêtes HTTP pour l'interface utilisateur.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, timedelta
import json

from .models import (
    Alert, DeviceMetric, MetricValue, CheckResult,
    Dashboard, DeviceServiceCheck, ServiceCheck, BusinessKPI
)
from .serializers import (
    AlertSerializer, CheckResultSerializer,
    DashboardSerializer
)
from .serializers.metrics_serializers import MetricValueSerializer
from .forms import AlertFilterForm, ServiceCheckFilterForm


# Pages principales

@login_required
def monitoring_dashboard(request):
    """
    Page d'accueil du module de surveillance.
    
    Args:
        request: Requête HTTP
        
    Returns:
        Réponse HTTP avec le rendu de la page d'accueil
    """
    # Récupérer le dashboard par défaut ou le premier disponible
    dashboard = Dashboard.objects.filter(is_default=True).first()
    if not dashboard:
        dashboard = Dashboard.objects.first()
    
    # Statistiques pour le tableau de bord
    alerts_count = Alert.objects.count()
    active_alerts_count = Alert.objects.filter(status='active').count()
    critical_alerts_count = Alert.objects.filter(status='active', severity='critical').count()
    
    devices_with_issues = Alert.objects.filter(
        status='active'
    ).values('device__name', 'device_id').annotate(
        alert_count=Count('id')
    ).order_by('-alert_count')[:5]
    
    # Récupérer les dernières alertes
    latest_alerts = Alert.objects.all().order_by('-created_at')[:10]
    
    context = {
        'dashboard': dashboard,
        'alerts_count': alerts_count,
        'active_alerts_count': active_alerts_count,
        'critical_alerts_count': critical_alerts_count,
        'devices_with_issues': devices_with_issues,
        'latest_alerts': latest_alerts,
    }
    
    return render(request, 'monitoring/dashboard.html', context)


@login_required
def alert_list(request):
    """
    Liste des alertes avec filtres.
    
    Args:
        request: Requête HTTP
        
    Returns:
        Réponse HTTP avec le rendu de la page de liste des alertes
    """
    # Initialiser les filtres
    filter_form = AlertFilterForm(request.GET)
    alerts = Alert.objects.all()
    
    # Appliquer les filtres si le formulaire est valide
    if filter_form.is_valid():
        # Filtre de statut
        status = filter_form.cleaned_data.get('status')
        if status:
            alerts = alerts.filter(status=status)
        
        # Filtre de sévérité
        severity = filter_form.cleaned_data.get('severity')
        if severity:
            alerts = alerts.filter(severity=severity)
        
        # Filtre d'équipement
        device = filter_form.cleaned_data.get('device')
        if device:
            alerts = alerts.filter(device=device)
        
        # Filtre de date
        start_date = filter_form.cleaned_data.get('start_date')
        if start_date:
            alerts = alerts.filter(created_at__gte=start_date)
            
        end_date = filter_form.cleaned_data.get('end_date')
        if end_date:
            alerts = alerts.filter(created_at__lte=end_date)
        
        # Filtre de recherche
        search = filter_form.cleaned_data.get('search')
        if search:
            alerts = alerts.filter(
                Q(message__icontains=search) |
                Q(device__name__icontains=search)
            )
    
    # Tri par défaut
    alerts = alerts.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(alerts, 20)  # 20 alertes par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filter_form': filter_form,
        'active_count': Alert.objects.filter(status='active').count(),
        'critical_count': Alert.objects.filter(severity='critical', status='active').count(),
    }
    
    return render(request, 'monitoring/alert_list.html', context)


@login_required
def alert_detail(request, alert_id):
    """
    Détails d'une alerte spécifique.
    
    Args:
        request: Requête HTTP
        alert_id: ID de l'alerte
        
    Returns:
        Réponse HTTP avec le rendu de la page de détails de l'alerte
    """
    alert = get_object_or_404(Alert, id=alert_id)
    
    # Récupérer l'historique des alertes similaires
    similar_alerts = Alert.objects.filter(
        device=alert.device,
        message=alert.message
    ).exclude(id=alert_id).order_by('-created_at')[:5]
    
    # Récupérer les métriques associées si disponibles
    metrics = []
    if alert.metric:
        metric_values = MetricValue.objects.filter(
            device_metric__metric=alert.metric,
            device_metric__device=alert.device
        ).order_by('-timestamp')[:100]
        
        metrics = [{
            'timestamp': value.timestamp.isoformat(),
            'value': value.value
        } for value in metric_values]
    
    context = {
        'alert': alert,
        'similar_alerts': similar_alerts,
        'metrics': json.dumps(metrics),
    }
    
    return render(request, 'monitoring/alert_detail.html', context)


@login_required
def device_list(request):
    """
    Liste des équipements avec leurs statistiques de surveillance.
    
    Args:
        request: Requête HTTP
        
    Returns:
        Réponse HTTP avec le rendu de la page de liste des équipements
    """
    from network_management.models import NetworkDevice
    
    devices = NetworkDevice.objects.all()
    
    # Ajouter des statistiques de surveillance pour chaque équipement
    device_stats = []
    for device in devices:
        # Nombre d'alertes actives
        active_alerts = Alert.objects.filter(device=device, status='active').count()
        
        # Nombre de métriques configurées
        metrics_count = DeviceMetric.objects.filter(device=device, is_active=True).count()
        
        # Nombre de vérifications de service configurées
        service_checks_count = DeviceServiceCheck.objects.filter(device=device, is_active=True).count()
        
        # Dernière vérification réussie
        last_success_check = CheckResult.objects.filter(
            device_service_check__device=device, 
            status='ok'
        ).order_by('-timestamp').first()
        
        device_stats.append({
            'device': device,
            'active_alerts': active_alerts,
            'metrics_count': metrics_count,
            'service_checks_count': service_checks_count,
            'last_success_check': last_success_check.timestamp if last_success_check else None,
        })
    
    context = {
        'device_stats': device_stats,
    }
    
    return render(request, 'monitoring/device_list.html', context)


@login_required
def device_detail(request, device_id):
    """
    Détails de surveillance pour un équipement spécifique.
    
    Args:
        request: Requête HTTP
        device_id: ID de l'équipement
        
    Returns:
        Réponse HTTP avec le rendu de la page de détails de l'équipement
    """
    from network_management.models import NetworkDevice
    
    device = get_object_or_404(NetworkDevice, id=device_id)
    
    # Récupérer les alertes actives
    active_alerts = Alert.objects.filter(device=device, status='active').order_by('-created_at')
    
    # Récupérer les métriques configurées
    device_metrics = DeviceMetric.objects.filter(device=device, is_active=True)
    
    # Récupérer les vérifications de service configurées
    service_checks = DeviceServiceCheck.objects.filter(device=device, is_active=True)
    
    # Récupérer les derniers résultats de vérification
    last_checks = CheckResult.objects.filter(
        device_service_check__device=device
    ).order_by('-timestamp')[:20]
    
    context = {
        'device': device,
        'active_alerts': active_alerts,
        'device_metrics': device_metrics,
        'service_checks': service_checks,
        'last_checks': last_checks,
    }
    
    return render(request, 'monitoring/device_detail.html', context)


@login_required
def device_metrics(request, device_id):
    """
    Page de visualisation des métriques d'un équipement.
    
    Args:
        request: Requête HTTP
        device_id: ID de l'équipement
        
    Returns:
        Réponse HTTP avec le rendu de la page de métriques de l'équipement
    """
    from network_management.models import NetworkDevice
    
    device = get_object_or_404(NetworkDevice, id=device_id)
    
    # Récupérer les métriques configurées
    device_metrics = DeviceMetric.objects.filter(device=device, is_active=True)
    
    # Récupérer la plage de temps demandée (par défaut : 24 dernières heures)
    time_range = request.GET.get('time_range', '24h')
    
    if time_range == '1h':
        start_time = timezone.now() - timedelta(hours=1)
    elif time_range == '6h':
        start_time = timezone.now() - timedelta(hours=6)
    elif time_range == '24h':
        start_time = timezone.now() - timedelta(days=1)
    elif time_range == '7d':
        start_time = timezone.now() - timedelta(days=7)
    elif time_range == '30d':
        start_time = timezone.now() - timedelta(days=30)
    else:
        start_time = timezone.now() - timedelta(days=1)
    
    # Préparer les données des métriques
    metrics_data = []
    for metric in device_metrics:
        # Récupérer les valeurs sur la période demandée
        values = MetricValue.objects.filter(
            device_metric=metric,
            timestamp__gte=start_time
        ).order_by('timestamp')
        
        # Préparer les données pour le graphique
        data_points = [{
            'timestamp': value.timestamp.isoformat(),
            'value': value.value
        } for value in values]
        
        metrics_data.append({
            'metric': metric,
            'data': data_points,
        })
    
    context = {
        'device': device,
        'metrics_data': json.dumps(metrics_data),
        'time_range': time_range,
        'device_metrics': device_metrics,
    }
    
    return render(request, 'monitoring/device_metrics.html', context)


@login_required
def dashboard_list(request):
    """
    Liste des tableaux de bord disponibles.
    
    Args:
        request: Requête HTTP
        
    Returns:
        Réponse HTTP avec le rendu de la page de liste des tableaux de bord
    """
    user = request.user
    
    # Récupérer les tableaux de bord publics et ceux de l'utilisateur
    dashboards = Dashboard.objects.filter(
        Q(is_public=True) | Q(owner=user)
    ).order_by('title')
    
    context = {
        'dashboards': dashboards,
    }
    
    return render(request, 'monitoring/dashboard_list.html', context)


@login_required
def dashboard_detail(request, uid):
    """
    Affiche un tableau de bord spécifique.
    
    Args:
        request: Requête HTTP
        uid: UID du tableau de bord
        
    Returns:
        Réponse HTTP avec le rendu du tableau de bord
    """
    dashboard = get_object_or_404(Dashboard, uid=uid)
    
    # Vérifier les permissions
    if not dashboard.is_public and dashboard.owner != request.user:
        return redirect('monitoring:dashboard_list')
    
    context = {
        'dashboard': dashboard,
    }
    
    return render(request, 'monitoring/dashboard_detail.html', context)


@login_required
def report_list(request):
    """
    Liste des rapports disponibles.
    
    Args:
        request: Requête HTTP
        
    Returns:
        Réponse HTTP avec le rendu de la page de liste des rapports
    """
    # TODO: Implémenter la liste des rapports
    context = {}
    
    return render(request, 'monitoring/report_list.html', context)


@login_required
def report_detail(request, report_id):
    """
    Affiche un rapport spécifique.
    
    Args:
        request: Requête HTTP
        report_id: ID du rapport
        
    Returns:
        Réponse HTTP avec le rendu du rapport
    """
    # TODO: Implémenter les détails du rapport
    context = {
        'report_id': report_id,
    }
    
    return render(request, 'monitoring/report_detail.html', context)


@login_required
def monitoring_admin(request):
    """
    Interface d'administration personnalisée.
    
    Args:
        request: Requête HTTP
        
    Returns:
        Réponse HTTP avec le rendu de la page d'administration
    """
    # Statistiques pour l'administration
    stats = {
        'alert_count': Alert.objects.count(),
        'active_alert_count': Alert.objects.filter(status='active').count(),
        'service_check_count': ServiceCheck.objects.count(),
        'metrics_definition_count': DeviceMetric.objects.count(),
    }
    
    context = {
        'stats': stats,
    }
    
    return render(request, 'monitoring/admin/index.html', context)


@login_required
def monitoring_config(request):
    """
    Page de configuration du module de surveillance.
    
    Args:
        request: Requête HTTP
        
    Returns:
        Réponse HTTP avec le rendu de la page de configuration
    """
    # TODO: Implémenter la page de configuration
    context = {}
    
    return render(request, 'monitoring/admin/config.html', context)


# API Views

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def collect_metrics_view(request):
    """
    Endpoint pour collecter des métriques.
    
    Args:
        request: Requête HTTP
        
    Returns:
        Response avec le résultat de la collecte
    """
    try:
        from .di_container import resolve
        collect_metrics_use_case = resolve('CollectMetricsUseCase')
        
        # Récupérer l'ID de l'équipement (optionnel)
        device_id = request.data.get('device_id')
        
        result = collect_metrics_use_case.execute(device_id=device_id)
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': str(e),
            'success': False
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def device_metrics_history(request, device_id):
    """
    Endpoint pour récupérer l'historique des métriques d'un équipement.
    
    Args:
        request: Requête HTTP
        device_id: ID de l'équipement
        
    Returns:
        Response avec l'historique des métriques
    """
    try:
        # Paramètres de requête
        from_time = request.query_params.get('from')
        to_time = request.query_params.get('to')
        metric_ids = request.query_params.get('metrics')
        
        # Convertir les paramètres
        if from_time:
            from_time = datetime.fromisoformat(from_time)
        else:
            from_time = timezone.now() - timedelta(days=1)
            
        if to_time:
            to_time = datetime.fromisoformat(to_time)
        else:
            to_time = timezone.now()
            
        # Filtrer les métriques demandées
        device_metrics = DeviceMetric.objects.filter(device_id=device_id, is_active=True)
        if metric_ids:
            metric_ids = [int(id) for id in metric_ids.split(',')]
            device_metrics = device_metrics.filter(id__in=metric_ids)
        
        # Récupérer les valeurs pour chaque métrique
        result = {}
        for device_metric in device_metrics:
            values = MetricValue.objects.filter(
                device_metric=device_metric,
                timestamp__gte=from_time,
                timestamp__lte=to_time
            ).order_by('timestamp')
            
            result[device_metric.id] = {
                'metric': {
                    'id': device_metric.metric.id,
                    'name': device_metric.metric.name,
                    'unit': device_metric.metric.unit,
                    'type': device_metric.metric.metric_type
                },
                'values': MetricValueSerializer(values, many=True).data
            }
        
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_metrics_data(request):
    """
    Endpoint pour récupérer les données des métriques pour un tableau de bord.
    
    Args:
        request: Requête HTTP
        
    Returns:
        Response avec les données des métriques
    """
    try:
        # Paramètres de requête
        dashboard_uid = request.query_params.get('dashboard_uid')
        
        # Récupérer le tableau de bord
        dashboard = get_object_or_404(Dashboard, uid=dashboard_uid)
        
        # Récupérer les widgets du tableau de bord
        widgets = dashboard.widgets.all()
        
        # Récupérer les données pour chaque widget
        result = {}
        for widget in widgets:
            # Vérifier le type de widget
            if widget.widget_type == 'metric_value':
                # Widget de valeur de métrique
                device_metric_id = widget.data_source.get('device_metric_id')
                if device_metric_id:
                    latest_value = MetricValue.objects.filter(
                        device_metric_id=device_metric_id
                    ).order_by('-timestamp').first()
                    
                    if latest_value:
                        result[widget.id] = {
                            'value': latest_value.value,
                            'timestamp': latest_value.timestamp.isoformat()
                        }
            
            elif widget.widget_type == 'chart':
                # Widget de graphique
                device_metric_ids = widget.data_source.get('device_metric_ids', [])
                if device_metric_ids:
                    # Récupérer la plage de temps
                    time_range = widget.data_source.get('time_range', '24h')
                    if time_range == '1h':
                        start_time = timezone.now() - timedelta(hours=1)
                    elif time_range == '6h':
                        start_time = timezone.now() - timedelta(hours=6)
                    elif time_range == '24h':
                        start_time = timezone.now() - timedelta(days=1)
                    elif time_range == '7d':
                        start_time = timezone.now() - timedelta(days=7)
                    elif time_range == '30d':
                        start_time = timezone.now() - timedelta(days=30)
                    else:
                        start_time = timezone.now() - timedelta(days=1)
                    
                    # Récupérer les données pour chaque métrique
                    chart_data = {}
                    for device_metric_id in device_metric_ids:
                        values = MetricValue.objects.filter(
                            device_metric_id=device_metric_id,
                            timestamp__gte=start_time
                        ).order_by('timestamp')
                        
                        chart_data[device_metric_id] = MetricValueSerializer(values, many=True).data
                    
                    result[widget.id] = chart_data
            
            elif widget.widget_type == 'alert_list':
                # Widget de liste d'alertes
                limit = widget.data_source.get('limit', 5)
                status_filter = widget.data_source.get('status')
                severity_filter = widget.data_source.get('severity')
                
                alerts = Alert.objects.all()
                if status_filter:
                    alerts = alerts.filter(status=status_filter)
                if severity_filter:
                    alerts = alerts.filter(severity=severity_filter)
                
                alerts = alerts.order_by('-created_at')[:limit]
                result[widget.id] = AlertSerializer(alerts, many=True).data
        
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def check_services_view(request):
    """
    Endpoint pour vérifier les services.
    
    Args:
        request: Requête HTTP
        
    Returns:
        Response avec le résultat des vérifications
    """
    try:
        from .di_container import resolve
        check_services_use_case = resolve('CheckServicesUseCase')
        
        if request.method == 'GET':
            # Récupérer le service check ID (optionnel)
            service_check_id = request.query_params.get('service_check_id')
            device_id = request.query_params.get('device_id')
            
            result = check_services_use_case.execute(
                service_check_id=service_check_id,
                device_id=device_id
            )
        else:  # POST
            # Récupérer le service check ID (optionnel)
            service_check_id = request.data.get('service_check_id')
            device_id = request.data.get('device_id')
            
            result = check_services_use_case.execute(
                service_check_id=service_check_id,
                device_id=device_id
            )
            
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': str(e),
            'success': False
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def last_service_checks(request):
    """
    Endpoint pour récupérer les dernières vérifications de service.
    
    Args:
        request: Requête HTTP
        
    Returns:
        Response avec les dernières vérifications
    """
    try:
        # Paramètres de requête
        device_id = request.query_params.get('device_id')
        service_check_id = request.query_params.get('service_check_id')
        device_service_check_id = request.query_params.get('device_service_check_id')
        limit = request.query_params.get('limit', 10)
        
        # Convertir limit en entier
        try:
            limit = int(limit)
        except (ValueError, TypeError):
            limit = 10
            
        # Limiter à 100 maximum
        limit = min(limit, 100)
        
        # Filtrer les résultats
        results = CheckResult.objects.all()
        if device_id:
            results = results.filter(device_service_check__device_id=device_id)
        if service_check_id:
            results = results.filter(device_service_check__service_check_id=service_check_id)
        if device_service_check_id:
            results = results.filter(device_service_check_id=device_service_check_id)
            
        # Trier et limiter
        results = results.order_by('-timestamp')[:limit]
        
        # Sérialiser
        serializer = CheckResultSerializer(results, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def anomaly_detection_view(request):
    """
    Endpoint pour la détection d'anomalies.
    
    Args:
        request: Requête HTTP
        
    Returns:
        Response avec les anomalies détectées
    """
    try:
        # TODO: Implémenter la détection d'anomalies
        from .di_container import resolve
        detect_anomalies_use_case = resolve('DetectAnomaliesUseCase')
        
        # Récupérer les paramètres
        device_metric_id = request.data.get('device_metric_id')
        
        # Paramètres optionnels
        start_time = request.data.get('start_time')
        end_time = request.data.get('end_time')
        algorithm = request.data.get('algorithm', 'auto')
        
        if start_time:
            start_time = datetime.fromisoformat(start_time)
        else:
            start_time = timezone.now() - timedelta(days=7)
            
        if end_time:
            end_time = datetime.fromisoformat(end_time)
        else:
            end_time = timezone.now()
        
        result = detect_anomalies_use_case.execute(
            device_metric_id=device_metric_id,
            start_time=start_time,
            end_time=end_time,
            algorithm=algorithm
        )
        
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': str(e),
            'success': False
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def metric_forecast_view(request):
    """
    Endpoint pour la prévision de métriques.
    
    Args:
        request: Requête HTTP
        
    Returns:
        Response avec les prévisions
    """
    try:
        # TODO: Implémenter la prévision de métriques
        from .di_container import resolve
        predict_metric_trend_use_case = resolve('PredictMetricTrendUseCase')
        
        # Récupérer les paramètres
        device_metric_id = request.data.get('device_metric_id')
        
        # Paramètres optionnels
        hours_ahead = request.data.get('hours_ahead', 24)
        algorithm = request.data.get('algorithm', 'auto')
        
        result = predict_metric_trend_use_case.execute(
            device_metric_id=device_metric_id,
            hours_ahead=hours_ahead,
            algorithm=algorithm
        )
        
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': str(e),
            'success': False
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 