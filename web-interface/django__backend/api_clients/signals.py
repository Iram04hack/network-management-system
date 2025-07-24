"""
Signaux pour l'application api_clients.

Ce module contient les signaux pour l'application api_clients.
"""

import logging
from django.dispatch import Signal, receiver
from django.db.models.signals import post_save, post_delete

# Logger
logger = logging.getLogger(__name__)

# Signaux personnalisés
api_client_request_success = Signal()  # Envoyé lorsqu'une requête API réussit
api_client_request_failure = Signal()  # Envoyé lorsqu'une requête API échoue
api_client_registered = Signal()       # Envoyé lorsqu'un nouveau client API est enregistré
api_client_unregistered = Signal()     # Envoyé lorsqu'un client API est désenregistré

@receiver(api_client_request_success)
def log_api_client_request_success(sender, client_name, response_time, **kwargs):
    """
    Enregistre les requêtes API réussies.
    
    Args:
        sender: L'expéditeur du signal.
        client_name: Le nom du client API.
        response_time: Le temps de réponse en secondes.
        **kwargs: Arguments supplémentaires.
    """
    logger.info(f"API client '{client_name}' request succeeded in {response_time:.3f}s")
    
    # On pourrait ajouter ici l'enregistrement des métriques
    from api_clients.metrics import ApiClientMetrics
    metrics = ApiClientMetrics()
    metrics.record_request(client_name, True, response_time)

@receiver(api_client_request_failure)
def log_api_client_request_failure(sender, client_name, error, response_time, **kwargs):
    """
    Enregistre les requêtes API échouées.
    
    Args:
        sender: L'expéditeur du signal.
        client_name: Le nom du client API.
        error: L'erreur survenue.
        response_time: Le temps de réponse en secondes.
        **kwargs: Arguments supplémentaires.
    """
    logger.error(f"API client '{client_name}' request failed in {response_time:.3f}s: {error}")
    
    # On pourrait ajouter ici l'enregistrement des métriques
    from api_clients.metrics import ApiClientMetrics
    metrics = ApiClientMetrics()
    metrics.record_request(client_name, False, response_time)

@receiver(api_client_registered)
def log_api_client_registered(sender, client_name, **kwargs):
    """
    Enregistre l'enregistrement d'un nouveau client API.
    
    Args:
        sender: L'expéditeur du signal.
        client_name: Le nom du client API.
        **kwargs: Arguments supplémentaires.
    """
    logger.info(f"API client '{client_name}' registered")

@receiver(api_client_unregistered)
def log_api_client_unregistered(sender, client_name, **kwargs):
    """
    Enregistre le désenregistrement d'un client API.
    
    Args:
        sender: L'expéditeur du signal.
        client_name: Le nom du client API.
        **kwargs: Arguments supplémentaires.
    """
    logger.info(f"API client '{client_name}' unregistered") 