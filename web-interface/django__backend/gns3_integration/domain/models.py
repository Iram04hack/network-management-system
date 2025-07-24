"""Modèles de domaine pour l'intégration GNS3."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class GNS3Server:
    """Représentation d'un serveur GNS3."""
    name: str
    host: str
    port: int
    protocol: str = "http"
    id: Optional[int] = None
    password: Optional[str] = None
    api_key: Optional[str] = None
    status: str = "unknown"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    @property
    def url(self) -> str:
        """Retourne l'URL complète du serveur."""
        return f"{self.protocol}://{self.host}:{self.port}"


@dataclass
class Node:
    """Représentation d'un nœud dans un projet GNS3."""
    name: str
    node_type: str
    id: Optional[str] = None
    status: str = "stopped"
    console_port: Optional[int] = None
    x: int = 0
    y: int = 0
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Link:
    """Représentation d'un lien entre deux nœuds dans un projet GNS3."""
    source_node_id: str
    source_port_number: int
    target_node_id: str
    target_port_number: int
    id: Optional[str] = None
    link_type: str = "ethernet"
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GNS3Project:
    """Représentation d'un projet GNS3."""
    name: str
    server_id: int
    id: Optional[str] = None
    description: str = ""
    status: str = "closed"
    nodes: List[Node] = field(default_factory=list)
    links: List[Link] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
