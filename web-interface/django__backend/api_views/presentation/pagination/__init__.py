# Pagination avancée pour les API Views
from .advanced_pagination import (
    AdvancedPageNumberPagination,
    OptimizedLimitOffsetPagination,
    CachingPaginationMixin
)
from .cursor_pagination import (
    CursorPagination,
    DateTimeCursorPagination,
    IDCursorPagination,
    CustomCursorPagination
)

# Alias pour compatibilité
SmartPagination = AdvancedPageNumberPagination

__all__ = [
    'AdvancedPageNumberPagination',
    'OptimizedLimitOffsetPagination',
    'CachingPaginationMixin',
    'CursorPagination',
    'DateTimeCursorPagination',
    'IDCursorPagination',
    'CustomCursorPagination',
    'SmartPagination'
]