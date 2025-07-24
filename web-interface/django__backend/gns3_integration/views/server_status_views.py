"""
Vues pour le statut temps réel du serveur GNS3.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from django.core.cache import cache
from django.utils import timezone
import asyncio
import logging

logger = logging.getLogger(__name__)


@swagger_auto_schema(
    method='get',
    operation_summary="Statut du serveur GNS3 en temps réel",
    operation_description="Récupère le statut en temps réel du serveur GNS3 avec détection automatique",
    tags=['GNS3 Integration'],
    manual_parameters=[
        openapi.Parameter(
            'force',
            openapi.IN_QUERY,
            description="Force une nouvelle vérification (true/false)",
            type=openapi.TYPE_BOOLEAN,
            default=False
        )
    ],
    responses={
        200: openapi.Response(
            description="Statut du serveur GNS3",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'is_available': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'version': openapi.Schema(type=openapi.TYPE_STRING),
                    'projects_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'last_check': openapi.Schema(type=openapi.TYPE_STRING),
                    'response_time_ms': openapi.Schema(type=openapi.TYPE_NUMBER),
                    'error_message': openapi.Schema(type=openapi.TYPE_STRING),
                    'server_mode': openapi.Schema(type=openapi.TYPE_STRING),
                    'detection_status': openapi.Schema(type=openapi.TYPE_STRING)
                }
            )
        ),
        500: "Erreur interne du serveur"
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def gns3_server_status(request):
    """
    Récupère le statut en temps réel du serveur GNS3.
    
    Utilise le service de détection automatique pour fournir
    des informations en temps réel sur la disponibilité du serveur.
    """
    try:
        # Vérifier si on force une nouvelle détection
        force_check = request.query_params.get('force', 'false').lower() == 'true'
        
        # Import dynamique pour éviter les erreurs de dépendance circulaire
        try:
            from ..infrastructure.gns3_detection_service import GNS3DetectionService
            from django.core.cache import cache
            
            # Créer un nouveau service pour éviter les problèmes de cache/SSL
            service = GNS3DetectionService()
            
            # Vider le cache si force_check
            if force_check:
                cache.delete(service.cache_key)
                cache.delete(service.notification_cache_key)
            
            # Obtenir le statut via le service de détection
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                gns3_status = loop.run_until_complete(service.check_server_availability())
            finally:
                loop.close()
                
        except ImportError as e:
            logger.error(f"Service de détection GNS3 non disponible: {e}")
            # Fallback avec vérification basique
            gns3_status = _basic_gns3_check()
        
        # Récupérer les métriques de monitoring
        monitoring_metrics = cache.get('gns3_monitoring_metrics', {})
        
        # Déterminer le mode de fonctionnement
        server_mode = 'real' if gns3_status.is_available else 'cached'
        detection_status = 'active' if gns3_status.is_available else 'failed'
        
        response_data = {
            'is_available': gns3_status.is_available,
            'version': gns3_status.version,
            'projects_count': gns3_status.projects_count,
            'last_check': gns3_status.last_check.isoformat() if gns3_status.last_check else None,
            'response_time_ms': gns3_status.response_time_ms,
            'error_message': gns3_status.error_message,
            'server_mode': server_mode,
            'detection_status': detection_status,
            'monitoring_metrics': {
                'consecutive_failures': monitoring_metrics.get('consecutive_failures', 0),
                'last_available': monitoring_metrics.get('last_available'),
                'uptime_percentage': monitoring_metrics.get('uptime_percentage', 0)
            }
        }
        
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du statut GNS3: {e}")
        return Response(
            {"error": f"Erreur lors de la récupération du statut: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_summary="Rapport de santé du serveur GNS3",
    operation_description="Génère un rapport de santé détaillé du serveur GNS3",
    tags=['GNS3 Integration'],
    responses={
        200: openapi.Response(
            description="Rapport de santé",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'generated_at': openapi.Schema(type=openapi.TYPE_STRING),
                    'server_status': openapi.Schema(type=openapi.TYPE_STRING),
                    'availability_score': openapi.Schema(type=openapi.TYPE_NUMBER),
                    'performance_score': openapi.Schema(type=openapi.TYPE_NUMBER),
                    'projects_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'recommendations': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING))
                }
            )
        ),
        500: "Erreur interne du serveur"
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def gns3_health_report(request):
    """
    Génère un rapport de santé détaillé du serveur GNS3.
    """
    try:
        # Récupérer le rapport de santé du cache
        report = cache.get('gns3_health_report')
        
        if not report:
            # Générer un rapport basique si pas en cache
            try:
                from ..infrastructure.gns3_detection_service import get_gns3_server_status
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    gns3_status = loop.run_until_complete(get_gns3_server_status())
                finally:
                    loop.close()
                    
            except ImportError:
                gns3_status = _basic_gns3_check()
            
            report = {
                'generated_at': timezone.now().isoformat(),
                'server_status': 'healthy' if gns3_status.is_available else 'unhealthy',
                'availability_score': 100 if gns3_status.is_available else 0,
                'performance_score': 100 if gns3_status.response_time_ms and gns3_status.response_time_ms < 1000 else 50,
                'projects_count': gns3_status.projects_count or 0,
                'recommendations': [
                    "Serveur GNS3 non disponible - Vérifier la configuration"
                ] if not gns3_status.is_available else []
            }
        
        return Response(report)
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération du rapport GNS3: {e}")
        return Response(
            {"error": f"Erreur lors de la génération du rapport: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _basic_gns3_check():
    """
    Vérification basique du serveur GNS3 sans dépendances.
    """
    import requests
    from datetime import datetime
    from dataclasses import dataclass
    
    @dataclass
    class BasicGNS3Status:
        is_available: bool
        last_check: datetime
        version: str = None
        projects_count: int = 0
        error_message: str = None
        response_time_ms: float = None
    
    try:
        import time
        start_time = time.time()
        
        response = requests.get(
            "http://localhost:3080/v2/version",
            timeout=5
        )
        
        response_time = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            version_data = response.json()
            
            # Essayer de récupérer les projets
            projects_count = 0
            try:
                projects_response = requests.get(
                    "http://localhost:3080/v2/projects",
                    timeout=5
                )
                if projects_response.status_code == 200:
                    projects_count = len(projects_response.json())
            except:
                pass
            
            return BasicGNS3Status(
                is_available=True,
                last_check=datetime.now(),
                version=version_data.get('version', 'Unknown'),
                projects_count=projects_count,
                response_time_ms=response_time
            )
        else:
            return BasicGNS3Status(
                is_available=False,
                last_check=datetime.now(),
                error_message=f"HTTP {response.status_code}"
            )
            
    except requests.exceptions.ConnectionError:
        return BasicGNS3Status(
            is_available=False,
            last_check=datetime.now(),
            error_message="Connexion refusée"
        )
    except requests.exceptions.Timeout:
        return BasicGNS3Status(
            is_available=False,
            last_check=datetime.now(),
            error_message="Timeout de connexion"
        )
    except Exception as e:
        return BasicGNS3Status(
            is_available=False,
            last_check=datetime.now(),
            error_message=str(e)
        )


@swagger_auto_schema(
    method='get',
    operation_summary="Projets GNS3 avec organisation multi-projets",
    operation_description="Liste les projets GNS3 avec détection automatique et organisation",
    tags=['GNS3 Integration'],
    manual_parameters=[
        openapi.Parameter(
            'group_by',
            openapi.IN_QUERY,
            description="Grouper par (status, created_date, name)",
            type=openapi.TYPE_STRING,
            default='status'
        )
    ],
    responses={
        200: openapi.Response(
            description="Liste organisée des projets",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'server_available': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'projects_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'groups': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'last_sync': openapi.Schema(type=openapi.TYPE_STRING)
                }
            )
        ),
        500: "Erreur interne du serveur"
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def gns3_projects_organized(request):
    """
    Liste les projets GNS3 avec organisation multi-projets.
    """
    try:
        group_by = request.query_params.get('group_by', 'status')
        
        # Vérifier la disponibilité du serveur
        try:
            from ..infrastructure.gns3_detection_service import get_gns3_server_status
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                server_status = loop.run_until_complete(get_gns3_server_status())
            finally:
                loop.close()
                
        except ImportError:
            server_status = _basic_gns3_check()
        
        response_data = {
            'server_available': server_status.is_available,
            'projects_count': 0,
            'groups': {},
            'last_sync': timezone.now().isoformat()
        }
        
        if server_status.is_available:
            # Récupérer les projets depuis le serveur GNS3
            try:
                import requests
                
                projects_response = requests.get(
                    "http://localhost:3080/v2/projects",
                    timeout=10
                )
                
                if projects_response.status_code == 200:
                    projects = projects_response.json()
                    response_data['projects_count'] = len(projects)
                    
                    # Organiser les projets selon le critère
                    groups = {}
                    for project in projects:
                        key = project.get(group_by, 'unknown')
                        
                        if key not in groups:
                            groups[key] = []
                        
                        groups[key].append({
                            'project_id': project.get('project_id'),
                            'name': project.get('name'),
                            'status': project.get('status'),
                            'created_at': project.get('created_at'),
                            'scene_height': project.get('scene_height'),
                            'scene_width': project.get('scene_width'),
                            'auto_start': project.get('auto_start'),
                            'auto_open': project.get('auto_open'),
                            'auto_close': project.get('auto_close')
                        })
                    
                    response_data['groups'] = groups
                    
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des projets: {e}")
                response_data['error'] = str(e)
        else:
            # Mode dégradé : récupérer depuis le cache ou la base
            cached_projects = cache.get('gns3_projects_sync', {})
            if cached_projects:
                response_data['projects_count'] = cached_projects.get('projects_count', 0)
                response_data['last_sync'] = cached_projects.get('timestamp')
                response_data['groups'] = {'cached': cached_projects.get('projects', [])}
        
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Erreur lors de l'organisation des projets: {e}")
        return Response(
            {"error": f"Erreur lors de l'organisation des projets: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='post',
    operation_summary="Tester le système de notifications GNS3",
    operation_description="""
    Envoie une notification de test sur le système Ubuntu.
    
    **Fonctionnalités :**
    - Test complet du système de notifications
    - Vérification de la disponibilité de notify-send
    - Notification avec icône et formatage approprié
    - Feedback sur le succès de l'opération
    
    **Notification envoyée :**
    - Titre : "🧪 Test NMS Backend"
    - Message informatif sur le test
    - Icône système et urgence faible
    - Durée d'affichage : 3 secondes
    """,
    tags=['GNS3 Integration'],
    responses={
        200: openapi.Response(
            description="Test de notification réussi",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Succès de l'opération"),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description="Message de retour"),
                    'notification_sent': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Notification envoyée avec succès")
                }
            )
        ),
        500: "Erreur lors du test de notification"
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_gns3_notifications(request):
    """
    Teste le système de notifications GNS3.
    """
    try:
        # Import dynamique
        from ..infrastructure.gns3_detection_service import test_notification_system
        
        # Exécuter le test de notification
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            notification_success = loop.run_until_complete(test_notification_system())
        finally:
            loop.close()
        
        return Response({
            'success': True,
            'message': 'Test de notification exécuté',
            'notification_sent': notification_success
        })
        
    except Exception as e:
        logger.error(f"Erreur lors du test de notifications: {e}")
        return Response(
            {"error": f"Erreur lors du test: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='post',
    operation_summary="Forcer détection GNS3 avec notification",
    operation_description="""
    Force une nouvelle détection du serveur GNS3 et envoie une notification système.
    
    **Fonctionnalités :**
    - Vide le cache de détection pour forcer une nouvelle vérification
    - Contacte directement le serveur GNS3 sur localhost:3080
    - Récupère les informations complètes (version, projets, performance)
    - Envoie une notification système Ubuntu détaillée
    
    **Types de notifications :**
    - ✅ **Succès** : Serveur détecté avec informations détaillées
    - ❌ **Échec** : Serveur indisponible avec diagnostic d'erreur
    
    **Informations collectées :**
    - Version du serveur GNS3
    - Nombre de projets disponibles
    - Temps de réponse en millisecondes
    - Statut de disponibilité
    """,
    tags=['GNS3 Integration'],
    responses={
        200: openapi.Response(
            description="Détection forcée avec notification",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'server_detected': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Serveur GNS3 détecté"),
                    'version': openapi.Schema(type=openapi.TYPE_STRING, description="Version du serveur GNS3"),
                    'projects_count': openapi.Schema(type=openapi.TYPE_INTEGER, description="Nombre de projets"),
                    'response_time_ms': openapi.Schema(type=openapi.TYPE_NUMBER, description="Temps de réponse (ms)"),
                    'error_message': openapi.Schema(type=openapi.TYPE_STRING, description="Message d'erreur si applicable"),
                    'notification_sent': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Notification envoyée"),
                    'last_check': openapi.Schema(type=openapi.TYPE_STRING, description="Horodatage de la vérification")
                }
            )
        ),
        500: "Erreur lors de la détection"
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def force_gns3_detection(request):
    """
    Force une détection GNS3 avec notification.
    """
    try:
        # Import dynamique
        from ..infrastructure.gns3_detection_service import force_gns3_detection_with_notification
        
        # Forcer la détection
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            gns3_status = loop.run_until_complete(force_gns3_detection_with_notification())
        finally:
            loop.close()
        
        return Response({
            'server_detected': gns3_status.is_available,
            'version': gns3_status.version,
            'projects_count': gns3_status.projects_count,
            'response_time_ms': gns3_status.response_time_ms,
            'error_message': gns3_status.error_message,
            'notification_sent': True,  # La notification est toujours tentée
            'last_check': gns3_status.last_check.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la détection forcée: {e}")
        return Response(
            {"error": f"Erreur lors de la détection: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_summary="Statut du système de notifications GNS3",
    operation_description="""
    Récupère les informations détaillées sur le système de notifications GNS3.
    
    **Informations retournées :**
    - État d'activation des notifications
    - Horodatage de la dernière notification envoyée
    - Statut de la dernière notification (succès/échec)
    - Statut du cache de notifications
    
    **Utilisation :**
    - Diagnostic du système de notifications
    - Vérification de la configuration
    - Suivi de l'activité des notifications
    - Débuggage des problèmes de notification
    """,
    tags=['GNS3 Integration'],
    responses={
        200: openapi.Response(
            description="Statut des notifications",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'notifications_enabled': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Notifications activées"),
                    'last_notification_sent': openapi.Schema(type=openapi.TYPE_STRING, description="Dernière notification envoyée"),
                    'last_notification_status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Statut dernière notification"),
                    'notification_cache_active': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Cache de notification actif")
                }
            )
        ),
        500: "Erreur lors de la récupération du statut"
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def gns3_notification_status(request):
    """
    Récupère le statut du système de notifications GNS3.
    """
    try:
        from ..infrastructure.gns3_detection_service import get_gns3_notification_status
        
        notification_status = get_gns3_notification_status()
        
        return Response(notification_status)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du statut notifications: {e}")
        return Response(
            {"error": f"Erreur: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='post',
    operation_summary="Activer/Désactiver notifications GNS3",
    operation_description="""
    Contrôle l'activation du système de notifications GNS3.
    
    **Paramètres :**
    - `enabled` : true pour activer, false pour désactiver
    
    **Fonctionnalités :**
    - Activation/désactivation globale des notifications
    - Configuration persistante pendant la session
    - Effet immédiat sur toutes les détections futures
    - Feedback de confirmation de l'état
    
    **Cas d'usage :**
    - Désactiver temporairement les notifications pendant la maintenance
    - Activer les notifications pour les tests et développement
    - Contrôle granulaire du système de notification
    """,
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'enabled': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Activer les notifications")
        },
        required=['enabled']
    ),
    tags=['GNS3 Integration'],
    responses={
        200: openapi.Response(
            description="Configuration mise à jour",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Succès de l'opération"),
                    'notifications_enabled': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="État des notifications"),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description="Message de confirmation")
                }
            )
        ),
        400: "Paramètres invalides"
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_gns3_notifications(request):
    """
    Active ou désactive les notifications GNS3.
    """
    try:
        enabled = request.data.get('enabled')
        
        if enabled is None:
            return Response(
                {"error": "Paramètre 'enabled' requis"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from ..infrastructure.gns3_detection_service import enable_gns3_notifications
        
        enable_gns3_notifications(enabled)
        
        return Response({
            'success': True,
            'notifications_enabled': enabled,
            'message': f"Notifications {'activées' if enabled else 'désactivées'}"
        })
        
    except Exception as e:
        logger.error(f"Erreur lors du toggle notifications: {e}")
        return Response(
            {"error": f"Erreur: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )