"""
Vues pour la gestion des dashboards personnalisés.

Ce module contient les vues pour créer, modifier et gérer
les dashboards personnalisés des utilisateurs.
"""

import json
import logging
from typing import Dict, Any, List
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from datetime import date
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..models import CustomDashboard, DashboardViewLog
from ..domain.entities import DashboardOverview
from ..application.use_cases import GetDashboardOverviewUseCase
from dashboard.di_container import container

logger = logging.getLogger(__name__)


class CustomDashboardView(APIView):
    """
    Vue pour la gestion des dashboards personnalisés.
    
    Permet aux utilisateurs de créer, modifier et gérer leurs propres
    configurations de dashboard.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Récupérer les dashboards personnalisés",
        operation_description="Récupère la liste des dashboards de l'utilisateur ou un dashboard spécifique",
        responses={
            200: openapi.Response(
                description="Dashboard ou liste des dashboards",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'dashboards': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                        'total': openapi.Schema(type=openapi.TYPE_INTEGER)
                    }
                )
            ),
            404: "Dashboard non trouvé"
        },
        tags=['Dashboard']
    )
    def get(self, request, dashboard_id=None):
        """
        Récupérer un dashboard personnalisé ou la liste des dashboards de l'utilisateur.
        
        Args:
            dashboard_id: ID du dashboard spécifique (optionnel)
            
        Returns:
            Configuration du dashboard ou liste des dashboards
        """
        try:
            user = request.user
            
            if dashboard_id:
                # Récupérer un dashboard spécifique
                dashboard = get_object_or_404(
                    CustomDashboard,
                    id=dashboard_id,
                    owner=user
                )
                
                # Enregistrer les statistiques d'accès
                self._record_dashboard_access(dashboard)
                
                # Enrichir avec les données en temps réel
                dashboard_config = self._dashboard_to_dict(dashboard)
                enriched_dashboard = self._enrich_dashboard_with_data(dashboard_config)
                return Response(enriched_dashboard)
            else:
                # Récupérer la liste des dashboards de l'utilisateur
                dashboards = CustomDashboard.objects.filter(
                    owner=user
                ).order_by('-updated_at')
                
                dashboards_data = [
                    self._dashboard_to_summary(dashboard) 
                    for dashboard in dashboards
                ]
                
                return Response({
                    'dashboards': dashboards_data,
                    'total': len(dashboards_data)
                })
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du dashboard: {e}")
            return Response(
                {'error': 'Erreur lors de la récupération du dashboard'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        operation_summary="Créer un dashboard personnalisé",
        operation_description="Crée un nouveau dashboard personnalisé avec widgets et configuration",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description="Nom du dashboard"),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description="Description du dashboard"),
                'layout': openapi.Schema(type=openapi.TYPE_OBJECT, description="Configuration de la mise en page"),
                'filters': openapi.Schema(type=openapi.TYPE_OBJECT, description="Filtres par défaut"),
                'refresh_interval': openapi.Schema(type=openapi.TYPE_INTEGER, description="Intervalle de rafraîchissement en secondes")
            },
            required=['name']
        ),
        responses={
            201: openapi.Response(description="Dashboard créé avec succès"),
            400: "Données invalides"
        },
        tags=['Dashboard']
    )
    def post(self, request):
        """
        Créer un nouveau dashboard personnalisé.
        
        Body:
            {
                "name": "Mon Dashboard",
                "description": "Description du dashboard",
                "layout": {
                    "widgets": [...],
                    "grid": {...}
                },
                "filters": {...},
                "refresh_interval": 30
            }
            
        Returns:
            Configuration du dashboard créé
        """
        try:
            user = request.user
            data = request.data
            
            # Valider les données
            validation_errors = self._validate_dashboard_data(data)
            if validation_errors:
                return Response(
                    {'errors': validation_errors}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Créer le dashboard
            dashboard = CustomDashboard(
                owner=user,
                name=data.get('name'),
                description=data.get('description', ''),
                layout=data.get('layout', {}),
                refresh_interval=data.get('refresh_interval', 30)
            )
            
            # Sauvegarder avec validation
            dashboard.save()
            
            # Retourner les données du dashboard créé
            dashboard_dict = self._dashboard_to_dict(dashboard)
            return Response(dashboard_dict, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            return Response(
                {'errors': e.message_dict if hasattr(e, 'message_dict') else str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Erreur lors de la création du dashboard: {e}")
            return Response(
                {'error': 'Erreur lors de la création du dashboard'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        operation_summary="Mettre à jour un dashboard personnalisé",
        operation_description="Met à jour un dashboard personnalisé existant (modification partielle autorisée)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description="Nom du dashboard"),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description="Description du dashboard"),
                'layout': openapi.Schema(type=openapi.TYPE_OBJECT, description="Configuration de la mise en page"),
                'filters': openapi.Schema(type=openapi.TYPE_OBJECT, description="Filtres par défaut"),
                'refresh_interval': openapi.Schema(type=openapi.TYPE_INTEGER, description="Intervalle de rafraîchissement en secondes")
            }
        ),
        responses={
            200: openapi.Response(description="Dashboard mis à jour avec succès"),
            400: "Données invalides",
            404: "Dashboard non trouvé"
        },
        tags=['Dashboard']
    )
    def put(self, request, dashboard_id):
        """
        Mettre à jour un dashboard personnalisé existant.
        
        Args:
            dashboard_id: ID du dashboard à modifier
            
        Body:
            Mêmes champs que POST (partiels autorisés)
            
        Returns:
            Configuration du dashboard mise à jour
        """
        try:
            user = request.user
            data = request.data
            
            # Récupérer le dashboard existant
            dashboard = get_object_or_404(
                CustomDashboard,
                id=dashboard_id,
                owner=user
            )
            
            # Valider les données (mise à jour partielle)
            validation_errors = self._validate_dashboard_data(data, partial=True)
            if validation_errors:
                return Response(
                    {'errors': validation_errors}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Mettre à jour les champs fournis
            if 'name' in data:
                dashboard.name = data['name']
            if 'description' in data:
                dashboard.description = data['description']
            if 'layout' in data:
                dashboard.layout_config = data['layout']
            if 'filters' in data:
                dashboard.filters_config = data['filters']
            if 'refresh_interval' in data:
                dashboard.refresh_interval = data['refresh_interval']
            
            # Sauvegarder avec validation
            dashboard.save()
            
            # Retourner les données mises à jour
            dashboard_dict = self._dashboard_to_dict(dashboard)
            return Response(dashboard_dict)
            
        except ValidationError as e:
            return Response(
                {'errors': e.message_dict if hasattr(e, 'message_dict') else str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du dashboard: {e}")
            return Response(
                {'error': 'Erreur lors de la mise à jour du dashboard'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        operation_summary="Supprimer un dashboard personnalisé",
        operation_description="Supprime définitivement un dashboard personnalisé de l'utilisateur",
        responses={
            204: openapi.Response(description="Dashboard supprimé avec succès"),
            404: "Dashboard non trouvé"
        },
        tags=['Dashboard']
    )
    def delete(self, request, dashboard_id):
        """
        Supprimer un dashboard personnalisé.
        
        Args:
            dashboard_id: ID du dashboard à supprimer
            
        Returns:
            Confirmation de suppression
        """
        try:
            user = request.user
            
            # Récupérer le dashboard existant
            dashboard = get_object_or_404(
                CustomDashboard,
                id=dashboard_id,
                owner=user
            )
            
            # Marquer comme inactif plutôt que supprimer (soft delete)
            dashboard.is_active = False
            dashboard.save()
            
            return Response({
                'message': 'Dashboard supprimé avec succès',
                'dashboard_id': dashboard_id
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du dashboard: {e}")
            return Response(
                {'error': 'Erreur lors de la suppression du dashboard'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _validate_dashboard_data(self, data: Dict[str, Any], partial: bool = False) -> List[str]:
        """
        Valide les données du dashboard.
        
        Args:
            data: Données à valider
            partial: Si True, validation partielle (pour les mises à jour)
            
        Returns:
            Liste des erreurs de validation
        """
        errors = []
        
        if not partial:
            # Validation complète pour la création
            if not data.get('name'):
                errors.append("Le nom du dashboard est requis")
            
            if not data.get('layout'):
                errors.append("La configuration de layout est requise")
        
        # Validations communes
        if 'name' in data:
            name = data['name']
            if not isinstance(name, str) or len(name.strip()) == 0:
                errors.append("Le nom du dashboard doit être une chaîne non vide")
            elif len(name) > 100:
                errors.append("Le nom du dashboard ne peut pas dépasser 100 caractères")
        
        if 'refresh_interval' in data:
            interval = data['refresh_interval']
            if not isinstance(interval, int) or interval < 5 or interval > 300:
                errors.append("L'intervalle de rafraîchissement doit être entre 5 et 300 secondes")
        
        if 'layout' in data:
            layout = data['layout']
            if not isinstance(layout, dict):
                errors.append("La configuration de layout doit être un objet")
            else:
                # Valider la structure du layout
                layout_errors = self._validate_layout_structure(layout)
                errors.extend(layout_errors)
        
        return errors
    
    def _validate_layout_structure(self, layout: Dict[str, Any]) -> List[str]:
        """
        Valide la structure du layout du dashboard.
        
        Args:
            layout: Configuration du layout
            
        Returns:
            Liste des erreurs de validation
        """
        errors = []
        
        if 'widgets' not in layout:
            errors.append("La configuration des widgets est requise dans le layout")
        elif not isinstance(layout['widgets'], list):
            errors.append("Les widgets doivent être une liste")
        else:
            # Valider chaque widget
            for i, widget in enumerate(layout['widgets']):
                if not isinstance(widget, dict):
                    errors.append(f"Le widget {i} doit être un objet")
                    continue
                
                if 'type' not in widget:
                    errors.append(f"Le widget {i} doit avoir un type")
                
                if 'position' not in widget:
                    errors.append(f"Le widget {i} doit avoir une position")
                
                # Valider les types de widgets supportés
                supported_types = [
                    'device_summary', 'alert_list', 'performance_chart',
                    'network_topology', 'health_metrics', 'qos_summary'
                ]
                if widget.get('type') not in supported_types:
                    errors.append(f"Type de widget non supporté: {widget.get('type')}")
        
        return errors
    
    def _enrich_dashboard_with_data(self, dashboard_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrichit la configuration du dashboard avec les données en temps réel.
        
        Args:
            dashboard_config: Configuration du dashboard
            
        Returns:
            Dashboard enrichi avec les données
        """
        try:
            # Récupérer les données via les cas d'utilisation
            dashboard_use_case = container.get_service('dashboard_service')
            
            # Obtenir les données de base
            import asyncio
            
            async def get_dashboard_data():
                return await dashboard_use_case.get_dashboard_overview()
            
            dashboard_data = asyncio.run(get_dashboard_data())
            
            # Convertir en dictionnaire si nécessaire
            if hasattr(dashboard_data, '__dict__'):
                dashboard_data = {
                    'devices': {
                        'total': getattr(dashboard_data, 'total_devices', 0),
                        'active': getattr(dashboard_data, 'active_devices', 0)
                    },
                    'security_alerts': getattr(dashboard_data, 'recent_alerts', []),
                    'system_alerts': [],
                    'health_metrics': {
                        'cpu_usage': getattr(dashboard_data.system_health, 'cpu_usage', 0) if hasattr(dashboard_data, 'system_health') else 0,
                        'memory_usage': getattr(dashboard_data.system_health, 'memory_usage', 0) if hasattr(dashboard_data, 'system_health') else 0,
                        'disk_usage': getattr(dashboard_data.system_health, 'disk_usage', 0) if hasattr(dashboard_data, 'system_health') else 0,
                        'network_load': getattr(dashboard_data.system_health, 'network_load', 0) if hasattr(dashboard_data, 'system_health') else 0
                    }
                }
            
            # Enrichir selon les widgets configurés
            enriched_config = dashboard_config.copy()
            enriched_config['data'] = {}
            
            for widget in dashboard_config.get('layout', {}).get('widgets', []):
                widget_type = widget.get('type')
                widget_data = self._get_widget_data(widget_type, dashboard_data, widget.get('config', {}))
                enriched_config['data'][widget.get('id', widget_type)] = widget_data
            
            return enriched_config
            
        except Exception as e:
            logger.error(f"Erreur lors de l'enrichissement du dashboard: {e}")
            # Retourner la configuration sans données en cas d'erreur
            return dashboard_config
    
    def _get_widget_data(self, widget_type: str, dashboard_data: Dict[str, Any], widget_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Récupère les données spécifiques à un type de widget.
        
        Args:
            widget_type: Type du widget
            dashboard_data: Données globales du dashboard
            widget_config: Configuration spécifique du widget
            
        Returns:
            Données formatées pour le widget
        """
        if widget_type == 'device_summary':
            return dashboard_data.get('devices', {})
        
        elif widget_type == 'alert_list':
            alerts = dashboard_data.get('security_alerts', []) + dashboard_data.get('system_alerts', [])
            # Trier par timestamp et limiter
            limit = widget_config.get('limit', 10)
            sorted_alerts = sorted(alerts, key=lambda x: x.get('timestamp', ''), reverse=True)
            return {'alerts': sorted_alerts[:limit]}
        
        elif widget_type == 'performance_chart':
            return dashboard_data.get('performance', {})
        
        elif widget_type == 'health_metrics':
            return dashboard_data.get('health_metrics', {})
        
        elif widget_type == 'qos_summary':
            # Récupérer les données QoS depuis le dashboard réseau
            try:
                import asyncio
                network_use_case = container.get_service('network_overview_service')
                
                async def get_network_data():
                    return await network_use_case.get_network_overview()
                
                network_data = asyncio.run(get_network_data())
                
                # Extraire les données QoS de l'objet NetworkOverview
                qos_data = {
                    'total_policies': getattr(network_data, 'qos_policies', 0),
                    'active_policies': getattr(network_data, 'active_qos_policies', 0)
                }
                return qos_data
            except Exception:
                return {}
        
        else:
            return {}
    
    def _dashboard_to_dict(self, dashboard: CustomDashboard) -> Dict[str, Any]:
        """
        Convertit un objet CustomDashboard en dictionnaire.

        Args:
            dashboard: Instance de CustomDashboard

        Returns:
            Dictionnaire représentant le dashboard
        """
        return {
            'id': str(dashboard.id),
            'name': dashboard.name,
            'description': dashboard.description,
            'layout': dashboard.layout,
            'is_default': dashboard.is_default,
            'owner': dashboard.owner.username,
            'created_at': dashboard.created_at.isoformat(),
            'updated_at': dashboard.updated_at.isoformat(),
            'is_public': dashboard.is_public
        }
    
    def _dashboard_to_summary(self, dashboard: CustomDashboard) -> Dict[str, Any]:
        """
        Convertit un dashboard en résumé pour les listes.

        Args:
            dashboard: Instance de CustomDashboard

        Returns:
            Résumé du dashboard
        """
        return {
            'id': dashboard.id,
            'name': dashboard.name,
            'description': dashboard.description,
            'widget_count': dashboard.get_widget_count(),
            'widget_types': dashboard.get_widget_types(),
            'refresh_interval': dashboard.refresh_interval,
            'is_default': dashboard.is_default,
            'created_at': dashboard.created_at.isoformat(),
            'updated_at': dashboard.updated_at.isoformat()
        }
    
    def _record_dashboard_access(self, dashboard: CustomDashboard):
        """
        Enregistre l'accès à un dashboard pour les statistiques.

        Args:
            dashboard: Dashboard accédé
        """
        try:
            # Créer un log de vue
            DashboardViewLog.objects.create(
                user=dashboard.owner,
                dashboard=dashboard
            )
        except Exception as e:
            # Ne pas faire échouer la requête pour un problème de stats
            logger.warning(f"Erreur lors de l'enregistrement des stats: {e}")


class DashboardStatsView(APIView):
    """
    Vue pour récupérer les statistiques d'utilisation des dashboards.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Statistiques d'utilisation des dashboards",
        operation_description="Récupère les statistiques d'utilisation des dashboards personnalisés (accès, durée, fréquence) pour l'utilisateur connecté",
        manual_parameters=[
            openapi.Parameter(
                'dashboard_id',
                openapi.IN_QUERY,
                description="ID du dashboard spécifique (optionnel - si omis, retourne les stats de tous les dashboards)",
                type=openapi.TYPE_INTEGER,
                required=False
            )
        ],
        responses={
            200: openapi.Response(
                description="Statistiques récupérées avec succès",
                examples={
                    "application/json": {
                        "user_dashboard_stats": [
                            {
                                "dashboard_id": "1",
                                "dashboard_name": "Mon Dashboard",
                                "total_views_last_7_days": 15,
                                "last_accessed": "2025-06-29T12:00:00Z"
                            }
                        ],
                        "total_dashboards": 3
                    }
                }
            ),
            401: "Non authentifié",
            500: "Erreur serveur"
        },
        tags=['Dashboard']
    )
    def get(self, request, dashboard_id=None):
        """
        Récupérer les statistiques d'un dashboard ou de tous les dashboards.
        
        Args:
            dashboard_id: ID du dashboard (optionnel)
            
        Returns:
            Statistiques d'utilisation
        """
        try:
            user = request.user
            
            if dashboard_id:
                # Stats pour un dashboard spécifique
                dashboard = get_object_or_404(
                    CustomDashboard,
                    id=dashboard_id,
                    owner=user
                )

                stats = DashboardViewLog.objects.filter(
                    dashboard=dashboard
                ).order_by('-timestamp')[:30]  # 30 derniers jours
                
                return Response({
                    'dashboard_id': dashboard_id,
                    'dashboard_name': dashboard.name,
                    'stats': [
                        {
                            'timestamp': stat.timestamp.isoformat(),
                            'user': stat.user.username if stat.user else 'Anonymous',
                            'duration': stat.duration
                        }
                        for stat in stats
                    ]
                })
            else:
                # Stats globales pour l'utilisateur
                dashboards = CustomDashboard.objects.filter(
                    owner=user
                )

                dashboard_stats = []
                for dashboard in dashboards:
                    recent_stats = DashboardViewLog.objects.filter(
                        dashboard=dashboard
                    ).order_by('-timestamp')[:7]  # 7 derniers jours
                    
                    total_views = len(recent_stats)

                    dashboard_stats.append({
                        'dashboard_id': str(dashboard.id),
                        'dashboard_name': dashboard.name,
                        'total_views_last_7_days': total_views,
                        'last_accessed': recent_stats[0].timestamp.isoformat() if recent_stats else None
                    })
                
                return Response({
                    'user_dashboard_stats': dashboard_stats,
                    'total_dashboards': len(dashboard_stats)
                })
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des statistiques: {e}")
            return Response(
                {'error': 'Erreur lors de la récupération des statistiques'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )