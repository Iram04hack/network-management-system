"""
Tests d'intégration pour Suricata dans le module security_management.
"""

import unittest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock, Mock, mock_open
from datetime import datetime, timezone, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model

from ..models import SecurityEvent, AlertRule, ThreatSignature
from ..infrastructure.docker_integration import DockerSecurityService

User = get_user_model()


class SuricataAdapter:
    """
    Adaptateur pour l'intégration avec Suricata IDS.
    Implémentation simplifiée pour les tests.
    """
    
    def __init__(self, config_path: str = "/etc/suricata/suricata.yaml", log_path: str = "/var/log/suricata/"):
        self.config_path = config_path
        self.log_path = log_path
        self.eve_log_path = os.path.join(log_path, "eve.json")
        self.fast_log_path = os.path.join(log_path, "fast.log")
    
    def parse_eve_log(self, max_lines: int = 1000):
        """
        Parse le fichier eve.json pour extraire les alertes.
        """
        alerts = []
        try:
            with open(self.eve_log_path, 'r') as f:
                lines = f.readlines()[-max_lines:] if max_lines else f.readlines()
                
                for line in lines:
                    try:
                        log_entry = json.loads(line.strip())
                        if log_entry.get('event_type') == 'alert':
                            alerts.append(log_entry)
                    except json.JSONDecodeError:
                        continue
            
            return {
                'success': True,
                'alerts': alerts,
                'count': len(alerts),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'alerts': [],
                'count': 0
            }
    
    def get_stats(self):
        """
        Récupère les statistiques de Suricata.
        """
        try:
            stats_path = os.path.join(self.log_path, "stats.log")
            if os.path.exists(stats_path):
                with open(stats_path, 'r') as f:
                    last_line = f.readlines()[-1] if f.readlines() else ""
                    stats_data = json.loads(last_line) if last_line else {}
            else:
                stats_data = {}
            
            return {
                'success': True,
                'stats': stats_data,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'stats': {}
            }
    
    def reload_rules(self):
        """
        Recharge les règles Suricata.
        """
        try:
            # Simulation du rechargement des règles
            # En réalité, cela enverrait un signal USR2 au processus Suricata
            return {
                'success': True,
                'message': 'Rules reloaded successfully',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def add_custom_rule(self, rule_content: str, rule_file: str = "local.rules"):
        """
        Ajoute une règle personnalisée à Suricata.
        """
        try:
            rules_dir = "/etc/suricata/rules"
            rule_path = os.path.join(rules_dir, rule_file)
            
            # En mode test, on simule l'écriture
            return {
                'success': True,
                'rule_content': rule_content,
                'rule_file': rule_path,
                'message': f'Rule added to {rule_file}',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


class SuricataIntegrationTest(TestCase):
    """
    Tests pour l'intégration avec Suricata IDS.
    """
    
    def setUp(self):
        """
        Initialisation des données de test.
        """
        self.adapter = SuricataAdapter()
        self.user = User.objects.create_user(
            username="security_admin",
            email="security@example.com",
            password="password"
        )
        
        # Mock des logs Suricata
        self.mock_eve_alerts = [
            {
                "timestamp": "2025-07-11T10:30:00.123456+0000",
                "flow_id": 123456789,
                "event_type": "alert",
                "src_ip": "192.168.1.100",
                "src_port": 54321,
                "dest_ip": "10.0.0.5",
                "dest_port": 80,
                "proto": "TCP",
                "alert": {
                    "action": "allowed",
                    "gid": 1,
                    "signature_id": 2001219,
                    "rev": 19,
                    "signature": "ET POLICY Suspicious inbound to MSSQL port 1433",
                    "category": "Potentially Bad Traffic",
                    "severity": 2
                },
                "payload": "474554202f20485454502f312e310d0a",
                "payload_printable": "GET / HTTP/1.1\r\n"
            },
            {
                "timestamp": "2025-07-11T10:35:00.456789+0000",
                "flow_id": 987654321,
                "event_type": "alert",
                "src_ip": "172.16.0.50",
                "src_port": 12345,
                "dest_ip": "192.168.1.200",
                "dest_port": 22,
                "proto": "TCP",
                "alert": {
                    "action": "blocked",
                    "gid": 1,
                    "signature_id": 2001458,
                    "rev": 6,
                    "signature": "ET SCAN SSH brute force attempt",
                    "category": "Attempted Information Leak",
                    "severity": 1
                },
                "ssh": {
                    "client": {
                        "proto_version": "2.0",
                        "software_version": "OpenSSH_7.4"
                    },
                    "server": {
                        "proto_version": "2.0",
                        "software_version": "OpenSSH_8.0"
                    }
                }
            }
        ]
        
        self.mock_stats = {
            "timestamp": "2025-07-11T10:40:00.000000+0000",
            "uptime": 3600,
            "capture": {
                "kernel_packets": 125000,
                "kernel_drops": 15,
                "errors": 0
            },
            "decoder": {
                "pkts": 124985,
                "bytes": 89567234,
                "invalid": 0,
                "ipv4": 120000,
                "ipv6": 4985,
                "ethernet": 124985,
                "tcp": 98756,
                "udp": 25789,
                "icmpv4": 440
            },
            "flow": {
                "tcp": 15678,
                "udp": 3421,
                "icmpv4": 89,
                "spare": 10000,
                "emerg_mode_entered": 0,
                "emerg_mode_over": 0
            },
            "detect": {
                "alert": 234,
                "engines": [
                    {
                        "id": 0,
                        "last_reload": "2025-07-11T09:00:00.000000+0000",
                        "rules_loaded": 25000,
                        "rules_failed": 0
                    }
                ]
            }
        }
    
    @patch('builtins.open', new_callable=mock_open)
    def test_parse_eve_log_success(self, mock_file):
        """
        Test de parsing réussi du fichier eve.json.
        """
        # Préparer le contenu du fichier mock
        eve_content = "\n".join([
            json.dumps(alert) for alert in self.mock_eve_alerts
        ])
        mock_file.return_value.readlines.return_value = eve_content.split('\n')
        
        # Exécution du test
        result = self.adapter.parse_eve_log(max_lines=100)
        
        # Vérifications
        self.assertTrue(result['success'])
        self.assertEqual(result['count'], 2)
        self.assertIn('alerts', result)
        
        alerts = result['alerts']
        self.assertEqual(len(alerts), 2)
        
        # Vérifier la première alerte
        first_alert = alerts[0]
        self.assertEqual(first_alert['src_ip'], '192.168.1.100')
        self.assertEqual(first_alert['dest_port'], 80)
        self.assertEqual(first_alert['alert']['signature_id'], 2001219)
        self.assertEqual(first_alert['alert']['severity'], 2)
        
        # Vérifier la deuxième alerte
        second_alert = alerts[1]
        self.assertEqual(second_alert['src_ip'], '172.16.0.50')
        self.assertEqual(second_alert['dest_port'], 22)
        self.assertEqual(second_alert['alert']['action'], 'blocked')
        self.assertEqual(second_alert['alert']['severity'], 1)
    
    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_parse_eve_log_file_not_found(self, mock_file):
        """
        Test de gestion d'erreur quand le fichier eve.json n'existe pas.
        """
        # Exécution du test
        result = self.adapter.parse_eve_log()
        
        # Vérifications
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertEqual(result['count'], 0)
        self.assertEqual(len(result['alerts']), 0)
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists', return_value=True)
    def test_get_stats_success(self, mock_exists, mock_file):
        """
        Test de récupération réussie des statistiques Suricata.
        """
        # Préparer le contenu du fichier de stats
        stats_content = json.dumps(self.mock_stats)
        mock_file.return_value.readlines.return_value = [stats_content]
        
        # Exécution du test
        result = self.adapter.get_stats()
        
        # Vérifications
        self.assertTrue(result['success'])
        self.assertIn('stats', result)
        
        stats = result['stats']
        self.assertEqual(stats['uptime'], 3600)
        self.assertEqual(stats['capture']['kernel_packets'], 125000)
        self.assertEqual(stats['decoder']['pkts'], 124985)
        self.assertEqual(stats['detect']['alert'], 234)
        self.assertEqual(stats['detect']['engines'][0]['rules_loaded'], 25000)
    
    @patch('os.path.exists', return_value=False)
    def test_get_stats_file_not_found(self, mock_exists):
        """
        Test de gestion quand le fichier de stats n'existe pas.
        """
        # Exécution du test
        result = self.adapter.get_stats()
        
        # Vérifications
        self.assertTrue(result['success'])
        self.assertEqual(result['stats'], {})
    
    def test_reload_rules_success(self):
        """
        Test de rechargement réussi des règles.
        """
        # Exécution du test
        result = self.adapter.reload_rules()
        
        # Vérifications
        self.assertTrue(result['success'])
        self.assertIn('Rules reloaded successfully', result['message'])
        self.assertIn('timestamp', result)
    
    def test_add_custom_rule_success(self):
        """
        Test d'ajout réussi d'une règle personnalisée.
        """
        # Règle de test
        test_rule = 'alert tcp any any -> $HOME_NET 80 (msg:"Test HTTP alert"; content:"GET"; sid:9001; rev:1;)'
        
        # Exécution du test
        result = self.adapter.add_custom_rule(test_rule, "custom.rules")
        
        # Vérifications
        self.assertTrue(result['success'])
        self.assertEqual(result['rule_content'], test_rule)
        self.assertIn('custom.rules', result['rule_file'])
        self.assertIn('Rule added', result['message'])
    
    def test_convert_suricata_alerts_to_security_events(self):
        """
        Test de conversion des alertes Suricata en événements de sécurité NMS.
        """
        # Simuler le parsing des alertes
        suricata_alerts = self.mock_eve_alerts
        
        # Conversion des alertes
        security_events = []
        for alert in suricata_alerts:
            # Extraire les informations importantes
            alert_info = alert.get('alert', {})
            
            # Déterminer la sévérité NMS à partir de la sévérité Suricata
            suricata_severity = alert_info.get('severity', 3)
            if suricata_severity == 1:
                nms_severity = 'critical'
            elif suricata_severity == 2:
                nms_severity = 'high'
            elif suricata_severity == 3:
                nms_severity = 'medium'
            else:
                nms_severity = 'low'
            
            # Créer l'événement de sécurité
            security_event = SecurityEvent.objects.create(
                event_type='intrusion_detection',
                source_ip=alert.get('src_ip'),
                destination_ip=alert.get('dest_ip'),
                source_port=alert.get('src_port'),
                destination_port=alert.get('dest_port'),
                protocol=alert.get('proto', '').lower(),
                severity=nms_severity,
                description=alert_info.get('signature', 'Unknown Suricata alert'),
                details={
                    'suricata_alert': alert,
                    'signature_id': alert_info.get('signature_id'),
                    'category': alert_info.get('category'),
                    'action': alert_info.get('action'),
                    'flow_id': alert.get('flow_id'),
                    'payload': alert.get('payload_printable', '')
                },
                raw_data=json.dumps(alert),
                detected_at=datetime.fromisoformat(
                    alert['timestamp'].replace('Z', '+00:00')
                ) if alert.get('timestamp') else datetime.now(timezone.utc)
            )
            security_events.append(security_event)
        
        # Vérifications
        self.assertEqual(len(security_events), 2)
        self.assertEqual(SecurityEvent.objects.count(), 2)
        
        # Vérifier le premier événement
        event1 = security_events[0]
        self.assertEqual(event1.event_type, 'intrusion_detection')
        self.assertEqual(event1.source_ip, '192.168.1.100')
        self.assertEqual(event1.destination_port, 80)
        self.assertEqual(event1.severity, 'high')  # Suricata severity 2 -> high
        self.assertIn('MSSQL', event1.description)
        
        # Vérifier le deuxième événement
        event2 = security_events[1]
        self.assertEqual(event2.event_type, 'intrusion_detection')
        self.assertEqual(event2.source_ip, '172.16.0.50')
        self.assertEqual(event2.destination_port, 22)
        self.assertEqual(event2.severity, 'critical')  # Suricata severity 1 -> critical
        self.assertIn('SSH brute force', event2.description)
        self.assertEqual(event2.details['action'], 'blocked')
    
    def test_create_threat_signatures_from_suricata_rules(self):
        """
        Test de création de signatures de menaces à partir des règles Suricata.
        """
        # Signatures basées sur les alertes Suricata
        signatures_data = [
            {
                'signature_id': 2001219,
                'name': 'ET POLICY Suspicious inbound to MSSQL port 1433',
                'description': 'Detects suspicious inbound connections to MSSQL database port',
                'category': 'Database Attack',
                'severity': 'high',
                'rule_content': 'alert tcp any any -> $HOME_NET 1433 (msg:"ET POLICY Suspicious inbound to MSSQL port 1433"; sid:2001219; rev:19;)'
            },
            {
                'signature_id': 2001458,
                'name': 'ET SCAN SSH brute force attempt',
                'description': 'Detects SSH brute force attack attempts',
                'category': 'Brute Force',
                'severity': 'critical',
                'rule_content': 'alert tcp any any -> $HOME_NET 22 (msg:"ET SCAN SSH brute force attempt"; sid:2001458; rev:6;)'
            }
        ]
        
        # Créer les signatures dans le système
        created_signatures = []
        for sig_data in signatures_data:
            signature = ThreatSignature.objects.create(
                name=sig_data['name'],
                signature_type='suricata_rule',
                content=sig_data['rule_content'],
                severity=sig_data['severity'],
                category=sig_data['category'],
                description=sig_data['description'],
                is_active=True,
                metadata={
                    'suricata_sid': sig_data['signature_id'],
                    'source': 'emerging_threats',
                    'last_updated': datetime.now(timezone.utc).isoformat()
                }
            )
            created_signatures.append(signature)
        
        # Vérifications
        self.assertEqual(len(created_signatures), 2)
        self.assertEqual(ThreatSignature.objects.count(), 2)
        
        # Vérifier la première signature
        sig1 = created_signatures[0]
        self.assertEqual(sig1.signature_type, 'suricata_rule')
        self.assertIn('MSSQL', sig1.name)
        self.assertEqual(sig1.severity, 'high')
        self.assertEqual(sig1.metadata['suricata_sid'], 2001219)
        
        # Vérifier la deuxième signature
        sig2 = created_signatures[1]
        self.assertEqual(sig2.signature_type, 'suricata_rule')
        self.assertIn('SSH brute force', sig2.name)
        self.assertEqual(sig2.severity, 'critical')
        self.assertEqual(sig2.metadata['suricata_sid'], 2001458)
    
    @patch.object(SuricataAdapter, 'parse_eve_log')
    @patch.object(SuricataAdapter, 'get_stats')
    def test_real_time_monitoring_integration(self, mock_stats, mock_parse):
        """
        Test d'intégration de monitoring en temps réel avec Suricata.
        """
        # Configuration des mocks
        mock_parse.return_value = {
            'success': True,
            'alerts': self.mock_eve_alerts,
            'count': len(self.mock_eve_alerts)
        }
        
        mock_stats.return_value = {
            'success': True,
            'stats': self.mock_stats
        }
        
        # Simulation d'une collecte de monitoring
        alerts_result = self.adapter.parse_eve_log(max_lines=50)
        stats_result = self.adapter.get_stats()
        
        # Vérifications des alertes
        self.assertTrue(alerts_result['success'])
        self.assertEqual(alerts_result['count'], 2)
        
        # Vérifications des statistiques
        self.assertTrue(stats_result['success'])
        stats = stats_result['stats']
        self.assertEqual(stats['detect']['alert'], 234)
        self.assertEqual(stats['decoder']['pkts'], 124985)
        
        # Calcul de métriques de performance
        total_packets = stats['decoder']['pkts']
        total_alerts = stats['detect']['alert']
        drop_rate = stats['capture']['kernel_drops'] / stats['capture']['kernel_packets'] * 100
        alert_rate = total_alerts / total_packets * 100 if total_packets > 0 else 0
        
        # Vérifications des métriques
        self.assertLess(drop_rate, 1.0)  # Taux de perte < 1%
        self.assertGreater(alert_rate, 0)  # Il y a des alertes
        self.assertLess(alert_rate, 5.0)  # Mais pas trop (< 5%)
    
    @patch.object(DockerSecurityService, 'restart_service')
    @patch.object(SuricataAdapter, 'reload_rules')
    def test_rule_management_workflow(self, mock_reload, mock_restart):
        """
        Test du workflow de gestion des règles Suricata.
        """
        # Configuration des mocks
        mock_reload.return_value = {'success': True, 'message': 'Rules reloaded'}
        mock_restart.return_value = {'success': True, 'status': 'running'}
        
        # Créer une nouvelle règle d'alerte
        new_rule = AlertRule.objects.create(
            name="Custom Malware Detection",
            rule_type="suricata",
            content='alert tcp any any -> $HOME_NET any (msg:"Custom malware detected"; content:"|deadbeef|"; sid:9999; rev:1;)',
            severity="high",
            is_active=True,
            created_by=self.user
        )
        
        # Ajouter la règle à Suricata
        add_result = self.adapter.add_custom_rule(new_rule.content, "custom.rules")
        self.assertTrue(add_result['success'])
        
        # Recharger les règles
        reload_result = self.adapter.reload_rules()
        self.assertTrue(reload_result['success'])
        
        # Vérifications
        self.assertEqual(AlertRule.objects.count(), 1)
        created_rule = AlertRule.objects.first()
        self.assertEqual(created_rule.name, "Custom Malware Detection")
        self.assertEqual(created_rule.rule_type, "suricata")
        self.assertIn("deadbeef", created_rule.content)
        
        # Vérifier que les méthodes ont été appelées
        mock_reload.assert_called_once()


if __name__ == '__main__':
    unittest.main()