"""
Filtres avancés spécialisés pour chaque type de ressource du système NMS
"""

from typing import List
from django.db.models import Q
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend

from .dynamic_filters import AdvancedFilterSet


class SearchFilterBackend(DjangoFilterBackend):
    """
    Backend de filtrage pour les recherches textuelles avancées
    """
    
    def filter_queryset(self, request, queryset, view):
        """
        Applique les filtres de recherche textuelle
        """
        queryset = super().filter_queryset(request, queryset, view)
        
        # Recherche globale
        search_query = request.query_params.get('q', '')
        if search_query and hasattr(view, 'search_fields'):
            search_filter = self._build_search_filter(search_query, view.search_fields)
            queryset = queryset.filter(search_filter)
        
        return queryset
    
    def _build_search_filter(self, search_query: str, search_fields: List[str]) -> Q:
        """
        Construit un filtre de recherche Q pour plusieurs champs
        """
        terms = search_query.split()
        query = Q()
        
        for term in terms:
            term_query = Q()
            for field in search_fields:
                term_query |= Q(**{f"{field}__icontains": term})
            query &= term_query
        
        return query


class NetworkDeviceFilterSet(AdvancedFilterSet):
    """
    Filtres avancés pour les équipements réseau
    """
    
    # Filtres spécifiques aux équipements
    device_type = filters.ChoiceFilter(
        choices=[
            ('router', 'Routeur'),
            ('switch', 'Commutateur'),
            ('firewall', 'Pare-feu'),
            ('access_point', 'Point d\'accès'),
            ('server', 'Serveur'),
            ('other', 'Autre')
        ],
        help_text="Type d'équipement"
    )
    
    status = filters.ChoiceFilter(
        choices=[
            ('online', 'En ligne'),
            ('offline', 'Hors ligne'),
            ('maintenance', 'Maintenance'),
            ('error', 'Erreur'),
            ('unknown', 'Inconnu')
        ],
        help_text="Statut de l'équipement"
    )
    
    vendor = filters.CharFilter(
        lookup_expr='icontains',
        help_text="Fabricant de l'équipement"
    )
    
    model = filters.CharFilter(
        lookup_expr='icontains', 
        help_text="Modèle de l'équipement"
    )
    
    ip_address = filters.CharFilter(
        lookup_expr='icontains',
        help_text="Adresse IP"
    )
    
    subnet = filters.CharFilter(
        method='filter_subnet',
        help_text="Sous-réseau (ex: 192.168.1.0/24)"
    )
    
    location = filters.CharFilter(
        lookup_expr='icontains',
        help_text="Localisation physique"
    )
    
    # Filtres de performance
    cpu_usage_max = filters.NumberFilter(
        field_name='current_cpu_usage',
        lookup_expr='lte',
        help_text="Usage CPU maximum (%)"
    )
    
    memory_usage_max = filters.NumberFilter(
        field_name='current_memory_usage',
        lookup_expr='lte',
        help_text="Usage mémoire maximum (%)"
    )
    
    # Filtres de connectivité
    has_alerts = filters.BooleanFilter(
        method='filter_has_alerts',
        help_text="Équipements avec alertes actives"
    )
    
    last_seen_after = filters.DateTimeFilter(
        field_name='last_seen',
        lookup_expr='gte',
        help_text="Dernière vue après cette date"
    )
    
    class Meta:
        fields = ['device_type', 'status', 'vendor', 'model', 'location']
    
    @property
    def search_fields(self):
        return ['name', 'description', 'ip_address', 'mac_address', 'vendor', 'model', 'location']
    
    def filter_search(self, queryset, name, value):
        """
        Recherche textuelle dans les champs de l'équipement
        """
        return queryset.filter(self.get_search_query(value, self.search_fields))
    
    def filter_subnet(self, queryset, name, value):
        """
        Filtre par sous-réseau
        """
        try:
            # Extraction du réseau et du masque
            if '/' in value:
                network, prefix = value.split('/', 1)
                prefix_len = int(prefix)
                
                # Construction du filtre pour les IPs dans le sous-réseau
                # Simplification : on filtre par le début de l'IP
                network_parts = network.split('.')
                if prefix_len >= 24:
                    # /24 ou plus : filtrer par les 3 premiers octets
                    network_prefix = '.'.join(network_parts[:3])
                    return queryset.filter(ip_address__startswith=network_prefix)
                elif prefix_len >= 16:
                    # /16 : filtrer par les 2 premiers octets
                    network_prefix = '.'.join(network_parts[:2])
                    return queryset.filter(ip_address__startswith=network_prefix)
                elif prefix_len >= 8:
                    # /8 : filtrer par le premier octet
                    network_prefix = network_parts[0]
                    return queryset.filter(ip_address__startswith=network_prefix)
            
            return queryset.filter(ip_address__icontains=value)
            
        except (ValueError, IndexError):
            return queryset
    
    def filter_has_alerts(self, queryset, name, value):
        """
        Filtre les équipements avec ou sans alertes actives
        """
        if value:
            return queryset.filter(alerts__status='active').distinct()
        else:
            return queryset.exclude(alerts__status='active').distinct()


