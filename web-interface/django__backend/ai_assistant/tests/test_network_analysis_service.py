"""
Tests pour le service d'analyse réseau.

Ce module contient les tests unitaires pour le service d'analyse réseau.
"""

import unittest
from unittest.mock import patch, MagicMock

from ai_assistant.domain.services.network_analysis_service import NetworkAnalysisService
from ai_assistant.domain.exceptions import NetworkAnalysisError


class TestNetworkAnalysisService(unittest.TestCase):
    """Tests pour le service d'analyse réseau."""
    
    def setUp(self):
        """Initialise les tests."""
        self.service = NetworkAnalysisService()
    
    @patch('subprocess.run')
    def test_analyze_ping(self, mock_run):
        """Teste l'analyse d'une commande ping."""
        # Configurer le mock pour subprocess.run
        mock_process = MagicMock()
        mock_process.stdout = "PING google.com (142.250.74.110) 56(84) bytes of data.\n" \
                             "64 bytes from par10s41-in-f14.1e100.net (142.250.74.110): icmp_seq=1 ttl=115 time=10.8 ms\n" \
                             "64 bytes from par10s41-in-f14.1e100.net (142.250.74.110): icmp_seq=2 ttl=115 time=10.6 ms\n" \
                             "\n" \
                             "--- google.com ping statistics ---\n" \
                             "2 packets transmitted, 2 received, 0% packet loss, time 1001ms\n" \
                             "rtt min/avg/max/mdev = 10.588/10.694/10.801/0.106 ms"
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        # Test avec une commande ping valide
        with patch.object(self.service, 'analyze_ping_output', return_value={
            "analyse": {
                "packets_transmitted": 2,
                "packets_received": 2,
                "packet_loss": 0.0,
                "rtt_min": 10.588,
                "rtt_avg": 10.694,
                "rtt_max": 10.801
            }
        }):
            result = self.service.analyze_ping("google.com")
            
            self.assertIn("analyse", result)
            self.assertIn("packets_transmitted", result["analyse"])
            self.assertEqual(result["analyse"]["packets_transmitted"], 2)
            self.assertEqual(result["analyse"]["packets_received"], 2)
            self.assertEqual(result["analyse"]["packet_loss"], 0.0)
    
    @patch('subprocess.run')
    def test_analyze_ping_with_error(self, mock_run):
        """Teste la gestion des erreurs lors de l'analyse d'une commande ping."""
        # Configurer le mock pour simuler une erreur
        mock_process = MagicMock()
        mock_process.stderr = "ping: nonexistent.host: Name or service not known"
        mock_process.returncode = 2
        mock_run.return_value = mock_process
        
        # Test avec une commande ping qui échoue
        result = self.service.analyze_ping("nonexistent.host")
        
        self.assertIn("erreur", result)
        self.assertIn("Impossible de résoudre le nom d'hôte", result["erreur"])
    
    @patch('subprocess.run')
    def test_analyze_ping_with_exception(self, mock_run):
        """Teste la gestion des exceptions lors de l'analyse d'une commande ping."""
        # Configurer le mock pour lever une exception
        mock_run.side_effect = Exception("Process error")
        
        # Test avec une exception
        with self.assertRaises(NetworkAnalysisError):
            self.service.analyze_ping("google.com")
    
    @patch('subprocess.run')
    def test_analyze_traceroute(self, mock_run):
        """Teste l'analyse d'une commande traceroute."""
        # Configurer le mock pour subprocess.run
        mock_process = MagicMock()
        mock_process.stdout = "traceroute to google.com (142.250.74.110), 30 hops max, 60 byte packets\n" \
                             " 1  _gateway (192.168.1.1)  3.171 ms  3.047 ms  2.988 ms\n" \
                             " 2  10.0.0.1 (10.0.0.1)  12.200 ms  12.113 ms  12.075 ms\n" \
                             " 3  * * *\n" \
                             " 4  par21s19-in-f14.1e100.net (142.250.74.110)  13.655 ms  13.614 ms  13.574 ms"
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        # Test avec une commande traceroute valide
        with patch.object(self.service, 'analyze_traceroute_output', return_value={
            "analyse": {
                "hops": [
                    {"hop": 1, "host": "_gateway", "ip": "192.168.1.1", "time": 3.171},
                    {"hop": 2, "host": "", "ip": "10.0.0.1", "time": 12.200},
                    {"hop": 3, "host": "", "ip": "", "time": None},
                    {"hop": 4, "host": "par21s19-in-f14.1e100.net", "ip": "142.250.74.110", "time": 13.655}
                ]
            }
        }):
            result = self.service.analyze_traceroute("google.com")
            
            self.assertIn("analyse", result)
            self.assertIn("hops", result["analyse"])
            self.assertEqual(len(result["analyse"]["hops"]), 4)
    
    @patch('subprocess.run')
    def test_analyze_ifconfig(self, mock_run):
        """Teste l'analyse d'une commande ifconfig."""
        # Configurer le mock pour subprocess.run
        mock_process = MagicMock()
        mock_process.stdout = "eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500\n" \
                             "        inet 192.168.1.100  netmask 255.255.255.0  broadcast 192.168.1.255\n" \
                             "        inet6 fe80::1234:5678:9abc:def0  prefixlen 64  scopeid 0x20<link>\n" \
                             "        ether 00:11:22:33:44:55  txqueuelen 1000  (Ethernet)\n" \
                             "        RX packets 12345  bytes 1234567 (1.2 MB)\n" \
                             "        RX errors 0  dropped 0  overruns 0  frame 0\n" \
                             "        TX packets 67890  bytes 6789012 (6.7 MB)\n" \
                             "        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0"
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        # Test avec une commande ifconfig valide
        with patch.object(self.service, 'analyze_ifconfig_output', return_value={
            "analyse": {
                "interfaces": {
                    "eth0": {
                        "ipv4": "192.168.1.100",
                        "ipv6": "fe80::1234:5678:9abc:def0",
                        "mac": "00:11:22:33:44:55",
                        "mtu": 1500,
                        "rx_packets": 12345,
                        "tx_packets": 67890
                    }
                }
            }
        }):
            result = self.service.analyze_ifconfig()
            
            self.assertIn("analyse", result)
            self.assertIn("interfaces", result["analyse"])
            self.assertIn("eth0", result["analyse"]["interfaces"])
            self.assertEqual(result["analyse"]["interfaces"]["eth0"]["ipv4"], "192.168.1.100")
    
    @patch('subprocess.run')
    def test_analyze_netstat(self, mock_run):
        """Teste l'analyse d'une commande netstat."""
        # Configurer le mock pour subprocess.run
        mock_process = MagicMock()
        mock_process.stdout = "Active Internet connections (w/o servers)\n" \
                             "Proto Recv-Q Send-Q Local Address           Foreign Address         State\n" \
                             "tcp        0      0 192.168.1.100:22        192.168.1.10:12345      ESTABLISHED\n" \
                             "tcp        0      0 192.168.1.100:80        192.168.1.20:54321      TIME_WAIT\n" \
                             "tcp6       0      0 ::1:631                 ::1:54321               ESTABLISHED\n"
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        # Test avec une commande netstat valide
        with patch.object(self.service, 'analyze_netstat_output', return_value={
            "analyse": {
                "connections": [
                    {"proto": "tcp", "local_address": "192.168.1.100:22", "foreign_address": "192.168.1.10:12345", "state": "ESTABLISHED"},
                    {"proto": "tcp", "local_address": "192.168.1.100:80", "foreign_address": "192.168.1.20:54321", "state": "TIME_WAIT"},
                    {"proto": "tcp6", "local_address": "::1:631", "foreign_address": "::1:54321", "state": "ESTABLISHED"}
                ]
            }
        }):
            result = self.service.analyze_netstat()
            
            self.assertIn("analyse", result)
            self.assertIn("connections", result["analyse"])
            self.assertEqual(len(result["analyse"]["connections"]), 3)
    
    @patch('subprocess.run')
    def test_analyze_nmap(self, mock_run):
        """Teste l'analyse d'une commande nmap."""
        # Configurer le mock pour subprocess.run
        mock_process = MagicMock()
        mock_process.stdout = "Starting Nmap 7.80 ( https://nmap.org ) at 2023-10-15 12:00 CEST\n" \
                             "Nmap scan report for google.com (142.250.74.110)\n" \
                             "Host is up (0.010s latency).\n" \
                             "rDNS record for 142.250.74.110: par10s41-in-f14.1e100.net\n" \
                             "Not shown: 998 filtered ports\n" \
                             "PORT    STATE SERVICE\n" \
                             "80/tcp  open  http\n" \
                             "443/tcp open  https\n" \
                             "\n" \
                             "Nmap done: 1 IP address (1 host up) scanned in 5.20 seconds"
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        # Test avec une commande nmap valide
        with patch.object(self.service, 'analyze_nmap_output', return_value={
            "analyse": {
                "hosts": [
                    {
                        "host": "google.com",
                        "ip": "142.250.74.110",
                        "status": "up",
                        "latency": 0.010,
                        "ports": [
                            {"port": 80, "protocol": "tcp", "state": "open", "service": "http"},
                            {"port": 443, "protocol": "tcp", "state": "open", "service": "https"}
                        ]
                    }
                ]
            }
        }):
            result = self.service.analyze_nmap("google.com")
            
            self.assertIn("analyse", result)
            self.assertIn("hosts", result["analyse"])
            self.assertEqual(len(result["analyse"]["hosts"]), 1)
            self.assertIn("ports", result["analyse"]["hosts"][0])
            self.assertEqual(len(result["analyse"]["hosts"][0]["ports"]), 2)


if __name__ == "__main__":
    unittest.main()

