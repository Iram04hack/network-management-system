"""
Validateurs d'entrées pour sécuriser les clients API.

Ce module fournit une validation rigoureuse des paramètres d'entrée
pour prévenir les vulnérabilités de sécurité et améliorer la robustesse.
"""

import re
import ipaddress
import urllib.parse
from typing import Any, Optional, Union, List, Dict, Pattern
from abc import ABC, abstractmethod
from datetime import datetime
import logging

from ..domain.exceptions import ValidationException

logger = logging.getLogger(__name__)

class BaseValidator(ABC):
    """Interface de base pour tous les validateurs."""
    
    @abstractmethod
    def validate(self, value: Any, field_name: str = None) -> Any:
        """
        Valide une valeur d'entrée.
        
        Args:
            value: Valeur à valider
            field_name: Nom du champ (pour les messages d'erreur)
            
        Returns:
            Valeur validée et potentiellement normalisée
            
        Raises:
            ValidationException: Si la validation échoue
        """
        pass

class StringValidator(BaseValidator):
    """Validateur pour les chaînes de caractères."""
    
    def __init__(
        self,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[Union[str, Pattern]] = None,
        allowed_chars: Optional[str] = None,
        forbidden_chars: Optional[str] = None,
        strip_whitespace: bool = True,
        case_sensitive: bool = True
    ):
        """
        Initialise le validateur de chaînes.
        
        Args:
            min_length: Longueur minimale
            max_length: Longueur maximale
            pattern: Pattern regex à respecter
            allowed_chars: Caractères autorisés uniquement
            forbidden_chars: Caractères interdits
            strip_whitespace: Supprimer les espaces en début/fin
            case_sensitive: Validation sensible à la casse
        """
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = re.compile(pattern) if isinstance(pattern, str) else pattern
        self.allowed_chars = set(allowed_chars) if allowed_chars else None
        self.forbidden_chars = set(forbidden_chars) if forbidden_chars else None
        self.strip_whitespace = strip_whitespace
        self.case_sensitive = case_sensitive
    
    def validate(self, value: Any, field_name: str = None) -> str:
        """Valide et normalise une chaîne de caractères."""
        if not isinstance(value, str):
            raise ValidationException(
                f"Doit être une chaîne de caractères, reçu {type(value).__name__}",
                field_name, str(value)
            )
        
        # Normalisation
        if self.strip_whitespace:
            value = value.strip()
        
        if not self.case_sensitive:
            value = value.lower()
        
        # Validation de longueur
        if self.min_length is not None and len(value) < self.min_length:
            raise ValidationException(
                f"Longueur minimale requise: {self.min_length}, reçu: {len(value)}",
                field_name, value
            )
        
        if self.max_length is not None and len(value) > self.max_length:
            raise ValidationException(
                f"Longueur maximale autorisée: {self.max_length}, reçu: {len(value)}",
                field_name, value
            )
        
        # Validation de pattern
        if self.pattern and not self.pattern.match(value):
            raise ValidationException(
                f"Ne respecte pas le format requis: {self.pattern.pattern}",
                field_name, value
            )
        
        # Validation des caractères autorisés
        if self.allowed_chars:
            invalid_chars = set(value) - self.allowed_chars
            if invalid_chars:
                raise ValidationException(
                    f"Caractères non autorisés: {', '.join(invalid_chars)}",
                    field_name, value
                )
        
        # Validation des caractères interdits
        if self.forbidden_chars:
            found_forbidden = set(value) & self.forbidden_chars
            if found_forbidden:
                raise ValidationException(
                    f"Caractères interdits trouvés: {', '.join(found_forbidden)}",
                    field_name, value
                )
        
        return value

