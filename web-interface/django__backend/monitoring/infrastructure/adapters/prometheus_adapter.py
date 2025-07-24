"""
Adaptateur pour l'intégration avec Prometheus.

Ce module fournit l'interface pour interagir avec Prometheus
et collecter des métriques en temps réel.
"""

import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class PrometheusAdapter:
    """
    Adaptateur pour l'intégration avec Prometheus.
    
    Permet de collecter des métriques depuis Prometheus
    et de les intégrer dans le système de monitoring.
    """
    
    def __init__(self, base_url: str = "http://localhost:9090", timeout: int = 30):
        """
        Initialise l'adaptateur Prometheus.
        
        Args:
            base_url: URL de base de Prometheus
            timeout: Délai d'attente pour les requêtes
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        
    def query_instant(self, query: str, time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Exécute une requête instantanée sur Prometheus.
        
        Args:
            query: Requête PromQL
            time: Timestamp pour la requête (optionnel)
            
        Returns:
            Résultat de la requête
        """
        try:
            url = urljoin(self.base_url, '/api/v1/query')
            params = {'query': query}
            
            if time:
                params['time'] = time.timestamp()
                
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] != 'success':
                raise Exception(f"Erreur Prometheus: {data.get('error', 'Erreur inconnue')}")
                
            return {
                'success': True,
                'data': data['data'],
                'query': query,
                'timestamp': datetime.now().isoformat()
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur de connexion Prometheus: {e}")
            return {
                'success': False,
                'error': f"Erreur de connexion: {str(e)}",
                'query': query
            }
        except Exception as e:
            logger.error(f"Erreur lors de la requête Prometheus: {e}")
            return {
                'success': False,
                'error': str(e),
                'query': query
            }
    
    def query_range(self, query: str, start: datetime, end: datetime, step: str = "15s") -> Dict[str, Any]:
        """
        Exécute une requête sur une plage de temps.
        
        Args:
            query: Requête PromQL
            start: Timestamp de début
            end: Timestamp de fin
            step: Pas de temps (ex: "15s", "1m", "5m")
            
        Returns:
            Résultat de la requête sur la plage
        """
        try:
            url = urljoin(self.base_url, '/api/v1/query_range')
            params = {
                'query': query,
                'start': start.timestamp(),
                'end': end.timestamp(),
                'step': step
            }
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] != 'success':
                raise Exception(f"Erreur Prometheus: {data.get('error', 'Erreur inconnue')}")
                
            return {
                'success': True,
                'data': data['data'],
                'query': query,
                'start': start.isoformat(),
                'end': end.isoformat(),
                'step': step,
                'timestamp': datetime.now().isoformat()
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur de connexion Prometheus: {e}")
            return {
                'success': False,
                'error': f"Erreur de connexion: {str(e)}",
                'query': query
            }
        except Exception as e:
            logger.error(f"Erreur lors de la requête Prometheus: {e}")
            return {
                'success': False,
                'error': str(e),
                'query': query
            }
    
    def get_targets(self) -> Dict[str, Any]:
        """
        Récupère la liste des cibles Prometheus.
        
        Returns:
            Liste des cibles et leur état
        """
        try:
            url = urljoin(self.base_url, '/api/v1/targets')
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] != 'success':
                raise Exception(f"Erreur Prometheus: {data.get('error', 'Erreur inconnue')}")
                
            return {
                'success': True,
                'targets': data['data']['activeTargets'],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des cibles: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_metrics_list(self) -> Dict[str, Any]:
        """
        Récupère la liste des métriques disponibles.
        
        Returns:
            Liste des métriques
        """
        try:
            url = urljoin(self.base_url, '/api/v1/label/__name__/values')
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] != 'success':
                raise Exception(f"Erreur Prometheus: {data.get('error', 'Erreur inconnue')}")
                
            return {
                'success': True,
                'metrics': data['data'],
                'count': len(data['data']),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des métriques: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def collect_system_metrics(self, instance: str = "localhost:9100") -> Dict[str, Any]:
        """
        Collecte les métriques système standard depuis node_exporter.
        
        Args:
            instance: Instance node_exporter à surveiller
            
        Returns:
            Métriques système collectées
        """
        metrics = {}
        
        # Métriques CPU
        cpu_query = f'100 - (avg by (instance) (irate(node_cpu_seconds_total{{mode="idle",instance="{instance}"}}[5m])) * 100)'
        cpu_result = self.query_instant(cpu_query)
        if cpu_result['success'] and cpu_result['data']['result']:
            metrics['cpu_usage'] = float(cpu_result['data']['result'][0]['value'][1])
        
        # Métriques mémoire
        memory_query = f'(1 - (node_memory_MemAvailable_bytes{{instance="{instance}"}} / node_memory_MemTotal_bytes{{instance="{instance}"}}) * 100)'
        memory_result = self.query_instant(memory_query)
        if memory_result['success'] and memory_result['data']['result']:
            metrics['memory_usage'] = float(memory_result['data']['result'][0]['value'][1])
        
        # Métriques disque
        disk_query = f'100 - ((node_filesystem_avail_bytes{{instance="{instance}",mountpoint="/"}} / node_filesystem_size_bytes{{instance="{instance}",mountpoint="/"}}) * 100)'
        disk_result = self.query_instant(disk_query)
        if disk_result['success'] and disk_result['data']['result']:
            metrics['disk_usage'] = float(disk_result['data']['result'][0]['value'][1])
        
        # Métriques réseau
        network_in_query = f'irate(node_network_receive_bytes_total{{instance="{instance}",device!~"lo|veth.*|docker.*"}}[5m])'
        network_in_result = self.query_instant(network_in_query)
        if network_in_result['success'] and network_in_result['data']['result']:
            metrics['network_in'] = sum(float(result['value'][1]) for result in network_in_result['data']['result'])
        
        network_out_query = f'irate(node_network_transmit_bytes_total{{instance="{instance}",device!~"lo|veth.*|docker.*"}}[5m])'
        network_out_result = self.query_instant(network_out_query)
        if network_out_result['success'] and network_out_result['data']['result']:
            metrics['network_out'] = sum(float(result['value'][1]) for result in network_out_result['data']['result'])
        
        return {
            'success': True,
            'metrics': metrics,
            'instance': instance,
            'timestamp': datetime.now().isoformat()
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Teste la connexion à Prometheus.
        
        Returns:
            Résultat du test de connexion
        """
        try:
            url = urljoin(self.base_url, '/api/v1/query')
            params = {'query': 'up'}
            
            response = self.session.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                'success': True,
                'status': data['status'],
                'url': self.base_url,
                'response_time': response.elapsed.total_seconds(),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'url': self.base_url,
                'timestamp': datetime.now().isoformat()
            } 