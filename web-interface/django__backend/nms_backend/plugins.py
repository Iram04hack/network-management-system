"""
Compatibilité pour les anciennes importations.

Ce module réexporte les fonctionnalités du module plugins pour assurer
la compatibilité avec le code existant.

Déprécié: Utilisez directement les importations depuis le module plugins.
"""

from plugins.infrastructure.registry import PluginRegistry, register_plugin

# Réexporter pour la compatibilité avec le code existant
__all__ = [
    'PluginRegistry',
    'register_plugin',
]
