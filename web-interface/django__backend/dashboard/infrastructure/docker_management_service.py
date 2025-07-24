"""
Service de gestion des conteneurs Docker pour le dashboard.

Ce service permet de gérer les conteneurs Docker depuis l'interface dashboard,
offrant des fonctionnalités de démarrage, arrêt, redémarrage et surveillance.
"""

import logging
import asyncio
import subprocess
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ContainerAction(Enum):
    """Actions possibles sur les conteneurs."""
    START = "start"
    STOP = "stop"
    RESTART = "restart"
    PAUSE = "pause"
    UNPAUSE = "unpause"
    REMOVE = "remove"


class ServiceGroup(Enum):
    """Groupes de services."""
    BASE = "base"           # PostgreSQL, Redis, Django
    SECURITY = "security"   # Suricata, Elasticsearch, Kibana, Fail2ban
    MONITORING = "monitoring"  # Netdata, ntopng, HAProxy, Prometheus, Grafana
    TRAFFIC = "traffic"     # Traffic Control (QoS)
    ALL = "all"


@dataclass
class ContainerInfo:
    """Informations d'un conteneur."""
    name: str
    status: str
    image: str
    ports: List[str]
    created: str
    size: str
    networks: List[str]
    service_group: str
    compose_service: Optional[str] = None


@dataclass
class ServiceOperation:
    """Résultat d'une opération sur un service."""
    service_name: str
    action: str
    success: bool
    message: str
    execution_time: float
    details: Optional[Dict[str, Any]] = None


