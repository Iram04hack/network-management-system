"""
Configuration des URLs pour l'API de l'assistant IA.

Ce module contient les définitions des URLs pour l'API de l'assistant IA.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Import des vues simplifiées pour corriger les erreurs d'intégration
from ai_assistant.api.views.simple_views import (
    SimpleConversationViewSet,
    SimpleMessageViewSet,
    SimpleDocumentViewSet,
    SimpleSearchView,
    SimpleCommandView,
    SimpleNetworkAnalysisView,
)

# Import des vues d'intégration GNS3
from ai_assistant.views.gns3_integration_views import (
    get_network_context,
    analyze_device,
    analyze_project,
    get_integration_status,
    get_available_devices,
    get_available_projects
)

# Créer le routeur principal avec les vues simplifiées
router = DefaultRouter()
router.register(r'conversations', SimpleConversationViewSet, basename='conversation')
router.register(r'messages', SimpleMessageViewSet, basename='message')
router.register(r'documents', SimpleDocumentViewSet, basename='document')

# Définir les URLs
urlpatterns = [
    # Inclure les URLs du routeur principal
    path('', include(router.urls)),

    # URLs manuelles pour les messages imbriqués (utilise l'action messages du ConversationViewSet)
    path('conversations/<int:conversation_pk>/messages/',
         SimpleConversationViewSet.as_view({'get': 'messages', 'post': 'messages'}),
         name='conversation-messages'),

    # Ajouter les vues supplémentaires simplifiées
    path('search/', SimpleSearchView.as_view(), name='search'),
    path('commands/', SimpleCommandView.as_view(), name='command'),
    path('network-analysis/', SimpleNetworkAnalysisView.as_view(), name='network-analysis'),

    # URL pour la recherche de documents
    path('documents/search/', SimpleDocumentViewSet.as_view({'get': 'search'}), name='document-search'),
    
    # ================== APIs INTÉGRATION GNS3 ==================
    
    # Contexte réseau GNS3
    path('gns3/network-context/', get_network_context, name='gns3-network-context'),
    
    # Analyse de dispositifs et projets
    path('gns3/analyze-device/', analyze_device, name='gns3-analyze-device'),
    path('gns3/analyze-project/', analyze_project, name='gns3-analyze-project'),
    
    # Statut et ressources disponibles
    path('gns3/integration-status/', get_integration_status, name='gns3-integration-status'),
    path('gns3/available-devices/', get_available_devices, name='gns3-available-devices'),
    path('gns3/available-projects/', get_available_projects, name='gns3-available-projects'),
]