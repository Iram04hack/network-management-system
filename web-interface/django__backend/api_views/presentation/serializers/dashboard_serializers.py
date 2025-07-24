"""
Sérialiseurs pour les données de tableaux de bord.

Ce module contient les sérialiseurs spécialisés pour la validation et transformation
des données des tableaux de bord du système de gestion de réseau.
"""

from typing import Dict, Any, List, Optional
from rest_framework import serializers
from rest_framework.exceptions import ValidationError as DRFValidationError

from .base_serializers import BaseAPISerializer, FilterSerializer


class DashboardRequestSerializer(BaseAPISerializer):
    """
    Sérialiseur pour les requêtes de données de tableau de bord.
    """
    dashboard_type = serializers.ChoiceField(
        choices=[
            ('system-overview', 'Vue d\'ensemble du système'),
            ('network-status', 'Statut réseau'),
            ('security-dashboard', 'Tableau de bord sécurité'),
            ('monitoring-dashboard', 'Tableau de bord monitoring'),
            ('user-dashboard', 'Tableau de bord utilisateur'),
            ('custom', 'Tableau de bord personnalisé')
        ],
        help_text="Type de tableau de bord demandé"
    )
    
    time_range = serializers.ChoiceField(
        choices=[
            ('1h', 'Dernière heure'),
            ('24h', 'Dernières 24 heures'),
            ('7d', 'Derniers 7 jours'),
            ('30d', 'Derniers 30 jours'),
            ('90d', 'Derniers 90 jours'),
            ('custom', 'Période personnalisée')
        ],
        default='24h',
        required=False,
        help_text="Période de temps pour les données"
    )
    
    start_date = serializers.DateTimeField(
        required=False,
        help_text="Date de début pour les périodes personnalisées"
    )
    
    end_date = serializers.DateTimeField(
        required=False,
        help_text="Date de fin pour les périodes personnalisées"
    )
    
    filters = serializers.DictField(
        required=False,
        help_text="Filtres supplémentaires pour les données"
    )
    
    refresh_data = serializers.BooleanField(
        default=False,
        required=False,
        help_text="Force la mise à jour des données depuis la source"
    )

    refresh_interval = serializers.IntegerField(
        required=False,
        min_value=30,
        max_value=3600,
        default=300,
        help_text="Intervalle de rafraîchissement en secondes (30-3600)"
    )
    
    def validate(self, data):
        """Validation cross-field pour les requêtes de dashboard."""
        data = super().validate(data)
        
        # Validation des dates pour les périodes personnalisées
        if data.get('time_range') == 'custom':
            if not data.get('start_date') or not data.get('end_date'):
                raise DRFValidationError(
                    "start_date et end_date sont requis pour time_range='custom'"
                )
            
            if data['start_date'] >= data['end_date']:
                raise DRFValidationError(
                    "start_date doit être antérieure à end_date"
                )
        
        # Validation spécifique selon le type de dashboard
        dashboard_type = data.get('dashboard_type')
        if dashboard_type == 'user-dashboard':
            # Vérifier que l'utilisateur est authentifié
            if hasattr(self, 'context') and 'request' in self.context:
                if not self.context['request'].user.is_authenticated:
                    raise DRFValidationError(
                        "Authentification requise pour user-dashboard"
                    )
        
        return data
    
    class Meta:
        staff_only_fields = ['refresh_data']