class URLValidator(BaseValidator):
    """Validateur pour les URLs."""
    
    def __init__(
        self,
        allowed_schemes: Optional[List[str]] = None,
        allowed_hosts: Optional[List[str]] = None,
        forbidden_hosts: Optional[List[str]] = None,
        require_tld: bool = True,
        allow_private_ips: bool = False
    ):
        """
        Initialise le validateur d'URLs.
        
        Args:
            allowed_schemes: Schémas autorisés (http, https, etc.)
            allowed_hosts: Hosts autorisés uniquement
            forbidden_hosts: Hosts interdits
            require_tld: Exiger un TLD valide
            allow_private_ips: Autoriser les IPs privées
        """
        self.allowed_schemes = allowed_schemes or ['http', 'https']
        self.allowed_hosts = set(allowed_hosts) if allowed_hosts else None
        self.forbidden_hosts = set(forbidden_hosts) if forbidden_hosts else None
        self.require_tld = require_tld
        self.allow_private_ips = allow_private_ips
    
    def validate(self, value: Any, field_name: str = None) -> str:
        """Valide une URL."""
        if not isinstance(value, str):
            raise ValidationException(
                f"URL doit être une chaîne, reçu {type(value).__name__}",
                field_name, str(value)
            )
        
        try:
            parsed = urllib.parse.urlparse(value)
        except Exception as e:
            raise ValidationException(
                f"Format d'URL invalide: {e}",
                field_name, value
            )
        
        # Validation du schéma
        if parsed.scheme not in self.allowed_schemes:
            raise ValidationException(
                f"Schéma non autorisé '{parsed.scheme}'. Autorisés: {self.allowed_schemes}",
                field_name, value
            )
        
        # Validation de l'host
        if not parsed.netloc:
            raise ValidationException(
                "Host manquant dans l'URL",
                field_name, value
            )
        
        host = parsed.hostname or parsed.netloc
        
        # Vérifier les hosts autorisés/interdits
        if self.allowed_hosts and host not in self.allowed_hosts:
            raise ValidationException(
                f"Host non autorisé '{host}'. Autorisés: {list(self.allowed_hosts)}",
                field_name, value
            )
        
        if self.forbidden_hosts and host in self.forbidden_hosts:
            raise ValidationException(
                f"Host interdit '{host}'",
                field_name, value
            )
        
        # Vérification des IPs privées
        if not self.allow_private_ips:
            try:
                ip = ipaddress.ip_address(host)
                if ip.is_private:
                    raise ValidationException(
                        f"Adresse IP privée non autorisée: {host}",
                        field_name, value
                    )
            except ValueError:
                # Pas une IP, continuer avec la validation de domaine
                pass
        
        # Validation TLD
        if self.require_tld and '.' not in host:
            raise ValidationException(
                "TLD manquant dans le nom de domaine",
                field_name, value
            )
        
        return value

class QueryValidator(BaseValidator):
    """Validateur pour les requêtes (PromQL, SQL, etc.)."""
    
    def __init__(
        self,
        max_length: int = 5000,
        forbidden_keywords: Optional[List[str]] = None,
        allowed_functions: Optional[List[str]] = None,
        require_non_empty: bool = True
    ):
        """
        Initialise le validateur de requêtes.
        
        Args:
            max_length: Longueur maximale de la requête
            forbidden_keywords: Mots-clés interdits
            allowed_functions: Fonctions autorisées uniquement
            require_non_empty: Exiger une requête non vide
        """
        self.max_length = max_length
        self.forbidden_keywords = [kw.lower() for kw in (forbidden_keywords or [])]
        self.allowed_functions = [func.lower() for func in (allowed_functions or [])]
        self.require_non_empty = require_non_empty
        
        # Mots-clés dangereux par défaut pour SQL
        self.default_forbidden_sql = [
            'drop', 'delete', 'truncate', 'alter', 'create',
            'exec', 'execute', 'xp_', 'sp_', 'into', 'insert',
            'update', 'merge', 'bulk'
        ]
    
    def validate(self, value: Any, field_name: str = None) -> str:
        """Valide une requête."""
        if not isinstance(value, str):
            raise ValidationException(
                f"Requête doit être une chaîne, reçu {type(value).__name__}",
                field_name, str(value)
            )
        
        value = value.strip()
        
        if self.require_non_empty and not value:
            raise ValidationException(
                "Requête ne peut pas être vide",
                field_name, value
            )
        
        if len(value) > self.max_length:
            raise ValidationException(
                f"Requête trop longue: {len(value)} caractères (max: {self.max_length})",
                field_name, value
            )
        
        # Vérifier les mots-clés interdits
        value_lower = value.lower()
        all_forbidden = self.forbidden_keywords + self.default_forbidden_sql
        
        for keyword in all_forbidden:
            if keyword in value_lower:
                raise ValidationException(
                    f"Mot-clé interdit détecté: '{keyword}'",
                    field_name, value
                )
        
        return value

