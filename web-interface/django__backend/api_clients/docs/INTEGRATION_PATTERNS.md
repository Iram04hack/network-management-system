# 🔗 Patterns d'Intégration - Module API_CLIENTS

## 🎯 Vue d'Ensemble

Ce document présente les patterns d'intégration recommandés pour utiliser efficacement le module `api_clients` dans l'architecture hexagonale du système NMS.

## 🏗️ Architecture Hexagonale

### Structure du Module

```
api_clients/
├── base.py                 # BaseAPIClient - Couche Infrastructure
├── domain/                 # Couche Domaine
│   ├── exceptions.py       # Exceptions métier
│   └── interfaces.py       # Interfaces/Ports
├── infrastructure/         # Couche Infrastructure
│   ├── http_adapter.py     # Adaptateur HTTP
│   └── retry_adapter.py    # Adaptateur Retry
├── network/               # Clients spécialisés
│   ├── gns3_client.py     # Client GNS3
│   ├── snmp_client.py     # Client SNMP
│   └── netflow_client.py  # Client Netflow
└── tests/                 # Tests exhaustifs
```

### Séparation des Responsabilités

```python
# ✅ CORRECT - Séparation claire des couches

# Couche Domaine - Logique métier pure
class NetworkDevice:
    def __init__(self, ip_address: str, device_type: str):
        self.ip_address = ip_address
        self.device_type = device_type
        self.status = "unknown"
    
    def is_reachable(self) -> bool:
        """Logique métier - indépendante de l'infrastructure."""
        return self.status in ["up", "running"]

# Couche Application - Orchestration
class NetworkMonitoringService:
    def __init__(self, snmp_client: SNMPClient):
        self.snmp_client = snmp_client  # Injection de dépendance
    
    def monitor_device(self, device: NetworkDevice) -> bool:
        """Service applicatif utilisant l'infrastructure."""
        try:
            response = self.snmp_client.get_system_status(device.ip_address)
            device.status = response["status"]
            return device.is_reachable()
        except APIClientException:
            device.status = "unreachable"
            return False

# Couche Infrastructure - Détails techniques
class SNMPClient(BaseAPIClient):
    def get_system_status(self, host: str) -> Dict[str, Any]:
        """Implémentation technique spécifique."""
        return self.get(f"status/{host}")
```

## 🔌 Patterns d'Injection de Dépendance

### Pattern Repository

```python
from abc import ABC, abstractmethod
from typing import List, Optional

# Interface (Port)
class NetworkDeviceRepository(ABC):
    @abstractmethod
    def find_all_devices(self) -> List[NetworkDevice]:
        pass
    
    @abstractmethod
    def find_device_by_ip(self, ip: str) -> Optional[NetworkDevice]:
        pass
    
    @abstractmethod
    def save_device(self, device: NetworkDevice) -> bool:
        pass

# Implémentation avec API Client (Adaptateur)
class SNMPNetworkDeviceRepository(NetworkDeviceRepository):
    def __init__(self, snmp_client: SNMPClient):
        self.snmp_client = snmp_client
    
    def find_all_devices(self) -> List[NetworkDevice]:
        """Récupère tous les devices via SNMP discovery."""
        response = self.snmp_client.get("discovery/scan")
        if response["success"]:
            devices = []
            for device_data in response["devices"]:
                device = NetworkDevice(
                    ip_address=device_data["ip"],
                    device_type=device_data["type"]
                )
                devices.append(device)
            return devices
        return []
    
    def find_device_by_ip(self, ip: str) -> Optional[NetworkDevice]:
        """Trouve un device spécifique par IP."""
        response = self.snmp_client.get(f"device/{ip}")
        if response["success"]:
            data = response["device"]
            return NetworkDevice(
                ip_address=data["ip"],
                device_type=data["type"]
            )
        return None
    
    def save_device(self, device: NetworkDevice) -> bool:
        """Sauvegarde les informations du device."""
        device_data = {
            "ip_address": device.ip_address,
            "device_type": device.device_type,
            "status": device.status
        }
        response = self.snmp_client.post("devices", json_data=device_data)
        return response["success"]

# Utilisation avec injection de dépendance
class DeviceManagementService:
    def __init__(self, device_repository: NetworkDeviceRepository):
        self.device_repository = device_repository
    
    def get_all_active_devices(self) -> List[NetworkDevice]:
        """Service métier utilisant le repository."""
        all_devices = self.device_repository.find_all_devices()
        return [device for device in all_devices if device.is_reachable()]
```

