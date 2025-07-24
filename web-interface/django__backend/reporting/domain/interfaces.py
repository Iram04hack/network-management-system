"""
Interfaces du domaine pour le module Reporting.

Ce module définit les contrats que doivent respecter les implémentations
concrètes des services et repositories liés aux rapports.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, BinaryIO
from datetime import datetime
from enum import Enum

class ReportFormat(Enum):
    """Formats de rapports supportés."""
    PDF = "pdf"
    XLSX = "xlsx"
    CSV = "csv"
    JSON = "json"
    HTML = "html"

class VisualizationType(Enum):
    """Types de visualisations supportées."""
    CHART = "chart"
    TABLE = "table"
    GRAPH = "graph"
    MAP = "map"
    DASHBOARD = "dashboard"

class ReportRepository(ABC):
    """
    Interface pour le repository des rapports.
    
    Responsable de l'accès et de la manipulation des données des rapports.
    """
    
    @abstractmethod
    def get_by_id(self, report_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère un rapport par son ID.
        
        Args:
            report_id: ID du rapport à récupérer
            
        Returns:
            Le rapport correspondant ou None s'il n'existe pas
        """
        pass
    
    @abstractmethod
    def list(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Liste les rapports selon des filtres optionnels.
        
        Args:
            filters: Dictionnaire de filtres (report_type, status, created_by...)
            
        Returns:
            Liste des rapports correspondants
        """
        pass
    
    @abstractmethod
    def create(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un nouveau rapport.
        
        Args:
            report_data: Données du rapport
            
        Returns:
            Le rapport créé avec son ID généré
        """
        pass
    
    @abstractmethod
    def update(self, report_id: int, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour un rapport existant.
        
        Args:
            report_id: ID du rapport à mettre à jour
            report_data: Nouvelles données
            
        Returns:
            Le rapport mis à jour
        """
        pass
    
    @abstractmethod
    def update_status(self, report_id: int, status: str) -> Dict[str, Any]:
        """
        Met à jour le statut d'un rapport.
        
        Args:
            report_id: ID du rapport
            status: Nouveau statut ('draft', 'processing', 'completed', 'failed')
            
        Returns:
            Le rapport mis à jour
        """
        pass
    
    @abstractmethod
    def update_content(self, report_id: int, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour le contenu d'un rapport.
        
        Args:
            report_id: ID du rapport
            content: Nouveau contenu
            
        Returns:
            Le rapport mis à jour
        """
        pass
    
    @abstractmethod
    def delete(self, report_id: int) -> bool:
        """
        Supprime un rapport.
        
        Args:
            report_id: ID du rapport à supprimer
            
        Returns:
            True si la suppression a réussi
        """
        pass

class ReportTemplateRepository(ABC):
    """
    Interface pour le repository des modèles de rapport.
    
    Responsable de l'accès et de la manipulation des données des modèles de rapport.
    """
    
    @abstractmethod
    def get_by_id(self, template_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère un modèle de rapport par son ID.
        
        Args:
            template_id: ID du modèle à récupérer
            
        Returns:
            Le modèle correspondant ou None s'il n'existe pas
        """
        pass
    
    @abstractmethod
    def list(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Liste les modèles de rapport selon des filtres optionnels.
        
        Args:
            filters: Dictionnaire de filtres (template_type, is_active...)
            
        Returns:
            Liste des modèles correspondants
        """
        pass

    @abstractmethod
    def create(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un nouveau template de rapport.
        
        Args:
            template_data: Données du template
            
        Returns:
            Le template créé avec son ID généré
        """
        pass
    
    @abstractmethod
    def update(self, template_id: int, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour un template existant.
        
        Args:
            template_id: ID du template à mettre à jour
            template_data: Nouvelles données
            
        Returns:
            Le template mis à jour
        """
        pass
    
    @abstractmethod
    def delete(self, template_id: int) -> bool:
        """
        Supprime un template.
        
        Args:
            template_id: ID du template à supprimer
            
        Returns:
            True si la suppression a réussi
        """
        pass

class ScheduledReportRepository(ABC):
    """
    Interface pour le repository des rapports planifiés.
    
    Responsable de l'accès et de la manipulation des données des rapports planifiés.
    """
    
    @abstractmethod
    def get_by_id(self, scheduled_report_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère un rapport planifié par son ID.
        
        Args:
            scheduled_report_id: ID du rapport planifié à récupérer
            
        Returns:
            Le rapport planifié correspondant ou None s'il n'existe pas
        """
        pass
    
    @abstractmethod
    def list(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Liste les rapports planifiés selon des filtres optionnels.
        
        Args:
            filters: Dictionnaire de filtres (report_type, frequency, is_active...)
            
        Returns:
            Liste des rapports planifiés correspondants
        """
        pass
    
    @abstractmethod
    def create(self, scheduled_report_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un nouveau rapport planifié.
        
        Args:
            scheduled_report_data: Données du rapport planifié
            
        Returns:
            Le rapport planifié créé avec son ID généré
        """
        pass
    
    @abstractmethod
    def update(self, scheduled_report_id: int, scheduled_report_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour un rapport planifié existant.
        
        Args:
            scheduled_report_id: ID du rapport planifié à mettre à jour
            scheduled_report_data: Nouvelles données
            
        Returns:
            Le rapport planifié mis à jour
        """
        pass
    
    @abstractmethod
    def delete(self, scheduled_report_id: int) -> bool:
        """
        Supprime un rapport planifié.
        
        Args:
            scheduled_report_id: ID du rapport planifié à supprimer
            
        Returns:
            True si la suppression a réussi
        """
        pass
    
    @abstractmethod
    def add_recipient(self, scheduled_report_id: int, user_id: int) -> bool:
        """
        Ajoute un destinataire à un rapport planifié.
        
        Args:
            scheduled_report_id: ID du rapport planifié
            user_id: ID de l'utilisateur à ajouter
            
        Returns:
            True si l'ajout a réussi
        """
        pass
    
    @abstractmethod
    def remove_recipient(self, scheduled_report_id: int, user_id: int) -> bool:
        """
        Retire un destinataire d'un rapport planifié.
        
        Args:
            scheduled_report_id: ID du rapport planifié
            user_id: ID de l'utilisateur à retirer
            
        Returns:
            True si le retrait a réussi
        """
        pass

class ReportGenerationService(ABC):
    """
    Interface pour le service de génération de rapports.
    
    Responsable de la génération et du traitement des rapports.
    """
    
    @abstractmethod
    def generate_report(self, report_id: int) -> bool:
        """
        Génère un rapport.
        
        Args:
            report_id: ID du rapport à générer
            
        Returns:
            True si la génération a réussi
        """
        pass
    
    @abstractmethod
    def regenerate_report(self, report_id: int) -> bool:
        """
        Régénère un rapport existant.
        
        Args:
            report_id: ID du rapport à régénérer
            
        Returns:
            True si la régénération a réussi
        """
        pass

class ReportStorageService(ABC):
    """
    Interface pour le service de stockage des rapports.
    
    Responsable du stockage, de l'archivage et de la gestion des fichiers de rapports.
    """
    
    @abstractmethod
    def store(self, content: Any, report_type: str, file_format: str, 
              metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Stocke un rapport généré.
        
        Args:
            content: Contenu du rapport
            report_type: Type de rapport
            file_format: Format du fichier
            metadata: Métadonnées additionnelles
            
        Returns:
            Chemin/URL du fichier stocké
        """
        pass
    
    @abstractmethod
    def retrieve(self, file_path: str) -> Optional[BinaryIO]:
        """
        Récupère un rapport stocké.
        
        Args:
            file_path: Chemin du fichier
            
        Returns:
            Contenu du fichier ou None si non trouvé
        """
        pass
    
    @abstractmethod
    def delete(self, file_path: str) -> bool:
        """
        Supprime un fichier de rapport.
        
        Args:
            file_path: Chemin du fichier à supprimer
            
        Returns:
            True si la suppression a réussi
        """
        pass
    
    @abstractmethod
    def archive(self, file_path: str, archive_location: str) -> bool:
        """
        Archive un rapport ancien.
        
        Args:
            file_path: Chemin du fichier à archiver
            archive_location: Emplacement d'archivage
            
        Returns:
            True si l'archivage a réussi
        """
        pass
    
    @abstractmethod
    def compress(self, file_path: str) -> str:
        """
        Compresse un fichier de rapport.
        
        Args:
            file_path: Chemin du fichier à compresser
            
        Returns:
            Chemin du fichier compressé
        """
        pass

class VisualizationService(ABC):
    """
    Interface pour le service de visualisation de rapports.
    
    Responsable de la création de visualisations interactives et de graphiques.
    """
    
    @abstractmethod
    def create_visualization(self, data: Dict[str, Any], 
                           visualization_type: VisualizationType,
                           config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée une visualisation à partir des données.
        
        Args:
            data: Données à visualiser
            visualization_type: Type de visualisation
            config: Configuration de la visualisation
            
        Returns:
            Configuration de la visualisation créée
        """
        pass
    
    @abstractmethod
    def generate_interactive_dashboard(self, report_id: int,
                                     widgets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Génère un dashboard interactif.
        
        Args:
            report_id: ID du rapport
            widgets: Liste des widgets à inclure
            
        Returns:
            Configuration du dashboard
        """
        pass
    
    @abstractmethod
    def export_visualization(self, visualization_id: str, 
                           export_format: ReportFormat) -> str:
        """
        Exporte une visualisation dans un format spécifié.
        
        Args:
            visualization_id: ID de la visualisation
            export_format: Format d'export
            
        Returns:
            Chemin du fichier exporté
        """
        pass

class AnalyticsService(ABC):
    """
    Interface pour le service d'analyse avancée.
    
    Responsable de l'analyse prédictive, de la détection d'anomalies et des insights.
    """
    
    @abstractmethod
    def detect_anomalies(self, data: List[Dict[str, Any]], 
                        config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Détecte les anomalies dans les données.
        
        Args:
            data: Données à analyser
            config: Configuration de l'analyse
            
        Returns:
            Liste des anomalies détectées
        """
        pass
    
    @abstractmethod
    def predict_trends(self, historical_data: List[Dict[str, Any]], 
                      prediction_horizon: int) -> Dict[str, Any]:
        """
        Prédit les tendances futures.
        
        Args:
            historical_data: Données historiques
            prediction_horizon: Horizon de prédiction (en jours)
            
        Returns:
            Prédictions et métriques de confiance
        """
        pass
    
    @abstractmethod
    def generate_insights(self, report_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Génère des insights automatiques.
        
        Args:
            report_data: Données du rapport
            
        Returns:
            Liste des insights générés
        """
        pass
    
    @abstractmethod
    def correlation_analysis(self, datasets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyse les corrélations entre différents datasets.
        
        Args:
            datasets: Liste des jeux de données
            
        Returns:
            Matrice de corrélation et insights
        """
        pass

class DataIntegrationService(ABC):
    """
    Interface pour le service d'intégration de données.
    
    Responsable de l'agrégation et de la fusion de données multi-sources.
    """
    
    @abstractmethod
    def integrate_data_sources(self, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Intègre des données de sources multiples.
        
        Args:
            sources: Liste des sources de données avec leurs configurations
            
        Returns:
            Données intégrées et métadonnées
        """
        pass
    
    @abstractmethod
    def transform_data(self, data: Dict[str, Any], 
                      transformation_rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Transforme les données selon des règles définies.
        
        Args:
            data: Données source
            transformation_rules: Règles de transformation
            
        Returns:
            Données transformées
        """
        pass
    
    @abstractmethod
    def validate_data_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valide la qualité des données.
        
        Args:
            data: Données à valider
            
        Returns:
            Rapport de qualité des données
        """
        pass

class ScheduledReportService(ABC):
    """
    Interface pour le service de gestion des rapports planifiés.
    
    Responsable de l'exécution et de la gestion des rapports planifiés.
    """
    
    @abstractmethod
    def process_scheduled_report(self, scheduled_report_id: int) -> bool:
        """
        Traite un rapport planifié.
        
        Args:
            scheduled_report_id: ID du rapport planifié à traiter
            
        Returns:
            True si le traitement a réussi
        """
        pass
    
    @abstractmethod
    def get_due_reports(self, reference_date: datetime = None) -> List[Dict[str, Any]]:
        """
        Récupère les rapports planifiés à exécuter.
        
        Args:
            reference_date: Date de référence (par défaut: maintenant)
            
        Returns:
            Liste des rapports planifiés à exécuter
        """
        pass
    
    @abstractmethod
    def send_report(self, report_id: int, recipient_ids: List[int]) -> bool:
        """
        Envoie un rapport aux destinataires spécifiés.
        
        Args:
            report_id: ID du rapport à envoyer
            recipient_ids: Liste des IDs des destinataires
            
        Returns:
            True si l'envoi a réussi
        """
        pass

class CacheService(ABC):
    """
    Interface pour le service de mise en cache.
    
    Responsable de la gestion du cache pour optimiser les performances.
    """
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """
        Récupère une valeur du cache.
        
        Args:
            key: Clé de cache
            
        Returns:
            Valeur mise en cache ou None
        """
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Met en cache une valeur.
        
        Args:
            key: Clé de cache
            value: Valeur à mettre en cache
            ttl: Durée de vie en secondes
            
        Returns:
            True si la mise en cache a réussi
        """
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        Supprime une entrée du cache.
        
        Args:
            key: Clé à supprimer
            
        Returns:
            True si la suppression a réussi
        """
        pass
    
    @abstractmethod
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalide toutes les clés correspondant à un pattern.
        
        Args:
            pattern: Pattern de clés à invalider
            
        Returns:
            Nombre de clés invalidées
        """
        pass

class ReportDistributionService(ABC):
    """
    Interface pour le service de distribution des rapports.
    
    Responsable de la distribution des rapports aux destinataires.
    """
    
    @abstractmethod
    def distribute_report(self, report_id: int, recipients: List[int], 
                          distribution_method: str) -> bool:
        """
        Distribue un rapport aux destinataires spécifiés.
        
        Args:
            report_id: ID du rapport à distribuer
            recipients: Liste des IDs des destinataires
            distribution_method: Méthode de distribution ('email', 'api', etc.)
            
        Returns:
            True si la distribution a réussi
        """
        pass
    
    @abstractmethod
    def schedule_distribution(self, report_id: int, schedule_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Planifie la distribution d'un rapport.
        
        Args:
            report_id: ID du rapport à distribuer
            schedule_config: Configuration de la planification
            
        Returns:
            La planification créée
        """
        pass
    
    @abstractmethod
    def cancel_distribution(self, schedule_id: int) -> bool:
        """
        Annule une distribution planifiée.
        
        Args:
            schedule_id: ID de la planification à annuler
            
        Returns:
            True si l'annulation a réussi
        """
        pass

class ReportExportService(ABC):
    """
    Interface pour le service d'exportation de rapports.
    
    Responsable de l'exportation des rapports dans différents formats.
    """
    
    @abstractmethod
    def export_report(self, report_id: int, format: ReportFormat, output_path: str = None) -> bool:
        """
        Exporte un rapport dans le format spécifié.
        
        Args:
            report_id: ID du rapport à exporter
            format: Format d'exportation (PDF, XLSX, etc.)
            output_path: Chemin de sortie (optionnel)
            
        Returns:
            bool: True si l'exportation a réussi
        """
        pass

class NotificationService(ABC):
    """
    Interface pour le service de notification.
    
    Responsable de l'envoi de notifications concernant les rapports.
    """
    
    @abstractmethod
    def notify_report_completion(self, report_id: int, recipients: List[int]) -> bool:
        """
        Notifie les destinataires de la complétion d'un rapport.
        
        Args:
            report_id: ID du rapport
            recipients: Liste des IDs des destinataires
            
        Returns:
            bool: True si la notification a réussi
        """
        pass 