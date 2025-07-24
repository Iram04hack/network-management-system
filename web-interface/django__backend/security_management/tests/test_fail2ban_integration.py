"""
Tests d'intégration pour Fail2ban dans le module security_management.
"""

import unittest
import re
import tempfile
import os
from unittest.mock import patch, MagicMock, Mock, mock_open
from datetime import datetime, timezone, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model

from ..models import SecurityEvent, BlockedIP, SecurityAction
from ..infrastructure.docker_integration import DockerSecurityService

User = get_user_model()


class Fail2banAdapter:
    """
    Adaptateur pour l'intégration avec Fail2ban.
    Implémentation simplifiée pour les tests.
    """
    
    def __init__(self, log_path: str = "/var/log/fail2ban.log", socket_path: str = "/var/run/fail2ban/fail2ban.sock"):
        self.log_path = log_path
        self.socket_path = socket_path
    
    def parse_fail2ban_log(self, max_lines: int = 1000):
        """
        Parse le fichier de log Fail2ban pour extraire les actions.
        """
        actions = []
        try:
            with open(self.log_path, 'r') as f:
                lines = f.readlines()[-max_lines:] if max_lines else f.readlines()
                
                for line in lines:
                    # Parser les différents types d'actions Fail2ban
                    action = self._parse_log_line(line.strip())
                    if action:
                        actions.append(action)
            
            return {
                'success': True,
                'actions': actions,
                'count': len(actions),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'actions': [],
                'count': 0
            }
    
    def _parse_log_line(self, line: str):
        """
        Parse une ligne de log Fail2ban.
        """
        # Motifs regex pour différents types d'actions
        ban_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}).+\[(\w+)\]\s+NOTICE\s+\[(\w+)\]\s+Ban\s+([\d\.]+)'
        unban_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}).+\[(\w+)\]\s+NOTICE\s+\[(\w+)\]\s+Unban\s+([\d\.]+)'
        found_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}).+\[(\w+)\]\s+INFO\s+\[(\w+)\]\s+Found\s+([\d\.]+)\s+-\s+(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})'
        
        # Essayer de matcher un bannissement
        ban_match = re.search(ban_pattern, line)
        if ban_match:
            return {
                'timestamp': ban_match.group(1),
                'level': ban_match.group(2),
                'jail': ban_match.group(3),
                'ip': ban_match.group(4),
                'action': 'ban',
                'raw_line': line
            }
        
        # Essayer de matcher un débannissement
        unban_match = re.search(unban_pattern, line)
        if unban_match:
            return {
                'timestamp': unban_match.group(1),
                'level': unban_match.group(2),
                'jail': unban_match.group(3),
                'ip': unban_match.group(4),
                'action': 'unban',
                'raw_line': line
            }
        
        # Essayer de matcher une détection
        found_match = re.search(found_pattern, line)
        if found_match:
            return {
                'timestamp': found_match.group(1),
                'level': found_match.group(2),
                'jail': found_match.group(3),
                'ip': found_match.group(4),
                'action': 'found',
                'detection_time': found_match.group(5),
                'raw_line': line
            }
        
        return None
    
    def get_banned_ips(self, jail: str = None):
        """
        Récupère la liste des IPs actuellement bannies.
        """
        try:
            # Simulation de la commande: fail2ban-client status [jail]
            if jail:
                # Simulation d'IPs bannies pour une jail spécifique
                banned_ips = [
                    "192.168.1.100",
                    "10.0.0.50",
                    "172.16.0.25"
                ]
            else:
                # Toutes les IPs bannies
                banned_ips = [
                    "192.168.1.100",
                    "10.0.0.50",
                    "172.16.0.25",
                    "203.0.113.45",
                    "198.51.100.78"
                ]
            
            return {
                'success': True,
                'banned_ips': banned_ips,
                'jail': jail,
                'count': len(banned_ips),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'banned_ips': []
            }
    
    def get_jail_status(self, jail: str):
        """
        Récupère le statut d'une jail spécifique.
        """
        try:
            # Simulation du statut d'une jail
            jail_status = {
                'jail_name': jail,
                'status': 'active',
                'filter': f'{jail}[mode=normal]',
                'actions': ['iptables-multiport'],
                'currently_failed': 3,
                'total_failed': 127,
                'currently_banned': 2,
                'total_banned': 45,
                'banned_ip_list': ['192.168.1.100', '10.0.0.50']
            }
            
            return {
                'success': True,
                'jail_status': jail_status,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def ban_ip(self, ip: str, jail: str):
        """
        Bannit manuellement une adresse IP.
        """
        try:
            # Simulation de la commande: fail2ban-client set [jail] banip [ip]
            return {
                'success': True,
                'action': 'manual_ban',
                'ip': ip,
                'jail': jail,
                'message': f'IP {ip} has been banned in jail {jail}',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'ip': ip,
                'jail': jail
            }
    
    def unban_ip(self, ip: str, jail: str):
        """
        Débannit manuellement une adresse IP.
        """
        try:
            # Simulation de la commande: fail2ban-client set [jail] unbanip [ip]
            return {
                'success': True,
                'action': 'manual_unban',
                'ip': ip,
                'jail': jail,
                'message': f'IP {ip} has been unbanned from jail {jail}',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'ip': ip,
                'jail': jail
            }
    
    def get_all_jails(self):
        """
        Récupère la liste de toutes les jails actives.
        """
        try:
            # Simulation des jails actives
            jails = [
                'sshd',
                'apache-auth',
                'apache-badbots',
                'apache-noscript',
                'apache-overflows',
                'postfix',
                'proftpd',
                'pure-ftpd',
                'vsftpd'
            ]
            
            return {
                'success': True,
                'jails': jails,
                'count': len(jails),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'jails': []
            }


class Fail2banIntegrationTest(TestCase):
    """
    Tests pour l'intégration avec Fail2ban.
    """
    
    def setUp(self):
        """
        Initialisation des données de test.
        """
        self.adapter = Fail2banAdapter()
        self.user = User.objects.create_user(
            username="security_admin",
            email="security@example.com",
            password="password"
        )
        
        # Mock des logs Fail2ban
        self.mock_log_lines = [
            "2025-07-11 10:30:15,123 fail2ban.actions[1234]: NOTICE [sshd] Ban 192.168.1.100",
            "2025-07-11 10:25:42,456 fail2ban.filter[5678]: INFO [sshd] Found 192.168.1.100 - 2025-07-11 10:25:40",
            "2025-07-11 10:20:33,789 fail2ban.actions[9012]: NOTICE [apache-auth] Ban 10.0.0.50",
            "2025-07-11 10:45:18,321 fail2ban.actions[3456]: NOTICE [sshd] Unban 172.16.0.25",
            "2025-07-11 10:40:55,654 fail2ban.filter[7890]: INFO [apache-badbots] Found 203.0.113.45 - 2025-07-11 10:40:50"
        ]
    
    @patch('builtins.open', new_callable=mock_open)
    def test_parse_fail2ban_log_success(self, mock_file):
        """
        Test de parsing réussi du fichier de log Fail2ban.
        """
        # Préparer le contenu du fichier mock
        log_content = "\n".join(self.mock_log_lines)
        mock_file.return_value.readlines.return_value = self.mock_log_lines
        
        # Exécution du test
        result = self.adapter.parse_fail2ban_log(max_lines=100)
        
        # Vérifications
        self.assertTrue(result['success'])
        self.assertEqual(result['count'], 5)
        self.assertIn('actions', result)
        
        actions = result['actions']
        self.assertEqual(len(actions), 5)
        
        # Vérifier les différents types d'actions
        ban_actions = [a for a in actions if a['action'] == 'ban']
        unban_actions = [a for a in actions if a['action'] == 'unban']
        found_actions = [a for a in actions if a['action'] == 'found']
        
        self.assertEqual(len(ban_actions), 2)
        self.assertEqual(len(unban_actions), 1)
        self.assertEqual(len(found_actions), 2)
        
        # Vérifier une action de bannissement
        ssh_ban = next(a for a in ban_actions if a['jail'] == 'sshd')
        self.assertEqual(ssh_ban['ip'], '192.168.1.100')
        self.assertEqual(ssh_ban['level'], 'fail2ban.actions')
        
        # Vérifier une action de débannissement
        unban_action = unban_actions[0]
        self.assertEqual(unban_action['ip'], '172.16.0.25')
        self.assertEqual(unban_action['jail'], 'sshd')
    
    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_parse_fail2ban_log_file_not_found(self, mock_file):
        """
        Test de gestion d'erreur quand le fichier de log n'existe pas.
        """
        # Exécution du test
        result = self.adapter.parse_fail2ban_log()
        
        # Vérifications
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertEqual(result['count'], 0)
        self.assertEqual(len(result['actions']), 0)
    
    def test_get_banned_ips_success(self):
        """
        Test de récupération réussie des IPs bannies.
        """
        # Test sans jail spécifique
        result = self.adapter.get_banned_ips()
        
        # Vérifications
        self.assertTrue(result['success'])
        self.assertIn('banned_ips', result)
        self.assertEqual(result['count'], 5)
        self.assertIn('192.168.1.100', result['banned_ips'])
        self.assertIn('203.0.113.45', result['banned_ips'])
        
        # Test avec jail spécifique
        result_jail = self.adapter.get_banned_ips('sshd')
        
        # Vérifications
        self.assertTrue(result_jail['success'])
        self.assertEqual(result_jail['jail'], 'sshd')
        self.assertEqual(result_jail['count'], 3)
    
    def test_get_jail_status_success(self):
        """
        Test de récupération du statut d'une jail.
        """
        # Exécution du test
        result = self.adapter.get_jail_status('sshd')
        
        # Vérifications
        self.assertTrue(result['success'])
        self.assertIn('jail_status', result)
        
        status = result['jail_status']
        self.assertEqual(status['jail_name'], 'sshd')
        self.assertEqual(status['status'], 'active')
        self.assertEqual(status['currently_banned'], 2)
        self.assertEqual(status['total_banned'], 45)
        self.assertIn('192.168.1.100', status['banned_ip_list'])
    
    def test_ban_ip_success(self):
        """
        Test de bannissement manuel d'une IP.
        """
        # Exécution du test
        result = self.adapter.ban_ip('198.51.100.123', 'sshd')
        
        # Vérifications
        self.assertTrue(result['success'])
        self.assertEqual(result['action'], 'manual_ban')
        self.assertEqual(result['ip'], '198.51.100.123')
        self.assertEqual(result['jail'], 'sshd')
        self.assertIn('has been banned', result['message'])
        self.assertIn('timestamp', result)
    
    def test_unban_ip_success(self):
        """
        Test de débannissement manuel d'une IP.
        """
        # Exécution du test
        result = self.adapter.unban_ip('192.168.1.100', 'sshd')
        
        # Vérifications
        self.assertTrue(result['success'])
        self.assertEqual(result['action'], 'manual_unban')
        self.assertEqual(result['ip'], '192.168.1.100')
        self.assertEqual(result['jail'], 'sshd')
        self.assertIn('has been unbanned', result['message'])
        self.assertIn('timestamp', result)
    
    def test_get_all_jails_success(self):
        """
        Test de récupération de toutes les jails actives.
        """
        # Exécution du test
        result = self.adapter.get_all_jails()
        
        # Vérifications
        self.assertTrue(result['success'])
        self.assertIn('jails', result)
        self.assertEqual(result['count'], 9)
        
        jails = result['jails']
        self.assertIn('sshd', jails)
        self.assertIn('apache-auth', jails)
        self.assertIn('postfix', jails)
    
    def test_convert_fail2ban_actions_to_security_events(self):
        """
        Test de conversion des actions Fail2ban en événements de sécurité NMS.
        """
        # Simuler le parsing des actions
        with patch.object(self.adapter, 'parse_fail2ban_log') as mock_parse:
            mock_parse.return_value = {
                'success': True,
                'actions': [
                    {
                        'timestamp': '2025-07-11 10:30:15,123',
                        'level': 'fail2ban.actions',
                        'jail': 'sshd',
                        'ip': '192.168.1.100',
                        'action': 'ban',
                        'raw_line': 'test line'
                    },
                    {
                        'timestamp': '2025-07-11 10:20:33,789',
                        'level': 'fail2ban.actions',
                        'jail': 'apache-auth',
                        'ip': '10.0.0.50',
                        'action': 'ban',
                        'raw_line': 'test line 2'
                    }
                ],
                'count': 2
            }
            
            # Récupérer les actions
            result = self.adapter.parse_fail2ban_log()
            fail2ban_actions = result['actions']
            
            # Conversion en événements de sécurité
            security_events = []
            for action in fail2ban_actions:
                if action['action'] == 'ban':
                    # Créer l'événement de sécurité
                    security_event = SecurityEvent.objects.create(
                        event_type='automated_response',
                        source_ip=action['ip'],
                        destination_ip=None,
                        severity='medium',
                        description=f"IP {action['ip']} banned by Fail2ban in jail {action['jail']}",
                        details={
                            'fail2ban_action': action,
                            'jail': action['jail'],
                            'action_type': action['action'],
                            'level': action['level']
                        },
                        raw_data=action['raw_line'],
                        detected_at=datetime.strptime(
                            action['timestamp'], '%Y-%m-%d %H:%M:%S,%f'
                        ).replace(tzinfo=timezone.utc)
                    )
                    security_events.append(security_event)
            
            # Vérifications
            self.assertEqual(len(security_events), 2)
            self.assertEqual(SecurityEvent.objects.count(), 2)
            
            # Vérifier le premier événement
            event1 = security_events[0]
            self.assertEqual(event1.event_type, 'automated_response')
            self.assertEqual(event1.source_ip, '192.168.1.100')
            self.assertEqual(event1.severity, 'medium')
            self.assertIn('sshd', event1.description)
            self.assertEqual(event1.details['jail'], 'sshd')
    
    def test_create_blocked_ips_from_fail2ban_data(self):
        """
        Test de création d'entrées BlockedIP à partir des données Fail2ban.
        """
        # Simuler la récupération des IPs bannies
        with patch.object(self.adapter, 'get_banned_ips') as mock_banned:
            mock_banned.return_value = {
                'success': True,
                'banned_ips': ['192.168.1.100', '10.0.0.50', '203.0.113.45'],
                'count': 3
            }
            
            # Récupérer les IPs bannies
            result = self.adapter.get_banned_ips()
            banned_ips = result['banned_ips']
            
            # Créer les entrées BlockedIP
            blocked_entries = []
            for ip in banned_ips:
                blocked_ip = BlockedIP.objects.create(
                    ip_address=ip,
                    reason='fail2ban_auto_ban',
                    blocked_at=datetime.now(timezone.utc),
                    blocked_by=self.user,
                    is_active=True,
                    source='fail2ban',
                    metadata={
                        'detection_method': 'fail2ban',
                        'jail': 'multiple',  # Pourrait être spécifique selon le contexte
                        'auto_blocked': True
                    }
                )
                blocked_entries.append(blocked_ip)
            
            # Vérifications
            self.assertEqual(len(blocked_entries), 3)
            self.assertEqual(BlockedIP.objects.count(), 3)
            
            # Vérifier une entrée
            first_entry = blocked_entries[0]
            self.assertEqual(first_entry.ip_address, '192.168.1.100')
            self.assertEqual(first_entry.reason, 'fail2ban_auto_ban')
            self.assertEqual(first_entry.source, 'fail2ban')
            self.assertTrue(first_entry.is_active)
            self.assertTrue(first_entry.metadata['auto_blocked'])
    
    def test_security_action_integration(self):
        """
        Test d'intégration avec le système d'actions de sécurité.
        """
        # Créer une action de bannissement manuel
        ban_action = SecurityAction.objects.create(
            action_type='block_ip',
            target_ip='198.51.100.123',
            reason='Manual ban due to suspicious activity',
            initiated_by=self.user,
            status='pending',
            details={
                'method': 'fail2ban',
                'jail': 'sshd',
                'duration': 3600  # 1 heure
            }
        )
        
        # Simuler l'exécution de l'action via Fail2ban
        result = self.adapter.ban_ip(
            ban_action.target_ip,
            ban_action.details['jail']
        )
        
        # Mettre à jour le statut de l'action
        if result['success']:
            ban_action.status = 'completed'
            ban_action.executed_at = datetime.now(timezone.utc)
            ban_action.result = result
            ban_action.save()
        
        # Vérifications
        updated_action = SecurityAction.objects.get(id=ban_action.id)
        self.assertEqual(updated_action.status, 'completed')
        self.assertIsNotNone(updated_action.executed_at)
        self.assertTrue(updated_action.result['success'])
        self.assertEqual(updated_action.result['ip'], '198.51.100.123')
    
    @patch.object(Fail2banAdapter, 'get_jail_status')
    @patch.object(Fail2banAdapter, 'get_banned_ips')
    def test_fail2ban_monitoring_dashboard_data(self, mock_banned, mock_status):
        """
        Test de collecte de données pour le tableau de bord de monitoring Fail2ban.
        """
        # Configuration des mocks
        mock_banned.return_value = {
            'success': True,
            'banned_ips': ['192.168.1.100', '10.0.0.50'],
            'count': 2
        }
        
        mock_status.return_value = {
            'success': True,
            'jail_status': {
                'jail_name': 'sshd',
                'status': 'active',
                'currently_failed': 5,
                'total_failed': 150,
                'currently_banned': 2,
                'total_banned': 47
            }
        }
        
        # Collecte des données de monitoring
        banned_result = self.adapter.get_banned_ips()
        status_result = self.adapter.get_jail_status('sshd')
        
        # Compilation des données pour le dashboard
        dashboard_data = {
            'total_banned_ips': banned_result['count'] if banned_result['success'] else 0,
            'jail_status': status_result['jail_status'] if status_result['success'] else {},
            'active_bans': banned_result['banned_ips'] if banned_result['success'] else [],
            'jail_efficiency': 0
        }
        
        # Calculer l'efficacité de la jail (ratio banned/failed)
        if status_result['success']:
            jail_data = status_result['jail_status']
            total_failed = jail_data['total_failed']
            total_banned = jail_data['total_banned']
            if total_failed > 0:
                dashboard_data['jail_efficiency'] = (total_banned / total_failed) * 100
        
        # Vérifications
        self.assertEqual(dashboard_data['total_banned_ips'], 2)
        self.assertEqual(dashboard_data['jail_status']['jail_name'], 'sshd')
        self.assertEqual(len(dashboard_data['active_bans']), 2)
        self.assertAlmostEqual(dashboard_data['jail_efficiency'], 31.33, places=1)  # 47/150 * 100
    
    @patch.object(DockerSecurityService, 'get_service_status')
    def test_fail2ban_service_health_check(self, mock_service_status):
        """
        Test de vérification de santé du service Fail2ban.
        """
        # Configuration du mock
        mock_service_status.return_value = {
            'success': True,
            'status': 'running',
            'uptime': '2 days',
            'memory_usage': '45.2MB',
            'cpu_usage': '0.5%'
        }
        
        # Vérification de santé complète
        docker_service = DockerSecurityService()
        service_status = docker_service.get_service_status('fail2ban')
        
        # Test des jails actives
        jails_result = self.adapter.get_all_jails()
        
        # Compilation du rapport de santé
        health_report = {
            'service_running': service_status['success'] and service_status['status'] == 'running',
            'active_jails': jails_result['count'] if jails_result['success'] else 0,
            'service_uptime': service_status.get('uptime', 'unknown'),
            'resource_usage': {
                'memory': service_status.get('memory_usage', 'unknown'),
                'cpu': service_status.get('cpu_usage', 'unknown')
            },
            'overall_health': 'healthy'
        }
        
        # Déterminer la santé globale
        if not health_report['service_running'] or health_report['active_jails'] == 0:
            health_report['overall_health'] = 'unhealthy'
        elif health_report['active_jails'] < 5:
            health_report['overall_health'] = 'warning'
        
        # Vérifications
        self.assertTrue(health_report['service_running'])
        self.assertEqual(health_report['active_jails'], 9)
        self.assertEqual(health_report['overall_health'], 'healthy')
        self.assertIn('days', health_report['service_uptime'])


if __name__ == '__main__':
    unittest.main()