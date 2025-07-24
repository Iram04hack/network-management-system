"""
Client HAProxy sécurisé pour interagir avec HAProxy via socket de stats ou HTTP.

Ce module fournit une interface sécurisée pour HAProxy avec validation d'entrées
et protection contre les injections de commandes.
"""

import socket
import logging
import re
from typing import Dict, Any, List, Optional, Union
from contextlib import contextmanager

from ..base import BaseAPIClient
from ..infrastructure.input_validator import StringValidator, CompositeValidator, PortValidator
from ..domain.exceptions import (
    ValidationException,
    APIConnectionException,
    APIClientException
)

logger = logging.getLogger(__name__)

class HAProxySecurityError(APIClientException):
    """Exception pour les erreurs de sécurité HAProxy."""
    pass

class HAProxyClient(BaseAPIClient):
    """
    Client sécurisé pour interagir avec HAProxy via socket de stats ou HTTP.
    
    Cette implémentation corrige les vulnérabilités de sécurité identifiées :
    - Protection contre l'injection de commandes
    - Validation stricte des paramètres d'entrée
    - Gestion sécurisée des timeouts et des connexions
    - Logging sécurisé sans fuite d'informations sensibles
    """
    
    # Patterns de validation pour les noms HAProxy
    VALID_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')
    VALID_COMMAND_PATTERN = re.compile(r'^[a-zA-Z0-9_\s\-/]+$')
    
    # Commandes HAProxy autorisées (whitelist)
    ALLOWED_COMMANDS = {
        'show info',
        'show stat',
        'show stat json',
        'show servers state',
        'show pools',
        'show sess',
        'show errors',
        'show version'
    }
    
    # Templates de commandes sécurisées avec paramètres
    SAFE_COMMAND_TEMPLATES = {
        'enable_server': 'enable server {backend}/{server}',
        'disable_server': 'disable server {backend}/{server}',
        'set_server_state': 'set server {backend}/{server} state {state}',
        'set_server_weight': 'set weight {backend}/{server} {weight}',
        'show_server_state': 'show servers state {backend}'
    }
    
    # États valides pour les serveurs
    VALID_SERVER_STATES = {'ready', 'drain', 'maint'}
    
    def __init__(
        self, 
        stats_socket: Optional[str] = "/var/run/haproxy.sock",
        host: Optional[str] = None, 
        port: Optional[int] = 1936,
        username: Optional[str] = "admin", 
        password: Optional[str] = "admin",
        verify_ssl: bool = True, 
        timeout: int = 10,
        socket_timeout: float = 5.0
    ):
        """
        Initialise le client HAProxy avec validation sécurisée.
        
        Args:
            stats_socket: Chemin vers le socket de stats
            host: Hôte pour l'interface stats HTTP
            port: Port pour l'interface stats HTTP
            username: Nom d'utilisateur pour l'interface HTTP
            password: Mot de passe pour l'interface HTTP
            verify_ssl: Vérifier les certificats SSL
            timeout: Délai d'attente en secondes pour HTTP
            socket_timeout: Délai d'attente pour les connexions socket
        """
        self.stats_socket = stats_socket
        self.socket_timeout = socket_timeout
        self.use_socket = bool(stats_socket and not host)
        
        # Initialiser les validateurs
        self._init_validators()
        
        if host:
            # Valider l'host avant utilisation
            validated_host = self.validators.validate({'host': host, 'port': port})
            base_url = f"http://{validated_host['host']}:{validated_host['port']}"
            super().__init__(
                base_url=base_url, 
                username=username, 
                password=password, 
                verify_ssl=verify_ssl, 
                timeout=timeout
            )
        else:
            # Mode socket uniquement
            super().__init__(
                base_url="socket://haproxy", 
                verify_ssl=verify_ssl, 
                timeout=timeout
            )
        
        logger.info(f"HAProxyClient initialisé en mode {'socket' if self.use_socket else 'HTTP'}")
    
    def _init_validators(self):
        """Initialise les validateurs pour les paramètres d'entrée."""
        self.validators = CompositeValidator({
            'backend': StringValidator(
                min_length=1,
                max_length=50,
                pattern=self.VALID_NAME_PATTERN,
                strip_whitespace=True
            ),
            'server': StringValidator(
                min_length=1,
                max_length=50,
                pattern=self.VALID_NAME_PATTERN,
                strip_whitespace=True
            ),
            'host': StringValidator(
                min_length=1,
                max_length=253,  # Max FQDN length
                strip_whitespace=True
            ),
            'port': PortValidator(
                allow_well_known=True,
                allow_registered=True,
                allow_dynamic=True
            ),
            'state': StringValidator(
                min_length=1,
                max_length=10,
                strip_whitespace=True,
                case_sensitive=False
            ),
            'weight': StringValidator(
                pattern=re.compile(r'^\d{1,3}$')  # 0-999
            )
        })
    
    def _validate_haproxy_name(self, name: str, field_name: str) -> str:
        """
        Valide un nom HAProxy (backend, serveur, etc.).
        
        Args:
            name: Nom à valider
            field_name: Nom du champ pour les erreurs
            
        Returns:
            Nom validé
            
        Raises:
            ValidationException: Si le nom est invalide
        """
        if not isinstance(name, str):
            raise ValidationException(
                f"{field_name} doit être une chaîne",
                field_name, str(name)
            )
        
        name = name.strip()
        
        if not name:
            raise ValidationException(
                f"{field_name} ne peut pas être vide",
                field_name, name
            )
        
        if len(name) > 50:
            raise ValidationException(
                f"{field_name} trop long (max 50 caractères)",
                field_name, name
            )
        
        if not self.VALID_NAME_PATTERN.match(name):
            raise ValidationException(
                f"{field_name} contient des caractères invalides. "
                "Seuls alphanumériques, underscore et tiret autorisés",
                field_name, name
            )
        
        return name
    
    def _build_safe_command(self, template_key: str, **params) -> str:
        """
        Construit une commande sécurisée à partir d'un template.
        
        Args:
            template_key: Clé du template de commande
            **params: Paramètres pour le template
            
        Returns:
            Commande sécurisée
            
        Raises:
            HAProxySecurityError: Si le template n'existe pas ou paramètres invalides
        """
        if template_key not in self.SAFE_COMMAND_TEMPLATES:
            raise HAProxySecurityError(f"Template de commande non autorisé: {template_key}")
        
        template = self.SAFE_COMMAND_TEMPLATES[template_key]
        
        # Valider tous les paramètres avant substitution
        validated_params = {}
        for key, value in params.items():
            if key in ['backend', 'server']:
                validated_params[key] = self._validate_haproxy_name(value, key)
            elif key == 'state':
                if value.lower() not in self.VALID_SERVER_STATES:
                    raise ValidationException(
                        f"État de serveur invalide. Autorisés: {self.VALID_SERVER_STATES}",
                        key, value
                    )
                validated_params[key] = value.lower()
            elif key == 'weight':
                try:
                    weight_int = int(value)
                    if not 0 <= weight_int <= 256:
                        raise ValueError()
                    validated_params[key] = str(weight_int)
                except ValueError:
                    raise ValidationException(
                        "Poids doit être un entier entre 0 et 256",
                        key, value
                    )
            else:
                # Validation générique pour autres paramètres
                validated_params[key] = str(value).strip()
        
        try:
            command = template.format(**validated_params)
        except KeyError as e:
            raise HAProxySecurityError(f"Paramètre manquant pour la commande: {e}")
        
        # Validation finale de la commande construite
        if not self.VALID_COMMAND_PATTERN.match(command):
            raise HAProxySecurityError(f"Commande générée contient des caractères interdits")
        
        return command
    
    @contextmanager
    def _socket_connection(self):
        """
        Gestionnaire de contexte pour les connexions socket sécurisées.
        
        Yields:
            Socket connecté
            
        Raises:
            APIConnectionException: Si la connexion échoue
        """
        if not self.stats_socket:
            raise APIConnectionException("Socket de stats non configuré")
        
        sock = None
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(self.socket_timeout)
            sock.connect(self.stats_socket)
            yield sock
        
        except socket.timeout:
            raise APIConnectionException(
                f"Timeout de connexion au socket HAProxy ({self.socket_timeout}s)"
            )
        except socket.error as e:
            raise APIConnectionException(f"Erreur de connexion au socket HAProxy: {e}")
        except Exception as e:
            raise APIConnectionException(f"Erreur inattendue: {type(e).__name__}: {e}")
        
        finally:
            if sock:
                try:
                    sock.close()
                except Exception:
                    pass  # Ignorer les erreurs de fermeture
    
    def _send_command(self, command: str) -> str:
        """
        Envoie une commande sécurisée au socket HAProxy.
        
        Args:
            command: Commande validée à envoyer
            
        Returns:
            Réponse du socket
            
        Raises:
            HAProxySecurityError: Si la commande n'est pas autorisée
            APIConnectionException: Si la connexion échoue
        """
        # Vérifier que la commande est dans la whitelist ou utilise un template sécurisé
        command_base = command.split()[0:2]  # Premier(s) mot(s) de la commande
        command_prefix = ' '.join(command_base)
        
        is_allowed = (
            command in self.ALLOWED_COMMANDS or
            any(command.startswith(template.split('{')[0].strip()) 
                for template in self.SAFE_COMMAND_TEMPLATES.values())
        )
        
        if not is_allowed:
            raise HAProxySecurityError(f"Commande non autorisée: {command_prefix}")
        
        with self._socket_connection() as sock:
            try:
                # Envoyer la commande
                sock.sendall(f"{command}\n".encode('utf-8'))
                
                # Recevoir la réponse
                response_parts = []
                while True:
                    try:
                        data = sock.recv(4096)
                        if not data:
                            break
                        response_parts.append(data.decode('utf-8'))
                    except socket.timeout:
                        break  # Fin de réponse
                
                response = ''.join(response_parts)
                
                # Log sécurisé (sans détails de la commande)
                logger.debug(f"Commande HAProxy exécutée avec succès, réponse: {len(response)} caractères")
                
                return response
            
            except Exception as e:
                logger.error(f"Erreur lors de l'exécution de la commande HAProxy: {type(e).__name__}")
                raise APIConnectionException(f"Erreur d'exécution de commande: {type(e).__name__}")
    
    def test_connection(self) -> bool:
        """Teste la connexion à HAProxy de manière sécurisée."""
        try:
            if self.use_socket:
                return self._test_socket_connection()
            else:
                response = self.get("stats")
                return response is not None and response.get("success", False)
        except Exception as e:
            logger.error(f"Test de connexion HAProxy échoué: {type(e).__name__}")
            return False
    
    def _test_socket_connection(self) -> bool:
        """Teste la connexion au socket de stats de manière sécurisée."""
        try:
            with self._socket_connection() as sock:
                sock.sendall(b"show info\n")
                data = sock.recv(1024)  # Lecture limitée pour le test
            return len(data) > 0
        except Exception as e:
            logger.error(f"Test de connexion socket HAProxy échoué: {type(e).__name__}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Récupère les statistiques HAProxy de manière sécurisée."""
        try:
            if self.use_socket:
                raw_stats = self._send_command("show stat")
                return self._parse_stats(raw_stats)
            else:
                return self.get("stats/native")
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des stats: {type(e).__name__}")
            return {"success": False, "error": "Erreur de récupération des statistiques"}
    
    def get_info(self) -> Dict[str, Any]:
        """Récupère les informations générales HAProxy de manière sécurisée."""
        try:
            if self.use_socket:
                raw_info = self._send_command("show info")
                return self._parse_info(raw_info)
            else:
                return self.get("stats/info")
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des infos: {type(e).__name__}")
            return {"success": False, "error": "Erreur de récupération des informations"}
    
    def enable_server(self, backend: str, server: str) -> Dict[str, Any]:
        """
        Active un serveur dans un backend de manière sécurisée.
        
        Args:
            backend: Nom du backend (validé)
            server: Nom du serveur (validé)
            
        Returns:
            Résultat de l'opération
        """
        try:
            if self.use_socket:
                command = self._build_safe_command('enable_server', backend=backend, server=server)
                result = self._send_command(command)
                success = "successfully" in result.lower() or not result.strip()
                return {"success": success, "message": "Serveur activé" if success else "Échec d'activation"}
            else:
                # Validation des paramètres pour URL
                validated = self.validators.validate({'backend': backend, 'server': server})
                return self.post(f"stats/admin?action=enable&backend={validated['backend']}&server={validated['server']}")
        
        except (ValidationException, HAProxySecurityError) as e:
            logger.warning(f"Tentative d'activation de serveur avec paramètres invalides: {type(e).__name__}")
            return {"success": False, "error": "Paramètres invalides"}
        except Exception as e:
            logger.error(f"Erreur lors de l'activation du serveur: {type(e).__name__}")
            return {"success": False, "error": "Erreur d'activation du serveur"}
    
    def disable_server(self, backend: str, server: str) -> Dict[str, Any]:
        """
        Désactive un serveur dans un backend de manière sécurisée.
        
        Args:
            backend: Nom du backend (validé)
            server: Nom du serveur (validé)
            
        Returns:
            Résultat de l'opération
        """
        try:
            if self.use_socket:
                command = self._build_safe_command('disable_server', backend=backend, server=server)
                result = self._send_command(command)
                success = "successfully" in result.lower() or not result.strip()
                return {"success": success, "message": "Serveur désactivé" if success else "Échec de désactivation"}
            else:
                # Validation des paramètres pour URL
                validated = self.validators.validate({'backend': backend, 'server': server})
                return self.post(f"stats/admin?action=disable&backend={validated['backend']}&server={validated['server']}")
        
        except (ValidationException, HAProxySecurityError) as e:
            logger.warning(f"Tentative de désactivation de serveur avec paramètres invalides: {type(e).__name__}")
            return {"success": False, "error": "Paramètres invalides"}
        except Exception as e:
            logger.error(f"Erreur lors de la désactivation du serveur: {type(e).__name__}")
            return {"success": False, "error": "Erreur de désactivation du serveur"}
    
    def set_server_state(self, backend: str, server: str, state: str) -> Dict[str, Any]:
        """
        Change l'état d'un serveur de manière sécurisée.
        
        Args:
            backend: Nom du backend (validé)
            server: Nom du serveur (validé)  
            state: État cible ('ready', 'drain', 'maint')
            
        Returns:
            Résultat de l'opération
        """
        try:
            if self.use_socket:
                command = self._build_safe_command('set_server_state', 
                                                 backend=backend, server=server, state=state)
                result = self._send_command(command)
                success = not result.strip() or "successfully" in result.lower()
                return {"success": success, "message": f"État du serveur changé vers {state}" if success else "Échec du changement d'état"}
            else:
                # Validation des paramètres pour URL
                validated = self.validators.validate({'backend': backend, 'server': server, 'state': state})
                return self.post(f"stats/admin?action=state&backend={validated['backend']}&server={validated['server']}&state={validated['state']}")
        
        except (ValidationException, HAProxySecurityError) as e:
            logger.warning(f"Tentative de changement d'état avec paramètres invalides: {type(e).__name__}")
            return {"success": False, "error": "Paramètres invalides"}
        except Exception as e:
            logger.error(f"Erreur lors du changement d'état du serveur: {type(e).__name__}")
            return {"success": False, "error": "Erreur de changement d'état"}
    
    def get_backends(self) -> List[str]:
        """Récupère la liste des backends de manière sécurisée."""
        try:
            stats = self.get_stats()
            backends = set()
            
            if stats.get("success", True) and "data" in stats:
                for row in stats["data"]:
                    if row.get("svname") == "BACKEND":
                        backend_name = row.get("pxname")
                        if backend_name and self.VALID_NAME_PATTERN.match(backend_name):
                            backends.add(backend_name)
            
            return sorted(list(backends))
        
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des backends: {type(e).__name__}")
            return []
    
    def _parse_stats(self, raw_stats: str) -> Dict[str, Any]:
        """
        Parse les statistiques brutes HAProxy de manière sécurisée.
        
        Args:
            raw_stats: Statistiques brutes
            
        Returns:
            Statistiques parsées
        """
        try:
            lines = raw_stats.strip().split('\n')
            if not lines:
                return {"success": True, "data": []}
            
            # La première ligne contient les en-têtes
            header_line = lines[0]
            if not header_line.startswith('#'):
                return {"success": False, "error": "Format de statistiques invalide"}
                
            headers = header_line.strip('# ').split(',')
            
            data = []
            for line in lines[1:]:
                if line.strip():
                    values = line.split(',')
                    if len(values) == len(headers):
                        data.append(dict(zip(headers, values)))
            
            return {"success": True, "data": data}
        
        except Exception as e:
            logger.error(f"Erreur lors du parsing des stats: {type(e).__name__}")
            return {"success": False, "error": "Erreur de parsing des statistiques"}
    
    def _parse_info(self, raw_info: str) -> Dict[str, Any]:
        """
        Parse les informations brutes HAProxy de manière sécurisée.
        
        Args:
            raw_info: Informations brutes
            
        Returns:
            Informations parsées
        """
        try:
            info = {}
            for line in raw_info.strip().split('\n'):
                if ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        key, value = parts
                        # Nettoyer et valider la clé
                        clean_key = re.sub(r'[^a-zA-Z0-9_]', '_', key.strip())
                        info[clean_key] = value.strip()
            
            return {"success": True, "info": info}
        
        except Exception as e:
            logger.error(f"Erreur lors du parsing des infos: {type(e).__name__}")
            return {"success": False, "error": "Erreur de parsing des informations"} 