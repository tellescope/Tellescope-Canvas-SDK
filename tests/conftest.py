"""
Pytest configuration and shared fixtures for Tellescope Canvas SDK tests
"""

import pytest
from unittest.mock import Mock
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


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
    """Test environment variables loaded from .env file"""
    return {
        "TELLESCOPE_API_KEY": os.getenv("TELLESCOPE_API_KEY"),
        "TELLESCOPE_API_URL": os.getenv("TELLESCOPE_API_URL"),
        "CANVAS_API_KEY": os.getenv("CANVAS_API_KEY"),
    }