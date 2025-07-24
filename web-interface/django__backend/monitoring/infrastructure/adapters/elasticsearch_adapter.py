"""
Adaptateur Elasticsearch pour l'indexation et la recherche de logs et métriques.

Ce module fournit l'interface pour interagir avec Elasticsearch
pour stocker et rechercher les données de monitoring.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import requests
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class ElasticsearchAdapter:
    """
    Adaptateur pour l'intégration avec Elasticsearch.
    
    Permet d'indexer, rechercher et analyser les logs et métriques
    de monitoring en utilisant l'API REST d'Elasticsearch.
    """
    
    def __init__(self, base_url: str = "http://localhost:9200", timeout: int = 30):
        """
        Initialise l'adaptateur Elasticsearch.
        
        Args:
            base_url: URL de base d'Elasticsearch
            timeout: Délai d'attente pour les requêtes
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Teste la connexion à Elasticsearch.
        
        Returns:
            Résultat du test de connexion
        """
        try:
            response = self.session.get(self.base_url, timeout=10)
            response.raise_for_status()
            
            cluster_info = response.json()
            
            return {
                'success': True,
                'cluster_name': cluster_info.get('cluster_name'),
                'version': cluster_info.get('version', {}).get('number'),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def create_index(self, index_name: str, mapping: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Crée un index Elasticsearch.
        
        Args:
            index_name: Nom de l'index
            mapping: Mapping des champs (optionnel)
            
        Returns:
            Résultat de la création
        """
        try:
            url = urljoin(self.base_url, f'/{index_name}')
            
            body = {}
            if mapping:
                body['mappings'] = mapping
            
            response = self.session.put(url, json=body, timeout=self.timeout)
            
            if response.status_code == 400:
                # Index déjà existant
                return {
                    'success': True,
                    'message': 'Index already exists',
                    'index_name': index_name,
                    'timestamp': datetime.now().isoformat()
                }
            
            response.raise_for_status()
            result = response.json()
            
            return {
                'success': True,
                'result': result,
                'index_name': index_name,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'index {index_name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'index_name': index_name,
                'timestamp': datetime.now().isoformat()
            }
    
    def index_document(self, index_name: str, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Indexe un document dans Elasticsearch.
        
        Args:
            index_name: Nom de l'index
            document: Document à indexer
            
        Returns:
            Résultat de l'indexation
        """
        try:
            url = f"{self.base_url}/{index_name}/_doc"
            
            if '@timestamp' not in document:
                document['@timestamp'] = datetime.now().isoformat()
            
            response = self.session.post(url, json=document, timeout=self.timeout)
            response.raise_for_status()
            
            return {
                'success': True,
                'result': response.json(),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'indexation dans {index_name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def bulk_index(self, operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Indexe plusieurs documents en une seule requête.
        
        Args:
            operations: Liste des opérations d'indexation
            
        Returns:
            Résultat de l'indexation en bulk
        """
        try:
            url = urljoin(self.base_url, '/_bulk')
            
            # Construire le body pour l'opération bulk
            bulk_body = []
            for operation in operations:
                action = operation.get('action', 'index')
                index_name = operation['index']
                document = operation['document']
                doc_id = operation.get('id')
                
                action_line = {action: {'_index': index_name}}
                if doc_id:
                    action_line[action]['_id'] = doc_id
                
                bulk_body.append(json.dumps(action_line))
                
                if action in ['index', 'create', 'update']:
                    if '@timestamp' not in document:
                        document['@timestamp'] = datetime.now().isoformat()
                    bulk_body.append(json.dumps(document))
            
            bulk_data = '\n'.join(bulk_body) + '\n'
            
            headers = {'Content-Type': 'application/x-ndjson'}
            response = self.session.post(url, data=bulk_data, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            
            # Analyser les erreurs
            errors = []
            if result.get('errors'):
                for item in result.get('items', []):
                    for action, details in item.items():
                        if details.get('error'):
                            errors.append(details['error'])
            
            return {
                'success': not result.get('errors', False),
                'result': result,
                'processed': len(operations),
                'errors': errors,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'indexation bulk: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def search(self, index_name: str, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Effectue une recherche dans Elasticsearch.
        
        Args:
            index_name: Nom de l'index ou pattern d'index
            query: Requête Elasticsearch DSL
            
        Returns:
            Résultats de la recherche
        """
        try:
            url = f"{self.base_url}/{index_name}/_search"
            
            search_body = {
                'query': query,
                'size': 100,
                'sort': [{'@timestamp': {'order': 'desc'}}]
            }
            
            response = self.session.post(url, json=search_body, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            hits = result.get('hits', {})
            
            return {
                'success': True,
                'documents': [hit['_source'] for hit in hits.get('hits', [])],
                'total': hits.get('total', {}).get('value', 0),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche dans {index_name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def aggregate(self, index_name: str, aggregations: Dict[str, Any], 
                 query: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Effectue des agrégations sur les données.
        
        Args:
            index_name: Nom de l'index
            aggregations: Définition des agrégations
            query: Filtre de requête (optionnel)
            
        Returns:
            Résultats des agrégations
        """
        try:
            url = urljoin(self.base_url, f'/{index_name}/_search')
            
            search_body = {
                'size': 0,
                'aggs': aggregations
            }
            
            if query:
                search_body['query'] = query
            
            response = self.session.post(url, json=search_body, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            
            return {
                'success': True,
                'aggregations': result.get('aggregations', {}),
                'took_ms': result.get('took', 0),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'agrégation dans {index_name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'index_name': index_name,
                'timestamp': datetime.now().isoformat()
            }
    
    def index_monitoring_data(self, device_id: int, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Indexe des données de monitoring.
        
        Args:
            device_id: ID de l'équipement
            metrics: Métriques collectées
            
        Returns:
            Résultat de l'indexation
        """
        index_name = f"monitoring-{datetime.now().strftime('%Y.%m')}"
        
        document = {
            '@timestamp': datetime.now().isoformat(),
            'device_id': device_id,
            'metrics': metrics,
            'type': 'monitoring_data'
        }
        
        return self.index_document(index_name, document)
    
    def index_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Indexe une alerte.
        
        Args:
            alert_data: Données de l'alerte
            
        Returns:
            Résultat de l'indexation
        """
        index_name = f"alerts-{datetime.now().strftime('%Y.%m')}"
        
        document = {
            '@timestamp': datetime.now().isoformat(),
            'type': 'alert',
            **alert_data
        }
        
        return self.index_document(index_name, document)
    
    def search_alerts(self, device_id: int = None, status: str = None, 
                     start_time: datetime = None, end_time: datetime = None) -> Dict[str, Any]:
        """
        Recherche des alertes avec filtres.
        
        Args:
            device_id: ID de l'équipement (optionnel)
            status: Statut des alertes (optionnel)
            start_time: Date de début (optionnel)
            end_time: Date de fin (optionnel)
            
        Returns:
            Alertes trouvées
        """
        index_pattern = "alerts-*"
        
        # Construire la requête
        must_clauses = [{'term': {'type': 'alert'}}]
        
        if device_id:
            must_clauses.append({'term': {'device_id': device_id}})
        
        if status:
            must_clauses.append({'term': {'status': status}})
        
        if start_time or end_time:
            time_range = {}
            if start_time:
                time_range['gte'] = start_time.isoformat()
            if end_time:
                time_range['lte'] = end_time.isoformat()
            
            must_clauses.append({
                'range': {
                    '@timestamp': time_range
                }
            })
        
        query = {
            'bool': {
                'must': must_clauses
            }
        }
        
        return self.search(index_pattern, query)
    
    def get_monitoring_stats(self, device_id: int, hours: int = 24) -> Dict[str, Any]:
        """
        Récupère les statistiques de monitoring pour un équipement.
        
        Args:
            device_id: ID de l'équipement
            hours: Nombre d'heures à analyser
            
        Returns:
            Statistiques de monitoring
        """
        index_pattern = "monitoring-*"
        
        # Période de temps
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        query = {
            'bool': {
                'must': [
                    {'term': {'device_id': device_id}},
                    {'term': {'type': 'monitoring_data'}},
                    {
                        'range': {
                            '@timestamp': {
                                'gte': start_time.isoformat(),
                                'lte': end_time.isoformat()
                            }
                        }
                    }
                ]
            }
        }
        
        aggregations = {
            'cpu_avg': {
                'avg': {
                    'field': 'metrics.cpu_usage'
                }
            },
            'memory_avg': {
                'avg': {
                    'field': 'metrics.memory_usage'
                }
            },
            'network_in_sum': {
                'sum': {
                    'field': 'metrics.network_in'
                }
            },
            'network_out_sum': {
                'sum': {
                    'field': 'metrics.network_out'
                }
            },
            'timeline': {
                'date_histogram': {
                    'field': '@timestamp',
                    'fixed_interval': '1h'
                },
                'aggs': {
                    'cpu_avg': {
                        'avg': {
                            'field': 'metrics.cpu_usage'
                        }
                    },
                    'memory_avg': {
                        'avg': {
                            'field': 'metrics.memory_usage'
                        }
                    }
                }
            }
        }
        
        return self.aggregate(index_pattern, aggregations, query)
    
    def create_monitoring_indices(self) -> Dict[str, Any]:
        """
        Crée les indices pour le monitoring.
        
        Returns:
            Résultat de la création des indices
        """
        results = {}
        
        # Mapping pour les données de monitoring
        monitoring_mapping = {
            'properties': {
                '@timestamp': {'type': 'date'},
                'device_id': {'type': 'integer'},
                'type': {'type': 'keyword'},
                'metrics': {
                    'properties': {
                        'cpu_usage': {'type': 'float'},
                        'memory_usage': {'type': 'float'},
                        'network_in': {'type': 'long'},
                        'network_out': {'type': 'long'},
                        'disk_usage': {'type': 'float'}
                    }
                }
            }
        }
        
        # Mapping pour les alertes
        alerts_mapping = {
            'properties': {
                '@timestamp': {'type': 'date'},
                'device_id': {'type': 'integer'},
                'type': {'type': 'keyword'},
                'severity': {'type': 'keyword'},
                'status': {'type': 'keyword'},
                'message': {'type': 'text'},
                'metric_name': {'type': 'keyword'},
                'threshold': {'type': 'float'},
                'current_value': {'type': 'float'}
            }
        }
        
        # Créer les indices
        current_month = datetime.now().strftime('%Y.%m')
        
        monitoring_index = f"monitoring-{current_month}"
        alerts_index = f"alerts-{current_month}"
        
        results['monitoring'] = self.create_index(monitoring_index, monitoring_mapping)
        results['alerts'] = self.create_index(alerts_index, alerts_mapping)
        
        return {
            'success': all(r['success'] for r in results.values()),
            'results': results,
            'timestamp': datetime.now().isoformat()
        } 