### Pattern Factory

```python
from enum import Enum

class ClientType(Enum):
    GNS3 = "gns3"
    SNMP = "snmp"
    NETFLOW = "netflow"

class APIClientFactory:
    """Factory pour créer les clients API appropriés."""
    
    @staticmethod
    def create_client(client_type: ClientType, config: Dict[str, Any]) -> BaseAPIClient:
        """Crée un client API selon le type demandé."""
        
        if client_type == ClientType.GNS3:
            return GNS3Client(
                base_url=config["base_url"],
                username=config.get("username"),
                password=config.get("password"),
                timeout=config.get("timeout", 30),
                max_retries=config.get("max_retries", 3)
            )
        
        elif client_type == ClientType.SNMP:
            return SNMPClient(
                base_url=config["base_url"],
                community=config.get("community", "public"),
                version=config.get("version", "2c"),
                timeout=config.get("timeout", 15)
            )
        
        elif client_type == ClientType.NETFLOW:
            return NetflowClient(
                base_url=config["base_url"],
                timeout=config.get("timeout", 60),
                max_retries=config.get("max_retries", 5)
            )
        
        else:
            raise ValueError(f"Type de client non supporté: {client_type}")

# Configuration centralisée
API_CONFIGS = {
    ClientType.GNS3: {
        "base_url": "http://gns3-server:3080",
        "username": "admin",
        "password": "admin",
        "timeout": 30,
        "max_retries": 3
    },
    ClientType.SNMP: {
        "base_url": "http://snmp-service:161",
        "community": "public",
        "version": "2c",
        "timeout": 15
    },
    ClientType.NETFLOW: {
        "base_url": "http://netflow-collector:9995",
        "timeout": 60,
        "max_retries": 5
    }
}

# Utilisation
def create_monitoring_service() -> NetworkMonitoringService:
    """Factory method pour créer le service de monitoring."""
    snmp_client = APIClientFactory.create_client(
        ClientType.SNMP, 
        API_CONFIGS[ClientType.SNMP]
    )
    return NetworkMonitoringService(snmp_client)
```

## 🔄 Patterns Asynchrones

### Pattern Observer pour Monitoring

```python
from abc import ABC, abstractmethod
from typing import List
import threading
import time

# Interface Observer
class NetworkEventObserver(ABC):
    @abstractmethod
    def on_device_status_changed(self, device: NetworkDevice, old_status: str, new_status: str):
        pass
    
    @abstractmethod
    def on_device_discovered(self, device: NetworkDevice):
        pass

# Implémentations concrètes
class LoggingObserver(NetworkEventObserver):
    def on_device_status_changed(self, device: NetworkDevice, old_status: str, new_status: str):
        print(f"📊 Device {device.ip_address}: {old_status} → {new_status}")
    
    def on_device_discovered(self, device: NetworkDevice):
        print(f"🔍 Nouveau device découvert: {device.ip_address} ({device.device_type})")

class AlertingObserver(NetworkEventObserver):
    def on_device_status_changed(self, device: NetworkDevice, old_status: str, new_status: str):
        if new_status == "down" and old_status == "up":
            self._send_alert(f"🚨 ALERTE: Device {device.ip_address} est tombé!")
    
    def on_device_discovered(self, device: NetworkDevice):
        self._send_notification(f"✅ Nouveau device: {device.ip_address}")
    
    def _send_alert(self, message: str):
        # Implémentation d'envoi d'alerte
        print(f"ALERT: {message}")
    
    def _send_notification(self, message: str):
        # Implémentation de notification
        print(f"NOTIF: {message}")

# Service Observable
class ObservableNetworkMonitor:
    def __init__(self, snmp_client: SNMPClient):
        self.snmp_client = snmp_client
        self.observers: List[NetworkEventObserver] = []
        self.devices: Dict[str, NetworkDevice] = {}
        self.running = False
    
    def add_observer(self, observer: NetworkEventObserver):
        """Ajoute un observer."""
        self.observers.append(observer)
    
    def remove_observer(self, observer: NetworkEventObserver):
        """Supprime un observer."""
        if observer in self.observers:
            self.observers.remove(observer)
    
    def _notify_status_changed(self, device: NetworkDevice, old_status: str, new_status: str):
        """Notifie tous les observers d'un changement de statut."""
        for observer in self.observers:
            observer.on_device_status_changed(device, old_status, new_status)
    
    def _notify_device_discovered(self, device: NetworkDevice):
        """Notifie tous les observers d'une découverte."""
        for observer in self.observers:
            observer.on_device_discovered(device)
    
    def start_monitoring(self, interval: int = 60):
        """Démarre le monitoring en arrière-plan."""
        self.running = True
        
        def monitor_loop():
            while self.running:
                try:
                    self._scan_and_update()
                    time.sleep(interval)
                except Exception as e:
                    print(f"Erreur monitoring: {e}")
                    time.sleep(10)  # Attente courte en cas d'erreur
        
        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()
    
    def stop_monitoring(self):
        """Arrête le monitoring."""
        self.running = False
    
    def _scan_and_update(self):
        """Scanne le réseau et met à jour les statuts."""
        # Découverte de nouveaux devices
        response = self.snmp_client.get("discovery/scan")
        if response["success"]:
            for device_data in response["devices"]:
                ip = device_data["ip"]
                
                if ip not in self.devices:
                    # Nouveau device découvert
                    device = NetworkDevice(ip, device_data["type"])
                    device.status = device_data["status"]
                    self.devices[ip] = device
                    self._notify_device_discovered(device)
                else:
                    # Device existant - vérifier changement de statut
                    device = self.devices[ip]
                    old_status = device.status
                    new_status = device_data["status"]
                    
                    if old_status != new_status:
                        device.status = new_status
                        self._notify_status_changed(device, old_status, new_status)

# Utilisation du pattern Observer
monitor = ObservableNetworkMonitor(snmp_client)

# Ajouter des observers
monitor.add_observer(LoggingObserver())
monitor.add_observer(AlertingObserver())

# Démarrer le monitoring
monitor.start_monitoring(interval=30)
```

