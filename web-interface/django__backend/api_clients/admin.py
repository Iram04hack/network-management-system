"""
Configuration de l'interface d'administration pour l'application api_clients.

Ce module contient la configuration de l'interface d'administration pour l'application api_clients.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.template.defaultfilters import truncatechars

# Note: Nous n'avons pas de modèles à enregistrer pour l'instant,
# mais nous pourrions ajouter des modèles pour stocker les configurations des clients API,
# les métriques, etc. dans le futur.
