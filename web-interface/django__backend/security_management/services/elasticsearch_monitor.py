"""
Service de monitoring Elasticsearch pour les alertes Suricata.

Ce service surveille Elasticsearch pour détecter automatiquement
les nouvelles alertes de sécurité et déclencher les rapports.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from django.conf import settings
from django.utils import timezone
from elasticsearch import Elasticsearch, exceptions

logger = logging.getLogger(__name__)


class ElasticsearchMonitor:
    """
    Moniteur Elasticsearch pour les alertes de sécurité.
    
    Ce service se connecte à Elasticsearch pour récupérer les alertes
    Suricata en temps réel et déclencher les actions automatiques.
    """
    
    def __init__(self):
        """Initialise la connexion Elasticsearch."""
        self.es_url = getattr(settings, 'ELASTICSEARCH_URL', 'http://localhost:9200')
        self.suricata_index_pattern = 'suricata-*'
        self.logstash_index_pattern = 'logstash-*'
        
        try:
            self.es_client = Elasticsearch([self.es_url])
            # Test de connexion
            if self.es_client.ping():
                logger.info(f"✅ Connexion Elasticsearch établie: {self.es_url}")
            else:
                logger.error(f"❌ Impossible de se connecter à Elasticsearch: {self.es_url}")
                self.es_client = None
        except Exception as e:
            logger.error(f"❌ Erreur initialisation Elasticsearch: {e}")
            self.es_client = None
    
    def get_new_alerts_since(self, since_time: datetime) -> List[Dict[str, Any]]:
        """
        Récupère les nouvelles alertes depuis un timestamp donné.
        
        Args:
            since_time: Timestamp depuis lequel récupérer les alertes
            
        Returns:
            Liste des nouvelles alertes
        """
        if not self.es_client:
            logger.warning("⚠️ Client Elasticsearch non disponible")
            return []
        
        try:
            # Requête Elasticsearch pour les nouvelles alertes
            query = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "range": {
                                    "@timestamp": {
                                        "gte": since_time.isoformat(),
                                        "lte": timezone.now().isoformat()
                                    }
                                }
                            }
                        ],
                        "filter": [
                            {"exists": {"field": "alert"}},
                            {"term": {"event_type": "alert"}}
                        ]
                    }
                },
                "sort": [
                    {"@timestamp": {"order": "desc"}}
                ],
                "size": 1000  # Maximum 1000 alertes par scan
            }
            
            # Rechercher dans les indices Suricata
            response = self.es_client.search(
                index=self.suricata_index_pattern,
                body=query
            )
            
            alerts = []
            for hit in response['hits']['hits']:
                source = hit['_source']
                
                # Enrichir l'alerte avec des métadonnées
                alert_data = {
                    '_id': hit['_id'],
                    '_index': hit['_index'],
                    '@timestamp': source.get('@timestamp'),
                    'event_type': source.get('event_type', 'alert'),
                    'alert': source.get('alert', {}),
                    'src_ip': source.get('src_ip', ''),
                    'dest_ip': source.get('dest_ip', ''),
                    'src_port': source.get('src_port', 0),
                    'dest_port': source.get('dest_port', 0),
                    'proto': source.get('proto', ''),
                    'flow': source.get('flow', {}),
                    'packet_info': source.get('packet_info', {}),
                    'host': source.get('host', {}),
                    'raw_source': source
                }
                
                # Déterminer la sévérité
                alert_info = source.get('alert', {})
                severity_num = alert_info.get('severity', 3)
                
                # Mapping sévérité numérique vers texte
                severity_map = {
                    1: 'critical',
                    2: 'high', 
                    3: 'medium',
                    4: 'low'
                }
                alert_data['severity'] = severity_map.get(severity_num, 'medium')
                
                # Enrichir avec signature et catégorie
                alert_data['signature'] = alert_info.get('signature', 'Unknown Alert')
                alert_data['category'] = alert_info.get('category', 'Unknown')
                alert_data['gid'] = alert_info.get('gid', 0)
                alert_data['sid'] = alert_info.get('sid', 0)
                alert_data['rev'] = alert_info.get('rev', 0)
                
                # Identifier les alertes critiques
                critical_signatures = [
                    'malware', 'trojan', 'exploit', 'shellcode', 
                    'backdoor', 'botnet', 'ransomware', 'apt'
                ]
                
                if any(keyword in alert_data['signature'].lower() for keyword in critical_signatures):
                    alert_data['severity'] = 'critical'
                
                alerts.append(alert_data)
            
            logger.info(f"📥 {len(alerts)} nouvelles alertes récupérées depuis {since_time}")
            return alerts
            
        except exceptions.NotFoundError:
            logger.warning(f"⚠️ Index Suricata non trouvé: {self.suricata_index_pattern}")
            return []
        except Exception as e:
            logger.error(f"❌ Erreur récupération alertes Elasticsearch: {e}")
            return []
    
    def get_alert_statistics(self, time_range_hours: int = 24) -> Dict[str, Any]:
        """
        Récupère les statistiques des alertes sur une période donnée.
        
        Args:
            time_range_hours: Période en heures pour les statistiques
            
        Returns:
            Dictionnaire avec les statistiques
        """
        if not self.es_client:
            return {"error": "Elasticsearch non disponible"}
        
        try:
            since_time = timezone.now() - timedelta(hours=time_range_hours)
            
            query = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "range": {
                                    "@timestamp": {
                                        "gte": since_time.isoformat()
                                    }
                                }
                            }
                        ],
                        "filter": [
                            {"exists": {"field": "alert"}},
                            {"term": {"event_type": "alert"}}
                        ]
                    }
                },
                "aggs": {
                    "severity_breakdown": {
                        "terms": {
                            "field": "alert.severity",
                            "size": 10
                        }
                    },
                    "top_signatures": {
                        "terms": {
                            "field": "alert.signature.keyword",
                            "size": 10
                        }
                    },
                    "source_ips": {
                        "terms": {
                            "field": "src_ip.keyword",
                            "size": 10
                        }
                    },
                    "alerts_over_time": {
                        "date_histogram": {
                            "field": "@timestamp",
                            "calendar_interval": "1h"
                        }
                    }
                },
                "size": 0  # Seulement les agrégations
            }
            
            response = self.es_client.search(
                index=self.suricata_index_pattern,
                body=query
            )
            
            stats = {
                "time_range_hours": time_range_hours,
                "total_alerts": response['hits']['total']['value'],
                "severity_breakdown": {},
                "top_signatures": [],
                "top_source_ips": [],
                "alerts_timeline": []
            }
            
            # Traiter les agrégations
            aggs = response.get('aggregations', {})
            
            # Répartition par sévérité
            for bucket in aggs.get('severity_breakdown', {}).get('buckets', []):
                severity_map = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low'}
                severity = severity_map.get(bucket['key'], f"severity_{bucket['key']}")
                stats['severity_breakdown'][severity] = bucket['doc_count']
            
            # Top signatures
            for bucket in aggs.get('top_signatures', {}).get('buckets', []):
                stats['top_signatures'].append({
                    "signature": bucket['key'],
                    "count": bucket['doc_count']
                })
            
            # Top IPs sources
            for bucket in aggs.get('source_ips', {}).get('buckets', []):
                stats['top_source_ips'].append({
                    "ip": bucket['key'],
                    "count": bucket['doc_count']
                })
            
            # Timeline des alertes
            for bucket in aggs.get('alerts_over_time', {}).get('buckets', []):
                stats['alerts_timeline'].append({
                    "timestamp": bucket['key_as_string'],
                    "count": bucket['doc_count']
                })
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération statistiques: {e}")
            return {"error": str(e)}
    
    def get_critical_alerts_last_hour(self) -> List[Dict[str, Any]]:
        """
        Récupère les alertes critiques de la dernière heure.
        
        Returns:
            Liste des alertes critiques récentes
        """
        since_time = timezone.now() - timedelta(hours=1)
        
        all_alerts = self.get_new_alerts_since(since_time)
        critical_alerts = [
            alert for alert in all_alerts 
            if alert.get('severity') in ['critical', 'high']
        ]
        
        return critical_alerts
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Teste la connexion Elasticsearch.
        
        Returns:
            Résultat du test de connexion
        """
        if not self.es_client:
            return {
                "connected": False,
                "error": "Client Elasticsearch non initialisé"
            }
        
        try:
            # Test ping
            if not self.es_client.ping():
                return {
                    "connected": False,
                    "error": "Ping Elasticsearch échoué"
                }
            
            # Test info cluster
            cluster_info = self.es_client.info()
            
            # Test existence indices Suricata
            indices = self.es_client.indices.get_alias(index=self.suricata_index_pattern)
            
            return {
                "connected": True,
                "cluster_name": cluster_info.get('cluster_name'),
                "version": cluster_info.get('version', {}).get('number'),
                "suricata_indices": list(indices.keys()) if indices else [],
                "indices_count": len(indices) if indices else 0
            }
            
        except Exception as e:
            return {
                "connected": False,
                "error": str(e)
            }