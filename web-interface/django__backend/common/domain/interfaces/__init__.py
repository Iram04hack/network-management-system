"""
Interfaces pour les services du module Common.

Ce package définit les interfaces (ports) suivant le principe de l'architecture hexagonale.
Les interfaces décrivent les contrats que doivent respecter les implémentations de services.
"""

from .notification import NotificationInterface
from .alert import AlertInterface
from .plugin import PluginInterface
from .unified_alert import UnifiedAlertInterface

__all__ = [
    'NotificationInterface',
    'AlertInterface',
    'PluginInterface',
    'UnifiedAlertInterface',
] 