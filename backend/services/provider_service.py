"""API Provider management service."""
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import uuid
import httpx

from ..models import APIProvider, APIProviderType


# Default provider configurations
DEFAULT_PROVIDERS = {
    "ollama": {
        "name": "Ollama (Local)",
        "type": APIProviderType.OLLAMA,
        "api_base": "http://localhost:11434/v1",
        "api_key": "",
    },
    "openai": {
        "name": "OpenAI",
        "type": APIProviderType.OPENAI,
        "api_base": "https://api.openai.com/v1",
        "api_key": "",
    },
    "anthropic": {
        "name": "Anthropic (Claude)",
        "type": APIProviderType.ANTHROPIC,
        "api_base": "https://api.anthropic.com/v1",
        "api_key": "",
    },
    "groq": {
        "name": "Groq",
        "type": APIProviderType.GROQ,
        "api_base": "https://api.groq.com/openai/v1",
        "api_key": "",
    },
    "xai": {
        "name": "xAI (Grok)",
        "type": APIProviderType.XAI,
        "api_base": "https://api.x.ai/v1",
        "api_key": "",
    },
    "together": {
        "name": "Together AI",
        "type": APIProviderType.TOGETHER,
        "api_base": "https://api.together.xyz/v1",
        "api_key": "",
    },
    "mistral": {
        "name": "Mistral AI",
        "type": APIProviderType.MISTRAL,
        "api_base": "https://api.mistral.ai/v1",
        "api_key": "",
    },
    "openrouter": {
        "name": "OpenRouter",
        "type": APIProviderType.OPENROUTER,
        "api_base": "https://openrouter.ai/api/v1",
        "api_key": "",
    },
}