class TopologyFilterSet(AdvancedFilterSet):
    """
    Filtres avancés pour les topologies réseau
    """
    
    topology_type = filters.ChoiceFilter(
        choices=[
            ('physical', 'Physique'),
            ('logical', 'Logique'),
            ('vlan', 'VLAN'),
            ('routing', 'Routage'),
            ('security', 'Sécurité')
        ],
        help_text="Type de topologie"
    )
    
    discovery_status = filters.ChoiceFilter(
        choices=[
            ('pending', 'En attente'),
            ('running', 'En cours'),
            ('completed', 'Terminé'),
            ('failed', 'Échoué'),
            ('cancelled', 'Annulé')
        ],
        help_text="Statut de la découverte"
    )
    
    node_count_min = filters.NumberFilter(
        field_name='node_count',
        lookup_expr='gte',
        help_text="Nombre minimum de nœuds"
    )
    
    node_count_max = filters.NumberFilter(
        field_name='node_count',
        lookup_expr='lte',
        help_text="Nombre maximum de nœuds"
    )
    
    has_connections = filters.BooleanFilter(
        method='filter_has_connections',
        help_text="Topologies avec connexions détectées"
    )
    
    class Meta:
        fields = ['topology_type', 'discovery_status']
    
    @property
    def search_fields(self):
        return ['name', 'description', 'discovery_method']
    
    def filter_search(self, queryset, name, value):
        return queryset.filter(self.get_search_query(value, self.search_fields))
    
    def filter_has_connections(self, queryset, name, value):
        """
        Filtre les topologies avec ou sans connexions
        """
        if value:
            return queryset.filter(connections__isnull=False).distinct()
        else:
            return queryset.filter(connections__isnull=True).distinct()


class SecurityAlertFilterSet(AdvancedFilterSet):
    """
    Filtres avancés pour les alertes de sécurité
    """
    
    severity = filters.ChoiceFilter(
        choices=[
            ('low', 'Faible'),
            ('medium', 'Moyenne'),
            ('high', 'Élevée'),
            ('critical', 'Critique')
        ],
        help_text="Niveau de sévérité"
    )
    
    alert_type = filters.ChoiceFilter(
        choices=[
            ('intrusion', 'Intrusion'),
            ('malware', 'Malware'),
            ('anomaly', 'Anomalie'),
            ('vulnerability', 'Vulnérabilité'),
            ('policy_violation', 'Violation de politique'),
            ('authentication', 'Authentification'),
            ('network', 'Réseau'),
            ('other', 'Autre')
        ],
        help_text="Type d'alerte"
    )
    
    status = filters.ChoiceFilter(
        choices=[
            ('new', 'Nouvelle'),
            ('acknowledged', 'Acquittée'),
            ('investigating', 'En cours d\'investigation'),
            ('resolved', 'Résolue'),
            ('false_positive', 'Faux positif'),
            ('ignored', 'Ignorée')
        ],
        help_text="Statut de l'alerte"
    )
    
    source_ip = filters.CharFilter(
        lookup_expr='icontains',
        help_text="Adresse IP source"
    )
    
    target_ip = filters.CharFilter(
        lookup_expr='icontains',
        help_text="Adresse IP cible"
    )
    
    is_acknowledged = filters.BooleanFilter(
        help_text="Alerte acquittée"
    )
    
    assigned_to = filters.CharFilter(
        field_name='assigned_to__username',
        lookup_expr='icontains',
        help_text="Assignée à l'utilisateur"
    )
    
    # Filtres temporels spécifiques
    detected_after = filters.DateTimeFilter(
        field_name='detected_at',
        lookup_expr='gte',
        help_text="Détectée après cette date"
    )
    
    detected_before = filters.DateTimeFilter(
        field_name='detected_at',
        lookup_expr='lte',
        help_text="Détectée avant cette date"
    )
    
    class Meta:
        fields = ['severity', 'alert_type', 'status', 'is_acknowledged']
    
    @property
    def search_fields(self):
        return ['title', 'description', 'source_ip', 'target_ip', 'rule_name']
    
    def filter_search(self, queryset, name, value):
        return queryset.filter(self.get_search_query(value, self.search_fields))


