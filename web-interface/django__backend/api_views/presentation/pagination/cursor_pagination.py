"""
Pagination cursor pour les très grands datasets
Implémentation haute performance sans les problèmes de LIMIT/OFFSET
"""

import base64
import json
from typing import Any, Dict, Optional, Tuple
from collections import OrderedDict
from datetime import datetime

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework.pagination import BasePagination
from rest_framework.response import Response
from rest_framework.utils.urls import replace_query_param, remove_query_param


class CursorPagination(BasePagination):
    """
    Pagination cursor générique pour les très grands datasets
    Évite les problèmes de performance des LIMIT/OFFSET sur de gros volumes
    """
    
    page_size = 50
    page_size_query_param = 'page_size'
    cursor_query_param = 'cursor'
    max_page_size = 1000
    ordering = '-id'  # Champ d'ordre par défaut
    
    # Configuration du curseur
    cursor_query_description = 'Curseur de pagination'
    page_size_query_description = 'Nombre d\'éléments par page'
    
    # Configuration des liens
    include_cursor_links = True
    include_metadata = True
    
    def __init__(self):
        self.page_size = self.get_page_size()
        
    def get_page_size(self, request=None):
        """
        Détermine la taille de page
        """
        if request and self.page_size_query_param in request.query_params:
            try:
                page_size = int(request.query_params[self.page_size_query_param])
                return min(max(1, page_size), self.max_page_size)
            except (ValueError, TypeError):
                pass
        return self.page_size
    
    def paginate_queryset(self, queryset, request, view=None):
        """
        Pagine le queryset en utilisant la pagination cursor
        """
        self.page_size = self.get_page_size(request)
        self.request = request
        self.view = view
        
        # Appliquer l'ordre
        if not queryset.query.order_by:
            queryset = queryset.order_by(self.ordering)
        
        # Décoder le curseur
        cursor_position = self._decode_cursor(request)
        
        # Appliquer le filtrage basé sur le curseur
        if cursor_position:
            queryset = self._apply_cursor_filter(queryset, cursor_position)
        
        # Obtenir page_size + 1 pour détecter s'il y a une page suivante
        results = list(queryset[:self.page_size + 1])
        
        # Déterminer s'il y a une page suivante
        self.has_next = len(results) > self.page_size
        if self.has_next:
            results = results[:-1]
        
        # Stocker les résultats pour générer les liens
        self.results = results
        
        return results
    
    def get_paginated_response(self, data):
        """
        Retourne une réponse paginée avec curseur
        """
        response_data = OrderedDict([
            ('results', data)
        ])
        
        if self.include_cursor_links:
            response_data['links'] = {
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            }
        
        if self.include_metadata:
            response_data['pagination'] = {
                'page_size': self.page_size,
                'has_next': self.has_next,
                'has_previous': self._has_previous(),
                'cursor_info': {
                    'current': self._get_current_cursor(),
                    'ordering': self.ordering
                }
            }
        
        return Response(response_data)
    
    def get_next_link(self):
        """
        Génère le lien vers la page suivante
        """
        if not self.has_next:
            return None
        
        cursor = self._encode_cursor(self._get_next_cursor_position())
        return self._get_cursor_link(cursor)
    
    def get_previous_link(self):
        """
        Génère le lien vers la page précédente
        """
        if not self._has_previous():
            return None
        
        cursor = self._encode_cursor(self._get_previous_cursor_position())
        return self._get_cursor_link(cursor)
    
    def _decode_cursor(self, request):
        """
        Décode le curseur depuis les paramètres de requête
        """
        cursor_str = request.query_params.get(self.cursor_query_param)
        if not cursor_str:
            return None
        
        try:
            decoded = base64.b64decode(cursor_str).decode('utf-8')
            return json.loads(decoded)
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
            return None
    
    def _encode_cursor(self, cursor_data):
        """
        Encode les données du curseur
        """
        if not cursor_data:
            return None
        
        cursor_str = json.dumps(cursor_data, default=str)
        return base64.b64encode(cursor_str.encode('utf-8')).decode('utf-8')
    
    def _apply_cursor_filter(self, queryset, cursor_position):
        """
        Applique le filtre basé sur la position du curseur
        """
        # À redéfinir dans les classes filles
        return queryset
    
    def _get_next_cursor_position(self):
        """
        Obtient la position du curseur pour la page suivante
        """
        if not self.results:
            return None
        
        last_item = self.results[-1]
        return self._extract_cursor_data(last_item)
    
    def _get_previous_cursor_position(self):
        """
        Obtient la position du curseur pour la page précédente
        """
        if not self.results:
            return None
        
        first_item = self.results[0]
        return self._extract_cursor_data(first_item, reverse=True)
    
    def _extract_cursor_data(self, item, reverse=False):
        """
        Extrait les données du curseur depuis un élément
        À redéfinir dans les classes filles
        """
        return {'id': getattr(item, 'id', None)}
    
    def _get_current_cursor(self):
        """
        Obtient le curseur courant
        """
        cursor_str = self.request.query_params.get(self.cursor_query_param)
        return cursor_str if cursor_str else None
    
    def _has_previous(self):
        """
        Détermine s'il y a une page précédente
        """
        return self._get_current_cursor() is not None
    
    def _get_cursor_link(self, cursor):
        """
        Génère un lien avec le curseur spécifié
        """
        if not cursor:
            return None
        
        url = self.request.build_absolute_uri()
        return replace_query_param(url, self.cursor_query_param, cursor)


