"""
Module de métriques pour les clients API.

Ce module contient la classe ApiClientMetrics qui gère les métriques des clients API.
"""

import logging
import time
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ApiClientMetrics:
    """
    Classe pour collecter des métriques sur les clients API.
    
    Cette classe permet de collecter des métriques sur les clients API,
    comme le temps de réponse, le nombre de requêtes, etc.
    """
    
    def __init__(self):
        """
        Initialise les métriques.
        """
        self._metrics = {
            'requests': {
                'total': 0,
                'success': 0,
                'error': 0
            },
            'response_time': {
                'avg': 0,
                'min': None,
                'max': None
            },
            'clients': {}
        }
        self._start_time = time.time()
    
    def record_request(self, client_name: str, success: bool, response_time: float):
        """
        Enregistre une requête.
        
        Args:
            client_name: Le nom du client API.
            success: Si la requête a réussi.
            response_time: Le temps de réponse de la requête en secondes.
        """
        # Mise à jour des métriques globales
        self._metrics['requests']['total'] += 1
        if success:
            self._metrics['requests']['success'] += 1
        else:
            self._metrics['requests']['error'] += 1
        
        # Mise à jour des temps de réponse
        if self._metrics['response_time']['min'] is None or response_time < self._metrics['response_time']['min']:
            self._metrics['response_time']['min'] = response_time
        
        if self._metrics['response_time']['max'] is None or response_time > self._metrics['response_time']['max']:
            self._metrics['response_time']['max'] = response_time
        
        # Calcul de la moyenne glissante
        current_avg = self._metrics['response_time']['avg']
        total_requests = self._metrics['requests']['total']
        self._metrics['response_time']['avg'] = (current_avg * (total_requests - 1) + response_time) / total_requests
        
        # Mise à jour des métriques par client
        if client_name not in self._metrics['clients']:
            self._metrics['clients'][client_name] = {
                'requests': {
                    'total': 0,
                    'success': 0,
                    'error': 0
                },
                'response_time': {
                    'avg': 0,
                    'min': None,
                    'max': None
                }
            }
        
        client_metrics = self._metrics['clients'][client_name]
        client_metrics['requests']['total'] += 1
        if success:
            client_metrics['requests']['success'] += 1
        else:
            client_metrics['requests']['error'] += 1
        
        # Mise à jour des temps de réponse du client
        if client_metrics['response_time']['min'] is None or response_time < client_metrics['response_time']['min']:
            client_metrics['response_time']['min'] = response_time
        
        if client_metrics['response_time']['max'] is None or response_time > client_metrics['response_time']['max']:
            client_metrics['response_time']['max'] = response_time
        
        # Calcul de la moyenne glissante pour le client
        current_avg = client_metrics['response_time']['avg']
        total_requests = client_metrics['requests']['total']
        client_metrics['response_time']['avg'] = (current_avg * (total_requests - 1) + response_time) / total_requests
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Récupère les métriques.
        
        Returns:
            Les métriques collectées.
        """
        uptime = time.time() - self._start_time
        metrics = self._metrics.copy()
        metrics['uptime'] = uptime
        return metrics
    
    def get_client_metrics(self, client_name: str) -> Dict[str, Any]:
        """
        Récupère les métriques d'un client.
        
        Args:
            client_name: Le nom du client API.
            
        Returns:
            Les métriques du client.
        """
        if client_name not in self._metrics['clients']:
            return {
                'requests': {
                    'total': 0,
                    'success': 0,
                    'error': 0
                },
                'response_time': {
                    'avg': 0,
                    'min': None,
                    'max': None
                }
            }
        
        return self._metrics['clients'][client_name].copy()
    
    def reset_metrics(self):
        """
        Réinitialise les métriques.
        """
        self._metrics = {
            'requests': {
                'total': 0,
                'success': 0,
                'error': 0
            },
            'response_time': {
                'avg': 0,
                'min': None,
                'max': None
            },
            'clients': {}
        }
        self._start_time = time.time() 