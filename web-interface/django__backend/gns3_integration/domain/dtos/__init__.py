"""
Data Transfer Objects (DTOs) pour l'intégration GNS3.
Permet la conversion type-safe entre le domaine et les couches externe.
"""

from .server_dto import GNS3ServerDTO
from .project_dto import GNS3ProjectDTO
from .node_dto import GNS3NodeDTO
from .link_dto import GNS3LinkDTO
from .automation_dto import (
    GNS3ScriptDTO, GNS3ScriptExecutionDTO,
    GNS3SnapshotDTO, GNS3WorkflowDTO, GNS3WorkflowExecutionDTO
)

__all__ = [
    'GNS3ServerDTO',
    'GNS3ProjectDTO',
    'GNS3NodeDTO',
    'GNS3LinkDTO',
    'GNS3ScriptDTO',
    'GNS3ScriptExecutionDTO',
    'GNS3SnapshotDTO',
    'GNS3WorkflowDTO',
    'GNS3WorkflowExecutionDTO'
] 