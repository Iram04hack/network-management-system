"""
Interfaces pour les repositories du domaine Monitoring.
Ce module définit les contrats pour l'accès aux données persistantes.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

class AlertRepository(ABC):
    """
    Interface pour le repository des alertes.
    """
    
    @abstractmethod
    def get_by_id(self, alert_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère une alerte par son ID.
        
        Args:
            alert_id: ID de l'alerte à récupérer
            
        Returns:
            L'alerte récupérée ou None si elle n'existe pas
        """
        pass
    
    @abstractmethod
    def list_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Récupère une liste d'alertes filtrées.
        
        Args:
            filters: Filtres à appliquer (optionnel)
            
        Returns:
            Liste des alertes correspondant aux filtres
        """
        pass
    
    @abstractmethod
    def create(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée une nouvelle alerte.
        
        Args:
            alert_data: Données de l'alerte à créer
            
        Returns:
            L'alerte créée
        """
        pass
    
    @abstractmethod
    def update(self, alert_id: int, alert_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Met à jour une alerte.
        
        Args:
            alert_id: ID de l'alerte à mettre à jour
            alert_data: Nouvelles données pour l'alerte
            
        Returns:
            L'alerte mise à jour ou None si elle n'existe pas
        """
        pass
    
    @abstractmethod
    def update_status(self, alert_id: int, status: str, user_id: Optional[int], 
                     comment: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Met à jour le statut d'une alerte.
        
        Args:
            alert_id: ID de l'alerte
            status: Nouveau statut
            user_id: ID de l'utilisateur qui effectue la mise à jour
            comment: Commentaire optionnel
            
        Returns:
            L'alerte mise à jour ou None si elle n'existe pas
        """
        pass
    
    @abstractmethod
    def delete(self, alert_id: int) -> bool:
        """
        Supprime une alerte.
        
        Args:
            alert_id: ID de l'alerte à supprimer
            
        Returns:
            True si l'alerte a été supprimée, False sinon
        """
        pass
    
    @abstractmethod
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Compte le nombre d'alertes correspondant aux filtres.

        Args:
            filters: Filtres à appliquer (optionnel)

        Returns:
            Nombre d'alertes
        """
        pass


class AlertCommentRepository(ABC):
    """
    Interface pour le repository des commentaires d'alerte.
    """

    @abstractmethod
    def get_by_id(self, comment_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère un commentaire par son ID.

        Args:
            comment_id: ID du commentaire

        Returns:
            Le commentaire ou None s'il n'existe pas
        """
        pass

    @abstractmethod
    def get_by_alert(self, alert_id: int) -> List[Dict[str, Any]]:
        """
        Récupère les commentaires d'une alerte.

        Args:
            alert_id: ID de l'alerte

        Returns:
            Liste des commentaires
        """
        pass

    @abstractmethod
    def create(self, alert_id: int, user_id: int, comment: str) -> Dict[str, Any]:
        """
        Crée un nouveau commentaire.

        Args:
            alert_id: ID de l'alerte
            user_id: ID de l'utilisateur
            comment: Texte du commentaire

        Returns:
            Le commentaire créé
        """
        pass

    @abstractmethod
    def delete(self, comment_id: int) -> bool:
        """
        Supprime un commentaire.

        Args:
            comment_id: ID du commentaire

        Returns:
            True si supprimé, False sinon
        """
        pass


class AlertHistoryRepository(ABC):
    """
    Interface pour le repository de l'historique des alertes.
    """

    @abstractmethod
    def get_by_id(self, history_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère un élément d'historique par son ID.

        Args:
            history_id: ID de l'élément d'historique

        Returns:
            L'élément d'historique ou None s'il n'existe pas
        """
        pass

    @abstractmethod
    def get_by_alert(self, alert_id: int) -> List[Dict[str, Any]]:
        """
        Récupère l'historique d'une alerte.

        Args:
            alert_id: ID de l'alerte

        Returns:
            Liste des éléments d'historique
        """
        pass

    @abstractmethod
    def create(self, alert_id: int, action: str, user_id: Optional[int] = None,
              details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Crée un nouvel élément d'historique.

        Args:
            alert_id: ID de l'alerte
            action: Action effectuée
            user_id: ID de l'utilisateur (optionnel)
            details: Détails supplémentaires (optionnel)

        Returns:
            L'élément d'historique créé
        """
        pass


class DashboardRepository(ABC):
    """
    Interface pour le repository des tableaux de bord.
    """

    @abstractmethod
    def get_by_id(self, dashboard_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère un tableau de bord par son ID.

        Args:
            dashboard_id: ID du tableau de bord

        Returns:
            Le tableau de bord ou None s'il n'existe pas
        """
        pass

    @abstractmethod
    def get_by_uid(self, uid: str) -> Optional[Dict[str, Any]]:
        """
        Récupère un tableau de bord par son UID.

        Args:
            uid: UID du tableau de bord

        Returns:
            Le tableau de bord ou None s'il n'existe pas
        """
        pass

    @abstractmethod
    def list_by_user(self, user_id: int, include_public: bool = True) -> List[Dict[str, Any]]:
        """
        Liste les tableaux de bord accessibles par un utilisateur.

        Args:
            user_id: ID de l'utilisateur
            include_public: Inclure les tableaux publics

        Returns:
            Liste des tableaux de bord
        """
        pass

    @abstractmethod
    def create(self, dashboard_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un nouveau tableau de bord.

        Args:
            dashboard_data: Données du tableau de bord

        Returns:
            Le tableau de bord créé
        """
        pass

    @abstractmethod
    def update(self, dashboard_id: int, dashboard_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Met à jour un tableau de bord.

        Args:
            dashboard_id: ID du tableau de bord
            dashboard_data: Nouvelles données

        Returns:
            Le tableau de bord mis à jour ou None s'il n'existe pas
        """
        pass

    @abstractmethod
    def delete(self, dashboard_id: int) -> bool:
        """
        Supprime un tableau de bord.

        Args:
            dashboard_id: ID du tableau de bord

        Returns:
            True si supprimé, False sinon
        """
        pass

    @abstractmethod
    def get_default_dashboard(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère le tableau de bord par défaut d'un utilisateur.

        Args:
            user_id: ID de l'utilisateur

        Returns:
            Le tableau de bord par défaut ou None
        """
        pass


class DashboardShareRepository(ABC):
    """
    Interface pour le repository des partages de tableau de bord.
    """

    @abstractmethod
    def get_by_dashboard(self, dashboard_id: int) -> List[Dict[str, Any]]:
        """
        Récupère les partages d'un tableau de bord.

        Args:
            dashboard_id: ID du tableau de bord

        Returns:
            Liste des partages
        """
        pass

    @abstractmethod
    def create(self, dashboard_id: int, user_id: int, can_edit: bool = False) -> Dict[str, Any]:
        """
        Crée un nouveau partage.

        Args:
            dashboard_id: ID du tableau de bord
            user_id: ID de l'utilisateur
            can_edit: Autorisation d'édition

        Returns:
            Le partage créé
        """
        pass

    @abstractmethod
    def update(self, share_id: int, share_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Met à jour un partage.

        Args:
            share_id: ID du partage
            share_data: Nouvelles données

        Returns:
            Le partage mis à jour ou None s'il n'existe pas
        """
        pass

    @abstractmethod
    def delete(self, share_id: int) -> bool:
        """
        Supprime un partage.

        Args:
            share_id: ID du partage

        Returns:
            True si supprimé, False sinon
        """
        pass


class DeviceMetricRepository(ABC):
    """
    Interface pour le repository des métriques d'équipements.
    """
    
    @abstractmethod
    def get_by_id(self, device_metric_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère une métrique d'équipement par son ID.
        
        Args:
            device_metric_id: ID de la métrique
            
        Returns:
            La métrique récupérée ou None si elle n'existe pas
        """
        pass
    
    @abstractmethod
    def list_by_device(self, device_id: int) -> List[Dict[str, Any]]:
        """
        Liste les métriques pour un équipement.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            Liste des métriques de l'équipement
        """
        pass
    
    @abstractmethod
    def create(self, device_metric_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée une nouvelle métrique d'équipement.
        
        Args:
            device_metric_data: Données de la métrique
            
        Returns:
            La métrique créée
        """
        pass
    
    @abstractmethod
    def update(self, device_metric_id: int, device_metric_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Met à jour une métrique d'équipement.

        Args:
            device_metric_id: ID de la métrique
            device_metric_data: Nouvelles données

        Returns:
            La métrique mise à jour ou None si elle n'existe pas
        """
        pass

    @abstractmethod
    def list_all(self) -> List[Dict[str, Any]]:
        """
        Liste toutes les métriques d'équipements.

        Returns:
            Liste de toutes les métriques
        """
        pass


class MetricValueRepository(ABC):
    """
    Interface pour le repository des valeurs de métriques.
    """
    
    @abstractmethod
    def create(self, metric_value_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée une nouvelle valeur de métrique.
        
        Args:
            metric_value_data: Données de la valeur
            
        Returns:
            La valeur créée
        """
        pass
    
    @abstractmethod
    def create_batch(self, metric_values: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Crée un lot de valeurs de métriques.
        
        Args:
            metric_values: Liste des données de valeurs
            
        Returns:
            Liste des valeurs créées
        """
        pass
    
    @abstractmethod
    def get_values(self, device_metric_id: int, time_range: Dict[str, datetime],
                  aggregation: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Récupère les valeurs pour une métrique d'équipement sur une période donnée.

        Args:
            device_metric_id: ID de la métrique d'équipement
            time_range: Plage de temps (start et end)
            aggregation: Méthode d'agrégation optionnelle

        Returns:
            Liste des valeurs
        """
        pass

    @abstractmethod
    def save(self, metric_value_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sauvegarde une valeur de métrique (alias pour create).

        Args:
            metric_value_data: Données de la valeur

        Returns:
            La valeur sauvegardée
        """
        pass

    @abstractmethod
    def get_values_by_period(self, metric_id: int, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """
        Récupère les valeurs pour une métrique sur une période.

        Args:
            metric_id: ID de la métrique
            start_time: Début de la période
            end_time: Fin de la période

        Returns:
            Liste des valeurs
        """
        pass

    @abstractmethod
    def count_before_date(self, cutoff_date: datetime) -> int:
        """
        Compte les valeurs avant une date donnée.

        Args:
            cutoff_date: Date limite

        Returns:
            Nombre de valeurs
        """
        pass

    @abstractmethod
    def delete_before_date(self, cutoff_date: datetime) -> int:
        """
        Supprime les valeurs avant une date donnée.

        Args:
            cutoff_date: Date limite

        Returns:
            Nombre de valeurs supprimées
        """
        pass


class MetricsDefinitionRepository(ABC):
    """
    Interface pour le repository des définitions de métriques.
    """
    
    @abstractmethod
    def get_by_id(self, metrics_definition_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère une définition de métrique par son ID.
        
        Args:
            metrics_definition_id: ID de la définition
            
        Returns:
            La définition récupérée ou None si elle n'existe pas
        """
        pass
    
    @abstractmethod
    def list_all(self) -> List[Dict[str, Any]]:
        """
        Liste toutes les définitions de métriques.
        
        Returns:
            Liste des définitions
        """
        pass
    
    @abstractmethod
    def create(self, metrics_definition_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée une nouvelle définition de métrique.
        
        Args:
            metrics_definition_data: Données de la définition
            
        Returns:
            La définition créée
        """
        pass
    
    @abstractmethod
    def update(self, metrics_definition_id: int, metrics_definition_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Met à jour une définition de métrique.
        
        Args:
            metrics_definition_id: ID de la définition
            metrics_definition_data: Nouvelles données
            
        Returns:
            La définition mise à jour ou None si elle n'existe pas
        """
        pass
    
    @abstractmethod
    def delete(self, metrics_definition_id: int) -> bool:
        """
        Supprime une définition de métrique.

        Args:
            metrics_definition_id: ID de la définition

        Returns:
            True si la définition a été supprimée, False sinon
        """
        pass

    @abstractmethod
    def get_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Récupère les définitions par catégorie.

        Args:
            category: Catégorie des métriques

        Returns:
            Liste des définitions de la catégorie
        """
        pass

    @abstractmethod
    def get_by_collection_method(self, collection_method: str) -> List[Dict[str, Any]]:
        """
        Récupère les définitions par méthode de collecte.

        Args:
            collection_method: Méthode de collecte

        Returns:
            Liste des définitions avec cette méthode
        """
        pass

    @abstractmethod
    def get_thresholds(self, metric_id: int) -> List[Dict[str, Any]]:
        """
        Récupère les seuils pour une métrique.

        Args:
            metric_id: ID de la métrique

        Returns:
            Liste des seuils
        """
        pass


class MonitoringTemplateRepository(ABC):
    """
    Interface pour le repository des templates de surveillance.
    """
    
    @abstractmethod
    def get_by_id(self, template_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère un template par son ID.
        
        Args:
            template_id: ID du template
            
        Returns:
            Le template récupéré ou None s'il n'existe pas
        """
        pass
    
    @abstractmethod
    def list_all(self) -> List[Dict[str, Any]]:
        """
        Liste tous les templates.
        
        Returns:
            Liste des templates
        """
        pass
    
    @abstractmethod
    def create(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un nouveau template.
        
        Args:
            template_data: Données du template
            
        Returns:
            Le template créé
        """
        pass
    
    @abstractmethod
    def update(self, template_id: int, template_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Met à jour un template.
        
        Args:
            template_id: ID du template
            template_data: Nouvelles données
            
        Returns:
            Le template mis à jour ou None s'il n'existe pas
        """
        pass
    
    @abstractmethod
    def delete(self, template_id: int) -> bool:
        """
        Supprime un template.
        
        Args:
            template_id: ID du template
            
        Returns:
            True si le template a été supprimé, False sinon
        """
        pass


class ServiceCheckRepository(ABC):
    """
    Interface pour le repository des vérifications de service.
    """
    
    @abstractmethod
    def get_by_id(self, service_check_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère une vérification par son ID.
        
        Args:
            service_check_id: ID de la vérification
            
        Returns:
            La vérification ou None si elle n'existe pas
        """
        pass
    
    @abstractmethod
    def list_all(self) -> List[Dict[str, Any]]:
        """
        Liste toutes les vérifications.
        
        Returns:
            Liste des vérifications
        """
        pass
    
    @abstractmethod
    def list_by_device(self, device_id: int) -> List[Dict[str, Any]]:
        """
        Liste les vérifications pour un équipement.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            Liste des vérifications
        """
        pass
    
    @abstractmethod
    def create(self, service_check_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée une nouvelle vérification.
        
        Args:
            service_check_data: Données de la vérification
            
        Returns:
            La vérification créée
        """
        pass
    
    @abstractmethod
    def update(self, service_check_id: int, service_check_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Met à jour une vérification.
        
        Args:
            service_check_id: ID de la vérification
            service_check_data: Nouvelles données
            
        Returns:
            La vérification mise à jour ou None si elle n'existe pas
        """
        pass
    
    @abstractmethod
    def delete(self, service_check_id: int) -> bool:
        """
        Supprime une vérification.
        
        Args:
            service_check_id: ID de la vérification
            
        Returns:
            True si la vérification a été supprimée, False sinon
        """
        pass


class NotificationRepository(ABC):
    """
    Interface pour le repository des notifications.
    """
    
    @abstractmethod
    def create(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée une nouvelle notification.
        
        Args:
            notification_data: Données de la notification
            
        Returns:
            La notification créée
        """
        pass
    
    @abstractmethod
    def list_by_user(self, user_id: int, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Liste les notifications pour un utilisateur.
        
        Args:
            user_id: ID de l'utilisateur
            filters: Filtres à appliquer (optionnel)
            
        Returns:
            Liste des notifications
        """
        pass
    
    @abstractmethod
    def mark_as_read(self, notification_id: int) -> Optional[Dict[str, Any]]:
        """
        Marque une notification comme lue.
        
        Args:
            notification_id: ID de la notification
            
        Returns:
            La notification mise à jour ou None si elle n'existe pas
        """
        pass
    
    @abstractmethod
    def delete(self, notification_id: int) -> bool:
        """
        Supprime une notification.

        Args:
            notification_id: ID de la notification

        Returns:
            True si la notification a été supprimée, False sinon
        """
        pass

    @abstractmethod
    def update(self, notification_id: int, notification_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Met à jour une notification.

        Args:
            notification_id: ID de la notification
            notification_data: Nouvelles données

        Returns:
            La notification mise à jour ou None si elle n'existe pas
        """
        pass


class NotificationChannelRepository(ABC):
    """
    Interface pour le repository des canaux de notification.
    """

    @abstractmethod
    def get_by_id(self, channel_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère un canal par son ID.

        Args:
            channel_id: ID du canal

        Returns:
            Le canal ou None s'il n'existe pas
        """
        pass

    @abstractmethod
    def list_by_user(self, user_id: int, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Liste les canaux d'un utilisateur.

        Args:
            user_id: ID de l'utilisateur
            filters: Filtres à appliquer (optionnel)

        Returns:
            Liste des canaux
        """
        pass

    @abstractmethod
    def create(self, channel_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un nouveau canal.

        Args:
            channel_data: Données du canal

        Returns:
            Le canal créé
        """
        pass

    @abstractmethod
    def update(self, channel_id: int, channel_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Met à jour un canal.

        Args:
            channel_id: ID du canal
            channel_data: Nouvelles données

        Returns:
            Le canal mis à jour ou None s'il n'existe pas
        """
        pass

    @abstractmethod
    def delete(self, channel_id: int) -> bool:
        """
        Supprime un canal.

        Args:
            channel_id: ID du canal

        Returns:
            True si supprimé, False sinon
        """
        pass


class NotificationRuleRepository(ABC):
    """
    Interface pour le repository des règles de notification.
    """

    @abstractmethod
    def get_by_id(self, rule_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère une règle par son ID.

        Args:
            rule_id: ID de la règle

        Returns:
            La règle ou None si elle n'existe pas
        """
        pass

    @abstractmethod
    def list_by_user(self, user_id: int, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Liste les règles d'un utilisateur.

        Args:
            user_id: ID de l'utilisateur
            filters: Filtres à appliquer (optionnel)

        Returns:
            Liste des règles
        """
        pass

    @abstractmethod
    def create(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée une nouvelle règle.

        Args:
            rule_data: Données de la règle

        Returns:
            La règle créée
        """
        pass

    @abstractmethod
    def update(self, rule_id: int, rule_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Met à jour une règle.

        Args:
            rule_id: ID de la règle
            rule_data: Nouvelles données

        Returns:
            La règle mise à jour ou None si elle n'existe pas
        """
        pass

    @abstractmethod
    def delete(self, rule_id: int) -> bool:
        """
        Supprime une règle.

        Args:
            rule_id: ID de la règle

        Returns:
            True si supprimée, False sinon
        """
        pass


class DeviceServiceCheckRepository(ABC):
    """
    Interface pour le repository des vérifications de service appliquées aux équipements.
    """
    
    @abstractmethod
    def get_by_id(self, device_service_check_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère une vérification de service appliquée par son ID.
        
        Args:
            device_service_check_id: ID de la vérification appliquée
            
        Returns:
            La vérification appliquée ou None si elle n'existe pas
        """
        pass
    
    @abstractmethod
    def list_by_device(self, device_id: int) -> List[Dict[str, Any]]:
        """
        Liste les vérifications appliquées pour un équipement.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            Liste des vérifications appliquées
        """
        pass
    
    @abstractmethod
    def list_by_service_check(self, service_check_id: int) -> List[Dict[str, Any]]:
        """
        Liste les applications d'une vérification de service.
        
        Args:
            service_check_id: ID de la vérification de service
            
        Returns:
            Liste des applications
        """
        pass
    
    @abstractmethod
    def create(self, device_service_check_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée une nouvelle application de vérification de service.
        
        Args:
            device_service_check_data: Données de l'application
            
        Returns:
            L'application créée
        """
        pass
    
    @abstractmethod
    def update(self, device_service_check_id: int, device_service_check_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Met à jour une application de vérification de service.
        
        Args:
            device_service_check_id: ID de l'application
            device_service_check_data: Nouvelles données
            
        Returns:
            L'application mise à jour ou None si elle n'existe pas
        """
        pass
    
    @abstractmethod
    def delete(self, device_service_check_id: int) -> bool:
        """
        Supprime une application de vérification de service.
        
        Args:
            device_service_check_id: ID de l'application
            
        Returns:
            True si l'application a été supprimée, False sinon
        """
        pass


class CheckResultRepository(ABC):
    """
    Interface pour le repository des résultats de vérification.
    """
    
    @abstractmethod
    def get_by_id(self, check_result_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère un résultat de vérification par son ID.
        
        Args:
            check_result_id: ID du résultat
            
        Returns:
            Le résultat récupéré ou None s'il n'existe pas
        """
        pass
    
    @abstractmethod
    def list_by_device_service_check(self, device_service_check_id: int, 
                                   limit: int = 100) -> List[Dict[str, Any]]:
        """
        Liste les résultats pour une vérification appliquée.
        
        Args:
            device_service_check_id: ID de la vérification appliquée
            limit: Nombre maximum de résultats à récupérer
            
        Returns:
            Liste des résultats
        """
        pass
    
    @abstractmethod
    def create(self, check_result_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un nouveau résultat de vérification.
        
        Args:
            check_result_data: Données du résultat
            
        Returns:
            Le résultat créé
        """
        pass
    
    @abstractmethod
    def create_batch(self, check_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Crée un lot de résultats de vérification.
        
        Args:
            check_results: Liste des données de résultats
            
        Returns:
            Liste des résultats créés
        """
        pass


class DashboardRepository(ABC):
    """
    Interface pour le repository des tableaux de bord.
    """
    
    @abstractmethod
    def get_by_id(self, dashboard_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère un tableau de bord par son ID.
        
        Args:
            dashboard_id: ID du tableau de bord
            
        Returns:
            Le tableau de bord récupéré ou None s'il n'existe pas
        """
        pass
    
    @abstractmethod
    def list_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Liste les tableaux de bord d'un utilisateur.
        
        Args:
            user_id: ID de l'utilisateur
            
        Returns:
            Liste des tableaux de bord
        """
        pass
    
    @abstractmethod
    def create(self, dashboard_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un nouveau tableau de bord.
        
        Args:
            dashboard_data: Données du tableau de bord
            
        Returns:
            Le tableau de bord créé
        """
        pass
    
    @abstractmethod
    def update(self, dashboard_id: int, dashboard_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Met à jour un tableau de bord.
        
        Args:
            dashboard_id: ID du tableau de bord
            dashboard_data: Nouvelles données
            
        Returns:
            Le tableau de bord mis à jour ou None s'il n'existe pas
        """
        pass
    
    @abstractmethod
    def delete(self, dashboard_id: int) -> bool:
        """
        Supprime un tableau de bord.
        
        Args:
            dashboard_id: ID du tableau de bord
            
        Returns:
            True si le tableau de bord a été supprimé, False sinon
        """
        pass
    
    @abstractmethod
    def add_widget(self, dashboard_id: int, widget_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ajoute un widget à un tableau de bord.
        
        Args:
            dashboard_id: ID du tableau de bord
            widget_data: Données du widget
            
        Returns:
            Le widget ajouté
        """
        pass
    
    @abstractmethod
    def update_widget(self, widget_id: int, widget_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Met à jour un widget.
        
        Args:
            widget_id: ID du widget
            widget_data: Nouvelles données
            
        Returns:
            Le widget mis à jour ou None s'il n'existe pas
        """
        pass
    
    @abstractmethod
    def delete_widget(self, widget_id: int) -> bool:
        """
        Supprime un widget.
        
        Args:
            widget_id: ID du widget
            
        Returns:
            True si le widget a été supprimé, False sinon
        """
        pass 