class DashboardWidgetSerializer(BaseAPISerializer):
    """
    Sérialiseur pour les widgets de tableau de bord.
    """
    id = serializers.CharField(help_text="Identifiant unique du widget")
    type = serializers.ChoiceField(
        choices=[
            ('alerts', 'Liste d\'alertes'),
            ('devices', 'État des équipements'),
            ('metrics', 'Métriques système'),
            ('charts', 'Graphiques'),
            ('topology', 'Carte de topologie'),
            ('security', 'Informations de sécurité'),
            ('custom', 'Widget personnalisé')
        ],
        help_text="Type de widget"
    )
    
    title = serializers.CharField(
        max_length=100,
        help_text="Titre affiché du widget"
    )
    
    position = serializers.DictField(
        required=False,
        help_text="Position du widget dans la grille"
    )
    
    size = serializers.DictField(
        required=False,
        help_text="Taille du widget (width, height)"
    )
    
    configuration = serializers.DictField(
        required=False,
        help_text="Configuration spécifique du widget"
    )
    
    refresh_interval = serializers.IntegerField(
        min_value=30,
        max_value=3600,
        default=300,
        required=False,
        help_text="Intervalle de rafraîchissement en secondes"
    )
    
    visible = serializers.BooleanField(
        default=True,
        required=False,
        help_text="Visibilité du widget"
    )
    
    def validate_position(self, value):
        """Valide la position du widget."""
        if not value:
            return value
        
        required_fields = ['x', 'y']
        for field in required_fields:
            if field not in value:
                raise DRFValidationError(f"Position doit contenir '{field}'")
            
            if not isinstance(value[field], int) or value[field] < 0:
                raise DRFValidationError(f"Position.{field} doit être un entier positif")
        
        return value
    
    def validate_size(self, value):
        """Valide la taille du widget."""
        if not value:
            return value
        
        required_fields = ['width', 'height']
        for field in required_fields:
            if field not in value:
                raise DRFValidationError(f"Size doit contenir '{field}'")
            
            if not isinstance(value[field], int) or value[field] <= 0:
                raise DRFValidationError(f"Size.{field} doit être un entier positif")
        
        # Limites de taille
        if value['width'] > 12:
            raise DRFValidationError("Largeur maximum: 12 colonnes")
        if value['height'] > 8:
            raise DRFValidationError("Hauteur maximum: 8 lignes")
        
        return value
    
    def validate_configuration(self, value):
        """Valide la configuration spécifique selon le type de widget."""
        if not value:
            return value

        # Récupérer le type depuis les données validées ou initiales
        widget_type = None
        if hasattr(self, 'initial_data') and self.initial_data:
            widget_type = self.initial_data.get('type')
        elif hasattr(self, '_validated_data') and self._validated_data:
            widget_type = self._validated_data.get('type')

        if not widget_type:
            return value
        
        if widget_type == 'alerts':
            # Validation pour les widgets d'alertes
            if 'severities' in value:
                valid_severities = ['critical', 'warning', 'info']
                for severity in value['severities']:
                    if severity not in valid_severities:
                        raise DRFValidationError(
                            f"Severity invalide: {severity}. "
                            f"Valeurs autorisées: {valid_severities}"
                        )
        
        elif widget_type == 'devices':
            # Validation pour les widgets d'équipements
            if 'device_types' in value:
                valid_types = ['router', 'switch', 'firewall', 'server', 'other']
                for device_type in value['device_types']:
                    if device_type not in valid_types:
                        raise DRFValidationError(
                            f"Device type invalide: {device_type}. "
                            f"Valeurs autorisées: {valid_types}"
                        )
        
        elif widget_type == 'metrics':
            # Validation pour les widgets de métriques
            if 'metrics' in value:
                valid_metrics = ['cpu', 'memory', 'disk', 'network', 'bandwidth']
                for metric in value['metrics']:
                    if metric not in valid_metrics:
                        raise DRFValidationError(
                            f"Metric invalide: {metric}. "
                            f"Valeurs autorisées: {valid_metrics}"
                        )
        
        return value


