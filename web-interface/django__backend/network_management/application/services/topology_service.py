"""
Module contenant le service de topologie réseau.
"""

from typing import List, Dict, Any, Optional
# import networkx as nx  # TODO: Installer networkx

from ...domain.interfaces import (
    NetworkDeviceRepository,
    NetworkInterfaceRepository,
    NetworkConnectionRepository,
    NetworkTopologyRepository
)
from ...domain.entities import NetworkDeviceEntity, NetworkInterfaceEntity, ConnectionEntity, TopologyEntity
from ..ports.input_ports import NetworkTopologyUseCases
from ...domain.exceptions import ResourceNotFoundException, ValidationException


class TopologyService(NetworkTopologyUseCases):
    """
    Service pour la gestion de la topologie réseau.

    Cette classe implémente l'interface NetworkTopologyUseCases
    et fournit les fonctionnalités de gestion de la topologie réseau.
    """
    
    def __init__(
        self,
        device_repository: NetworkDeviceRepository,
        interface_repository: NetworkInterfaceRepository,
        connection_repository: NetworkConnectionRepository,
        topology_repository: NetworkTopologyRepository
    ):
        """
        Initialise une nouvelle instance de TopologyService.

        Args:
            device_repository (NetworkDeviceRepository): Le repository d'équipements à utiliser.
            interface_repository (NetworkInterfaceRepository): Le repository d'interfaces à utiliser.
            connection_repository (NetworkConnectionRepository): Le repository de connexions à utiliser.
            topology_repository (NetworkTopologyRepository): Le repository de topologies à utiliser.
        """
        self._device_repository = device_repository
        self._interface_repository = interface_repository
        self._connection_repository = connection_repository
        self._topology_repository = topology_repository
    
    def get_topology(self, topology_id: int) -> TopologyEntity:
        """
        Récupère une topologie par son ID.

        Args:
            topology_id (int): L'ID de la topologie à récupérer.

        Returns:
            TopologyEntity: La topologie trouvée.

        Raises:
            ResourceNotFoundException: Si la topologie n'a pas été trouvée.
        """
        topology = self._topology_repository.get_by_id(topology_id)
        if not topology:
            raise ResourceNotFoundException("Topology", str(topology_id))
        return topology
    
    def get_all_topologies(self) -> List[TopologyEntity]:
        """
        Récupère toutes les topologies.

        Returns:
            List[TopologyEntity]: Une liste contenant toutes les topologies.
        """
        return self._topology_repository.get_all()
    
    def create_topology(self, topology_data: Dict[str, Any]) -> TopologyEntity:
        """
        Crée une nouvelle topologie.

        Args:
            topology_data (Dict[str, Any]): Les données de la topologie à créer.

        Returns:
            TopologyEntity: La topologie créée.

        Raises:
            ValidationException: Si les données de la topologie sont invalides.
        """
        # Valider les données
        self._validate_topology_data(topology_data)

        # Créer la topologie
        topology = TopologyEntity(**topology_data)
        return self._topology_repository.create(topology)
    
    def update_topology(self, topology_id: int, topology_data: Dict[str, Any]) -> TopologyEntity:
        """
        Met à jour une topologie existante.

        Args:
            topology_id (int): L'ID de la topologie à mettre à jour.
            topology_data (Dict[str, Any]): Les nouvelles données de la topologie.

        Returns:
            TopologyEntity: La topologie mise à jour.

        Raises:
            ResourceNotFoundException: Si la topologie n'a pas été trouvée.
            ValidationException: Si les données de la topologie sont invalides.
        """
        # Récupérer la topologie existante
        existing_topology = self._topology_repository.get_by_id(topology_id)
        if not existing_topology:
            raise ResourceNotFoundException("Topology", str(topology_id))
        
        # Valider les données
        self._validate_topology_data(topology_data)
        
        # Mettre à jour la topologie
        for key, value in topology_data.items():
            setattr(existing_topology, key, value)
        
        return self._topology_repository.update(existing_topology)
    
    def delete_topology(self, topology_id: int) -> bool:
        """
        Supprime une topologie.
        
        Args:
            topology_id (int): L'ID de la topologie à supprimer.
            
        Returns:
            bool: True si la topologie a été supprimée, False sinon.
            
        Raises:
            ResourceNotFoundException: Si la topologie n'a pas été trouvée.
        """
        # Vérifier que la topologie existe
        if not self._topology_repository.get_by_id(topology_id):
            raise ResourceNotFoundException("Topology", str(topology_id))
        
        # Supprimer la topologie
        return self._topology_repository.delete(topology_id)
    
    def get_connections(self, topology_id: int) -> List[ConnectionEntity]:
        """
        Récupère les connexions d'une topologie.

        Args:
            topology_id (int): L'ID de la topologie dont on veut récupérer les connexions.

        Returns:
            List[ConnectionEntity]: Une liste contenant les connexions de la topologie.

        Raises:
            ResourceNotFoundException: Si la topologie n'a pas été trouvée.
        """
        # Vérifier que la topologie existe
        if not self._topology_repository.get_by_id(topology_id):
            raise ResourceNotFoundException("Topology", str(topology_id))

        # Récupérer les connexions
        return self._connection_repository.get_by_topology_id(topology_id)

    def add_connection(self, topology_id: int, connection_data: Dict[str, Any]) -> ConnectionEntity:
        """
        Ajoute une connexion à une topologie.

        Args:
            topology_id (int): L'ID de la topologie à laquelle ajouter la connexion.
            connection_data (Dict[str, Any]): Les données de la connexion à ajouter.

        Returns:
            ConnectionEntity: La connexion ajoutée.

        Raises:
            ResourceNotFoundException: Si la topologie n'a pas été trouvée.
            ValidationException: Si les données de la connexion sont invalides.
        """
        # Vérifier que la topologie existe
        topology = self._topology_repository.get_by_id(topology_id)
        if not topology:
            raise ResourceNotFoundException("Topology", str(topology_id))

        # Valider les données
        self._validate_connection_data(connection_data)

        # Récupérer les interfaces
        source_interface = self._interface_repository.get_by_id(connection_data['source_interface_id'])
        if not source_interface:
            raise ResourceNotFoundException("Interface", str(connection_data['source_interface_id']))

        target_interface = self._interface_repository.get_by_id(connection_data['target_interface_id'])
        if not target_interface:
            raise ResourceNotFoundException("Interface", str(connection_data['target_interface_id']))
        
        # Créer la connexion
        connection = ConnectionEntity(
            id=None,
            topology=topology,
            source_interface=source_interface,
            target_interface=target_interface,
            connection_type=connection_data.get('connection_type', 'ethernet'),
            status=connection_data.get('status', 'active'),
            description=connection_data.get('description', '')
        )
        
        return self._connection_repository.create(connection)
    
    def remove_connection(self, connection_id: int) -> bool:
        """
        Supprime une connexion.
        
        Args:
            connection_id (int): L'ID de la connexion à supprimer.
            
        Returns:
            bool: True si la connexion a été supprimée, False sinon.
            
        Raises:
            ResourceNotFoundException: Si la connexion n'a pas été trouvée.
        """
        # Vérifier que la connexion existe
        if not self._connection_repository.get_by_id(connection_id):
            raise ResourceNotFoundException("Connection", str(connection_id))
        
        # Supprimer la connexion
        return self._connection_repository.delete(connection_id)
    
    def generate_graph(self, topology_id: int) -> Dict[str, Any]:
        """
        Génère un graphe à partir d'une topologie.
        
        Args:
            topology_id (int): L'ID de la topologie à partir de laquelle générer le graphe.
            
        Returns:
            Dict[str, Any]: Un dictionnaire contenant le graphe généré.
            
        Raises:
            ResourceNotFoundException: Si la topologie n'a pas été trouvée.
        """
        # Vérifier que la topologie existe
        topology = self._topology_repository.get_by_id(topology_id)
        if not topology:
            raise ResourceNotFoundException("Topology", str(topology_id))
        
        # Récupérer les connexions
        connections = self._connection_repository.get_by_topology_id(topology_id)
        
        # Créer le graphe (implémentation simple sans networkx)
        devices = {}
        links = []

        # Collecter les équipements et connexions
        for connection in connections:
            source_device = connection.source_interface.device
            target_device = connection.target_interface.device

            # Ajouter les équipements
            if source_device.id not in devices:
                devices[source_device.id] = {
                    "id": source_device.id,
                    "name": source_device.name,
                    "type": source_device.device_type
                }

            if target_device.id not in devices:
                devices[target_device.id] = {
                    "id": target_device.id,
                    "name": target_device.name,
                    "type": target_device.device_type
                }

            # Ajouter la connexion
            links.append({
                "source": source_device.id,
                "target": target_device.id,
                "source_interface": connection.source_interface.name,
                "target_interface": connection.target_interface.name,
                "connection_type": connection.connection_type
            })

        # Retourner le résultat
        return {
            "nodes": list(devices.values()),
            "links": links
        }
    
    def _validate_topology_data(self, topology_data: Dict[str, Any]) -> None:
        """
        Valide les données d'une topologie.
        
        Args:
            topology_data (Dict[str, Any]): Les données de la topologie à valider.
            
        Raises:
            ValidationException: Si les données de la topologie sont invalides.
        """
        # Vérifier que les champs obligatoires sont présents
        required_fields = ['name']
        for field in required_fields:
            if field not in topology_data:
                raise ValidationException(f"Missing required field: {field}")
        
        # Vérifier que le nom n'est pas vide
        if not topology_data['name']:
            raise ValidationException("Topology name cannot be empty")
    
    def _validate_connection_data(self, connection_data: Dict[str, Any]) -> None:
        """
        Valide les données d'une connexion.
        
        Args:
            connection_data (Dict[str, Any]): Les données de la connexion à valider.
            
        Raises:
            ValidationException: Si les données de la connexion sont invalides.
        """
        # Vérifier que les champs obligatoires sont présents
        required_fields = ['source_interface_id', 'target_interface_id']
        for field in required_fields:
            if field not in connection_data:
                raise ValidationException(f"Missing required field: {field}")
        
        # Vérifier que les IDs sont valides
        if not isinstance(connection_data['source_interface_id'], int) or connection_data['source_interface_id'] <= 0:
            raise ValidationException("Invalid source interface ID")
        
        if not isinstance(connection_data['target_interface_id'], int) or connection_data['target_interface_id'] <= 0:
            raise ValidationException("Invalid target interface ID")
        
        # Vérifier que les interfaces sont différentes
        if connection_data['source_interface_id'] == connection_data['target_interface_id']:
            raise ValidationException("Source and target interfaces cannot be the same") 