## 🛡️ Patterns de Résilience

### Pattern Circuit Breaker

```python
import time
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"      # Fonctionnement normal
    OPEN = "open"          # Circuit ouvert - échecs détectés
    HALF_OPEN = "half_open" # Test de récupération

class CircuitBreaker:
    """Implémentation du pattern Circuit Breaker."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    def call(self, func, *args, **kwargs):
        """Exécute une fonction avec protection Circuit Breaker."""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Vérifie si on peut tenter une récupération."""
        return (time.time() - self.last_failure_time) >= self.recovery_timeout
    
    def _on_success(self):
        """Appelé en cas de succès."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        """Appelé en cas d'échec."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

# Client API avec Circuit Breaker
class ResilientAPIClient:
    def __init__(self, base_client: BaseAPIClient):
        self.base_client = base_client
        self.circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)
    
    def get(self, endpoint: str, **kwargs):
        """GET avec protection Circuit Breaker."""
        return self.circuit_breaker.call(self.base_client.get, endpoint, **kwargs)
    
    def post(self, endpoint: str, **kwargs):
        """POST avec protection Circuit Breaker."""
        return self.circuit_breaker.call(self.base_client.post, endpoint, **kwargs)

# Utilisation
resilient_client = ResilientAPIClient(gns3_client)

try:
    projects = resilient_client.get("projects")
except Exception as e:
    print(f"Service indisponible: {e}")
```

### Pattern Bulkhead

