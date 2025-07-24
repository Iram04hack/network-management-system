"""
Vues pour la gestion des politiques QoS.

Ce module contient les vues pour la gestion des opérations CRUD des politiques QoS
selon l'architecture hexagonale.
"""

from rest_framework import viewsets, status
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..application import (
    GetQoSPolicyUseCase,
    ListQoSPoliciesUseCase,
    CreateQoSPolicyUseCase,
    UpdateQoSPolicyUseCase,
    DeleteQoSPolicyUseCase
)
from ..domain.exceptions import (
    QoSPolicyNotFoundException,
    QoSValidationException,
    QoSConfigurationException
)
from ..serializers import (
    QoSPolicySerializer,
    QoSPolicyCreateSerializer,
    QoSPolicyUpdateSerializer
)
from .mixins import DIViewMixin, QoSPermissionMixin, AdminRequiredMixin


class QoSPolicyViewSet(DIViewMixin, QoSPermissionMixin, AdminRequiredMixin, viewsets.ViewSet):
    """
    ViewSet pour les opérations CRUD sur les politiques QoS.
    
    Gestion complète des politiques de Qualité de Service (QoS) avec :
    - Configuration des algorithmes de QoS (HTB, HFSC, CBQ, FQ_CODEL)
    - Gestion des limites de bande passante et priorités
    - Validation automatique des configurations
    - Support des paramètres avancés par type de politique
    """
    
    # Configurer les dépendances requises
    _dependencies = {
        "get_qos_policy_use_case": GetQoSPolicyUseCase,
        "list_qos_policies_use_case": ListQoSPoliciesUseCase,
        "create_qos_policy_use_case": CreateQoSPolicyUseCase,
        "update_qos_policy_use_case": UpdateQoSPolicyUseCase,
        "delete_qos_policy_use_case": DeleteQoSPolicyUseCase
    }
    
    permission_type = "qos_policy"
    
    @swagger_auto_schema(
        operation_summary="Liste des politiques QoS",
        operation_description="""
        Récupère la liste complète des politiques QoS configurées dans le système.
        
        **Fonctionnalités :**
        - Filtrage par type de politique, statut ou nom
        - Support des recherches par mots-clés
        - Tri par priorité et nom
        - Pagination automatique des résultats
        
        **Filtres disponibles :**
        - `policy_type` : Type de politique (htb, hfsc, cbq, fq_codel)
        - `status` : Statut (active, inactive)
        - `search` : Recherche dans nom et description
        """,
        manual_parameters=[
            openapi.Parameter('policy_type', openapi.IN_QUERY, description="Filtrer par type de politique", type=openapi.TYPE_STRING),
            openapi.Parameter('status', openapi.IN_QUERY, description="Filtrer par statut", type=openapi.TYPE_STRING),
            openapi.Parameter('search', openapi.IN_QUERY, description="Recherche par mots-clés", type=openapi.TYPE_STRING),
        ],
        responses={
            200: openapi.Response("Liste des politiques QoS", QoSPolicySerializer(many=True)),
            500: "Erreur serveur interne"
        },
        tags=['QoS Management']
    )
    def list(self, request):
        """
        Liste toutes les politiques QoS.
        
        Args:
            request: Requête HTTP contenant les filtres
            
        Returns:
            Response: Liste des politiques QoS
        """
        filters = request.query_params.dict()
        
        # Appliquer les filtres
        policies = self.list_qos_policies_use_case.execute(filters)
        
        # Sérialiser les données
        serializer = QoSPolicySerializer(policies, many=True)
        
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_summary="Détails d'une politique QoS",
        operation_description="""
        Récupère tous les détails d'une politique QoS spécifique par son identifiant.
        
        **Informations retournées :**
        - Configuration complète de la politique
        - Algorithme QoS utilisé et paramètres
        - Limites de bande passante et priorités
        - Classes de trafic associées
        - Statut et métadonnées
        """,
        responses={
            200: openapi.Response("Politique QoS trouvée avec succès", QoSPolicySerializer),
            404: "Politique QoS non trouvée avec cet identifiant",
            500: "Erreur serveur interne"
        },
        tags=['QoS Management']
    )
    def retrieve(self, request, pk=None):
        """
        Récupère une politique QoS spécifique.
        
        Args:
            request: Requête HTTP
            pk: ID de la politique à récupérer
            
        Returns:
            Response: Politique QoS demandée
        """
        try:
            policy = self.get_qos_policy_use_case.execute(int(pk))
            serializer = QoSPolicySerializer(policy)
            return Response(serializer.data)
        except QoSPolicyNotFoundException as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @swagger_auto_schema(
        operation_summary="Créer une politique QoS",
        operation_description="""
        Crée une nouvelle politique QoS avec validation automatique des paramètres.
        
        **Paramètres requis :**
        - `name` : Nom unique de la politique
        - `policy_type` : Type d'algorithme (htb, hfsc, cbq, fq_codel)
        - `bandwidth_limit` : Limite de bande passante en kbps
        
        **Fonctionnalités :**
        - Validation des paramètres selon le type de politique
        - Vérification de l'unicité du nom
        - Configuration par défaut intelligente
        - Support des paramètres avancés
        """,
        request_body=QoSPolicyCreateSerializer,
        responses={
            201: openapi.Response("Politique QoS créée avec succès", QoSPolicySerializer),
            400: "Données invalides ou nom déjà utilisé",
            500: "Erreur serveur interne"
        },
        tags=['QoS Management']
    )
    def create(self, request):
        """
        Crée une nouvelle politique QoS.
        
        Args:
            request: Requête HTTP contenant les données de la politique
            
        Returns:
            Response: Politique QoS créée
        """
        serializer = QoSPolicyCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Créer la politique avec les données validées
            policy = self.create_qos_policy_use_case.execute(serializer.validated_data)
            
            # Sérialiser la réponse
            response_serializer = QoSPolicySerializer(policy)
            
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
        except QoSValidationException as e:
            return Response(
                {"detail": str(e), "errors": e.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @swagger_auto_schema(
        operation_summary="Mettre à jour une politique QoS",
        operation_description="Met à jour une politique QoS existante",
        request_body=QoSPolicyUpdateSerializer,
        responses={
            200: openapi.Response("Politique QoS mise à jour", QoSPolicySerializer),
            400: "Données invalides",
            404: "Politique QoS non trouvée"
        },
        tags=['QoS Management']
    )
    def update(self, request, pk=None):
        """
        Met à jour une politique QoS existante.
        
        Args:
            request: Requête HTTP contenant les données de mise à jour
            pk: ID de la politique à mettre à jour
            
        Returns:
            Response: Politique QoS mise à jour
        """
        serializer = QoSPolicyUpdateSerializer(data=request.data, partial=True)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Mettre à jour la politique avec les données validées
            policy = self.update_qos_policy_use_case.execute(
                int(pk),
                serializer.validated_data
            )
            
            # Sérialiser la réponse
            response_serializer = QoSPolicySerializer(policy)
            
            return Response(response_serializer.data)
        except QoSPolicyNotFoundException as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except QoSValidationException as e:
            return Response(
                {"detail": str(e), "errors": e.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @swagger_auto_schema(
        operation_summary="Supprimer une politique QoS",
        operation_description="Supprime une politique QoS existante",
        responses={
            204: "Politique QoS supprimée avec succès",
            400: "Impossible de supprimer la politique",
            404: "Politique QoS non trouvée"
        },
        tags=['QoS Management']
    )
    def destroy(self, request, pk=None):
        """
        Supprime une politique QoS.
        
        Args:
            request: Requête HTTP
            pk: ID de la politique à supprimer
            
        Returns:
            Response: Confirmation de suppression
        """
        force = request.query_params.get('force', 'false').lower() == 'true'
        
        try:
            self.delete_qos_policy_use_case.execute(int(pk), force=force)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except QoSPolicyNotFoundException as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except QoSConfigurationException as e:
            return Response(
                {"detail": str(e), "reason": e.reason},
                status=status.HTTP_400_BAD_REQUEST
            ) 