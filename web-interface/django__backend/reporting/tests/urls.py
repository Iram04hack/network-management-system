"""
Configuration des URLs pour les tests du module reporting.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/reporting/', include('reporting.urls')),
] 