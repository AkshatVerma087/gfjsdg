"""Pytest fixtures and configuration."""

import pytest
from django.test import Client


@pytest.fixture
def client() -> Client:
    """Django test client fixture."""
    return Client()
