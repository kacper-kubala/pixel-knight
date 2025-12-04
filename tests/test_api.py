"""Tests for API endpoints."""
import pytest


class TestModelsEndpoint:
    """Tests for /api/models endpoint."""
    
    def test_get_models_returns_list(self, client):
        """Test that /api/models returns a list."""
        response = client.get("/api/models")
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert isinstance(data["models"], list)


class TestSessionsEndpoint:
    """Tests for /api/sessions endpoints."""
    
    def test_get_sessions_returns_list(self, client):
        """Test that /api/sessions returns a list."""
        response = client.get("/api/sessions")
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert isinstance(data["sessions"], list)
    
    def test_create_session(self, client, sample_session_data):
        """Test creating a new session."""
        response = client.post("/api/sessions", json=sample_session_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_session_data["name"]
        assert data["model"] == sample_session_data["model"]
        assert "id" in data
    
    def test_get_nonexistent_session_returns_404(self, client):
        """Test that getting nonexistent session returns 404."""
        response = client.get("/api/sessions/nonexistent-id")
        assert response.status_code == 404


class TestPresetsEndpoint:
    """Tests for /api/presets endpoints."""
    
    def test_get_presets_returns_list(self, client):
        """Test that /api/presets returns presets."""
        response = client.get("/api/presets")
        assert response.status_code == 200
        data = response.json()
        assert "presets" in data
        assert isinstance(data["presets"], list)
        # Should have built-in presets
        assert len(data["presets"]) > 0
    
    def test_get_preset_by_id(self, client):
        """Test getting a specific preset."""
        response = client.get("/api/presets/assistant")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "assistant"
        assert "system_prompt" in data
    
    def test_get_nonexistent_preset_returns_404(self, client):
        """Test that getting nonexistent preset returns 404."""
        response = client.get("/api/presets/nonexistent-preset")
        assert response.status_code == 404


class TestRootEndpoint:
    """Tests for root endpoint."""
    
    def test_root_returns_html(self, client):
        """Test that root returns HTML."""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestImageStatus:
    """Tests for image generation status."""
    
    def test_image_status_returns_configured_flag(self, client):
        """Test that image status endpoint works."""
        response = client.get("/api/images/status")
        assert response.status_code == 200
        data = response.json()
        assert "configured" in data
        assert isinstance(data["configured"], bool)

