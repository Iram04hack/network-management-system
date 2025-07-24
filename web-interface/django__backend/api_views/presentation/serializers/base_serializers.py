"""
Sérialiseurs de base pour le module API Views.

Ce module contient les sérialiseurs de base qui fournissent des fonctionnalités
communes de validation et de transformation des données.
"""

from typing import Dict, Any, List, Optional
from rest_framework import serializers
from rest_framework.exceptions import ValidationError as DRFValidationError
import uuid
import re

from ...application.validation import ValidationMixin


class BaseAPISerializer(ValidationMixin, serializers.Serializer):
    """
    Sérialiseur de base pour toutes les API du système.
    
    Fournit des fonctionnalités communes :
    - Validation standardisée
    - Gestion d'erreurs cohérente
    - Transformation de données
    - Méthodes utilitaires
    """
    
    # Champs communs optionnels
    id = serializers.UUIDField(read_only=True, required=False)
    created_at = serializers.DateTimeField(read_only=True, required=False)
    updated_at = serializers.DateTimeField(read_only=True, required=False)
    
    def __init__(self, *args, **kwargs):
        # Support pour les contextes personnalisés
        self.request_context = kwargs.pop('request_context', {})
        super().__init__(*args, **kwargs)
    
    def validate(self, data):
        """
        Validation cross-field personnalisée.
        
        Args:
            data: Données validées
            
        Returns:
            Données validées et enrichies
            
        Raises:
            ValidationError: Si les données ne sont pas valides
        """
        # Appliquer la validation de base
        data = super().validate(data)
        
        # Validation contextuelle selon le type d'utilisateur
        if hasattr(self, 'context') and 'request' in self.context:
            user = self.context['request'].user
            data = self._validate_user_permissions(data, user)
        
        # Validation métier spécifique
        data = self._validate_business_rules(data)
        
        return data
    
    def _validate_user_permissions(self, data: Dict[str, Any], user) -> Dict[str, Any]:
        """
        Valide les permissions utilisateur pour les données.
        
        Args:
            data: Données à valider
            user: Utilisateur de la requête
            
        Returns:
            Données validées
            
        Raises:
            ValidationError: Si l'utilisateur n'a pas les permissions
        """
        # Validation basique des permissions
        if not user.is_authenticated:
            raise DRFValidationError("Authentification requise")
        
        # Les utilisateurs non-staff ne peuvent pas modifier certains champs
        if not user.is_staff:
            restricted_fields = getattr(self.Meta, 'staff_only_fields', [])
            for field in restricted_fields:
                if field in data:
                    raise DRFValidationError(
                        f"Le champ '{field}' nécessite des privilèges administrateur"
                    )
        
        return data
    
    def _validate_business_rules(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valide les règles métier spécifiques.
        
        Args:
            data: Données à valider
            
        Returns:
            Données validées
            
        Raises:
            ValidationError: Si les règles métier ne sont pas respectées
        """
        # Validation de base - peut être overridée dans les sous-classes
        return data
    
    def validate_uuid_field(self, value: str, field_name: str) -> uuid.UUID:
        """
        Valide un champ UUID.
        
        Args:
            value: Valeur à valider
            field_name: Nom du champ pour les messages d'erreur
            
        Returns:
            UUID validé
            
        Raises:
            ValidationError: Si l'UUID n'est pas valide
        """
        try:
            return uuid.UUID(str(value))
        except (ValueError, TypeError):
            raise DRFValidationError(f"'{field_name}' doit être un UUID valide")
    
    def validate_ip_address(self, value: str) -> str:
        """
        Valide une adresse IP.
        
        Args:
            value: Adresse IP à valider
            
        Returns:
            Adresse IP validée
            
        Raises:
            ValidationError: Si l'adresse IP n'est pas valide
        """
        # Pattern pour IPv4
        ipv4_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        
        if not re.match(ipv4_pattern, value):
            raise DRFValidationError("Adresse IP IPv4 invalide")
        
        return value
    
    def validate_port_number(self, value: int) -> int:
        """
        Valide un numéro de port.
        
        Args:
            value: Numéro de port à valider
            
        Returns:
            Port validé
            
        Raises:
            ValidationError: Si le port n'est pas valide
        """
        if not isinstance(value, int) or not (1 <= value <= 65535):
            raise DRFValidationError("Le port doit être un entier entre 1 et 65535")
        
        return value
    
    def to_representation(self, instance):
        """
        Personnalise la représentation des données.
        
        Args:
            instance: Instance à sérialiser
            
        Returns:
            Données sérialisées
        """
        data = super().to_representation(instance)
        
        # Supprimer les champs None selon la configuration
        if getattr(self.Meta, 'exclude_none_fields', False):
            data = {k: v for k, v in data.items() if v is not None}
        
        # Ajouter des métadonnées si demandées
        if getattr(self.Meta, 'include_metadata', False):
            data['_metadata'] = self._get_metadata(instance)
        
        return data
    
    def _get_metadata(self, instance) -> Dict[str, Any]:
        """
        Génère les métadonnées pour l'instance.
        
        Args:
            instance: Instance pour laquelle générer les métadonnées
            
        Returns:
            Métadonnées
        """
        metadata = {
            'serializer': self.__class__.__name__,
            'timestamp': self.context.get('request_timestamp') if hasattr(self, 'context') else None
        }
        
        # Ajouter l'ID utilisateur si disponible
        if hasattr(self, 'context') and 'request' in self.context:
            user = self.context['request'].user
            if user.is_authenticated:
                metadata['user_id'] = user.id
        
        return metadata
    
    class Meta:
        # Configuration par défaut
        exclude_none_fields = True
        include_metadata = False
        staff_only_fields = []


class PaginatedResponseSerializer(serializers.Serializer):
    """
    Sérialiseur pour les réponses paginées.
    """
    count = serializers.IntegerField(help_text="Nombre total d'éléments")
    next = serializers.URLField(allow_null=True, help_text="URL de la page suivante")
    previous = serializers.URLField(allow_null=True, help_text="URL de la page précédente")
    page = serializers.IntegerField(help_text="Numéro de la page actuelle")
    page_size = serializers.IntegerField(help_text="Nombre d'éléments par page")
    total_pages = serializers.IntegerField(help_text="Nombre total de pages")
    results = serializers.ListField(help_text="Résultats de la page actuelle")


class ErrorResponseSerializer(serializers.Serializer):
    """
    Sérialiseur pour les réponses d'erreur standardisées.
    """
    error = serializers.CharField(help_text="Message d'erreur principal")
    error_code = serializers.CharField(required=False, help_text="Code d'erreur spécifique")
    details = serializers.DictField(required=False, help_text="Détails supplémentaires sur l'erreur")
    timestamp = serializers.DateTimeField(help_text="Horodatage de l'erreur")
    request_id = serializers.UUIDField(required=False, help_text="ID de la requête pour le suivi")
    
    def validate_error_code(self, value):
        """Valide le code d'erreur."""
        valid_codes = [
            'VALIDATION_ERROR', 'PERMISSION_DENIED', 'NOT_FOUND',
            'INTERNAL_ERROR', 'RATE_LIMITED', 'SERVICE_UNAVAILABLE'
        ]
        
        if value and value not in valid_codes:
            raise DRFValidationError(f"Code d'erreur invalide: {value}")
        
        return value


class SuccessResponseSerializer(serializers.Serializer):
    """
    Sérialiseur pour les réponses de succès standardisées.
    """
    success = serializers.BooleanField(default=True, help_text="Indicateur de succès")
    message = serializers.CharField(help_text="Message de succès")
    data = serializers.DictField(required=False, help_text="Données de la réponse")
    timestamp = serializers.DateTimeField(help_text="Horodatage de la réponse")
    request_id = serializers.UUIDField(required=False, help_text="ID de la requête pour le suivi")


class FilterSerializer(BaseAPISerializer):
    """
    Sérialiseur de base pour les filtres de recherche.
    """
    search = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Terme de recherche général"
    )
    ordering = serializers.CharField(
        required=False,
        help_text="Champ pour l'ordre (préfixer avec '-' pour décroissant)"
    )
    limit = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=1000,
        default=20,
        help_text="Nombre maximum de résultats"
    )
    offset = serializers.IntegerField(
        required=False,
        min_value=0,
        default=0,
        help_text="Décalage pour la pagination"
    )
    
    def validate_ordering(self, value):
        """Valide le champ d'ordonnancement."""
        if not value:
            return value
        
        # Supprimer le préfixe '-' pour la validation
        field_name = value.lstrip('-')
        
        # Valider que le champ existe dans les champs autorisés
        allowed_fields = getattr(self.Meta, 'ordering_fields', [])
        if allowed_fields and field_name not in allowed_fields:
            raise DRFValidationError(
                f"Ordonnancement par '{field_name}' non autorisé. "
                f"Champs autorisés: {', '.join(allowed_fields)}"
            )
        
        return value
    
    class Meta:
        ordering_fields = []  # À définir dans les sous-classes 