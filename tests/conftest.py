"""
Pytest configuration and shared fixtures for Tellescope Canvas SDK tests
"""

import pytest
import os
from unittest.mock import Mock


@pytest.fixture
def mock_canvas_sdk():
    """Mock Canvas SDK for testing"""
    return Mock()


@pytest.fixture
def mock_tellescope_api():
    """Mock Tellescope API for testing"""
    return Mock()


@pytest.fixture
def test_env_vars():
    """Test environment variables"""
    return {
        "TELLESCOPE_API_KEY": "test_api_key",
        "CANVAS_API_KEY": "test_canvas_key",
        # Add other test env vars as needed
    }


@pytest.fixture(autouse=True)
def setup_test_env(test_env_vars):
    """Automatically set up test environment variables"""
    original_env = {}
    
    # Save original values and set test values
    for key, value in test_env_vars.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield
    
    # Restore original values
    for key in test_env_vars:
        if original_env[key] is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_env[key]