class IPAddressValidator(BaseValidator):
    """Validateur pour les adresses IP."""
    
    def __init__(
        self,
        allow_ipv4: bool = True,
        allow_ipv6: bool = True,
        allow_private: bool = True,
        allow_loopback: bool = True,
        allow_multicast: bool = False
    ):
        """
        Initialise le validateur d'adresses IP.
        
        Args:
            allow_ipv4: Autoriser IPv4
            allow_ipv6: Autoriser IPv6
            allow_private: Autoriser les adresses privées
            allow_loopback: Autoriser les adresses de loopback
            allow_multicast: Autoriser les adresses multicast
        """
        self.allow_ipv4 = allow_ipv4
        self.allow_ipv6 = allow_ipv6
        self.allow_private = allow_private
        self.allow_loopback = allow_loopback
        self.allow_multicast = allow_multicast
    
    def validate(self, value: Any, field_name: str = None) -> str:
        """Valide une adresse IP."""
        if not isinstance(value, str):
            raise ValidationException(
                f"Adresse IP doit être une chaîne, reçu {type(value).__name__}",
                field_name, str(value)
            )
        
        try:
            ip = ipaddress.ip_address(value.strip())
        except ValueError as e:
            raise ValidationException(
                f"Format d'adresse IP invalide: {e}",
                field_name, value
            )
        
        # Validation du type d'IP
        if isinstance(ip, ipaddress.IPv4Address) and not self.allow_ipv4:
            raise ValidationException(
                "Adresses IPv4 non autorisées",
                field_name, value
            )
        
        if isinstance(ip, ipaddress.IPv6Address) and not self.allow_ipv6:
            raise ValidationException(
                "Adresses IPv6 non autorisées",
                field_name, value
            )
        
        # Validation des types spéciaux
        if ip.is_private and not self.allow_private:
            raise ValidationException(
                "Adresses IP privées non autorisées",
                field_name, value
            )
        
        if ip.is_loopback and not self.allow_loopback:
            raise ValidationException(
                "Adresses de loopback non autorisées",
                field_name, value
            )
        
        if ip.is_multicast and not self.allow_multicast:
            raise ValidationException(
                "Adresses multicast non autorisées",
                field_name, value
            )
        
        return str(ip)

class TimestampValidator(BaseValidator):
    """Validateur pour les timestamps et formats temporels."""
    
    def __init__(
        self,
        formats: Optional[List[str]] = None,
        allow_unix_timestamp: bool = True,
        min_timestamp: Optional[Union[int, float, datetime]] = None,
        max_timestamp: Optional[Union[int, float, datetime]] = None
    ):
        """
        Initialise le validateur de timestamps.
        
        Args:
            formats: Formats de date autorisés (strftime)
            allow_unix_timestamp: Autoriser les timestamps Unix
            min_timestamp: Timestamp minimum autorisé
            max_timestamp: Timestamp maximum autorisé
        """
        self.formats = formats or [
            '%Y-%m-%d',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%d %H:%M:%S'
        ]
        self.allow_unix_timestamp = allow_unix_timestamp
        self.min_timestamp = min_timestamp
        self.max_timestamp = max_timestamp
    
    def validate(self, value: Any, field_name: str = None) -> Union[str, int, float]:
        """Valide un timestamp."""
        if isinstance(value, (int, float)) and self.allow_unix_timestamp:
            # Validation des timestamps Unix
            try:
                dt = datetime.fromtimestamp(value)
                return self._validate_datetime_range(dt, value, field_name)
            except (ValueError, OSError) as e:
                raise ValidationException(
                    f"Timestamp Unix invalide: {e}",
                    field_name, str(value)
                )
        
        elif isinstance(value, str):
            # Essayer de parser selon les formats autorisés
            for fmt in self.formats:
                try:
                    dt = datetime.strptime(value, fmt)
                    return self._validate_datetime_range(dt, value, field_name)
                except ValueError:
                    continue
            
            raise ValidationException(
                f"Format de date non reconnu. Formats acceptés: {self.formats}",
                field_name, value
            )
        
        else:
            raise ValidationException(
                f"Timestamp doit être un nombre ou une chaîne, reçu {type(value).__name__}",
                field_name, str(value)
            )
    
    def _validate_datetime_range(self, dt: datetime, original_value: Any, field_name: str) -> Any:
        """Valide que la datetime est dans la plage autorisée."""
        if self.min_timestamp:
            min_dt = (datetime.fromtimestamp(self.min_timestamp) 
                     if isinstance(self.min_timestamp, (int, float))
                     else self.min_timestamp)
            if dt < min_dt:
                raise ValidationException(
                    f"Timestamp antérieur au minimum autorisé: {min_dt}",
                    field_name, str(original_value)
                )
        
        if self.max_timestamp:
            max_dt = (datetime.fromtimestamp(self.max_timestamp)
                     if isinstance(self.max_timestamp, (int, float))
                     else self.max_timestamp)
            if dt > max_dt:
                raise ValidationException(
                    f"Timestamp postérieur au maximum autorisé: {max_dt}",
                    field_name, str(original_value)
                )
        
        return original_value

