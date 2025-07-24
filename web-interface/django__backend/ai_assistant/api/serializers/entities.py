"""
Sérialisateurs pour les entités du domaine.

Ce module contient les sérialisateurs pour convertir les entités du domaine
en représentations JSON et vice-versa.
"""

from rest_framework import serializers


class MessageSerializer(serializers.Serializer):
    """Sérialisateur pour l'entité Message."""
    
    id = serializers.CharField(required=False, allow_null=True)
    role = serializers.CharField()
    content = serializers.CharField()
    timestamp = serializers.DateTimeField(required=False)
    metadata = serializers.DictField(required=False, default=dict)
    actions_taken = serializers.ListField(required=False, default=list)
    
    def to_representation(self, instance):
        """
        Convertit une instance de Message en dictionnaire.
        
        Args:
            instance: Instance de Message
            
        Returns:
            Dictionnaire représentant le message
        """
        data = super().to_representation(instance)
        
        # Formatage des actions pour une meilleure lisibilité
        if data.get('actions_taken'):
            for action in data['actions_taken']:
                if 'result' in action and isinstance(action['result'], dict):
                    # Tronquer les sorties longues pour une meilleure lisibilité
                    if 'output' in action['result'] and len(action['result']['output']) > 500:
                        action['result']['output'] = action['result']['output'][:500] + '... (tronqué)'
        
        return data


class ConversationSerializer(serializers.Serializer):
    """Sérialisateur pour l'entité Conversation."""
    
    id = serializers.CharField(required=False, allow_null=True)
    title = serializers.CharField()
    user_id = serializers.CharField()
    messages = MessageSerializer(many=True, required=False, default=list)
    context = serializers.CharField(required=False, allow_blank=True, default='')
    metadata = serializers.DictField(required=False, default=dict)
    
    def to_representation(self, instance):
        """
        Convertit une instance de Conversation en dictionnaire.
        
        Args:
            instance: Instance de Conversation
            
        Returns:
            Dictionnaire représentant la conversation
        """
        data = super().to_representation(instance)
        
        # Ajouter des informations supplémentaires
        data['message_count'] = len(data.get('messages', []))
        
        # Déterminer le dernier message pour un aperçu
        if data.get('messages'):
            last_message = data['messages'][-1]
            data['last_message'] = {
                'role': last_message['role'],
                'content_preview': last_message['content'][:100] + '...' if len(last_message['content']) > 100 else last_message['content'],
                'timestamp': last_message['timestamp']
            }
        else:
            data['last_message'] = None
        
        return data


class DocumentSerializer(serializers.Serializer):
    """Sérialisateur pour l'entité Document."""
    
    id = serializers.CharField(required=False, allow_null=True)
    title = serializers.CharField()
    content = serializers.CharField()
    metadata = serializers.DictField(required=False, default=dict)
    
    def to_representation(self, instance):
        """
        Convertit une instance de Document en dictionnaire.
        
        Args:
            instance: Instance de Document
            
        Returns:
            Dictionnaire représentant le document
        """
        data = super().to_representation(instance)
        
        # Ajouter un aperçu du contenu
        content = data.get('content', '')
        data['content_preview'] = content[:200] + '...' if len(content) > 200 else content
        
        return data


class SearchResultSerializer(serializers.Serializer):
    """Sérialisateur pour l'entité SearchResult."""
    
    id = serializers.CharField(required=False, allow_null=True)
    title = serializers.CharField()
    content = serializers.CharField()
    metadata = serializers.DictField(required=False, default=dict)
    score = serializers.FloatField()
    
    def to_representation(self, instance):
        """
        Convertit une instance de SearchResult en dictionnaire.
        
        Args:
            instance: Instance de SearchResult
            
        Returns:
            Dictionnaire représentant le résultat de recherche
        """
        data = super().to_representation(instance)
        
        # Ajouter un aperçu du contenu
        content = data.get('content', '')
        data['content_preview'] = content[:200] + '...' if len(content) > 200 else content
        
        # Formater le score pour une meilleure lisibilité
        data['relevance'] = f"{data.get('score', 0) * 100:.1f}%"
        
        return data


class CommandResultSerializer(serializers.Serializer):
    """Sérialisateur pour l'entité CommandResult."""
    
    command = serializers.CharField()
    exit_code = serializers.IntegerField()
    stdout = serializers.CharField(allow_blank=True)
    stderr = serializers.CharField(allow_blank=True)
    success = serializers.BooleanField()
    
    def to_representation(self, instance):
        """
        Convertit une instance de CommandResult en dictionnaire.
        
        Args:
            instance: Instance de CommandResult
            
        Returns:
            Dictionnaire représentant le résultat de commande
        """
        data = super().to_representation(instance)
        
        # Tronquer les sorties longues pour une meilleure lisibilité
        if 'stdout' in data and len(data['stdout']) > 1000:
            data['stdout'] = data['stdout'][:1000] + '... (tronqué)'
        if 'stderr' in data and len(data['stderr']) > 1000:
            data['stderr'] = data['stderr'][:1000] + '... (tronqué)'
        
        return data 