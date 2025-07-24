#!/usr/bin/env python3
"""
Manager de Communication Django - Interface Réelle avec les Modules NMS
=======================================================================

Ce module gère toute la communication RÉELLE avec les modules Django :
- gns3_integration : Gestion des projets et équipements GNS3
- common : Orchestration centrale et communication inter-modules  
- monitoring : Surveillance et alertes
- security_management : Gestion des événements de sécurité
- Tous les autres modules NMS

AUCUNE SIMULATION - Communication directe via les APIs REST Django.
"""

import logging
import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import urllib3

# Désactiver les warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

@dataclass
class DjangoAPIResponse:
    """Réponse d'une API Django."""
    success: bool
    status_code: int
    data: Dict[str, Any]
    error_message: Optional[str] = None
    response_time_ms: float = 0.0

class DjangoCommunicationManager:
    """
    Manager pour toute la communication avec les modules Django NMS.
    
    Utilise les APIs REST réelles définies dans chaque module Django
    pour une intégration complète sans simulation.
    """
    
    def __init__(self, django_url: str, auth: Tuple[str, str]):
        self.django_url = django_url
        self.auth = auth
        self.session = requests.Session()
        self.session.auth = auth
        self.session.verify = False
        
        # Configuration pour accepter HTTP et HTTPS
        if django_url.startswith('https://'):
            # Désactiver les warnings SSL pour HTTPS
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Obtenir le token CSRF
        self._get_csrf_token()
        
        # Configuration des timeouts par type d'API
        self.timeouts = {
            'gns3': 30,      # GNS3 peut être lent
            'common': 20,    # Orchestration moyenne
            'monitoring': 15, # Monitoring rapide
            'security': 25,   # Sécurité peut analyser
            'reporting': 45   # Rapports peuvent être longs
        }
        
        logger.info(f"🔗 Manager Django initialisé pour {django_url}")
    
    def _get_csrf_token(self):
        """Obtient le token CSRF de Django."""
        try:
            # Obtenir le token CSRF
            csrf_response = self.session.get(f"{self.django_url}/api/")
            if 'csrftoken' in self.session.cookies:
                csrf_token = self.session.cookies['csrftoken']
                self.session.headers.update({'X-CSRFToken': csrf_token})
                logger.debug("✅ Token CSRF obtenu")
            else:
                # Essayer d'obtenir le token depuis les headers
                csrf_token = csrf_response.headers.get('X-CSRFToken')
                if csrf_token:
                    self.session.headers.update({'X-CSRFToken': csrf_token})
                    logger.debug("✅ Token CSRF obtenu depuis les headers")
                else:
                    logger.warning("⚠️ Aucun token CSRF trouvé")
        except Exception as e:
            logger.warning(f"⚠️ Erreur obtention token CSRF: {e}")
    
    # ==========================================
    # COMMUNICATION AVEC MODULE GNS3_INTEGRATION
    # ==========================================
    
    async def get_gns3_projects(self) -> DjangoAPIResponse:
        """Récupère la liste des projets GNS3 via le module gns3_integration."""
        return self._make_request(
            method='GET',
            endpoint='/api/gns3/projects/',
            module_type='gns3',
            description="Récupération des projets GNS3"
        )
    
    async def get_gns3_server_status(self) -> DjangoAPIResponse:
        """Récupère le statut du serveur GNS3 via Django."""
        return self._make_request(
            method='GET',
            endpoint='/api/gns3/server/status/',
            module_type='gns3',
            description="Statut serveur GNS3"
        )
    
    async def activate_gns3_project(self, project_id: str, session_id: str) -> DjangoAPIResponse:
        """Active un projet GNS3 pour les tests via Django."""
        return self._make_request(
            method='POST',
            endpoint='/api/gns3/projects/',
            module_type='gns3',
            data={
                "action": "activate_for_testing",
                "project_id": project_id,
                "testing_session_id": session_id,
                "auto_start_nodes": True,
                "enable_monitoring": True,
                "requester": "real_security_testing_framework"
            },
            description=f"Activation projet GNS3 {project_id}"
        )
    
    async def get_project_nodes(self, project_id: str) -> DjangoAPIResponse:
        """Récupère les nœuds d'un projet GNS3 via Django."""
        return self._make_request(
            method='GET',
            endpoint=f'/api/gns3/projects/{project_id}/nodes/',
            module_type='gns3',
            description=f"Nœuds du projet {project_id}"
        )
    
    async def start_project_nodes(self, project_id: str) -> DjangoAPIResponse:
        """Démarre tous les nœuds d'un projet via Django."""
        return self._make_request(
            method='POST',
            endpoint=f'/api/gns3/projects/{project_id}/start/',
            module_type='gns3',
            description=f"Démarrage nœuds projet {project_id}"
        )
    
    # ========================================
    # COMMUNICATION AVEC MODULE COMMON  
    # ========================================
    
    async def notify_common_testing_session(self, project_id: str, session_id: str) -> DjangoAPIResponse:
        """Notifie le module common du début d'une session de test."""
        return self._make_request(
            method='POST',
            endpoint='/api/common/api/v1/integration/gns3/projects/',
            module_type='common',
            data={
                "action": "start_testing_session",
                "project_id": project_id,
                "session_id": session_id,
                "testing_framework": "real_security_testing",
                "auto_orchestrate": True,
                "enable_workflow_engine": True
            },
            description="Notification session de test au module common"
        )
    
    async def get_integration_status(self, session_id: str, project_id: str) -> DjangoAPIResponse:
        """Récupère le statut d'intégration depuis le module common."""
        return self._make_request(
            method='GET',
            endpoint='/api/common/api/v1/integration/status/',
            module_type='common',
            params={
                "session_id": session_id,
                "project_id": project_id
            },
            description="Statut d'intégration depuis common"
        )
    
    async def get_discovered_equipment(self, project_id: str) -> DjangoAPIResponse:
        """Récupère les équipements découverts via le module common."""
        return self._make_request(
            method='GET',
            endpoint=f'/api/common/api/v1/equipment/projects/{project_id}/equipment/',
            module_type='common',
            description=f"Équipements découverts projet {project_id}"
        )
    
    async def trigger_equipment_discovery(self, project_id: str) -> DjangoAPIResponse:
        """Déclenche la découverte d'équipements via common."""
        return self._make_request(
            method='POST',
            endpoint=f'/api/common/api/v1/equipment/projects/{project_id}/discover/',
            module_type='common',
            description=f"Découverte équipements projet {project_id}"
        )
    
    async def send_inter_module_message(self, target_module: str, message_data: Dict, message_type: str = "security_alert") -> DjangoAPIResponse:
        """Envoie un message inter-modules via common."""
        return self._make_request(
            method='POST',
            endpoint='/api/common/api/v1/integration/messages/send/',
            module_type='common',
            data={
                "message_type": message_type,
                "target": target_module,
                "data": {
                    "message": message_data,
                    "sender": "real_security_testing_framework"
                }
            },
            description=f"Message inter-modules vers {target_module}"
        )
    
    # ======================================
    # COMMUNICATION AVEC MODULE MONITORING
    # ======================================
    
    async def get_monitoring_status(self, session_id: Optional[str] = None) -> DjangoAPIResponse:
        """Récupère le statut du monitoring via Django."""
        params = {}
        if session_id:
            params["session_id"] = session_id
            
        return self._make_request(
            method='GET',
            endpoint='/api/monitoring/',
            module_type='monitoring',
            params=params,
            description="Statut du monitoring"
        )
    
    async def create_monitoring_alert(self, alert_data: Dict) -> DjangoAPIResponse:
        """Crée une alerte de monitoring via Django."""
        return self._make_request(
            method='POST',
            endpoint='/api/monitoring/alerts/',
            module_type='monitoring',
            data=alert_data,
            description="Création alerte monitoring"
        )
    
    async def get_system_metrics(self) -> DjangoAPIResponse:
        """Récupère les métriques système via monitoring."""
        return self._make_request(
            method='GET',
            endpoint='/api/monitoring/metrics/',
            module_type='monitoring',
            description="Métriques système"
        )
    
    # =========================================
    # COMMUNICATION AVEC MODULE SECURITY_MANAGEMENT
    # =========================================
    
    async def report_security_event(self, event_data: Dict) -> DjangoAPIResponse:
        """Rapporte un événement de sécurité au module security_management."""
        return self._make_request(
            method='POST',
            endpoint='/api/security/events/',
            module_type='security',
            data={
                "event_type": "security_test_event",
                "source": "real_security_testing_framework",
                "data": event_data,
                "timestamp": datetime.now().isoformat()
            },
            description="Rapport événement sécurité"
        )
    
    async def get_security_alerts(self, session_id: Optional[str] = None) -> DjangoAPIResponse:
        """Récupère les alertes de sécurité."""
        params = {}
        if session_id:
            params["session_id"] = session_id
            
        return self._make_request(
            method='GET',
            endpoint='/api/security/alerts/',
            module_type='security',
            params=params,
            description="Alertes de sécurité"
        )
    
    # ====================================
    # COMMUNICATION AVEC MODULE REPORTING
    # ====================================
    
    async def request_test_report(self, session_id: str, report_type: str = "security_test") -> DjangoAPIResponse:
        """Demande la génération d'un rapport via le module reporting."""
        return self._make_request(
            method='POST',
            endpoint='/api/reporting/',
            module_type='reporting',
            data={
                "report_type": report_type,
                "session_id": session_id,
                "requester": "real_security_testing_framework",
                "include_security_analysis": True,
                "include_traffic_analysis": True
            },
            description=f"Demande rapport {report_type}"
        )
    
    async def get_report_status(self, report_id: str) -> DjangoAPIResponse:
        """Récupère le statut d'un rapport."""
        return self._make_request(
            method='GET',
            endpoint=f'/api/reporting/reports/{report_id}/',
            module_type='reporting',
            description=f"Statut rapport {report_id}"
        )
    
    # =====================================
    # MÉTHODES DE COLLECTE DE RÉSULTATS
    # =====================================
    
    async def get_session_results(self, session_id: str) -> DjangoAPIResponse:
        """Collecte tous les résultats d'une session depuis tous les modules."""
        return self._make_request(
            method='GET',
            endpoint='/api/common/api/v1/integration/results/',
            module_type='common',
            params={"session_id": session_id},
            description=f"Résultats session {session_id}"
        )
    
    async def get_activated_modules(self, session_id: str) -> List[str]:
        """Récupère la liste des modules activés pour une session."""
        try:
            response = await self.get_monitoring_status(session_id)
            if response.success:
                return response.data.get("active_modules", [])
            return []
        except Exception as e:
            logger.error(f"❌ Erreur récupération modules activés: {e}")
            return []
    
    async def get_generated_alerts_count(self, session_id: str) -> int:
        """Récupère le nombre d'alertes générées pour une session."""
        try:
            response = await self.get_security_alerts(session_id)
            if response.success:
                return len(response.data.get("alerts", []))
            return 0
        except Exception as e:
            logger.error(f"❌ Erreur comptage alertes: {e}")
            return 0
    
    # =============================
    # MÉTHODES UTILITAIRES PRIVÉES
    # =============================
    
    def _make_request(self, method: str, endpoint: str, module_type: str, 
                     data: Optional[Dict] = None, params: Optional[Dict] = None,
                     description: str = "") -> DjangoAPIResponse:
        """
        Effectue une requête HTTP vers une API Django.
        
        Args:
            method: Méthode HTTP (GET, POST, PUT, DELETE)
            endpoint: Endpoint de l'API
            module_type: Type de module pour le timeout approprié
            data: Données à envoyer (pour POST/PUT)
            params: Paramètres query string
            description: Description pour les logs
        """
        start_time = time.time()
        url = f"{self.django_url}{endpoint}"
        timeout = self.timeouts.get(module_type, 20)
        
        try:
            logger.debug(f"🌐 {method} {endpoint} - {description}")
            
            # Préparer les paramètres de la requête
            request_kwargs = {
                'timeout': timeout,
                'verify': False
            }
            
            if params:
                request_kwargs['params'] = params
            
            if data and method in ['POST', 'PUT', 'PATCH']:
                request_kwargs['json'] = data
            
            # Effectuer la requête
            response = self.session.request(method, url, **request_kwargs)
            
            response_time_ms = (time.time() - start_time) * 1000
            
            # Traiter la réponse
            try:
                response_data = response.json() if response.content else {}
            except json.JSONDecodeError:
                response_data = {"raw_content": response.text}
            
            success = response.status_code in [200, 201, 202]
            
            if success:
                logger.debug(f"✅ {description} - {response.status_code} ({response_time_ms:.1f}ms)")
            else:
                logger.warning(f"⚠️ {description} - {response.status_code} ({response_time_ms:.1f}ms)")
            
            return DjangoAPIResponse(
                success=success,
                status_code=response.status_code,
                data=response_data,
                error_message=None if success else response_data.get('error', f'HTTP {response.status_code}'),
                response_time_ms=response_time_ms
            )
            
        except requests.exceptions.Timeout:
            response_time_ms = (time.time() - start_time) * 1000
            error_msg = f"Timeout après {timeout}s"
            logger.error(f"⏰ {description} - {error_msg}")
            
            return DjangoAPIResponse(
                success=False,
                status_code=0,
                data={},
                error_message=error_msg,
                response_time_ms=response_time_ms
            )
            
        except requests.exceptions.ConnectionError as e:
            response_time_ms = (time.time() - start_time) * 1000
            error_msg = f"Erreur connexion: {str(e)}"
            logger.error(f"🔌 {description} - {error_msg}")
            
            return DjangoAPIResponse(
                success=False,
                status_code=0,
                data={},
                error_message=error_msg,
                response_time_ms=response_time_ms
            )
            
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            error_msg = f"Erreur inattendue: {str(e)}"
            logger.error(f"❌ {description} - {error_msg}")
            
            return DjangoAPIResponse(
                success=False,
                status_code=0,
                data={},
                error_message=error_msg,
                response_time_ms=response_time_ms
            )
    
    def close(self):
        """Ferme la session de communication."""
        try:
            self.session.close()
            logger.info("🔒 Session Django fermée")
        except Exception as e:
            logger.warning(f"⚠️ Erreur fermeture session: {e}")

# Fonction utilitaire pour créer un manager
def create_django_manager(django_url: str = "http://localhost:8000", 
                         username: str = "test_api_nms", 
                         password: str = "test123456") -> DjangoCommunicationManager:
    """Crée et retourne un manager de communication Django configuré."""
    return DjangoCommunicationManager(
        django_url=django_url,
        auth=(username, password)
    )
