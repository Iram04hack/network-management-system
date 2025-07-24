"""
Package de vues pour l'API de l'assistant IA.

Ce package contient les vues qui exposent les fonctionnalités
de l'assistant IA via une API REST.
"""

from ai_assistant.api.views.conversation_views import (
    ConversationViewSet,
    MessageViewSet,
)
from ai_assistant.api.views.document_views import (
    DocumentViewSet,
)
from ai_assistant.api.views.search_views import (
    SearchView,
)
from ai_assistant.api.views.command_views import (
    CommandView,
)
from ai_assistant.api.views.network_analysis_views import (
    NetworkAnalysisView,
)

__all__ = [
    'ConversationViewSet',
    'MessageViewSet',
    'DocumentViewSet',
    'SearchView',
    'CommandView',
    'NetworkAnalysisView',
] 