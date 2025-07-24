"""
Adaptateurs sophistiqués pour l'intégration avec les services Docker de sécurité.

Ce module contient les implémentations des adaptateurs pour interagir avec les services
Docker de sécurité (Suricata, Fail2Ban, Traffic Control, Elasticsearch) via leurs APIs REST.
Chaque adaptateur inclut la gestion des erreurs, le retry automatique, la mise en cache,
et la surveillance de santé des services.
"""

import json
import logging
import time
import threading
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from django.conf import settings
from django.utils import timezone
from django.core.cache import cache

from ..domain.interfaces import (
    SuricataService, Fail2BanService, FirewallService, DockerServiceConnector
)
from ..domain.entities import Jail, BannedIP

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """États possibles d'un service Docker."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    UNREACHABLE = "unreachable"


@dataclass
class ServiceHealthCheck:
    """Résultat d'un check de santé de service."""
    service_name: str
    status: ServiceStatus
    response_time_ms: int
    last_check: datetime
    error_message: Optional[str] = None
    consecutive_failures: int = 0
    version: Optional[str] = None
    uptime: Optional[str] = None


class DockerServiceAdapter(DockerServiceConnector):
    """
    Adaptateur de base pour les services Docker avec fonctionnalités avancées.
    """
    
    def __init__(self, service_name: str, base_url: str, timeout: int = 30):
        """
        Initialise l'adaptateur avec configuration avancée.
        
        Args:
            service_name: Nom du service Docker
            base_url: URL de base du service
            timeout: Timeout pour les requêtes HTTP
        """
        self.service_name = service_name
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        
        # Configuration des retries
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"]
        )
        
        # Session HTTP avec configuration optimisée
        self._session = requests.Session()
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)
        
        # Configuration de la session
        self._session.timeout = timeout
        self._session.headers.update({
            'User-Agent': f'NMS-SecurityManagement/{service_name}-Client',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        # Cache et monitoring
        self._cache_prefix = f"docker_service_{service_name}"
        self._cache_timeout = 300  # 5 minutes
        self._health_check_interval = 60  # 1 minute
        self._last_health_check = None
        self._health_status = ServiceStatus.UNKNOWN
        self._consecutive_failures = 0
        self._max_consecutive_failures = 5
        
        # Circuit breaker pattern
        self._circuit_open = False
        self._circuit_open_until = None
        self._circuit_failure_threshold = 5
        self._circuit_recovery_timeout = 300  # 5 minutes
        
        # Métriques
        self._request_count = 0
        self._error_count = 0
        self._total_response_time = 0.0
        
        logger.info(f"Adaptateur Docker initialisé pour {service_name} à {base_url}")
    
    def test_connection(self) -> bool:
        """Teste la connexion au service Docker."""
        try:
            start_time = time.time()
            response = self._session.get(f"{self.base_url}/health", timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            is_healthy = response.status_code == 200
            
            # Mettre à jour le statut de santé
            self._update_health_status(is_healthy, response_time, None)
            
            return is_healthy
            
        except Exception as e:
            self._update_health_status(False, 0, str(e))
            return False
    
    def get_service_status(self) -> Dict[str, Any]:
        """Récupère le statut détaillé du service Docker."""
        try:
            # Vérifier le cache d'abord
            cache_key = f"{self._cache_prefix}_status"
            cached_status = cache.get(cache_key)
            if cached_status:
                return cached_status
            
            start_time = time.time()
            response = self._session.get(f"{self.base_url}/status", timeout=self.timeout)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                # Enrichir avec nos métriques
                enhanced_status = {
                    **data,
                    'adapter_metrics': self._get_adapter_metrics(),
                    'response_time_ms': response_time,
                    'last_check': timezone.now().isoformat(),
                    'circuit_status': 'open' if self._circuit_open else 'closed'
                }
                
                # Mettre en cache
                cache.set(cache_key, enhanced_status, self._cache_timeout)
                
                self._update_health_status(True, response_time, None)
                return enhanced_status
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                self._update_health_status(False, response_time, error_msg)
                return {"status": "error", "message": error_msg}
                
        except Exception as e:
            error_msg = str(e)
            self._update_health_status(False, 0, error_msg)
            return {"status": "unreachable", "error": error_msg}
    
    def call_api(self, endpoint: str, method: str = 'GET', data: Optional[Dict] = None) -> Dict[str, Any]:
        """Effectue un appel API vers le service Docker avec circuit breaker."""
        # Vérifier le circuit breaker
        if self._is_circuit_open():
            return {
                "error": "Circuit breaker open - service temporarily unavailable",
                "circuit_open": True
            }
        
        try:
            self._request_count += 1
            start_time = time.time()
            
            url = f"{self.base_url}{endpoint}"
            
            # Préparer les kwargs pour la requête
            kwargs = {
                'timeout': self.timeout,
                'headers': self._session.headers
            }
            
            if data:
                kwargs['json'] = data
            
            # Effectuer la requête
            if method.upper() == 'GET':
                response = self._session.get(url, **kwargs)
            elif method.upper() == 'POST':
                response = self._session.post(url, **kwargs)
            elif method.upper() == 'PUT':
                response = self._session.put(url, **kwargs)
            elif method.upper() == 'DELETE':
                response = self._session.delete(url, **kwargs)
            else:
                return {"error": f"Méthode HTTP non supportée: {method}"}
            
            response_time = time.time() - start_time
            self._total_response_time += response_time
            
            # Traiter la réponse
            if response.status_code < 400:
                self._consecutive_failures = 0  # Reset sur succès
                
                if response.content:
                    try:
                        return response.json()
                    except json.JSONDecodeError:
                        return {"success": True, "raw_response": response.text}
                else:
                    return {"success": True}
            else:
                self._handle_request_failure(response.status_code, response.text)
                return {
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "status_code": response.status_code
                }
                
        except Exception as e:
            self._handle_request_failure(0, str(e))
            logger.error(f"Erreur lors de l'appel API {method} {endpoint}: {str(e)}")
            return {"error": str(e)}
    
    def _is_circuit_open(self) -> bool:
        """Vérifie si le circuit breaker est ouvert."""
        if not self._circuit_open:
            return False
        
        # Vérifier si le circuit peut être fermé
        if self._circuit_open_until and timezone.now() > self._circuit_open_until:
            logger.info(f"Tentative de fermeture du circuit breaker pour {self.service_name}")
            self._circuit_open = False
            self._circuit_open_until = None
            self._consecutive_failures = 0
            return False
        
        return True
    
    def _handle_request_failure(self, status_code: int, error_message: str):
        """Gère les échecs de requête et le circuit breaker."""
        self._error_count += 1
        self._consecutive_failures += 1
        
        # Ouvrir le circuit breaker si trop d'échecs consécutifs
        if self._consecutive_failures >= self._circuit_failure_threshold and not self._circuit_open:
            self._circuit_open = True
            self._circuit_open_until = timezone.now() + timedelta(seconds=self._circuit_recovery_timeout)
            logger.warning(f"Circuit breaker ouvert pour {self.service_name} après {self._consecutive_failures} échecs")
    
    def _update_health_status(self, is_healthy: bool, response_time: float, error_message: Optional[str]):
        """Met à jour le statut de santé du service."""
        if is_healthy:
            self._health_status = ServiceStatus.HEALTHY
            self._consecutive_failures = 0
        else:
            self._consecutive_failures += 1
            if self._consecutive_failures >= self._max_consecutive_failures:
                self._health_status = ServiceStatus.UNHEALTHY
            else:
                self._health_status = ServiceStatus.UNKNOWN
        
        self._last_health_check = timezone.now()
    
    def _get_adapter_metrics(self) -> Dict[str, Any]:
        """Retourne les métriques de l'adaptateur."""
        avg_response_time = 0
        if self._request_count > 0:
            avg_response_time = (self._total_response_time / self._request_count) * 1000
        
        error_rate = 0
        if self._request_count > 0:
            error_rate = (self._error_count / self._request_count) * 100
        
        return {
            'total_requests': self._request_count,
            'total_errors': self._error_count,
            'error_rate_percent': round(error_rate, 2),
            'avg_response_time_ms': round(avg_response_time, 2),
            'consecutive_failures': self._consecutive_failures,
            'health_status': self._health_status.value,
            'last_health_check': self._last_health_check.isoformat() if self._last_health_check else None
        }
    
    def get_health_check(self) -> ServiceHealthCheck:
        """Retourne un check de santé complet."""
        # Effectuer un check si nécessaire
        if (not self._last_health_check or 
            timezone.now() - self._last_health_check > timedelta(seconds=self._health_check_interval)):
            self.test_connection()
        
        return ServiceHealthCheck(
            service_name=self.service_name,
            status=self._health_status,
            response_time_ms=int(self._total_response_time / max(self._request_count, 1) * 1000),
            last_check=self._last_health_check or timezone.now(),
            consecutive_failures=self._consecutive_failures
        )


class SuricataDockerAdapter(DockerServiceAdapter, SuricataService):
    """
    Adaptateur sophistiqué pour le service Suricata IDS via Docker.
    """
    
    def __init__(self):
        """Initialise l'adaptateur Suricata."""
        suricata_url = getattr(settings, 'SURICATA_API_URL', 'http://nms-suricata:8068')
        super().__init__('suricata', suricata_url)
        
        # Configuration spécifique à Suricata
        self._rules_cache_timeout = 600  # 10 minutes
        self._alerts_cache_timeout = 60   # 1 minute
        
        # Statistiques Suricata
        self._rules_added = 0
        self._rules_deleted = 0
        self._alerts_fetched = 0
        self._validations_performed = 0
    
    def add_rule(self, rule_content: str, filename: Optional[str] = None) -> bool:
        """
        Ajoute une règle Suricata au fichier de règles approprié.
        
        Args:
            rule_content: Contenu de la règle au format Suricata
            filename: Nom du fichier de règles (optionnel)
            
        Returns:
            True si l'ajout a réussi
        """
        try:
            data = {
                'rule': rule_content,
                'filename': filename or 'custom.rules',
                'enabled': True
            }
            
            result = self.call_api('/rules', method='POST', data=data)
            
            if result.get('success') or not result.get('error'):
                self._rules_added += 1
                # Invalider le cache des règles
                cache.delete(f"{self._cache_prefix}_rules")
                logger.info(f"Règle Suricata ajoutée avec succès: {rule_content[:50]}...")
                return True
            else:
                logger.error(f"Erreur lors de l'ajout de la règle Suricata: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"Exception lors de l'ajout de la règle Suricata: {str(e)}")
            return False
    
    def delete_rule(self, rule_id: str) -> bool:
        """
        Supprime une règle Suricata par son ID.
        
        Args:
            rule_id: ID de la règle Suricata (SID)
            
        Returns:
            True si la suppression a réussi
        """
        try:
            result = self.call_api(f'/rules/{rule_id}', method='DELETE')
            
            if result.get('success') or not result.get('error'):
                self._rules_deleted += 1
                # Invalider le cache des règles
                cache.delete(f"{self._cache_prefix}_rules")
                logger.info(f"Règle Suricata supprimée: {rule_id}")
                return True
            else:
                logger.error(f"Erreur lors de la suppression de la règle Suricata: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"Exception lors de la suppression de la règle Suricata: {str(e)}")
            return False
    
    def reload_rules(self) -> bool:
        """
        Recharge les règles Suricata sans redémarrer le service.
        
        Returns:
            True si le rechargement a réussi
        """
        try:
            result = self.call_api('/reload', method='POST')
            
            if result.get('success') or not result.get('error'):
                # Invalider tous les caches liés aux règles
                cache.delete_many([
                    f"{self._cache_prefix}_rules",
                    f"{self._cache_prefix}_status"
                ])
                logger.info("Règles Suricata rechargées avec succès")
                return True
            else:
                logger.error(f"Erreur lors du rechargement des règles Suricata: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"Exception lors du rechargement des règles Suricata: {str(e)}")
            return False
    
    def get_alerts(self, since: Optional[datetime] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Récupère les alertes générées par Suricata.
        
        Args:
            since: Date/heure à partir de laquelle récupérer les alertes (optionnel)
            limit: Nombre maximum d'alertes à récupérer
            
        Returns:
            Liste des alertes Suricata
        """
        try:
            self._alerts_fetched += 1
            
            # Préparer les paramètres
            params = {'limit': min(limit, 1000)}  # Limiter à 1000 max
            if since:
                params['since'] = since.isoformat()
            
            # Vérifier le cache
            cache_key = f"{self._cache_prefix}_alerts_{since}_{limit}"
            cached_alerts = cache.get(cache_key)
            if cached_alerts:
                return cached_alerts
            
            # Construire l'URL avec paramètres
            endpoint = '/alerts'
            if params:
                query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
                endpoint += f"?{query_string}"
            
            result = self.call_api(endpoint, method='GET')
            
            if result.get('error'):
                logger.error(f"Erreur lors de la récupération des alertes Suricata: {result.get('error')}")
                return []
            
            alerts = result.get('alerts', [])
            
            # Enrichir les alertes avec des métadonnées
            enriched_alerts = []
            for alert in alerts:
                enriched_alert = {
                    **alert,
                    'source': 'suricata',
                    'retrieved_at': timezone.now().isoformat(),
                    'enriched': True
                }
                
                # Ajouter des classifications si disponibles
                if 'signature' in alert:
                    enriched_alert['classification'] = self._classify_alert(alert['signature'])
                
                enriched_alerts.append(enriched_alert)
            
            # Mettre en cache
            cache.set(cache_key, enriched_alerts, self._alerts_cache_timeout)
            
            logger.info(f"Récupéré {len(enriched_alerts)} alertes Suricata")
            return enriched_alerts
            
        except Exception as e:
            logger.error(f"Exception lors de la récupération des alertes Suricata: {str(e)}")
            return []
    
    def validate_rule(self, rule_content: str) -> Dict[str, Any]:
        """
        Valide la syntaxe d'une règle Suricata.
        
        Args:
            rule_content: Contenu de la règle à valider
            
        Returns:
            Résultat de la validation avec éventuelles erreurs
        """
        try:
            self._validations_performed += 1
            
            data = {'rule': rule_content}
            result = self.call_api('/validate', method='POST', data=data)
            
            if result.get('error'):
                return {
                    'valid': False,
                    'errors': [result.get('error')],
                    'warnings': [],
                    'suggestions': []
                }
            
            # Traiter la réponse de validation
            validation_result = {
                'valid': result.get('valid', True),
                'errors': result.get('errors', []),
                'warnings': result.get('warnings', []),
                'suggestions': result.get('suggestions', []),
                'sid': self._extract_sid_from_rule(rule_content),
                'validated_at': timezone.now().isoformat()
            }
            
            # Ajouter des validations supplémentaires côté client
            additional_checks = self._perform_additional_validation(rule_content)
            validation_result['warnings'].extend(additional_checks.get('warnings', []))
            validation_result['suggestions'].extend(additional_checks.get('suggestions', []))
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Exception lors de la validation de la règle Suricata: {str(e)}")
            return {
                'valid': False,
                'errors': [f"Erreur de validation: {str(e)}"],
                'warnings': [],
                'suggestions': []
            }
    
    def get_rules(self) -> List[Dict[str, Any]]:
        """Récupère toutes les règles Suricata actives."""
        try:
            # Vérifier le cache
            cache_key = f"{self._cache_prefix}_rules"
            cached_rules = cache.get(cache_key)
            if cached_rules:
                return cached_rules
            
            result = self.call_api('/rules', method='GET')
            
            if result.get('error'):
                logger.error(f"Erreur lors de la récupération des règles Suricata: {result.get('error')}")
                return []
            
            rules = result.get('rules', [])
            
            # Enrichir les règles avec des métadonnées
            enriched_rules = []
            for rule in rules:
                enriched_rule = {
                    **rule,
                    'source': 'suricata',
                    'retrieved_at': timezone.now().isoformat(),
                    'sid': self._extract_sid_from_rule(rule.get('content', '')),
                    'classification': self._classify_rule(rule.get('content', ''))
                }
                enriched_rules.append(enriched_rule)
            
            # Mettre en cache
            cache.set(cache_key, enriched_rules, self._rules_cache_timeout)
            
            return enriched_rules
            
        except Exception as e:
            logger.error(f"Exception lors de la récupération des règles Suricata: {str(e)}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques de l'adaptateur Suricata."""
        base_stats = self._get_adapter_metrics()
        
        suricata_stats = {
            **base_stats,
            'rules_added': self._rules_added,
            'rules_deleted': self._rules_deleted,
            'alerts_fetched': self._alerts_fetched,
            'validations_performed': self._validations_performed
        }
        
        return suricata_stats
    
    def _classify_alert(self, signature: str) -> str:
        """Classifie une alerte selon sa signature."""
        signature_lower = signature.lower()
        
        if any(keyword in signature_lower for keyword in ['malware', 'trojan', 'virus']):
            return 'malware'
        elif any(keyword in signature_lower for keyword in ['attack', 'exploit', 'vulnerability']):
            return 'attack'
        elif any(keyword in signature_lower for keyword in ['scan', 'probe', 'reconnaissance']):
            return 'reconnaissance'
        elif any(keyword in signature_lower for keyword in ['ddos', 'flood', 'dos']):
            return 'dos'
        else:
            return 'other'
    
    def _classify_rule(self, rule_content: str) -> str:
        """Classifie une règle selon son contenu."""
        rule_lower = rule_content.lower()
        
        if 'alert' in rule_lower:
            return 'detection'
        elif 'drop' in rule_lower or 'reject' in rule_lower:
            return 'prevention'
        elif 'pass' in rule_lower:
            return 'whitelist'
        else:
            return 'unknown'
    
    def _extract_sid_from_rule(self, rule_content: str) -> Optional[str]:
        """Extrait le SID d'une règle Suricata."""
        import re
        match = re.search(r'sid\s*:\s*(\d+)', rule_content)
        return match.group(1) if match else None
    
    def _perform_additional_validation(self, rule_content: str) -> Dict[str, List[str]]:
        """Effectue des validations supplémentaires côté client."""
        warnings = []
        suggestions = []
        
        # Vérifier la présence d'options importantes
        if 'msg:' not in rule_content:
            warnings.append("Option 'msg' manquante")
        
        if 'sid:' not in rule_content:
            warnings.append("Option 'sid' manquante")
        
        if 'rev:' not in rule_content:
            suggestions.append("Considérer l'ajout d'une option 'rev'")
        
        # Vérifier le format des adresses IP
        import re
        ip_matches = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', rule_content)
        for ip in ip_matches:
            parts = ip.split('.')
            if any(int(part) > 255 for part in parts):
                warnings.append(f"Adresse IP invalide: {ip}")
        
        return {'warnings': warnings, 'suggestions': suggestions}


class Fail2BanDockerAdapter(DockerServiceAdapter, Fail2BanService):
    """
    Adaptateur sophistiqué pour le service Fail2Ban via Docker.
    """
    
    def __init__(self):
        """Initialise l'adaptateur Fail2Ban."""
        fail2ban_url = getattr(settings, 'FAIL2BAN_API_URL', 'http://nms-fail2ban:5001')
        super().__init__('fail2ban', fail2ban_url)
        
        # Configuration spécifique à Fail2Ban
        self._jails_cache_timeout = 300  # 5 minutes
        self._banned_ips_cache_timeout = 60  # 1 minute
        
        # Statistiques Fail2Ban
        self._manual_bans = 0
        self._manual_unbans = 0
        self._jail_queries = 0
    
    def get_jails(self) -> List[Jail]:
        """
        Récupère la liste des prisons (jails) configurées.
        
        Returns:
            Liste des prisons Fail2Ban
        """
        try:
            self._jail_queries += 1
            
            # Vérifier le cache
            cache_key = f"{self._cache_prefix}_jails"
            cached_jails = cache.get(cache_key)
            if cached_jails:
                return cached_jails
            
            result = self.call_api('/jails', method='GET')
            
            if result.get('error'):
                logger.error(f"Erreur lors de la récupération des jails Fail2Ban: {result.get('error')}")
                return []
            
            jails_data = result.get('jails', [])
            jails = []
            
            for jail_data in jails_data:
                jail = Jail(
                    name=jail_data.get('name', 'unknown'),
                    enabled=jail_data.get('enabled', False),
                    filter_name=jail_data.get('filter', ''),
                    action=jail_data.get('action', ''),
                    max_retry=jail_data.get('maxretry', 3),
                    find_time=jail_data.get('findtime', 600),
                    ban_time=jail_data.get('bantime', 3600),
                    currently_failed=jail_data.get('currently_failed', 0),
                    total_failed=jail_data.get('total_failed', 0),
                    currently_banned=jail_data.get('currently_banned', 0),
                    total_banned=jail_data.get('total_banned', 0)
                )
                jails.append(jail)
            
            # Mettre en cache
            cache.set(cache_key, jails, self._jails_cache_timeout)
            
            logger.info(f"Récupéré {len(jails)} jails Fail2Ban")
            return jails
            
        except Exception as e:
            logger.error(f"Exception lors de la récupération des jails Fail2Ban: {str(e)}")
            return []
    
    def get_banned_ips(self, jail: Optional[str] = None) -> List[BannedIP]:
        """
        Récupère la liste des IPs bannies, éventuellement filtrée par prison.
        
        Args:
            jail: Nom de la prison (optionnel)
            
        Returns:
            Liste des IPs bannies
        """
        try:
            # Vérifier le cache
            cache_key = f"{self._cache_prefix}_banned_ips_{jail or 'all'}"
            cached_banned_ips = cache.get(cache_key)
            if cached_banned_ips:
                return cached_banned_ips
            
            endpoint = '/banned'
            if jail:
                endpoint += f'?jail={jail}'
            
            result = self.call_api(endpoint, method='GET')
            
            if result.get('error'):
                logger.error(f"Erreur lors de la récupération des IPs bannies: {result.get('error')}")
                return []
            
            banned_data = result.get('banned_ips', [])
            banned_ips = []
            
            for banned_item in banned_data:
                banned_ip = BannedIP(
                    ip_address=banned_item.get('ip', ''),
                    jail_name=banned_item.get('jail', ''),
                    ban_time=self._parse_datetime(banned_item.get('ban_time')),
                    unban_time=self._parse_datetime(banned_item.get('unban_time')),
                    attempts=banned_item.get('attempts', 0),
                    matches=banned_item.get('matches', [])
                )
                banned_ips.append(banned_ip)
            
            # Mettre en cache
            cache.set(cache_key, banned_ips, self._banned_ips_cache_timeout)
            
            logger.info(f"Récupéré {len(banned_ips)} IPs bannies")
            return banned_ips
            
        except Exception as e:
            logger.error(f"Exception lors de la récupération des IPs bannies: {str(e)}")
            return []
    
    def ban_ip(self, ip: str, jail: str, duration: Optional[int] = None) -> bool:
        """
        Banni manuellement une IP dans une prison donnée.
        
        Args:
            ip: Adresse IP à bannir
            jail: Nom de la prison
            duration: Durée du bannissement en secondes (optionnel)
            
        Returns:
            True si le bannissement a réussi
        """
        try:
            self._manual_bans += 1
            
            data = {
                'ip': ip,
                'jail': jail
            }
            
            if duration:
                data['duration'] = duration
            
            result = self.call_api('/ban', method='POST', data=data)
            
            if result.get('success') or not result.get('error'):
                # Invalider le cache des IPs bannies
                cache.delete_many([
                    f"{self._cache_prefix}_banned_ips_all",
                    f"{self._cache_prefix}_banned_ips_{jail}"
                ])
                logger.info(f"IP {ip} bannie manuellement dans la jail {jail}")
                return True
            else:
                logger.error(f"Erreur lors du bannissement de {ip}: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"Exception lors du bannissement de {ip}: {str(e)}")
            return False
    
    def unban_ip(self, ip: str, jail: Optional[str] = None) -> bool:
        """
        Lève le bannissement d'une IP, éventuellement seulement dans une prison donnée.
        
        Args:
            ip: Adresse IP à débannir
            jail: Nom de la prison (optionnel, toutes les prisons si non spécifié)
            
        Returns:
            True si le débannissement a réussi
        """
        try:
            self._manual_unbans += 1
            
            data = {'ip': ip}
            if jail:
                data['jail'] = jail
            
            result = self.call_api('/unban', method='POST', data=data)
            
            if result.get('success') or not result.get('error'):
                # Invalider le cache des IPs bannies
                cache_keys = [f"{self._cache_prefix}_banned_ips_all"]
                if jail:
                    cache_keys.append(f"{self._cache_prefix}_banned_ips_{jail}")
                cache.delete_many(cache_keys)
                
                logger.info(f"IP {ip} débannie" + (f" de la jail {jail}" if jail else " de toutes les jails"))
                return True
            else:
                logger.error(f"Erreur lors du débannissement de {ip}: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"Exception lors du débannissement de {ip}: {str(e)}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques de l'adaptateur Fail2Ban."""
        base_stats = self._get_adapter_metrics()
        
        fail2ban_stats = {
            **base_stats,
            'manual_bans': self._manual_bans,
            'manual_unbans': self._manual_unbans,
            'jail_queries': self._jail_queries
        }
        
        return fail2ban_stats
    
    def _parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse une chaîne de date/heure."""
        if not date_str:
            return None
        
        try:
            # Essayer plusieurs formats
            formats = [
                '%Y-%m-%dT%H:%M:%S.%fZ',
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M:%S.%f'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            return None
        except Exception:
            return None


class TrafficControlDockerAdapter(DockerServiceAdapter, FirewallService):
    """
    Adaptateur sophistiqué pour le service Traffic Control (Firewall) via Docker.
    """
    
    def __init__(self):
        """Initialise l'adaptateur Traffic Control."""
        traffic_url = getattr(settings, 'TRAFFIC_CONTROL_API_URL', 'http://nms-traffic-control:8003')
        super().__init__('traffic-control', traffic_url)
        
        # Configuration spécifique au Traffic Control
        self._rules_cache_timeout = 300  # 5 minutes
        
        # Statistiques Traffic Control
        self._rules_added = 0
        self._rules_deleted = 0
        self._ips_blocked = 0
        self._ips_unblocked = 0
    
    def add_rule(self, rule_definition: Dict[str, Any]) -> bool:
        """
        Ajoute une règle au pare-feu.
        
        Args:
            rule_definition: Définition de la règle de pare-feu
            
        Returns:
            True si l'ajout a réussi
        """
        try:
            self._rules_added += 1
            
            result = self.call_api('/firewall/rules', method='POST', data=rule_definition)
            
            if result.get('success') or not result.get('error'):
                # Invalider le cache des règles
                cache.delete(f"{self._cache_prefix}_rules")
                logger.info(f"Règle firewall ajoutée: {rule_definition.get('name', 'unnamed')}")
                return True
            else:
                logger.error(f"Erreur lors de l'ajout de la règle firewall: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"Exception lors de l'ajout de la règle firewall: {str(e)}")
            return False
    
    def delete_rule(self, rule_identifier: str) -> bool:
        """
        Supprime une règle du pare-feu.
        
        Args:
            rule_identifier: Identifiant de la règle à supprimer
            
        Returns:
            True si la suppression a réussi
        """
        try:
            self._rules_deleted += 1
            
            result = self.call_api(f'/firewall/rules/{rule_identifier}', method='DELETE')
            
            if result.get('success') or not result.get('error'):
                # Invalider le cache des règles
                cache.delete(f"{self._cache_prefix}_rules")
                logger.info(f"Règle firewall supprimée: {rule_identifier}")
                return True
            else:
                logger.error(f"Erreur lors de la suppression de la règle firewall: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"Exception lors de la suppression de la règle firewall: {str(e)}")
            return False
    
    def get_rules(self) -> List[Dict[str, Any]]:
        """
        Récupère les règles actuelles du pare-feu.
        
        Returns:
            Liste des règles de pare-feu
        """
        try:
            # Vérifier le cache
            cache_key = f"{self._cache_prefix}_rules"
            cached_rules = cache.get(cache_key)
            if cached_rules:
                return cached_rules
            
            result = self.call_api('/firewall/rules', method='GET')
            
            if result.get('error'):
                logger.error(f"Erreur lors de la récupération des règles firewall: {result.get('error')}")
                return []
            
            rules = result.get('rules', [])
            
            # Enrichir les règles avec des métadonnées
            enriched_rules = []
            for rule in rules:
                enriched_rule = {
                    **rule,
                    'source': 'traffic-control',
                    'retrieved_at': timezone.now().isoformat()
                }
                enriched_rules.append(enriched_rule)
            
            # Mettre en cache
            cache.set(cache_key, enriched_rules, self._rules_cache_timeout)
            
            return enriched_rules
            
        except Exception as e:
            logger.error(f"Exception lors de la récupération des règles firewall: {str(e)}")
            return []
    
    def block_ip(self, ip, duration: Optional[int] = None) -> bool:
        """
        Bloque une adresse IP dans le pare-feu.
        
        Args:
            ip: Adresse IP à bloquer
            duration: Durée du blocage en secondes (optionnel)
            
        Returns:
            True si le blocage a réussi
        """
        try:
            self._ips_blocked += 1
            
            data = {'ip': str(ip)}
            if duration:
                data['duration'] = duration
            
            result = self.call_api('/firewall/block', method='POST', data=data)
            
            if result.get('success') or not result.get('error'):
                logger.info(f"IP {ip} bloquée par le firewall")
                return True
            else:
                logger.error(f"Erreur lors du blocage de {ip}: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"Exception lors du blocage de {ip}: {str(e)}")
            return False
    
    def unblock_ip(self, ip) -> bool:
        """
        Débloque une adresse IP dans le pare-feu.
        
        Args:
            ip: Adresse IP à débloquer
            
        Returns:
            True si le déblocage a réussi
        """
        try:
            self._ips_unblocked += 1
            
            data = {'ip': str(ip)}
            result = self.call_api('/firewall/unblock', method='POST', data=data)
            
            if result.get('success') or not result.get('error'):
                logger.info(f"IP {ip} débloquée par le firewall")
                return True
            else:
                logger.error(f"Erreur lors du déblocage de {ip}: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"Exception lors du déblocage de {ip}: {str(e)}")
            return False
    
    def is_ip_blocked(self, ip) -> bool:
        """
        Vérifie si une adresse IP est actuellement bloquée.
        
        Args:
            ip: Adresse IP à vérifier
            
        Returns:
            True si l'adresse IP est bloquée
        """
        try:
            result = self.call_api(f'/firewall/status/{str(ip)}', method='GET')
            
            if result.get('error'):
                logger.error(f"Erreur lors de la vérification du statut de {ip}: {result.get('error')}")
                return False
            
            return result.get('blocked', False)
            
        except Exception as e:
            logger.error(f"Exception lors de la vérification du statut de {ip}: {str(e)}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques de l'adaptateur Traffic Control."""
        base_stats = self._get_adapter_metrics()
        
        traffic_stats = {
            **base_stats,
            'rules_added': self._rules_added,
            'rules_deleted': self._rules_deleted,
            'ips_blocked': self._ips_blocked,
            'ips_unblocked': self._ips_unblocked
        }
        
        return traffic_stats


class DockerServiceManager:
    """
    Gestionnaire centralisé pour tous les adaptateurs de services Docker.
    """
    
    def __init__(self):
        """Initialise le gestionnaire avec tous les adaptateurs."""
        self.suricata = SuricataDockerAdapter()
        self.fail2ban = Fail2BanDockerAdapter()
        self.traffic_control = TrafficControlDockerAdapter()
        
        self._adapters = {
            'suricata': self.suricata,
            'fail2ban': self.fail2ban,
            'traffic-control': self.traffic_control
        }
        
        # Monitoring global
        self._monitoring_enabled = True
        self._monitoring_interval = 60  # 1 minute
        self._last_global_check = None
        
        logger.info("DockerServiceManager initialisé avec %d adaptateurs", len(self._adapters))
    
    def get_all_health_checks(self) -> Dict[str, ServiceHealthCheck]:
        """Retourne les checks de santé de tous les services."""
        health_checks = {}
        
        for name, adapter in self._adapters.items():
            try:
                health_checks[name] = adapter.get_health_check()
            except Exception as e:
                logger.error(f"Erreur lors du check de santé de {name}: {str(e)}")
                health_checks[name] = ServiceHealthCheck(
                    service_name=name,
                    status=ServiceStatus.UNKNOWN,
                    response_time_ms=0,
                    last_check=timezone.now(),
                    error_message=str(e)
                )
        
        return health_checks
    
    def get_global_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques globales de tous les services."""
        global_stats = {
            'services_count': len(self._adapters),
            'healthy_services': 0,
            'unhealthy_services': 0,
            'services': {}
        }
        
        for name, adapter in self._adapters.items():
            try:
                service_stats = adapter.get_statistics()
                global_stats['services'][name] = service_stats
                
                # Compter les services en bonne santé
                if service_stats.get('health_status') == 'healthy':
                    global_stats['healthy_services'] += 1
                else:
                    global_stats['unhealthy_services'] += 1
                    
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des stats de {name}: {str(e)}")
                global_stats['unhealthy_services'] += 1
        
        return global_stats
    
    def test_all_connections(self) -> Dict[str, bool]:
        """Teste la connexion de tous les services."""
        results = {}
        
        for name, adapter in self._adapters.items():
            try:
                results[name] = adapter.test_connection()
            except Exception as e:
                logger.error(f"Erreur lors du test de connexion de {name}: {str(e)}")
                results[name] = False
        
        return results
    
    def get_adapter(self, service_name: str) -> Optional[DockerServiceAdapter]:
        """Retourne un adaptateur spécifique."""
        return self._adapters.get(service_name)


# Instance globale du gestionnaire
docker_service_manager = DockerServiceManager()