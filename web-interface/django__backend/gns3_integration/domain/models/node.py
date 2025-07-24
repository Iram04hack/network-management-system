"""
Modèle de domaine Node pour l'intégration GNS3.

Ce module définit l'entité Node du domaine GNS3.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class Node:
    """
    Entité Node du domaine GNS3.
    
    Cette classe représente un nœud GNS3 dans le domaine métier,
    indépendamment de la couche persistance.
    """
    id: str
    name: str
    project_id: str
    node_type: str
    status: str = "stopped"
    console_type: str = ""
    console_port: Optional[int] = None
    x: int = 0
    y: int = 0
    symbol: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)
    compute_id: str = "local"
    template_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    @property
    def is_started(self) -> bool:
        """Vérifie si le nœud est démarré."""
        return self.status == "started"
    
    @property
    def is_stopped(self) -> bool:
        """Vérifie si le nœud est arrêté."""
        return self.status == "stopped"
    
    @property
    def is_suspended(self) -> bool:
        """Vérifie si le nœud est suspendu."""
        return self.status == "suspended"
    
    @property
    def short_id(self) -> str:
        """Retourne l'identifiant court du nœud."""
        if len(self.id) > 8:
            return self.id[:8]
        return self.id
    
    @property
    def has_console(self) -> bool:
        """Vérifie si le nœud a une console accessible."""
        return self.console_port is not None and self.console_port > 0
    
    @property
    def is_router(self) -> bool:
        """Vérifie si le nœud est un routeur."""
        return self.node_type in ["dynamips", "iou"] or \
               "router" in self.name.lower()
    
    @property
    def is_switch(self) -> bool:
        """Vérifie si le nœud est un switch."""
        return self.node_type in ["ethernet_switch", "ethernet_hub"] or \
               "switch" in self.name.lower()
    
    @property
    def display_name(self) -> str:
        """Retourne le nom formaté pour l'affichage."""
        if not self.name:
            return f"{self.node_type} ({self.short_id})"
        return self.name
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit l'entité en dictionnaire.
        
        Returns:
            Dictionnaire représentant l'entité
        """
        return {
            "id": self.id,
            "name": self.name,
            "project_id": self.project_id,
            "node_type": self.node_type,
            "status": self.status,
            "console_type": self.console_type,
            "console_port": self.console_port,
            "x": self.x,
            "y": self.y,
            "symbol": self.symbol,
            "properties": self.properties,
            "compute_id": self.compute_id,
            "template_id": self.template_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Node':
        """
        Crée une entité à partir d'un dictionnaire.
        
        Args:
            data: Dictionnaire contenant les données
            
        Returns:
            Instance de Node
        """
        node = cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            project_id=data.get("project_id", ""),
            node_type=data.get("node_type", ""),
            status=data.get("status", "stopped"),
            console_type=data.get("console_type", ""),
            console_port=data.get("console_port"),
            x=data.get("x", 0),
            y=data.get("y", 0),
            symbol=data.get("symbol", ""),
            properties=data.get("properties", {}),
            compute_id=data.get("compute_id", "local"),
            template_id=data.get("template_id")
        )
        
        # Conversion des dates si présentes
        created_at = data.get("created_at")
        if created_at:
            if isinstance(created_at, str):
                node.created_at = datetime.fromisoformat(created_at)
            else:
                node.created_at = created_at
        
        updated_at = data.get("updated_at")
        if updated_at:
            if isinstance(updated_at, str):
                node.updated_at = datetime.fromisoformat(updated_at)
            else:
                node.updated_at = updated_at
        
        return node 