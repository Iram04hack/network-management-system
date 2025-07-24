"""
Module de gestion de la sécurité.

Ce module implémente les fonctionnalités de sécurité du système, notamment:
- Gestion des règles de sécurité (firewall, IDS, ACL)
- Détection et gestion des alertes de sécurité
- Intégration avec Suricata et Fail2Ban
- Analyse d'impact des politiques de sécurité
- Détection de conflits entre règles
- Renseignement sur les menaces
"""

default_app_config = 'security_management.apps.SecurityManagementConfig'

__version__ = '1.0.0' 