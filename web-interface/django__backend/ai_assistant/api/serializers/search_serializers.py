"""
Sérialiseurs pour la recherche.

Ce module contient les sérialiseurs pour convertir les modèles
de résultat de recherche en représentations JSON pour l'API.
"""

from rest_framework import serializers


class SearchResultSerializer(serializers.Serializer):
    """Sérialiseur pour les résultats de recherche."""
    
    id = serializers.CharField(read_only=True)
    title = serializers.CharField()
    content = serializers.CharField()
    score = serializers.FloatField()
    metadata = serializers.DictField()
    
    def to_representation(self, instance):
        """Personnalise la représentation de l'instance."""
        data = super().to_representation(instance)
        
        # Limiter la taille du contenu si nécessaire
        content_limit = self.context.get('content_limit')
        if content_limit is not None and isinstance(content_limit, int) and len(data['content']) > content_limit:
            data['content'] = data['content'][:content_limit] + "..."
            data['content_truncated'] = True
        else:
            data['content_truncated'] = False
        
        return data


class SearchQuerySerializer(serializers.Serializer):
    """Sérialiseur pour les requêtes de recherche."""
    
    query = serializers.CharField()
    max_results = serializers.IntegerField(required=False, default=5, min_value=1, max_value=20)
    content_limit = serializers.IntegerField(required=False, default=200, min_value=50, max_value=1000) 