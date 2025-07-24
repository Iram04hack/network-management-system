"""
Mixins pour les vues de QoS
"""
from rest_framework import permissions
from django.conf import settings
from ..di_container import resolve

class QoSPermissionMixin:
    """Mixin pour les autorisations QoS"""
    permission_classes = [permissions.IsAuthenticated]

class AdminRequiredMixin:
    """
    Mixin qui requiert des privilèges d'administrateur.
    
    Ce mixin peut être utilisé pour restreindre l'accès aux opérations
    sensibles aux seuls utilisateurs ayant des privilèges d'administrateur.
    """
    
    def check_permissions(self, request):
        """
        Vérifie que l'utilisateur a les permissions d'administration.
        
        Args:
            request: Requête HTTP
            
        Raises:
            PermissionDenied: Si l'utilisateur n'a pas les permissions
        """
        super().check_permissions(request)
        
        # Vérifier si l'utilisateur est admin ou a des permissions spéciales
        if not (request.user.is_superuser or request.user.is_staff):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Permissions d'administrateur requises")
    
    def has_admin_permission(self, request):
        """
        Vérifie si l'utilisateur a les permissions d'admin.
        
        Args:
            request: Requête HTTP
            
        Returns:
            bool: True si l'utilisateur a les permissions
        """
        return request.user.is_superuser or request.user.is_staff

class DIViewMixin:
    """
    Mixin pour l'injection de dépendances dans les vues.
    
    Ce mixin permet d'injecter facilement des dépendances dans les vues
    en utilisant le conteneur d'injection de dépendances.
    """
    
    _dependencies = {}
    
    def __init__(self, **kwargs):
        """
        Initialise la vue en résolvant les dépendances déclarées.
        
        Args:
            **kwargs: Arguments du constructeur parent
        """
        # Résoudre les dépendances déclarées dans _dependencies
        for key, dependency in self._dependencies.items():
            setattr(self, key, resolve(dependency))
        
        # Appeler le constructeur parent
        super().__init__(**kwargs)
    
    @classmethod
    def with_dependencies(cls, **dependencies):
        """
        Crée une sous-classe avec les dépendances spécifiées.
        
        Args:
            **dependencies: Dictionnaire des dépendances à injecter
            
        Returns:
            Sous-classe avec les dépendances spécifiées
        """
        return type(
            f"{cls.__name__}WithDependencies",
            (cls,),
            {"_dependencies": dependencies}
        ) 