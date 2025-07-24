"""
Configuration pytest pour network_management.
"""

import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.fixture  
def test_user():
    return User.objects.create_user(
        username="netuser",
        email="net@example.com",
        password="password123"
    )
