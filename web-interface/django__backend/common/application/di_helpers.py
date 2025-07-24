"""
Utilitaires d'injection de dépendances pour faciliter l'architecture hexagonale.

Ce module fournit des classes et fonctions pour faciliter l'utilisation
du conteneur d'injection de dépendances de manière cohérente dans tous les modules,
permettant ainsi un découplage fort entre les composants du système.

Inspiré par les principes SOLID, en particulier le principe d'inversion de dépendance,
ces utilitaires permettent aux classes de dépendre d'abstractions plutôt que 
d'implémentations concrètes.

Principales fonctionnalités:
- Mixin DI pour les vues Django et DRF
- Décorateur @inject pour l'injection automatique
- Fonctions utilitaires pour la résolution manuelle de dépendances
"""
from typing import Any, Dict, Type, TypeVar, Optional, cast, Callable, List, Union
import inspect
import functools

# Mock temporaire du conteneur DI pour les tests
class MockDIContainer:
    """Conteneur DI temporaire pour les tests."""
    
    def can_resolve(self, interface: Type) -> bool:
        """Vérifie si une interface peut être résolue."""
        return True
        
    def resolve(self, interface: Type) -> Any:
        """Résout une interface en une implémentation."""
        return None

# Fonction temporaire pour obtenir le conteneur DI
def get_container():
    """Retourne le conteneur DI global."""
    return MockDIContainer()

# Création d'une variable de type générique pour les types d'interface
T = TypeVar('T')
InterfaceType = Type[T]


class DIViewMixin:
    """
    Mixin pour l'injection de dépendances dans les vues Django et DRF.
    
    Cette classe fournit des méthodes utilitaires pour résoudre des dépendances
    à partir du conteneur global dans les vues.
    
    Exemple:
        class MyView(DIViewMixin, View):
            def get(self, request):
                logger = self.resolve(ILogger)
                service = self.resolve(IUserService)
                # ...
    """
    
    def resolve(self, interface: InterfaceType[T]) -> T:
        """
        Résout une interface en une implémentation concrète.
        
        Args:
            interface: L'interface à résoudre
            
        Returns:
            L'implémentation concrète
            
        Raises:
            ValueError: Si l'interface ne peut pas être résolue
        """
        container = get_container()
        
        if not container.can_resolve(interface):
            raise ValueError(f"Impossible de résoudre l'interface {interface.__name__}")
            
        return cast(T, container.resolve(interface))
    
    def resolve_all(self, *interfaces: InterfaceType) -> Dict[InterfaceType, Any]:
        """
        Résout plusieurs interfaces en un dictionnaire d'implémentations.
        
        Args:
            *interfaces: Les interfaces à résoudre
            
        Returns:
            Un dictionnaire avec les interfaces comme clés et les implémentations comme valeurs
        """
        return {interface: self.resolve(interface) for interface in interfaces}
    
    def resolve_multiple(self, *interfaces: InterfaceType) -> List[Any]:
        """
        Résout plusieurs interfaces et retourne une liste d'implémentations.
        
        Cette méthode est utile pour l'unpacking:
        service1, service2 = self.resolve_multiple(IService1, IService2)
        
        Args:
            *interfaces: Les interfaces à résoudre
            
        Returns:
            Une liste d'implémentations dans l'ordre des interfaces
        """
        return [self.resolve(interface) for interface in interfaces]


def _get_attribute_name(cls: Type) -> str:
    """
    Détermine le nom d'attribut à utiliser pour une classe injectée.
    
    Convertit le nom de la classe en snake_case et supprime le préfixe 'I'
    pour les interfaces.
    
    Args:
        cls: La classe pour laquelle déterminer le nom d'attribut
        
    Returns:
        Le nom d'attribut en snake_case
    """
    name = cls.__name__
    
    # Supprimer le préfixe 'I' pour les interfaces
    if name.startswith('I') and len(name) > 1 and name[1].isupper():
        name = name[1:]
    
    # Convertir CamelCase en snake_case
    result = [name[0].lower()]
    for char in name[1:]:
        if char.isupper():
            result.append('_')
            result.append(char.lower())
        else:
            result.append(char)
    
    return ''.join(result)


def _create_lazy_property(interface: Type) -> property:
    """
    Crée une propriété qui résout l'interface à la demande.
    
    Args:
        interface: L'interface à résoudre
        
    Returns:
        Une propriété qui résout l'interface lors du premier accès
    """
    attr_name = f"_{_get_attribute_name(interface)}"
    
    def getter(self):
        if not hasattr(self, attr_name):
            container = get_container()
            if not container.can_resolve(interface):
                raise ValueError(f"Impossible de résoudre l'interface {interface.__name__}")
            setattr(self, attr_name, container.resolve(interface))
        return getattr(self, attr_name)
    
    return property(getter)


def inject(*interfaces: Type, lazy: bool = False) -> Callable:
    """
    Décorateur pour injecter des dépendances dans une classe.
    
    Ce décorateur modifie l'initialisation d'une classe pour injecter
    automatiquement les dépendances spécifiées.
    
    Args:
        *interfaces: Les interfaces à injecter
        lazy: Si True, les dépendances sont résolues à la demande (lazy loading)
        
    Returns:
        Le décorateur de classe
        
    Exemple:
        @inject(ILogger, IUserService)
        class MyService:
            def __init__(self, name):
                self.name = name
                # self.logger et self.user_service sont injectés automatiquement
    """
    def decorator(cls: Type) -> Type:
        original_init = cls.__init__
        
        @functools.wraps(original_init)
        def new_init(self, *args, **kwargs):
            # Appeler l'initialisation originale
            original_init(self, *args, **kwargs)
            
            # Injecter les dépendances
            if lazy:
                # Lazy loading: créer des propriétés
                for interface in interfaces:
                    attr_name = _get_attribute_name(interface)
                    setattr(cls, attr_name, _create_lazy_property(interface))
            else:
                # Eager loading: résoudre immédiatement
                container = get_container()
                for interface in interfaces:
                    attr_name = _get_attribute_name(interface)
                    if not container.can_resolve(interface):
                        raise ValueError(f"Impossible de résoudre l'interface {interface.__name__}")
                    setattr(self, attr_name, container.resolve(interface))
        
        cls.__init__ = new_init
        return cls
    
    return decorator


def resolve(interface: InterfaceType[T]) -> T:
    """
    Fonction utilitaire pour résoudre une interface en dehors d'une classe.
    
    Cette fonction est utile dans les fonctions ou les modules qui ne sont pas
    des classes mais qui ont besoin d'accéder au conteneur DI.
    
    Args:
        interface: L'interface à résoudre
        
    Returns:
        L'implémentation concrète
        
    Raises:
        ValueError: Si l'interface ne peut pas être résolue
    """
    container = get_container()
    
    if not container.can_resolve(interface):
        raise ValueError(f"Impossible de résoudre l'interface {interface.__name__}")
        
    return cast(T, container.resolve(interface)) 