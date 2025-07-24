"""
Administration Django pour le module plugins.

Ce module définit les interfaces d'administration pour gérer les plugins
du système.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponseRedirect
from .infrastructure.registry import PluginRegistry


class PluginAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour visualiser les plugins enregistrés.
    
    Bien que les plugins ne soient pas des modèles Django à proprement parler,
    cette classe offre une interface pour les visualiser dans l'admin Django.
    """
    model = None
    change_list_template = 'admin/plugins/plugin_change_list.html'
    
    def get_queryset(self, request):
        """Remplacé pour renvoyer les plugins au lieu des objets de la base de données."""
        return []  # Aucun modèle réel
    
    def changelist_view(self, request, extra_context=None):
        """Vue personnalisée pour afficher la liste des plugins enregistrés."""
        # Collecter les informations sur tous les types de plugins
        plugin_types = ['alert_handlers', 'dashboard_widgets', 'report_generators']
        all_plugins = []
        
        for plugin_type in plugin_types:
            plugin_classes = PluginRegistry.get_plugins(plugin_type)
            for plugin_class in plugin_classes:
                try:
                    plugin_instance = plugin_class()
                    metadata = {}
                    
                    if hasattr(plugin_instance, 'get_metadata'):
                        metadata = plugin_instance.get_metadata()
                    else:
                        metadata = {
                            'id': plugin_class.__name__,
                            'name': getattr(plugin_instance, 'name', plugin_class.__name__),
                            'version': 'N/A',
                            'description': getattr(plugin_instance, '__doc__', 'Pas de description'),
                            'author': 'N/A'
                        }
                    
                    metadata['type'] = plugin_type
                    metadata['class_name'] = plugin_class.__name__
                    metadata['module'] = plugin_class.__module__
                    
                    # Vérifier si le plugin est correctement initialisé
                    if hasattr(plugin_instance, 'initialize'):
                        metadata['initialized'] = plugin_instance.initialize()
                    else:
                        metadata['initialized'] = True
                    
                    all_plugins.append(metadata)
                except Exception as e:
                    # En cas d'erreur lors de l'initialisation
                    all_plugins.append({
                        'id': plugin_class.__name__,
                        'name': plugin_class.__name__,
                        'type': plugin_type,
                        'class_name': plugin_class.__name__,
                        'module': plugin_class.__module__,
                        'initialized': False,
                        'error': str(e)
                    })
        
        # Préparer le contexte pour le template
        context = {
            'title': 'Plugins enregistrés',
            'plugins': all_plugins,
            'plugin_types': plugin_types,
        }
        
        if extra_context:
            context.update(extra_context)
        
        return super().changelist_view(request, context)


# Note: PluginAdmin est une vue personnalisée pour afficher les plugins enregistrés
# Elle ne gère pas un modèle Django spécifique, donc pas d'enregistrement admin.site.register()