class DateTimeCursorPagination(CursorPagination):
    """
    Pagination cursor basée sur un champ datetime
    Optimale pour les données horodatées
    """
    
    ordering = '-created_at'
    datetime_field = 'created_at'
    
    def _apply_cursor_filter(self, queryset, cursor_position):
        """
        Applique le filtre basé sur datetime
        """
        if 'datetime' not in cursor_position:
            return queryset
        
        cursor_datetime = cursor_position['datetime']
        
        # Convertir en datetime si c'est une string
        if isinstance(cursor_datetime, str):
            try:
                cursor_datetime = datetime.fromisoformat(cursor_datetime.replace('Z', '+00:00'))
            except ValueError:
                return queryset
        
        # Appliquer le filtre selon l'ordre
        if self.ordering.startswith('-'):
            # Ordre décroissant : éléments antérieurs au curseur
            filter_kwargs = {f"{self.datetime_field}__lt": cursor_datetime}
        else:
            # Ordre croissant : éléments postérieurs au curseur
            filter_kwargs = {f"{self.datetime_field}__gt": cursor_datetime}
        
        return queryset.filter(**filter_kwargs)
    
    def _extract_cursor_data(self, item, reverse=False):
        """
        Extrait la datetime pour le curseur
        """
        datetime_value = getattr(item, self.datetime_field, None)
        if datetime_value:
            return {
                'datetime': datetime_value.isoformat(),
                'id': getattr(item, 'id', None)  # ID de fallback
            }
        return {'id': getattr(item, 'id', None)}


class IDCursorPagination(CursorPagination):
    """
    Pagination cursor basée sur l'ID
    Simple et efficace pour la plupart des cas
    """
    
    ordering = '-id'
    id_field = 'id'
    
    def _apply_cursor_filter(self, queryset, cursor_position):
        """
        Applique le filtre basé sur l'ID
        """
        if 'id' not in cursor_position:
            return queryset
        
        cursor_id = cursor_position['id']
        
        # Appliquer le filtre selon l'ordre
        if self.ordering.startswith('-'):
            # Ordre décroissant : IDs inférieurs au curseur
            filter_kwargs = {f"{self.id_field}__lt": cursor_id}
        else:
            # Ordre croissant : IDs supérieurs au curseur
            filter_kwargs = {f"{self.id_field}__gt": cursor_id}
        
        return queryset.filter(**filter_kwargs)
    
    def _extract_cursor_data(self, item, reverse=False):
        """
        Extrait l'ID pour le curseur
        """
        return {'id': getattr(item, self.id_field, None)}


