"""
Sérialiseurs pour les fonctionnalités de recherche API.

Ce module contient les sérialiseurs spécialisés pour la validation et transformation
des données de recherche dans les API du système de gestion de réseau.
"""

from typing import Dict, Any, List, Optional
from rest_framework import serializers
from rest_framework.exceptions import ValidationError as DRFValidationError

from .base_serializers import BaseAPISerializer, FilterSerializer


class SearchRequestSerializer(BaseAPISerializer):
    """
    Sérialiseur pour les requêtes de recherche.
    """
    query = serializers.CharField(
        max_length=500,
        help_text="Terme de recherche"
    )
    
    search_type = serializers.ChoiceField(
        choices=[
            ('global', 'Recherche globale'),
            ('devices', 'Équipements uniquement'),
            ('alerts', 'Alertes uniquement'),
            ('topologies', 'Topologies uniquement'),
            ('configurations', 'Configurations uniquement'),
            ('users', 'Utilisateurs uniquement'),
            ('logs', 'Logs uniquement')
        ],
        default='global',
        help_text="Type de recherche à effectuer"
    )
    
    resource_types = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Types de ressources à inclure dans la recherche"
    )
    
    filters = serializers.DictField(
        required=False,
        help_text="Filtres supplémentaires pour affiner la recherche"
    )
    
    # Paramètres de recherche
    fuzzy = serializers.BooleanField(
        default=True,
        help_text="Autoriser la recherche approximative"
    )
    
    case_sensitive = serializers.BooleanField(
        default=False,
        help_text="Recherche sensible à la casse"
    )
    
    include_archived = serializers.BooleanField(
        default=False,
        help_text="Inclure les éléments archivés"
    )
    
    # Pagination et tri
    limit = serializers.IntegerField(
        min_value=1,
        max_value=1000,
        default=20,
        help_text="Nombre maximum de résultats"
    )
    
    offset = serializers.IntegerField(
        min_value=0,
        default=0,
        help_text="Décalage pour la pagination"
    )
    
    sort_by = serializers.ChoiceField(
        choices=[
            ('relevance', 'Pertinence'),
            ('name', 'Nom'),
            ('created_at', 'Date de création'),
            ('updated_at', 'Date de modification'),
            ('type', 'Type'),
            ('status', 'Statut')
        ],
        default='relevance',
        help_text="Critère de tri"
    )
    
    sort_order = serializers.ChoiceField(
        choices=[('asc', 'Croissant'), ('desc', 'Décroissant')],
        default='desc',
        help_text="Ordre de tri"
    )
    
    # Champs spécifiques à retourner
    fields = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Liste des champs à inclure dans les résultats"
    )
    
    exclude_fields = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Liste des champs à exclure des résultats"
    )
    
    # Options avancées
    highlight = serializers.BooleanField(
        default=True,
        help_text="Surligner les termes de recherche dans les résultats"
    )
    
    include_suggestions = serializers.BooleanField(
        default=True,
        help_text="Inclure des suggestions de recherche"
    )
    
    include_facets = serializers.BooleanField(
        default=False,
        help_text="Inclure des informations de facettes"
    )
    
    def validate_query(self, value):
        """Valide la requête de recherche."""
        if not value or not value.strip():
            raise DRFValidationError("La requête de recherche ne peut pas être vide")
        
        # Limiter la longueur effective
        cleaned_query = value.strip()
        if len(cleaned_query) < 2:
            raise DRFValidationError("La requête doit contenir au moins 2 caractères")
        
        # Vérifier les caractères spéciaux dangereux
        dangerous_chars = ['<', '>', '"', '\'', '&', ';']
        for char in dangerous_chars:
            if char in cleaned_query:
                raise DRFValidationError(f"Caractère interdit dans la requête: {char}")
        
        return cleaned_query
    
    def validate_resource_types(self, value):
        """Valide les types de ressources."""
        if not value:
            return value
        
        valid_types = [
            'device', 'alert', 'topology', 'configuration', 
            'user', 'log', 'interface', 'connection'
        ]
        
        for resource_type in value:
            if resource_type not in valid_types:
                raise DRFValidationError(
                    f"Type de ressource invalide: {resource_type}. "
                    f"Types autorisés: {valid_types}"
                )
        
        return value
    
    def validate_filters(self, value):
        """Valide les filtres de recherche."""
        if not value:
            return value
        
        # Validation des filtres de date
        date_filters = ['created_after', 'created_before', 'updated_after', 'updated_before']
        for date_filter in date_filters:
            if date_filter in value:
                try:
                    from datetime import datetime
                    datetime.fromisoformat(value[date_filter].replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    raise DRFValidationError(f"Format de date invalide pour {date_filter}")
        
        # Validation des filtres numériques
        numeric_filters = ['min_score', 'max_score']
        for numeric_filter in numeric_filters:
            if numeric_filter in value:
                try:
                    float(value[numeric_filter])
                except (ValueError, TypeError):
                    raise DRFValidationError(f"Valeur numérique invalide pour {numeric_filter}")
        
        return value


class SearchResponseSerializer(BaseAPISerializer):
    """
    Sérialiseur pour les réponses de recherche.
    """
    query = serializers.CharField(help_text="Requête de recherche exécutée")
    total = serializers.IntegerField(help_text="Nombre total de résultats")
    page = serializers.IntegerField(help_text="Page actuelle")
    pages = serializers.IntegerField(help_text="Nombre total de pages")
    limit = serializers.IntegerField(help_text="Limite par page")
    
    results = serializers.ListField(
        child=serializers.DictField(),
        help_text="Résultats de la recherche"
    )
    
    # Méta-informations
    search_time = serializers.FloatField(
        help_text="Temps d'exécution de la recherche en secondes"
    )
    
    suggestions = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Suggestions de recherche alternative"
    )
    
    facets = serializers.DictField(
        required=False,
        help_text="Informations de facettes pour filtrage"
    )
    
    # Statistiques par type de ressource
    type_counts = serializers.DictField(
        required=False,
        help_text="Nombre de résultats par type de ressource"
    )
    
    # Liens de navigation
    next_page = serializers.URLField(
        required=False,
        allow_null=True,
        help_text="URL de la page suivante"
    )
    
    previous_page = serializers.URLField(
        required=False,
        allow_null=True,
        help_text="URL de la page précédente"
    )
    
    # Métadonnées de la recherche
    filters_applied = serializers.DictField(
        required=False,
        help_text="Filtres appliqués à cette recherche"
    )
    
    search_id = serializers.UUIDField(
        required=False,
        help_text="Identifiant unique de cette recherche"
    )


