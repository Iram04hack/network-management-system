"""
Framework de Tests de Sécurité NMS - Version Unifiée et Réelle
=============================================================

Ce framework implémente toutes les fonctionnalités de l'ancien security_testing
dans une architecture moderne avec communication directe avec les modules Django.

Workflow RÉEL :
1. Framework affiche la liste des projets GNS3 (via Django API)
2. Utilisateur choisit un projet/réseau
3. Framework transfère automatiquement l'info aux modules Django (gns3_integration/common)
4. Modules Django allument et analysent le réseau
5. Framework demande le niveau de tests à l'utilisateur
6. Framework commence l'injection de trafic RÉEL
7. Automatiquement, tout le workflow Django se déclenche via Celery
8. Surveillance et rapports en temps réel

Fonctionnalités conservées :
- Tous les types d'attaques de l'ancien framework
- Génération de trafic réel adapté aux équipements détectés
- Communication bidirectionnelle avec Django via APIs
- Utilisation de Celery pour déclencher les workflows
- Rapports et analyses complètes

Auteur: Expert Cybersécurité NMS
Date: 2025-07-13
Version: 2.0 (Unifiée et Réelle)
"""

__version__ = "2.0.0"
__author__ = "Expert Cybersécurité NMS"
__description__ = "Framework de Tests de Sécurité NMS Unifié et Réel"

# Structure des modules
__all__ = [
    'RealSecurityTestingFramework',
    'DjangoCommunicationManager', 
    'GNS3IntegrationManager',
    'RealTrafficGenerator',
    'SecurityAttackEngine',
    'ReportingEngine',
    'CeleryWorkflowTrigger'
]