class CustomDashboardSerializer(BaseAPISerializer):
    """
    Sérialiseur pour les tableaux de bord personnalisés.
    """
    name = serializers.CharField(
        max_length=100,
        help_text="Nom du tableau de bord"
    )
    
    description = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="Description du tableau de bord"
    )
    
    layout = serializers.ChoiceField(
        choices=[
            ('grid', 'Disposition en grille'),
            ('flow', 'Disposition libre'),
            ('fixed', 'Positions fixes')
        ],
        default='grid',
        help_text="Type de disposition"
    )
    
    widgets = DashboardWidgetSerializer(
        many=True,
        help_text="Liste des widgets du tableau de bord"
    )
    
    shared = serializers.BooleanField(
        default=False,
        required=False,
        help_text="Tableau de bord partagé avec d'autres utilisateurs"
    )
    
    auto_refresh = serializers.BooleanField(
        default=True,
        required=False,
        help_text="Rafraîchissement automatique activé"
    )
    
    refresh_interval = serializers.IntegerField(
        min_value=30,
        max_value=3600,
        default=300,
        required=False,
        help_text="Intervalle de rafraîchissement global en secondes"
    )
    
    def validate_widgets(self, value):
        """Valide la liste des widgets."""
        if not value:
            raise DRFValidationError("Au moins un widget est requis")
        
        if len(value) > 20:
            raise DRFValidationError("Maximum 20 widgets par tableau de bord")
        
        # Vérifier l'unicité des IDs de widgets
        widget_ids = [widget['id'] for widget in value]
        if len(widget_ids) != len(set(widget_ids)):
            raise DRFValidationError("Les IDs de widgets doivent être uniques")
        
        # Validation des positions pour layout fixed
        if self.initial_data.get('layout') == 'fixed':
            for widget in value:
                if not widget.get('position'):
                    raise DRFValidationError(
                        "Position requise pour tous les widgets en layout 'fixed'"
                    )
        
        return value
    
    def _validate_business_rules(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validation des règles métier pour les dashboards."""
        data = super()._validate_business_rules(data)
        
        # Les tableaux de bord partagés nécessitent des privilèges
        if data.get('shared', False):
            if hasattr(self, 'context') and 'request' in self.context:
                user = self.context['request'].user
                if not user.is_staff:
                    raise DRFValidationError(
                        "Seuls les administrateurs peuvent créer des tableaux de bord partagés"
                    )
        
        return data
    
    class Meta:
        staff_only_fields = ['shared']


class DashboardConfigurationSerializer(BaseAPISerializer):
    """
    Sérialiseur pour la configuration d'un tableau de bord.
    """
    dashboard_type = serializers.CharField(help_text="Type de tableau de bord")
    configuration = serializers.DictField(help_text="Configuration complète")
    user_id = serializers.IntegerField(
        required=False,
        help_text="ID utilisateur pour les configurations personnelles"
    )
    
    def validate_configuration(self, value):
        """Valide la structure de la configuration."""
        if not isinstance(value, dict):
            raise DRFValidationError("Configuration doit être un objet JSON")
        
        # Validation de base de la structure
        if 'widgets' in value:
            if not isinstance(value['widgets'], list):
                raise DRFValidationError("Configuration.widgets doit être une liste")
        
        return value


class DashboardDataSerializer(BaseAPISerializer):
    """
    Sérialiseur pour les données de réponse d'un tableau de bord.
    """
    dashboard_type = serializers.CharField(help_text="Type de tableau de bord")
    data = serializers.DictField(help_text="Données du tableau de bord")
    metadata = serializers.DictField(
        required=False,
        help_text="Métadonnées sur les données"
    )
    last_updated = serializers.DateTimeField(help_text="Dernière mise à jour des données")
    refresh_interval = serializers.IntegerField(
        required=False,
        help_text="Intervalle de rafraîchissement recommandé"
    )
    
    class Meta:
        include_metadata = True


class DashboardFilterSerializer(FilterSerializer):
    """
    Sérialiseur pour les filtres spécifiques aux tableaux de bord.
    """
    dashboard_type = serializers.CharField(
        required=False,
        help_text="Filtrer par type de tableau de bord"
    )
    
    shared_only = serializers.BooleanField(
        default=False,
        required=False,
        help_text="Afficher uniquement les tableaux de bord partagés"
    )
    
    user_id = serializers.IntegerField(
        required=False,
        help_text="Filtrer par utilisateur créateur"
    )
    
    class Meta:
        ordering_fields = ['name', 'created_at', 'updated_at', 'dashboard_type'] 