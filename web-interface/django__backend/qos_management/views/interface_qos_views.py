from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
import logging
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..di_container import qos_container
from ..services.traffic_control_service import TrafficControlService
from ..models import InterfaceQoSPolicy, QoSPolicy
from ..serializers import InterfaceQoSPolicySerializer
from .mixins import QoSPermissionMixin

logger = logging.getLogger(__name__)

class InterfaceQoSPolicyViewSet(QoSPermissionMixin, viewsets.ModelViewSet):
    """
    API ViewSet pour les applications de politiques QoS aux interfaces.
    
    Gestion complète des associations entre interfaces réseau et politiques QoS :
    - Application et retrait de politiques aux interfaces
    - Activation/désactivation dynamique des politiques
    - Monitoring de l'état des applications QoS
    - Configuration des paramètres par interface
    - Gestion des directions de trafic (ingress/egress)
    """
    queryset = InterfaceQoSPolicy.objects.all()
    serializer_class = InterfaceQoSPolicySerializer
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialiser les dépendances via le conteneur
        self.traffic_control_service = qos_container.traffic_control_service()
    
    @swagger_auto_schema(
        operation_summary="Liste des applications QoS aux interfaces",
        operation_description="""
        Récupère la liste des politiques QoS appliquées aux interfaces réseau.
        
        **Fonctionnalités :**
        - Filtrage par interface, politique ou direction
        - Visualisation de l'état d'activation
        - Informations sur les paramètres d'application
        - Monitoring des performances par interface
        
        **Filtres disponibles :**
        - `interface_id` : Filtrer par interface réseau
        - `policy_id` : Filtrer par politique QoS
        - `direction` : Direction du trafic (ingress/egress)
        - `is_active` : État d'activation (true/false)
        """,
        manual_parameters=[
            openapi.Parameter('interface_id', openapi.IN_QUERY, description="ID de l'interface", type=openapi.TYPE_INTEGER),
            openapi.Parameter('policy_id', openapi.IN_QUERY, description="ID de la politique QoS", type=openapi.TYPE_INTEGER),
            openapi.Parameter('direction', openapi.IN_QUERY, description="Direction du trafic", type=openapi.TYPE_STRING, enum=['ingress', 'egress']),
            openapi.Parameter('is_active', openapi.IN_QUERY, description="État d'activation", type=openapi.TYPE_BOOLEAN),
        ],
        responses={
            200: openapi.Response("Liste des applications QoS", InterfaceQoSPolicySerializer(many=True)),
            500: "Erreur serveur interne"
        },
        tags=['QoS Management']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Détails d'une application QoS",
        operation_description="""
        Récupère les détails d'une application QoS spécifique.
        
        **Informations retournées :**
        - Configuration complète de l'application
        - État d'activation et paramètres
        - Interface et politique associées
        - Statistiques de performance
        """,
        responses={
            200: openapi.Response("Application QoS trouvée", InterfaceQoSPolicySerializer),
            404: "Application QoS non trouvée",
            500: "Erreur serveur interne"
        },
        tags=['QoS Management']
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Créer une application QoS",
        operation_description="""
        Crée une nouvelle application de politique QoS à une interface.
        
        **Paramètres requis :**
        - `interface_id` : ID de l'interface cible
        - `policy_id` : ID de la politique QoS
        - `direction` : Direction du trafic (ingress/egress)
        
        **Fonctionnalités :**
        - Validation de compatibilité interface/politique
        - Configuration automatique des paramètres
        - Application optionnelle immédiate
        """,
        request_body=InterfaceQoSPolicySerializer,
        responses={
            201: openapi.Response("Application QoS créée", InterfaceQoSPolicySerializer),
            400: "Données invalides ou incompatibilité",
            500: "Erreur serveur interne"
        },
        tags=['QoS Management']
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Mettre à jour une application QoS",
        operation_description="Mise à jour d'une application QoS existante",
        request_body=InterfaceQoSPolicySerializer,
        responses={
            200: openapi.Response("Application QoS mise à jour", InterfaceQoSPolicySerializer),
            400: "Données invalides",
            404: "Application QoS non trouvée"
        },
        tags=['QoS Management']
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Mettre à jour partiellement une application QoS",
        operation_description="Mise à jour partielle d'une application QoS existante",
        request_body=InterfaceQoSPolicySerializer,
        responses={
            200: openapi.Response("Application QoS mise à jour partiellement", InterfaceQoSPolicySerializer),
            400: "Données invalides",
            404: "Application QoS non trouvée"
        },
        tags=['QoS Management']
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Supprimer une application QoS",
        operation_description="Supprime une application QoS et nettoie l'interface",
        responses={
            204: "Application QoS supprimée avec succès",
            404: "Application QoS non trouvée"
        },
        tags=['QoS Management']
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Filtre les applications selon les paramètres de requête
        
        Query Parameters:
            interface_id: ID de l'interface
            policy_id: ID de la politique QoS
            direction: Direction du trafic (ingress/egress)
            is_active: État d'activation (true/false)
        """
        # Gestion Swagger : retourner un queryset vide si c'est une vue factice
        if getattr(self, 'swagger_fake_view', False):
            return InterfaceQoSPolicy.objects.none()
            
        queryset = InterfaceQoSPolicy.objects.all()
        
        # Filtres (vérifier que self.request n'est pas None)
        interface_id = self.request.query_params.get('interface_id', None) if self.request else None
        policy_id = self.request.query_params.get('policy_id', None) if self.request else None
        direction = self.request.query_params.get('direction', None) if self.request else None
        is_active = self.request.query_params.get('is_active', None) if self.request else None
        
        if interface_id:
            queryset = queryset.filter(interface_id=interface_id)
            
        if policy_id:
            queryset = queryset.filter(policy_id=policy_id)
            
        if direction:
            queryset = queryset.filter(direction=direction)
            
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    @swagger_auto_schema(
        operation_summary="Activer/Désactiver une application QoS",
        operation_description="""
        Bascule l'état d'activation d'une application QoS sur une interface.
        
        **Fonctionnalités :**
        - Activation : Application des règles QoS via Traffic Control
        - Désactivation : Suppression des configurations sans perte de données
        - Validation de l'état post-opération
        - Gestion des erreurs de configuration
        
        **Opérations effectuées :**
        - Configuration des files d'attente
        - Application des règles de classification
        - Mise à jour des compteurs de trafic
        - Vérification de l'intégrité
        """,
        responses={
            200: openapi.Response("Statut modifié avec succès", InterfaceQoSPolicySerializer),
            400: "Erreur lors de la modification du statut",
            404: "Application QoS ou politique non trouvée",
            500: "Erreur serveur lors de l'application"
        },
        tags=['QoS Management']
    )
    def toggle_status(self, request, pk=None):
        """
        Active ou désactive cette application de politique
        
        Si la politique est activée, elle est appliquée à l'interface via Traffic Control.
        Si elle est désactivée, la configuration est retirée de l'interface.
        """
        interface_policy = self.get_object()
        interface_policy.is_active = not interface_policy.is_active
        interface_policy.save()
        
        # Appliquer ou supprimer la politique via Traffic Control
        try:
            if interface_policy.is_active:
                # Récupérer la politique et l'appliquer via Traffic Control
                policy = QoSPolicy.objects.get(id=interface_policy.policy_id)
                success = self.traffic_control_service.configure_interface(
                    interface_name=interface_policy.interface.name,
                    direction=interface_policy.direction,
                    bandwidth_limit=policy.bandwidth_limit,
                    traffic_classes=policy.traffic_classes.all()
                )
                
                if not success:
                    interface_policy.is_active = False
                    interface_policy.save()
                    logger.error(f"Échec de l'application de la politique sur l'interface {interface_policy.interface.name}")
                    return Response(
                        {'error': "Échec de l'application de la politique QoS via Traffic Control"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            else:
                # Supprimer la politique
                success = self.traffic_control_service.clear_interface(interface_policy.interface.name)
                if not success:
                    interface_policy.is_active = True
                    interface_policy.save()
                    logger.error(f"Échec de la suppression de la politique sur l'interface {interface_policy.interface.name}")
                    return Response(
                        {'error': "Échec de la désactivation de la politique QoS"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                    
        except QoSPolicy.DoesNotExist:
            logger.error(f"Politique QoS avec ID {interface_policy.policy_id} non trouvée")
            return Response(
                {'error': f"Politique QoS avec ID {interface_policy.policy_id} non trouvée"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.exception(f"Erreur lors de la modification de l'état de la politique QoS: {e}")
            return Response(
                {'error': f"Erreur lors de la modification de l'état: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        serializer = self.get_serializer(interface_policy)
        return Response(serializer.data)
    
    @action(detail=True, methods=['delete'])
    @swagger_auto_schema(
        operation_summary="Retirer complètement une application QoS",
        operation_description="""
        Supprime définitivement une application QoS et nettoie l'interface.
        
        **Opérations effectuées :**
        - Nettoyage complet de la configuration QoS
        - Suppression des files d'attente et règles
        - Restauration des paramètres par défaut
        - Suppression de l'entrée en base de données
        
        **Attention :** Cette opération est irréversible et supprime
        définitivement l'association interface/politique.
        """,
        responses={
            200: openapi.Response("Application supprimée avec succès", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description="Message de confirmation")
                }
            )),
            404: "Application QoS non trouvée",
            500: "Erreur lors du nettoyage de l'interface"
        },
        tags=['QoS Management']
    )
    def remove(self, request, pk=None):
        """
        Supprime cette application de politique et nettoie l'interface
        
        La configuration QoS est retirée de l'interface avant la suppression
        de l'association de la base de données.
        """
        interface_policy = self.get_object()
        
        # Nettoyer l'interface via Traffic Control
        try:
            success = self.traffic_control_service.clear_interface(interface_policy.interface.name)
            if not success:
                logger.warning(f"Échec du nettoyage de l'interface {interface_policy.interface.name}")
                return Response(
                    {'error': "Échec du nettoyage de l'interface. L'entrée sera tout de même supprimée."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            logger.exception(f"Erreur lors du nettoyage de l'interface: {e}")
            return Response(
                {'error': f"Erreur lors du nettoyage de l'interface: {str(e)}. L'entrée sera tout de même supprimée."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Supprimer l'application
        interface_policy.delete()
        
        return Response({
            'message': 'Application de politique supprimée avec succès'
        }) 