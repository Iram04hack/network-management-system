"""
Configuration pytest pour les tests du module.
"""

import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock

User = get_user_model()

@pytest.fixture
def test_user():
    """Utilisateur de test standard."""
    return User.objects.create_user(
        username="testuser",
        email="test@example.com", 
        password="password123"
    )

@pytest.fixture
def admin_user():
    """Utilisateur administrateur."""
    return User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="admin123"
    )

@pytest.fixture
def authenticated_client(client, test_user):
    """Client authentifié."""
    client.force_login(test_user)
    return client
