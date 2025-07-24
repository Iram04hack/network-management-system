"""
Implémentation concrète du repository pour les tableaux de bord.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid

from django.db.models import Q

from ...domain.interfaces.repositories import DashboardRepository as IDashboardRepository
from ...models import Dashboard, DashboardWidget
from .base_repository import BaseRepository

# Configuration du logger
logger = logging.getLogger(__name__)


class DashboardRepository(BaseRepository[Dashboard], IDashboardRepository):
    """
    Repository pour les tableaux de bord.
    """
    
    def __init__(self):
        """
        Initialise le repository avec le modèle Dashboard.
        """
        super().__init__(Dashboard)
    
    def create_dashboard(self, title: str, description: str = None, 
                        owner_id: int = None, is_public: bool = False,
                        is_default: bool = False,
                        layout_config: Dict[str, Any] = None) -> Dashboard:
        """
        Crée un nouveau tableau de bord.
        
        Args:
            title: Titre du tableau de bord
            description: Description du tableau de bord (optionnel)
            owner_id: ID du propriétaire (optionnel)
            is_public: Si le tableau de bord est public
            is_default: Si le tableau de bord est le tableau de bord par défaut
            layout_config: Configuration de mise en page (optionnel)
            
        Returns:
            Le tableau de bord créé
        """
        try:
            # Générer un UID unique
            uid = str(uuid.uuid4())
            
            dashboard = Dashboard(
                title=title,
                description=description,
                uid=uid,
                owner_id=owner_id,
                is_public=is_public,
                is_default=is_default,
                layout_config=layout_config or {},
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            # Si ce tableau de bord est défini comme par défaut, désactiver les autres tableaux de bord par défaut
            if is_default and owner_id:
                Dashboard.objects.filter(owner_id=owner_id, is_default=True).update(is_default=False)
            
            dashboard.save()
            logger.info(f"Tableau de bord créé: {dashboard.id} - {title}")
            return dashboard
        except Exception as e:
            logger.error(f"Erreur lors de la création d'un tableau de bord: {e}")
            raise
    
    def get_by_uid(self, uid: str) -> Optional[Dashboard]:
        """
        Récupère un tableau de bord par son UID.
        
        Args:
            uid: UID du tableau de bord
            
        Returns:
            Le tableau de bord ou None s'il n'existe pas
        """
        try:
            return Dashboard.objects.get(uid=uid)
        except Dashboard.DoesNotExist:
            logger.warning(f"Tableau de bord avec UID {uid} n'existe pas")
            return None
    
    def get_by_owner(self, owner_id: int) -> List[Dashboard]:
        """
        Récupère les tableaux de bord d'un propriétaire.
        
        Args:
            owner_id: ID du propriétaire
            
        Returns:
            Liste des tableaux de bord
        """
        return self.filter(owner_id=owner_id)
    
    def get_public_dashboards(self) -> List[Dashboard]:
        """
        Récupère les tableaux de bord publics.
        
        Returns:
            Liste des tableaux de bord publics
        """
        return self.filter(is_public=True)
    
    def get_default_dashboard(self, owner_id: Optional[int] = None) -> Optional[Dashboard]:
        """
        Récupère le tableau de bord par défaut.
        
        Args:
            owner_id: ID du propriétaire (optionnel)
            
        Returns:
            Le tableau de bord par défaut ou None s'il n'existe pas
        """
        if owner_id:
            try:
                return Dashboard.objects.filter(owner_id=owner_id, is_default=True).first()
            except Dashboard.DoesNotExist:
                pass
                
        # Si aucun tableau de bord par défaut n'est trouvé pour le propriétaire,
        # essayer de récupérer un tableau de bord public par défaut
        try:
            return Dashboard.objects.filter(is_public=True, is_default=True).first()
        except Dashboard.DoesNotExist:
            return None
    
    def add_widget(self, dashboard_id: int, title: str, widget_type: str,
                  position: Dict[str, int] = None, size: Dict[str, int] = None,
                  data_source: Dict[str, Any] = None,
                  config: Dict[str, Any] = None) -> Optional[DashboardWidget]:
        """
        Ajoute un widget à un tableau de bord.
        
        Args:
            dashboard_id: ID du tableau de bord
            title: Titre du widget
            widget_type: Type de widget ('metric_value', 'chart', 'alert_list', etc.)
            position: Position du widget (optionnel)
            size: Taille du widget (optionnel)
            data_source: Source de données du widget (optionnel)
            config: Configuration du widget (optionnel)
            
        Returns:
            Le widget créé ou None si le tableau de bord n'existe pas
        """
        dashboard = self.get_by_id(dashboard_id)
        if not dashboard:
            return None
        
        try:
            widget = DashboardWidget(
                dashboard=dashboard,
                title=title,
                widget_type=widget_type,
                position=position or {},
                size=size or {},
                data_source=data_source or {},
                config=config or {}
            )
            
            widget.save()
            
            # Mettre à jour la date de modification du tableau de bord
            dashboard.updated_at = datetime.now(timezone.utc)
            dashboard.save()
            
            logger.info(f"Widget ajouté au tableau de bord {dashboard_id}: {widget.id} - {title}")
            return widget
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout d'un widget au tableau de bord {dashboard_id}: {e}")
            raise
    
    def remove_widget(self, widget_id: int) -> bool:
        """
        Supprime un widget d'un tableau de bord.
        
        Args:
            widget_id: ID du widget
            
        Returns:
            True si la suppression a réussi, False sinon
        """
        try:
            widget = DashboardWidget.objects.get(id=widget_id)
            dashboard_id = widget.dashboard_id
            
            # Supprimer le widget
            widget.delete()
            
            # Mettre à jour la date de modification du tableau de bord
            dashboard = self.get_by_id(dashboard_id)
            if dashboard:
                dashboard.updated_at = datetime.now(timezone.utc)
                dashboard.save()
            
            logger.info(f"Widget {widget_id} supprimé du tableau de bord {dashboard_id}")
            return True
        except DashboardWidget.DoesNotExist:
            logger.warning(f"Widget {widget_id} n'existe pas")
            return False
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du widget {widget_id}: {e}")
            return False
    
    def update_widget(self, widget_id: int, 
                     title: Optional[str] = None,
                     position: Optional[Dict[str, int]] = None,
                     size: Optional[Dict[str, int]] = None,
                     data_source: Optional[Dict[str, Any]] = None,
                     config: Optional[Dict[str, Any]] = None) -> Optional[DashboardWidget]:
        """
        Met à jour un widget.
        
        Args:
            widget_id: ID du widget
            title: Nouveau titre (optionnel)
            position: Nouvelle position (optionnel)
            size: Nouvelle taille (optionnel)
            data_source: Nouvelle source de données (optionnel)
            config: Nouvelle configuration (optionnel)
            
        Returns:
            Le widget mis à jour ou None s'il n'existe pas
        """
        try:
            widget = DashboardWidget.objects.get(id=widget_id)
            
            if title:
                widget.title = title
                
            if position:
                widget.position = position
                
            if size:
                widget.size = size
                
            if data_source:
                # Fusionner avec la source de données existante
                if widget.data_source:
                    widget.data_source.update(data_source)
                else:
                    widget.data_source = data_source
                
            if config:
                # Fusionner avec la configuration existante
                if widget.config:
                    widget.config.update(config)
                else:
                    widget.config = config
            
            widget.save()
            
            # Mettre à jour la date de modification du tableau de bord
            dashboard = self.get_by_id(widget.dashboard_id)
            if dashboard:
                dashboard.updated_at = datetime.now(timezone.utc)
                dashboard.save()
            
            logger.info(f"Widget {widget_id} mis à jour")
            return widget
        except DashboardWidget.DoesNotExist:
            logger.warning(f"Widget {widget_id} n'existe pas")
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du widget {widget_id}: {e}")
            raise
    
    def get_widgets(self, dashboard_id: int) -> List[DashboardWidget]:
        """
        Récupère les widgets d'un tableau de bord.
        
        Args:
            dashboard_id: ID du tableau de bord
            
        Returns:
            Liste des widgets
        """
        return list(DashboardWidget.objects.filter(dashboard_id=dashboard_id))
    
    def get_widget_by_id(self, widget_id: int) -> Optional[DashboardWidget]:
        """
        Récupère un widget par son ID.
        
        Args:
            widget_id: ID du widget
            
        Returns:
            Le widget ou None s'il n'existe pas
        """
        try:
            return DashboardWidget.objects.get(id=widget_id)
        except DashboardWidget.DoesNotExist:
            logger.warning(f"Widget {widget_id} n'existe pas")
            return None 
    
    def list_by_user(self, user_id: int, include_public: bool = True) -> List[Dashboard]:
        """
        Liste les tableaux de bord accessibles par un utilisateur.
        Cette méthode est requise par l'interface abstraite.
        
        Args:
            user_id: ID de l'utilisateur
            include_public: Inclure les tableaux publics
            
        Returns:
            Liste des tableaux de bord
        """
        # Récupérer les tableaux de bord de l'utilisateur
        user_dashboards = self.get_by_owner(user_id)
        
        if include_public:
            # Récupérer les tableaux de bord publics
            public_dashboards = self.get_public_dashboards()
            
            # Fusionner les deux listes en évitant les doublons
            dashboard_ids = set(d.id for d in user_dashboards)
            for dashboard in public_dashboards:
                if dashboard.id not in dashboard_ids:
                    user_dashboards.append(dashboard)
        
        return user_dashboards
    
    def delete_widget(self, widget_id: int) -> bool:
        """
        Supprime un widget d'un tableau de bord.
        Cette méthode est requise par l'interface abstraite.
        
        Args:
            widget_id: ID du widget
            
        Returns:
            True si la suppression a réussi, False sinon
        """
        return self.remove_widget(widget_id) 