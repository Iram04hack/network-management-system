#!/usr/bin/env python
"""
Script de diagnostic Docker pour l'environnement de tests api_clients.
Identifie et résout les problèmes de démarrage Docker.
"""

import subprocess
import time
import json
import socket
from typing import Dict, List, Tuple, Optional
from pathlib import Path


class DockerDiagnostics:
    """Diagnostics et résolution des problèmes Docker pour les tests."""
    
    def __init__(self):
        self.docker_compose_file = self._find_docker_compose_test_file()
        self.issues_found = []
        self.fixes_applied = []
    
    def _find_docker_compose_test_file(self) -> Optional[Path]:
        """Trouve le fichier docker-compose.test.yml."""
        current_dir = Path(__file__).resolve()
        
        for parent in current_dir.parents:
            docker_file = parent / 'docker-compose.test.yml'
            if docker_file.exists():
                return docker_file
        
        return None
    
    def run_complete_diagnostics(self) -> bool:
        """Exécute un diagnostic complet de l'environnement Docker."""
        print("🔧 DIAGNOSTIC DOCKER POUR TESTS API_CLIENTS")
        print("="*60)
        
        if not self.docker_compose_file:
            print("❌ Fichier docker-compose.test.yml non trouvé")
            return False
        
        print(f"📁 Fichier Docker Compose: {self.docker_compose_file}")
        
        # 1. Vérifier Docker
        if not self._check_docker_availability():
            return False
        
        # 2. Vérifier les conflits de ports
        self._check_port_conflicts()
        
        # 3. Vérifier les réseaux existants
        self._check_network_conflicts()
        
        # 4. Vérifier les volumes et dépendances
        self._check_volumes_and_dependencies()
        
        # 5. Nettoyer les ressources conflictuelles
        self._cleanup_conflicting_resources()
        
        # 6. Test de démarrage progressif
        success = self._test_progressive_startup()
        
        # 7. Rapport final
        self._generate_diagnostics_report()
        
        return success
    
    def _check_docker_availability(self) -> bool:
        """Vérifie que Docker est disponible et fonctionnel."""
        print("\n🐳 Vérification de Docker...")
        
        try:
            # Test Docker daemon
            result = subprocess.run(['docker', 'version'], capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                print(f"❌ Docker non disponible: {result.stderr}")
                return False
            
            print("✅ Docker daemon disponible")
            
            # Test Docker Compose
            result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                print(f"❌ Docker Compose non disponible: {result.stderr}")
                return False
            
            print("✅ Docker Compose disponible")
            
            # Vérifier l'espace disque
            result = subprocess.run(['docker', 'system', 'df'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("✅ Espace disque Docker vérifié")
            
            return True
            
        except subprocess.TimeoutExpired:
            print("❌ Timeout lors de la vérification Docker")
            return False
        except Exception as e:
            print(f"❌ Erreur Docker: {e}")
            return False
    
    def _check_port_conflicts(self):
        """Vérifie les conflits de ports avec les services existants."""
        print("\n🔌 Vérification des conflits de ports...")
        
        test_ports = [5433, 6380, 9091, 3002, 9201, 1162, 8081, 8405, 9996]
        
        for port in test_ports:
            if self._is_port_in_use(port):
                print(f"⚠️ Port {port} déjà utilisé")
                self.issues_found.append(f"Port {port} en conflit")
                
                # Identifier le processus utilisant le port
                process_info = self._get_process_using_port(port)
                if process_info:
                    print(f"   Utilisé par: {process_info}")
            else:
                print(f"✅ Port {port} disponible")
    
    def _is_port_in_use(self, port: int) -> bool:
        """Vérifie si un port est utilisé."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                return result == 0
        except Exception:
            return False
    
    def _get_process_using_port(self, port: int) -> Optional[str]:
        """Identifie le processus utilisant un port."""
        try:
            result = subprocess.run(['lsof', '-i', f':{port}'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    return lines[1].split()[0]  # Nom du processus
        except Exception:
            pass
        return None
    
    def _check_network_conflicts(self):
        """Vérifie les conflits de réseaux Docker."""
        print("\n🌐 Vérification des réseaux Docker...")
        
        try:
            result = subprocess.run(['docker', 'network', 'ls', '--format', 'json'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                networks = []
                for line in result.stdout.strip().split('\n'):
                    if line:
                        try:
                            network = json.loads(line)
                            networks.append(network['Name'])
                        except json.JSONDecodeError:
                            pass
                
                test_networks = ['nms-backend-test', 'nms-monitoring-test', 
                               'nms-infrastructure-test', 'nms-network-test']
                
                for network in test_networks:
                    if network in networks:
                        print(f"⚠️ Réseau {network} existe déjà")
                        self.issues_found.append(f"Réseau {network} en conflit")
                    else:
                        print(f"✅ Réseau {network} disponible")
            
        except Exception as e:
            print(f"⚠️ Erreur lors de la vérification des réseaux: {e}")
    
    def _check_volumes_and_dependencies(self):
        """Vérifie les volumes et dépendances."""
        print("\n📁 Vérification des volumes et dépendances...")
        
        # Vérifier que les répertoires de configuration existent ou peuvent être créés
        config_dirs = [
            'config/prometheus',
            'config/haproxy/test',
            'config/fail2ban/test',
            'config/suricata/test',
            'data/gns3/test',
            'data/fail2ban/test',
            'data/suricata/test'
        ]
        
        base_dir = self.docker_compose_file.parent
        
        for config_dir in config_dirs:
            full_path = base_dir / config_dir
            if not full_path.exists():
                print(f"⚠️ Répertoire manquant: {config_dir}")
                self.issues_found.append(f"Répertoire manquant: {config_dir}")
            else:
                print(f"✅ Répertoire existe: {config_dir}")
    
    def _cleanup_conflicting_resources(self):
        """Nettoie les ressources Docker conflictuelles."""
        print("\n🧹 Nettoyage des ressources conflictuelles...")
        
        try:
            # Arrêter les conteneurs de test existants
            result = subprocess.run([
                'docker-compose', '-f', str(self.docker_compose_file), 'down'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ Conteneurs de test arrêtés")
                self.fixes_applied.append("Conteneurs de test arrêtés")
            else:
                print(f"⚠️ Erreur lors de l'arrêt: {result.stderr}")
            
            # Nettoyer les réseaux orphelins
            result = subprocess.run(['docker', 'network', 'prune', '-f'], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ Réseaux orphelins nettoyés")
                self.fixes_applied.append("Réseaux orphelins nettoyés")
            
            # Nettoyer les volumes orphelins
            result = subprocess.run(['docker', 'volume', 'prune', '-f'], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ Volumes orphelins nettoyés")
                self.fixes_applied.append("Volumes orphelins nettoyés")
            
        except subprocess.TimeoutExpired:
            print("⚠️ Timeout lors du nettoyage")
        except Exception as e:
            print(f"⚠️ Erreur lors du nettoyage: {e}")
    
    def _test_progressive_startup(self) -> bool:
        """Test de démarrage progressif des services."""
        print("\n🚀 Test de démarrage progressif...")
        
        # Services essentiels d'abord
        essential_services = ['postgres-test', 'redis-test']
        
        try:
            # Démarrer les services essentiels
            print("📦 Démarrage des services essentiels...")
            result = subprocess.run([
                'docker-compose', '-f', str(self.docker_compose_file), 
                'up', '-d'
            ] + essential_services, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                print(f"❌ Échec du démarrage des services essentiels: {result.stderr}")
                return False
            
            print("✅ Services essentiels démarrés")
            
            # Attendre que les services soient prêts
            print("⏳ Attente de la disponibilité des services...")
            time.sleep(10)
            
            # Vérifier la santé des services essentiels
            healthy_services = self._check_services_health(essential_services)
            
            if len(healthy_services) == len(essential_services):
                print("✅ Tous les services essentiels sont sains")
                return True
            else:
                print(f"⚠️ Seulement {len(healthy_services)}/{len(essential_services)} services sains")
                return False
            
        except subprocess.TimeoutExpired:
            print("❌ Timeout lors du démarrage progressif")
            return False
        except Exception as e:
            print(f"❌ Erreur lors du démarrage progressif: {e}")
            return False
    
    def _check_services_health(self, services: List[str]) -> List[str]:
        """Vérifie la santé des services spécifiés."""
        healthy_services = []
        
        for service in services:
            try:
                result = subprocess.run([
                    'docker-compose', '-f', str(self.docker_compose_file),
                    'ps', service
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0 and 'Up' in result.stdout:
                    print(f"  ✅ {service}: Sain")
                    healthy_services.append(service)
                else:
                    print(f"  ❌ {service}: Problème")
                    
            except Exception as e:
                print(f"  ❌ {service}: Erreur - {e}")
        
        return healthy_services
    
    def _generate_diagnostics_report(self):
        """Génère le rapport de diagnostic."""
        print("\n" + "="*60)
        print("📊 RAPPORT DE DIAGNOSTIC DOCKER")
        print("="*60)
        
        print(f"📁 Fichier Docker Compose: {self.docker_compose_file}")
        
        if self.issues_found:
            print(f"\n⚠️ PROBLÈMES IDENTIFIÉS ({len(self.issues_found)}):")
            for issue in self.issues_found:
                print(f"   - {issue}")
        else:
            print("\n✅ AUCUN PROBLÈME MAJEUR IDENTIFIÉ")
        
        if self.fixes_applied:
            print(f"\n🔧 CORRECTIONS APPLIQUÉES ({len(self.fixes_applied)}):")
            for fix in self.fixes_applied:
                print(f"   - {fix}")
        
        print(f"\n📋 RECOMMANDATIONS:")
        print(f"   1. Utiliser 'docker-compose -f {self.docker_compose_file.name} up -d' pour démarrer")
        print(f"   2. Surveiller les logs avec 'docker-compose -f {self.docker_compose_file.name} logs -f'")
        print(f"   3. Vérifier la santé avec 'docker-compose -f {self.docker_compose_file.name} ps'")


def main():
    """Fonction principale de diagnostic."""
    diagnostics = DockerDiagnostics()
    
    success = diagnostics.run_complete_diagnostics()
    
    if success:
        print("\n🎉 DIAGNOSTIC RÉUSSI!")
        print("✅ Environnement Docker prêt pour les tests api_clients")
        return 0
    else:
        print("\n⚠️ PROBLÈMES DÉTECTÉS")
        print("📋 Consultez le rapport ci-dessus pour les corrections nécessaires")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