class ResourceDetailSerializer(BaseAPISerializer):
    """
    Sérialiseur pour les détails d'une ressource trouvée.
    """
    id = serializers.CharField(help_text="Identifiant unique de la ressource")
    type = serializers.CharField(help_text="Type de ressource")
    title = serializers.CharField(help_text="Titre ou nom de la ressource")
    description = serializers.CharField(
        required=False,
        help_text="Description de la ressource"
    )
    
    # Informations de base
    created_at = serializers.DateTimeField(
        required=False,
        help_text="Date de création"
    )
    updated_at = serializers.DateTimeField(
        required=False,
        help_text="Date de dernière modification"
    )
    
    # Score de pertinence
    score = serializers.FloatField(
        required=False,
        help_text="Score de pertinence (0.0 à 1.0)"
    )
    
    # Contenus mis en évidence
    highlights = serializers.DictField(
        required=False,
        help_text="Extraits de texte avec termes mis en évidence"
    )
    
    # Métadonnées spécifiques au type
    metadata = serializers.DictField(
        required=False,
        help_text="Métadonnées spécifiques au type de ressource"
    )
    
    # Liens et actions
    url = serializers.URLField(
        required=False,
        help_text="URL pour accéder aux détails complets"
    )
    
    actions = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        help_text="Actions disponibles sur cette ressource"
    )
    
    # Informations contextuelles
    parent = serializers.DictField(
        required=False,
        help_text="Ressource parent (si applicable)"
    )
    
    children_count = serializers.IntegerField(
        required=False,
        help_text="Nombre de ressources enfants"
    )
    
    # Tags et catégories
    tags = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Tags associés à la ressource"
    )
    
    category = serializers.CharField(
        required=False,
        help_text="Catégorie de la ressource"
    )


class SearchSuggestionSerializer(BaseAPISerializer):
    """
    Sérialiseur pour les suggestions de recherche.
    """
    suggestion = serializers.CharField(help_text="Suggestion de recherche")
    type = serializers.ChoiceField(
        choices=[
            ('completion', 'Complétion automatique'),
            ('correction', 'Correction orthographique'),
            ('related', 'Terme associé'),
            ('popular', 'Recherche populaire'),
            ('recent', 'Recherche récente')
        ],
        help_text="Type de suggestion"
    )
    
    frequency = serializers.IntegerField(
        required=False,
        help_text="Fréquence d'utilisation de cette suggestion"
    )
    
    score = serializers.FloatField(
        required=False,
        help_text="Score de pertinence de la suggestion"
    )
    
    context = serializers.CharField(
        required=False,
        help_text="Contexte d'utilisation de la suggestion"
    )


class GlobalSearchSerializer(BaseAPISerializer):
    """
    Sérialiseur pour la recherche globale multi-types.
    """
    query = serializers.CharField(max_length=500)
    
    # Options de recherche rapide
    quick_filters = serializers.DictField(
        required=False,
        help_text="Filtres rapides prédéfinis"
    )
    
    # Pondération par type de ressource
    type_weights = serializers.DictField(
        required=False,
        help_text="Pondération de pertinence par type de ressource"
    )
    
    # Options d'affichage
    group_by_type = serializers.BooleanField(
        default=True,
        help_text="Grouper les résultats par type de ressource"
    )
    
    max_per_type = serializers.IntegerField(
        min_value=1,
        max_value=50,
        default=5,
        help_text="Nombre maximum de résultats par type"
    )
    
    # Cache et performance
    use_cache = serializers.BooleanField(
        default=True,
        help_text="Utiliser le cache pour accélérer la recherche"
    )
    
    cache_duration = serializers.IntegerField(
        min_value=0,
        max_value=3600,
        default=300,
        help_text="Durée de mise en cache en secondes"
    )
    
    def validate_type_weights(self, value):
        """Valide les pondérations par type."""
        if not value:
            return value
        
        for resource_type, weight in value.items():
            try:
                weight = float(weight)
                if not (0.0 <= weight <= 10.0):
                    raise ValueError("Poids hors plage")
            except (ValueError, TypeError):
                raise DRFValidationError(
                    f"Poids invalide pour {resource_type}: doit être entre 0.0 et 10.0"
                )
        
        return value


