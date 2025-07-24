"""
Vues pour la gestion des classes de trafic.

Ce module contient les vues pour la gestion des classes de trafic
selon l'architecture hexagonale.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..application import (
    GetTrafficClassUseCase,
    ListTrafficClassesUseCase,
    CreateTrafficClassUseCase,
    ListTrafficClassifiersUseCase,
    CreateTrafficClassifierUseCase
)
from ..domain.exceptions import (
    QoSPolicyNotFoundException,
    TrafficClassNotFoundException,
    QoSValidationException,
    BandwidthLimitExceededException,
    TrafficClassifierNotFoundException
)
from ..serializers import (
    TrafficClassSerializer,
    TrafficClassCreateSerializer,
    TrafficClassUpdateSerializer,
    TrafficClassifierSerializer,
    TrafficClassifierCreateSerializer
)
from .mixins import DIViewMixin, QoSPermissionMixin, AdminRequiredMixin


class TrafficClassViewSet(DIViewMixin, QoSPermissionMixin, AdminRequiredMixin, viewsets.ViewSet):
    """
    ViewSet pour la gestion des classes de trafic QoS.
    
    Gestion complète des classes de trafic avec :
    - Classification fine du trafic réseau
    - Attribution de priorités et DSCP
    - Allocation de bande passante par classe
    - Gestion des files d'attente et limites
    - Support des algorithmes de classification avancés
    """
    
    # Configurer les dépendances requises
    _dependencies = {
        "get_traffic_class_use_case": GetTrafficClassUseCase,
        "list_traffic_classes_use_case": ListTrafficClassesUseCase,
        "create_traffic_class_use_case": CreateTrafficClassUseCase,
        "list_traffic_classifiers_use_case": ListTrafficClassifiersUseCase,
        "create_traffic_classifier_use_case": CreateTrafficClassifierUseCase
    }
    
    permission_type = "traffic_class"
    
    @swagger_auto_schema(
        operation_summary="Liste des classes de trafic",
        operation_description="""
        Récupère la liste des classes de trafic QoS configurées.
        
        **Fonctionnalités :**
        - Filtrage par politique QoS parente
        - Support des recherches par priorité et DSCP
        - Informations détaillées sur l'allocation de bande passante
        - Configuration des files d'attente par classe
        
        **Filtres disponibles :**
        - `policy_id` : Filtrer par politique QoS parent
        - `priority` : Filtrer par niveau de priorité
        - `dscp` : Filtrer par valeur DSCP
        """,
        manual_parameters=[
            openapi.Parameter('policy_id', openapi.IN_QUERY, description="ID de la politique QoS parent", type=openapi.TYPE_INTEGER),
            openapi.Parameter('priority', openapi.IN_QUERY, description="Niveau de priorité", type=openapi.TYPE_INTEGER),
            openapi.Parameter('dscp', openapi.IN_QUERY, description="Valeur DSCP (0-63)", type=openapi.TYPE_INTEGER),
        ],
        responses={
            200: openapi.Response("Liste des classes de trafic", TrafficClassSerializer(many=True)),
            400: "Paramètres de filtrage invalides",
            500: "Erreur serveur interne"
        },
        tags=['QoS Management']
    )
    def list(self, request):
        """Liste toutes les classes de trafic."""
        filters = request.query_params.dict()
        policy_id = filters.pop('policy_id', None)
        
        if policy_id:
            try:
                policy_id = int(policy_id)
            except (ValueError, TypeError):
                return Response(
                    {"detail": "policy_id doit être un entier"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Obtenir les classes de trafic
        traffic_classes = self.list_traffic_classes_use_case.execute(policy_id, filters)
        
        # Sérialiser les données
        serializer = TrafficClassSerializer(traffic_classes, many=True)
        
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_summary="Détails d'une classe de trafic",
        operation_description="""
        Récupère les détails complets d'une classe de trafic QoS spécifique.
        
        **Informations retournées :**
        - Configuration complète de la classe de trafic
        - Allocation de bande passante et priorité
        - Valeurs DSCP et configuration des files d'attente
        - Classificateurs associés
        - Politique QoS parente
        """,
        responses={
            200: openapi.Response("Classe de trafic trouvée avec succès", TrafficClassSerializer),
            404: "Classe de trafic non trouvée avec cet identifiant",
            500: "Erreur serveur interne"
        },
        tags=['QoS Management']
    )
    def retrieve(self, request, pk=None):
        """Récupère une classe de trafic spécifique."""
        try:
            traffic_class = self.get_traffic_class_use_case.execute(int(pk))
            serializer = TrafficClassSerializer(traffic_class)
            return Response(serializer.data)
        except TrafficClassNotFoundException as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @swagger_auto_schema(
        operation_summary="Créer une classe de trafic",
        operation_description="""
        Crée une nouvelle classe de trafic QoS avec validation automatique.
        
        **Paramètres requis :**
        - `name` : Nom unique de la classe de trafic
        - `policy` : ID de la politique QoS parente
        - `priority` : Niveau de priorité (1-7)
        - `bandwidth_percent` : Pourcentage de bande passante allouée
        
        **Fonctionnalités :**
        - Validation des paramètres de bande passante
        - Vérification de la cohérence des priorités
        - Configuration automatique des files d'attente
        - Support des valeurs DSCP personnalisées
        """,
        request_body=TrafficClassCreateSerializer,
        responses={
            201: openapi.Response("Classe de trafic créée avec succès", TrafficClassSerializer),
            400: "Données invalides ou limite de bande passante dépassée",
            404: "Politique QoS parente non trouvée",
            500: "Erreur serveur interne"
        },
        tags=['QoS Management']
    )
    def create(self, request):
        """Crée une nouvelle classe de trafic."""
        serializer = TrafficClassCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Créer la classe de trafic avec les données validées
            traffic_class = self.create_traffic_class_use_case.execute(serializer.validated_data)
            
            # Sérialiser la réponse
            response_serializer = TrafficClassSerializer(traffic_class)
            
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
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
        except BandwidthLimitExceededException as e:
            return Response(
                {
                    "detail": str(e),
                    "bandwidth": e.bandwidth,
                    "available": e.available
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'], url_path='by-policy/(?P<policy_id>[^/.]+)')
    @swagger_auto_schema(
        operation_summary="Classes de trafic par politique",
        operation_description="""
        Récupère toutes les classes de trafic associées à une politique QoS spécifique.
        
        **Fonctionnalités :**
        - Liste complète des classes de trafic d'une politique
        - Informations sur l'allocation de bande passante totale
        - Tri par priorité décroissante
        - Validation de l'existence de la politique
        """,
        manual_parameters=[
            openapi.Parameter('policy_id', openapi.IN_PATH, description="ID de la politique QoS", type=openapi.TYPE_INTEGER, required=True),
        ],
        responses={
            200: openapi.Response("Liste des classes de trafic", TrafficClassSerializer(many=True)),
            400: "ID de politique invalide",
            404: "Politique QoS non trouvée",
            500: "Erreur serveur interne"
        },
        tags=['QoS Management']
    )
    def by_policy(self, request, policy_id=None):
        """Récupère les classes de trafic associées à une politique QoS."""
        try:
            # Convertir policy_id en entier
            policy_id = int(policy_id)
            
            # Obtenir les classes de trafic
            traffic_classes = self.list_traffic_classes_use_case.execute(policy_id)
            
            # Sérialiser les données
            serializer = TrafficClassSerializer(traffic_classes, many=True)
            
            return Response(serializer.data)
        except ValueError:
            return Response(
                {"detail": "policy_id doit être un entier"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except QoSPolicyNotFoundException as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['get'])
    @swagger_auto_schema(
        operation_summary="Classificateurs d'une classe de trafic",
        operation_description="""
        Récupère tous les classificateurs de trafic associés à une classe de trafic.
        
        **Informations retournées :**
        - Liste des règles de classification
        - Critères de correspondance (IP, port, protocole, DSCP)
        - Actions associées aux classificateurs
        - Ordre de priorité des règles
        """,
        responses={
            200: openapi.Response("Liste des classificateurs", TrafficClassifierSerializer(many=True)),
            400: "ID de classe de trafic invalide",
            404: "Classe de trafic non trouvée",
            500: "Erreur serveur interne"
        },
        tags=['QoS Management']
    )
    def classifiers(self, request, pk=None):
        """Renvoie les classificateurs associés à cette classe de trafic."""
        try:
            class_id = int(pk)
            
            # Obtenir les classificateurs via le cas d'utilisation
            classifiers = self.list_traffic_classifiers_use_case.execute(class_id)
            
            # Sérialiser les données
            serializer = TrafficClassifierSerializer(classifiers, many=True)
            
            return Response(serializer.data)
        except TrafficClassNotFoundException as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError:
            return Response(
                {"detail": "ID de classe de trafic non valide"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    @swagger_auto_schema(
        operation_summary="Ajouter un classificateur",
        operation_description="""
        Ajoute un nouveau classificateur de trafic à une classe de trafic existante.
        
        **Paramètres requis :**
        - `name` : Nom du classificateur
        - `match_criteria` : Critères de correspondance
        - `priority` : Priorité du classificateur
        
        **Critères de correspondance supportés :**
        - Adresses IP source/destination
        - Ports source/destination
        - Protocoles (TCP, UDP, ICMP)
        - Valeurs DSCP
        - Interfaces réseau
        """,
        request_body=TrafficClassifierCreateSerializer,
        responses={
            201: openapi.Response("Classificateur ajouté avec succès", TrafficClassifierSerializer),
            400: "Données invalides ou classificateur en conflit",
            404: "Classe de trafic non trouvée",
            500: "Erreur serveur interne"
        },
        tags=['QoS Management']
    )
    def add_classifier(self, request, pk=None):
        """Ajoute un classificateur à cette classe de trafic."""
        try:
            serializer = TrafficClassifierCreateSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Ajouter le traffic_class_id aux données validées
            class_id = int(pk)
            classifier_data = {
                **serializer.validated_data,
                "traffic_class_id": class_id
            }
            
            # Créer le classificateur via le cas d'utilisation
            classifier = self.create_traffic_classifier_use_case.execute(classifier_data)
            
            # Sérialiser la réponse
            response_serializer = TrafficClassifierSerializer(classifier)
            
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
        except TrafficClassNotFoundException as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except QoSValidationException as e:
            return Response(
                {"detail": str(e), "errors": e.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValueError:
            return Response(
                {"detail": "ID de classe de trafic non valide"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"detail": f"Une erreur s'est produite: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 