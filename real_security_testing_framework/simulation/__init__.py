"""
Module de Simulation Workflow NMS
=================================

Ce module fournit une simulation réaliste du workflow Django 
pour les démonstrations et tests du système NMS.
"""

from .workflow_integration import (
    trigger_django_workflow,
    get_django_workflow_status, 
    is_django_workflow_active,
    get_last_django_results
)

__all__ = [
    'trigger_django_workflow',
    'get_django_workflow_status',
    'is_django_workflow_active', 
    'get_last_django_results'
]