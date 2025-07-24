"""
Modèle de domaine Server pour l'intégration GNS3.

Ce module définit l'entité Server du domaine GNS3.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List


@dataclass
class Server:
    """
    Entité Server du domaine GNS3.
    
    Cette classe représente un serveur GNS3 dans le domaine métier,
    indépendamment de la couche persistance.
    """
    id: Optional[int] = None
    name: str = ""
    host: str = "localhost"
    port: int = 3080
    protocol: str = "http"
    username: str = ""
    password: str = ""
    verify_ssl: bool = True
    is_active: bool = True
    timeout: int = 30
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Statistiques calculées à la volée (non persistées directement)
    projects_count: int = 0
    version: str = ""
    
    @property
    def base_url(self) -> str:
        """Retourne l'URL de base du serveur GNS3."""
        return f"{self.protocol}://{self.host}:{self.port}"
    
    @property
    def api_url(self) -> str:
        """Retourne l'URL de l'API du serveur GNS3."""
        return f"{self.base_url}/v2"
    
    @property
    def display_name(self) -> str:
        """Retourne une représentation textuelle du serveur."""
        return f"{self.name} ({self.host}:{self.port})"
    
    @property
    def has_auth(self) -> bool:
        """Vérifie si le serveur nécessite une authentification."""
        return bool(self.username) and bool(self.password)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit l'entité en dictionnaire.
        
        Returns:
            Dictionnaire représentant l'entité
        """
        return {
            "id": self.id,
            "name": self.name,
            "host": self.host,
            "port": self.port,
            "protocol": self.protocol,
            "username": self.username,
            # Ne pas inclure le mot de passe pour des raisons de sécurité
            "verify_ssl": self.verify_ssl,
            "is_active": self.is_active,
            "timeout": self.timeout,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "projects_count": self.projects_count,
            "version": self.version,
            "base_url": self.base_url
        }
    
    def to_auth_dict(self) -> Dict[str, Any]:
        """
        Convertit l'entité en dictionnaire avec les informations d'authentification.
        
        Returns:
            Dictionnaire représentant l'entité avec les informations d'authentification
        """
        result = self.to_dict()
        if self.has_auth:
            result["has_auth"] = True
            # Indiquer que le mot de passe est défini sans le révéler
            result["password_set"] = True
        else:
            result["has_auth"] = False
            result["password_set"] = False
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Server':
        """
        Crée une entité à partir d'un dictionnaire.
        
        Args:
            data: Dictionnaire contenant les données
            
        Returns:
            Instance de Server
        """
        server = cls(
            id=data.get("id"),
            name=data.get("name", ""),
            host=data.get("host", "localhost"),
            port=data.get("port", 3080),
            protocol=data.get("protocol", "http"),
            username=data.get("username", ""),
            password=data.get("password", ""),
            verify_ssl=data.get("verify_ssl", True),
            is_active=data.get("is_active", True),
            timeout=data.get("timeout", 30),
            projects_count=data.get("projects_count", 0),
            version=data.get("version", "")
        )
        
        # Conversion des dates si présentes
        created_at = data.get("created_at")
        if created_at:
            if isinstance(created_at, str):
                server.created_at = datetime.fromisoformat(created_at)
            else:
                server.created_at = created_at
        
        updated_at = data.get("updated_at")
        if updated_at:
            if isinstance(updated_at, str):
                server.updated_at = datetime.fromisoformat(updated_at)
            else:
                server.updated_at = updated_at
        
        return server 