class PortValidator(BaseValidator):
    """Validateur pour les numéros de port."""
    
    def __init__(
        self,
        allow_well_known: bool = True,    # 1-1023
        allow_registered: bool = True,    # 1024-49151
        allow_dynamic: bool = False       # 49152-65535
    ):
        """
        Initialise le validateur de ports.
        
        Args:
            allow_well_known: Autoriser les ports bien connus (1-1023)
            allow_registered: Autoriser les ports enregistrés (1024-49151)
            allow_dynamic: Autoriser les ports dynamiques (49152-65535)
        """
        self.allow_well_known = allow_well_known
        self.allow_registered = allow_registered
        self.allow_dynamic = allow_dynamic
    
    def validate(self, value: Any, field_name: str = None) -> int:
        """Valide un numéro de port."""
        if isinstance(value, str):
            try:
                value = int(value)
            except ValueError:
                raise ValidationException(
                    f"Port doit être un nombre entier, reçu '{value}'",
                    field_name, str(value)
                )
        
        if not isinstance(value, int):
            raise ValidationException(
                f"Port doit être un nombre entier, reçu {type(value).__name__}",
                field_name, str(value)
            )
        
        if value < 1 or value > 65535:
            raise ValidationException(
                f"Port doit être entre 1 et 65535, reçu {value}",
                field_name, str(value)
            )
        
        # Validation des plages autorisées
        if 1 <= value <= 1023 and not self.allow_well_known:
            raise ValidationException(
                "Ports bien connus (1-1023) non autorisés",
                field_name, str(value)
            )
        
        if 1024 <= value <= 49151 and not self.allow_registered:
            raise ValidationException(
                "Ports enregistrés (1024-49151) non autorisés",
                field_name, str(value)
            )
        
        if 49152 <= value <= 65535 and not self.allow_dynamic:
            raise ValidationException(
                "Ports dynamiques (49152-65535) non autorisés",
                field_name, str(value)
            )
        
        return value

class CompositeValidator:
    """Validateur composite pour valider plusieurs champs."""
    
    def __init__(self, validators: Dict[str, BaseValidator]):
        """
        Initialise le validateur composite.
        
        Args:
            validators: Dictionnaire {nom_champ: validateur}
        """
        self.validators = validators
    
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valide un dictionnaire de données.
        
        Args:
            data: Données à valider
            
        Returns:
            Données validées et normalisées
            
        Raises:
            ValidationException: Si une validation échoue
        """
        if not isinstance(data, dict):
            raise ValidationException(
                f"Données doivent être un dictionnaire, reçu {type(data).__name__}"
            )
        
        validated = {}
        
        for field_name, validator in self.validators.items():
            if field_name in data:
                try:
                    validated[field_name] = validator.validate(
                        data[field_name], field_name
                    )
                except ValidationException as e:
                    # Re-lancer avec le contexte du champ
                    raise ValidationException(
                        f"Validation échouée pour le champ '{field_name}': {e.message}",
                        field_name, 
                        str(data[field_name])
                    ) from e
        
        return validated

# Validateurs pré-configurés pour les cas d'usage courants
PROMETHEUS_QUERY_VALIDATOR = QueryValidator(
    max_length=2000,
    forbidden_keywords=['drop', 'delete', 'create', 'alter'],
    require_non_empty=True
)

API_URL_VALIDATOR = URLValidator(
    allowed_schemes=['http', 'https'],
    allow_private_ips=True,
    require_tld=False
)

SECURE_URL_VALIDATOR = URLValidator(
    allowed_schemes=['https'],
    allow_private_ips=False,
    require_tld=True
)

IP_ADDRESS_VALIDATOR = IPAddressValidator(
    allow_private=True,
    allow_loopback=True,
    allow_multicast=False
)

UNIX_TIMESTAMP_VALIDATOR = TimestampValidator(
    allow_unix_timestamp=True
)

SERVICE_PORT_VALIDATOR = PortValidator(
    allow_well_known=False,
    allow_registered=True,
    allow_dynamic=False
) 