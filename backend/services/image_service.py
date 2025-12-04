"""Image generation service using OpenAI DALL-E API."""
import os
import base64
import httpx
from typing import Optional
from datetime import datetime
from pathlib import Path

from ..config import settings


class ImageService:
    """Service for generating images using DALL-E."""
    
    def __init__(self):
        self.api_key = settings.openai_dalle_key or os.getenv("OPENAI_DALLE_KEY")
        self.api_url = "https://api.openai.com/v1/images/generations"
        self.output_dir = Path("./data/images")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def is_configured(self) -> bool:
        """Check if DALL-E API is configured."""
        return bool(self.api_key)
    
    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        style: str = "vivid",
        n: int = 1,
    ) -> dict:
        """
        Generate an image using DALL-E 3.
        
        Args:
            prompt: The text description of the image to generate
            size: Image size (1024x1024, 1792x1024, or 1024x1792)
            quality: Image quality (standard or hd)
            style: Image style (vivid or natural)
            n: Number of images to generate (1 for DALL-E 3)
        
        Returns:
            dict with url, revised_prompt, and saved_path
        """
        if not self.is_configured():
            raise ValueError("DALL-E API key not configured. Set OPENAI_DALLE_KEY in .env")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "dall-e-3",
                    "prompt": prompt,
                    "n": n,
                    "size": size,
                    "quality": quality,
                    "style": style,
                    "response_format": "b64_json",  # Get base64 data
                },
                timeout=120.0,  # DALL-E can take a while
            )
            
            if response.status_code != 200:
                error_data = response.json()
                raise Exception(f"DALL-E API error: {error_data.get('error', {}).get('message', 'Unknown error')}")
            
            data = response.json()
            image_data = data["data"][0]
            
            # Decode and save the image
            image_bytes = base64.b64decode(image_data["b64_json"])
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"image_{timestamp}.png"
            filepath = self.output_dir / filename
            
            with open(filepath, "wb") as f:
                f.write(image_bytes)
            
            return {
                "url": f"/static/images/{filename}",
                "revised_prompt": image_data.get("revised_prompt", prompt),
                "saved_path": str(filepath),
                "size": size,
            }
    
    def get_generated_images(self) -> list:
        """Get list of generated images."""
        images = []
        for filepath in sorted(self.output_dir.glob("*.png"), reverse=True):
            images.append({
                "filename": filepath.name,
                "url": f"/static/images/{filepath.name}",
                "created_at": datetime.fromtimestamp(filepath.stat().st_mtime).isoformat(),
            })
        return images


image_service = ImageService()

