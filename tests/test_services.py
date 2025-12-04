"""Tests for backend services."""
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from backend.services.session_service import SessionService
from backend.services.preset_service import PresetService
from backend.models import MessageRole


class TestSessionService:
    """Tests for SessionService."""
    
    @pytest.fixture
    def session_service(self, tmp_path):
        """Create a SessionService with temporary directory."""
        service = SessionService()
        service.data_dir = tmp_path / "sessions"
        service.data_dir.mkdir(parents=True, exist_ok=True)
        return service
    
    def test_create_session(self, session_service):
        """Test creating a new session."""
        session = session_service.create_session(
            name="Test Session",
            model="test-model",
            temperature=0.7,
            max_tokens=2048,
            system_prompt="Test prompt"
        )
        
        assert session is not None
        assert session.name == "Test Session"
        assert session.model == "test-model"
        assert session.temperature == 0.7
        assert session.max_tokens == 2048
        assert session.system_prompt == "Test prompt"
        assert session.id is not None
    
    def test_get_session(self, session_service):
        """Test getting a session by ID."""
        created = session_service.create_session(
            name="Test",
            model="model"
        )
        
        retrieved = session_service.get_session(created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == created.name
    
    def test_get_nonexistent_session_returns_none(self, session_service):
        """Test that getting nonexistent session returns None."""
        result = session_service.get_session("nonexistent-id")
        assert result is None
    
    def test_add_message(self, session_service):
        """Test adding a message to a session."""
        session = session_service.create_session(
            name="Test",
            model="model"
        )
        
        message = session_service.add_message(
            session.id,
            MessageRole.USER,
            "Hello, world!"
        )
        
        assert message is not None
        assert message.content == "Hello, world!"
        assert message.role == MessageRole.USER
    
    def test_get_messages(self, session_service):
        """Test getting messages from a session."""
        session = session_service.create_session(
            name="Test",
            model="model"
        )
        
        session_service.add_message(session.id, MessageRole.USER, "Message 1")
        session_service.add_message(session.id, MessageRole.ASSISTANT, "Message 2")
        
        messages = session_service.get_messages(session.id)
        
        assert len(messages) == 2
        assert messages[0].content == "Message 1"
        assert messages[1].content == "Message 2"
    
    def test_delete_session(self, session_service):
        """Test deleting a session."""
        session = session_service.create_session(
            name="Test",
            model="model"
        )
        
        result = session_service.delete_session(session.id)
        
        assert result is True
        assert session_service.get_session(session.id) is None
    
    def test_update_session(self, session_service):
        """Test updating session properties."""
        session = session_service.create_session(
            name="Original Name",
            model="model"
        )
        
        updated = session_service.update_session(
            session.id,
            name="Updated Name",
            temperature=0.9
        )
        
        assert updated is not None
        assert updated.name == "Updated Name"
        assert updated.temperature == 0.9
    
    def test_remove_message(self, session_service):
        """Test removing a message."""
        session = session_service.create_session(
            name="Test",
            model="model"
        )
        
        message = session_service.add_message(
            session.id,
            MessageRole.USER,
            "To be deleted"
        )
        
        result = session_service.remove_message(session.id, message.id)
        
        assert result is True
        messages = session_service.get_messages(session.id)
        assert len(messages) == 0
    
    def test_search_sessions(self, session_service):
        """Test searching sessions."""
        session_service.create_session(name="Python Tutorial", model="model")
        session_service.create_session(name="JavaScript Guide", model="model")
        
        results = session_service.search_sessions("Python")
        
        assert len(results) == 1
        assert results[0].name == "Python Tutorial"
    
    def test_get_total_usage(self, session_service):
        """Test getting usage statistics."""
        session = session_service.create_session(name="Test", model="model")
        session_service.add_message(session.id, MessageRole.USER, "Hello")
        
        usage = session_service.get_total_usage()
        
        assert usage["total_sessions"] == 1
        assert usage["total_messages"] == 1


class TestPresetService:
    """Tests for PresetService."""
    
    @pytest.fixture
    def preset_service(self, tmp_path):
        """Create a PresetService with temporary directory."""
        service = PresetService()
        service.data_file = tmp_path / "presets.json"
        return service
    
    def test_get_all_presets(self, preset_service):
        """Test getting all presets."""
        presets = preset_service.get_all_presets()
        
        assert len(presets) > 0
        # Should include built-in presets
        preset_ids = [p.id for p in presets]
        assert "assistant" in preset_ids
        assert "coder" in preset_ids
    
    def test_get_preset_by_id(self, preset_service):
        """Test getting a specific preset."""
        preset = preset_service.get_preset("assistant")
        
        assert preset is not None
        assert preset.id == "assistant"
        assert preset.name == "General Assistant"
    
    def test_get_nonexistent_preset_returns_none(self, preset_service):
        """Test that getting nonexistent preset returns None."""
        result = preset_service.get_preset("nonexistent")
        assert result is None
    
    def test_create_custom_preset(self, preset_service):
        """Test creating a custom preset."""
        preset = preset_service.create_preset(
            name="My Custom Preset",
            description="Test preset",
            system_prompt="Be helpful",
            temperature=0.5,
            max_tokens=1024,
        )
        
        assert preset is not None
        assert preset.name == "My Custom Preset"
        assert preset.id.startswith("custom_")
    
    def test_delete_custom_preset(self, preset_service):
        """Test deleting a custom preset."""
        preset = preset_service.create_preset(
            name="To Delete",
            description="Will be deleted",
            system_prompt="Test",
        )
        
        result = preset_service.delete_preset(preset.id)
        
        assert result is True
        assert preset_service.get_preset(preset.id) is None
    
    def test_get_categories(self, preset_service):
        """Test getting all categories."""
        categories = preset_service.get_categories()
        
        assert len(categories) > 0
        assert "general" in categories
        assert "development" in categories

