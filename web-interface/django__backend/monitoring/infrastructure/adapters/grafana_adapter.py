"""
Adaptateur pour l'intégration avec Grafana.

Ce module fournit l'interface pour interagir avec Grafana
et gérer les tableaux de bord et panneaux.
"""

import logging
import requests
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class GrafanaAdapter:
    """
    Adaptateur pour l'intégration avec Grafana.
    
    Permet de gérer les tableaux de bord, créer des panneaux
    et interagir avec l'API Grafana.
    """
    
    def __init__(self, base_url: str = "http://localhost:3000", api_key: str = None, username: str = "admin", password: str = "admin"):
        """
        Initialise l'adaptateur Grafana.
        
        Args:
            base_url: URL de base de Grafana
            api_key: Clé API Grafana (optionnel)
            username: Nom d'utilisateur (si pas de clé API)
            password: Mot de passe (si pas de clé API)
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})
        else:
            self.session.auth = (username, password)
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Teste la connexion à Grafana.
        
        Returns:
            Résultat du test de connexion
        """
        try:
            url = urljoin(self.base_url, '/api/health')
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            return {
                'success': True,
                'status': response.json(),
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
    
    def get_dashboards(self) -> Dict[str, Any]:
        """
        Récupère la liste des tableaux de bord.
        
        Returns:
            Liste des tableaux de bord
        """
        try:
            url = urljoin(self.base_url, '/api/search?type=dash-db')
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            dashboards = response.json()
            
            return {
                'success': True,
                'dashboards': dashboards,
                'count': len(dashboards),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des tableaux de bord: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_dashboard(self, uid: str) -> Dict[str, Any]:
        """
        Récupère un tableau de bord par UID.
        
        Args:
            uid: UID du tableau de bord
            
        Returns:
            Détails du tableau de bord
        """
        try:
            url = urljoin(self.base_url, f'/api/dashboards/uid/{uid}')
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            dashboard_data = response.json()
            
            return {
                'success': True,
                'dashboard': dashboard_data,
                'uid': uid,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du tableau de bord {uid}: {e}")
            return {
                'success': False,
                'error': str(e),
                'uid': uid
            }
    
    def create_dashboard(self, dashboard_json: Dict[str, Any], folder_id: int = 0) -> Dict[str, Any]:
        """
        Crée un nouveau tableau de bord.
        
        Args:
            dashboard_json: Configuration JSON du tableau de bord
            folder_id: ID du dossier (0 = dossier racine)
            
        Returns:
            Résultat de la création
        """
        try:
            url = urljoin(self.base_url, '/api/dashboards/db')
            
            payload = {
                'dashboard': dashboard_json,
                'folderId': folder_id,
                'overwrite': False
            }
            
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            return {
                'success': True,
                'result': result,
                'dashboard_id': result.get('id'),
                'uid': result.get('uid'),
                'url': result.get('url'),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du tableau de bord: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_dashboard(self, dashboard_json: Dict[str, Any], folder_id: int = 0) -> Dict[str, Any]:
        """
        Met à jour un tableau de bord existant.
        
        Args:
            dashboard_json: Configuration JSON du tableau de bord
            folder_id: ID du dossier
            
        Returns:
            Résultat de la mise à jour
        """
        try:
            url = urljoin(self.base_url, '/api/dashboards/db')
            
            payload = {
                'dashboard': dashboard_json,
                'folderId': folder_id,
                'overwrite': True
            }
            
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            return {
                'success': True,
                'result': result,
                'dashboard_id': result.get('id'),
                'uid': result.get('uid'),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du tableau de bord: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_dashboard(self, uid: str) -> Dict[str, Any]:
        """
        Supprime un tableau de bord.
        
        Args:
            uid: UID du tableau de bord
            
        Returns:
            Résultat de la suppression
        """
        try:
            url = urljoin(self.base_url, f'/api/dashboards/uid/{uid}')
            response = self.session.delete(url, timeout=30)
            response.raise_for_status()
            
            return {
                'success': True,
                'uid': uid,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du tableau de bord {uid}: {e}")
            return {
                'success': False,
                'error': str(e),
                'uid': uid
            }
    
    def create_monitoring_dashboard(self, device_name: str, device_id: int) -> Dict[str, Any]:
        """
        Crée un tableau de bord de monitoring pour un équipement.
        
        Args:
            device_name: Nom de l'équipement
            device_id: ID de l'équipement
            
        Returns:
            Résultat de la création
        """
        dashboard_json = {
            "id": None,
            "title": f"Monitoring - {device_name}",
            "tags": ["monitoring", "nms", f"device-{device_id}"],
            "style": "dark",
            "timezone": "browser",
            "refresh": "30s",
            "time": {
                "from": "now-1h",
                "to": "now"
            },
            "panels": [
                {
                    "id": 1,
                    "title": "CPU Usage",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": f"cpu_usage{{device_id=\"{device_id}\"}}",
                            "refId": "A"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {
                                "mode": "thresholds"
                            },
                            "thresholds": {
                                "steps": [
                                    {"color": "green", "value": None},
                                    {"color": "yellow", "value": 60},
                                    {"color": "red", "value": 80}
                                ]
                            },
                            "unit": "percent"
                        }
                    },
                    "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0}
                },
                {
                    "id": 2,
                    "title": "Memory Usage",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": f"memory_usage{{device_id=\"{device_id}\"}}",
                            "refId": "A"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {
                                "mode": "thresholds"
                            },
                            "thresholds": {
                                "steps": [
                                    {"color": "green", "value": None},
                                    {"color": "yellow", "value": 70},
                                    {"color": "red", "value": 85}
                                ]
                            },
                            "unit": "percent"
                        }
                    },
                    "gridPos": {"h": 8, "w": 6, "x": 6, "y": 0}
                },
                {
                    "id": 3,
                    "title": "Network Traffic",
                    "type": "timeseries",
                    "targets": [
                        {
                            "expr": f"network_in{{device_id=\"{device_id}\"}}",
                            "refId": "A",
                            "legendFormat": "In"
                        },
                        {
                            "expr": f"network_out{{device_id=\"{device_id}\"}}",
                            "refId": "B",
                            "legendFormat": "Out"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "unit": "bps"
                        }
                    },
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
                },
                {
                    "id": 4,
                    "title": "Active Alerts",
                    "type": "table",
                    "targets": [
                        {
                            "expr": f"alerts{{device_id=\"{device_id}\",status=\"active\"}}",
                            "refId": "A"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 24, "x": 0, "y": 8}
                }
            ]
        }
        
        return self.create_dashboard(dashboard_json)
    
    def get_datasources(self) -> Dict[str, Any]:
        """
        Récupère la liste des sources de données.
        
        Returns:
            Liste des sources de données
        """
        try:
            url = urljoin(self.base_url, '/api/datasources')
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            datasources = response.json()
            
            return {
                'success': True,
                'datasources': datasources,
                'count': len(datasources),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des sources de données: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_prometheus_datasource(self, prometheus_url: str = "http://localhost:9090") -> Dict[str, Any]:
        """
        Crée une source de données Prometheus.
        
        Args:
            prometheus_url: URL de Prometheus
            
        Returns:
            Résultat de la création
        """
        try:
            url = urljoin(self.base_url, '/api/datasources')
            
            datasource_config = {
                "name": "Prometheus",
                "type": "prometheus",
                "url": prometheus_url,
                "access": "proxy",
                "isDefault": True,
                "basicAuth": False
            }
            
            response = self.session.post(url, json=datasource_config, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            return {
                'success': True,
                'result': result,
                'datasource_id': result.get('id'),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de la source de données Prometheus: {e}")
            return {
                'success': False,
                'error': str(e)
            } 