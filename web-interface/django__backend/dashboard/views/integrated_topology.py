"""
Vue intégrée de la topologie.

Cette vue fournit la visualisation enrichie d'une topologie réseau avec des informations
sur les équipements, les connexions et leur état de santé.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
import logging
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from dashboard.di_container import container

logger = logging.getLogger(__name__)

class IntegratedTopologyView(APIView):
    """Vue intégrée de la topologie avec informations d'anomalies et QoS"""
    permission_classes = [permissions.IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.integrated_topology_use_case = container.get_service('topology_service')
        except Exception as e:
            logger.warning(f"Erreur lors de l'initialisation du service: {e}")
            self.integrated_topology_use_case = None
    
    @swagger_auto_schema(
        operation_summary="Topologie intégrée détaillée",
        operation_description="Récupère les détails d'une topologie réseau spécifique avec informations enrichies (équipements, connexions, état de santé, anomalies, QoS)",
        manual_parameters=[
            openapi.Parameter(
                'topology_id',
                openapi.IN_PATH,
                description="ID de la topologie à récupérer",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Topologie récupérée avec succès",
                examples={
                    "application/json": {
                        "topology_id": 1,
                        "nodes": [
                            {"id": "router-1", "name": "Router-01", "type": "router", "status": "healthy"}
                        ],
                        "links": [
                            {"source": "router-1", "target": "switch-1", "status": "up", "qos": "normal"}
                        ],
                        "health_status": "good"
                    }
                }
            ),
            404: "Topologie non trouvée",
            401: "Non authentifié",
            500: "Erreur serveur"
        },
        tags=['Dashboard']
    )
    def get(self, request, topology_id):
        """Obtenir les détails d'une topologie avec informations enrichies"""
        try:
            if self.integrated_topology_use_case:
                # Utiliser le service pour récupérer la topologie intégrée
                import asyncio
                
                async def get_topology_data():
                    return await self.integrated_topology_use_case.get_integrated_topology(int(topology_id))
                
                topology_data = asyncio.run(get_topology_data())
                
                # Convertir l'objet TopologyView en dictionnaire
                result_dict = {
                    "topology_id": getattr(topology_data, 'topology_id', topology_id),
                    "name": getattr(topology_data, 'name', f'Topology {topology_id}'),
                    "nodes": getattr(topology_data, 'devices', []),
                    "links": getattr(topology_data, 'connections', []),
                    "layout": getattr(topology_data, 'layout', 'auto'),
                    "metadata": getattr(topology_data, 'metadata', {}),
                    "health_status": "good" if getattr(topology_data, 'devices', []) else "unknown"
                }
                return Response(result_dict)
            else:
                # Fallback: retourner des données par défaut
                result = {
                    "topology_id": topology_id,
                    "nodes": [],
                    "links": [],
                    "health_status": "unknown"
                }
                return Response(result)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(f"Erreur lors de la récupération des données de topologie intégrée: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )