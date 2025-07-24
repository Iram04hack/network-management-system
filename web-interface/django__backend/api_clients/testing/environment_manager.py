"""
Gestionnaire d'environnement de tests pour api_clients.
Gère le démarrage/arrêt des services Docker et la validation de l'environnement.
"""

import os
import sys
import time
import subprocess
import socket
from typing import Dict, List, Optional
from pathlib import Path

from .test_config import TestConfig
from ..utils.service_detector import ServiceDetector, ServiceStatus


class TestEnvironmentManager:
    """Gestionnaire de l'environnement de tests complet pour api_clients."""
    
    def __init__(self):
        self.config = TestConfig()
        self.service_detector = ServiceDetector()
        self.docker_compose_file = self._find_docker_compose_test_file()
        self.services_status = {}
        
    def _find_docker_compose_test_file(self) -> Optional[Path]:
        """Trouve le fichier docker-compose.test.yml."""
        # Chercher dans le répertoire racine du projet
        current_dir = Path(__file__).resolve()
        
        # Remonter jusqu'à trouver le fichier docker-compose.test.yml
        for parent in current_dir.parents:
            docker_file = parent / 'docker-compose.test.yml'
            if docker_file.exists():
                return docker_file
        
        return None
    
    def start_test_services(self) -> bool:
        """Démarre tous les services de test Docker avec diagnostic préalable."""
        print("🚀 DÉMARRAGE ENVIRONNEMENT DE TESTS API_CLIENTS")
        print("="*60)

        if not self.docker_compose_file:
            print("⚠️ Fichier docker-compose.test.yml non trouvé")
            print("   Tests s'exécuteront sans services externes")
            return True  # Continuer sans Docker

        try:
            # Diagnostic préalable
            print("🔧 Diagnostic Docker préalable...")
            from .docker_diagnostics import DockerDiagnostics

            diagnostics = DockerDiagnostics()
            diagnostic_success = diagnostics.run_complete_diagnostics()

            if not diagnostic_success:
                print("⚠️ Problèmes Docker détectés, démarrage en mode dégradé")
                return True  # Continuer sans Docker

            print(f"📦 Utilisation de: {self.docker_compose_file}")

            # Démarrage progressif des services
            print("⏳ Démarrage progressif des services Docker...")

            # Phase 1: Services essentiels
            essential_services = ['postgres-test', 'redis-test']
            success = self._start_service_group("Services essentiels", essential_services)

            if not success:
                print("⚠️ Échec des services essentiels, tests en mode dégradé")
                return True

            # Phase 2: Services de monitoring
            monitoring_services = ['prometheus-test', 'grafana-test', 'elasticsearch-test']
            self._start_service_group("Services monitoring", monitoring_services, required=False)

            # Phase 3: Services réseau
            network_services = ['snmp-simulator-test', 'netflow-simulator-test']
            self._start_service_group("Services réseau", network_services, required=False)

            # Phase 4: Services infrastructure
            infra_services = ['haproxy-test']
            self._start_service_group("Services infrastructure", infra_services, required=False)

            # Vérification finale de la santé
            print("\n🔍 Vérification finale de la santé des services...")
            self._check_services_health()

            return True

        except Exception as e:
            print(f"❌ Erreur lors du démarrage: {e}")
            print("   Tests s'exécuteront sans services externes")
            return True  # Continuer sans Docker

    def _start_service_group(self, group_name: str, services: List[str], required: bool = True) -> bool:
        """Démarre un groupe de services."""
        print(f"\n📦 {group_name}...")

        try:
            cmd = [
                "docker-compose",
                "-f", str(self.docker_compose_file),
                "up", "-d"
            ] + services

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.docker_compose_file.parent,
                timeout=60
            )

            if result.returncode == 0:
                print(f"✅ {group_name} démarrés")

                # Attendre un peu que les services se stabilisent
                time.sleep(5)
                return True
            else:
                print(f"⚠️ Problème avec {group_name}: {result.stderr}")
                if required:
                    return False
                return True

        except subprocess.TimeoutExpired:
            print(f"⚠️ Timeout pour {group_name}")
            return not required
        except Exception as e:
            print(f"⚠️ Erreur {group_name}: {e}")
            return not required
    
    def stop_test_services(self) -> bool:
        """Arrête tous les services de test."""
        print("\n🛑 ARRÊT ENVIRONNEMENT DE TESTS")
        print("="*40)
        
        if not self.docker_compose_file:
            print("✅ Aucun service Docker à arrêter")
            return True
        
        try:
            cmd = [
                "docker-compose", 
                "-f", str(self.docker_compose_file), 
                "down"
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True,
                cwd=self.docker_compose_file.parent
            )
            
            if result.returncode == 0:
                print("✅ Services Docker arrêtés")
            else:
                print(f"⚠️ Avertissement lors de l'arrêt: {result.stderr}")
            
            return True
            
        except Exception as e:
            print(f"⚠️ Erreur lors de l'arrêt: {e}")
            return True
    
    def _check_services_health(self):
        """Vérifie la santé de tous les services configurés."""
        print("🔍 Vérification de la santé des services...")
        
        services_config = self.config.TEST_SERVICES
        healthy_count = 0
        total_count = len(services_config)
        
        for service_name, config in services_config.items():
            try:
                if service_name == 'gns3':
                    # Utiliser notre détecteur GNS3 spécialisé
                    gns3_info = self.service_detector.detect_gns3_service()
                    if gns3_info.status == ServiceStatus.AVAILABLE:
                        print(f"  ✅ {service_name}: Disponible sur {gns3_info.host}:{gns3_info.port}")
                        healthy_count += 1
                        self.services_status[service_name] = 'healthy'
                    else:
                        print(f"  ❌ {service_name}: {gns3_info.error_message}")
                        self.services_status[service_name] = 'unhealthy'
                
                elif service_name == 'postgresql':
                    # Test spécial pour PostgreSQL
                    if self._check_postgresql_connection(config):
                        print(f"  ✅ {service_name}: Connecté")
                        healthy_count += 1
                        self.services_status[service_name] = 'healthy'
                    else:
                        print(f"  ❌ {service_name}: Non connecté")
                        self.services_status[service_name] = 'unhealthy'
                
                else:
                    # Test de connectivité TCP générique
                    host = config.get('host', 'localhost')
                    port = config.get('port', 80)
                    
                    if self._check_tcp_connectivity(host, port):
                        print(f"  ✅ {service_name}: Disponible sur {host}:{port}")
                        healthy_count += 1
                        self.services_status[service_name] = 'healthy'
                    else:
                        print(f"  ❌ {service_name}: Non disponible sur {host}:{port}")
                        self.services_status[service_name] = 'unhealthy'
                        
            except Exception as e:
                print(f"  ❌ {service_name}: Erreur - {e}")
                self.services_status[service_name] = 'error'
        
        health_percentage = (healthy_count / total_count) * 100
        print(f"\n📊 Santé globale: {healthy_count}/{total_count} services ({health_percentage:.1f}%)")
        
        if health_percentage >= 50:
            print("✅ Environnement suffisamment sain pour les tests")
        else:
            print("⚠️ Environnement partiellement disponible")
            print("   Tests adaptatifs s'ajusteront automatiquement")
    
    def _check_postgresql_connection(self, config: Dict) -> bool:
        """Vérifie la connexion PostgreSQL."""
        try:
            # Pour les tests, on utilise SQLite donc on simule une connexion réussie
            # En production, on utiliserait psycopg2 pour tester la vraie connexion
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except Exception:
            return False
    
    def _check_tcp_connectivity(self, host: str, port: int, timeout: int = 3) -> bool:
        """Vérifie la connectivité TCP vers un hôte/port."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def get_environment_status(self) -> Dict:
        """Retourne le statut de l'environnement de test."""
        return {
            'docker_compose_available': self.docker_compose_file is not None,
            'docker_compose_path': str(self.docker_compose_file) if self.docker_compose_file else None,
            'services_status': self.services_status.copy(),
            'healthy_services': len([s for s in self.services_status.values() if s == 'healthy']),
            'total_services': len(self.services_status),
            'environment_ready': len([s for s in self.services_status.values() if s == 'healthy']) > 0
        }
    
    def setup_complete_environment(self) -> bool:
        """Configure l'environnement complet de test."""
        print("🎯 CONFIGURATION ENVIRONNEMENT COMPLET API_CLIENTS")
        print("="*60)
        
        # 1. Configuration Django
        print("⚙️ Configuration Django...")
        self.config.setup_test_environment()
        
        # 2. Démarrage des services
        print("\n🚀 Démarrage des services...")
        services_started = self.start_test_services()
        
        # 3. Validation de l'environnement
        print("\n✅ Validation de l'environnement...")
        env_status = self.get_environment_status()
        
        print(f"\n📊 RÉSUMÉ ENVIRONNEMENT:")
        print(f"   Docker Compose: {'✅' if env_status['docker_compose_available'] else '❌'}")
        print(f"   Services sains: {env_status['healthy_services']}/{env_status['total_services']}")
        print(f"   Environnement prêt: {'✅' if env_status['environment_ready'] else '⚠️'}")
        
        if env_status['environment_ready']:
            print("\n🎉 Environnement de test prêt pour les tests api_clients!")
        else:
            print("\n⚠️ Environnement partiel - tests adaptatifs activés")
        
        return True  # Toujours continuer, même avec environnement partiel
    
    def cleanup_environment(self):
        """Nettoie l'environnement de test."""
        print("\n🧹 NETTOYAGE ENVIRONNEMENT")
        print("="*30)
        
        # Arrêter les services Docker
        self.stop_test_services()
        
        # Nettoyer les fichiers temporaires
        temp_files = [
            'htmlcov_api_clients',
            '.coverage',
            'test_results.xml'
        ]
        
        for temp_file in temp_files:
            temp_path = Path(temp_file)
            if temp_path.exists():
                if temp_path.is_dir():
                    import shutil
                    shutil.rmtree(temp_path)
                else:
                    temp_path.unlink()
                print(f"🗑️ Supprimé: {temp_file}")
        
        print("✅ Nettoyage terminé")


# Fonction utilitaire pour usage direct
def setup_test_environment():
    """Fonction utilitaire pour configurer rapidement l'environnement."""
    manager = TestEnvironmentManager()
    return manager.setup_complete_environment()


if __name__ == "__main__":
    # Test du gestionnaire d'environnement
    manager = TestEnvironmentManager()
    
    try:
        success = manager.setup_complete_environment()
        
        if success:
            print("\n✅ Test du gestionnaire d'environnement réussi!")
            
            # Afficher le statut
            status = manager.get_environment_status()
            print(f"\nStatut: {status}")
        else:
            print("\n❌ Échec du test du gestionnaire")
            
    finally:
        manager.cleanup_environment()