class DashboardFilterSet(AdvancedFilterSet):
    """
    Filtres avancés pour les tableaux de bord
    """
    
    dashboard_type = filters.ChoiceFilter(
        choices=[
            ('network', 'Réseau'),
            ('security', 'Sécurité'),
            ('performance', 'Performance'),
            ('traffic', 'Trafic'),
            ('custom', 'Personnalisé')
        ],
        help_text="Type de tableau de bord"
    )
    
    is_default = filters.BooleanFilter(
        help_text="Tableau de bord par défaut"
    )
    
    is_shared = filters.BooleanFilter(
        help_text="Tableau de bord partagé"
    )
    
    owner = filters.CharFilter(
        field_name='owner__username',
        lookup_expr='icontains',
        help_text="Propriétaire du tableau de bord"
    )
    
    widget_count_min = filters.NumberFilter(
        field_name='widgets__count',
        lookup_expr='gte',
        help_text="Nombre minimum de widgets"
    )
    
    class Meta:
        fields = ['dashboard_type', 'is_default', 'is_shared']
    
    @property
    def search_fields(self):
        return ['name', 'description', 'tags']
    
    def filter_search(self, queryset, name, value):
        return queryset.filter(self.get_search_query(value, self.search_fields))


class DateRangeFilterSet(AdvancedFilterSet):
    """
    FilterSet spécialisé pour les filtres de plages de dates
    """
    
    # Plages prédéfinies
    date_range = filters.ChoiceFilter(
        method='filter_date_range',
        choices=[
            ('today', 'Aujourd\'hui'),
            ('yesterday', 'Hier'),
            ('last_7_days', '7 derniers jours'),
            ('last_30_days', '30 derniers jours'),
            ('last_90_days', '90 derniers jours'),
            ('this_week', 'Cette semaine'),
            ('last_week', 'Semaine dernière'),
            ('this_month', 'Ce mois'),
            ('last_month', 'Mois dernier'),
            ('this_year', 'Cette année'),
            ('last_year', 'Année dernière')
        ],
        help_text="Plage de dates prédéfinie"
    )
    
    # Filtres de dates personnalisées
    date_from = filters.DateFilter(
        method='filter_date_from',
        help_text="Date de début (YYYY-MM-DD)"
    )
    
    date_to = filters.DateFilter(
        method='filter_date_to',
        help_text="Date de fin (YYYY-MM-DD)"
    )
    
    class Meta:
        abstract = True
    
    def filter_date_range(self, queryset, name, value):
        """
        Filtre par plage de dates prédéfinie
        """
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        now = timezone.now()
        today = now.date()
        
        date_ranges = {
            'today': (today, today + timedelta(days=1)),
            'yesterday': (today - timedelta(days=1), today),
            'last_7_days': (today - timedelta(days=7), today),
            'last_30_days': (today - timedelta(days=30), today),
            'last_90_days': (today - timedelta(days=90), today),
            'this_week': (today - timedelta(days=today.weekday()), today + timedelta(days=1)),
            'last_week': (
                today - timedelta(days=today.weekday() + 7),
                today - timedelta(days=today.weekday())
            ),
            'this_month': (today.replace(day=1), today + timedelta(days=1)),
            'last_month': (
                (today.replace(day=1) - timedelta(days=1)).replace(day=1),
                today.replace(day=1)
            ),
            'this_year': (today.replace(month=1, day=1), today + timedelta(days=1)),
            'last_year': (
                today.replace(year=today.year-1, month=1, day=1),
                today.replace(month=1, day=1)
            )
        }
        
        if value in date_ranges:
            start_date, end_date = date_ranges[value]
            return self._apply_date_filter(queryset, start_date, end_date)
        
        return queryset
    
    def filter_date_from(self, queryset, name, value):
        """
        Filtre à partir d'une date
        """
        return self._apply_date_filter(queryset, value, None)
    
    def filter_date_to(self, queryset, name, value):
        """
        Filtre jusqu'à une date
        """
        return self._apply_date_filter(queryset, None, value)
    
    def _apply_date_filter(self, queryset, start_date, end_date):
        """
        Applique un filtre de date au queryset
        À redéfinir dans les classes filles pour spécifier le champ de date
        """
        date_field = getattr(self.Meta, 'date_field', 'created_at')
        
        if start_date:
            queryset = queryset.filter(**{f"{date_field}__gte": start_date})
        if end_date:
            queryset = queryset.filter(**{f"{date_field}__lt": end_date})
        
        return queryset 