class SearchHistorySerializer(BaseAPISerializer):
    """
    Sérialiseur pour l'historique de recherche.
    """
    id = serializers.UUIDField(read_only=True)
    query = serializers.CharField()
    search_type = serializers.CharField()
    user_id = serializers.IntegerField(required=False)
    
    results_count = serializers.IntegerField(
        help_text="Nombre de résultats obtenus"
    )
    
    search_time = serializers.FloatField(
        help_text="Temps d'exécution en secondes"
    )
    
    filters_used = serializers.DictField(
        required=False,
        help_text="Filtres utilisés pour cette recherche"
    )
    
    clicked_results = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="IDs des résultats sur lesquels l'utilisateur a cliqué"
    )
    
    created_at = serializers.DateTimeField(read_only=True)
    
    # Métrique de qualité de la recherche
    satisfaction_score = serializers.FloatField(
        required=False,
        min_value=0.0,
        max_value=5.0,
        help_text="Score de satisfaction utilisateur (0-5)"
    )


class SearchFilterSerializer(FilterSerializer):
    """
    Sérialiseur pour les filtres spécifiques aux recherches.
    """
    query_contains = serializers.CharField(
        required=False,
        help_text="Filtrer par contenu de la requête"
    )
    
    search_type = serializers.CharField(
        required=False,
        help_text="Filtrer par type de recherche"
    )
    
    user_id = serializers.IntegerField(
        required=False,
        help_text="Filtrer par utilisateur"
    )
    
    min_results = serializers.IntegerField(
        required=False,
        min_value=0,
        help_text="Nombre minimum de résultats"
    )
    
    max_results = serializers.IntegerField(
        required=False,
        min_value=0,
        help_text="Nombre maximum de résultats"
    )
    
    search_time_min = serializers.FloatField(
        required=False,
        min_value=0.0,
        help_text="Temps de recherche minimum en secondes"
    )
    
    search_time_max = serializers.FloatField(
        required=False,
        min_value=0.0,
        help_text="Temps de recherche maximum en secondes"
    )
    
    has_clicks = serializers.BooleanField(
        required=False,
        help_text="Recherches avec ou sans clics sur les résultats"
    )
    
    date_from = serializers.DateTimeField(
        required=False,
        help_text="Recherches à partir de cette date"
    )
    
    date_to = serializers.DateTimeField(
        required=False,
        help_text="Recherches jusqu'à cette date"
    )
    
    class Meta:
        ordering_fields = ['created_at', 'search_time', 'results_count', 'query']


class SearchAnalyticsSerializer(BaseAPISerializer):
    """
    Sérialiseur pour les analyses de recherche.
    """
    period = serializers.ChoiceField(
        choices=[
            ('hour', 'Dernière heure'),
            ('day', 'Dernière journée'),
            ('week', 'Dernière semaine'),
            ('month', 'Dernier mois'),
            ('quarter', 'Dernier trimestre'),
            ('year', 'Dernière année'),
            ('custom', 'Période personnalisée')
        ],
        default='day'
    )
    
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    
    # Métriques générales
    total_searches = serializers.IntegerField(read_only=True)
    unique_queries = serializers.IntegerField(read_only=True)
    unique_users = serializers.IntegerField(read_only=True)
    average_search_time = serializers.FloatField(read_only=True)
    
    # Top requêtes
    top_queries = serializers.ListField(
        child=serializers.DictField(),
        read_only=True,
        help_text="Requêtes les plus fréquentes"
    )
    
    # Répartition par type
    search_types_distribution = serializers.DictField(
        read_only=True,
        help_text="Répartition des recherches par type"
    )
    
    # Métriques de performance
    performance_metrics = serializers.DictField(
        read_only=True,
        help_text="Métriques de performance de recherche"
    )
    
    # Tendances
    search_trends = serializers.DictField(
        read_only=True,
        help_text="Tendances de recherche sur la période"
    )
    
    def validate(self, data):
        """Validation des paramètres d'analyse."""
        data = super().validate(data)
        
        if data.get('period') == 'custom':
            if not data.get('start_date') or not data.get('end_date'):
                raise DRFValidationError(
                    "start_date et end_date requis pour period='custom'"
                )
            
            if data['start_date'] >= data['end_date']:
                raise DRFValidationError(
                    "start_date doit être antérieure à end_date"
                )
        
        return data 