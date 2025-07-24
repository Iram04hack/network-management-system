"""
Adaptateur SNMP pour la collecte de métriques depuis les équipements réseau.

Ce module fournit l'interface pour interagir avec les équipements
via SNMP et collecter des métriques en temps réel.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import subprocess
import json

logger = logging.getLogger(__name__)


class SNMPAdapter:
    """
    Adaptateur pour la collecte SNMP.
    
    Utilise les outils système snmpget et snmpwalk pour
    la collecte de métriques depuis les équipements réseau.
    """
    
    # OIDs standards pour les métriques communes
    SYSTEM_OIDS = {
        'sysDescr': '1.3.6.1.2.1.1.1.0',
        'sysUpTime': '1.3.6.1.2.1.1.3.0',
        'sysContact': '1.3.6.1.2.1.1.4.0',
        'sysName': '1.3.6.1.2.1.1.5.0',
        'sysLocation': '1.3.6.1.2.1.1.6.0'
    }
    
    INTERFACE_OIDS = {
        'ifNumber': '1.3.6.1.2.1.2.1.0',
        'ifDescr': '1.3.6.1.2.1.2.2.1.2',
        'ifOperStatus': '1.3.6.1.2.1.2.2.1.8',
        'ifInOctets': '1.3.6.1.2.1.2.2.1.10',
        'ifOutOctets': '1.3.6.1.2.1.2.2.1.16'
    }
    
    def __init__(self, timeout: int = 5, retries: int = 3):
        """
        Initialise l'adaptateur SNMP.
        
        Args:
            timeout: Délai d'attente pour les requêtes SNMP
            retries: Nombre de tentatives en cas d'échec
        """
        self.timeout = timeout
        self.retries = retries
    
    def snmp_get(self, target: str, oid: str, community: str = 'public', version: str = '2c') -> Dict[str, Any]:
        """
        Exécute une requête SNMP GET.
        
        Args:
            target: Adresse IP de l'équipement
            oid: OID à interroger
            community: Communauté SNMP
            version: Version SNMP
            
        Returns:
            Résultat de la requête
        """
        try:
            cmd = [
                'snmpget',
                '-v', version,
                '-c', community,
                '-t', str(self.timeout),
                '-r', str(self.retries),
                '-Oq',
                target,
                oid
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout + 5)
            
            if result.returncode == 0 and result.stdout:
                # Parser la sortie SNMP
                output = result.stdout.strip()
                if ' = ' in output:
                    oid_part, value_part = output.split(' = ', 1)
                    return {
                        'success': True,
                        'oid': oid_part.strip(),
                        'value': value_part.strip(),
                        'raw_output': output
                    }
            
            return {
                'success': False,
                'error': result.stderr.strip() if result.stderr else 'No output',
                'returncode': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': f'Timeout after {self.timeout} seconds'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def snmp_walk(self, target: str, oid: str, community: str = 'public', version: str = '2c') -> Dict[str, Any]:
        """
        Exécute une requête SNMP WALK.
        
        Args:
            target: Adresse IP de l'équipement
            oid: OID de base pour le walk
            community: Communauté SNMP
            version: Version SNMP
            
        Returns:
            Résultats du walk
        """
        try:
            cmd = [
                'snmpwalk',
                '-v', version,
                '-c', community,
                '-t', str(self.timeout),
                '-r', str(self.retries),
                '-Oq',
                target,
                oid
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=(self.timeout + 5) * 3)
            
            if result.returncode == 0 and result.stdout:
                data = {}
                for line in result.stdout.strip().split('\n'):
                    if ' = ' in line:
                        oid_part, value_part = line.split(' = ', 1)
                        data[oid_part.strip()] = value_part.strip()
                
                return {
                    'success': True,
                    'data': data,
                    'count': len(data)
                }
            
            return {
                'success': False,
                'error': result.stderr.strip() if result.stderr else 'No output',
                'returncode': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': f'Timeout after {self.timeout * 3} seconds'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_system_info(self, target: str, community: str = 'public') -> Dict[str, Any]:
        """
        Collecte les informations système de base.
        
        Args:
            target: Adresse IP de l'équipement
            community: Communauté SNMP
            
        Returns:
            Informations système
        """
        system_info = {}
        errors = []
        
        for name, oid in self.SYSTEM_OIDS.items():
            result = self.snmp_get(target, oid, community)
            if result['success']:
                system_info[name] = result['value']
            else:
                errors.append(f"{name}: {result.get('error', 'Unknown error')}")
        
        return {
            'success': len(system_info) > 0,
            'target': target,
            'system_info': system_info,
            'errors': errors,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_interface_metrics(self, target: str, community: str = 'public') -> Dict[str, Any]:
        """
        Collecte les métriques des interfaces réseau.
        
        Args:
            target: Adresse IP de l'équipement
            community: Communauté SNMP
            
        Returns:
            Métriques des interfaces
        """
        try:
            # Obtenir le nombre d'interfaces
            num_result = self.snmp_get(target, self.INTERFACE_OIDS['ifNumber'], community)
            
            if not num_result['success']:
                return {
                    'success': False,
                    'target': target,
                    'error': f"Cannot get interface count: {num_result.get('error')}",
                    'timestamp': datetime.now().isoformat()
                }
            
            try:
                num_interfaces = int(num_result['value'].split()[0])
            except (ValueError, IndexError):
                num_interfaces = 10  # Valeur par défaut
            
            # Collecter les métriques pour chaque interface
            interfaces = {}
            
            for i in range(1, min(num_interfaces + 1, 25)):  # Limite à 24 interfaces
                interface_data = {}
                
                for metric, base_oid in self.INTERFACE_OIDS.items():
                    if metric != 'ifNumber':
                        oid = f"{base_oid}.{i}"
                        result = self.snmp_get(target, oid, community)
                        
                        if result['success']:
                            value = result['value']
                            # Nettoyer la valeur
                            if ' ' in value:
                                value = value.split()[0]
                            interface_data[metric] = value
                
                if interface_data:
                    interfaces[f"interface_{i}"] = interface_data
            
            return {
                'success': True,
                'target': target,
                'interface_count': len(interfaces),
                'interfaces': interfaces,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'target': target,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def test_connectivity(self, target: str, community: str = 'public') -> Dict[str, Any]:
        """
        Teste la connectivité SNMP avec un équipement.
        
        Args:
            target: Adresse IP de l'équipement
            community: Communauté SNMP
            
        Returns:
            Résultat du test de connectivité
        """
        start_time = datetime.now()
        
        # Test simple avec sysDescr
        result = self.snmp_get(target, self.SYSTEM_OIDS['sysDescr'], community)
        
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        
        if result['success']:
            return {
                'success': True,
                'target': target,
                'community': community,
                'response_time_seconds': response_time,
                'system_description': result['value'][:100] + '...' if len(result['value']) > 100 else result['value'],
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'success': False,
                'target': target,
                'error': result.get('error', 'No SNMP response'),
                'response_time_seconds': response_time,
                'timestamp': datetime.now().isoformat()
            }
    
    def collect_comprehensive_metrics(self, target: str, community: str = 'public') -> Dict[str, Any]:
        """
        Collecte un ensemble complet de métriques depuis un équipement.
        
        Args:
            target: Adresse IP de l'équipement
            community: Communauté SNMP
            
        Returns:
            Ensemble complet de métriques
        """
        comprehensive_data = {
            'target': target,
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'errors': []
        }
        
        # Test de connectivité d'abord
        connectivity_test = self.test_connectivity(target, community)
        if not connectivity_test['success']:
            comprehensive_data['errors'].append(f"Connectivity test failed: {connectivity_test.get('error')}")
            return comprehensive_data
        
        comprehensive_data['connectivity'] = connectivity_test
        
        # Informations système
        system_result = self.get_system_info(target, community)
        if system_result['success']:
            comprehensive_data['system_info'] = system_result['system_info']
        else:
            comprehensive_data['errors'].extend(system_result.get('errors', []))
        
        # Métriques des interfaces
        interface_result = self.get_interface_metrics(target, community)
        if interface_result['success']:
            comprehensive_data['interfaces'] = interface_result['interfaces']
            comprehensive_data['interface_count'] = interface_result['interface_count']
        else:
            comprehensive_data['errors'].append(f"Interface metrics: {interface_result.get('error')}")
        
        # Déterminer le succès global
        comprehensive_data['success'] = (
            comprehensive_data.get('system_info') or 
            comprehensive_data.get('interfaces')
        )
        
        return comprehensive_data
    
    def is_snmp_available(self) -> bool:
        """
        Vérifie si les outils SNMP sont disponibles sur le système.
        
        Returns:
            True si les outils SNMP sont disponibles
        """
        try:
            result = subprocess.run(['snmpget', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except Exception:
            return False 