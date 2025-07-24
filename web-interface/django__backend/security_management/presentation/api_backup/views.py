"""
Vues API REST pour le module security_management.

Ce fichier contient les vues Django REST Framework qui exposent
les fonctionnalités du module security_management via une API REST.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ...di_container import container
from .serializers import (
    SecurityRuleSerializer,
    SecurityAlertSerializer
)
from ...domain.exceptions import (
    SecurityRuleValidationException,
    RuleConflictException
)
from ...infrastructure.models import SecurityRuleModel, SecurityAlertModel


class SecurityRuleViewSet(viewsets.ModelViewSet):
    """
    API pour la gestion des règles de sécurité.
    
    Cette API permet de créer, lire, mettre à jour et supprimer des règles
    de sécurité, ainsi que de les activer ou désactiver.
    """
    
    queryset = SecurityRuleModel.objects.all()
    serializer_class = SecurityRuleSerializer
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """
        Liste toutes les règles de sécurité.
        
        Paramètres de requête:
        - rule_type: Filtrer par type de règle
        - enabled: Filtrer par statut (true/false)
        """
        # Construire les filtres à partir des paramètres de requête
        filters = {}
        
        rule_type = request.query_params.get('rule_type')
        if rule_type:
            filters['rule_type'] = rule_type
        
        enabled = request.query_params.get('enabled')
        if enabled is not None:
            filters['enabled'] = enabled.lower() == 'true'
        
        # Récupérer les règles via le cas d'utilisation
        rules = container.rule_management_use_case.list_rules(filters)
        
        # Sérialiser et retourner les résultats
        serializer = SecurityRuleSerializer(rules, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        """
        Récupère une règle de sécurité par son ID.
        """
        rule = container.rule_management_use_case.get_rule(pk)
        
        if not rule:
            return Response(
                {"detail": f"Règle avec ID {pk} non trouvée"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = SecurityRuleSerializer(rule)
        return Response(serializer.data)
    
    def create(self, request):
        """
        Crée une nouvelle règle de sécurité.
        """
        serializer = SecurityRuleSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            rule = container.rule_management_use_case.create_rule(serializer.validated_data)
            result_serializer = SecurityRuleSerializer(rule)
            return Response(
                result_serializer.data,
                status=status.HTTP_201_CREATED
            )
            
        except SecurityRuleValidationException as e:
            return Response(
                {
                    "detail": e.message,
                    "errors": e.details
                },
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except RuleConflictException as e:
            return Response(
                {
                    "detail": e.message,
                    "conflicts": e.conflicts
                },
                status=status.HTTP_409_CONFLICT
            )
            
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def update(self, request, pk=None):
        """
        Met à jour une règle de sécurité existante.
        """
        # Vérifier si la règle existe
        rule = container.rule_management_use_case.get_rule(pk)
        
        if not rule:
            return Response(
                {"detail": f"Règle avec ID {pk} non trouvée"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Valider les données
        serializer = SecurityRuleSerializer(data=request.data, partial=True)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            updated_rule = container.rule_management_use_case.update_rule(
                pk, serializer.validated_data
            )
            result_serializer = SecurityRuleSerializer(updated_rule)
            return Response(result_serializer.data)
            
        except SecurityRuleValidationException as e:
            return Response(
                {
                    "detail": e.message,
                    "errors": e.details
                },
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except RuleConflictException as e:
            return Response(
                {
                    "detail": e.message,
                    "conflicts": e.conflicts
                },
                status=status.HTTP_409_CONFLICT
            )
            
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def destroy(self, request, pk=None):
        """
        Supprime une règle de sécurité.
        """
        success = container.rule_management_use_case.delete_rule(pk)
        
        if not success:
            return Response(
                {"detail": f"Règle avec ID {pk} non trouvée ou impossible à supprimer"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @swagger_auto_schema(
        method='patch',
        operation_description='Active ou désactive une règle de sécurité',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'enabled': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Activer (true) ou désactiver (false)')
            },
            required=['enabled']
        ),
        responses={200: SecurityRuleSerializer}
    )
    @action(detail=True, methods=['patch'])
    def toggle_status(self, request, pk=None):
        """
        Active ou désactive une règle de sécurité.
        
        Paramètres de requête:
        - enabled: true pour activer, false pour désactiver
        """
        enabled = request.data.get('enabled')
        
        if enabled is None:
            return Response(
                {"detail": "Le paramètre 'enabled' est requis"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            enabled_bool = enabled if isinstance(enabled, bool) else enabled.lower() == 'true'
            rule = container.rule_management_use_case.toggle_rule_status(pk, enabled_bool)
            serializer = SecurityRuleSerializer(rule)
            return Response(serializer.data)
            
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
            
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SecurityAlertViewSet(viewsets.ModelViewSet):
    """
    API pour la gestion des alertes de sécurité.
    
    Cette API permet de consulter et gérer les alertes de sécurité
    générées par le système.
    """
    
    queryset = SecurityAlertModel.objects.all()
    serializer_class = SecurityAlertSerializer
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """
        Liste les alertes de sécurité.
        
        Paramètres de requête:
        - severity: Filtrer par niveau de gravité
        - status: Filtrer par statut
        - source_ip: Filtrer par adresse IP source
        - from_date: Filtrer à partir d'une date (format ISO)
        - to_date: Filtrer jusqu'à une date (format ISO)
        """
        # Construire les filtres à partir des paramètres de requête
        filters = {}
        
        severity = request.query_params.get('severity')
        if severity:
            filters['severity'] = severity
        
        status = request.query_params.get('status')
        if status:
            filters['status'] = status
        
        source_ip = request.query_params.get('source_ip')
        if source_ip:
            filters['source_ip'] = source_ip
        
        from_date = request.query_params.get('from_date')
        if from_date:
            filters['from_date'] = from_date
        
        to_date = request.query_params.get('to_date')
        if to_date:
            filters['to_date'] = to_date
        
        # Récupérer les alertes via le cas d'utilisation
        alerts = container.alert_management_use_case.list_alerts(filters)
        
        # Sérialiser et retourner les résultats
        serializer = SecurityAlertSerializer(alerts, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        """
        Récupère une alerte de sécurité par son ID.
        """
        alert = container.alert_management_use_case.get_alert(pk)
        
        if not alert:
            return Response(
                {"detail": f"Alerte avec ID {pk} non trouvée"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = SecurityAlertSerializer(alert)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        method='patch',
        operation_description='Marque une alerte comme traitée',
        responses={200: SecurityAlertSerializer}
    )
    @action(detail=True, methods=['patch'])
    def mark_processed(self, request, pk=None):
        """
        Marque une alerte comme traitée.
        """
        success = container.alert_management_use_case.mark_as_processed(pk)
        
        if not success:
            return Response(
                {"detail": f"Alerte avec ID {pk} non trouvée"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Récupérer l'alerte mise à jour
        alert = container.alert_management_use_case.get_alert(pk)
        serializer = SecurityAlertSerializer(alert)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        method='patch',
        operation_description='Marque une alerte comme faux positif',
        responses={200: SecurityAlertSerializer}
    )
    @action(detail=True, methods=['patch'])
    def mark_false_positive(self, request, pk=None):
        """
        Marque une alerte comme faux positif.
        """
        success = container.alert_management_use_case.mark_as_false_positive(pk)
        
        if not success:
            return Response(
                {"detail": f"Alerte avec ID {pk} non trouvée"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Récupérer l'alerte mise à jour
        alert = container.alert_management_use_case.get_alert(pk)
        serializer = SecurityAlertSerializer(alert)
        return Response(serializer.data) 