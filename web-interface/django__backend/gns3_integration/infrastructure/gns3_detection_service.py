"""
Service de détection permanent du serveur GNS3.

Ce service vérifie en permanence la disponibilité du serveur GNS3
et gère le mode adaptatif (GNS3 disponible/indisponible).
"""

import asyncio
import logging
import aiohttp
import subprocess
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from django.core.cache import cache
from django.conf import settings

from gns3_integration.domain.exceptions import GNS3ConnectionError

logger = logging.getLogger(__name__)


@dataclass
class GNS3ServerStatus:
    """État du serveur GNS3."""
    is_available: bool
    last_check: datetime
    version: Optional[str] = None
    projects_count: int = 0
    error_message: Optional[str] = None
    response_time_ms: Optional[float] = None
    notification_sent: bool = False  # Nouvelle propriété pour tracking notifications


class GNS3DetectionService:
    """
    Service de détection permanent du serveur GNS3.
    
    Fonctionnalités :
    - Détection automatique de la disponibilité
    - Cache des statuts pour éviter les appels répétés
    - Mode adaptatif selon la disponibilité
    - Gestion des timeouts et reconnexions
    """
    
    def __init__(self, host: str = None, port: int = None):
        from django.conf import settings
        host = host or getattr(settings, 'GNS3_HOST', 'localhost')
        port = port or getattr(settings, 'GNS3_PORT', 3080)
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.cache_key = f"gns3_server_status_{host}_{port}"
        self.cache_timeout = 30  # Cache pendant 30 secondes
        self.detection_timeout = 5  # Timeout pour la détection
        
        # Configuration adaptative
        self.retry_intervals = [5, 10, 30, 60]  # Intervalles de retry en secondes
        self.current_retry_index = 0
        
        # Configuration des notifications système
        self.notifications_enabled = True
        self.last_notification_status = None  # Pour éviter les notifications répétées
        self.notification_cache_key = f"gns3_notification_sent_{host}_{port}"
        
    async def check_server_availability(self) -> GNS3ServerStatus:
        """
        Vérifie la disponibilité du serveur GNS3.
        
        Returns:
            GNS3ServerStatus avec les informations de statut
        """
        start_time = datetime.now()
        
        try:
            # Forcer l'usage d'un connector sans SSL pour éviter les erreurs de configuration
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.detection_timeout),
                connector=connector
            ) as session:
                # Tester l'endpoint version (plus léger que projects)
                async with session.get(f"{self.base_url}/v2/version") as response:
                    if response.status == 200:
                        version_data = await response.json()
                        response_time = (datetime.now() - start_time).total_seconds() * 1000
                        
                        # Récupérer le nombre de projets
                        projects_count = await self._get_projects_count(session)
                        
                        status = GNS3ServerStatus(
                            is_available=True,
                            last_check=datetime.now(),
                            version=version_data.get('version', 'Unknown'),
                            projects_count=projects_count,
                            response_time_ms=response_time
                        )
                        
                        # Reset retry index si connexion réussie
                        self.current_retry_index = 0
                        
                        logger.info(f"Serveur GNS3 disponible - Version: {status.version}, "
                                  f"Projets: {status.projects_count}, "
                                  f"Temps de réponse: {status.response_time_ms:.0f}ms")
                        
                        # Envoyer notification de détection réussie
                        await self._send_detection_notification(status)
                        
                        return status
                    else:
                        raise GNS3ConnectionError(f"HTTP {response.status}")
                        
        except asyncio.TimeoutError:
            error_msg = f"Timeout lors de la connexion au serveur GNS3 ({self.base_url})"
            logger.warning(error_msg)
            status = self._create_unavailable_status(error_msg)
            await self._send_detection_notification(status)
            return status
            
        except aiohttp.ClientConnectorError as e:
            error_msg = f"Impossible de se connecter au serveur GNS3: {e}"
            logger.warning(error_msg)
            status = self._create_unavailable_status(error_msg)
            await self._send_detection_notification(status)
            return status
            
        except Exception as e:
            error_msg = f"Erreur lors de la vérification GNS3: {e}"
            logger.error(error_msg)
            status = self._create_unavailable_status(error_msg)
            await self._send_detection_notification(status)
            return status
    
    async def _get_projects_count(self, session: aiohttp.ClientSession) -> int:
        """Récupère le nombre de projets GNS3."""
        try:
            async with session.get(f"{self.base_url}/v2/projects") as response:
                if response.status == 200:
                    projects = await response.json()
                    return len(projects)
        except Exception as e:
            logger.debug(f"Impossible de récupérer le nombre de projets: {e}")
        return 0
    
    def _create_unavailable_status(self, error_message: str) -> GNS3ServerStatus:
        """Crée un statut indisponible."""
        return GNS3ServerStatus(
            is_available=False,
            last_check=datetime.now(),
            error_message=error_message
        )
    
    def get_cached_status(self) -> Optional[GNS3ServerStatus]:
        """Récupère le statut depuis le cache."""
        return cache.get(self.cache_key)
    
    def cache_status(self, status: GNS3ServerStatus):
        """Met en cache le statut."""
        cache.set(self.cache_key, status, self.cache_timeout)
    
    async def get_server_status(self, force_check: bool = False) -> GNS3ServerStatus:
        """
        Récupère le statut du serveur (avec cache).
        
        Args:
            force_check: Force une nouvelle vérification
            
        Returns:
            GNS3ServerStatus
        """
        if not force_check:
            cached_status = self.get_cached_status()
            if cached_status:
                return cached_status
        
        # Vérification en temps réel
        status = await self.check_server_availability()
        self.cache_status(status)
        return status
    
    def get_next_retry_interval(self) -> int:
        """Calcule le prochain intervalle de retry."""
        if self.current_retry_index < len(self.retry_intervals):
            interval = self.retry_intervals[self.current_retry_index]
            self.current_retry_index += 1
        else:
            interval = self.retry_intervals[-1]  # Utiliser le dernier intervalle
        
        return interval
    
    def should_attempt_connection(self) -> bool:
        """
        Détermine si on devrait tenter une connexion.
        
        Utilise une stratégie de backoff pour éviter les tentatives trop fréquentes.
        """
        cached_status = self.get_cached_status()
        if not cached_status:
            return True
        
        if cached_status.is_available:
            return True
        
        # Si le serveur était indisponible, utiliser le backoff
        time_since_last_check = datetime.now() - cached_status.last_check
        retry_interval = timedelta(seconds=self.get_next_retry_interval())
        
        return time_since_last_check >= retry_interval
    
    async def _send_detection_notification(self, status: GNS3ServerStatus):
        """
        Envoie une notification système Ubuntu pour la détection du serveur GNS3.
        
        Args:
            status: Statut du serveur GNS3
        """
        if not self.notifications_enabled:
            return
        
        try:
            # Vérifier si une notification a déjà été envoyée récemment
            last_notification = cache.get(self.notification_cache_key)
            
            # Envoyer notification seulement si:
            # 1. Aucune notification récente OU
            # 2. Le statut a changé (indisponible -> disponible)
            if (not last_notification or 
                (self.last_notification_status == False and status.is_available)):
                
                if status.is_available:
                    # Notification de détection réussie
                    title = "🟢 Serveur GNS3 Détecté"
                    message = (f"✅ Serveur GNS3 opérationnel\n"
                             f"🔧 Version: {status.version}\n"
                             f"📊 Projets: {status.projects_count}\n"
                             f"⚡ Temps de réponse: {status.response_time_ms:.0f}ms")
                    icon = "network-workgroup"
                    urgency = "normal"
                else:
                    # Notification de perte de connexion
                    title = "🔴 Serveur GNS3 Indisponible"
                    message = f"❌ Connexion perdue\n⚠️ {status.error_message}"
                    icon = "network-error"
                    urgency = "critical"
                
                # Construire et exécuter la commande notify-send
                cmd = [
                    "notify-send",
                    title,
                    message,
                    f"--icon={icon}",
                    f"--urgency={urgency}",
                    "--app-name=NMS-Backend",
                    "--expire-time=5000"  # 5 secondes
                ]
                
                # Exécuter la notification en arrière-plan
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.communicate()
                
                # Mettre en cache pour éviter les notifications répétées
                cache.set(self.notification_cache_key, datetime.now(), 300)  # 5 minutes
                self.last_notification_status = status.is_available
                
                logger.info(f"📱 Notification système envoyée: {title}")
                
        except Exception as e:
            logger.warning(f"Erreur lors de l'envoi de notification: {e}")
    
    def enable_notifications(self, enabled: bool = True):
        """
        Active ou désactive les notifications système.
        
        Args:
            enabled: True pour activer, False pour désactiver
        """
        self.notifications_enabled = enabled
        logger.info(f"Notifications système {'activées' if enabled else 'désactivées'}")
    
    async def force_notification_test(self):
        """
        Force l'envoi d'une notification de test.
        
        Returns:
            bool: True si la notification a été envoyée avec succès
        """
        try:
            cmd = [
                "notify-send",
                "🧪 Test NMS Backend",
                "🔬 Notification de test du système de détection GNS3\n✅ Système opérationnel",
                "--icon=applications-system",
                "--urgency=low",
                "--app-name=NMS-Backend",
                "--expire-time=3000"
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info("📱 Notification de test envoyée avec succès")
                return True
            else:
                logger.error(f"Erreur notification test: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors du test de notification: {e}")
            return False


# Instance globale du service de détection
detection_service = GNS3DetectionService()

# Activer les notifications par défaut
detection_service.enable_notifications(True)


async def get_gns3_server_status(force_check: bool = False) -> GNS3ServerStatus:
    """
    Fonction utilitaire pour récupérer le statut du serveur GNS3.
    
    Args:
        force_check: Force une nouvelle vérification
        
    Returns:
        GNS3ServerStatus
    """
    return await detection_service.get_server_status(force_check)


async def test_notification_system() -> bool:
    """
    Teste le système de notifications.
    
    Returns:
        True si le test réussit
    """
    return await detection_service.force_notification_test()


def enable_gns3_notifications(enabled: bool = True):
    """
    Active ou désactive les notifications GNS3.
    
    Args:
        enabled: True pour activer, False pour désactiver
    """
    detection_service.enable_notifications(enabled)


async def force_gns3_detection_with_notification() -> GNS3ServerStatus:
    """
    Force une détection GNS3 et envoie une notification.
    
    Returns:
        GNS3ServerStatus
    """
    # Activer les notifications
    detection_service.enable_notifications(True)
    
    # Vider le cache pour forcer une nouvelle détection
    cache.delete(detection_service.cache_key)
    cache.delete(detection_service.notification_cache_key)
    
    # Forçer une nouvelle détection
    status = await detection_service.get_server_status(force_check=True)
    
    return status


def is_gns3_available() -> bool:
    """
    Vérification synchrone rapide de la disponibilité GNS3.
    
    Returns:
        True si GNS3 est disponible selon le cache
    """
    cached_status = detection_service.get_cached_status()
    return cached_status.is_available if cached_status else False


def get_gns3_notification_status() -> dict:
    """
    Récupère le statut du système de notifications.
    
    Returns:
        Dict avec les informations de notification
    """
    last_notification = cache.get(detection_service.notification_cache_key)
    
    return {
        'notifications_enabled': detection_service.notifications_enabled,
        'last_notification_sent': last_notification.isoformat() if last_notification else None,
        'last_notification_status': detection_service.last_notification_status,
        'notification_cache_active': bool(last_notification)
    }