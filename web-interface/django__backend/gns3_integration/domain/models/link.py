"""
Modèle de domaine Link pour l'intégration GNS3.

Ce module définit l'entité Link du domaine GNS3.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any

from .node import Node


@dataclass
class Link:
    """
    Entité Link du domaine GNS3.
    
    Cette classe représente un lien GNS3 dans le domaine métier,
    indépendamment de la couche persistance.
    """
    id: str
    project_id: str
    source_node: Optional[Node] = None
    source_port: int = 0
    destination_node: Optional[Node] = None
    destination_port: int = 0
    link_type: str = "ethernet"
    status: str = "started"
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Identifiants pour la récupération des nœuds (utilisés si les nœuds ne sont pas fournis)
    source_node_id: str = ""
    destination_node_id: str = ""
    
    @property
    def is_started(self) -> bool:
        """Vérifie si le lien est actif."""
        return self.status == "started"
    
    @property
    def is_stopped(self) -> bool:
        """Vérifie si le lien est désactivé."""
        return self.status == "stopped"
    
    @property
    def is_suspended(self) -> bool:
        """Vérifie si le lien est suspendu."""
        return self.status == "suspended"
    
    @property
    def short_id(self) -> str:
        """Retourne l'identifiant court du lien."""
        if len(self.id) > 8:
            return self.id[:8]
        return self.id
    
    @property
    def display_name(self) -> str:
        """Retourne une représentation textuelle du lien."""
        source_name = self.source_node.name if self.source_node else self.source_node_id
        dest_name = self.destination_node.name if self.destination_node else self.destination_node_id
        
        return f"{source_name}:{self.source_port} → {dest_name}:{self.destination_port}"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit l'entité en dictionnaire.
        
        Returns:
            Dictionnaire représentant l'entité
        """
        result = {
            "id": self.id,
            "project_id": self.project_id,
            "source_port": self.source_port,
            "destination_port": self.destination_port,
            "link_type": self.link_type,
            "status": self.status,
            "properties": self.properties,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        
        # Gestion des nœuds source et destination
        if self.source_node:
            result["source_node"] = self.source_node.to_dict()
            result["source_node_id"] = self.source_node.id
        else:
            result["source_node_id"] = self.source_node_id
        
        if self.destination_node:
            result["destination_node"] = self.destination_node.to_dict()
            result["destination_node_id"] = self.destination_node.id
        else:
            result["destination_node_id"] = self.destination_node_id
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Link':
        """
        Crée une entité à partir d'un dictionnaire.
        
        Args:
            data: Dictionnaire contenant les données
            
        Returns:
            Instance de Link
        """
        # Extraction des nœuds source et destination s'ils sont présents
        source_node = None
        if "source_node" in data and isinstance(data["source_node"], dict):
            source_node = Node.from_dict(data["source_node"])
        
        destination_node = None
        if "destination_node" in data and isinstance(data["destination_node"], dict):
            destination_node = Node.from_dict(data["destination_node"])
        
        # Création du lien
        link = cls(
            id=data.get("id", ""),
            project_id=data.get("project_id", ""),
            source_node=source_node,
            source_port=data.get("source_port", 0),
            destination_node=destination_node,
            destination_port=data.get("destination_port", 0),
            link_type=data.get("link_type", "ethernet"),
            status=data.get("status", "started"),
            properties=data.get("properties", {}),
            source_node_id=data.get("source_node_id", ""),
            destination_node_id=data.get("destination_node_id", "")
        )
        
        # Conversion des dates si présentes
        created_at = data.get("created_at")
        if created_at:
            if isinstance(created_at, str):
                link.created_at = datetime.fromisoformat(created_at)
            else:
                link.created_at = created_at
        
        updated_at = data.get("updated_at")
        if updated_at:
            if isinstance(updated_at, str):
                link.updated_at = datetime.fromisoformat(updated_at)
            else:
                link.updated_at = updated_at
        
        return link 