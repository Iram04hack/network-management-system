"""
Modèle de domaine Template pour l'intégration GNS3.

Ce module définit l'entité Template du domaine GNS3.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class Template:
    """
    Entité Template du domaine GNS3.
    
    Cette classe représente un template d'appareil GNS3 dans le domaine métier,
    indépendamment de la couche persistance.
    """
    id: str
    name: str
    template_type: str
    server_id: int
    builtin: bool = False
    symbol: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)
    compute_id: str = "local"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    @property
    def short_id(self) -> str:
        """Retourne l'identifiant court du template."""
        if len(self.id) > 8:
            return self.id[:8]
        return self.id
    
    @property
    def display_name(self) -> str:
        """Retourne une représentation textuelle du template."""
        return f"{self.name} ({self.template_type})"
    
    @property
    def is_router(self) -> bool:
        """Vérifie si le template est un routeur."""
        return self.template_type in ["dynamips", "iou"] or \
               "router" in self.name.lower()
    
    @property
    def is_switch(self) -> bool:
        """Vérifie si le template est un switch."""
        return self.template_type in ["ethernet_switch", "ethernet_hub"] or \
               "switch" in self.name.lower()
    
    @property
    def is_end_device(self) -> bool:
        """Vérifie si le template est un appareil terminal."""
        return self.template_type in ["vpcs", "qemu"] or \
               "pc" in self.name.lower() or \
               "station" in self.name.lower() or \
               "host" in self.name.lower()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit l'entité en dictionnaire.
        
        Returns:
            Dictionnaire représentant l'entité
        """
        return {
            "id": self.id,
            "name": self.name,
            "template_type": self.template_type,
            "server_id": self.server_id,
            "builtin": self.builtin,
            "symbol": self.symbol,
            "properties": self.properties,
            "compute_id": self.compute_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Template':
        """
        Crée une entité à partir d'un dictionnaire.
        
        Args:
            data: Dictionnaire contenant les données
            
        Returns:
            Instance de Template
        """
        template = cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            template_type=data.get("template_type", ""),
            server_id=data.get("server_id", 0),
            builtin=data.get("builtin", False),
            symbol=data.get("symbol", ""),
            properties=data.get("properties", {}),
            compute_id=data.get("compute_id", "local")
        )
        
        # Conversion des dates si présentes
        created_at = data.get("created_at")
        if created_at:
            if isinstance(created_at, str):
                template.created_at = datetime.fromisoformat(created_at)
            else:
                template.created_at = created_at
        
        updated_at = data.get("updated_at")
        if updated_at:
            if isinstance(updated_at, str):
                template.updated_at = datetime.fromisoformat(updated_at)
            else:
                template.updated_at = updated_at
        
        return template 