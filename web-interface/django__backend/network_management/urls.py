"""
Module contenant les URLs pour le module Network Management.
"""

from django.urls import path, include

urlpatterns = [
    path('api/', include('network_management.api.urls')),
]
