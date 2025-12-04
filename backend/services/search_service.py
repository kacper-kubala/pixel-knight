"""Search service for web searches."""
import httpx
from typing import List, Dict, Any, Optional
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
from ..models import SearchProvider
from ..config import settings


class SearchService:
    """Service for web searches."""
    
    def __init__(self):
        self.brave_api_key = settings.brave_api_key
        self.searxng_url = settings.searxng_url
    
    async def search(
        self,
        query: str,
        provider: SearchProvider = SearchProvider.DUCKDUCKGO,
        max_results: int = 5,
        brave_key: Optional[str] = None,
        searxng_url: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Execute search using specified provider."""
        if provider == SearchProvider.DUCKDUCKGO:
            return await self._search_duckduckgo(query, max_results)
        elif provider == SearchProvider.BRAVE:
            key = brave_key or self.brave_api_key
            if not key:
                raise ValueError("Brave API key required")
            return await self._search_brave(query, key, max_results)
        elif provider == SearchProvider.SEARXNG:
            url = searxng_url or self.searxng_url
            if not url:
                raise ValueError("SearXNG URL required")
            return await self._search_searxng(query, url, max_results)
        else:
            raise ValueError(f"Unknown search provider: {provider}")
    
    async def _search_duckduckgo(
        self, query: str, max_results: int
    ) -> List[Dict[str, Any]]:
        """Search using DuckDuckGo."""
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                return [
                    {
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", ""),
                    }
                    for r in results
                ]
        except Exception as e:
            print(f"DuckDuckGo search error: {e}")
            return []
    
    async def _search_brave(
        self, query: str, api_key: str, max_results: int
    ) -> List[Dict[str, Any]]:
        """Search using Brave Search API."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    "https://api.search.brave.com/res/v1/web/search",
                    params={"q": query, "count": max_results},
                    headers={
                        "Accept": "application/json",
                        "X-Subscription-Token": api_key,
                    },
                )
                response.raise_for_status()
                data = response.json()
                
                results = []
                for r in data.get("web", {}).get("results", [])[:max_results]:
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "snippet": r.get("description", ""),
                    })
                return results
            except Exception as e:
                print(f"Brave search error: {e}")
                return []
    
    async def _search_searxng(
        self, query: str, base_url: str, max_results: int
    ) -> List[Dict[str, Any]]:
        """Search using SearXNG instance."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{base_url}/search",
                    params={
                        "q": query,
                        "format": "json",
                        "engines": "google,bing,duckduckgo",
                    },
                )
                response.raise_for_status()
                data = response.json()
                
                results = []
                for r in data.get("results", [])[:max_results]:
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "snippet": r.get("content", ""),
                    })
                return results
            except Exception as e:
                print(f"SearXNG search error: {e}")
                return []
    
    async def fetch_page_content(self, url: str) -> str:
        """Fetch and extract text content from a webpage."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, timeout=10.0)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Remove script and style elements
                for element in soup(["script", "style", "nav", "header", "footer"]):
                    element.decompose()
                
                text = soup.get_text(separator=" ", strip=True)
                # Limit text length
                return text[:8000]
            except Exception as e:
                print(f"Error fetching page: {e}")
                return ""


search_service = SearchService()

