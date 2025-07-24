"""
Service d'application pour la gestion des configurations réseau.

Ce module contient le service d'application qui implémente
les cas d'utilisation liés à la gestion des configurations réseau.
"""

from typing import Dict, Any, List, Optional, Union
from ...domain.exceptions import ResourceNotFoundException, ValidationException, ConfigurationException
from ...domain.interfaces import DeviceConfigPort, ConfigurationValidationPort, ConfigurationTemplateService
from ..ports.input_ports import NetworkConfigurationUseCases
from ..ports.output_ports import DevicePersistencePort, ConfigurationPersistencePort, TemplatePersistencePort


class ConfigurationService(NetworkConfigurationUseCases):
    """
    Service d'application pour la gestion des configurations réseau.
    
    Cette classe implémente les cas d'utilisation liés à la gestion des configurations réseau
    en utilisant les ports de sortie pour interagir avec les adaptateurs secondaires.
    """
    
    def __init__(
        self,
        device_repository: DevicePersistencePort,
        config_repository: ConfigurationPersistencePort,
        template_repository: TemplatePersistencePort,
        device_config_port: DeviceConfigPort,
        config_validation_port: ConfigurationValidationPort,
        template_service: ConfigurationTemplateService
    ):
        """
        Initialise le service avec les dépendances nécessaires.
        
        Args:
            device_repository: Repository pour les équipements réseau
            config_repository: Repository pour les configurations
            template_repository: Repository pour les modèles de configuration
            device_config_port: Port pour la gestion des configurations d'équipements
            config_validation_port: Port pour la validation des configurations
            template_service: Service pour les modèles de configuration
        """
        self.device_repository = device_repository
        self.config_repository = config_repository
        self.template_repository = template_repository
        self.device_config_port = device_config_port
        self.config_validation_port = config_validation_port
        self.template_service = template_service
    
    def get_device_configuration(self, device_id: int) -> Dict[str, Any]:
        """
        Récupère la configuration actuelle d'un équipement.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            Configuration de l'équipement
            
        Raises:
            ResourceNotFoundException: Si l'équipement n'existe pas
            ConfigurationException: Si la récupération de la configuration échoue
        """
        # Vérifie que l'équipement existe
        self.device_repository.get_device_by_id(device_id)
        
        try:
            # Récupère la configuration actuelle depuis l'équipement
            config = self.device_config_port.get_current_config(device_id)
            
            # Enregistre la configuration dans le repository
            config_data = {
                "device_id": device_id,
                "content": config.get("content", ""),
                "version": config.get("version", "running"),
                "is_active": True,
                "created_by": "system",
                "comment": "Configuration récupérée automatiquement"
            }
            
            saved_config = self.config_repository.create_configuration(config_data)
            
            return saved_config
        except Exception as e:
            # Essaie de récupérer la dernière configuration connue
            try:
                return self.config_repository.get_latest_configuration_by_device(device_id)
            except ResourceNotFoundException:
                # Aucune configuration n'est disponible
                raise ConfigurationException(f"Impossible de récupérer la configuration de l'équipement {device_id}: {str(e)}")
    
    def get_configuration_history(self, device_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Récupère l'historique des configurations d'un équipement.
        
        Args:
            device_id: ID de l'équipement
            limit: Nombre maximum de configurations à récupérer
            
        Returns:
            Liste des configurations
            
        Raises:
            ResourceNotFoundException: Si l'équipement n'existe pas
        """
        # Vérifie que l'équipement existe
        self.device_repository.get_device_by_id(device_id)
        
        return self.config_repository.get_configuration_history_by_device(device_id, limit)
    
    def apply_configuration(self, device_id: int, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Applique une configuration à un équipement.
        
        Args:
            device_id: ID de l'équipement
            config_data: Données de configuration
            
        Returns:
            Résultat de l'opération
            
        Raises:
            ResourceNotFoundException: Si l'équipement n'existe pas
            ValidationException: Si les données sont invalides
            ConfigurationException: Si l'application de la configuration échoue
        """
        # Vérifie que l'équipement existe
        self.device_repository.get_device_by_id(device_id)
        
        # Valide les données de configuration
        self._validate_config_data(config_data)
        
        # Valide la configuration
        validation_result = self.validate_configuration(device_id, config_data)
        if not validation_result.get("is_valid", False):
            raise ValidationException("Configuration invalide", validation_result.get("errors", {}))
        
        # Enregistre la configuration
        config_content = config_data.get("content", "")
        config_version = config_data.get("version", "candidate")
        config_comment = config_data.get("comment", "")
        config_created_by = config_data.get("created_by", "user")
        
        saved_config = self.config_repository.create_configuration({
            "device_id": device_id,
            "content": config_content,
            "version": config_version,
            "is_active": False,
            "created_by": config_created_by,
            "comment": config_comment
        })
        
        # Applique la configuration à l'équipement
        try:
            result = self.device_config_port.apply_config(device_id, saved_config["id"])
            
            # Met à jour le statut de la configuration
            if result.get("success", False):
                self.config_repository.update_configuration(saved_config["id"], {
                    "is_active": True,
                    "applied_at": result.get("applied_at"),
                    "status": "applied"
                })
            else:
                self.config_repository.update_configuration(saved_config["id"], {
                    "status": "failed",
                    "error": result.get("error", "")
                })
            
            return {
                "config_id": saved_config["id"],
                "success": result.get("success", False),
                "message": result.get("message", ""),
                "details": result.get("details", {})
            }
        except Exception as e:
            # Met à jour le statut de la configuration en cas d'erreur
            self.config_repository.update_configuration(saved_config["id"], {
                "status": "failed",
                "error": str(e)
            })
            
            raise ConfigurationException(f"Erreur lors de l'application de la configuration: {str(e)}")
    
    def validate_configuration(self, device_id: int, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valide une configuration pour un équipement.
        
        Args:
            device_id: ID de l'équipement
            config_data: Données de configuration
            
        Returns:
            Résultat de la validation
            
        Raises:
            ResourceNotFoundException: Si l'équipement n'existe pas
        """
        # Vérifie que l'équipement existe
        self.device_repository.get_device_by_id(device_id)
        
        # Récupère le contenu de la configuration
        config_content = config_data.get("content", "")
        
        # Valide la configuration
        try:
            validation_result = self.config_validation_port.validate(device_id, config_content)
            return validation_result
        except Exception as e:
            return {
                "is_valid": False,
                "errors": {"general": str(e)},
                "warnings": []
            }
    
    def rollback_configuration(self, device_id: int, version_id: int) -> Dict[str, Any]:
        """
        Restaure une version précédente de la configuration d'un équipement.
        
        Args:
            device_id: ID de l'équipement
            version_id: ID de la version de configuration
            
        Returns:
            Résultat de l'opération
            
        Raises:
            ResourceNotFoundException: Si l'équipement ou la version n'existe pas
            ConfigurationException: Si la restauration échoue
        """
        # Vérifie que l'équipement existe
        self.device_repository.get_device_by_id(device_id)
        
        # Vérifie que la version existe
        config_version = self.config_repository.get_configuration_by_id(version_id)
        
        # Vérifie que la version appartient à l'équipement
        if config_version.get("device_id") != device_id:
            raise ResourceNotFoundException("Configuration", version_id)
        
        # Applique la configuration à l'équipement
        try:
            result = self.device_config_port.rollback_config(device_id, version_id)
            
            # Crée une nouvelle version de configuration pour le rollback
            rollback_config = self.config_repository.create_configuration({
                "device_id": device_id,
                "content": config_version.get("content", ""),
                "version": "rollback",
                "is_active": result.get("success", False),
                "created_by": "system",
                "comment": f"Rollback vers la version {version_id}",
                "parent_id": version_id
            })
            
            return {
                "config_id": rollback_config["id"],
                "success": result.get("success", False),
                "message": result.get("message", ""),
                "details": result.get("details", {})
            }
        except Exception as e:
            raise ConfigurationException(f"Erreur lors de la restauration de la configuration: {str(e)}")
    
    def get_configuration_templates(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Récupère les modèles de configuration correspondant aux filtres.
        
        Args:
            filters: Filtres à appliquer (optionnel)
            
        Returns:
            Liste des modèles
        """
        return self.template_repository.get_all_templates(filters)
    
    def render_configuration_template(self, template_id: int, variables: Dict[str, Any]) -> Dict[str, Any]:
        """
        Génère une configuration à partir d'un modèle.
        
        Args:
            template_id: ID du modèle
            variables: Variables à injecter
            
        Returns:
            Configuration générée
            
        Raises:
            ResourceNotFoundException: Si le modèle n'existe pas
            ValidationException: Si les variables sont invalides
        """
        # Récupère le modèle
        template = self.template_repository.get_template_by_id(template_id)
        
        # Valide les variables
        required_vars = self.template_service.extract_variables(template.get("content", ""))
        missing_vars = [var for var in required_vars if var not in variables]
        
        if missing_vars:
            raise ValidationException(
                "Variables manquantes",
                {"variables": f"Variables requises manquantes: {', '.join(missing_vars)}"}
            )
        
        # Génère la configuration
        try:
            rendered_content = self.template_service.render_template(template_id, variables)
            
            return {
                "template_id": template_id,
                "template_name": template.get("name", ""),
                "content": rendered_content,
                "variables": variables
            }
        except Exception as e:
            raise ValidationException("Erreur lors de la génération de la configuration", {"general": str(e)})
    
    def _validate_config_data(self, config_data: Dict[str, Any]) -> None:
        """
        Valide les données de configuration.
        
        Args:
            config_data: Données à valider
            
        Raises:
            ValidationException: Si les données sont invalides
        """
        errors = {}
        
        # Vérifie que le contenu est présent
        if "content" not in config_data or not config_data["content"]:
            errors["content"] = "Le contenu de la configuration est requis"
        
        # Si des erreurs sont détectées, lève une exception
        if errors:
            raise ValidationException("Données de configuration invalides", errors) 