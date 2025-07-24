"""
Exportateur Prometheus pour les métriques de performance.

Ce module fournit un exportateur pour exposer les métriques de performance
des clients API dans un format compatible avec Prometheus.
"""

import time
from typing import Dict, List, Any, Optional, Callable
from datetime import timedelta

from prometheus_client import (
    Counter, 
    Gauge, 
    Histogram, 
    Summary, 
    CollectorRegistry, 
    generate_latest,
    CONTENT_TYPE_LATEST
)

from .performance import PerformanceMetrics, measure_performance

class PrometheusExporter:
    """
    Exportateur Prometheus pour les métriques de performance des clients API.
    """
    
    def __init__(self):
        """
        Initialise l'exportateur Prometheus.
        """
        self.registry = CollectorRegistry()
        
        # Métriques pour les requêtes API
        self.requests_total = Counter(
            'api_client_requests_total',
            'Nombre total de requêtes API',
            ['endpoint', 'status'],
            registry=self.registry
        )
        
        self.request_duration = Histogram(
            'api_client_request_duration_seconds',
            'Durée des requêtes API en secondes',
            ['endpoint'],
            buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
            registry=self.registry
        )
        
        self.request_in_flight = Gauge(
            'api_client_requests_in_flight',
            'Nombre de requêtes API en cours',
            ['endpoint'],
            registry=self.registry
        )
        
        self.request_success_ratio = Gauge(
            'api_client_request_success_ratio',
            'Ratio de succès des requêtes API',
            ['endpoint'],
            registry=self.registry
        )
        
        # Metrics for cache
        self.cache_hit_total = Counter(
            'api_client_cache_hit_total',
            'Nombre total de hits cache',
            ['endpoint'],
            registry=self.registry
        )
        
        self.cache_miss_total = Counter(
            'api_client_cache_miss_total',
            'Nombre total de misses cache',
            ['endpoint'],
            registry=self.registry
        )
        
        # Metrics for circuit breaker
        self.circuit_breaker_state = Gauge(
            'api_client_circuit_breaker_state',
            'État du circuit breaker (0=fermé, 1=ouvert, 2=demi-ouvert)',
            ['endpoint'],
            registry=self.registry
        )
        
        self.circuit_breaker_failures = Counter(
            'api_client_circuit_breaker_failures_total',
            'Nombre total d\'échecs qui ont déclenché le circuit breaker',
            ['endpoint'],
            registry=self.registry
        )
    
    def update_metrics(self, timeframe: Optional[timedelta] = None) -> None:
        """
        Met à jour les métriques Prometheus à partir des métriques de performance.
        
        Args:
            timeframe: Période de temps à considérer (optionnel)
        """
        metrics_service = PerformanceMetrics()
        summaries = metrics_service.get_metrics_summary(timeframe=timeframe)
        
        for summary in summaries:
            # Mise à jour du ratio de succès
            if summary.count > 0:
                success_ratio = summary.success_count / summary.count
                self.request_success_ratio.labels(endpoint=summary.endpoint).set(success_ratio)
            
            # Observer la durée moyenne des requêtes
            if summary.avg_response_time > 0:
                self.request_duration.labels(endpoint=summary.endpoint).observe(
                    summary.avg_response_time
                )
    
    def instrument(self, func: Callable, endpoint_name: Optional[str] = None) -> Callable:
        """
        Instrumente une fonction pour collecter des métriques Prometheus.
        
        Args:
            func: Fonction à instrumenter
            endpoint_name: Nom de l'endpoint (si None, utilise le nom de la fonction)
            
        Returns:
            Fonction instrumentée
        """
        endpoint = endpoint_name or func.__name__
        
        @measure_performance(endpoint)
        def wrapper(*args, **kwargs):
            self.request_in_flight.labels(endpoint=endpoint).inc()
            
            try:
                result = func(*args, **kwargs)
                
                # Collecter des métriques basées sur le résultat
                status = "success"
                if hasattr(result, 'status_code'):
                    status = "success" if 200 <= result.status_code < 400 else "error"
                
                self.requests_total.labels(endpoint=endpoint, status=status).inc()
                
                return result
                
            except Exception as e:
                self.requests_total.labels(endpoint=endpoint, status="error").inc()
                raise
                
            finally:
                self.request_in_flight.labels(endpoint=endpoint).dec()
                
        return wrapper
    
    def generate_metrics(self) -> bytes:
        """
        Génère les métriques au format Prometheus.
        
        Returns:
            Métriques au format Prometheus
        """
        self.update_metrics()
        return generate_latest(self.registry)
    
    def metrics_handler(self, request=None) -> tuple:
        """
        Gestionnaire HTTP pour exposer les métriques Prometheus.
        
        Args:
            request: Requête HTTP (ignorée)
            
        Returns:
            Tuple (corps de réponse, type de contenu)
        """
        return generate_latest(self.registry), CONTENT_TYPE_LATEST

# Créer une instance par défaut pour faciliter l'utilisation
exporter = PrometheusExporter() 