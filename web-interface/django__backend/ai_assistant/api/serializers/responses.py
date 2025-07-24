"""
Sérialisateurs pour les réponses API.

Ce module contient les sérialisateurs pour formater les données
de sortie des réponses API.
"""

from rest_framework import serializers
from .entities import MessageSerializer, ConversationSerializer, DocumentSerializer, SearchResultSerializer


class MessageResponseSerializer(serializers.Serializer):
    """Sérialisateur pour les réponses aux messages."""
    
    message = MessageSerializer()
    conversation = ConversationSerializer()
    processing_time = serializers.FloatField()
    model_info = serializers.DictField(required=False)
    
    def to_representation(self, instance):
        """
        Convertit les données de réponse en dictionnaire.
        
        Args:
            instance: Données de réponse
            
        Returns:
            Dictionnaire formaté pour la réponse API
        """
        data = super().to_representation(instance)
        
        # Ajouter des informations supplémentaires
        if 'model_info' in data and isinstance(data['model_info'], dict):
            # Formater les informations sur l'utilisation des tokens
            usage = data['model_info'].get('usage', {})
            if usage:
                data['model_info']['usage_summary'] = (
                    f"Tokens: {usage.get('total_tokens', 0)} total "
                    f"({usage.get('prompt_tokens', 0)} entrée, "
                    f"{usage.get('completion_tokens', 0)} sortie)"
                )
        
        return data


class CommandResponseSerializer(serializers.Serializer):
    """Sérialisateur pour les réponses aux commandes."""
    
    success = serializers.BooleanField()
    output = serializers.CharField(allow_blank=True)
    error = serializers.CharField(allow_blank=True, required=False)
    exit_code = serializers.IntegerField()
    execution_time = serializers.FloatField(required=False)
    safety_analysis = serializers.DictField(required=False)
    
    def to_representation(self, instance):
        """
        Convertit les données de réponse en dictionnaire.
        
        Args:
            instance: Données de réponse
            
        Returns:
            Dictionnaire formaté pour la réponse API
        """
        data = super().to_representation(instance)
        
        # Ajouter un résumé du statut
        if data.get('success'):
            data['status_summary'] = "Commande exécutée avec succès"
            if 'execution_time' in data:
                data['status_summary'] += f" en {data['execution_time']:.2f} secondes"
        else:
            data['status_summary'] = f"Échec de la commande (code {data.get('exit_code', 'inconnu')})"
        
        # Tronquer les sorties longues
        if 'output' in data and len(data['output']) > 5000:
            data['output'] = data['output'][:5000] + '... (tronqué)'
        if 'error' in data and len(data['error']) > 1000:
            data['error'] = data['error'][:1000] + '... (tronqué)'
        
        return data


class SearchResponseSerializer(serializers.Serializer):
    """Sérialisateur pour les réponses aux recherches."""
    
    results = SearchResultSerializer(many=True)
    query = serializers.CharField()
    total_results = serializers.IntegerField()
    processing_time = serializers.FloatField(required=False)
    
    def to_representation(self, instance):
        """
        Convertit les données de réponse en dictionnaire.
        
        Args:
            instance: Données de réponse
            
        Returns:
            Dictionnaire formaté pour la réponse API
        """
        data = super().to_representation(instance)
        
        # Ajouter un résumé des résultats
        result_count = len(data.get('results', []))
        total = data.get('total_results', result_count)
        
        if result_count == 0:
            data['summary'] = "Aucun résultat trouvé"
        elif result_count == 1:
            data['summary'] = "1 résultat trouvé"
        elif result_count < total:
            data['summary'] = f"{result_count} résultats affichés sur {total} trouvés"
        else:
            data['summary'] = f"{result_count} résultats trouvés"
        
        if 'processing_time' in data:
            data['summary'] += f" en {data['processing_time']:.2f} secondes"
        
        return data


class DocumentResponseSerializer(serializers.Serializer):
    """Sérialisateur pour les réponses aux opérations sur les documents."""
    
    id = serializers.CharField()
    title = serializers.CharField()
    content_preview = serializers.CharField()
    metadata = serializers.DictField(required=False)
    
    def to_representation(self, instance):
        """
        Convertit les données de réponse en dictionnaire.
        
        Args:
            instance: Données de réponse
            
        Returns:
            Dictionnaire formaté pour la réponse API
        """
        if isinstance(instance, dict) and 'id' in instance:
            # Si c'est déjà un dictionnaire formaté
            return super().to_representation(instance)
        
        # Sinon, créer un dictionnaire à partir de l'instance
        document_dict = {
            'id': instance.id if hasattr(instance, 'id') else None,
            'title': instance.title,
            'content_preview': instance.content[:200] + '...' if len(instance.content) > 200 else instance.content,
            'metadata': instance.metadata
        }
        
        return super().to_representation(document_dict)


class NetworkAnalysisResponseSerializer(serializers.Serializer):
    """Sérialisateur pour les réponses aux analyses réseau."""
    
    topology = serializers.DictField(required=False)
    raw_data = serializers.DictField(required=False)
    recommendations = serializers.ListField(required=False)
    processing_time = serializers.FloatField(required=False)
    
    def to_representation(self, instance):
        """
        Convertit les données de réponse en dictionnaire.
        
        Args:
            instance: Données de réponse
            
        Returns:
            Dictionnaire formaté pour la réponse API
        """
        data = super().to_representation(instance)
        
        # Ajouter un résumé des résultats
        if 'topology' in data:
            interfaces = data['topology'].get('interfaces', [])
            routes = data['topology'].get('routes', [])
            open_ports = data['topology'].get('open_ports', [])
            
            summary_parts = []
            if interfaces:
                summary_parts.append(f"{len(interfaces)} interface(s)")
            if routes:
                summary_parts.append(f"{len(routes)} route(s)")
            if open_ports:
                summary_parts.append(f"{len(open_ports)} port(s) ouvert(s)")
            
            if summary_parts:
                data['summary'] = "Analyse de topologie: " + ", ".join(summary_parts)
            else:
                data['summary'] = "Analyse de topologie effectuée"
        else:
            data['summary'] = "Analyse réseau effectuée"
        
        if 'processing_time' in data:
            data['summary'] += f" en {data['processing_time']:.2f} secondes"
        
        return data


class ErrorResponseSerializer(serializers.Serializer):
    """Sérialisateur pour les réponses d'erreur."""
    
    error = serializers.CharField()
    error_type = serializers.CharField(required=False)
    detail = serializers.CharField(required=False)
    status_code = serializers.IntegerField(required=False)
    
    def to_representation(self, instance):
        """
        Convertit les données d'erreur en dictionnaire.
        
        Args:
            instance: Données d'erreur
            
        Returns:
            Dictionnaire formaté pour la réponse API
        """
        data = super().to_representation(instance)
        
        # Ajouter un message d'erreur formaté
        error_msg = data.get('error', 'Une erreur est survenue')
        error_type = data.get('error_type', '')
        
        if error_type:
            data['error_message'] = f"{error_type}: {error_msg}"
        else:
            data['error_message'] = error_msg
        
        return data 