class ProviderService:
    """Service for managing multiple API providers."""
    
    def __init__(self):
        self.providers: Dict[str, APIProvider] = {}
        self.data_file = Path("./data/providers.json")
        self._load_providers()
    
    def _load_providers(self):
        """Load providers from disk."""
        if self.data_file.exists():
            try:
                with open(self.data_file) as f:
                    data = json.load(f)
                    for provider_data in data:
                        provider = APIProvider(**provider_data)
                        self.providers[provider.id] = provider
            except Exception as e:
                print(f"Error loading providers: {e}")
                self._init_default_providers()
        else:
            self._init_default_providers()
    
    def _init_default_providers(self):
        """Initialize with default providers."""
        # Add Ollama as default enabled provider
        ollama = APIProvider(
            id="ollama",
            name="Ollama (Local)",
            type=APIProviderType.OLLAMA,
            api_base="http://localhost:11434/v1",
            api_key="",
            enabled=True,
        )
        self.providers["ollama"] = ollama
        self._save_providers()
    
    def _save_providers(self):
        """Save providers to disk."""
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        providers = [p.model_dump(mode="json") for p in self.providers.values()]
        with open(self.data_file, "w") as f:
            json.dump(providers, f, indent=2, default=str)
    
    def get_all_providers(self) -> List[APIProvider]:
        """Get all configured providers."""
        return list(self.providers.values())
    
    def get_enabled_providers(self) -> List[APIProvider]:
        """Get only enabled providers."""
        return [p for p in self.providers.values() if p.enabled]
    
    def get_provider(self, provider_id: str) -> Optional[APIProvider]:
        """Get a specific provider by ID."""
        return self.providers.get(provider_id)
    
    def add_provider(
        self,
        name: str,
        provider_type: APIProviderType,
        api_base: str,
        api_key: str = "",
    ) -> APIProvider:
        """Add a new provider."""
        provider = APIProvider(
            id=str(uuid.uuid4()),
            name=name,
            type=provider_type,
            api_base=api_base.rstrip("/"),
            api_key=api_key,
            enabled=True,
        )
        self.providers[provider.id] = provider
        self._save_providers()
        return provider
    
    def add_preset_provider(self, preset_key: str, api_key: str = "") -> Optional[APIProvider]:
        """Add a preset provider (like openai, anthropic, etc.)."""
        if preset_key not in DEFAULT_PROVIDERS:
            return None
        
        preset = DEFAULT_PROVIDERS[preset_key]
        provider = APIProvider(
            id=preset_key,
            name=preset["name"],
            type=preset["type"],
            api_base=preset["api_base"],
            api_key=api_key,
            enabled=bool(api_key) or preset_key == "ollama",
        )
        self.providers[provider.id] = provider
        self._save_providers()
        return provider
    
    def update_provider(
        self,
        provider_id: str,
        name: Optional[str] = None,
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
        enabled: Optional[bool] = None,
    ) -> Optional[APIProvider]:
        """Update a provider."""
        provider = self.providers.get(provider_id)
        if not provider:
            return None
        
        if name is not None:
            provider.name = name
        if api_base is not None:
            provider.api_base = api_base.rstrip("/")
        if api_key is not None:
            provider.api_key = api_key
        if enabled is not None:
            provider.enabled = enabled
        
        self._save_providers()
        return provider
    
    def delete_provider(self, provider_id: str) -> bool:
        """Delete a provider."""
        if provider_id in self.providers:
            del self.providers[provider_id]
            self._save_providers()
            return True
        return False
    
    def toggle_provider(self, provider_id: str) -> Optional[APIProvider]:
        """Toggle provider enabled status."""
        provider = self.providers.get(provider_id)
        if provider:
            provider.enabled = not provider.enabled
            self._save_providers()
        return provider
    
    async def test_provider(self, provider_id: str) -> dict:
        """Test if a provider is reachable and get models."""
        provider = self.providers.get(provider_id)
        if not provider:
            return {"success": False, "error": "Provider not found"}
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {}
                if provider.api_key:
                    headers["Authorization"] = f"Bearer {provider.api_key}"
                
                # Special handling for Anthropic
                if provider.type == APIProviderType.ANTHROPIC:
                    headers["x-api-key"] = provider.api_key
                    headers["anthropic-version"] = "2023-06-01"
                    # Anthropic doesn't have a models endpoint, return known models
                    provider.models = ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307", "claude-3-5-sonnet-20241022"]
                    provider.last_check = datetime.now()
                    self._save_providers()
                    return {"success": True, "models": provider.models}
                
                response = await client.get(
                    f"{provider.api_base}/models",
                    headers=headers,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    models = []
                    if "data" in data:
                        models = [m.get("id", m.get("name", "unknown")) for m in data["data"]]
                    elif isinstance(data, list):
                        models = [m.get("id", m.get("name", "unknown")) for m in data]
                    
                    provider.models = models
                    provider.last_check = datetime.now()
                    self._save_providers()
                    
                    return {"success": True, "models": models}
                else:
                    return {"success": False, "error": f"HTTP {response.status_code}"}
                    
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_all_models(self) -> List[dict]:
        """Get models from all enabled providers."""
        all_models = []
        
        for provider in self.get_enabled_providers():
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    headers = {}
                    if provider.api_key:
                        headers["Authorization"] = f"Bearer {provider.api_key}"
                    
                    # Special handling for Anthropic
                    if provider.type == APIProviderType.ANTHROPIC:
                        # Anthropic doesn't have models endpoint
                        for model_id in ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"]:
                            all_models.append({
                                "id": model_id,
                                "name": model_id,
                                "provider_id": provider.id,
                                "provider_name": provider.name,
                                "provider_type": provider.type,
                            })
                        continue
                    
                    response = await client.get(
                        f"{provider.api_base}/models",
                        headers=headers,
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        models = []
                        if "data" in data:
                            models = data["data"]
                        elif isinstance(data, list):
                            models = data
                        
                        for model in models:
                            model_id = model.get("id", model.get("name", "unknown"))
                            all_models.append({
                                "id": model_id,
                                "name": model_id,
                                "provider_id": provider.id,
                                "provider_name": provider.name,
                                "provider_type": provider.type,
                            })
                            
            except Exception as e:
                print(f"Error fetching models from {provider.name}: {e}")
                continue
        
        return all_models
    
    def get_provider_for_model(self, model_id: str) -> Optional[APIProvider]:
        """Find which provider has a specific model."""
        # First check cached models
        for provider in self.get_enabled_providers():
            if model_id in provider.models:
                return provider
        
        # Fallback: check by model prefix patterns
        model_lower = model_id.lower()
        
        if "claude" in model_lower:
            return self.providers.get("anthropic")
        elif "gpt" in model_lower or "o1" in model_lower:
            return self.providers.get("openai")
        elif "grok" in model_lower:
            return self.providers.get("xai")
        elif "mixtral" in model_lower or "mistral" in model_lower:
            for p in self.get_enabled_providers():
                if p.type in [APIProviderType.MISTRAL, APIProviderType.GROQ, APIProviderType.TOGETHER]:
                    return p
        elif "llama" in model_lower:
            for p in self.get_enabled_providers():
                if p.type in [APIProviderType.OLLAMA, APIProviderType.GROQ, APIProviderType.TOGETHER]:
                    return p
        
        # Return first enabled provider as fallback
        enabled = self.get_enabled_providers()
        return enabled[0] if enabled else None
    
    def get_available_presets(self) -> List[dict]:
        """Get list of available preset providers that aren't configured yet."""
        configured_types = {p.type for p in self.providers.values()}
        available = []
        
        for key, preset in DEFAULT_PROVIDERS.items():
            if key not in self.providers:
                available.append({
                    "key": key,
                    "name": preset["name"],
                    "type": preset["type"],
                    "api_base": preset["api_base"],
                    "requires_key": key != "ollama",
                })
        
        return available


provider_service = ProviderService()

