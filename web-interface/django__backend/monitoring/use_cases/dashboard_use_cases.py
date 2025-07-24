"""
Cas d'utilisation pour la gestion des tableaux de bord.
"""

from typing import List, Dict, Any, Optional

class DashboardUseCase:
    """Cas d'utilisation pour la gestion des tableaux de bord."""
    
    def __init__(self, dashboard_repository):
        self.dashboard_repository = dashboard_repository
    
    def list_dashboards(self, user_id=None, include_public=True):
        """
        Liste les tableaux de bord accessibles par un utilisateur.
        
        Args:
            user_id: ID de l'utilisateur (optionnel)
            include_public: Si True, inclut les tableaux de bord publics
            
        Returns:
            Liste des tableaux de bord
        """
        if user_id is not None:
            # Récupérer les tableaux de bord de l'utilisateur
            user_dashboards = self.dashboard_repository.get_by_owner(user_id)
            
            if include_public:
                # Récupérer les tableaux de bord publics
                public_dashboards = self.dashboard_repository.get_public_dashboards()
                
                # Fusionner les deux listes en évitant les doublons
                dashboard_ids = set(d.id for d in user_dashboards)
                for dashboard in public_dashboards:
                    if dashboard.id not in dashboard_ids:
                        user_dashboards.append(dashboard)
                
                return user_dashboards
            else:
                return user_dashboards
        else:
            if include_public:
                return self.dashboard_repository.get_public_dashboards()
            else:
                return []
    
    def get_dashboard(self, dashboard_id=None, uid=None):
        """
        Récupère un tableau de bord par son ID ou son UID.
        
        Args:
            dashboard_id: ID du tableau de bord (optionnel)
            uid: UID du tableau de bord (optionnel)
            
        Returns:
            Tableau de bord
            
        Raises:
            ValueError: Si le tableau de bord n'existe pas
        """
        if dashboard_id is not None:
            dashboard = self.dashboard_repository.get_by_id(dashboard_id)
        elif uid is not None:
            dashboard = self.dashboard_repository.get_by_uid(uid)
        else:
            raise ValueError("Either dashboard_id or uid must be provided")
        
        if dashboard is None:
            raise ValueError(f"Dashboard not found")
        
        return dashboard
    
    def get_default_dashboard(self, user_id):
        """
        Récupère le tableau de bord par défaut d'un utilisateur.
        
        Args:
            user_id: ID de l'utilisateur
            
        Returns:
            Tableau de bord par défaut ou None si aucun tableau de bord par défaut n'existe
        """
        return self.dashboard_repository.get_default_dashboard(user_id)
    
    def create_dashboard(self, title, owner_id, description=None, is_public=False, is_default=False, layout_config=None):
        """
        Crée un nouveau tableau de bord.
        
        Args:
            title: Titre du tableau de bord
            owner_id: ID du propriétaire
            description: Description du tableau de bord (optionnel)
            is_public: Si le tableau de bord est public
            is_default: Si le tableau de bord est le tableau de bord par défaut
            layout_config: Configuration de mise en page (optionnel)
            
        Returns:
            Tableau de bord créé
        """
        # Si le tableau de bord est défini comme défaut, désactiver le tableau de bord par défaut existant
        if is_default:
            current_default = self.dashboard_repository.get_default_dashboard(owner_id)
            if current_default is not None:
                self.dashboard_repository.update(current_default.id, is_default=False)
        
        return self.dashboard_repository.create_dashboard(
            title=title,
            description=description,
            owner_id=owner_id,
            is_public=is_public,
            is_default=is_default,
            layout_config=layout_config
        )
    
    def update_dashboard(self, dashboard_id, **kwargs):
        """
        Met à jour un tableau de bord.
        
        Args:
            dashboard_id: ID du tableau de bord
            **kwargs: Champs à mettre à jour
            
        Returns:
            Tableau de bord mis à jour
            
        Raises:
            ValueError: Si le tableau de bord n'existe pas
        """
        dashboard = self.get_dashboard(dashboard_id=dashboard_id)
        
        # Si le tableau de bord est défini comme défaut, désactiver le tableau de bord par défaut existant
        if kwargs.get('is_default', False) and not dashboard.is_default:
            current_default = self.dashboard_repository.get_default_dashboard(dashboard.owner_id)
            if current_default is not None and current_default.id != dashboard_id:
                self.dashboard_repository.update(current_default.id, is_default=False)
        
        return self.dashboard_repository.update(dashboard_id, **kwargs)
    
    def delete_dashboard(self, dashboard_id):
        """
        Supprime un tableau de bord.
        
        Args:
            dashboard_id: ID du tableau de bord
            
        Returns:
            True si la suppression a réussi, False sinon
            
        Raises:
            ValueError: Si le tableau de bord n'existe pas
        """
        dashboard = self.get_dashboard(dashboard_id=dashboard_id)
        return self.dashboard_repository.delete(dashboard_id)
    
    def add_widget(self, dashboard_id, title, widget_type, position, size, data_source=None, config=None):
        """
        Ajoute un widget à un tableau de bord.
        
        Args:
            dashboard_id: ID du tableau de bord
            title: Titre du widget
            widget_type: Type de widget
            position: Position du widget
            size: Taille du widget
            data_source: Source de données du widget (optionnel)
            config: Configuration du widget (optionnel)
            
        Returns:
            Widget créé
            
        Raises:
            ValueError: Si le tableau de bord n'existe pas
        """
        dashboard = self.get_dashboard(dashboard_id=dashboard_id)
        
        return self.dashboard_repository.add_widget(
            dashboard_id=dashboard_id,
            title=title,
            widget_type=widget_type,
            position=position,
            size=size,
            data_source=data_source,
            config=config
        )
    
    def update_widget(self, widget_id, **kwargs):
        """
        Met à jour un widget.
        
        Args:
            widget_id: ID du widget
            **kwargs: Champs à mettre à jour
            
        Returns:
            Widget mis à jour
            
        Raises:
            ValueError: Si le widget n'existe pas
        """
        return self.dashboard_repository.update_widget(widget_id, **kwargs)
    
    def remove_widget(self, widget_id):
        """
        Supprime un widget d'un tableau de bord.
        
        Args:
            widget_id: ID du widget
            
        Returns:
            True si la suppression a réussi, False sinon
            
        Raises:
            ValueError: Si le widget n'existe pas
        """
        return self.dashboard_repository.remove_widget(widget_id) 