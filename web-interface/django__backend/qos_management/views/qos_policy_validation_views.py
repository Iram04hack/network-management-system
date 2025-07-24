"""
Vues pour la validation des politiques QoS.

Ce module contient les vues pour la validation des politiques QoS
selon l'architecture hexagonale.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..application import (
    CreateQoSPolicyUseCase
)
from ..domain.exceptions import (
    QoSValidationException
)
from ..serializers import (
    QoSPolicyCreateSerializer
)
from .mixins import DIViewMixin, QoSPermissionMixin, AdminRequiredMixin


class QoSPolicyValidationViewSet(DIViewMixin, QoSPermissionMixin, AdminRequiredMixin, viewsets.ViewSet):
    """
    ViewSet pour la validation des politiques QoS.
    
    Outils de validation et vérification des politiques QoS :
    - Validation préalable sans création
    - Vérification de cohérence des paramètres
    - Test de compatibilité avec les infrastructures
    - Information sur les types de politiques disponibles
    """
    
    # Configurer les dépendances requises
    _dependencies = {
        "create_qos_policy_use_case": CreateQoSPolicyUseCase
    }
    
    permission_type = "qos_policy_validation"
    
    @action(detail=False, methods=['post'])
    @swagger_auto_schema(
        operation_summary="Valider une politique QoS",
        operation_description="""
        Valide une politique QoS sans la créer pour vérifier sa cohérence.
        
        **Validations effectuées :**
        - Cohérence des paramètres selon le type de politique
        - Respect des contraintes de bande passante
        - Unicité du nom de la politique
        - Compatibilité des algorithmes QoS
        
        **Types de politique supportés :**
        - `htb` : Hierarchical Token Bucket
        - `hfsc` : Hierarchical Fair Service Curve
        - `cbq` : Class Based Queueing
        - `fq_codel` : Fair Queuing with Controlled Delay
        
        **Réponse :**
        - `valid: true` si la politique est valide
        - `valid: false` avec détails des erreurs sinon
        """,
        request_body=QoSPolicyCreateSerializer,
        responses={
            200: openapi.Response("Politique valide", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'valid': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Statut de validation"),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description="Message de validation")
                }
            )),
            400: openapi.Response("Politique invalide", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'valid': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Statut de validation (false)"),
                    'detail': openapi.Schema(type=openapi.TYPE_STRING, description="Description de l'erreur"),
                    'errors': openapi.Schema(type=openapi.TYPE_OBJECT, description="Détails des erreurs de validation")
                }
            )),
            500: "Erreur serveur lors de la validation"
        },
        tags=['QoS Management']
    )
    def validate(self, request):
        """
        Valide une politique QoS sans la créer.
        
        Args:
            request: Requête HTTP contenant la politique à valider
            
        Returns:
            Response: Résultat de la validation
        """
        serializer = QoSPolicyCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Valider la politique avec les données validées (sans créer)
            result = self.create_qos_policy_use_case.execute(
                serializer.validated_data,
                validate_only=True
            )
            
            return Response({"valid": True})
        except QoSValidationException as e:
            return Response(
                {"valid": False, "detail": str(e), "errors": e.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    @swagger_auto_schema(
        operation_summary="Types de politiques QoS disponibles",
        operation_description="""
        Récupère la liste des types de politiques QoS supportés par le système.
        
        **Types disponibles :**
        
        **HTB (Hierarchical Token Bucket) :**
        - Contrôle hiérarchique de la bande passante
        - Support des garanties et limites
        - Idéal pour les réseaux d'entreprise
        
        **HFSC (Hierarchical Fair Service Curve) :**
        - Garanties de délai et de bande passante
        - Contrôle précis de la latence
        - Optimal pour les applications temps réel
        
        **CBQ (Class Based Queueing) :**
        - Classification par classes de trafic
        - Partage équitable des ressources
        - Compatible avec les équipements anciens
        
        **FQ-CoDel (Fair Queuing with Controlled Delay) :**
        - Réduction active de la latence
        - Partage équitable automatique
        - Idéal pour les réseaux domestiques
        """,
        responses={
            200: openapi.Response("Liste des types de politiques", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'types': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_STRING, description="Identifiant du type"),
                                'name': openapi.Schema(type=openapi.TYPE_STRING, description="Nom complet du type")
                            }
                        )
                    )
                }
            )),
            500: "Erreur serveur lors de la récupération des types"
        },
        tags=['QoS Management']
    )
    def types(self, request):
        """
        Retourne les types de politiques QoS disponibles.
        
        Args:
            request: Requête HTTP
            
        Returns:
            Response: Liste des types de politiques QoS
        """
        return Response({
            "types": [
                {"id": "htb", "name": _("Hierarchical Token Bucket (HTB)")},
                {"id": "hfsc", "name": _("Hierarchical Fair Service Curve (HFSC)")},
                {"id": "cbq", "name": _("Class Based Queueing (CBQ)")},
                {"id": "fq_codel", "name": _("Fair Queuing with Controlled Delay (FQ-CoDel)")}
            ]
        }) 