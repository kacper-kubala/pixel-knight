"""LLM service for interacting with AI models."""
import httpx
from typing import AsyncGenerator, List, Dict, Any, Optional
from openai import AsyncOpenAI
from ..config import settings
from ..models import ChatMessage, MessageRole, APIProviderType


class LLMService:
    """Service for LLM interactions."""
    
    def __init__(self):
        self._clients: Dict[str, AsyncOpenAI] = {}
        self._usage_stats = {
            "total_tokens": 0,
            "total_requests": 0,
        }
    
    def _get_client(self, api_base: str, api_key: str) -> AsyncOpenAI:
        """Get or create a client for a specific API endpoint."""
        cache_key = f"{api_base}:{api_key[:8] if api_key else 'nokey'}"
        
        if cache_key not in self._clients:
            self._clients[cache_key] = AsyncOpenAI(
                base_url=api_base,
                api_key=api_key or "sk-no-key-required",
            )
        
        return self._clients[cache_key]
    
    def _get_provider_client(self, model: str) -> AsyncOpenAI:
        """Get the appropriate client for a model."""
        from .provider_service import provider_service
        
        provider = provider_service.get_provider_for_model(model)
        if provider:
            return self._get_client(provider.api_base, provider.api_key)
        
        # Fallback to default settings
        return self._get_client(settings.openai_api_base, settings.openai_api_key)
    
    def update_client(self):
        """Clear cached clients to force refresh."""
        self._clients.clear()
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Fetch available models from all enabled providers."""
        from .provider_service import provider_service
        
        try:
            return await provider_service.get_all_models()
        except Exception as e:
            print(f"Error fetching models: {e}")
            return []
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough estimate: ~4 chars per token)."""
        return len(text) // 4
    
    def truncate_messages(
        self,
        messages: List[ChatMessage],
        max_tokens: int = 4000,
        keep_system: bool = True
    ) -> List[ChatMessage]:
        """Truncate message history to fit within token limit."""
        if not messages:
            return messages
        
        # Calculate total tokens
        total_tokens = sum(self.estimate_tokens(m.content) for m in messages)
        
        if total_tokens <= max_tokens:
            return messages
        
        # Keep most recent messages, always keep the last user message
        truncated = []
        current_tokens = 0
        
        # Process messages in reverse (newest first)
        for msg in reversed(messages):
            msg_tokens = self.estimate_tokens(msg.content)
            if current_tokens + msg_tokens <= max_tokens:
                truncated.insert(0, msg)
                current_tokens += msg_tokens
            elif not truncated:  # Always include at least the last message
                truncated.insert(0, msg)
                break
        
        return truncated
    
    async def chat_completion(
        self,
        messages: List[ChatMessage],
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        top_p: float = 1.0,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
    ) -> tuple[str, int]:
        """Generate chat completion. Returns (content, tokens_used)."""
        formatted_messages = []
        
        if system_prompt:
            formatted_messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        # Truncate messages if needed
        truncated = self.truncate_messages(messages, max_tokens=4000)
        
        for msg in truncated:
            formatted_messages.append({
                "role": msg.role.value,
                "content": msg.content
            })
        
        try:
            client = self._get_provider_client(model)
            response = await client.chat.completions.create(
                model=model,
                messages=formatted_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
            )
            
            # Track usage
            tokens_used = getattr(response.usage, 'total_tokens', 0) if response.usage else 0
            self._usage_stats["total_tokens"] += tokens_used
            self._usage_stats["total_requests"] += 1
            
            return response.choices[0].message.content, tokens_used
        except Exception as e:
            raise Exception(f"Error generating completion: {e}")
    
    async def chat_completion_stream(
        self,
        messages: List[ChatMessage],
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        top_p: float = 1.0,
    ) -> AsyncGenerator[str, None]:
        """Generate streaming chat completion."""
        formatted_messages = []
        
        if system_prompt:
            formatted_messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        # Truncate messages if needed
        truncated = self.truncate_messages(messages, max_tokens=4000)
        
        for msg in truncated:
            formatted_messages.append({
                "role": msg.role.value,
                "content": msg.content
            })
        
        try:
            client = self._get_provider_client(model)
            stream = await client.chat.completions.create(
                model=model,
                messages=formatted_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                stream=True,
            )
            
            self._usage_stats["total_requests"] += 1
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"Error: {e}"
    
    async def generate_session_name(self, first_message: str, model: str) -> str:
        """Generate a concise name for a chat session based on the first message."""
        try:
            client = self._get_provider_client(model)
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "Generate a very short (3-5 words max) title for a conversation that starts with the following message. Reply with ONLY the title, nothing else."
                    },
                    {
                        "role": "user",
                        "content": first_message[:500]  # Limit input
                    }
                ],
                temperature=0.7,
                max_tokens=20,
            )
            name = response.choices[0].message.content.strip()
            # Clean up the name
            name = name.strip('"\'')[:50]
            return name if name else "New Chat"
        except Exception as e:
            print(f"Error generating session name: {e}")
            return "New Chat"
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return self._usage_stats.copy()
    
    def reset_usage_stats(self):
        """Reset usage statistics."""
        self._usage_stats = {
            "total_tokens": 0,
            "total_requests": 0,
        }


llm_service = LLMService()
