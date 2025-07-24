"""
Sérialiseurs pour les conversations et les messages.

Ce module contient les sérialiseurs pour convertir les modèles
de conversation et de message en représentations JSON pour l'API.
"""

from rest_framework import serializers


class MessageSerializer(serializers.Serializer):
    """Sérialiseur pour les messages."""
    
    id = serializers.CharField(read_only=True)
    role = serializers.CharField()
    content = serializers.CharField()
    timestamp = serializers.DateTimeField(read_only=True)
    metadata = serializers.DictField(required=False)
    actions_taken = serializers.ListField(required=False, child=serializers.DictField())


class MessageCreateSerializer(serializers.Serializer):
    """Sérialiseur pour la création de messages."""
    
    role = serializers.CharField()
    content = serializers.CharField()
    metadata = serializers.DictField(required=False)


class ConversationSerializer(serializers.Serializer):
    """Sérialiseur pour les conversations."""
    
    id = serializers.CharField(read_only=True)
    title = serializers.CharField()
    user_id = serializers.CharField(read_only=True)
    messages = MessageSerializer(many=True, read_only=True)
    context = serializers.CharField(required=False, allow_blank=True)
    metadata = serializers.DictField(required=False)
    
    def to_representation(self, instance):
        """Personnalise la représentation de l'instance."""
        data = super().to_representation(instance)
        
        # Limiter le nombre de messages retournés si nécessaire
        limit = self.context.get('message_limit')
        if limit is not None and isinstance(limit, int):
            data['messages'] = data['messages'][-limit:]
        
        return data


class ConversationCreateSerializer(serializers.Serializer):
    """Sérialiseur pour la création de conversations."""
    
    title = serializers.CharField(required=False)
    context = serializers.CharField(required=False, allow_blank=True)
    initial_message = serializers.CharField(required=False) 