"""Pytest configuration and fixtures."""
import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_session_data():
    """Sample session data for testing."""
    return {
        "name": "Test Session",
        "model": "test-model",
        "temperature": 0.7,
        "max_tokens": 2048,
        "system_prompt": "You are a test assistant."
    }


@pytest.fixture
def sample_chat_request():
    """Sample chat request data."""
    return {
        "session_id": "test-session-id",
        "message": "Hello, how are you?",
        "model": "test-model",
        "enable_search": False,
        "enable_rag": False,
    }

