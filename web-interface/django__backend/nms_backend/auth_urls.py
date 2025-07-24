"""
URLs pour l'authentification transparente du Network Management System.

Ce module configure les endpoints pour l'authentification transparente
permettant au frontend React d'accéder aux APIs Django avec des super_utilisateurs.
"""

from django.urls import path
from . import transparent_auth_views

urlpatterns = [
    # === ENDPOINTS D'AUTHENTIFICATION TRANSPARENTE ===
    
    # Connexion transparente avec création automatique de super_utilisateur
    path('login/', transparent_auth_views.transparent_login, name='transparent-login'),
    
    # Inscription transparente avec création automatique de super_utilisateur
    path('register/', transparent_auth_views.transparent_register, name='transparent-register'),
    
    # Déconnexion
    path('logout/', transparent_auth_views.transparent_logout, name='transparent-logout'),
    
    # Informations utilisateur connecté
    path('user/', transparent_auth_views.user_info, name='user-info'),
    
    # Endpoint alternatif pour la connexion transparente
    path('transparent-login/', transparent_auth_views.transparent_login, name='transparent-login-alt'),
]