class CustomCursorPagination(CursorPagination):
    """
    Pagination cursor personnalisable pour des ordres complexes
    """
    
    # Configuration des champs d'ordre
    ordering_fields = ['created_at', 'id']  # Ordre multi-champs
    
    def __init__(self, ordering_fields=None):
        super().__init__()
        if ordering_fields:
            self.ordering_fields = ordering_fields
        
        # Construire l'ordre Django
        self.ordering = [f"-{field}" if not field.startswith('-') else field 
                        for field in self.ordering_fields]
    
    def _apply_cursor_filter(self, queryset, cursor_position):
        """
        Applique le filtre pour un ordre multi-champs
        """
        if not cursor_position or 'values' not in cursor_position:
            return queryset
        
        cursor_values = cursor_position['values']
        conditions = models.Q()
        
        # Construire les conditions pour chaque champ d'ordre
        for i, field in enumerate(self.ordering_fields):
            if i >= len(cursor_values):
                break
            
            field_name = field.lstrip('-')
            is_descending = field.startswith('-')
            cursor_value = cursor_values[i]
            
            # Condition stricte pour ce champ
            if is_descending:
                field_condition = models.Q(**{f"{field_name}__lt": cursor_value})
            else:
                field_condition = models.Q(**{f"{field_name}__gt": cursor_value})
            
            # Condition d'égalité pour les champs précédents
            equality_conditions = models.Q()
            for j in range(i):
                prev_field = self.ordering_fields[j].lstrip('-')
                equality_conditions &= models.Q(**{prev_field: cursor_values[j]})
            
            # Combiner les conditions
            if equality_conditions:
                conditions |= equality_conditions & field_condition
            else:
                conditions |= field_condition
        
        return queryset.filter(conditions)
    
    def _extract_cursor_data(self, item, reverse=False):
        """
        Extrait les valeurs pour un curseur multi-champs
        """
        values = []
        for field in self.ordering_fields:
            field_name = field.lstrip('-')
            value = getattr(item, field_name, None)
            
            # Sérialiser les valeurs complexes
            if isinstance(value, datetime):
                value = value.isoformat()
            
            values.append(value)
        
        return {'values': values}


class OptimizedCursorPagination(DateTimeCursorPagination):
    """
    Pagination cursor avec optimisations avancées
    """
    
    # Cache des métadonnées de pagination
    use_metadata_cache = True
    cache_timeout = 300
    
    def paginate_queryset(self, queryset, request, view=None):
        """
        Pagination optimisée avec cache et préchargement
        """
        # Optimisation du queryset si possible
        if hasattr(view, 'get_optimized_queryset'):
            queryset = view.get_optimized_queryset(queryset)
        
        # Utiliser select_related/prefetch_related automatiquement
        queryset = self._optimize_queryset(queryset)
        
        return super().paginate_queryset(queryset, request, view)
    
    def _optimize_queryset(self, queryset):
        """
        Applique les optimisations automatiques au queryset
        """
        try:
            # Détecter les relations à précharger
            model = queryset.model
            
            # select_related pour les ForeignKey
            select_related_fields = []
            for field in model._meta.get_fields():
                if hasattr(field, 'related_model') and field.many_to_one:
                    select_related_fields.append(field.name)
            
            if select_related_fields:
                queryset = queryset.select_related(*select_related_fields[:3])  # Limiter à 3
            
            # prefetch_related pour les relations Many-to-Many
            prefetch_fields = []
            for field in model._meta.get_fields():
                if hasattr(field, 'related_model') and (field.many_to_many or field.one_to_many):
                    prefetch_fields.append(field.name)
            
            if prefetch_fields:
                queryset = queryset.prefetch_related(*prefetch_fields[:2])  # Limiter à 2
            
            return queryset
            
        except Exception:
            # En cas d'erreur, retourner le queryset original
            return queryset 