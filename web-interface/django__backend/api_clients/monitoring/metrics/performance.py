"""
Système de métriques de performance pour les clients API.

Ce module fournit des collecteurs de métriques de performance pour surveiller
les appels API et leur temps de réponse.
"""

import time
import threading
import statistics
from functools import wraps
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta

@dataclass
class MetricPoint:
    """
    Point de données pour une métrique.
    """
    timestamp: datetime
    value: float
    endpoint: str
    status_code: int
    success: bool

@dataclass
class MetricSummary:
    """
    Résumé des métriques pour une période donnée.
    """
    endpoint: str
    count: int = 0
    success_count: int = 0
    failure_count: int = 0
    min_response_time: float = float('inf')
    max_response_time: float = 0.0
    avg_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0

class PerformanceMetrics:
    """
    Collecteur de métriques de performance pour les clients API.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Implémentation du singleton pour assurer une instance unique."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialise le collecteur de métriques."""
        if self._initialized:
            return
            
        self._metrics: List[MetricPoint] = []
        self._endpoints: Dict[str, Dict[str, Any]] = {}
        self._retention_period = timedelta(hours=24)
        self._lock = threading.Lock()
        self._initialized = True
    
    def record_metric(
        self, 
        endpoint: str, 
        response_time: float, 
        status_code: int, 
        success: bool
    ) -> None:
        """
        Enregistre une métrique de performance.
        
        Args:
            endpoint: Endpoint de l'API
            response_time: Temps de réponse en secondes
            status_code: Code de statut HTTP
            success: Indique si l'appel a réussi
        """
        now = datetime.now()
        
        with self._lock:
            # Ajouter la nouvelle métrique
            self._metrics.append(MetricPoint(
                timestamp=now,
                value=response_time,
                endpoint=endpoint,
                status_code=status_code,
                success=success
            ))
            
            # Mettre à jour les statistiques de l'endpoint
            if endpoint not in self._endpoints:
                self._endpoints[endpoint] = {
                    'count': 0,
                    'success_count': 0,
                    'failure_count': 0,
                    'min_time': float('inf'),
                    'max_time': 0.0,
                    'total_time': 0.0
                }
            
            self._endpoints[endpoint]['count'] += 1
            if success:
                self._endpoints[endpoint]['success_count'] += 1
            else:
                self._endpoints[endpoint]['failure_count'] += 1
            
            self._endpoints[endpoint]['min_time'] = min(
                self._endpoints[endpoint]['min_time'], 
                response_time
            )
            self._endpoints[endpoint]['max_time'] = max(
                self._endpoints[endpoint]['max_time'], 
                response_time
            )
            self._endpoints[endpoint]['total_time'] += response_time
            
            # Supprimer les anciennes métriques
            cutoff_time = now - self._retention_period
            self._metrics = [
                m for m in self._metrics if m.timestamp > cutoff_time
            ]
    
    def get_metrics_summary(
        self, 
        endpoint: Optional[str] = None, 
        timeframe: Optional[timedelta] = None
    ) -> List[MetricSummary]:
        """
        Récupère un résumé des métriques de performance.
        
        Args:
            endpoint: Filtrer par endpoint spécifique (optionnel)
            timeframe: Période de temps à considérer (optionnel)
            
        Returns:
            Liste de résumés de métriques par endpoint
        """
        now = datetime.now()
        cutoff_time = now - (timeframe or self._retention_period)
        
        with self._lock:
            # Filtrer les métriques pertinentes
            relevant_metrics = [
                m for m in self._metrics 
                if m.timestamp > cutoff_time
                and (endpoint is None or m.endpoint == endpoint)
            ]
            
            # Grouper par endpoint
            metrics_by_endpoint: Dict[str, List[MetricPoint]] = {}
            for metric in relevant_metrics:
                if metric.endpoint not in metrics_by_endpoint:
                    metrics_by_endpoint[metric.endpoint] = []
                metrics_by_endpoint[metric.endpoint].append(metric)
            
            # Calculer les statistiques pour chaque endpoint
            summaries = []
            for endpoint_name, metrics in metrics_by_endpoint.items():
                response_times = [m.value for m in metrics]
                success_count = sum(1 for m in metrics if m.success)
                
                # Calculer les percentiles
                p95 = 0.0
                p99 = 0.0
                if response_times:
                    response_times.sort()
                    if len(response_times) >= 20:  # Au moins 20 points pour les percentiles
                        p95 = response_times[int(len(response_times) * 0.95)]
                        p99 = response_times[int(len(response_times) * 0.99)]
                
                summary = MetricSummary(
                    endpoint=endpoint_name,
                    count=len(metrics),
                    success_count=success_count,
                    failure_count=len(metrics) - success_count,
                    min_response_time=min(response_times) if response_times else 0.0,
                    max_response_time=max(response_times) if response_times else 0.0,
                    avg_response_time=statistics.mean(response_times) if response_times else 0.0,
                    p95_response_time=p95,
                    p99_response_time=p99
                )
                summaries.append(summary)
            
            return summaries
    
    def clear_metrics(self) -> None:
        """
        Efface toutes les métriques enregistrées.
        """
        with self._lock:
            self._metrics = []
            self._endpoints = {}
    
    def set_retention_period(self, period: timedelta) -> None:
        """
        Définit la période de rétention des métriques.
        
        Args:
            period: Période de rétention
        """
        with self._lock:
            self._retention_period = period

def measure_performance(endpoint_name: Optional[str] = None):
    """
    Décorateur pour mesurer la performance d'une méthode d'API.
    
    Args:
        endpoint_name: Nom de l'endpoint (si None, utilise le nom de la méthode)
        
    Returns:
        Fonction décorée avec mesure de performance
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            metrics = PerformanceMetrics()
            endpoint = endpoint_name or func.__name__
            
            start_time = time.time()
            success = True
            status_code = 200
            
            try:
                result = func(*args, **kwargs)
                
                # Essayer d'extraire le code de statut si c'est une réponse HTTP
                if hasattr(result, 'status_code'):
                    status_code = result.status_code
                    success = 200 <= status_code < 400
                
                return result
                
            except Exception as e:
                success = False
                status_code = 500
                raise
                
            finally:
                response_time = time.time() - start_time
                metrics.record_metric(
                    endpoint=endpoint,
                    response_time=response_time,
                    status_code=status_code,
                    success=success
                )
        
        return wrapper
    
    return decorator

# Créer une instance singleton
metrics = PerformanceMetrics() 