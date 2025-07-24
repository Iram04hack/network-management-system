"""
Vues API pour le module plugins.

Ce module implémente les endpoints REST pour la gestion des plugins.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from django.shortcuts import get_object_or_404
from security_management.models import SecurityAlert
from monitoring.models import Alert
from ..infrastructure.registry import PluginRegistry
from ..swagger_schema import plugin_operations, plugin_metadata_schema, plugin_list_response_schema, alert_handler_response_schema


class PluginViewSet(viewsets.ViewSet):
    """
    API pour interagir avec le système de plugins.
    
    Permet de lister les plugins disponibles, récupérer les détails d'un plugin
    et utiliser les plugins pour traiter des alertes.
    """
    
    @swagger_auto_schema(
        operation_description="Liste tous les plugins enregistrés, filtrable par type",
        operation_id=plugin_operations['list']['operation_id'],
        manual_parameters=plugin_operations['list']['parameters'],
        responses=plugin_operations['list']['responses'],
        tags=plugin_operations['list']['tags']
    )
    def list(self, request):
        """
        Liste tous les plugins enregistrés.
        
        Peut être filtré par type de plugin avec le paramètre de requête 'plugin_type'.
        """
        plugin_type = request.query_params.get('plugin_type')
        
        if plugin_type:
            plugin_classes = PluginRegistry.get_plugins(plugin_type)
        else:
            # Si aucun type n'est spécifié, collecte tous les types connus
            plugin_types = ['alert_handlers', 'dashboard_widgets', 'report_generators']
            plugin_classes = []
            for p_type in plugin_types:
                plugin_classes.extend(PluginRegistry.get_plugins(p_type))
        
        # Instancier les classes de plugins et récupérer leurs métadonnées
        plugins_metadata = []
        for plugin_class in plugin_classes:
            try:
                plugin = plugin_class()
                if hasattr(plugin, 'get_metadata'):
                    metadata = plugin.get_metadata()
                    plugins_metadata.append(metadata)
            except Exception as e:
                # Continuer si l'instanciation échoue
                plugins_metadata.append({
                    'id': plugin_class.__name__,
                    'name': plugin_class.__name__,
                    'error': str(e),
                    'status': 'error'
                })
        
        return Response(plugins_metadata)
    
    @swagger_auto_schema(
        operation_description="Récupère les détails d'un plugin spécifique",
        operation_id=plugin_operations['retrieve']['operation_id'],
        responses=plugin_operations['retrieve']['responses'],
        tags=plugin_operations['retrieve']['tags']
    )
    def retrieve(self, request, pk=None):
        """
        Récupère les détails d'un plugin spécifique.
        """
        # Parcourir tous les types de plugins connus
        plugin_types = ['alert_handlers', 'dashboard_widgets', 'report_generators']
        for plugin_type in plugin_types:
            plugin = PluginRegistry.get_plugin(plugin_type, pk)
            if plugin:
                if hasattr(plugin, 'get_metadata'):
                    return Response(plugin.get_metadata())
                return Response({
                    'id': plugin.__class__.__name__,
                    'name': pk
                })
        
        return Response(
            {'error': f'Plugin "{pk}" non trouvé'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    @swagger_auto_schema(
        operation_description="Traite une alerte avec les handlers appropriés",
        method='post',
        request_body=plugin_operations['handle_alert']['parameters'][0].schema,
        responses=plugin_operations['handle_alert']['responses'],
        tags=plugin_operations['handle_alert']['tags']
    )
    @action(detail=False, methods=['post'])
    def handle_alert(self, request):
        """
        Traite une alerte avec les handlers appropriés.
        
        Nécessite les données suivantes dans le corps de la requête:
        - alert_id: ID de l'alerte à traiter
        - alert_type: Type d'alerte ('security' ou 'monitoring')
        """
        alert_id = request.data.get('alert_id')
        alert_type = request.data.get('alert_type')
        
        if not alert_id or not alert_type:
            return Response(
                {'error': 'Les paramètres alert_id et alert_type sont requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Récupérer l'alerte selon son type
            if alert_type == 'security':
                alert = get_object_or_404(SecurityAlert, pk=alert_id)
            elif alert_type == 'monitoring':
                alert = get_object_or_404(Alert, pk=alert_id)
            else:
                return Response(
                    {'error': f'Type d\'alerte inconnu: {alert_type}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Accéder au service de gestion des plugins
            from common.application.services.plugin_service import PluginService
            plugin_service = PluginService()
            
            # Traiter l'alerte avec tous les handlers disponibles
            results = plugin_service.handle_alert(alert)
            return Response(results)
            
        except Exception as e:
            return Response(
                {'error': f'Erreur lors du traitement de l\'alerte: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 