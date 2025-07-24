"""
Pagination avancée pour les API Views
Inclut optimisations performance, mise en cache et pagination intelligente
"""

import hashlib
from typing import Dict, Any, Optional
from collections import OrderedDict

from django.core.cache import cache
from django.core.paginator import Paginator
from django.db import models
from django.conf import settings
from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.utils.urls import replace_query_param, remove_query_param


class CachingPaginationMixin:
    """
    Mixin pour ajouter la mise en cache aux paginations
    """
    
    cache_timeout = getattr(settings, 'PAGINATION_CACHE_TIMEOUT', 300)  # 5 minutes
    cache_key_prefix = 'pagination'
    
    def get_cache_key(self, request, queryset) -> str:
        """
        Génère une clé de cache unique pour la requête paginée
        """
        # Paramètres de la requête
        query_params = dict(request.query_params)
        
        # Hash du queryset (approximatif)
        queryset_hash = self._get_queryset_hash(queryset)
        
        # Informations utilisateur
        user_id = getattr(request.user, 'id', 'anonymous')
        
        # Construction de la clé
        cache_data = {
            'user_id': user_id,
            'query_params': query_params,
            'queryset_hash': queryset_hash,
            'pagination_class': self.__class__.__name__
        }
        
        cache_string = str(sorted(cache_data.items()))
        cache_hash = hashlib.md5(cache_string.encode()).hexdigest()
        
        return f"{self.cache_key_prefix}:{cache_hash}"
    
    def _get_queryset_hash(self, queryset) -> str:
        """
        Génère un hash approximatif du queryset pour le cache
        """
        try:
            # Utiliser la requête SQL comme approximation
            sql_hash = hashlib.md5(str(queryset.query).encode()).hexdigest()[:8]
            return f"{queryset.model._meta.label}:{sql_hash}"
        except Exception:
            return f"{queryset.model._meta.label}:no_hash"
    
    def get_cached_page(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Récupère une page depuis le cache
        """
        return cache.get(cache_key)
    
    def cache_page(self, cache_key: str, page_data: Dict[str, Any]):
        """
        Met en cache une page
        """
        cache.set(cache_key, page_data, self.cache_timeout)
    
    def invalidate_cache(self, model_class):
        """
        Invalide le cache pour un modèle donné
        """
        # Simple invalidation : supprimer toutes les clés commençant par le préfixe
        # Dans un vrai système, on utiliserait des tags de cache
        cache.delete_many(cache.iter_keys(f"{self.cache_key_prefix}:*"))


class AdvancedPageNumberPagination(CachingPaginationMixin, PageNumberPagination):
    """
    Pagination par numéro de page avec fonctionnalités avancées :
    - Mise en cache automatique
    - Métadonnées enrichies
    - Optimisation des comptages
    - Support pour les grands datasets
    """
    
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 1000
    
    # Configuration du cache
    cache_timeout = 300
    
    # Configuration des métadonnées
    include_total_count = True
    include_page_links = True
    include_range_info = True
    
    def paginate_queryset(self, queryset, request, view=None):
        """
        Pagine le queryset avec mise en cache et optimisations
        """
        # Vérifier le cache en premier
        cache_key = self.get_cache_key(request, queryset)
        cached_result = self.get_cached_page(cache_key)
        
        if cached_result:
            # Reconstituer l'état de pagination depuis le cache
            self.page = cached_result['page']
            self.request = request
            return cached_result['results']
        
        # Pagination normale
        page_size = self.get_page_size(request)
        if not page_size:
            return None
        
        # Optimisation : utiliser select_related/prefetch_related si disponible
        if hasattr(view, 'get_optimized_queryset'):
            queryset = view.get_optimized_queryset(queryset)
        
        paginator = self.django_paginator_class(queryset, page_size)
        page_number = request.query_params.get(self.page_query_param, 1)
        
        try:
            self.page = paginator.page(page_number)
        except Exception:
            self.page = paginator.page(1)
        
        self.request = request
        results = list(self.page)
        
        # Mettre en cache le résultat
        cache_data = {
            'page': self.page,
            'results': results,
            'total_count': paginator.count if self.include_total_count else None
        }
        self.cache_page(cache_key, cache_data)
        
        return results
    
    def get_paginated_response(self, data):
        """
        Retourne une réponse paginée avec métadonnées enrichies
        """
        response_data = OrderedDict([
            ('results', data)
        ])
        
        # Informations de navigation
        if self.include_page_links:
            response_data['links'] = {
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
                'first': self.get_first_link(),
                'last': self.get_last_link()
            }
        
        # Informations de pagination
        response_data['pagination'] = {
            'current_page': self.page.number,
            'page_size': self.get_page_size(self.request),
            'total_pages': self.page.paginator.num_pages,
        }
        
        # Informations de comptage
        if self.include_total_count:
            response_data['pagination']['total_count'] = self.page.paginator.count
        
        # Informations de plage
        if self.include_range_info:
            start_index = self.page.start_index()
            end_index = self.page.end_index()
            response_data['pagination']['range'] = {
                'start': start_index,
                'end': end_index,
                'current_page_count': len(data)
            }
        
        # Métadonnées additionnelles
        response_data['pagination']['has_next'] = self.page.has_next()
        response_data['pagination']['has_previous'] = self.page.has_previous()
        
        return Response(response_data)
    
    def get_first_link(self):
        """
        Retourne le lien vers la première page
        """
        if not self.page.has_previous():
            return None
        url = self.request.build_absolute_uri()
        return remove_query_param(url, self.page_query_param)
    
    def get_last_link(self):
        """
        Retourne le lien vers la dernière page
        """
        if not self.page.has_next():
            return None
        url = self.request.build_absolute_uri()
        return replace_query_param(url, self.page_query_param, self.page.paginator.num_pages)


class OptimizedLimitOffsetPagination(CachingPaginationMixin, LimitOffsetPagination):
    """
    Pagination Limit/Offset optimisée pour les grands datasets
    """
    
    default_limit = 25
    limit_query_param = 'limit'
    offset_query_param = 'offset'
    max_limit = 1000
    
    # Seuil à partir duquel utiliser les optimisations
    optimization_threshold = 10000
    
    def paginate_queryset(self, queryset, request, view=None):
        """
        Pagine avec optimisations pour les grands datasets
        """
        # Vérifier le cache
        cache_key = self.get_cache_key(request, queryset)
        cached_result = self.get_cached_page(cache_key)
        
        if cached_result:
            self.limit = cached_result['limit']
            self.offset = cached_result['offset']
            self.count = cached_result['count']
            self.request = request
            return cached_result['results']
        
        self.limit = self.get_limit(request)
        if self.limit is None:
            return None
        
        self.offset = self.get_offset(request)
        self.count = self.get_count(queryset)
        self.request = request
        
        # Optimisation pour les grands offsets
        if self.offset > self.optimization_threshold:
            results = self._optimized_slice(queryset, self.offset, self.limit)
        else:
            results = list(queryset[self.offset:self.offset + self.limit])
        
        # Cache
        cache_data = {
            'limit': self.limit,
            'offset': self.offset,
            'count': self.count,
            'results': results
        }
        self.cache_page(cache_key, cache_data)
        
        return results
    
    def _optimized_slice(self, queryset, offset, limit):
        """
        Slice optimisé pour les grands offsets utilisant des techniques avancées
        """
        try:
            # Technique 1 : Utiliser le curseur si un ID est disponible
            if hasattr(queryset.model, 'id'):
                # Obtenir l'ID de départ
                start_ids = list(queryset.values_list('id', flat=True)[offset:offset+1])
                if start_ids:
                    start_id = start_ids[0]
                    return list(queryset.filter(id__gte=start_id)[:limit])
            
            # Technique 2 : Fallback vers la méthode standard
            return list(queryset[offset:offset + limit])
            
        except Exception:
            # Fallback sécurisé
            return list(queryset[offset:offset + limit])
    
    def get_count(self, queryset):
        """
        Obtient le compte total avec optimisations
        """
        try:
            # Pour les très gros datasets, éviter le COUNT(*)
            if hasattr(queryset, '_result_cache') and queryset._result_cache is not None:
                return len(queryset._result_cache)
            
            # Utiliser une approximation si disponible
            if hasattr(queryset.model._meta.db_table, 'cardinality'):
                return queryset.model._meta.db_table.cardinality
            
            # COUNT standard
            return queryset.count()
            
        except Exception:
            return 0
    
    def get_paginated_response(self, data):
        """
        Réponse paginée avec informations sur les performances
        """
        return Response(OrderedDict([
            ('results', data),
            ('pagination', {
                'limit': self.limit,
                'offset': self.offset,
                'count': self.count,
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
                'page_info': {
                    'current_page': (self.offset // self.limit) + 1 if self.limit else 1,
                    'total_pages': (self.count // self.limit) + (1 if self.count % self.limit else 0) if self.limit else 1,
                    'has_next': self.offset + self.limit < self.count,
                    'has_previous': self.offset > 0
                }
            })
        ]))


class SmartPagination(AdvancedPageNumberPagination):
    """
    Pagination intelligente qui s'adapte au type de données et à la charge
    """
    
    # Tailles de page adaptatives selon le type de contenu
    adaptive_page_sizes = {
        'light': 100,   # Données légères (IDs, noms)
        'medium': 50,   # Données moyennes (équipements basiques)
        'heavy': 25,    # Données lourdes (détails complets)
        'very_heavy': 10  # Données très lourdes (avec relations)
    }
    
    def get_page_size(self, request):
        """
        Détermine la taille de page optimale selon le contexte
        """
        # Taille explicitement demandée
        explicit_size = super().get_page_size(request)
        if explicit_size:
            return min(explicit_size, self.max_page_size)
        
        # Détection du type de contenu
        content_type = self._detect_content_type(request)
        adaptive_size = self.adaptive_page_sizes.get(content_type, self.page_size)
        
        # Ajustement selon la charge du serveur
        load_factor = self._get_load_factor()
        if load_factor > 0.8:  # Charge élevée
            adaptive_size = min(adaptive_size, 25)
        elif load_factor < 0.3:  # Charge faible
            adaptive_size = min(adaptive_size * 2, self.max_page_size)
        
        return adaptive_size
    
    def _detect_content_type(self, request):
        """
        Détecte le type de contenu basé sur les paramètres de requête
        """
        # Vérifier les paramètres qui indiquent un contenu lourd
        heavy_params = ['include_details', 'with_relations', 'full_data']
        if any(param in request.query_params for param in heavy_params):
            return 'very_heavy'
        
        # Vérifier les champs demandés
        fields = request.query_params.get('fields', '')
        if len(fields.split(',')) > 10:
            return 'heavy'
        
        # Type par défaut
        return 'medium'
    
    def _get_load_factor(self):
        """
        Estime la charge actuelle du serveur (simplifiée)
        """
        try:
            # Dans un vrai système, on surveillerait CPU, mémoire, DB, etc.
            # Ici, simulation basée sur le cache
            cache_stats = cache.get('system_load', 0.5)
            return min(cache_stats, 1.0)
        except Exception:
            return 0.5  # Charge moyenne par défaut 