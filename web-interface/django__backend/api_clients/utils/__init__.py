"""
Package d'utilitaires pour le module api_clients.

Ce package contient des fonctions et classes utilitaires pour faciliter
le développement et la documentation des clients API.
"""

from .swagger_utils import (
    apply_swagger_auto_schema,
    auto_schema_viewset,
    generate_schema_for_all_views
)

__all__ = [
    'apply_swagger_auto_schema',
    'auto_schema_viewset',
    'generate_schema_for_all_views'
] 