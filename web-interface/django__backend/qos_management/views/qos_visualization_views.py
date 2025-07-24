from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import logging
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..di_container import qos_container
from ..application.use_cases import GetQoSVisualizationUseCase
from .mixins import QoSPermissionMixin

logger = logging.getLogger(__name__)

class QoSVisualizationView(QoSPermissionMixin, APIView):
    """
    Visualisation temps réel des métriques et performances QoS.
    
    Fournit des données enrichies pour les dashboards de monitoring QoS :
    - Utilisation de la bande passante par classe de trafic
    - Métriques de performance en temps réel (latence, perte de paquets)
    - Graphiques d'allocation et consommation des ressources
    - Indicateurs de conformité SLA et alertes
    - Historiques de performance et tendances
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialiser les dépendances via le conteneur
        from ..di_container import resolve
        self.get_visualization_use_case = resolve(GetQoSVisualizationUseCase)
    
    @swagger_auto_schema(
        operation_summary="Données de visualisation QoS",
        operation_description="""
        Récupère les données de visualisation temps réel pour une politique QoS spécifique.
        
        **Métriques incluses :**
        - Utilisation de bande passante actuelle vs. allouée
        - Performance par classe de trafic (latence, jitter, perte)
        - Distribution du trafic entre les classes
        - Conformité SLA et indicateurs de santé
        - Tendances d'utilisation et pics de charge
        
        **Formats de visualisation :**
        - Graphiques en barres pour l'allocation
        - Graphiques circulaires pour la distribution
        - Séries temporelles pour les tendances
        - Indicateurs de statut et alertes
        """,
        manual_parameters=[
            openapi.Parameter('policy_id', openapi.IN_PATH, description="ID de la politique QoS (optionnel)", type=openapi.TYPE_INTEGER),
        ],
        responses={
            200: openapi.Response("Données de visualisation QoS", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'policy_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID de la politique"),
                    'policy_name': openapi.Schema(type=openapi.TYPE_STRING, description="Nom de la politique"),
                    'bandwidth_limit': openapi.Schema(type=openapi.TYPE_INTEGER, description="Limite de bande passante (kbps)"),
                    'traffic_classes': openapi.Schema(
                        type=openapi.TYPE_ARRAY, 
                        description="Classes de trafic configurées",
                        items=openapi.Schema(type=openapi.TYPE_OBJECT)
                    ),
                    'traffic_data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        description="Données de trafic temps réel",
                        properties={
                            'current_usage': openapi.Schema(type=openapi.TYPE_NUMBER, description="Utilisation actuelle"),
                            'peak_usage': openapi.Schema(type=openapi.TYPE_NUMBER, description="Pic d'utilisation"),
                            'average_usage': openapi.Schema(type=openapi.TYPE_NUMBER, description="Utilisation moyenne")
                        }
                    )
                }
            )),
            400: "ID de politique invalide",
            404: "Politique QoS non trouvée",
            500: "Erreur serveur interne"
        },
        tags=['QoS Management']
    )
    def get(self, request, policy_id=None):
        """
        Obtenir les données de visualisation d'une politique QoS
        
        Args:
            policy_id: ID de la politique QoS à visualiser
            
        Returns:
            Données de visualisation pour la politique spécifiée
            
        Raises:
            404: Si la politique n'existe pas
            500: En cas d'erreur serveur
        """
        # Vérifier que l'ID de politique est fourni
        if policy_id is None:
            return Response(
                {'error': 'Un ID de politique QoS est requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Valider que l'ID est un entier positif
            if isinstance(policy_id, str) and not policy_id.isdigit():
                return Response(
                    {'error': "L'ID de politique doit être un nombre entier"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Exécuter le cas d'utilisation
            visualization_data = self.get_visualization_use_case.execute(policy_id)
            
            # Convertir l'objet de domaine en dictionnaire pour la réponse
            result = {
                'policy_id': visualization_data.policy_id,
                'policy_name': visualization_data.policy_name,
                'bandwidth_limit': visualization_data.bandwidth_limit,
                'traffic_classes': visualization_data.traffic_classes,
                'traffic_data': visualization_data.traffic_data
            }
            
            return Response(result)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(f"Erreur lors de la récupération des données de visualisation: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 