"""
Vues pour le module Dashboard.

Ce fichier contient les vues Django qui rendent les templates HTML
pour le module Dashboard.
"""

import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings

from .di_container import container

logger = logging.getLogger(__name__)


@login_required
def dashboard_view(request):
    """
    Vue principale du tableau de bord.
    
    Args:
        request: Requête HTTP
        
    Returns:
        Réponse HTTP avec le template du tableau de bord
    """
    try:
        # Récupérer le service depuis le conteneur
        dashboard_service = container.get_service('dashboard_service')
        
        # Récupérer la configuration de l'utilisateur
        user_id = request.user.id
        config = dashboard_service.get_user_dashboard_config(user_id)
        
        # Contexte pour le template
        context = {
            'title': 'Tableau de bord',
            'user_config': config,
            'refresh_interval': config.get('refresh_interval', 60) if isinstance(config, dict) else 60,
            'theme': config.get('theme', 'light') if isinstance(config, dict) else 'light',
            'debug': settings.DEBUG
        }
        
        return render(request, 'dashboard/index.html', context)
    except Exception as e:
        logger.error(f"Erreur lors du rendu du tableau de bord: {e}")
        return render(request, 'dashboard/error.html', {
            'title': 'Erreur',
            'error_message': str(e)
        })


@login_required
def network_overview(request):
    """
    Vue d'aperçu réseau.
    
    Args:
        request: Requête HTTP
        
    Returns:
        Réponse HTTP avec le template d'aperçu réseau
    """
    try:
        # Contexte pour le template
        context = {
            'title': 'Aperçu réseau',
            'debug': settings.DEBUG
        }
        
        return render(request, 'dashboard/network_overview.html', context)
    except Exception as e:
        logger.error(f"Erreur lors du rendu de l'aperçu réseau: {e}")
        return render(request, 'dashboard/error.html', {
            'title': 'Erreur',
            'error_message': str(e)
        })


@login_required
def topology_view(request):
    """
    Vue de visualisation de topologie.
    
    Args:
        request: Requête HTTP
        
    Returns:
        Réponse HTTP avec le template de visualisation de topologie
    """
    try:
        # Récupérer l'ID de la topologie depuis les paramètres de requête
        topology_id = request.GET.get('topology_id')
        
        # Contexte pour le template
        context = {
            'title': 'Visualisation de topologie',
            'topology_id': topology_id,
            'debug': settings.DEBUG
        }
        
        return render(request, 'dashboard/topology.html', context)
    except Exception as e:
        logger.error(f"Erreur lors du rendu de la visualisation de topologie: {e}")
        return render(request, 'dashboard/error.html', {
            'title': 'Erreur',
            'error_message': str(e)
        })


@login_required
def dashboard_settings(request):
    """
    Vue des paramètres du tableau de bord.
    
    Args:
        request: Requête HTTP
        
    Returns:
        Réponse HTTP avec le template des paramètres
    """
    try:
        # Récupérer le service depuis le conteneur
        dashboard_service = container.get_service('dashboard_service')
        
        # Récupérer la configuration de l'utilisateur
        user_id = request.user.id
        config = dashboard_service.get_user_dashboard_config(user_id)
        
        # Traitement du formulaire de mise à jour
        if request.method == 'POST':
            # Récupérer les données du formulaire
            theme = request.POST.get('theme', 'light')
            layout = request.POST.get('layout', 'grid')
            refresh_interval = int(request.POST.get('refresh_interval', 60))
            
            # Mettre à jour la configuration
            new_config = {
                'theme': theme,
                'layout': layout,
                'refresh_interval': refresh_interval
            }
            
            # Si des widgets sont fournis, les ajouter à la configuration
            if 'widgets' in request.POST:
                new_config['widgets'] = request.POST.get('widgets')
            
            # Enregistrer la configuration
            success = dashboard_service.save_user_dashboard_config(user_id, new_config)
            
            if success:
                return redirect('dashboard:index')
            else:
                context = {
                    'title': 'Paramètres du tableau de bord',
                    'user_config': config,
                    'error_message': 'Erreur lors de l\'enregistrement des paramètres',
                    'debug': settings.DEBUG
                }
                return render(request, 'dashboard/settings.html', context)
        
        # Contexte pour le template
        context = {
            'title': 'Paramètres du tableau de bord',
            'user_config': config,
            'debug': settings.DEBUG
        }
        
        return render(request, 'dashboard/settings.html', context)
    except Exception as e:
        logger.error(f"Erreur lors du rendu des paramètres du tableau de bord: {e}")
        return render(request, 'dashboard/error.html', {
            'title': 'Erreur',
            'error_message': str(e)
        }) 