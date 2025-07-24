# 💡 Exemples d'Utilisation Pratiques - Module API_CLIENTS

## 🎯 Scénarios Réels d'Utilisation

Cette documentation présente des exemples concrets d'utilisation du module `api_clients` dans des contextes réels de gestion réseau.

## 🌐 Gestion de Projets GNS3

### Création et Configuration d'un Projet

```python
from api_clients.network.gns3_client import GNS3Client

# Initialisation du client GNS3
gns3 = GNS3Client(
    base_url="http://gns3-server:3080",
    username="admin",
    password="admin",
    max_retries=3
)

# Créer un nouveau projet
project_data = {
    "name": "Réseau Entreprise",
    "description": "Topologie réseau pour formation",
    "auto_start": False,
    "auto_open": False
}

response = gns3.post("projects", json_data=project_data)
if response["success"]:
    project_id = response["project_id"]
    print(f"Projet créé avec l'ID: {project_id}")
else:
    print(f"Erreur création projet: {response['error']}")

# Lister tous les projets
projects = gns3.get("projects")
if projects["success"]:
    for project in projects["data"]:
        print(f"- {project['name']} ({project['status']})")
```

### Gestion des Nœuds Réseau

```python
# Ajouter un routeur Cisco
router_config = {
    "name": "Router-1",
    "node_type": "dynamips",
    "compute_id": "local",
    "properties": {
        "platform": "c7200",
        "image": "c7200-adventerprisek9-mz.124-24.T5.image",
        "ram": 512
    }
}

response = gns3.post(f"projects/{project_id}/nodes", json_data=router_config)
if response["success"]:
    router_id = response["node_id"]
    print(f"Routeur créé: {router_id}")

# Démarrer le nœud
start_response = gns3.post(f"projects/{project_id}/nodes/{router_id}/start")
if start_response["success"]:
    print("Routeur démarré avec succès")
```

## 📊 Monitoring SNMP

### Collecte de Métriques Réseau

```python
from api_clients.network.snmp_client import SNMPClient

# Client SNMP pour monitoring
snmp = SNMPClient(
    base_url="http://snmp-service:161",
    community="public",
    version="2c",
    timeout=15
)

# Obtenir les informations système
def get_system_info(host):
    """Récupère les informations système via SNMP."""
    oids = {
        "sysName": "1.3.6.1.2.1.1.5.0",
        "sysDescr": "1.3.6.1.2.1.1.1.0",
        "sysUpTime": "1.3.6.1.2.1.1.3.0",
        "sysContact": "1.3.6.1.2.1.1.4.0"
    }
    
    system_info = {}
    for name, oid in oids.items():
        response = snmp.get(f"walk/{host}", params={"oid": oid})
        if response["success"]:
            system_info[name] = response["value"]
    
    return system_info

# Utilisation
host_info = get_system_info("192.168.1.1")
print(f"Nom système: {host_info.get('sysName', 'N/A')}")
print(f"Description: {host_info.get('sysDescr', 'N/A')}")
```

### Monitoring des Interfaces

```python
def monitor_interfaces(host):
    """Surveille l'état des interfaces réseau."""
    # OID pour les interfaces
    interface_oids = {
        "ifDescr": "1.3.6.1.2.1.2.2.1.2",      # Description
        "ifOperStatus": "1.3.6.1.2.1.2.2.1.8", # Statut opérationnel
        "ifInOctets": "1.3.6.1.2.1.2.2.1.10",  # Octets entrants
        "ifOutOctets": "1.3.6.1.2.1.2.2.1.16"  # Octets sortants
    }
    
    interfaces = []
    
    # Récupérer la liste des interfaces
    response = snmp.get(f"walk/{host}", params={"oid": interface_oids["ifDescr"]})
    if response["success"]:
        for interface_data in response["data"]:
            interface_id = interface_data["index"]
            
            # Récupérer les métriques pour cette interface
            interface_info = {
                "id": interface_id,
                "description": interface_data["value"]
            }
            
            # Statut opérationnel
            status_response = snmp.get(f"get/{host}", params={
                "oid": f"{interface_oids['ifOperStatus']}.{interface_id}"
            })
            if status_response["success"]:
                interface_info["status"] = "UP" if status_response["value"] == "1" else "DOWN"
            
            interfaces.append(interface_info)
    
    return interfaces

# Surveillance continue
import time

def continuous_monitoring(hosts, interval=60):
    """Surveillance continue des hôtes."""
    while True:
        for host in hosts:
            try:
                print(f"\n=== Monitoring {host} ===")
                interfaces = monitor_interfaces(host)
                
                for interface in interfaces:
                    status_icon = "🟢" if interface["status"] == "UP" else "🔴"
                    print(f"{status_icon} {interface['description']}: {interface['status']}")
                
            except Exception as e:
                print(f"❌ Erreur monitoring {host}: {e}")
        
        time.sleep(interval)

# Lancer le monitoring
# continuous_monitoring(["192.168.1.1", "192.168.1.2"])
```

## 🌊 Analyse Netflow

### Collecte et Analyse du Trafic

```python
from api_clients.network.netflow_client import NetflowClient
from datetime import datetime, timedelta

# Client Netflow
netflow = NetflowClient(
    base_url="http://netflow-collector:9995",
    timeout=60,
    max_retries=5
)

def analyze_traffic_patterns(start_time=None, end_time=None):
    """Analyse les patterns de trafic Netflow."""
    if not start_time:
        start_time = datetime.now() - timedelta(hours=1)
    if not end_time:
        end_time = datetime.now()
    
    # Paramètres de requête
    params = {
        "start": start_time.isoformat(),
        "end": end_time.isoformat(),
        "aggregation": "5min"
    }
    
    # Récupérer les données de trafic
    response = netflow.get("flows", params=params)
    if response["success"]:
        flows = response["data"]
        
        # Analyser les top talkers
        top_talkers = {}
        for flow in flows:
            src_ip = flow["src_addr"]
            bytes_count = flow["in_bytes"]
            
            if src_ip in top_talkers:
                top_talkers[src_ip] += bytes_count
            else:
                top_talkers[src_ip] = bytes_count
        
        # Trier par volume de trafic
        sorted_talkers = sorted(top_talkers.items(), 
                              key=lambda x: x[1], reverse=True)
        
        print("🔝 Top 10 Talkers:")
        for i, (ip, bytes_count) in enumerate(sorted_talkers[:10], 1):
            mb_count = bytes_count / (1024 * 1024)
            print(f"{i:2d}. {ip:15s} - {mb_count:8.2f} MB")
        
        return sorted_talkers
    else:
        print(f"Erreur récupération flows: {response['error']}")
        return []

# Analyse en temps réel
traffic_data = analyze_traffic_patterns()
```

### Détection d'Anomalies

```python
def detect_traffic_anomalies(threshold_mbps=100):
    """Détecte les anomalies de trafic."""
    current_time = datetime.now()
    
    # Analyser les 5 dernières minutes
    params = {
        "start": (current_time - timedelta(minutes=5)).isoformat(),
        "end": current_time.isoformat(),
        "aggregation": "1min"
    }
    
    response = netflow.get("flows/summary", params=params)
    if response["success"]:
        summary = response["data"]
        
        anomalies = []
        for minute_data in summary:
            timestamp = minute_data["timestamp"]
            total_mbps = minute_data["total_bytes"] * 8 / (1024 * 1024 * 60)
            
            if total_mbps > threshold_mbps:
                anomalies.append({
                    "timestamp": timestamp,
                    "traffic_mbps": total_mbps,
                    "severity": "HIGH" if total_mbps > threshold_mbps * 2 else "MEDIUM"
                })
        
        if anomalies:
            print("🚨 Anomalies détectées:")
            for anomaly in anomalies:
                severity_icon = "🔴" if anomaly["severity"] == "HIGH" else "🟡"
                print(f"{severity_icon} {anomaly['timestamp']}: "
                      f"{anomaly['traffic_mbps']:.2f} Mbps ({anomaly['severity']})")
        
        return anomalies
    
    return []

# Surveillance des anomalies
anomalies = detect_traffic_anomalies(threshold_mbps=50)
```

## 🔄 Intégration Multi-Services

### Orchestration Complète

```python
class NetworkOrchestrator:
    """Orchestrateur pour la gestion réseau complète."""
    
    def __init__(self):
        self.gns3 = GNS3Client(base_url="http://gns3-server:3080")
        self.snmp = SNMPClient(base_url="http://snmp-service:161")
        self.netflow = NetflowClient(base_url="http://netflow-collector:9995")
    
    def deploy_network_scenario(self, scenario_config):
        """Déploie un scénario réseau complet."""
        try:
            # 1. Créer le projet GNS3
            project_response = self.gns3.post("projects", json_data={
                "name": scenario_config["name"],
                "description": scenario_config["description"]
            })
            
            if not project_response["success"]:
                raise Exception(f"Erreur création projet: {project_response['error']}")
            
            project_id = project_response["project_id"]
            print(f"✅ Projet créé: {project_id}")
            
            # 2. Déployer les nœuds
            for node_config in scenario_config["nodes"]:
                node_response = self.gns3.post(
                    f"projects/{project_id}/nodes",
                    json_data=node_config
                )
                
                if node_response["success"]:
                    print(f"✅ Nœud déployé: {node_config['name']}")
                else:
                    print(f"❌ Erreur nœud {node_config['name']}: {node_response['error']}")
            
            # 3. Démarrer le projet
            start_response = self.gns3.post(f"projects/{project_id}/start")
            if start_response["success"]:
                print("✅ Projet démarré")
            
            # 4. Attendre la stabilisation
            time.sleep(30)
            
            # 5. Configurer le monitoring SNMP
            self._setup_monitoring(scenario_config.get("monitoring_hosts", []))
            
            return project_id
            
        except Exception as e:
            print(f"❌ Erreur déploiement: {e}")
            return None
    
    def _setup_monitoring(self, hosts):
        """Configure le monitoring SNMP."""
        for host in hosts:
            try:
                # Test de connectivité SNMP
                response = self.snmp.get(f"get/{host}", params={"oid": "1.3.6.1.2.1.1.1.0"})
                if response["success"]:
                    print(f"✅ Monitoring configuré pour {host}")
                else:
                    print(f"⚠️  Monitoring non disponible pour {host}")
            except Exception as e:
                print(f"❌ Erreur monitoring {host}: {e}")

# Utilisation de l'orchestrateur
orchestrator = NetworkOrchestrator()

scenario = {
    "name": "Lab CCNA",
    "description": "Laboratoire de formation CCNA",
    "nodes": [
        {
            "name": "R1",
            "node_type": "dynamips",
            "properties": {"platform": "c7200", "ram": 512}
        },
        {
            "name": "R2", 
            "node_type": "dynamips",
            "properties": {"platform": "c7200", "ram": 512}
        }
    ],
    "monitoring_hosts": ["192.168.1.1", "192.168.1.2"]
}

project_id = orchestrator.deploy_network_scenario(scenario)
```

## 🛡️ Gestion d'Erreurs Avancée

### Retry et Fallback

```python
from api_clients.domain.exceptions import APITimeoutException, APIConnectionException

def robust_api_call(client, endpoint, max_attempts=3, fallback_data=None):
    """Appel API robuste avec fallback."""
    for attempt in range(max_attempts):
        try:
            response = client.get(endpoint)
            if response["success"]:
                return response["data"]
            else:
                print(f"Tentative {attempt + 1} échouée: {response['error']}")
                
        except APITimeoutException:
            print(f"Timeout tentative {attempt + 1}")
            if attempt < max_attempts - 1:
                time.sleep(2 ** attempt)  # Backoff exponentiel
                
        except APIConnectionException:
            print(f"Connexion échouée tentative {attempt + 1}")
            if attempt < max_attempts - 1:
                time.sleep(5)  # Attente plus longue pour reconnexion
    
    # Utiliser les données de fallback si disponibles
    if fallback_data:
        print("⚠️  Utilisation des données de fallback")
        return fallback_data
    
    raise Exception("Toutes les tentatives ont échoué")

# Utilisation avec fallback
try:
    projects = robust_api_call(
        gns3, 
        "projects",
        fallback_data=[]  # Liste vide en cas d'échec
    )
except Exception as e:
    print(f"Erreur critique: {e}")
```

## 📈 Monitoring et Métriques

### Collecte de Métriques de Performance

```python
import time
from collections import defaultdict

class APIMetricsCollector:
    """Collecteur de métriques pour les APIs."""
    
    def __init__(self):
        self.metrics = defaultdict(list)
    
    def measure_api_call(self, client, method, endpoint, **kwargs):
        """Mesure les performances d'un appel API."""
        start_time = time.time()
        
        try:
            if method.upper() == "GET":
                response = client.get(endpoint, **kwargs)
            elif method.upper() == "POST":
                response = client.post(endpoint, **kwargs)
            else:
                raise ValueError(f"Méthode non supportée: {method}")
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Enregistrer les métriques
            self.metrics[f"{client.__class__.__name__}_{endpoint}"].append({
                "duration": duration,
                "success": response.get("success", False),
                "timestamp": start_time,
                "method": method.upper()
            })
            
            return response
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            self.metrics[f"{client.__class__.__name__}_{endpoint}"].append({
                "duration": duration,
                "success": False,
                "error": str(e),
                "timestamp": start_time,
                "method": method.upper()
            })
            
            raise
    
    def get_performance_report(self):
        """Génère un rapport de performance."""
        report = {}
        
        for endpoint, calls in self.metrics.items():
            if not calls:
                continue
                
            durations = [call["duration"] for call in calls]
            success_rate = sum(1 for call in calls if call["success"]) / len(calls)
            
            report[endpoint] = {
                "total_calls": len(calls),
                "success_rate": success_rate,
                "avg_duration": sum(durations) / len(durations),
                "min_duration": min(durations),
                "max_duration": max(durations)
            }
        
        return report

# Utilisation du collecteur
metrics = APIMetricsCollector()

# Mesurer les appels API
response = metrics.measure_api_call(gns3, "GET", "projects")
response = metrics.measure_api_call(snmp, "GET", "walk/192.168.1.1", params={"oid": "1.3.6.1.2.1.1.1.0"})

# Générer le rapport
report = metrics.get_performance_report()
for endpoint, stats in report.items():
    print(f"\n📊 {endpoint}:")
    print(f"  Appels: {stats['total_calls']}")
    print(f"  Taux de succès: {stats['success_rate']:.2%}")
    print(f"  Durée moyenne: {stats['avg_duration']:.3f}s")
```

Ces exemples montrent l'utilisation pratique du module `api_clients` dans des scénarios réels de gestion réseau, avec gestion d'erreurs robuste et monitoring des performances.
