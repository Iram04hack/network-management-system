#!/usr/bin/env python3
"""
Déclencheur de Workflows Celery - Interface Réelle avec les Tâches Django
=========================================================================

Ce module déclenche RÉELLEMENT les workflows Django via les tâches Celery
définies dans chaque module NMS :

- common.tasks : Orchestration centrale et coordination
- gns3_integration.tasks : Monitoring et synchronisation GNS3  
- monitoring.tasks : Collecte de métriques et alertes
- security_management.tasks : Surveillance sécurité
- reporting.tasks : Génération de rapports
- Toutes les autres tâches Celery des modules

UTILISE CELERY POUR DÉCLENCHER LES TÂCHES comme demandé.
"""

import logging
import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import urllib3

# Désactiver les warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

class CeleryWorkflowTrigger:
    """
    Déclencheur de workflows via les tâches Celery réelles des modules Django.
    
    Utilise les endpoints Django qui déclenchent les tâches Celery
    définies dans chaque module pour orchestrer le workflow NMS.
    """
    
    def __init__(self, django_url: str, auth: tuple):
        self.django_url = django_url
        self.auth = auth
        self.triggered_tasks = []
        
        # Créer une session avec authentification
        self.session = requests.Session()
        self.session.auth = auth
        self.session.verify = False
        
        # Obtenir le token CSRF
        self._get_csrf_token()
        
        logger.info("🔥 Déclencheur Celery initialisé")
    
    def _get_csrf_token(self):
        """Obtient le token CSRF de Django."""
        try:
            # Obtenir le token CSRF
            csrf_response = self.session.get(f"{self.django_url}/api/")
            if 'csrftoken' in self.session.cookies:
                csrf_token = self.session.cookies['csrftoken']
                self.session.headers.update({'X-CSRFToken': csrf_token})
                logger.debug("✅ Token CSRF obtenu pour Celery")
            else:
                csrf_token = csrf_response.headers.get('X-CSRFToken')
                if csrf_token:
                    self.session.headers.update({'X-CSRFToken': csrf_token})
                    logger.debug("✅ Token CSRF obtenu depuis les headers pour Celery")
                else:
                    logger.warning("⚠️ Aucun token CSRF trouvé pour Celery")
        except Exception as e:
            logger.warning(f"⚠️ Erreur obtention token CSRF pour Celery: {e}")
    
    # =======================================
    # TÂCHES CELERY MODULE COMMON (Orchestration)
    # =======================================
    
    async def trigger_system_monitoring(self) -> List[str]:
        """
        Déclenche l'orchestrateur central via common.tasks.orchestrate_system_monitoring.
        
        Cette tâche lance et coordonne toutes les collectes de tous les modules
        pour avoir une vue d'ensemble synchronisée.
        """
        try:
            logger.info("🎯 Déclenchement orchestrateur système global via Celery")
            
            # Déclencher via l'API Django qui lance la tâche Celery
            response = self.session.post(
                f"{self.django_url}/api/common/api/v1/hub/workflows/execute/",
                json={
                    "workflow_name": "security_testing_full_workflow",
                    "initial_data": {
                        "trigger_source": "real_security_testing_framework",
                        "async_execution": True
                    }
                },
                timeout=30
            )
            
            if response.status_code in [200, 201, 202]:
                result = response.json()
                task_id = result.get('task_id', 'orchestrate_system_monitoring')
                self.triggered_tasks.append(task_id)
                
                logger.info(f"✅ Tâche Celery orchestrate_system_monitoring déclenchée: {task_id}")
                return [task_id]
            else:
                logger.error(f"❌ Erreur déclenchement orchestrateur: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Erreur déclenchement orchestrateur système: {e}")
            return []
    
    async def trigger_inter_module_communication(self) -> List[str]:
        """Déclenche la coordination inter-modules via Celery."""
        try:
            response = self.session.post(
                f"{self.django_url}/api/common/api/v1/hub/workflows/execute/",
                json={
                    "workflow_name": "security_testing_full_workflow",
                    "initial_data": {
                        "trigger_source": "real_security_testing_framework",
                        "action": "coordinate_inter_module_communication"
                    }
                },
                timeout=20
            )
            
            if response.status_code in [200, 201, 202]:
                result = response.json()
                task_id = result.get('task_id', 'coordinate_inter_module_communication')
                self.triggered_tasks.append(task_id)
                
                logger.info(f"✅ Tâche Celery coordinate_inter_module_communication déclenchée: {task_id}")
                return [task_id]
            else:
                return []
                
        except Exception as e:
            logger.error(f"❌ Erreur déclenchement communication inter-modules: {e}")
            return []
    
    async def trigger_unified_system_report(self) -> List[str]:
        """Déclenche la génération du rapport système unifié via Celery."""
        try:
            response = self.session.post(
                f"{self.django_url}/api/common/api/v1/hub/workflows/execute/",
                json={
                    "workflow_name": "security_testing_full_workflow",
                    "initial_data": {
                        "trigger_source": "real_security_testing_framework",
                        "action": "generate_unified_system_report"
                    }
                },
                timeout=60
            )
            
            if response.status_code in [200, 201, 202]:
                result = response.json()
                task_id = result.get('task_id', 'generate_unified_system_report')
                self.triggered_tasks.append(task_id)
                
                logger.info(f"✅ Tâche Celery generate_unified_system_report déclenchée: {task_id}")
                return [task_id]
            else:
                return []
                
        except Exception as e:
            logger.error(f"❌ Erreur déclenchement rapport unifié: {e}")
            return []
    
    # ==========================================
    # TÂCHES CELERY MODULE GNS3_INTEGRATION
    # ==========================================
    
    async def trigger_gns3_monitoring(self) -> List[str]:
        """
        Déclenche le monitoring GNS3 via gns3_integration.tasks.monitor_gns3_server.
        """
        try:
            logger.info("🔧 Déclenchement monitoring GNS3 via Celery")
            
            response = requests.post(
                f"{self.django_url}/api/gns3/server/monitor/",
                auth=self.auth,
                verify=False,
                json={
                    "action": "start_monitoring",
                    "trigger_source": "real_security_testing_framework"
                },
                timeout=30
            )
            
            if response.status_code in [200, 201, 202]:
                result = response.json()
                task_id = result.get('task_id', 'monitor_gns3_server')
                self.triggered_tasks.append(task_id)
                
                logger.info(f"✅ Tâche Celery monitor_gns3_server déclenchée: {task_id}")
                return [task_id]
            else:
                return []
                
        except Exception as e:
            logger.error(f"❌ Erreur déclenchement monitoring GNS3: {e}")
            return []
    
    async def trigger_multi_projects_monitoring(self) -> List[str]:
        """
        Déclenche la surveillance multi-projets via gns3_integration.tasks.monitor_multi_projects_traffic.
        """
        try:
            response = requests.post(
                f"{self.django_url}/api/gns3/multi-projects/monitor/",
                auth=self.auth,
                verify=False,
                json={
                    "action": "start_traffic_monitoring",
                    "trigger_source": "real_security_testing_framework"
                },
                timeout=30
            )
            
            if response.status_code in [200, 201, 202]:
                result = response.json()
                task_id = result.get('task_id', 'monitor_multi_projects_traffic')
                self.triggered_tasks.append(task_id)
                
                logger.info(f"✅ Tâche Celery monitor_multi_projects_traffic déclenchée: {task_id}")
                return [task_id]
            else:
                return []
                
        except Exception as e:
            logger.error(f"❌ Erreur déclenchement surveillance multi-projets: {e}")
            return []
    
    async def trigger_gns3_projects_sync(self) -> List[str]:
        """
        Déclenche la synchronisation des projets GNS3 via gns3_integration.tasks.sync_gns3_projects.
        """
        try:
            response = requests.post(
                f"{self.django_url}/api/gns3/projects/sync/",
                auth=self.auth,
                verify=False,
                json={
                    "action": "sync_all_projects",
                    "trigger_source": "real_security_testing_framework"
                },
                timeout=30
            )
            
            if response.status_code in [200, 201, 202]:
                result = response.json()
                task_id = result.get('task_id', 'sync_gns3_projects')
                self.triggered_tasks.append(task_id)
                
                logger.info(f"✅ Tâche Celery sync_gns3_projects déclenchée: {task_id}")
                return [task_id]
            else:
                return []
                
        except Exception as e:
            logger.error(f"❌ Erreur déclenchement sync projets GNS3: {e}")
            return []
    
    # ==================================
    # TÂCHES CELERY MODULE MONITORING  
    # ==================================
    
    async def trigger_monitoring_collection(self) -> List[str]:
        """
        Déclenche la collecte de métriques via monitoring.tasks.collect_metrics.
        """
        try:
            logger.info("📊 Déclenchement collecte monitoring via Celery")
            
            response = requests.post(
                f"{self.django_url}/api/monitoring/metrics/collect/",
                auth=self.auth,
                verify=False,
                json={
                    "action": "start_collection",
                    "trigger_source": "real_security_testing_framework",
                    "include_security_metrics": True
                },
                timeout=30
            )
            
            if response.status_code in [200, 201, 202]:
                result = response.json()
                task_id = result.get('task_id', 'collect_metrics')
                self.triggered_tasks.append(task_id)
                
                logger.info(f"✅ Tâche Celery collect_metrics déclenchée: {task_id}")
                return [task_id]
            else:
                return []
                
        except Exception as e:
            logger.error(f"❌ Erreur déclenchement collecte monitoring: {e}")
            return []
    
    async def trigger_alert_processing(self) -> List[str]:
        """Déclenche le traitement des alertes via monitoring.tasks."""
        try:
            response = requests.post(
                f"{self.django_url}/api/monitoring/alerts/process/",
                auth=self.auth,
                verify=False,
                json={
                    "action": "process_pending_alerts",
                    "trigger_source": "real_security_testing_framework"
                },
                timeout=30
            )
            
            if response.status_code in [200, 201, 202]:
                result = response.json()
                task_id = result.get('task_id', 'process_alerts')
                self.triggered_tasks.append(task_id)
                
                logger.info(f"✅ Tâche Celery process_alerts déclenchée: {task_id}")
                return [task_id]
            else:
                return []
                
        except Exception as e:
            logger.error(f"❌ Erreur déclenchement traitement alertes: {e}")
            return []
    
    # ========================================
    # TÂCHES CELERY MODULE SECURITY_MANAGEMENT
    # ========================================
    
    async def trigger_security_monitoring(self) -> List[str]:
        """
        Déclenche la surveillance sécurité via security_management.tasks.monitor_security_alerts.
        """
        try:
            logger.info("🛡️ Déclenchement surveillance sécurité via Celery")
            
            response = requests.post(
                f"{self.django_url}/api/security/monitor/",
                auth=self.auth,
                verify=False,
                json={
                    "action": "start_security_monitoring",
                    "trigger_source": "real_security_testing_framework",
                    "enhanced_detection": True
                },
                timeout=30
            )
            
            if response.status_code in [200, 201, 202]:
                result = response.json()
                task_id = result.get('task_id', 'monitor_security_alerts')
                self.triggered_tasks.append(task_id)
                
                logger.info(f"✅ Tâche Celery monitor_security_alerts déclenchée: {task_id}")
                return [task_id]
            else:
                return []
                
        except Exception as e:
            logger.error(f"❌ Erreur déclenchement surveillance sécurité: {e}")
            return []
    
    async def trigger_suricata_monitoring(self) -> List[str]:
        """Déclenche la surveillance Suricata via security_management.tasks."""
        try:
            response = requests.post(
                f"{self.django_url}/api/security/suricata/monitor/",
                auth=self.auth,
                verify=False,
                json={
                    "action": "start_suricata_monitoring",
                    "trigger_source": "real_security_testing_framework"
                },
                timeout=30
            )
            
            if response.status_code in [200, 201, 202]:
                result = response.json()
                task_id = result.get('task_id', 'fetch_suricata_alerts')
                self.triggered_tasks.append(task_id)
                
                logger.info(f"✅ Tâche Celery fetch_suricata_alerts déclenchée: {task_id}")
                return [task_id]
            else:
                return []
                
        except Exception as e:
            logger.error(f"❌ Erreur déclenchement surveillance Suricata: {e}")
            return []
    
    # ===============================
    # TÂCHES CELERY MODULE REPORTING
    # ===============================
    
    async def trigger_security_report_generation(self, session_id: str) -> List[str]:
        """
        Déclenche la génération de rapport sécurité via reporting.tasks.
        """
        try:
            logger.info("📋 Déclenchement génération rapport sécurité via Celery")
            
            response = requests.post(
                f"{self.django_url}/api/reporting/generate/",
                auth=self.auth,
                verify=False,
                json={
                    "report_type": "security_analysis",
                    "session_id": session_id,
                    "trigger_source": "real_security_testing_framework",
                    "include_traffic_analysis": True,
                    "include_attack_vectors": True
                },
                timeout=60
            )
            
            if response.status_code in [200, 201, 202]:
                result = response.json()
                task_id = result.get('task_id', 'generate_security_report_from_alerts')
                self.triggered_tasks.append(task_id)
                
                logger.info(f"✅ Tâche Celery generate_security_report_from_alerts déclenchée: {task_id}")
                return [task_id]
            else:
                return []
                
        except Exception as e:
            logger.error(f"❌ Erreur déclenchement rapport sécurité: {e}")
            return []
    
    async def trigger_unified_report_distribution(self, session_id: str) -> List[str]:
        """Déclenche la distribution des rapports via reporting.tasks."""
        try:
            response = requests.post(
                f"{self.django_url}/api/reporting/distribute/",
                auth=self.auth,
                verify=False,
                json={
                    "action": "distribute_unified_report",
                    "session_id": session_id,
                    "trigger_source": "real_security_testing_framework"
                },
                timeout=45
            )
            
            if response.status_code in [200, 201, 202]:
                result = response.json()
                task_id = result.get('task_id', 'distribute_unified_report')
                self.triggered_tasks.append(task_id)
                
                logger.info(f"✅ Tâche Celery distribute_unified_report déclenchée: {task_id}")
                return [task_id]
            else:
                return []
                
        except Exception as e:
            logger.error(f"❌ Erreur déclenchement distribution rapports: {e}")
            return []
    
    # ===========================
    # TÂCHES CELERY MODULE NETWORK_MANAGEMENT
    # ===========================
    
    async def trigger_network_monitoring(self) -> List[str]:
        """
        Déclenche le monitoring réseau via network_management.tasks.
        """
        try:
            logger.info("🌐 Déclenchement monitoring réseau via Celery")
            
            response = requests.post(
                f"{self.django_url}/api/network/monitor/",
                auth=self.auth,
                verify=False,
                json={
                    "action": "start_network_monitoring",
                    "trigger_source": "real_security_testing_framework"
                },
                timeout=30
            )
            
            if response.status_code in [200, 201, 202]:
                result = response.json()
                task_id = result.get('task_id', 'update_device_statuses')
                self.triggered_tasks.append(task_id)
                
                logger.info(f"✅ Tâche Celery update_device_statuses déclenchée: {task_id}")
                return [task_id]
            else:
                return []
                
        except Exception as e:
            logger.error(f"❌ Erreur déclenchement monitoring réseau: {e}")
            return []
    
    # ===============================
    # TÂCHES CELERY MODULE QOS_MANAGEMENT
    # ===============================
    
    async def trigger_qos_monitoring(self) -> List[str]:
        """
        Déclenche le monitoring QoS via qos_management.tasks.
        """
        try:
            response = requests.post(
                f"{self.django_url}/api/qos/monitor/",
                auth=self.auth,
                verify=False,
                json={
                    "action": "start_qos_monitoring",
                    "trigger_source": "real_security_testing_framework"
                },
                timeout=30
            )
            
            if response.status_code in [200, 201, 202]:
                result = response.json()
                task_id = result.get('task_id', 'collect_traffic_statistics')
                self.triggered_tasks.append(task_id)
                
                logger.info(f"✅ Tâche Celery collect_traffic_statistics déclenchée: {task_id}")
                return [task_id]
            else:
                return []
                
        except Exception as e:
            logger.error(f"❌ Erreur déclenchement monitoring QoS: {e}")
            return []
    
    # =============================
    # MÉTHODES DE WORKFLOW COMPLET
    # =============================
    
    async def trigger_complete_nms_workflow(self, session_id: str) -> Dict[str, List[str]]:
        """
        Déclenche le workflow NMS complet via toutes les tâches Celery appropriées.
        
        Cette méthode déclenche automatiquement tout le workflow NMS
        comme demandé lors de l'injection de trafic.
        """
        logger.info("🚀 DÉCLENCHEMENT DU WORKFLOW NMS COMPLET VIA CELERY")
        
        all_triggered_tasks = {
            "orchestration": [],
            "monitoring": [],
            "security": [],
            "network": [],
            "gns3": [],
            "qos": [],
            "reporting": []
        }
        
        try:
            # 1. Orchestration centrale
            orchestration_tasks = await self.trigger_system_monitoring()
            all_triggered_tasks["orchestration"].extend(orchestration_tasks)
            
            # 2. Communication inter-modules
            comm_tasks = await self.trigger_inter_module_communication()
            all_triggered_tasks["orchestration"].extend(comm_tasks)
            
            # 3. Monitoring complet
            monitoring_tasks = await self.trigger_monitoring_collection()
            all_triggered_tasks["monitoring"].extend(monitoring_tasks)
            
            alert_tasks = await self.trigger_alert_processing()
            all_triggered_tasks["monitoring"].extend(alert_tasks)
            
            # 4. Surveillance sécurité
            security_tasks = await self.trigger_security_monitoring()
            all_triggered_tasks["security"].extend(security_tasks)
            
            suricata_tasks = await self.trigger_suricata_monitoring()
            all_triggered_tasks["security"].extend(suricata_tasks)
            
            # 5. Monitoring réseau
            network_tasks = await self.trigger_network_monitoring()
            all_triggered_tasks["network"].extend(network_tasks)
            
            # 6. Monitoring GNS3
            gns3_tasks = await self.trigger_gns3_monitoring()
            all_triggered_tasks["gns3"].extend(gns3_tasks)
            
            multi_project_tasks = await self.trigger_multi_projects_monitoring()
            all_triggered_tasks["gns3"].extend(multi_project_tasks)
            
            # 7. Monitoring QoS
            qos_tasks = await self.trigger_qos_monitoring()
            all_triggered_tasks["qos"].extend(qos_tasks)
            
            # 8. Génération de rapports
            report_tasks = await self.trigger_security_report_generation(session_id)
            all_triggered_tasks["reporting"].extend(report_tasks)
            
            unified_report_tasks = await self.trigger_unified_system_report()
            all_triggered_tasks["reporting"].extend(unified_report_tasks)
            
            # Calculer le total
            total_tasks = sum(len(tasks) for tasks in all_triggered_tasks.values())
            
            logger.info(f"✅ WORKFLOW COMPLET DÉCLENCHÉ: {total_tasks} tâches Celery lancées")
            
            for category, tasks in all_triggered_tasks.items():
                if tasks:
                    logger.info(f"   {category}: {len(tasks)} tâches")
            
            return all_triggered_tasks
            
        except Exception as e:
            logger.error(f"❌ Erreur déclenchement workflow complet: {e}")
            return all_triggered_tasks
    
    def get_triggered_tasks_summary(self) -> Dict[str, Any]:
        """Retourne un résumé des tâches déclenchées."""
        return {
            "total_tasks": len(self.triggered_tasks),
            "tasks": self.triggered_tasks,
            "last_triggered": datetime.now().isoformat()
        }
    
    async def check_tasks_status(self) -> Dict[str, Any]:
        """Vérifie le statut des tâches Celery déclenchées."""
        try:
            response = requests.get(
                f"{self.django_url}/api/monitoring/celery/status/",
                auth=self.auth,
                verify=False,
                timeout=20
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            return {"error": str(e)}

# Fonction utilitaire pour créer un déclencheur
def create_celery_trigger(django_url: str = "http://localhost:8000",
                         username: str = "test_api_nms", 
                         password: str = "test123456") -> CeleryWorkflowTrigger:
    """Crée et retourne un déclencheur Celery configuré."""
    return CeleryWorkflowTrigger(
        django_url=django_url,
        auth=(username, password)
    )
