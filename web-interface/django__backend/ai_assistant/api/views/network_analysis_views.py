"""
Vues pour l'analyse réseau.

Ce module contient les vues qui exposent les fonctionnalités
d'analyse réseau via une API REST.
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from ai_assistant.domain.services import NetworkAnalysisService
from ai_assistant.domain.exceptions import NetworkAnalysisError
from ai_assistant.api.serializers import NetworkAnalysisRequestSerializer, NetworkAnalysisResultSerializer


class NetworkAnalysisView(APIView):
    """Vue pour effectuer des analyses réseau."""
    
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.network_analysis_service = NetworkAnalysisService()
    
    def post(self, request):
        """Effectue une analyse réseau."""
        serializer = NetworkAnalysisRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        analysis_type = serializer.validated_data['analysis_type']
        
        try:
            # Effectuer l'analyse en fonction du type
            if analysis_type == 'device_performance':
                device_id = serializer.validated_data['device_id']
                result = self.network_analysis_service.analyze_device_performance(device_id)
            
            elif analysis_type == 'network_traffic':
                network_id = serializer.validated_data['network_id']
                result = self.network_analysis_service.analyze_network_traffic(network_id)
            
            elif analysis_type == 'security_posture':
                network_id = serializer.validated_data['network_id']
                result = self.network_analysis_service.analyze_security_posture(network_id)
            
            elif analysis_type == 'optimization_recommendations':
                network_id = serializer.validated_data['network_id']
                result = self.network_analysis_service.generate_optimization_recommendations(network_id)
            
            elif analysis_type == 'configuration_compliance':
                device_id = serializer.validated_data['device_id']
                compliance_template = serializer.validated_data.get('compliance_template')
                result = self.network_analysis_service.analyze_configuration_compliance(device_id, compliance_template)
            
            elif analysis_type == 'network_topology':
                network_id = serializer.validated_data['network_id']
                result = self.network_analysis_service.analyze_network_topology(network_id)
            
            elif analysis_type == 'network_health':
                network_id = serializer.validated_data['network_id']
                result = self.network_analysis_service.get_network_health_summary(network_id)
            
            else:
                return Response(
                    {"error": f"Type d'analyse non supporté: {analysis_type}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Sérialiser le résultat
            result_serializer = NetworkAnalysisResultSerializer({
                'analysis_type': analysis_type,
                'result': result
            })
            
            return Response(result_serializer.data)
        
        except NetworkAnalysisError as e:
            return Response(
                {
                    "error": str(e),
                    "analysis_type": analysis_type
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        except Exception as e:
            return Response(
                {
                    "error": f"Erreur lors de l'analyse réseau: {str(e)}",
                    "analysis_type": analysis_type
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 