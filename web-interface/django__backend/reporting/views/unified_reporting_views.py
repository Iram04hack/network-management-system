"""
Vues pour le service unifié de reporting avec intégration GNS3.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import logging

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..infrastructure.unified_reporting_service import unified_reporting_service

logger = logging.getLogger(__name__)

@swagger_auto_schema(
    method='get',
    operation_summary="Tableau de bord reporting unifié",
    operation_description="Récupère les données du tableau de bord avec intégration GNS3",
    responses={
        200: openapi.Response(
            description="Données du tableau de bord",
            schema=openapi.Schema(type=openapi.TYPE_OBJECT)
        )
    },
    tags=['Reporting Unifié']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def unified_dashboard(request):
    """Tableau de bord reporting unifié avec données GNS3."""
    try:
        dashboard_data = unified_reporting_service.get_reporting_dashboard()
        return Response(dashboard_data)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du dashboard unifié: {e}")
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='post',
    operation_summary="Génération de rapport unifié",
    operation_description="Génère un rapport avec données de multiples sources",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'report_type': openapi.Schema(type=openapi.TYPE_STRING, description="Type de rapport"),
            'format': openapi.Schema(type=openapi.TYPE_STRING, description="Format de sortie"),
            'include_topology': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Inclure données topologiques"),
            'include_performance': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Inclure données de performance"),
            'include_security_audit': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Inclure audit de sécurité"),
            'include_inventory': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Inclure inventaire"),
            'project_id': openapi.Schema(type=openapi.TYPE_STRING, description="ID du projet GNS3 (optionnel)"),
            'parameters': openapi.Schema(type=openapi.TYPE_OBJECT, description="Paramètres spécifiques")
        },
        required=['report_type', 'format']
    ),
    responses={
        201: openapi.Response(description="Rapport généré avec succès"),
        400: openapi.Response(description="Données invalides"),
        500: openapi.Response(description="Erreur lors de la génération")
    },
    tags=['Reporting Unifié']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_unified_report(request):
    """Génère un rapport unifié avec données de multiples sources."""
    try:
        report_config = request.data
        
        # Validation de base
        if not report_config.get('report_type'):
            return Response(
                {'error': 'Le type de rapport est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not report_config.get('format'):
            return Response(
                {'error': 'Le format est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Générer le rapport
        result = unified_reporting_service.generate_unified_report(report_config)
        
        return Response(result, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération du rapport unifié: {e}")
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='post',
    operation_summary="Distribution multi-canal",
    operation_description="Distribue un rapport via les canaux spécifiés (email, Slack, webhook, Telegram)",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'report_info': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                description="Informations du rapport",
                properties={
                    'id': openapi.Schema(type=openapi.TYPE_STRING),
                    'title': openapi.Schema(type=openapi.TYPE_STRING),
                    'report_type': openapi.Schema(type=openapi.TYPE_STRING),
                    'file_path': openapi.Schema(type=openapi.TYPE_STRING),
                    'url': openapi.Schema(type=openapi.TYPE_STRING),
                    'created_at': openapi.Schema(type=openapi.TYPE_STRING)
                }
            ),
            'channels': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_STRING),
                description="Liste des canaux: email, slack, webhook, telegram"
            ),
            'recipients': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                description="Configuration des destinataires par canal",
                properties={
                    'email': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'address': openapi.Schema(type=openapi.TYPE_STRING),
                                'name': openapi.Schema(type=openapi.TYPE_STRING)
                            }
                        )
                    ),
                    'telegram': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'chat_id': openapi.Schema(type=openapi.TYPE_STRING),
                                'username': openapi.Schema(type=openapi.TYPE_STRING)
                            }
                        )
                    ),
                    'slack': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'webhook_url': openapi.Schema(type=openapi.TYPE_STRING),
                                'channel': openapi.Schema(type=openapi.TYPE_STRING)
                            }
                        )
                    ),
                    'webhook': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'url': openapi.Schema(type=openapi.TYPE_STRING),
                                'method': openapi.Schema(type=openapi.TYPE_STRING),
                                'headers': openapi.Schema(type=openapi.TYPE_OBJECT)
                            }
                        )
                    )
                }
            )
        },
        required=['report_info', 'channels', 'recipients']
    ),
    responses={
        200: openapi.Response(description="Distribution réussie"),
        400: openapi.Response(description="Données invalides"),
        500: openapi.Response(description="Erreur lors de la distribution")
    },
    tags=['Reporting Unifié']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def distribute_report(request):
    """Distribue un rapport via les canaux spécifiés."""
    try:
        report_info = request.data.get('report_info')
        channels = request.data.get('channels', [])
        recipients = request.data.get('recipients', {})
        
        # Validation
        if not report_info:
            return Response(
                {'error': 'Les informations du rapport sont requises'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not channels:
            return Response(
                {'error': 'Au moins un canal de distribution est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Préparer la configuration de distribution
        distribution_config = {
            'channels': channels,
            'recipients': recipients
        }
        
        # Distribuer le rapport
        result = unified_reporting_service.distribute_report(report_info, distribution_config)
        
        return Response(result)
        
    except Exception as e:
        logger.error(f"Erreur lors de la distribution: {e}")
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='get',
    operation_summary="Canaux de distribution disponibles",
    operation_description="Retourne la liste des canaux de distribution avec leurs configurations",
    responses={
        200: openapi.Response(
            description="Liste des canaux disponibles",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'channels': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_OBJECT)
                    )
                }
            )
        )
    },
    tags=['Reporting Unifié']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def available_channels(request):
    """Liste des canaux de distribution disponibles."""
    try:
        channels = unified_reporting_service.get_available_distribution_channels()
        return Response({'channels': channels})
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des canaux: {e}")
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='post',
    operation_summary="Test de distribution",
    operation_description="Teste la distribution sur un canal spécifique",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'channel': openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Canal à tester: email, telegram, slack, webhook"
            ),
            'recipients': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_OBJECT),
                description="Liste des destinataires de test"
            )
        },
        required=['channel', 'recipients']
    ),
    responses={
        200: openapi.Response(description="Test réussi"),
        400: openapi.Response(description="Données invalides"),
        500: openapi.Response(description="Erreur lors du test")
    },
    tags=['Reporting Unifié']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_distribution(request):
    """Teste la distribution sur un canal spécifique."""
    try:
        channel = request.data.get('channel')
        recipients = request.data.get('recipients', [])
        
        if not channel:
            return Response(
                {'error': 'Le canal est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not recipients:
            return Response(
                {'error': 'Au moins un destinataire est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Créer un rapport de test
        test_report = {
            'id': 'test-001',
            'title': 'Rapport de test de distribution',
            'report_type': 'test',
            'description': 'Test de la distribution multi-canal',
            'created_at': '2025-01-09T10:00:00Z',
            'file_path': '/tmp/test_report.pdf',  # Fichier fictif
            'url': 'https://example.com/test-report',
            'file_size': 1024 * 512  # 512KB
        }
        
        # Configuration de distribution
        distribution_config = {
            'channels': [channel],
            'recipients': {channel: recipients}
        }
        
        # Tester la distribution
        result = unified_reporting_service.distribute_report(test_report, distribution_config)
        
        return Response({
            'test_completed': True,
            'channel_tested': channel,
            'recipients_count': len(recipients),
            'distribution_result': result
        })
        
    except Exception as e:
        logger.error(f"Erreur lors du test de distribution: {e}")
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )