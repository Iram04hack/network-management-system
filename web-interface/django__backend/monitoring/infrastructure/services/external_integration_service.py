"""
Service d'intégration des services externes.

Ce service orchestre l'interaction avec tous les services externes
(Prometheus, Grafana, Elasticsearch, SNMP) pour le monitoring.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from django.conf import settings

from ..adapters.prometheus_adapter import PrometheusAdapter
from ..adapters.grafana_adapter import GrafanaAdapter
from ..adapters.elasticsearch_adapter import ElasticsearchAdapter
from ..adapters.snmp_adapter import SNMPAdapter

# Import du Service Central de Topologie
try:
    from network_management.services.topology_service import ServiceCentralTopologie
except ImportError:
    ServiceCentralTopologie = None

logger = logging.getLogger(__name__)


class ExternalIntegrationService:
    """
    Service d'intégration des services externes.
    
    Centralise l'interaction avec Prometheus, Grafana, Elasticsearch et SNMP
    pour fournir une interface unifiée de monitoring.
    """
    
    def __init__(self):
        """Initialise le service avec tous les adaptateurs."""
        # Configuration par défaut
        self.prometheus_url = getattr(settings, 'PROMETHEUS_URL', 'http://localhost:9090')
        self.grafana_url = getattr(settings, 'GRAFANA_URL', 'http://localhost:3000')
        self.elasticsearch_url = getattr(settings, 'ELASTICSEARCH_URL', 'http://localhost:9200')
        
        # Initialisation des adaptateurs
        self.prometheus = PrometheusAdapter(self.prometheus_url)
        self.grafana = GrafanaAdapter(self.grafana_url)
        self.elasticsearch = ElasticsearchAdapter(self.elasticsearch_url)
        self.snmp = SNMPAdapter()
        
        # Service Central de Topologie
        self.topology_service = ServiceCentralTopologie() if ServiceCentralTopologie else None
        
        logger.info(f"Service d'intégration externe initialisé - Topologie: {'✅' if self.topology_service else '❌'}")
    
    def test_all_connections(self) -> Dict[str, Any]:
        """
        Teste la connectivité avec tous les services externes.
        
        Returns:
            État de tous les services
        """
        results = {
            'timestamp': datetime.now().isoformat(),
            'services': {},
            'overall_status': 'healthy'
        }
        
        # Test Prometheus
        prometheus_test = self.prometheus.test_connection()
        results['services']['prometheus'] = {
            'name': 'Prometheus',
            'status': 'healthy' if prometheus_test['success'] else 'unhealthy',
            'url': self.prometheus_url,
            'details': prometheus_test
        }
        
        # Test Grafana
        grafana_test = self.grafana.test_connection()
        results['services']['grafana'] = {
            'name': 'Grafana',
            'status': 'healthy' if grafana_test['success'] else 'unhealthy',
            'url': self.grafana_url,
            'details': grafana_test
        }
        
        # Test Elasticsearch
        elasticsearch_test = self.elasticsearch.test_connection()
        results['services']['elasticsearch'] = {
            'name': 'Elasticsearch',
            'status': 'healthy' if elasticsearch_test['success'] else 'unhealthy',
            'url': self.elasticsearch_url,
            'details': elasticsearch_test
        }
        
        # Test SNMP
        snmp_available = self.snmp.is_snmp_available()
        results['services']['snmp'] = {
            'name': 'SNMP Tools',
            'status': 'healthy' if snmp_available else 'unhealthy',
            'details': {'tools_available': snmp_available}
        }
        
        # Déterminer le statut global
        unhealthy_services = [
            name for name, service in results['services'].items()
            if service['status'] == 'unhealthy'
        ]
        
        if unhealthy_services:
            if len(unhealthy_services) == len(results['services']):
                results['overall_status'] = 'critical'
            else:
                results['overall_status'] = 'degraded'
        
        results['unhealthy_services'] = unhealthy_services
        
        return results
    
    def collect_device_metrics(self, device_ip: str, device_id: int, 
                             community: str = 'public') -> Dict[str, Any]:
        """
        Collecte des métriques complètes pour un équipement.
        
        Args:
            device_ip: Adresse IP de l'équipement
            device_id: ID de l'équipement
            community: Communauté SNMP
            
        Returns:
            Métriques collectées et stockées
        """
        collection_result = {
            'device_id': device_id,
            'device_ip': device_ip,
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'metrics': {},
            'errors': []
        }
        
        try:
            # Collecte SNMP
            snmp_result = self.snmp.collect_comprehensive_metrics(device_ip, community)
            
            if snmp_result['success']:
                collection_result['metrics']['snmp'] = snmp_result
                
                # Extraire les métriques essentielles
                essential_metrics = self._extract_essential_metrics(snmp_result)
                
                # Stocker dans Elasticsearch
                elasticsearch_result = self.elasticsearch.index_monitoring_data(
                    device_id, essential_metrics
                )
                
                if elasticsearch_result['success']:
                    collection_result['elasticsearch_indexed'] = True
                else:
                    collection_result['errors'].append(f"Elasticsearch indexing failed: {elasticsearch_result.get('error')}")
                
                # Collecte Prometheus (si disponible)
                prometheus_result = self.prometheus.collect_system_metrics(device_ip)
                if prometheus_result['success']:
                    collection_result['metrics']['prometheus'] = prometheus_result
                
                collection_result['success'] = True
                
            else:
                collection_result['errors'].append(f"SNMP collection failed: {snmp_result.get('error')}")
                
        except Exception as e:
            logger.error(f"Erreur lors de la collecte pour l'équipement {device_id}: {e}")
            collection_result['errors'].append(str(e))
        
        return collection_result
    
    def _extract_essential_metrics(self, snmp_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrait les métriques essentielles des données SNMP.
        
        Args:
            snmp_data: Données SNMP brutes
            
        Returns:
            Métriques essentielles formatées
        """
        metrics = {
            'collection_timestamp': datetime.now().isoformat(),
            'source': 'snmp'
        }
        
        # Informations système
        if 'system_info' in snmp_data:
            metrics['system'] = snmp_data['system_info']
        
        # Métriques des interfaces
        if 'interfaces' in snmp_data:
            interfaces = snmp_data['interfaces']
            
            # Calculer les totaux de trafic
            total_in_octets = 0
            total_out_octets = 0
            active_interfaces = 0
            
            for interface_name, interface_data in interfaces.items():
                if interface_data.get('ifOperStatus') == '1':  # Interface up
                    active_interfaces += 1
                    
                    try:
                        in_octets = int(interface_data.get('ifInOctets', 0))
                        out_octets = int(interface_data.get('ifOutOctets', 0))
                        total_in_octets += in_octets
                        total_out_octets += out_octets
                    except (ValueError, TypeError):
                        pass
            
            metrics['network'] = {
                'total_in_octets': total_in_octets,
                'total_out_octets': total_out_octets,
                'active_interfaces': active_interfaces,
                'total_interfaces': len(interfaces)
            }
        
        # Métriques de connectivité
        if 'connectivity' in snmp_data:
            metrics['connectivity'] = {
                'response_time_seconds': snmp_data['connectivity'].get('response_time_seconds', 0),
                'reachable': snmp_data['connectivity'].get('success', False)
            }
        
        return metrics
    
    def create_device_dashboard(self, device_id: int, device_name: str, 
                              device_ip: str) -> Dict[str, Any]:
        """
        Crée un tableau de bord Grafana pour un équipement.
        
        Args:
            device_id: ID de l'équipement
            device_name: Nom de l'équipement
            device_ip: Adresse IP de l'équipement
            
        Returns:
            Résultat de la création du tableau de bord
        """
        try:
            # Créer le tableau de bord
            dashboard_result = self.grafana.create_monitoring_dashboard(device_name, device_id)
            
            if dashboard_result['success']:
                return {
                    'success': True,
                    'dashboard_id': dashboard_result.get('dashboard_id'),
                    'dashboard_uid': dashboard_result.get('uid'),
                    'dashboard_url': dashboard_result.get('url'),
                    'device_id': device_id,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': dashboard_result.get('error'),
                    'device_id': device_id,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Erreur lors de la création du tableau de bord pour {device_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'device_id': device_id,
                'timestamp': datetime.now().isoformat()
            }
    
    def search_device_alerts(self, device_id: int, hours: int = 24) -> Dict[str, Any]:
        """
        Recherche les alertes pour un équipement.
        
        Args:
            device_id: ID de l'équipement
            hours: Nombre d'heures à rechercher
            
        Returns:
            Alertes trouvées
        """
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            # Construire la requête Elasticsearch
            query = {
                'bool': {
                    'must': [
                        {'term': {'device_id': device_id}},
                        {'term': {'type': 'alert'}},
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
            
            search_result = self.elasticsearch.search('alerts-*', query)
            
            if search_result['success']:
                alerts = search_result['documents']
                
                # Analyser les alertes
                alert_summary = {
                    'total_alerts': len(alerts),
                    'active_alerts': len([a for a in alerts if a.get('status') == 'active']),
                    'resolved_alerts': len([a for a in alerts if a.get('status') == 'resolved']),
                    'critical_alerts': len([a for a in alerts if a.get('severity') == 'critical']),
                    'warning_alerts': len([a for a in alerts if a.get('severity') == 'warning'])
                }
                
                return {
                    'success': True,
                    'device_id': device_id,
                    'alerts': alerts,
                    'summary': alert_summary,
                    'period_hours': hours,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': search_result.get('error'),
                    'device_id': device_id,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Erreur lors de la recherche d'alertes pour {device_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'device_id': device_id,
                'timestamp': datetime.now().isoformat()
            }
    
    def get_infrastructure_health(self) -> Dict[str, Any]:
        """
        Évalue la santé globale de l'infrastructure de monitoring.
        
        Returns:
            État de santé de l'infrastructure
        """
        health_data = {
            'timestamp': datetime.now().isoformat(),
            'overall_health': 'healthy',
            'services': {},
            'recommendations': []
        }
        
        # Test de connectivité
        connection_tests = self.test_all_connections()
        health_data['services'] = connection_tests['services']
        
        # Évaluation des services
        critical_services = ['prometheus', 'elasticsearch']
        optional_services = ['grafana', 'snmp']
        
        critical_down = [
            name for name in critical_services
            if health_data['services'].get(name, {}).get('status') == 'unhealthy'
        ]
        
        optional_down = [
            name for name in optional_services
            if health_data['services'].get(name, {}).get('status') == 'unhealthy'
        ]
        
        # Déterminer la santé globale
        if critical_down:
            health_data['overall_health'] = 'critical'
            health_data['recommendations'].extend([
                f"Service critique {service} est indisponible - intervention immédiate requise"
                for service in critical_down
            ])
        elif optional_down:
            health_data['overall_health'] = 'degraded'
            health_data['recommendations'].extend([
                f"Service optionnel {service} est indisponible - fonctionnalités limitées"
                for service in optional_down
            ])
        
        # Ajout de recommandations générales
        if health_data['overall_health'] == 'healthy':
            health_data['recommendations'].append("Tous les services fonctionnent correctement")
        
        health_data['critical_services_down'] = critical_down
        health_data['optional_services_down'] = optional_down
        
        return health_data
    
    def get_devices_from_topology(self, device_filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Récupère les équipements depuis le Service Central de Topologie.
        
        Args:
            device_filter: Filtre optionnel pour les équipements
            
        Returns:
            Liste des équipements avec leurs configurations
        """
        if not self.topology_service:
            logger.warning("Service Central de Topologie non disponible - Utilisation de données par défaut")
            return []
            
        try:
            # Obtenir les équipements pour le module monitoring
            devices_result = self.topology_service.get_devices_for_module('monitoring', device_filter)
            
            if devices_result['success']:
                devices = devices_result['devices']
                logger.info(f"Récupéré {len(devices)} équipements depuis le Service Central de Topologie")
                
                # Convertir au format attendu par le monitoring
                formatted_devices = []
                for device in devices:
                    formatted_device = {
                        'id': device.get('id'),
                        'name': device.get('name'),
                        'ip_address': device.get('ip_address'),
                        'device_type': device.get('device_type'),
                        'snmp_community': device.get('snmp_community', 'public'),
                        'is_active': device.get('is_active', True),
                        'monitoring_enabled': device.get('monitoring_enabled', True),
                        'critical_priority': device.get('device_type') in ['router', 'switch', 'firewall']
                    }
                    formatted_devices.append(formatted_device)
                    
                return formatted_devices
            else:
                logger.error(f"Erreur lors de la récupération des équipements: {devices_result.get('error')}")
                return []
                
        except Exception as e:
            logger.error(f"Erreur lors de l'accès au Service Central de Topologie: {e}")
            return []
    
    def collect_all_network_metrics(self, device_filter: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Collecte les métriques pour tous les équipements du réseau.
        
        Args:
            device_filter: Filtre optionnel pour les équipements
            
        Returns:
            Résultats de la collecte globale
        """
        collection_start = datetime.now()
        
        # Récupérer les équipements depuis la topologie
        devices = self.get_devices_from_topology(device_filter)
        
        if not devices:
            return {
                'success': False,
                'error': 'Aucun équipement trouvé ou Service Central de Topologie indisponible',
                'timestamp': collection_start.isoformat()
            }
        
        # Filtrer les équipements actifs et monitorables
        active_devices = [
            device for device in devices 
            if device.get('is_active', True) and device.get('monitoring_enabled', True)
        ]
        
        logger.info(f"Collecte de métriques pour {len(active_devices)} équipements actifs")
        
        # Collecte avec priorités (critiques en premier)
        critical_devices = [d for d in active_devices if d.get('critical_priority', False)]
        normal_devices = [d for d in active_devices if not d.get('critical_priority', False)]
        
        # Collecter pour les équipements critiques d'abord
        critical_results = self.bulk_collect_metrics(critical_devices)
        normal_results = self.bulk_collect_metrics(normal_devices)
        
        # Combiner les résultats
        total_results = {
            'timestamp': collection_start.isoformat(),
            'collection_duration_seconds': (datetime.now() - collection_start).total_seconds(),
            'total_devices': len(active_devices),
            'critical_devices': len(critical_devices),
            'normal_devices': len(normal_devices),
            'successful_collections': critical_results['successful_collections'] + normal_results['successful_collections'],
            'failed_collections': critical_results['failed_collections'] + normal_results['failed_collections'],
            'device_results': {**critical_results['device_results'], **normal_results['device_results']},
            'errors': critical_results['errors'] + normal_results['errors'],
            'topology_integration': True,
            'service_status': self.get_infrastructure_health()
        }
        
        total_results['success_rate'] = (
            total_results['successful_collections'] / total_results['total_devices'] * 100
            if total_results['total_devices'] > 0 else 0
        )
        
        # Notifier le Service Central de Topologie des résultats
        if self.topology_service:
            try:
                self.topology_service.update_monitoring_status({
                    'timestamp': collection_start.isoformat(),
                    'devices_monitored': total_results['total_devices'],
                    'success_rate': total_results['success_rate'],
                    'failed_devices': [device_id for device_id, result in total_results['device_results'].items() if not result['success']]
                })
            except Exception as e:
                logger.warning(f"Impossible de notifier le Service Central de Topologie: {e}")
        
        return total_results

    def bulk_collect_metrics(self, devices: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Collecte des métriques pour plusieurs équipements en parallèle.
        
        Args:
            devices: Liste des équipements à surveiller
            
        Returns:
            Résultats de la collecte en bulk
        """
        results = {
            'timestamp': datetime.now().isoformat(),
            'total_devices': len(devices),
            'successful_collections': 0,
            'failed_collections': 0,
            'device_results': {},
            'errors': []
        }
        
        for device in devices:
            device_id = device['id']
            device_ip = device['ip_address']
            community = device.get('snmp_community', 'public')
            
            try:
                collection_result = self.collect_device_metrics(device_ip, device_id, community)
                
                results['device_results'][device_id] = collection_result
                
                if collection_result['success']:
                    results['successful_collections'] += 1
                else:
                    results['failed_collections'] += 1
                    
            except Exception as e:
                error_msg = f"Erreur pour l'équipement {device_id}: {str(e)}"
                results['errors'].append(error_msg)
                results['failed_collections'] += 1
                logger.error(error_msg)
        
        results['success_rate'] = (
            results['successful_collections'] / results['total_devices'] * 100
            if results['total_devices'] > 0 else 0
        )
        
        return results 