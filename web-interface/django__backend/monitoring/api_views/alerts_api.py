"""
Vues API pour la gestion des alertes.
"""

from typing import List, Dict, Any

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..di_container import resolve
from ..domain.interfaces.repositories import AlertRepository
from ..domain.services import NotificationService
from ..use_cases.alert_use_cases import AlertUseCase
from ..serializers.alert_serializers import AlertSerializer


class AlertViewSet(viewsets.ViewSet):
    """Vue API pour la gestion des alertes."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.repository = resolve('alert_repository')()
        self.notification_service = resolve('notification_service')()
        self.use_case = AlertUseCase(self.repository, self.notification_service)
    
    @swagger_auto_schema(
        operation_summary="Liste des alertes",
        operation_description="Récupère la liste des alertes avec filtres optionnels par statut, sévérité et équipement.",
        tags=['Monitoring'],
        manual_parameters=[
            openapi.Parameter('status', openapi.IN_QUERY, description="Filtrer par statut", type=openapi.TYPE_STRING),
            openapi.Parameter('severity', openapi.IN_QUERY, description="Filtrer par sévérité", type=openapi.TYPE_STRING),
            openapi.Parameter('device_id', openapi.IN_QUERY, description="Filtrer par ID d'équipement", type=openapi.TYPE_INTEGER),
        ],
        responses={
            200: openapi.Response(
                description='Liste des alertes',
                schema=AlertSerializer
            ),
            401: "Non authentifié"
        }
    )
    def list(self, request: Request) -> Response:
        """Liste toutes les alertes."""
        # Extraire les filtres de la requête
        filters = {}
        if 'status' in request.query_params:
            filters['status'] = request.query_params['status']
        if 'severity' in request.query_params:
            filters['severity'] = request.query_params['severity']
        if 'device_id' in request.query_params:
            filters['device_id'] = int(request.query_params['device_id'])
        
        # Récupérer les alertes
        alerts = self.use_case.list_alerts(filters)
        
        # Sérialiser les résultats
        serializer = AlertSerializer(alerts, many=True)
        
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_summary="Détails d'une alerte",
        operation_description="Récupère les détails d'une alerte spécifique par son ID.",
        tags=['Monitoring'],
        responses={
            200: openapi.Response(
                description='Détails de l\'alerte',
                schema=AlertSerializer()
            ),
            404: "Alerte non trouvée",
            401: "Non authentifié"
        }
    )
    def retrieve(self, request: Request, pk=None) -> Response:
        """Récupère une alerte par son ID."""
        try:
            alert = self.use_case.get_alert(int(pk))
            serializer = AlertSerializer(alert)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    
    @swagger_auto_schema(
        operation_summary="Créer une alerte",
        operation_description="Crée une nouvelle alerte dans le système de monitoring.",
        tags=['Monitoring'],
        request_body=AlertSerializer,
        responses={
            201: openapi.Response(
                description='Alerte créée',
                schema=AlertSerializer()
            ),
            400: "Données invalides",
            401: "Non authentifié"
        }
    )
    def create(self, request: Request) -> Response:
        """Crée une nouvelle alerte."""
        # Valider les données d'entrée
        serializer = AlertSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Créer l'alerte
        try:
            alert = self.use_case.create_alert(
                title=serializer.validated_data['title'],
                severity=serializer.validated_data['severity'],
                status=serializer.validated_data.get('status', 'active'),
                description=serializer.validated_data.get('description'),
                source_type=serializer.validated_data.get('source_type'),
                source_id=serializer.validated_data.get('source_id'),
                device_id=serializer.validated_data.get('device_id'),
                details=serializer.validated_data.get('details')
            )
            
            # Sérialiser la réponse
            response_serializer = AlertSerializer(alert)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_summary="Modifier une alerte",
        operation_description="Met à jour complètement une alerte existante.",
        tags=['Monitoring'],
        request_body=AlertSerializer,
        responses={
            200: openapi.Response(
                description='Alerte mise à jour',
                schema=AlertSerializer()
            ),
            400: "Données invalides",
            404: "Alerte non trouvée",
            401: "Non authentifié"
        }
    )
    def update(self, request: Request, pk=None) -> Response:
        """Met à jour une alerte."""
        # Valider les données d'entrée
        serializer = AlertSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Mettre à jour l'alerte
        try:
            # Si le statut est mis à jour, utiliser la méthode spécifique
            if 'status' in serializer.validated_data:
                user_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None
                comment = serializer.validated_data.get('comment')
                
                alert = self.use_case.update_status(
                    alert_id=int(pk),
                    status=serializer.validated_data['status'],
                    user_id=user_id,
                    comment=comment
                )
                
                # Supprimer status pour ne pas le mettre à jour deux fois
                validated_data = dict(serializer.validated_data)
                validated_data.pop('status')
                if 'comment' in validated_data:
                    validated_data.pop('comment')
                
                # Mettre à jour les autres champs si nécessaire
                if validated_data:
                    alert = self.repository.update(int(pk), **validated_data)
            else:
                # Mise à jour standard
                alert = self.repository.update(int(pk), **serializer.validated_data)
            
            # Sérialiser la réponse
            response_serializer = AlertSerializer(alert)
            return Response(response_serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_summary="Supprimer une alerte",
        operation_description="Supprime une alerte du système.",
        tags=['Monitoring'],
        responses={
            204: "Alerte supprimée avec succès",
            404: "Alerte non trouvée",
            401: "Non authentifié"
        }
    )
    def destroy(self, request: Request, pk=None) -> Response:
        """Supprime une alerte."""
        try:
            result = self.use_case.delete_alert(int(pk))
            if result:
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({"error": "Failed to delete alert"}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    
    @swagger_auto_schema(
        operation_summary="Reconnaître une alerte",
        operation_description="Marque une alerte comme reconnue par l'utilisateur connecté.",
        tags=['Monitoring'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'comment': openapi.Schema(type=openapi.TYPE_STRING, description="Commentaire de reconnaissance")
            }
        ),
        responses={
            200: openapi.Response(
                description='Alerte reconnue',
                schema=AlertSerializer()
            ),
            400: "Données invalides",
            401: "Authentification requise",
            404: "Alerte non trouvée"
        }
    )
    @action(detail=True, methods=['post'])
    def acknowledge(self, request: Request, pk=None) -> Response:
        """Reconnaît une alerte."""
        try:
            user_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None
            comment = request.data.get('comment')
            
            if not user_id:
                return Response({"error": "User authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
            alert = self.use_case.acknowledge_alert(
                alert_id=int(pk),
                user_id=user_id,
                comment=comment
            )
            
            serializer = AlertSerializer(alert)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_summary="Résoudre une alerte",
        operation_description="Marque une alerte comme résolue par l'utilisateur connecté.",
        tags=['Monitoring'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'comment': openapi.Schema(type=openapi.TYPE_STRING, description="Commentaire de résolution")
            }
        ),
        responses={
            200: openapi.Response(
                description='Alerte résolue',
                schema=AlertSerializer()
            ),
            400: "Données invalides",
            401: "Authentification requise",
            404: "Alerte non trouvée"
        }
    )
    @action(detail=True, methods=['post'])
    def resolve(self, request: Request, pk=None) -> Response:
        """Résout une alerte."""
        try:
            user_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None
            comment = request.data.get('comment')
            
            if not user_id:
                return Response({"error": "User authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
            alert = self.use_case.resolve_alert(
                alert_id=int(pk),
                user_id=user_id,
                comment=comment
            )
            
            serializer = AlertSerializer(alert)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_summary="Résumé des alertes",
        operation_description="Récupère un résumé statistique des alertes par statut et sévérité.",
        tags=['Monitoring'],
        responses={
            200: openapi.Response(
                description="Résumé des alertes",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'total': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'by_status': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'by_severity': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            ),
            401: "Non authentifié"
        }
    )
    @action(detail=False, methods=['get'])
    def summary(self, request: Request) -> Response:
        """Récupère un résumé des alertes."""
        summary = self.use_case.get_alerts_summary()
        return Response(summary)
    
    @swagger_auto_schema(
        operation_summary="Mise à jour en lot",
        operation_description="Met à jour le statut de plusieurs alertes en une seule opération.",
        tags=['Monitoring'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['alert_ids', 'status'],
            properties={
                'alert_ids': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER),
                    description="Liste des IDs des alertes à mettre à jour"
                ),
                'status': openapi.Schema(type=openapi.TYPE_STRING, description="Nouveau statut"),
                'comment': openapi.Schema(type=openapi.TYPE_STRING, description="Commentaire optionnel")
            }
        ),
        responses={
            200: openapi.Response(
                description="Alertes mises à jour",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'updated_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'alerts': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'title': openapi.Schema(type=openapi.TYPE_STRING),
                                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                                    'severity': openapi.Schema(type=openapi.TYPE_STRING),
                                }
                            )
                        )
                    }
                )
            ),
            400: "Données invalides",
            401: "Non authentifié"
        }
    )
    @action(detail=False, methods=['post'])
    def bulk_update(self, request: Request) -> Response:
        """Met à jour plusieurs alertes en une seule opération."""
        # Valider les données d'entrée
        if not isinstance(request.data, dict) or 'alert_ids' not in request.data or 'status' not in request.data:
            return Response({"error": "Expected alert_ids and status in request data"}, status=status.HTTP_400_BAD_REQUEST)
        
        alert_ids = request.data['alert_ids']
        status_value = request.data['status']
        user_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None
        comment = request.data.get('comment')
        
        try:
            updated_alerts = self.use_case.bulk_update_status(
                alert_ids=alert_ids,
                status=status_value,
                user_id=user_id,
                comment=comment
            )
            
            serializer = AlertSerializer(updated_alerts, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
