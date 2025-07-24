"""
Package pour les adaptateurs d'infrastructure du module reporting.

Ce package contient les adaptateurs qui permettent d'intégrer les services
existants avec le nouveau module reporting.
"""

from .legacy_service_adapter import LegacyReportServiceAdapter

__all__ = [
    'LegacyReportServiceAdapter',
]
