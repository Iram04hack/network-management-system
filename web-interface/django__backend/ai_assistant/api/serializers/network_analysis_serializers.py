"""
Sérialiseurs pour l'analyse réseau.

Ce module contient les sérialiseurs pour convertir les modèles
d'analyse réseau en représentations JSON pour l'API.
"""

from rest_framework import serializers


class NetworkAnalysisRequestSerializer(serializers.Serializer):
    """Sérialiseur pour les requêtes d'analyse réseau."""
    
    analysis_type = serializers.ChoiceField(
        choices=[
            'device_performance',
            'network_traffic',
            'security_posture',
            'optimization_recommendations',
            'configuration_compliance',
            'network_topology',
            'network_health',
        ]
    )
    network_id = serializers.CharField(required=False)
    device_id = serializers.CharField(required=False)
    compliance_template = serializers.CharField(required=False)
    
    def validate(self, data):
        """Valide les données de la requête."""
        analysis_type = data.get('analysis_type')
        
        # Vérifier que les champs requis sont présents en fonction du type d'analyse
        if analysis_type in ['device_performance', 'configuration_compliance'] and 'device_id' not in data:
            raise serializers.ValidationError(f"Le champ 'device_id' est requis pour l'analyse de type '{analysis_type}'")
        
        if analysis_type in ['network_traffic', 'security_posture', 'optimization_recommendations', 'network_topology', 'network_health'] and 'network_id' not in data:
            raise serializers.ValidationError(f"Le champ 'network_id' est requis pour l'analyse de type '{analysis_type}'")
        
        return data


class NetworkAnalysisResultSerializer(serializers.Serializer):
    """Sérialiseur pour les résultats d'analyse réseau."""
    
    analysis_type = serializers.CharField()
    result = serializers.DictField() 