```python
import concurrent.futures
from typing import Dict, Any, Callable

class BulkheadExecutor:
    """Isolation des ressources par type d'opération."""
    
    def __init__(self):
        # Pools séparés pour différents types d'opérations
        self.read_pool = concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix="read")
        self.write_pool = concurrent.futures.ThreadPoolExecutor(max_workers=3, thread_name_prefix="write")
        self.monitoring_pool = concurrent.futures.ThreadPoolExecutor(max_workers=5, thread_name_prefix="monitor")
    
    def execute_read(self, func: Callable, *args, **kwargs) -> concurrent.futures.Future:
        """Exécute une opération de lecture."""
        return self.read_pool.submit(func, *args, **kwargs)
    
    def execute_write(self, func: Callable, *args, **kwargs) -> concurrent.futures.Future:
        """Exécute une opération d'écriture."""
        return self.write_pool.submit(func, *args, **kwargs)
    
    def execute_monitoring(self, func: Callable, *args, **kwargs) -> concurrent.futures.Future:
        """Exécute une opération de monitoring."""
        return self.monitoring_pool.submit(func, *args, **kwargs)
    
    def shutdown(self):
        """Arrête tous les pools."""
        self.read_pool.shutdown(wait=True)
        self.write_pool.shutdown(wait=True)
        self.monitoring_pool.shutdown(wait=True)

# Service utilisant Bulkhead
class BulkheadNetworkService:
    def __init__(self, gns3_client: GNS3Client, snmp_client: SNMPClient):
        self.gns3_client = gns3_client
        self.snmp_client = snmp_client
        self.executor = BulkheadExecutor()
    
    def get_projects_async(self):
        """Lecture asynchrone des projets."""
        return self.executor.execute_read(self.gns3_client.get, "projects")
    
    def create_project_async(self, project_data: Dict[str, Any]):
        """Création asynchrone de projet."""
        return self.executor.execute_write(self.gns3_client.post, "projects", json_data=project_data)
    
    def monitor_device_async(self, device_ip: str):
        """Monitoring asynchrone d'un device."""
        return self.executor.execute_monitoring(self.snmp_client.get, f"status/{device_ip}")

# Utilisation
service = BulkheadNetworkService(gns3_client, snmp_client)

# Opérations parallèles sans interférence
projects_future = service.get_projects_async()
monitoring_future = service.monitor_device_async("192.168.1.1")
create_future = service.create_project_async({"name": "Test Project"})

# Récupération des résultats
projects = projects_future.result(timeout=30)
device_status = monitoring_future.result(timeout=15)
new_project = create_future.result(timeout=60)
```

## 📊 Patterns de Monitoring

### Pattern Health Check

```python
from dataclasses import dataclass
from typing import List
import time

@dataclass
class HealthCheckResult:
    service_name: str
    status: str  # "healthy", "degraded", "unhealthy"
    response_time: float
    details: Dict[str, Any]
    timestamp: float

class HealthChecker:
    """Vérificateur de santé pour les services."""
    
    def __init__(self):
        self.clients: Dict[str, BaseAPIClient] = {}
    
    def register_client(self, name: str, client: BaseAPIClient):
        """Enregistre un client pour le health check."""
        self.clients[name] = client
    
    def check_all(self) -> List[HealthCheckResult]:
        """Vérifie la santé de tous les services."""
        results = []
        
        for name, client in self.clients.items():
            result = self._check_client(name, client)
            results.append(result)
        
        return results
    
    def _check_client(self, name: str, client: BaseAPIClient) -> HealthCheckResult:
        """Vérifie la santé d'un client spécifique."""
        start_time = time.time()
        
        try:
            health_data = client.health_check()
            response_time = time.time() - start_time
            
            if health_data.get("connection", False):
                status = "healthy"
            else:
                status = "unhealthy"
            
            return HealthCheckResult(
                service_name=name,
                status=status,
                response_time=response_time,
                details=health_data,
                timestamp=start_time
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            
            return HealthCheckResult(
                service_name=name,
                status="unhealthy",
                response_time=response_time,
                details={"error": str(e)},
                timestamp=start_time
            )
    
    def get_overall_status(self) -> str:
        """Détermine le statut global du système."""
        results = self.check_all()
        
        healthy_count = sum(1 for r in results if r.status == "healthy")
        total_count = len(results)
        
        if healthy_count == total_count:
            return "healthy"
        elif healthy_count > 0:
            return "degraded"
        else:
            return "unhealthy"

# Utilisation
health_checker = HealthChecker()
health_checker.register_client("gns3", gns3_client)
health_checker.register_client("snmp", snmp_client)
health_checker.register_client("netflow", netflow_client)

# Vérification périodique
def periodic_health_check():
    while True:
        overall_status = health_checker.get_overall_status()
        results = health_checker.check_all()
        
        print(f"\n🏥 Health Check - Statut global: {overall_status}")
        for result in results:
            status_icon = "✅" if result.status == "healthy" else "❌"
            print(f"{status_icon} {result.service_name}: {result.status} "
                  f"({result.response_time:.3f}s)")
        
        time.sleep(60)  # Vérification toutes les minutes

# Lancer le monitoring de santé
# threading.Thread(target=periodic_health_check, daemon=True).start()
```

Ces patterns d'intégration permettent de construire une architecture robuste, maintenable et évolutive en utilisant efficacement le module `api_clients` dans le respect des principes de l'architecture hexagonale.