class DockerManagementService:
    """
    Service de gestion des conteneurs Docker pour le dashboard.
    
    Permet de contrôler les services Docker du NMS depuis l'interface web.
    """
    
    def __init__(self, script_path: str = "/home/adjada/network-management-system"):
        """
        Initialise le service de gestion Docker.
        
        Args:
            script_path: Chemin vers le script de gestion NMS
        """
        self.script_path = script_path
        self.nms_manager = f"{script_path}/nms-manager.sh"
        
        # Mapping des services vers leurs groupes
        self.service_groups = {
            "base": ["postgres", "redis", "django", "celery"],
            "security": ["suricata", "elasticsearch", "kibana", "fail2ban"],
            "monitoring": ["netdata", "ntopng", "haproxy", "prometheus", "grafana"],
            "traffic": ["traffic-control"]
        }
        
        # Services critiques qui nécessitent une attention particulière
        self.critical_services = ["postgres", "redis", "django"]
        
        # Ports par défaut des services
        self.service_ports = {
            "postgres": "5432",
            "redis": "6379", 
            "django": "8000",
            "elasticsearch": "9200",
            "kibana": "5601",
            "prometheus": "9090",
            "grafana": "3001",
            "netdata": "19999",
            "ntopng": "3000",
            "haproxy": "1936",
            "suricata": "8068",
            "fail2ban": "5001"
        }
    
    async def get_containers_status(self) -> Dict[str, Any]:
        """
        Récupère le statut de tous les conteneurs Docker.
        
        Returns:
            Statut des conteneurs par groupe
        """
        try:
            # Récupérer la liste des conteneurs Docker
            cmd = ["docker", "ps", "-a", "--format", "json"]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Erreur Docker ps: {stderr.decode()}")
                return self._get_fallback_status()
            
            # Parser les résultats
            containers = []
            for line in stdout.decode().strip().split('\n'):
                if line:
                    try:
                        container_data = json.loads(line)
                        container = self._parse_container_info(container_data)
                        if container:
                            containers.append(container)
                    except json.JSONDecodeError:
                        continue
            
            # Organiser par groupes
            status_by_group = self._organize_by_groups(containers)
            
            # Ajouter les métriques globales
            status_by_group['global_metrics'] = self._calculate_global_metrics(containers)
            status_by_group['last_updated'] = datetime.now().isoformat()
            
            return status_by_group
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du statut des conteneurs: {e}")
            return self._get_fallback_status()
    
    def _parse_container_info(self, container_data: Dict[str, Any]) -> Optional[ContainerInfo]:
        """Parse les informations d'un conteneur."""
        try:
            name = container_data.get('Names', '')
            if not name.startswith('nms-'):
                return None
            
            # Extraire le nom du service
            service_name = name.replace('nms-', '').replace('-1', '')
            
            # Déterminer le groupe
            service_group = self._get_service_group(service_name)
            
            return ContainerInfo(
                name=name,
                status=container_data.get('State', 'unknown'),
                image=container_data.get('Image', ''),
                ports=self._parse_ports(container_data.get('Ports', '')),
                created=container_data.get('CreatedAt', ''),
                size=container_data.get('Size', ''),
                networks=self._parse_networks(container_data.get('Networks', '')),
                service_group=service_group,
                compose_service=service_name
            )
            
        except Exception as e:
            logger.error(f"Erreur lors du parsing du conteneur: {e}")
            return None
    
    def _get_service_group(self, service_name: str) -> str:
        """Détermine le groupe d'un service."""
        for group, services in self.service_groups.items():
            if any(service in service_name for service in services):
                return group
        return "other"
    
    def _parse_ports(self, ports_str: str) -> List[str]:
        """Parse la chaîne des ports."""
        if not ports_str:
            return []
        return [p.strip() for p in ports_str.split(',') if p.strip()]
    
    def _parse_networks(self, networks_str: str) -> List[str]:
        """Parse la chaîne des réseaux."""
        if not networks_str:
            return []
        return [n.strip() for n in networks_str.split(',') if n.strip()]
    
    def _organize_by_groups(self, containers: List[ContainerInfo]) -> Dict[str, Any]:
        """Organise les conteneurs par groupes."""
        groups = {group.value: [] for group in ServiceGroup if group != ServiceGroup.ALL}
        groups['other'] = []
        
        for container in containers:
            group_name = container.service_group
            if group_name in groups:
                groups[group_name].append({
                    'name': container.name,
                    'service': container.compose_service,
                    'status': container.status,
                    'image': container.image,
                    'ports': container.ports,
                    'created': container.created,
                    'networks': container.networks,
                    'is_critical': container.compose_service in self.critical_services
                })
        
        return groups
    
    def _calculate_global_metrics(self, containers: List[ContainerInfo]) -> Dict[str, Any]:
        """Calcule les métriques globales."""
        total = len(containers)
        running = sum(1 for c in containers if c.status in ['running', 'Up'])
        stopped = sum(1 for c in containers if c.status in ['exited', 'stopped'])
        
        return {
            'total_containers': total,
            'running_containers': running,
            'stopped_containers': stopped,
            'availability_percentage': round((running / total) * 100, 2) if total > 0 else 0,
            'critical_services_status': self._get_critical_services_status(containers)
        }
    
    def _get_critical_services_status(self, containers: List[ContainerInfo]) -> Dict[str, str]:
        """Vérifie le statut des services critiques."""
        critical_status = {}
        for service in self.critical_services:
            matching_containers = [c for c in containers if service in c.name]
            if matching_containers:
                critical_status[service] = matching_containers[0].status
            else:
                critical_status[service] = "not_found"
        return critical_status
    
    def _get_fallback_status(self) -> Dict[str, Any]:
        """Retourne un statut de fallback en cas d'erreur."""
        return {
            'error': 'Impossible de récupérer le statut des conteneurs',
            'global_metrics': {
                'total_containers': 0,
                'running_containers': 0,
                'stopped_containers': 0,
                'availability_percentage': 0
            },
            'last_updated': datetime.now().isoformat()
        }
    
    async def manage_service(self, service_name: str, action: ContainerAction) -> ServiceOperation:
        """
        Gère un service spécifique.
        
        Args:
            service_name: Nom du service
            action: Action à effectuer
            
        Returns:
            Résultat de l'opération
        """
        start_time = datetime.now()
        
        try:
            # Valider le service
            if not self._is_valid_service(service_name):
                return ServiceOperation(
                    service_name=service_name,
                    action=action.value,
                    success=False,
                    message=f"Service '{service_name}' non reconnu",
                    execution_time=0.0
                )
            
            # Vérifier les permissions pour les services critiques
            if service_name in self.critical_services and action in [ContainerAction.STOP, ContainerAction.REMOVE]:
                logger.warning(f"Tentative d'action {action.value} sur service critique {service_name}")
            
            # Exécuter l'action
            success, message, details = await self._execute_service_action(service_name, action)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return ServiceOperation(
                service_name=service_name,
                action=action.value,
                success=success,
                message=message,
                execution_time=execution_time,
                details=details
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Erreur lors de la gestion du service {service_name}: {e}")
            
            return ServiceOperation(
                service_name=service_name,
                action=action.value,
                success=False,
                message=f"Erreur lors de l'exécution: {str(e)}",
                execution_time=execution_time
            )
    
    async def _execute_service_action(self, service_name: str, action: ContainerAction) -> tuple[bool, str, Optional[Dict]]:
        """Exécute une action sur un service."""
        try:
            # Construire la commande
            if action == ContainerAction.START:
                cmd = [self.nms_manager, "start-service", service_name]
            elif action == ContainerAction.STOP:
                cmd = [self.nms_manager, "stop-service", service_name]
            elif action == ContainerAction.RESTART:
                cmd = [self.nms_manager, "restart-service", service_name]
            else:
                # Actions Docker directes
                container_name = f"nms-{service_name}"
                if action == ContainerAction.PAUSE:
                    cmd = ["docker", "pause", container_name]
                elif action == ContainerAction.UNPAUSE:
                    cmd = ["docker", "unpause", container_name]
                elif action == ContainerAction.REMOVE:
                    cmd = ["docker", "rm", "-f", container_name]
                else:
                    return False, f"Action {action.value} non supportée", None
            
            # Exécuter la commande
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return True, f"Action {action.value} réussie sur {service_name}", {
                    'stdout': stdout.decode(),
                    'command': ' '.join(cmd)
                }
            else:
                return False, f"Échec de l'action {action.value}: {stderr.decode()}", {
                    'stderr': stderr.decode(),
                    'command': ' '.join(cmd)
                }
                
        except Exception as e:
            return False, f"Erreur d'exécution: {str(e)}", None
    
    def _is_valid_service(self, service_name: str) -> bool:
        """Vérifie si un service est valide."""
        all_services = []
        for services in self.service_groups.values():
            all_services.extend(services)
        return service_name in all_services
    
    async def manage_service_group(self, group: ServiceGroup, action: ContainerAction) -> List[ServiceOperation]:
        """
        Gère un groupe de services.
        
        Args:
            group: Groupe de services
            action: Action à effectuer
            
        Returns:
            Liste des résultats d'opération
        """
        if group == ServiceGroup.ALL:
            services = []
            for group_services in self.service_groups.values():
                services.extend(group_services)
        else:
            services = self.service_groups.get(group.value, [])
        
        # Exécuter les actions en parallèle (avec limite)
        semaphore = asyncio.Semaphore(3)  # Limite à 3 actions simultanées
        
        async def manage_single_service(service):
            async with semaphore:
                return await self.manage_service(service, action)
        
        tasks = [manage_single_service(service) for service in services]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Traiter les résultats
        operations = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                operations.append(ServiceOperation(
                    service_name=services[i],
                    action=action.value,
                    success=False,
                    message=f"Exception: {str(result)}",
                    execution_time=0.0
                ))
            else:
                operations.append(result)
        
        return operations
    
    async def get_service_logs(self, service_name: str, lines: int = 100) -> Dict[str, Any]:
        """
        Récupère les logs d'un service.
        
        Args:
            service_name: Nom du service
            lines: Nombre de lignes à récupérer
            
        Returns:
            Logs du service
        """
        try:
            container_name = f"nms-{service_name}"
            cmd = ["docker", "logs", "--tail", str(lines), container_name]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return {
                    'success': True,
                    'service': service_name,
                    'logs': stdout.decode(),
                    'lines_requested': lines,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'service': service_name,
                    'error': stderr.decode(),
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des logs de {service_name}: {e}")
            return {
                'success': False,
                'service': service_name,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_available_actions(self, service_name: str) -> List[str]:
        """
        Retourne les actions disponibles pour un service.
        
        Args:
            service_name: Nom du service
            
        Returns:
            Liste des actions disponibles
        """
        base_actions = [ContainerAction.START.value, ContainerAction.STOP.value, ContainerAction.RESTART.value]
        
        if service_name in self.critical_services:
            # Services critiques: actions limitées
            return [ContainerAction.START.value, ContainerAction.RESTART.value]
        else:
            # Services non-critiques: toutes les actions
            return base_actions + [
                ContainerAction.PAUSE.value,
                ContainerAction.UNPAUSE.value,
                ContainerAction.REMOVE.value
            ]
    
    async def get_container_stats(self, service_name: str) -> Dict[str, Any]:
        """
        Récupère les statistiques d'un conteneur.
        
        Args:
            service_name: Nom du service
            
        Returns:
            Statistiques du conteneur
        """
        try:
            container_name = f"nms-{service_name}"
            cmd = ["docker", "stats", "--no-stream", "--format", "json", container_name]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                stats_data = json.loads(stdout.decode().strip())
                return {
                    'success': True,
                    'service': service_name,
                    'stats': stats_data,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'service': service_name,
                    'error': stderr.decode(),
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des stats de {service_name}: {e}")
            return {
                'success': False,
                'service': service_name,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


# Instance globale du service
docker_management_service = DockerManagementService()