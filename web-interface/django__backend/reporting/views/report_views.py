from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
import logging

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..models import ReportTemplate, Report
from ..serializers import ReportSerializer, ReportTemplateSerializer
from ..di_container import resolve

logger = logging.getLogger(__name__)

class ReportViewSet(viewsets.ModelViewSet):
    """API ViewSet pour les rapports"""
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Injection des cas d'utilisation depuis notre nouveau module
        from ..application.use_cases import (
            GetReportUseCase, 
            ListReportsUseCase, 
            GenerateReportUseCase,
            DeleteReportUseCase
        )
        from ..application.report_distribution_use_cases import (
            DistributeReportUseCase,
            ScheduleReportDistributionUseCase
        )
        self.get_report_use_case = resolve(GetReportUseCase)
        self.list_reports_use_case = resolve(ListReportsUseCase)
        self.generate_report_use_case = resolve(GenerateReportUseCase)
        self.delete_report_use_case = resolve(DeleteReportUseCase)
        self.distribute_report_use_case = resolve(DistributeReportUseCase)
        self.schedule_report_distribution_use_case = resolve(ScheduleReportDistributionUseCase)
    
    def get_queryset(self):
        """
        Récupère les rapports en utilisant le cas d'utilisation approprié.
        Les filtres sont appliqués selon les paramètres de requête.
        """
        # Gestion Swagger : retourner un queryset vide si c'est une vue factice
        if getattr(self, 'swagger_fake_view', False):
            return Report.objects.none()
            
        # Construire le dictionnaire des filtres à partir des paramètres de requête
        filters = {}
        
        if self.request and 'report_type' in self.request.query_params:
            filters['report_type'] = self.request.query_params.get('report_type')
            
        if self.request and 'status' in self.request.query_params:
            filters['status'] = self.request.query_params.get('status')
            
        if self.request and 'created_by' in self.request.query_params:
            filters['created_by'] = self.request.query_params.get('created_by')
            
        if self.request and 'search' in self.request.query_params:
            filters['search'] = self.request.query_params.get('search')
        
        # Utiliser le cas d'utilisation pour obtenir les rapports
        reports = self.list_reports_use_case.execute(filters)
        
        # Retourner une liste simulée pour maintenir la compatibilité avec le ViewSet
        # Dans une vraie implémentation, on convertirait les dictionnaires en objets du modèle
        # ou on adapterait le ViewSet pour fonctionner avec les dictionnaires directement
        return Report.objects.filter(id__in=[r['id'] for r in reports])
    
    @swagger_auto_schema(
        operation_summary="Lister les rapports",
        operation_description="Récupère la liste des rapports avec filtres optionnels",
        manual_parameters=[
            openapi.Parameter('report_type', openapi.IN_QUERY, description='Type de rapport', type=openapi.TYPE_STRING),
            openapi.Parameter('status', openapi.IN_QUERY, description='Statut du rapport', type=openapi.TYPE_STRING),
            openapi.Parameter('created_by', openapi.IN_QUERY, description='Créé par', type=openapi.TYPE_STRING),
            openapi.Parameter('search', openapi.IN_QUERY, description='Recherche textuelle', type=openapi.TYPE_STRING)
        ],
        responses={
            200: openapi.Response(
                description="Liste des rapports",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_OBJECT)
                )
            )
        },
        tags=['Reporting']
    )
    def list(self, request, *args, **kwargs):
        """
        Liste les rapports avec filtres optionnels.
        """
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Récupérer un rapport",
        operation_description="Récupère les détails d'un rapport spécifique",
        responses={
            200: openapi.Response(
                description="Détails du rapport",
                schema=openapi.Schema(type=openapi.TYPE_OBJECT)
            ),
            404: openapi.Response(description="Rapport non trouvé")
        },
        tags=['Reporting']
    )
    def retrieve(self, request, *args, **kwargs):
        """
        Récupère un rapport spécifique en utilisant le cas d'utilisation.
        """
        pk = self.kwargs.get('pk')
        try:
            report = self.get_report_use_case.execute(int(pk))
            return Response(report)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
    
    @swagger_auto_schema(
        operation_summary="Créer un rapport",
        operation_description="Crée un nouveau rapport avec génération automatique",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'title': openapi.Schema(type=openapi.TYPE_STRING, description="Titre du rapport"),
                'report_type': openapi.Schema(type=openapi.TYPE_STRING, description="Type de rapport"),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description="Description"),
                'format': openapi.Schema(type=openapi.TYPE_STRING, description="Format de sortie")
            },
            required=['title', 'report_type']
        ),
        responses={
            201: openapi.Response(
                description="Rapport créé avec succès",
                schema=openapi.Schema(type=openapi.TYPE_OBJECT)
            ),
            400: openapi.Response(description="Données invalides")
        },
        tags=['Reporting']
    )
    def create(self, request, *args, **kwargs):
        """
        Crée un nouveau rapport en utilisant le cas d'utilisation.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Préparer les données
            report_type = serializer.validated_data.get('report_type')
            parameters = {
                'title': serializer.validated_data.get('title', f'Rapport {report_type}'),
                'description': serializer.validated_data.get('description', ''),
                'format': serializer.validated_data.get('format', 'pdf'),
                'template_id': serializer.validated_data.get('template_id')
            }
            # Ajouter les données spécifiques au type de rapport
            if 'content' in serializer.validated_data:
                parameters.update(serializer.validated_data.get('content', {}))
            
            # Créer le rapport avec génération
            report = self.generate_report_use_case.execute(
                report_type=report_type,
                parameters=parameters,
                user_id=request.user.id
            )
            
            return Response(report, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.exception(f"Erreur lors de la création du rapport: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_summary="Supprimer un rapport",
        operation_description="Supprime définitivement un rapport",
        responses={
            204: openapi.Response(description="Rapport supprimé avec succès"),
            404: openapi.Response(description="Rapport non trouvé"),
            400: openapi.Response(description="Erreur lors de la suppression")
        },
        tags=['Reporting']
    )
    def destroy(self, request, *args, **kwargs):
        """
        Supprime un rapport en utilisant le cas d'utilisation approprié.
        """
        pk = self.kwargs.get('pk')
        try:
            result = self.delete_report_use_case.execute(int(pk))
            if result:
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({'error': 'Erreur lors de la suppression'}, 
                                status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
    
    @swagger_auto_schema(
        method='post',
        operation_summary="Régénérer un rapport",
        operation_description="Régénère un rapport existant avec les mêmes paramètres",
        responses={
            200: openapi.Response(description="Rapport régénéré avec succès"),
            404: openapi.Response(description="Rapport non trouvé"),
            500: openapi.Response(description="Erreur lors de la régénération")
        },
        tags=['Reporting']
    )
    @action(detail=True, methods=['post'])
    def regenerate(self, request, pk=None):
        """Régénère un rapport"""
        try:
            # Récupérer le rapport
            report = self.get_report_use_case.execute(int(pk))
            
            # Régénérer avec les mêmes paramètres
            report_type = report.get('report_type')
            parameters = report.get('content', {})
            
            # Si le rapport est lié à un utilisateur, utiliser cet utilisateur, 
            # sinon l'utilisateur actuel
            user_id = report.get('created_by_id') or request.user.id
            
            new_report = self.generate_report_use_case.execute(
                report_type=report_type,
                parameters=parameters,
                user_id=user_id
            )
            
            return Response(new_report)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(f"Erreur lors de la régénération du rapport {pk}: {str(e)}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        method='post',
        operation_summary="Distribuer un rapport",
        operation_description="Distribue un rapport via différents canaux (email, Slack, webhook)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'channels': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                    description="Liste des canaux de distribution"
                ),
                'recipients': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description="Configuration des destinataires par canal"
                )
            },
            required=['channels']
        ),
        responses={
            200: openapi.Response(description="Distribution réussie"),
            404: openapi.Response(description="Rapport non trouvé"),
            400: openapi.Response(description="Données invalides"),
            500: openapi.Response(description="Erreur lors de la distribution")
        },
        tags=['Reporting']
    )
    @action(detail=True, methods=['post'])
    def distribute(self, request, pk=None):
        """
        Distribue un rapport via différents canaux.
        
        Exemple de payload:
        {
            "channels": ["email", "slack"],
            "recipients": {
                "email": [
                    {"address": "user@example.com", "name": "User Name"},
                    {"address": "user2@example.com"}
                ],
                "slack": [
                    {"channel": "#reports", "webhook_url": "https://..."},
                    {"webhook_url": "https://..."}
                ]
            }
        }
        """
        try:
            # Vérifier que le rapport existe
            report = self.get_report_use_case.execute(int(pk))
            
            # Valider les données d'entrée
            if 'channels' not in request.data or not isinstance(request.data['channels'], list):
                return Response(
                    {'error': 'La liste des canaux de distribution est requise'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            channels = request.data['channels']
            recipients = request.data.get('recipients', {})
            
            # Effectuer la distribution
            result = self.distribute_report_use_case.execute(
                report_id=int(pk),
                distribution_channels=channels,
                recipients=recipients
            )
            
            return Response(result)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(f"Erreur lors de la distribution du rapport {pk}: {str(e)}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        method='post',
        operation_summary="Planifier la distribution d'un rapport",
        operation_description="Planifie la distribution périodique d'un rapport",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'schedule': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Fréquence de planification (daily, weekly, monthly)"
                ),
                'channels': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                    description="Liste des canaux de distribution"
                ),
                'recipients': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description="Configuration des destinataires par canal"
                )
            },
            required=['schedule', 'channels']
        ),
        responses={
            200: openapi.Response(description="Planification créée avec succès"),
            400: openapi.Response(description="Données invalides"),
            500: openapi.Response(description="Erreur lors de la planification")
        },
        tags=['Reporting']
    )
    @action(detail=True, methods=['post'])
    def schedule_distribution(self, request, pk=None):
        """
        Planifie la distribution périodique d'un rapport.
        
        Exemple de payload:
        {
            "schedule": "weekly",
            "channels": ["email", "slack"],
            "recipients": {
                "email": [
                    {"address": "user@example.com", "name": "User Name"},
                    {"address": "user2@example.com"}
                ],
                "slack": [
                    {"channel": "#reports", "webhook_url": "https://..."},
                    {"webhook_url": "https://..."}
                ]
            }
        }
        """
        try:
            # Vérifier que le rapport existe
            report = self.get_report_use_case.execute(int(pk))
            
            # Valider les données d'entrée
            if 'schedule' not in request.data:
                return Response(
                    {'error': 'La fréquence de planification est requise'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            if 'channels' not in request.data or not isinstance(request.data['channels'], list):
                return Response(
                    {'error': 'La liste des canaux de distribution est requise'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            schedule = request.data['schedule']
            channels = request.data['channels']
            recipients = request.data.get('recipients', {})
            
            # Planifier la distribution
            result = self.schedule_report_distribution_use_case.execute(
                report_id=int(pk),
                schedule=schedule,
                distribution_channels=channels,
                recipients=recipients
            )
            
            return Response(result)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(f"Erreur lors de la planification de la distribution du rapport {pk}: {str(e)}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        method='get',
        operation_summary="Types de rapports disponibles",
        operation_description="Retourne la liste des types de rapports disponibles",
        responses={
            200: openapi.Response(
                description="Types de rapports",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'types': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'value': openapi.Schema(type=openapi.TYPE_STRING),
                                    'label': openapi.Schema(type=openapi.TYPE_STRING)
                                }
                            )
                        )
                    }
                )
            )
        },
        tags=['Reporting']
    )
    @action(detail=False, methods=['get'])
    def types(self, request):
        """Retourne les types de rapports disponibles"""
        return Response({
            'types': [
                {'value': 'security', 'label': 'Rapport de sécurité'},
                {'value': 'performance', 'label': 'Rapport de performance'},
                {'value': 'inventory', 'label': 'Rapport d\'inventaire'},
                {'value': 'audit', 'label': 'Rapport d\'audit'},
                {'value': 'custom', 'label': 'Rapport personnalisé'}
            ]
        })
    
    @swagger_auto_schema(
        method='get',
        operation_summary="Formats de rapports disponibles",
        operation_description="Retourne la liste des formats de rapports disponibles",
        responses={
            200: openapi.Response(
                description="Formats de rapports",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'formats': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'value': openapi.Schema(type=openapi.TYPE_STRING),
                                    'label': openapi.Schema(type=openapi.TYPE_STRING)
                                }
                            )
                        )
                    }
                )
            )
        },
        tags=['Reporting']
    )
    @action(detail=False, methods=['get'])
    def formats(self, request):
        """Retourne les formats de rapports disponibles"""
        return Response({
            'formats': [
                {'value': 'pdf', 'label': 'PDF'},
                {'value': 'csv', 'label': 'CSV'},
                {'value': 'json', 'label': 'JSON'},
                {'value': 'html', 'label': 'HTML'}
            ]
        })

    @swagger_auto_schema(
        method='get',
        operation_summary="Modèles de rapport disponibles",
        operation_description="Liste des modèles de rapport disponibles",
        responses={
            200: openapi.Response(
                description="Liste des modèles de rapport",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_OBJECT)
                )
            )
        },
        tags=['Reporting']
    )
    @action(detail=False, methods=['get'])
    def templates(self, request):
        """Liste des modèles de rapport disponibles."""
        templates = ReportTemplate.objects.all()
        serializer = ReportTemplateSerializer(templates, many=True)
        return Response(serializer.data)
        
    @swagger_auto_schema(
        method='get',
        operation_summary="Canaux de distribution disponibles",
        operation_description="Liste des canaux de distribution disponibles avec leur configuration",
        responses={
            200: openapi.Response(
                description="Canaux de distribution",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'channels': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'value': openapi.Schema(type=openapi.TYPE_STRING),
                                    'label': openapi.Schema(type=openapi.TYPE_STRING),
                                    'description': openapi.Schema(type=openapi.TYPE_STRING),
                                    'recipient_fields': openapi.Schema(
                                        type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(type=openapi.TYPE_OBJECT)
                                    )
                                }
                            )
                        )
                    }
                )
            )
        },
        tags=['Reporting']
    )
    @action(detail=False, methods=['get'], url_path='distribution-channels')
    def distribution_channels(self, request):
        """Liste des canaux de distribution disponibles."""
        return Response({
            'channels': [
                {
                    'value': 'email',
                    'label': 'Email',
                    'description': 'Distribution par email avec pièce jointe',
                    'recipient_fields': [
                        {'name': 'address', 'type': 'email', 'required': True, 'label': 'Adresse email'},
                        {'name': 'name', 'type': 'text', 'required': False, 'label': 'Nom du destinataire'}
                    ]
                },
                {
                    'value': 'slack',
                    'label': 'Slack',
                    'description': 'Distribution via Slack (webhook ou canal)',
                    'recipient_fields': [
                        {'name': 'webhook_url', 'type': 'url', 'required': True, 'label': 'URL du webhook Slack'},
                        {'name': 'channel', 'type': 'text', 'required': False, 'label': 'Canal Slack (ex: #rapports)'}
                    ]
                },
                {
                    'value': 'webhook',
                    'label': 'Webhook',
                    'description': 'Distribution via webhook personnalisé',
                    'recipient_fields': [
                        {'name': 'url', 'type': 'url', 'required': True, 'label': 'URL du webhook'},
                        {'name': 'method', 'type': 'select', 'required': False, 'label': 'Méthode HTTP',
                         'options': [
                             {'value': 'POST', 'label': 'POST'},
                             {'value': 'PUT', 'label': 'PUT'}
                         ],
                         'default': 'POST'
                        },
                        {'name': 'headers', 'type': 'json', 'required': False, 'label': 'En-têtes HTTP'}
                    ]
                },
                {
                    'value': 'telegram',
                    'label': 'Telegram',
                    'description': 'Distribution via Telegram Bot',
                    'recipient_fields': [
                        {'name': 'chat_id', 'type': 'text', 'required': False, 'label': 'Chat ID Telegram (optionnel)'},
                        {'name': 'username', 'type': 'text', 'required': False, 'label': 'Nom d\'utilisateur (pour référence)'}
                    ]
                }
            ]
        }) 