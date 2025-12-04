"""Pydantic models for API requests and responses."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class SearchProvider(str, Enum):
    """Available search providers."""
    SEARXNG = "searxng"
    BRAVE = "brave"
    DUCKDUCKGO = "duckduckgo"


class MessageRole(str, Enum):
    """Chat message roles."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """Single chat message."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    sources: Optional[List[Dict[str, Any]]] = None
    token_count: Optional[int] = None


class ChatSession(BaseModel):
    """Chat session containing messages."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    model: str
    messages: List[ChatMessage] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    # LLM Parameters
    temperature: float = 0.7
    max_tokens: int = 2048
    system_prompt: str = "You are a helpful AI assistant."
    # Usage tracking
    total_tokens_used: int = 0


class LLMParameters(BaseModel):
    """LLM generation parameters."""
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1, le=32000)
    system_prompt: str = "You are a helpful AI assistant."
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)


class ChatRequest(BaseModel):
    """Request for chat completion."""
    session_id: str
    message: str
    model: str
    enable_search: bool = False
    enable_rag: bool = False
    search_provider: SearchProvider = SearchProvider.DUCKDUCKGO
    # LLM Parameters
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None


class ChatResponse(BaseModel):
    """Response from chat completion."""
    message: ChatMessage
    sources: Optional[List[Dict[str, Any]]] = None
    tokens_used: Optional[int] = None


class ModelInfo(BaseModel):
    """Information about available model."""
    id: str
    name: str
    context_length: Optional[int] = None
    owned_by: Optional[str] = None


class SearchSettings(BaseModel):
    """Search configuration."""
    provider: SearchProvider = SearchProvider.DUCKDUCKGO
    brave_api_key: Optional[str] = None
    searxng_url: Optional[str] = None


class RAGDocument(BaseModel):
    """Document for RAG indexing."""
    path: str
    size: int
    indexed: bool = False


class RAGIndexRequest(BaseModel):
    """Request to index directory for RAG."""
    directory_path: str


class FileUploadResponse(BaseModel):
    """Response after file upload."""
    filename: str
    size: int
    indexed: bool


class SessionCreate(BaseModel):
    """Request to create new session."""
    name: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 2048
    system_prompt: str = "You are a helpful AI assistant."


class SessionUpdate(BaseModel):
    """Request to update session."""
    name: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None


class UsageStats(BaseModel):
    """Usage statistics."""
    total_tokens: int = 0
    total_requests: int = 0
    sessions_count: int = 0
    last_request: Optional[datetime] = None


class YouTubeSummaryRequest(BaseModel):
    """Request to summarize YouTube video."""
    url: str
    language: str = "en"


class DeepResearchRequest(BaseModel):
    """Request for deep research."""
    query: str
    max_iterations: int = 5
    search_provider: SearchProvider = SearchProvider.DUCKDUCKGO


class TTSRequest(BaseModel):
    """Request for text-to-speech."""
    text: str
    voice: str = "alloy"
    speed: float = 1.0


class PromptPreset(BaseModel):
    """A preset for system prompts."""
    id: str
    name: str
    description: str
    system_prompt: str
    temperature: float = 0.7
    max_tokens: int = 2048
    icon: str = "📝"
    category: str = "general"


class PresetCreate(BaseModel):
    """Request to create a custom preset."""
    name: str
    description: str
    system_prompt: str
    temperature: float = 0.7
    max_tokens: int = 2048
    icon: str = "📝"
    category: str = "custom"


class ImageGenerateRequest(BaseModel):
    """Request to generate an image."""
    prompt: str
    size: str = "1024x1024"  # 1024x1024, 1792x1024, 1024x1792
    quality: str = "standard"  # standard, hd
    style: str = "vivid"  # vivid, natural


class APIProviderType(str, Enum):
    """Supported API provider types."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    GROQ = "groq"
    TOGETHER = "together"
    MISTRAL = "mistral"
    OPENROUTER = "openrouter"
    XAI = "xai"  # Grok
    CUSTOM = "custom"


class APIProvider(BaseModel):
    """Configuration for an API provider."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # Display name
    type: APIProviderType
    api_base: str
    api_key: str = ""
    enabled: bool = True
    models: List[str] = []  # Cached model list
    last_check: Optional[datetime] = None
    
    class Config:
        use_enum_values = True


class APIProviderCreate(BaseModel):
    """Request to add a new API provider."""
    name: str
    type: APIProviderType
    api_base: str
    api_key: str = ""


class APIProviderUpdate(BaseModel):
    """Request to update an API provider."""
    name: Optional[str] = None
    api_base: Optional[str] = None
    api_key: Optional[str] = None
    enabled: Optional[bool] = None
