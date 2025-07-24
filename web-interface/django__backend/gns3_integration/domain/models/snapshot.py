"""
Modèle de domaine Snapshot pour l'intégration GNS3.

Ce module définit l'entité Snapshot du domaine GNS3.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class Snapshot:
    """
    Entité Snapshot du domaine GNS3.
    
    Cette classe représente un snapshot de projet GNS3 dans le domaine métier,
    indépendamment de la couche persistance.
    """
    id: str
    name: str
    project_id: str
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    created_by_id: Optional[int] = None
    
    @property
    def short_id(self) -> str:
        """Retourne l'identifiant court du snapshot."""
        if len(self.id) > 8:
            return self.id[:8]
        return self.id
    
    @property
    def display_name(self) -> str:
        """Retourne une représentation textuelle du snapshot."""
        return f"{self.name} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
    
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
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by_id": self.created_by_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Snapshot':
        """
        Crée une entité à partir d'un dictionnaire.
        
        Args:
            data: Dictionnaire contenant les données
            
        Returns:
            Instance de Snapshot
        """
        snapshot = cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            project_id=data.get("project_id", ""),
            description=data.get("description", ""),
            created_by_id=data.get("created_by_id")
        )
        
        # Conversion de la date si présente
        created_at = data.get("created_at")
        if created_at:
            if isinstance(created_at, str):
                snapshot.created_at = datetime.fromisoformat(created_at)
            else:
                snapshot.created_at = created_at
        
        return snapshot 