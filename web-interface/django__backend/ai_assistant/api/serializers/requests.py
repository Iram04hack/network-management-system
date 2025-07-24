"""
Sérialisateurs pour les requêtes API.

Ce module contient les sérialisateurs pour valider et traiter
les données entrantes des requêtes API.
"""

from rest_framework import serializers


class MessageRequestSerializer(serializers.Serializer):
    """Sérialisateur pour les requêtes de messages."""
    
    content = serializers.CharField(required=True)
    conversation_id = serializers.CharField(required=False, allow_null=True)
    
    def validate_content(self, value):
        """
        Valide le contenu du message.
        
        Args:
            value: Contenu du message
            
        Returns:
            Contenu validé
            
        Raises:
            ValidationError: Si le contenu est vide ou trop long
        """
        if not value.strip():
            raise serializers.ValidationError("Le contenu du message ne peut pas être vide.")
        
        if len(value) > 10000:
            raise serializers.ValidationError("Le contenu du message est trop long (maximum 10000 caractères).")
        
        return value


class CommandRequestSerializer(serializers.Serializer):
    """Sérialisateur pour les requêtes de commandes."""
    
    command = serializers.CharField(required=True)
    command_type = serializers.CharField(required=False, default="shell")
    conversation_id = serializers.CharField(required=False, allow_null=True)
    
    def validate_command(self, value):
        """
        Valide la commande.
        
        Args:
            value: Commande à exécuter
            
        Returns:
            Commande validée
            
        Raises:
            ValidationError: Si la commande est vide ou trop longue
        """
        if not value.strip():
            raise serializers.ValidationError("La commande ne peut pas être vide.")
        
        if len(value) > 1000:
            raise serializers.ValidationError("La commande est trop longue (maximum 1000 caractères).")
        
        return value
    
    def validate_command_type(self, value):
        """
        Valide le type de commande.
        
        Args:
            value: Type de commande
            
        Returns:
            Type de commande validé
            
        Raises:
            ValidationError: Si le type de commande n'est pas valide
        """
        valid_types = ["shell", "sql", "python"]
        if value not in valid_types:
            raise serializers.ValidationError(f"Le type de commande doit être l'un des suivants: {', '.join(valid_types)}.")
        
        return value


class SearchRequestSerializer(serializers.Serializer):
    """Sérialisateur pour les requêtes de recherche."""
    
    query = serializers.CharField(required=True)
    max_results = serializers.IntegerField(required=False, default=5, min_value=1, max_value=50)
    
    def validate_query(self, value):
        """
        Valide la requête de recherche.
        
        Args:
            value: Requête de recherche
            
        Returns:
            Requête validée
            
        Raises:
            ValidationError: Si la requête est vide ou trop longue
        """
        if not value.strip():
            raise serializers.ValidationError("La requête de recherche ne peut pas être vide.")
        
        if len(value) > 500:
            raise serializers.ValidationError("La requête de recherche est trop longue (maximum 500 caractères).")
        
        return value


class DocumentRequestSerializer(serializers.Serializer):
    """Sérialisateur pour les requêtes de documents."""
    
    title = serializers.CharField(required=True)
    content = serializers.CharField(required=True)
    metadata = serializers.DictField(required=False, default=dict)
    
    def validate_title(self, value):
        """
        Valide le titre du document.
        
        Args:
            value: Titre du document
            
        Returns:
            Titre validé
            
        Raises:
            ValidationError: Si le titre est vide ou trop long
        """
        if not value.strip():
            raise serializers.ValidationError("Le titre du document ne peut pas être vide.")
        
        if len(value) > 200:
            raise serializers.ValidationError("Le titre du document est trop long (maximum 200 caractères).")
        
        return value
    
    def validate_content(self, value):
        """
        Valide le contenu du document.
        
        Args:
            value: Contenu du document
            
        Returns:
            Contenu validé
            
        Raises:
            ValidationError: Si le contenu est vide ou trop long
        """
        if not value.strip():
            raise serializers.ValidationError("Le contenu du document ne peut pas être vide.")
        
        if len(value) > 100000:
            raise serializers.ValidationError("Le contenu du document est trop long (maximum 100000 caractères).")
        
        return value


class NetworkAnalysisRequestSerializer(serializers.Serializer):
    """Sérialisateur pour les requêtes d'analyse réseau."""
    
    analysis_type = serializers.CharField(required=False, default="topology")
    target_hosts = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    
    def validate_analysis_type(self, value):
        """
        Valide le type d'analyse.
        
        Args:
            value: Type d'analyse
            
        Returns:
            Type d'analyse validé
            
        Raises:
            ValidationError: Si le type d'analyse n'est pas valide
        """
        valid_types = ["topology", "performance", "security", "full"]
        if value not in valid_types:
            raise serializers.ValidationError(f"Le type d'analyse doit être l'un des suivants: {', '.join(valid_types)}.")
        
        return value 