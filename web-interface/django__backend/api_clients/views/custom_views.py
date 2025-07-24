"""
Exemples de vues personnalisées avec documentation Swagger automatique.

Ce module montre comment utiliser les décorateurs Swagger automatiques
sur des ViewSets et des vues API personnalisées.
"""

from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from ..utils.swagger_utils import auto_schema_viewset
from ..serializers import GNS3ProjectSerializer, SNMPRequestSerializer


@auto_schema_viewset
class AutoDocumentedViewSet(mixins.ListModelMixin,
                           mixins.RetrieveModelMixin,
                           viewsets.GenericViewSet):
    """
    ViewSet avec documentation Swagger automatique.
    
    Ce ViewSet est un exemple d'utilisation du décorateur @auto_schema_viewset
    qui génère automatiquement la documentation Swagger pour toutes les méthodes.
    """
    permission_classes = [AllowAny]
    serializer_class = GNS3ProjectSerializer
    
    def get_queryset(self):
        """Retourne une liste fictive pour la documentation."""
        return []
    
    def list(self, request):
        """
        Liste tous les projets disponibles.
        
        Cette méthode retourne la liste de tous les projets disponibles.
        """
        return Response({
            "projects": [
                {"id": "demo-1", "name": "Projet Demo 1", "status": "active"},
                {"id": "demo-2", "name": "Projet Demo 2", "status": "inactive"}
            ]
        })
    
    def retrieve(self, request, pk=None):
        """
        Récupère les détails d'un projet spécifique.
        
        Cette méthode retourne les détails d'un projet spécifique identifié par son ID.
        """
        return Response({
            "id": pk,
            "name": f"Projet {pk}",
            "status": "active",
            "created_at": "2024-06-26T12:00:00Z"
        })
    
    @action(detail=False, methods=['post'])
    def test_action(self, request):
        """
        Action personnalisée pour tester l'API.
        
        Cette méthode est un exemple d'action personnalisée qui sera
        automatiquement documentée par le décorateur @auto_schema_viewset.
        """
        return Response({
            "status": "success",
            "message": "Action de test exécutée avec succès"
        })


# Exemple d'utilisation directe de la fonction apply_swagger_auto_schema
from ..utils.swagger_utils import apply_swagger_auto_schema

class ManuallyDecoratedViewSet(viewsets.ViewSet):
    """ViewSet décoré manuellement avec apply_swagger_auto_schema."""
    serializer_class = SNMPRequestSerializer
    
    def list(self, request):
        """Liste des éléments."""
        return Response({"items": []})

# Application manuelle du décorateur
ManuallyDecoratedViewSet = apply_swagger_auto_schema(ManuallyDecoratedViewSet) 