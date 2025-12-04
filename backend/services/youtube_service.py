"""YouTube video summarization service."""
import re
import httpx
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs


class YouTubeService:
    """Service for YouTube video processing."""
    
    def __init__(self):
        self.transcript_api_url = "https://www.youtube.com/watch"
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL."""
        # Handle different YouTube URL formats
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/shorts\/([a-zA-Z0-9_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # Try parsing as URL
        parsed = urlparse(url)
        if 'youtube.com' in parsed.netloc:
            query = parse_qs(parsed.query)
            if 'v' in query:
                return query['v'][0]
        
        return None
    
    async def get_video_info(self, video_id: str) -> Dict[str, Any]:
        """Get basic video information using oembed."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"https://www.youtube.com/oembed",
                    params={"url": f"https://www.youtube.com/watch?v={video_id}", "format": "json"},
                    timeout=10.0
                )
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                print(f"Error getting video info: {e}")
        
        return {"title": "Unknown", "author_name": "Unknown"}
    
    async def get_transcript(self, video_id: str, language: str = "en") -> Optional[str]:
        """
        Attempt to get video transcript.
        Note: This is a simplified version. For production, use youtube-transcript-api package.
        """
        # This would require the youtube-transcript-api package for proper implementation
        # For now, return a placeholder that explains the limitation
        return None
    
    async def summarize_video(
        self,
        url: str,
        llm_service,
        model: str,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Summarize a YouTube video.
        Returns video info and summary.
        """
        video_id = self.extract_video_id(url)
        if not video_id:
            raise ValueError("Invalid YouTube URL")
        
        # Get video info
        video_info = await self.get_video_info(video_id)
        
        # Try to get transcript
        transcript = await self.get_transcript(video_id, language)
        
        if transcript:
            # Summarize transcript using LLM
            summary_prompt = f"""Please summarize the following YouTube video transcript concisely.
            
Video Title: {video_info.get('title', 'Unknown')}
Author: {video_info.get('author_name', 'Unknown')}

Transcript:
{transcript[:8000]}  # Limit transcript length

Provide a clear, structured summary with:
1. Main topic/theme
2. Key points (bullet points)
3. Conclusion or takeaway
"""
            summary, _ = await llm_service.chat_completion(
                messages=[],
                model=model,
                system_prompt="You are a helpful assistant that summarizes YouTube videos clearly and concisely.",
                temperature=0.5,
                max_tokens=1000,
            )
        else:
            # Without transcript, provide video info and suggest manual viewing
            summary = f"""Unable to retrieve transcript for this video.

**Video Information:**
- Title: {video_info.get('title', 'Unknown')}
- Author: {video_info.get('author_name', 'Unknown')}

To get a summary, you can:
1. Watch the video manually
2. Use browser extensions that support transcript extraction
3. Check if captions are available on the video

Note: For full transcript support, the youtube-transcript-api package needs to be installed."""
        
        return {
            "video_id": video_id,
            "title": video_info.get("title", "Unknown"),
            "author": video_info.get("author_name", "Unknown"),
            "thumbnail": video_info.get("thumbnail_url", ""),
            "summary": summary,
            "has_transcript": transcript is not None,
        }


youtube_service = YouTubeService()

