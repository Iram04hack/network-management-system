"""
Vues pour la gestion de l'application des politiques QoS aux interfaces.

Ce module contient les vues pour appliquer et retirer des politiques QoS
des interfaces réseau selon l'architecture hexagonale.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..application import (
    ApplyPolicyToInterfaceUseCase,
    RemovePolicyFromInterfaceUseCase
)
from ..domain.exceptions import (
    QoSPolicyNotFoundException,
    QoSPolicyApplicationException,
    InterfaceQoSPolicyNotFoundException,
    BandwidthLimitExceededException
)
from ..serializers import (
    QoSPolicyApplySerializer
)
from .mixins import DIViewMixin, QoSPermissionMixin, AdminRequiredMixin


class QoSPolicyApplicationViewSet(DIViewMixin, QoSPermissionMixin, AdminRequiredMixin, viewsets.ViewSet):
    """
    ViewSet pour l'application des politiques QoS aux interfaces réseau.
    
    Gestion de l'application et du retrait des politiques QoS :
    - Application de politiques à des interfaces spécifiques
    - Configuration dynamique des paramètres QoS
    - Validation des contraintes de bande passante
    - Gestion des erreurs d'application
    """
    
    # Configurer les dépendances requises
    _dependencies = {
        "apply_policy_to_interface_use_case": ApplyPolicyToInterfaceUseCase,
        "remove_policy_from_interface_use_case": RemovePolicyFromInterfaceUseCase
    }
    
    permission_type = "qos_policy_application"
    
    @action(detail=True, methods=['post'])
    @swagger_auto_schema(
        operation_summary="Appliquer une politique QoS",
        operation_description="""
        Applique une politique QoS à une interface réseau spécifique.
        
        **Fonctionnalités :**
        - Application en temps réel de la politique
        - Validation des contraintes de bande passante
        - Configuration automatique des files d'attente
        - Vérification de compatibilité avec l'interface
        
        **Paramètres requis :**
        - `interface_id` : ID de l'interface cible
        - `parameters` : Paramètres d'application optionnels
        
        **Validations effectuées :**
        - Existence de la politique et de l'interface
        - Disponibilité de bande passante
        - Compatibilité des algorithmes QoS
        """,
        request_body=QoSPolicyApplySerializer,
        responses={
            200: openapi.Response("Politique appliquée avec succès", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Statut de l'application"),
                    'interface_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID de l'interface"),
                    'policy_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID de la politique"),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description="Message de confirmation")
                }
            )),
            400: "Données invalides ou contraintes non respectées",
            404: "Politique QoS ou interface non trouvée",
            500: "Erreur serveur lors de l'application"
        },
        tags=['QoS Management']
    )
    def apply(self, request, pk=None):
        """
        Applique une politique QoS à une interface réseau.
        
        Args:
            request: Requête HTTP contenant les données de l'application
            pk: ID de la politique QoS à appliquer
            
        Returns:
            Response: Résultat de l'application
        """
        serializer = QoSPolicyApplySerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Appliquer la politique avec les données validées
            interface_id = serializer.validated_data.get('interface_id')
            parameters = serializer.validated_data.get('parameters', {})
            
            result = self.apply_policy_to_interface_use_case.execute(
                int(pk),
                interface_id,
                parameters
            )
            
            return Response(result)
        except QoSPolicyNotFoundException as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except QoSPolicyApplicationException as e:
            return Response(
                {"detail": str(e), "reason": e.reason},
                status=status.HTTP_400_BAD_REQUEST
            )
        except BandwidthLimitExceededException as e:
            return Response(
                {
                    "detail": str(e),
                    "bandwidth": e.bandwidth,
                    "available": e.available
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'], url_path='remove-from-interface/(?P<interface_id>[^/.]+)')
    @swagger_auto_schema(
        operation_summary="Retirer une politique d'une interface",
        operation_description="""
        Retire une politique QoS d'une interface réseau et nettoie la configuration.
        
        **Fonctionnalités :**
        - Suppression complète de la configuration QoS
        - Nettoyage des files d'attente et règles
        - Restauration des paramètres par défaut
        - Vérification de l'état post-suppression
        
        **Opérations effectuées :**
        - Désactivation des règles de classification
        - Suppression des files d'attente QoS
        - Nettoyage des compteurs de trafic
        - Mise à jour du statut d'interface
        """,
        manual_parameters=[
            openapi.Parameter('interface_id', openapi.IN_PATH, description="ID de l'interface", type=openapi.TYPE_INTEGER, required=True),
        ],
        responses={
            200: openapi.Response("Politique retirée avec succès", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, description="Statut de l'opération"),
                    'interface_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID de l'interface"),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description="Message de confirmation")
                }
            )),
            400: "Erreur lors du retrait de la politique",
            404: "Interface ou politique non trouvée",
            500: "Erreur serveur lors du retrait"
        },
        tags=['QoS Management']
    )
    def remove_from_interface(self, request, interface_id=None):
        """
        Retire une politique QoS d'une interface réseau.
        
        Args:
            request: Requête HTTP
            interface_id: ID de l'interface
            
        Returns:
            Response: Résultat du retrait
        """
        try:
            # Convertir interface_id en entier
            interface_id = int(interface_id)
            
            # Retirer la politique de l'interface
            result = self.remove_policy_from_interface_use_case.execute(interface_id)
            
            return Response({"status": "success"})
        except InterfaceQoSPolicyNotFoundException as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except QoSPolicyApplicationException as e:
            return Response(
                {"detail": str(e), "reason": e.reason},
                status=status.HTTP_400_BAD_REQUEST
            ) 