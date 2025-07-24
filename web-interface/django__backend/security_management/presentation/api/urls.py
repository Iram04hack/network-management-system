"""
URLs simplifiées de présentation pour security_management.
Redirige vers la structure API principale.
"""

from django.urls import path, include

# Redirection vers la structure API principale
urlpatterns = [
    path('', include('security_management.api.urls')),
]