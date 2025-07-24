"""
Modèle de domaine Project pour l'intégration GNS3.

Ce module définit l'entité Project du domaine GNS3.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass
class Project:
    """
    Entité Project du domaine GNS3.
    
    Cette classe représente un projet GNS3 dans le domaine métier,
    indépendamment de la couche persistance.
    """
    id: str
    name: str
    status: str = "closed"
    path: str = ""
    filename: str = ""
    auto_start: bool = False
    auto_close: bool = True
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    server_id: Optional[int] = None
    created_by_id: Optional[int] = None
    
    # Statistiques calculées à la volée (non persistées directement)
    nodes_count: int = 0
    links_count: int = 0
    
    @property
    def is_open(self) -> bool:
        """Vérifie si le projet est ouvert."""
        return self.status == "open"
    
    @property
    def is_closed(self) -> bool:
        """Vérifie si le projet est fermé."""
        return self.status == "closed"
    
    @property
    def short_id(self) -> str:
        """Retourne l'identifiant court du projet."""
        if len(self.id) > 8:
            return self.id[:8]
        return self.id
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit l'entité en dictionnaire.
        
        Returns:
            Dictionnaire représentant l'entité
        """
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "path": self.path,
            "filename": self.filename,
            "auto_start": self.auto_start,
            "auto_close": self.auto_close,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "server_id": self.server_id,
            "created_by_id": self.created_by_id,
            "nodes_count": self.nodes_count,
            "links_count": self.links_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """
        Crée une entité à partir d'un dictionnaire.
        
        Args:
            data: Dictionnaire contenant les données
            
        Returns:
            Instance de Project
        """
        project = cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            status=data.get("status", "closed"),
            path=data.get("path", ""),
            filename=data.get("filename", ""),
            auto_start=data.get("auto_start", False),
            auto_close=data.get("auto_close", True),
            description=data.get("description", ""),
            server_id=data.get("server_id"),
            created_by_id=data.get("created_by_id")
        )
        
        # Conversion des dates si présentes
        created_at = data.get("created_at")
        if created_at:
            if isinstance(created_at, str):
                project.created_at = datetime.fromisoformat(created_at)
            else:
                project.created_at = created_at
        
        updated_at = data.get("updated_at")
        if updated_at:
            if isinstance(updated_at, str):
                project.updated_at = datetime.fromisoformat(updated_at)
            else:
                project.updated_at = updated_at
        
        # Statistiques
        project.nodes_count = data.get("nodes_count", 0)
        project.links_count = data.get("links_count", 0)
        
        return project 