from rest_framework import viewsets
import logging
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..models import TrafficClassifier
from ..serializers import TrafficClassifierSerializer
from .mixins import QoSPermissionMixin

logger = logging.getLogger(__name__)

class TrafficClassifierViewSet(QoSPermissionMixin, viewsets.ModelViewSet):
    """
    API ViewSet pour les classificateurs de trafic QoS.
    
    Gestion complète des classificateurs avec :
    - Règles de classification fine du trafic réseau
    - Critères de correspondance avancés (IP, port, protocole, DSCP)
    - Priorités et actions personnalisées
    - Support des expressions régulières et plages
    """
    queryset = TrafficClassifier.objects.all()
    serializer_class = TrafficClassifierSerializer
    
    @swagger_auto_schema(
        operation_summary="Liste des classificateurs de trafic",
        operation_description="""
        Récupère la liste complète des classificateurs de trafic QoS configurés.
        
        **Fonctionnalités :**
        - Filtrage par classe de trafic et protocole
        - Support des recherches par critères de correspondance
        - Tri par priorité et nom
        - Pagination automatique des résultats
        
        **Filtres disponibles :**
        - `traffic_class_id` : Filtrer par classe de trafic parente
        - `protocol` : Filtrer par protocole (TCP, UDP, ICMP)
        """,
        manual_parameters=[
            openapi.Parameter('traffic_class_id', openapi.IN_QUERY, description="ID de la classe de trafic", type=openapi.TYPE_INTEGER),
            openapi.Parameter('protocol', openapi.IN_QUERY, description="Protocole réseau", type=openapi.TYPE_STRING),
        ],
        responses={
            200: openapi.Response("Liste des classificateurs", TrafficClassifierSerializer(many=True)),
            500: "Erreur serveur interne"
        },
        tags=['QoS Management']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Détails d'un classificateur",
        operation_description="""
        Récupère les détails complets d'un classificateur de trafic spécifique.
        
        **Informations retournées :**
        - Configuration complète du classificateur
        - Critères de correspondance détaillés
        - Actions et priorités assignées
        - Statistiques d'utilisation
        """,
        responses={
            200: openapi.Response("Classificateur trouvé avec succès", TrafficClassifierSerializer),
            404: "Classificateur non trouvé",
            500: "Erreur serveur interne"
        },
        tags=['QoS Management']
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Créer un classificateur",
        operation_description="""
        Crée un nouveau classificateur de trafic avec validation automatique.
        
        **Paramètres requis :**
        - `name` : Nom unique du classificateur
        - `traffic_class_id` : ID de la classe de trafic parente
        - `match_criteria` : Critères de correspondance
        - `priority` : Priorité (1-100)
        
        **Critères de correspondance supportés :**
        - Adresses IP source/destination (CIDR)
        - Ports source/destination (plages)
        - Protocoles (TCP, UDP, ICMP, ALL)
        - Valeurs DSCP (0-63)
        - Interfaces réseau
        """,
        request_body=TrafficClassifierSerializer,
        responses={
            201: openapi.Response("Classificateur créé avec succès", TrafficClassifierSerializer),
            400: "Données invalides ou critères conflictuels",
            500: "Erreur serveur interne"
        },
        tags=['QoS Management']
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Mettre à jour un classificateur",
        operation_description="Mise à jour d'un classificateur de trafic existant",
        request_body=TrafficClassifierSerializer,
        responses={
            200: openapi.Response("Classificateur mis à jour", TrafficClassifierSerializer),
            400: "Données invalides",
            404: "Classificateur non trouvé"
        },
        tags=['QoS Management']
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Mettre à jour partiellement un classificateur",
        operation_description="Mise à jour partielle d'un classificateur de trafic existant",
        request_body=TrafficClassifierSerializer,
        responses={
            200: openapi.Response("Classificateur mis à jour partiellement", TrafficClassifierSerializer),
            400: "Données invalides",
            404: "Classificateur non trouvé"
        },
        tags=['QoS Management']
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Supprimer un classificateur",
        operation_description="Supprime un classificateur de trafic existant",
        responses={
            204: "Classificateur supprimé avec succès",
            404: "Classificateur non trouvé"
        },
        tags=['QoS Management']
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    
    def get_queryset(self):
        """Filtre les classificateurs selon les paramètres de requête"""
        # Gestion Swagger : retourner un queryset vide si c'est une vue factice
        if getattr(self, 'swagger_fake_view', False):
            return TrafficClassifier.objects.none()
            
        queryset = TrafficClassifier.objects.all()
        
        # Filtres (vérifier que self.request n'est pas None)
        traffic_class_id = self.request.query_params.get('traffic_class_id', None) if self.request else None
        protocol = self.request.query_params.get('protocol', None) if self.request else None
        
        if traffic_class_id:
            queryset = queryset.filter(traffic_class_id=traffic_class_id)
            
        if protocol:
            queryset = queryset.filter(protocol=protocol)
        
        return queryset 