"""
Filtres dynamiques pour l'API Views
Permet la construction de filtres à la volée basés sur les paramètres de requête
"""

import operator
from functools import reduce
from typing import Dict, List, Any, Optional

from django.db import models
from django.db.models import Q
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.request import Request
from rest_framework import serializers


class DynamicFilterBackend(DjangoFilterBackend):
    """
    Backend de filtrage dynamique qui construit des filtres à partir des paramètres de requête
    Supporte les opérations complexes et les filtres imbriqués
    """
    
    # Opérateurs supportés pour les filtres dynamiques
    SUPPORTED_OPERATORS = {
        'eq': 'exact',           # Égal
        'ne': 'exact',           # Pas égal (inversé)
        'lt': 'lt',              # Inférieur
        'le': 'lte',             # Inférieur ou égal
        'gt': 'gt',              # Supérieur
        'ge': 'gte',             # Supérieur ou égal
        'in': 'in',              # Dans la liste
        'nin': 'in',             # Pas dans la liste (inversé)
        'contains': 'icontains', # Contient (insensible à la casse)
        'startswith': 'istartswith', # Commence par
        'endswith': 'iendswith', # Finit par
        'regex': 'regex',        # Expression régulière
        'isnull': 'isnull',      # Est null
        'isnotnull': 'isnull',   # N'est pas null (inversé)
        'range': 'range',        # Dans l'intervalle
        'date': 'date',          # Date exacte
        'year': 'year',          # Année
        'month': 'month',        # Mois
        'day': 'day',            # Jour
    }
    
    # Opérateurs qui inversent la condition
    INVERSE_OPERATORS = {'ne', 'nin', 'isnotnull'}
    
    def filter_queryset(self, request: Request, queryset: models.QuerySet, view) -> models.QuerySet:
        """
        Applique les filtres dynamiques au queryset
        """
        # D'abord, appliquer les filtres standard
        queryset = super().filter_queryset(request, queryset, view)
        
        # Puis appliquer les filtres dynamiques
        dynamic_filters = self._parse_dynamic_filters(request.query_params)
        if dynamic_filters:
            queryset = self._apply_dynamic_filters(queryset, dynamic_filters)
        
        return queryset
    
    def _parse_dynamic_filters(self, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse les paramètres de requête pour extraire les filtres dynamiques
        Format attendu: filter[field][operator]=value
        """
        filters = []
        
        for key, value in query_params.items():
            if key.startswith('filter[') and key.endswith(']'):
                # Extraire le champ et l'opérateur
                # Ex: filter[device_name][contains] -> device_name, contains
                filter_part = key[7:-1]  # Enlever 'filter[' et ']'
                
                if '][' in filter_part:
                    field, operator = filter_part.split('][', 1)
                else:
                    field, operator = filter_part, 'eq'
                
                if operator in self.SUPPORTED_OPERATORS:
                    filters.append({
                        'field': field,
                        'operator': operator,
                        'value': value,
                        'inverse': operator in self.INVERSE_OPERATORS
                    })
        
        return filters
    
    def _apply_dynamic_filters(self, queryset: models.QuerySet, filters: List[Dict[str, Any]]) -> models.QuerySet:
        """
        Applique une liste de filtres dynamiques au queryset
        """
        q_objects = []
        
        for filter_config in filters:
            q_obj = self._build_q_object(filter_config)
            if q_obj:
                q_objects.append(q_obj)
        
        if q_objects:
            # Combiner tous les filtres avec AND
            combined_filter = reduce(operator.and_, q_objects)
            queryset = queryset.filter(combined_filter)
        
        return queryset
    
    def _build_q_object(self, filter_config: Dict[str, Any]) -> Optional[Q]:
        """
        Construit un objet Q à partir d'une configuration de filtre
        """
        field = filter_config['field']
        operator = filter_config['operator']
        value = filter_config['value']
        inverse = filter_config['inverse']
        
        try:
            # Construire le lookup
            django_operator = self.SUPPORTED_OPERATORS[operator]
            lookup = f"{field}__{django_operator}"
            
            # Traitement spécial pour certains opérateurs
            if operator == 'range':
                # Format: "min,max"
                try:
                    min_val, max_val = value.split(',', 1)
                    value = [min_val.strip(), max_val.strip()]
                except ValueError:
                    return None
            elif operator in ('in', 'nin'):
                # Format: "val1,val2,val3"
                value = [v.strip() for v in value.split(',')]
            elif operator in ('isnull', 'isnotnull'):
                # Valeur booléenne
                value = value.lower() in ('true', '1', 'yes', 'on')
            
            # Créer l'objet Q
            q_obj = Q(**{lookup: value})
            
            # Inverser si nécessaire
            if inverse:
                q_obj = ~q_obj
                
            return q_obj
            
        except (ValueError, TypeError, AttributeError):
            # Ignorer les filtres malformés
            return None


class AdvancedFilterSet(filters.FilterSet):
    """
    FilterSet avancé avec support pour les filtres complexes et les recherches full-text
    """
    
    # Champ de recherche générique
    search = filters.CharFilter(method='filter_search', help_text="Recherche textuelle générale")
    
    # Filtres de date
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    updated_after = filters.DateTimeFilter(field_name='updated_at', lookup_expr='gte')
    updated_before = filters.DateTimeFilter(field_name='updated_at', lookup_expr='lte')
    
    # Filtre de tri avancé - temporairement commenté pour éviter les problèmes de traduction
    # ordering = filters.OrderingFilter(
    #     fields=(
    #         ('created_at', 'created'),
    #         ('updated_at', 'updated'),
    #         ('name', 'name'),
    #         ('status', 'status'),
    #     )
    # )
    
    class Meta:
        abstract = True
    
    def filter_search(self, queryset, name, value):
        """
        Méthode de recherche générique - doit être redéfinie dans les classes filles
        """
        return queryset
    
    @property
    def search_fields(self):
        """
        Champs sur lesquels effectuer la recherche textuelle
        À redéfinir dans les classes filles
        """
        return []
    
    def get_search_query(self, search_terms: str, search_fields: List[str]) -> Q:
        """
        Construit une requête de recherche Q pour plusieurs champs
        """
        if not search_terms or not search_fields:
            return Q()
        
        terms = search_terms.split()
        query = Q()
        
        for term in terms:
            term_query = Q()
            for field in search_fields:
                term_query |= Q(**{f"{field}__icontains": term})
            query &= term_query
        
        return query


class FilterValidationMixin:
    """
    Mixin pour valider les paramètres de filtrage
    """
    
    def validate_filter_params(self, query_params: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Valide les paramètres de filtrage et retourne les erreurs
        """
        errors = {}
        
        # Valider les filtres dynamiques
        for key, value in query_params.items():
            if key.startswith('filter['):
                validation_errors = self._validate_dynamic_filter(key, value)
                if validation_errors:
                    errors[key] = validation_errors
        
        # Valider les paramètres de pagination
        pagination_errors = self._validate_pagination_params(query_params)
        if pagination_errors:
            errors.update(pagination_errors)
        
        return errors
    
    def _validate_dynamic_filter(self, key: str, value: str) -> List[str]:
        """
        Valide un filtre dynamique individuel
        """
        errors = []
        
        try:
            # Extraire le champ et l'opérateur
            filter_part = key[7:-1]  # Enlever 'filter[' et ']'
            
            if '][' in filter_part:
                field, operator = filter_part.split('][', 1)
            else:
                field, operator = filter_part, 'eq'
            
            # Vérifier que l'opérateur est supporté
            if operator not in DynamicFilterBackend.SUPPORTED_OPERATORS:
                errors.append(f"Opérateur '{operator}' non supporté")
            
            # Validation spécifique par type d'opérateur
            if operator == 'range' and ',' not in value:
                errors.append("Le filtre 'range' nécessite deux valeurs séparées par une virgule")
            
            elif operator in ('in', 'nin') and not value:
                errors.append(f"Le filtre '{operator}' nécessite au moins une valeur")
            
        except Exception:
            errors.append("Format de filtre invalide")
        
        return errors
    
    def _validate_pagination_params(self, query_params: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Valide les paramètres de pagination
        """
        errors = {}
        
        # Valider 'page'
        if 'page' in query_params:
            try:
                page = int(query_params['page'])
                if page < 1:
                    errors['page'] = ["Le numéro de page doit être supérieur à 0"]
            except ValueError:
                errors['page'] = ["Le numéro de page doit être un entier"]
        
        # Valider 'page_size'
        if 'page_size' in query_params:
            try:
                page_size = int(query_params['page_size'])
                if page_size < 1:
                    errors['page_size'] = ["La taille de page doit être supérieure à 0"]
                elif page_size > 1000:
                    errors['page_size'] = ["La taille de page ne peut pas dépasser 1000"]
            except ValueError:
                errors['page_size'] = ["La taille de page doit être un entier"]
        
        return errors


class FilterResponseSerializer(serializers.Serializer):
    """
    Serializer pour les réponses incluant des informations de filtrage
    """
    filters_applied = serializers.DictField(
        help_text="Filtres appliqués à la requête",
        read_only=True
    )
    total_before_filters = serializers.IntegerField(
        help_text="Nombre total d'éléments avant application des filtres",
        read_only=True
    )
    filter_summary = serializers.DictField(
        help_text="Résumé des filtres disponibles",
        read_only=True
    ) 