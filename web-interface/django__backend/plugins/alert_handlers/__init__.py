"""
Package de handlers d'alertes.

Ce package contient les différents handlers qui traitent les alertes
du système et envoient des notifications par différents canaux.
"""

from .email_handler import EmailAlertHandler
from .slack_handler import SlackAlertHandler

__all__ = [
    'EmailAlertHandler',
    'SlackAlertHandler',
]
