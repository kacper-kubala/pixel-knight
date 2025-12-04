"""Main FastAPI application for Pixel Knight."""
import json
import os
import shutil
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from pathlib import Path
from typing import List
from pydantic import BaseModel

from .models import (
    ChatRequest,
    SessionCreate,
    SessionUpdate,
    SearchSettings,
    RAGIndexRequest,
    MessageRole,
    SearchProvider,
    LLMParameters,
    YouTubeSummaryRequest,
    DeepResearchRequest,
    TTSRequest,
    PresetCreate,
    ImageGenerateRequest,
)
from .services.llm_service import llm_service
from .services.search_service import search_service
from .services.rag_service import rag_service
from .services.session_service import session_service
from .services.youtube_service import youtube_service
from .services.research_service import deep_research_service
from .services.preset_service import preset_service
from .services.image_service import image_service
from .services.provider_service import provider_service
from .config import settings

app = FastAPI(
    title="Pixel Knight",
    description="AI Chat Interface with Search and RAG capabilities",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
static_path = Path(__file__).parent.parent / "frontend"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Upload directory
upload_dir = Path("./data/uploads")
upload_dir.mkdir(parents=True, exist_ok=True)

# Images directory for generated images
images_dir = Path("./data/images")
images_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static/images", StaticFiles(directory=str(images_dir)), name="images")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main HTML page."""
    index_path = Path(__file__).parent.parent / "frontend" / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return HTMLResponse("<h1>Pixel Knight</h1><p>Frontend not found</p>")


# ============ Models Endpoints ============

@app.get("/api/models")
async def get_models():
    """Get available AI models from all enabled providers."""
    models = await llm_service.get_available_models()
    return {"models": models}


# ============ Provider Management Endpoints ============

@app.get("/api/providers")
async def get_providers():
    """Get all configured API providers."""
    providers = provider_service.get_all_providers()
    # Don't expose full API keys
    return {
        "providers": [
            {
                "id": p.id,
                "name": p.name,
                "type": p.type,
                "api_base": p.api_base,
                "has_key": bool(p.api_key),
                "enabled": p.enabled,
                "models_count": len(p.models),
                "last_check": p.last_check,
            }
            for p in providers
        ]
    }


@app.get("/api/providers/presets")
async def get_provider_presets():
    """Get available preset providers that can be added."""
    return {"presets": provider_service.get_available_presets()}


@app.post("/api/providers")
async def add_provider(
    name: str,
    provider_type: str,
    api_base: str,
    api_key: str = "",
):
    """Add a new API provider."""
    from .models import APIProviderType
    
    try:
        ptype = APIProviderType(provider_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid provider type: {provider_type}")
    
    provider = provider_service.add_provider(name, ptype, api_base, api_key)
    return {"provider": provider.model_dump(exclude={"api_key"})}


@app.post("/api/providers/preset/{preset_key}")
async def add_preset_provider(preset_key: str, api_key: str = ""):
    """Add a preset provider (openai, anthropic, groq, etc.)."""
    provider = provider_service.add_preset_provider(preset_key, api_key)
    if not provider:
        raise HTTPException(status_code=400, detail=f"Unknown preset: {preset_key}")
    
    return {"provider": {
        "id": provider.id,
        "name": provider.name,
        "type": provider.type,
        "api_base": provider.api_base,
        "has_key": bool(provider.api_key),
        "enabled": provider.enabled,
    }}


@app.put("/api/providers/{provider_id}")
async def update_provider(
    provider_id: str,
    name: str = None,
    api_base: str = None,
    api_key: str = None,
    enabled: bool = None,
):
    """Update an API provider."""
    provider = provider_service.update_provider(
        provider_id, name, api_base, api_key, enabled
    )
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    # Clear LLM client cache to pick up new settings
    llm_service.update_client()
    
    return {"provider": {
        "id": provider.id,
        "name": provider.name,
        "type": provider.type,
        "api_base": provider.api_base,
        "has_key": bool(provider.api_key),
        "enabled": provider.enabled,
    }}


@app.delete("/api/providers/{provider_id}")
async def delete_provider(provider_id: str):
    """Delete an API provider."""
    if provider_service.delete_provider(provider_id):
        return {"success": True}
    raise HTTPException(status_code=404, detail="Provider not found")


@app.post("/api/providers/{provider_id}/toggle")
async def toggle_provider(provider_id: str):
    """Toggle provider enabled/disabled status."""
    provider = provider_service.toggle_provider(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    return {"enabled": provider.enabled}


@app.post("/api/providers/{provider_id}/test")
async def test_provider(provider_id: str):
    """Test provider connection and fetch models."""
    result = await provider_service.test_provider(provider_id)
    return result


# ============ Sessions Endpoints ============

@app.get("/api/sessions")
async def get_sessions():
    """Get all chat sessions."""
    sessions = session_service.get_all_sessions()
    return {"sessions": [s.model_dump(mode="json") for s in sessions]}


@app.post("/api/sessions")
async def create_session(request: SessionCreate):
    """Create a new chat session."""
    session = session_service.create_session(
        name=request.name,
        model=request.model,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        system_prompt=request.system_prompt,
    )
    return session.model_dump(mode="json")


@app.get("/api/sessions/search")
async def search_sessions(q: str):
    """Search sessions by content."""
    results = session_service.search_sessions(q)
    return {"sessions": [s.model_dump(mode="json") for s in results]}


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Get a specific session."""
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.model_dump(mode="json")


@app.put("/api/sessions/{session_id}")
async def update_session(session_id: str, request: SessionUpdate):
    """Update session metadata and parameters."""
    session = session_service.update_session(
        session_id,
        name=request.name,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        system_prompt=request.system_prompt,
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.model_dump(mode="json")


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    if not session_service.delete_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "deleted"}


@app.post("/api/sessions/{session_id}/auto-name")
async def auto_name_session(session_id: str):
    """Auto-generate session name based on first message."""
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not session.messages:
        raise HTTPException(status_code=400, detail="Session has no messages")
    
    # Get first user message
    first_message = next(
        (m.content for m in session.messages if m.role == MessageRole.USER),
        None
    )
    
    if not first_message:
        raise HTTPException(status_code=400, detail="No user message found")
    
    # Generate name using LLM
    new_name = await llm_service.generate_session_name(first_message, session.model)
    
    # Update session
    session_service.update_session(session_id, name=new_name)
    
    return {"name": new_name}


@app.get("/api/sessions/{session_id}/export")
async def export_session(session_id: str, format: str = "md"):
    """Export session in markdown or JSON format."""
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if format.lower() == "json":
        # Export as JSON
        content = json.dumps(session.model_dump(mode="json"), indent=2, default=str)
        filename = f"{session.name.replace(' ', '_')}.json"
        media_type = "application/json"
    else:
        # Export as Markdown
        lines = [
            f"# {session.name}",
            f"",
            f"**Model:** {session.model}",
            f"**Created:** {session.created_at.strftime('%Y-%m-%d %H:%M')}",
            f"**Messages:** {len(session.messages)}",
            f"",
            f"---",
            f"",
        ]
        
        for msg in session.messages:
            role = "👤 **User**" if msg.role.value == "user" else "🤖 **Assistant**"
            timestamp = msg.timestamp.strftime("%H:%M")
            lines.append(f"### {role} ({timestamp})")
            lines.append(f"")
            lines.append(msg.content)
            lines.append(f"")
            
            if msg.sources:
                lines.append(f"**Sources:**")
                for source in msg.sources:
                    lines.append(f"- [{source.get('title', 'Link')}]({source.get('url', '#')})")
                lines.append(f"")
        
        content = "\n".join(lines)
        filename = f"{session.name.replace(' ', '_')}.md"
        media_type = "text/markdown"
    
    return StreamingResponse(
        iter([content]),
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        }
    )


# ============ Chat Endpoints ============

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Send a chat message and get a response."""
    session = session_service.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Add user message
    session_service.add_message(request.session_id, MessageRole.USER, request.message)
    
    sources = []
    context = ""
    
    # Search if enabled
    if request.enable_search:
        try:
            search_results = await search_service.search(
                request.message,
                provider=request.search_provider,
            )
            sources.extend(search_results)
            context += "\n\nSearch Results:\n"
            for i, result in enumerate(search_results, 1):
                context += f"{i}. {result['title']}: {result['snippet']}\n"
        except Exception as e:
            print(f"Search error: {e}")
    
    # RAG if enabled
    if request.enable_rag:
        rag_results = rag_service.search(request.message)
        for result in rag_results:
            sources.append({
                "title": result["metadata"].get("source", "Document"),
                "url": result["metadata"].get("source", ""),
                "snippet": result["content"][:200],
            })
            context += f"\n\nFrom document {result['metadata'].get('source', 'unknown')}:\n{result['content']}\n"
    
    # Use session's system prompt or override
    system_prompt = request.system_prompt or session.system_prompt
    if context:
        system_prompt += f"\n\nUse the following context to answer the user's question:\n{context}"
    
    # Get messages history
    messages = session_service.get_messages(request.session_id)
    
    # Use session parameters or request overrides
    temperature = request.temperature if request.temperature is not None else session.temperature
    max_tokens = request.max_tokens if request.max_tokens is not None else session.max_tokens
    
    # Generate response
    try:
        response_content, tokens_used = await llm_service.chat_completion(
            messages=messages,
            model=request.model,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # Add assistant message
    assistant_message = session_service.add_message(
        request.session_id,
        MessageRole.ASSISTANT,
        response_content,
        sources if sources else None,
        token_count=tokens_used,
    )
    
    return {
        "message": assistant_message.model_dump(mode="json"),
        "sources": sources if sources else None,
        "tokens_used": tokens_used,
    }


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """Send a chat message and get a streaming response."""
    session = session_service.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Add user message
    session_service.add_message(request.session_id, MessageRole.USER, request.message)
    
    sources = []
    context = ""
    
    # Search if enabled
    if request.enable_search:
        try:
            search_results = await search_service.search(
                request.message,
                provider=request.search_provider,
            )
            sources.extend(search_results)
            context += "\n\nSearch Results:\n"
            for i, result in enumerate(search_results, 1):
                context += f"{i}. {result['title']}: {result['snippet']}\n"
        except Exception as e:
            print(f"Search error: {e}")
    
    # RAG if enabled
    if request.enable_rag:
        rag_results = rag_service.search(request.message)
        for result in rag_results:
            sources.append({
                "title": result["metadata"].get("source", "Document"),
                "url": result["metadata"].get("source", ""),
                "snippet": result["content"][:200],
            })
            context += f"\n\nFrom document {result['metadata'].get('source', 'unknown')}:\n{result['content']}\n"
    
    # Use session's system prompt or override
    system_prompt = request.system_prompt or session.system_prompt
    if context:
        system_prompt += f"\n\nUse the following context to answer the user's question:\n{context}"
    
    messages = session_service.get_messages(request.session_id)
    
    # Use session parameters or request overrides
    temperature = request.temperature if request.temperature is not None else session.temperature
    max_tokens = request.max_tokens if request.max_tokens is not None else session.max_tokens
    
    async def generate():
        full_response = ""
        
        # Send sources first if any
        if sources:
            yield f"data: {json.dumps({'type': 'sources', 'data': sources})}\n\n"
        
        async for chunk in llm_service.chat_completion_stream(
            messages=messages,
            model=request.model,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        ):
            full_response += chunk
            yield f"data: {json.dumps({'type': 'content', 'data': chunk})}\n\n"
        
        # Save the complete response
        session_service.add_message(
            request.session_id,
            MessageRole.ASSISTANT,
            full_response,
            sources if sources else None,
        )
        
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


class RegenerateRequest(BaseModel):
    """Request to regenerate a response."""
    message_id: str


class EditMessageRequest(BaseModel):
    """Request to edit a message."""
    content: str


@app.put("/api/sessions/{session_id}/messages/{message_id}")
async def edit_message(session_id: str, message_id: str, request: EditMessageRequest):
    """Edit a message content."""
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    updated_message = session_service.update_message(session_id, message_id, request.content)
    if not updated_message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    return {"message": updated_message.model_dump(mode="json")}


@app.post("/api/chat/{session_id}/regenerate")
async def regenerate_response(session_id: str, request: RegenerateRequest):
    """Regenerate a response for a given message."""
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Find the message to regenerate
    msg_index = None
    for i, msg in enumerate(session.messages):
        if msg.id == request.message_id:
            msg_index = i
            break
    
    if msg_index is None:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # The message to regenerate should be an assistant message
    if session.messages[msg_index].role != MessageRole.ASSISTANT:
        raise HTTPException(status_code=400, detail="Can only regenerate assistant messages")
    
    # Find the preceding user message
    user_msg_index = msg_index - 1
    while user_msg_index >= 0 and session.messages[user_msg_index].role != MessageRole.USER:
        user_msg_index -= 1
    
    if user_msg_index < 0:
        raise HTTPException(status_code=400, detail="No user message found before this response")
    
    user_message = session.messages[user_msg_index].content
    
    # Remove the old assistant message
    session_service.remove_message(session_id, request.message_id)
    
    # Get updated messages (excluding the removed message)
    messages = session_service.get_messages(session_id)
    
    # Generate new response
    system_prompt = session.system_prompt
    
    try:
        response_content, tokens_used = await llm_service.chat_completion(
            messages=messages,
            model=session.model,
            system_prompt=system_prompt,
            temperature=session.temperature,
            max_tokens=session.max_tokens,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # Add new assistant message
    new_message = session_service.add_message(
        session_id,
        MessageRole.ASSISTANT,
        response_content,
        token_count=tokens_used,
    )
    
    return {
        "message": new_message.model_dump(mode="json"),
        "tokens_used": tokens_used,
    }


# ============ Search Endpoints ============

@app.post("/api/search/test")
async def test_search(query: str, provider: SearchProvider = SearchProvider.DUCKDUCKGO):
    """Test search functionality."""
    results = await search_service.search(query, provider)
    return {"results": results}


@app.post("/api/settings/search")
async def update_search_settings(settings_req: SearchSettings):
    """Update search settings."""
    return {"status": "updated", "settings": settings_req.model_dump()}


# ============ Preset Endpoints ============

@app.get("/api/presets")
async def get_presets(category: str = None):
    """Get all presets, optionally filtered by category."""
    if category:
        presets = preset_service.get_presets_by_category(category)
    else:
        presets = preset_service.get_all_presets()
    return {"presets": [p.model_dump() for p in presets]}


@app.get("/api/presets/categories")
async def get_preset_categories():
    """Get all preset categories."""
    categories = preset_service.get_categories()
    return {"categories": categories}


@app.get("/api/presets/{preset_id}")
async def get_preset(preset_id: str):
    """Get a specific preset by ID."""
    preset = preset_service.get_preset(preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    return preset.model_dump()


@app.post("/api/presets")
async def create_preset(request: PresetCreate):
    """Create a new custom preset."""
    preset = preset_service.create_preset(
        name=request.name,
        description=request.description,
        system_prompt=request.system_prompt,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        icon=request.icon,
        category=request.category,
    )
    return preset.model_dump()


@app.delete("/api/presets/{preset_id}")
async def delete_preset(preset_id: str):
    """Delete a custom preset."""
    # Don't allow deleting built-in presets
    preset = preset_service.get_preset(preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    if not preset_id.startswith("custom_"):
        raise HTTPException(status_code=400, detail="Cannot delete built-in presets")
    
    if preset_service.delete_preset(preset_id):
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Preset not found")


# ============ RAG Endpoints ============

@app.get("/api/rag/files")
async def get_rag_files():
    """Get indexed files."""
    files = rag_service.get_indexed_files()
    return {"files": files}


@app.post("/api/rag/index")
async def index_directory(request: RAGIndexRequest):
    """Index a directory for RAG."""
    try:
        result = await rag_service.index_directory(request.directory_path)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/rag/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload and index a file for RAG."""
    # Validate file type
    allowed_extensions = {".txt", ".md", ".py", ".js", ".ts", ".json", ".pdf"}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Save file
    file_path = upload_dir / file.filename
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    # Index the file
    try:
        await rag_service.index_directory(str(upload_dir))
        return {
            "filename": file.filename,
            "size": file_path.stat().st_size,
            "indexed": True,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/rag/directory")
async def remove_directory(directory_path: str):
    """Remove a directory from RAG index."""
    if rag_service.remove_directory(directory_path):
        return {"status": "removed"}
    raise HTTPException(status_code=404, detail="Directory not found")


# ============ Image Generation Endpoints ============

@app.get("/api/images/status")
async def get_image_status():
    """Check if image generation is configured."""
    return {"configured": image_service.is_configured()}


@app.post("/api/images/generate")
async def generate_image(request: ImageGenerateRequest):
    """Generate an image using DALL-E."""
    if not image_service.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Image generation not configured. Set OPENAI_DALLE_KEY environment variable."
        )
    
    try:
        result = await image_service.generate_image(
            prompt=request.prompt,
            size=request.size,
            quality=request.quality,
            style=request.style,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/images")
async def get_images():
    """Get list of generated images."""
    images = image_service.get_generated_images()
    return {"images": images}


# ============ YouTube Endpoints ============

@app.post("/api/youtube/summarize")
async def summarize_youtube(request: YouTubeSummaryRequest):
    """Summarize a YouTube video."""
    try:
        # Get first available model
        models = await llm_service.get_available_models()
        if not models:
            raise HTTPException(status_code=500, detail="No models available")
        
        model = models[0]["id"]
        
        result = await youtube_service.summarize_video(
            url=request.url,
            llm_service=llm_service,
            model=model,
            language=request.language,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ Deep Research Endpoints ============

@app.post("/api/research")
async def deep_research(request: DeepResearchRequest):
    """Conduct deep research on a topic."""
    try:
        # Get first available model
        models = await llm_service.get_available_models()
        if not models:
            raise HTTPException(status_code=500, detail="No models available")
        
        model = models[0]["id"]
        
        report = await deep_research_service.conduct_research(
            query=request.query,
            search_service=search_service,
            llm_service=llm_service,
            model=model,
            max_iterations=request.max_iterations,
            search_provider=request.search_provider,
        )
        
        return {
            "query": report.original_query,
            "summary": report.final_summary,
            "sources": report.sources,
            "iterations": len(report.steps),
            "total_sources": report.total_sources_analyzed,
            "duration_seconds": report.duration_seconds,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ Model Comparison Endpoints ============

class CompareChatRequest(BaseModel):
    """Request for model comparison."""
    messages: List[dict]
    model: str


@app.post("/api/compare/chat")
async def compare_chat(request: CompareChatRequest):
    """Generate a chat completion for model comparison."""
    try:
        # Convert to message format for LLM service
        messages = [
            {"role": m["role"], "content": m["content"]}
            for m in request.messages
        ]
        
        response_content, tokens_used = await llm_service.chat_completion(
            messages=messages,
            model=request.model,
            temperature=0.7,
            max_tokens=2048,
        )
        
        return {
            "content": response_content,
            "tokens_used": tokens_used,
            "model": request.model,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/research/stream")
async def deep_research_stream(request: DeepResearchRequest):
    """Conduct deep research with streaming progress updates."""
    # Get first available model
    models = await llm_service.get_available_models()
    if not models:
        raise HTTPException(status_code=500, detail="No models available")
    
    model = models[0]["id"]
    
    async def generate():
        progress_queue = []
        
        async def progress_callback(update):
            progress_queue.append(update)
        
        # Start research in background
        import asyncio
        research_task = asyncio.create_task(
            deep_research_service.conduct_research(
                query=request.query,
                search_service=search_service,
                llm_service=llm_service,
                model=model,
                max_iterations=request.max_iterations,
                search_provider=request.search_provider,
                progress_callback=progress_callback,
            )
        )
        
        # Stream progress updates
        while not research_task.done():
            while progress_queue:
                update = progress_queue.pop(0)
                yield f"data: {json.dumps(update)}\n\n"
            await asyncio.sleep(0.1)
        
        # Get final result
        report = await research_task
        
        yield f"data: {json.dumps({'type': 'complete', 'data': {'query': report.original_query, 'summary': report.final_summary, 'sources': report.sources, 'iterations': len(report.steps), 'total_sources': report.total_sources_analyzed, 'duration_seconds': report.duration_seconds}})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


# ============ TTS Endpoints ============

@app.post("/api/tts")
async def text_to_speech(request: TTSRequest):
    """Convert text to speech (placeholder - requires TTS backend)."""
    # This is a placeholder. For actual TTS, you would need to integrate with:
    # - OpenAI TTS API
    # - Coqui TTS
    # - ElevenLabs
    # - Or local TTS like piper
    return {
        "status": "not_implemented",
        "message": "TTS requires additional backend setup. Configure a TTS provider in settings.",
        "text_length": len(request.text),
    }


# ============ Usage & Stats Endpoints ============

@app.get("/api/usage")
async def get_usage():
    """Get usage statistics."""
    session_usage = session_service.get_total_usage()
    llm_usage = llm_service.get_usage_stats()
    
    return {
        "sessions": session_usage,
        "llm": llm_usage,
    }


# ============ Config Endpoints ============

@app.get("/api/config")
async def get_config():
    """Get current configuration."""
    return {
        "api_base": settings.openai_api_base,
        "has_brave_key": bool(settings.brave_api_key),
        "has_searxng": bool(settings.searxng_url),
    }


@app.put("/api/config")
async def update_config(request: Request):
    """Update configuration."""
    data = await request.json()
    
    if "api_base" in data:
        settings.openai_api_base = data["api_base"]
        llm_service.update_client()
    if "api_key" in data:
        settings.openai_api_key = data["api_key"]
        llm_service.update_client()
    if "brave_api_key" in data:
        settings.brave_api_key = data["brave_api_key"]
    if "searxng_url" in data:
        settings.searxng_url = data["searxng_url"]
    
    return {"status": "updated"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
