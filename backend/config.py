"""Configuration management for Pixel Knight."""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # API Configuration (default to Ollama)
    openai_api_base: str = "http://localhost:11434/v1"
    openai_api_key: str = "sk-no-key-required"
    
    # Search Providers
    brave_api_key: Optional[str] = None
    searxng_url: Optional[str] = None
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8080
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./data/pixel_knight.db"
    
    # RAG
    chroma_persist_directory: str = "./data/chroma"
    
    # Image Generation
    openai_dalle_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

