"""
Sérialiseurs pour les documents.

Ce module contient les sérialiseurs pour convertir les modèles
de document en représentations JSON pour l'API.
"""

from rest_framework import serializers


class DocumentSerializer(serializers.Serializer):
    """Sérialiseur pour les documents."""
    
    id = serializers.CharField(read_only=True)
    title = serializers.CharField()
    content = serializers.CharField()
    metadata = serializers.DictField(required=False)
    
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


class DocumentCreateSerializer(serializers.Serializer):
    """Sérialiseur pour la création de documents."""
    
    title = serializers.CharField()
    content = serializers.CharField()
    metadata = serializers.DictField(required=False) 