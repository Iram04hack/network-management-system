"""
Service d'intégration avec le Service Central de Topologie pour le monitoring.

Ce service fait le pont entre le module monitoring et le Service Central
de Topologie pour obtenir les données d'équipements et leurs configurations.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class TopologyIntegrationService:
    """
    Service d'intégration avec le Service Central de Topologie.
    
    Fournit une interface pour le module monitoring pour accéder
    aux données topologiques et de configuration des équipements.
    """
    
    def __init__(self):
        """Initialise le service d'intégration."""
        self.topology_service = None
        self._initialize_topology_service()
    
    def _initialize_topology_service(self):
        """Initialise la connexion au Service Central de Topologie."""
        try:
            from network_management.services.topology_service import ServiceCentralTopologie
            self.topology_service = ServiceCentralTopologie()
            logger.info("✅ Service Central de Topologie initialisé pour monitoring")
        except ImportError as e:
            logger.warning(f"❌ Service Central de Topologie non disponible: {e}")
            self.topology_service = None
    
    def get_monitorable_devices(self, device_filter: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Récupère la liste des équipements monitorables.
        
        Args:
            device_filter: Filtre optionnel pour les équipements
            
        Returns:
            Liste des équipements avec leurs configurations de monitoring
        """
        if not self.topology_service:
            return {
                'success': False,
                'error': 'Service Central de Topologie non disponible',
                'devices': []
            }
        
        try:
            # Obtenir les équipements pour le monitoring
            devices_result = self.topology_service.get_devices_for_module('monitoring', device_filter)
            
            if not devices_result['success']:
                return {
                    'success': False,
                    'error': devices_result.get('error', 'Erreur inconnue'),
                    'devices': []
                }
            
            # Enrichir avec les informations de monitoring
            enriched_devices = []
            for device in devices_result['devices']:
                enriched_device = self._enrich_device_for_monitoring(device)
                enriched_devices.append(enriched_device)
            
            logger.info(f"Récupéré {len(enriched_devices)} équipements monitorables")
            
            return {
                'success': True,
                'devices': enriched_devices,
                'total_count': len(enriched_devices),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des équipements monitorables: {e}")
            return {
                'success': False,
                'error': str(e),
                'devices': []
            }
    
    def _enrich_device_for_monitoring(self, device: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrichit un équipement avec les informations de monitoring.
        
        Args:
            device: Données de base de l'équipement
            
        Returns:
            Équipement enrichi avec les configurations de monitoring
        """
        device_type = device.get('device_type', 'unknown')
        
        # Configuration de base du monitoring
        monitoring_config = {
            'monitoring_enabled': device.get('is_active', True),
            'collection_interval': self._get_collection_interval(device_type),
            'priority': self._get_monitoring_priority(device_type),
            'snmp_config': {
                'community': device.get('snmp_community', 'public'),
                'version': '2c',
                'port': 161,
                'timeout': 5
            },
            'metrics_to_collect': self._get_default_metrics(device_type),
            'alerting_enabled': True,
            'dashboard_enabled': True
        }
        
        # Enrichir l'équipement
        enriched = {
            **device,
            'monitoring': monitoring_config,
            'last_monitoring_update': datetime.now().isoformat()
        }
        
        return enriched
    
    def _get_collection_interval(self, device_type: str) -> int:
        """
        Détermine l'intervalle de collecte selon le type d'équipement.
        
        Args:
            device_type: Type d'équipement
            
        Returns:
            Intervalle en secondes
        """
        intervals = {
            'router': 60,       # 1 minute
            'switch': 120,      # 2 minutes
            'firewall': 60,     # 1 minute
            'server': 180,      # 3 minutes
            'workstation': 300, # 5 minutes
            'printer': 600,     # 10 minutes
            'camera': 300,      # 5 minutes
            'access_point': 180 # 3 minutes
        }
        
        return intervals.get(device_type, 300)  # 5 minutes par défaut
    
    def _get_monitoring_priority(self, device_type: str) -> str:
        """
        Détermine la priorité de monitoring selon le type d'équipement.
        
        Args:
            device_type: Type d'équipement
            
        Returns:
            Priorité (critical, high, medium, low)
        """
        priorities = {
            'router': 'critical',
            'firewall': 'critical',
            'switch': 'high',
            'server': 'high',
            'access_point': 'medium',
            'workstation': 'low',
            'printer': 'low',
            'camera': 'low'
        }
        
        return priorities.get(device_type, 'medium')
    
    def _get_default_metrics(self, device_type: str) -> List[Dict[str, Any]]:
        """
        Retourne les métriques par défaut à collecter selon le type d'équipement.
        
        Args:
            device_type: Type d'équipement
            
        Returns:
            Liste des métriques à collecter
        """
        base_metrics = [
            {
                'name': 'system_uptime',
                'oid': '1.3.6.1.2.1.1.3.0',
                'type': 'snmp',
                'unit': 'seconds',
                'description': 'Temps de fonctionnement du système'
            },
            {
                'name': 'ping_response',
                'type': 'ping',
                'unit': 'ms',
                'description': 'Temps de réponse ping'
            }
        ]
        
        # Métriques spécifiques selon le type
        if device_type in ['router', 'switch', 'firewall']:
            # Équipements réseau
            base_metrics.extend([
                {
                    'name': 'cpu_utilization',
                    'oid': '1.3.6.1.4.1.9.9.109.1.1.1.1.7.1',  # Cisco CPU
                    'type': 'snmp',
                    'unit': 'percent',
                    'description': 'Utilisation CPU'
                },
                {
                    'name': 'memory_utilization',
                    'oid': '1.3.6.1.4.1.9.9.48.1.1.1.5.1',   # Cisco Memory
                    'type': 'snmp',
                    'unit': 'percent',
                    'description': 'Utilisation mémoire'
                },
                {
                    'name': 'interface_status',
                    'oid': '1.3.6.1.2.1.2.2.1.8',
                    'type': 'snmp',
                    'unit': 'status',
                    'description': 'Statut des interfaces'
                },
                {
                    'name': 'interface_traffic_in',
                    'oid': '1.3.6.1.2.1.2.2.1.10',
                    'type': 'snmp',
                    'unit': 'octets',
                    'description': 'Trafic entrant'
                },
                {
                    'name': 'interface_traffic_out',
                    'oid': '1.3.6.1.2.1.2.2.1.16',
                    'type': 'snmp',
                    'unit': 'octets',
                    'description': 'Trafic sortant'
                }
            ])
        
        elif device_type in ['server', 'workstation']:
            # Serveurs et postes de travail
            base_metrics.extend([
                {
                    'name': 'cpu_load',
                    'oid': '1.3.6.1.4.1.2021.10.1.3.1',
                    'type': 'snmp',
                    'unit': 'percent',
                    'description': 'Charge CPU'
                },
                {
                    'name': 'memory_usage',
                    'oid': '1.3.6.1.4.1.2021.4.5.0',
                    'type': 'snmp',
                    'unit': 'KB',
                    'description': 'Utilisation mémoire'
                },
                {
                    'name': 'disk_usage',
                    'oid': '1.3.6.1.4.1.2021.9.1.9.1',
                    'type': 'snmp',
                    'unit': 'percent',
                    'description': 'Utilisation disque'
                }
            ])
        
        return base_metrics
    
    def get_device_configuration(self, device_id: int) -> Dict[str, Any]:
        """
        Récupère la configuration complète d'un équipement pour le monitoring.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            Configuration complète de l'équipement
        """
        if not self.topology_service:
            return {
                'success': False,
                'error': 'Service Central de Topologie non disponible'
            }
        
        try:
            # Obtenir les détails de l'équipement
            device_result = self.topology_service.get_device_details(device_id)
            
            if not device_result['success']:
                return {
                    'success': False,
                    'error': device_result.get('error', 'Équipement non trouvé')
                }
            
            device = device_result['device']
            enriched_device = self._enrich_device_for_monitoring(device)
            
            return {
                'success': True,
                'device': enriched_device,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la configuration {device_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_monitoring_status(self, device_id: int, status_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour le statut de monitoring d'un équipement.
        
        Args:
            device_id: ID de l'équipement
            status_data: Données de statut de monitoring
            
        Returns:
            Résultat de la mise à jour
        """
        if not self.topology_service:
            return {
                'success': False,
                'error': 'Service Central de Topologie non disponible'
            }
        
        try:
            # Mettre à jour via le Service Central de Topologie
            update_result = self.topology_service.update_device_monitoring_status(device_id, status_data)
            
            return update_result
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du statut monitoring {device_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_topology_health(self) -> Dict[str, Any]:
        """
        Récupère l'état de santé de la topologie réseau.
        
        Returns:
            État de santé global de la topologie
        """
        if not self.topology_service:
            return {
                'success': False,
                'error': 'Service Central de Topologie non disponible',
                'health_status': 'unknown'
            }
        
        try:
            health_result = self.topology_service.get_health_status()
            
            if health_result['success']:
                return {
                    'success': True,
                    'topology_health': health_result,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': health_result.get('error', 'Erreur inconnue'),
                    'health_status': 'degraded'
                }
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'état de santé: {e}")
            return {
                'success': False,
                'error': str(e),
                'health_status': 'critical'
            }
    
    def is_topology_service_available(self) -> bool:
        """
        Vérifie si le Service Central de Topologie est disponible.
        
        Returns:
            True si disponible, False sinon
        """
        return self.topology_service is not None
    
    def sync_with_topology(self) -> Dict[str, Any]:
        """
        Synchronise le module monitoring avec la topologie.
        
        Returns:
            Résultat de la synchronisation
        """
        if not self.topology_service:
            return {
                'success': False,
                'error': 'Service Central de Topologie non disponible'
            }
        
        try:
            sync_start = datetime.now()
            
            # Obtenir tous les équipements
            devices_result = self.get_monitorable_devices()
            
            if not devices_result['success']:
                return {
                    'success': False,
                    'error': devices_result['error']
                }
            
            devices = devices_result['devices']
            sync_results = {
                'total_devices': len(devices),
                'synchronized_devices': 0,
                'failed_devices': 0,
                'new_devices': 0,
                'updated_devices': 0,
                'errors': []
            }
            
            # Traiter chaque équipement
            for device in devices:
                try:
                    # Logique de synchronisation spécifique
                    device_sync = self._sync_device_monitoring(device)
                    
                    if device_sync['success']:
                        sync_results['synchronized_devices'] += 1
                        if device_sync.get('is_new', False):
                            sync_results['new_devices'] += 1
                        else:
                            sync_results['updated_devices'] += 1
                    else:
                        sync_results['failed_devices'] += 1
                        sync_results['errors'].append(f"Équipement {device['id']}: {device_sync.get('error')}")
                        
                except Exception as e:
                    sync_results['failed_devices'] += 1
                    sync_results['errors'].append(f"Équipement {device['id']}: {str(e)}")
            
            sync_duration = (datetime.now() - sync_start).total_seconds()
            
            return {
                'success': True,
                'sync_duration_seconds': sync_duration,
                'results': sync_results,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation avec la topologie: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _sync_device_monitoring(self, device: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synchronise le monitoring pour un équipement spécifique.
        
        Args:
            device: Données de l'équipement
            
        Returns:
            Résultat de la synchronisation
        """
        try:
            device_id = device['id']
            
            # Ici, on implémenterait la logique de synchronisation
            # avec les modèles de monitoring locaux
            
            return {
                'success': True,
                'device_id': device_id,
                'is_new': False,  # À déterminer selon la logique métier
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }