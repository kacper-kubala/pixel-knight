"""Session management service with PostgreSQL and JSON fallback support."""
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import uuid
import asyncio

from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from ..models import ChatSession, ChatMessage, MessageRole
from ..database import (
    get_db_session, 
    DBSession, 
    DBMessage, 
    init_db, 
    is_db_configured,
    check_db_available,
)


class SessionService:
    """Service for managing chat sessions with PostgreSQL or JSON fallback."""
    
    def __init__(self):
        self.sessions: Dict[str, ChatSession] = {}
        self.data_dir = Path("./data/sessions")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._use_db = False
        self._initialized = False
    
    async def initialize(self):
        """Initialize the service - check database availability."""
        if self._initialized:
            return
        
        if is_db_configured():
            try:
                await init_db()
                self._use_db = await check_db_available()
                if self._use_db:
                    print("Using PostgreSQL database for sessions")
                else:
                    print("PostgreSQL not available, falling back to JSON storage")
                    self._load_sessions_from_json()
            except Exception as e:
                print(f"Database initialization error: {e}")
                self._use_db = False
                self._load_sessions_from_json()
        else:
            print("Using JSON storage for sessions (PostgreSQL not configured)")
            self._load_sessions_from_json()
        
        self._initialized = True
    
    def _ensure_initialized(self):
        """Ensure service is initialized (sync wrapper)."""
        if not self._initialized:
            # Load from JSON as fallback for sync initialization
            self._load_sessions_from_json()
            self._initialized = True
    
    def _load_sessions_from_json(self):
        """Load sessions from JSON files."""
        for session_file in self.data_dir.glob("*.json"):
            try:
                with open(session_file) as f:
                    data = json.load(f)
                    session = ChatSession(**data)
                    self.sessions[session.id] = session
            except Exception as e:
                print(f"Error loading session {session_file}: {e}")
    
    def _save_session_to_json(self, session: ChatSession):
        """Save session to JSON file."""
        session_file = self.data_dir / f"{session.id}.json"
        with open(session_file, "w") as f:
            json.dump(session.model_dump(mode="json"), f, default=str)
    
    def _delete_session_json(self, session_id: str):
        """Delete session JSON file."""
        session_file = self.data_dir / f"{session_id}.json"
        if session_file.exists():
            session_file.unlink()
    
    # ============ Sync methods (JSON fallback) ============
    
    def create_session(
        self,
        name: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        system_prompt: str = "You are a helpful AI assistant."
    ) -> ChatSession:
        """Create a new chat session (sync - JSON only)."""
        self._ensure_initialized()
        
        session = ChatSession(
            id=str(uuid.uuid4()),
            name=name,
            model=model,
            messages=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt,
            total_tokens_used=0,
        )
        self.sessions[session.id] = session
        self._save_session_to_json(session)
        return session
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get session by ID (sync)."""
        self._ensure_initialized()
        return self.sessions.get(session_id)
    
    def get_all_sessions(self) -> List[ChatSession]:
        """Get all sessions sorted by update time (sync)."""
        self._ensure_initialized()
        sessions = list(self.sessions.values())
        sessions.sort(key=lambda s: s.updated_at, reverse=True)
        return sessions
    
    def update_session(
        self,
        session_id: str,
        name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
    ) -> Optional[ChatSession]:
        """Update session metadata (sync)."""
        self._ensure_initialized()
        session = self.sessions.get(session_id)
        if session:
            if name is not None:
                session.name = name
            if temperature is not None:
                session.temperature = temperature
            if max_tokens is not None:
                session.max_tokens = max_tokens
            if system_prompt is not None:
                session.system_prompt = system_prompt
            session.updated_at = datetime.now()
            self._save_session_to_json(session)
        return session
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session (sync)."""
        self._ensure_initialized()
        if session_id in self.sessions:
            del self.sessions[session_id]
            self._delete_session_json(session_id)
            return True
        return False
    
    def add_message(
        self,
        session_id: str,
        role: MessageRole,
        content: str,
        sources: Optional[List[Dict]] = None,
        token_count: Optional[int] = None,
    ) -> Optional[ChatMessage]:
        """Add a message to a session (sync)."""
        self._ensure_initialized()
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        message = ChatMessage(
            id=str(uuid.uuid4()),
            role=role,
            content=content,
            timestamp=datetime.now(),
            sources=sources,
            token_count=token_count,
        )
        session.messages.append(message)
        session.updated_at = datetime.now()
        
        if token_count:
            session.total_tokens_used += token_count
        
        self._save_session_to_json(session)
        return message
    
    def get_messages(self, session_id: str) -> List[ChatMessage]:
        """Get all messages for a session (sync)."""
        self._ensure_initialized()
        session = self.sessions.get(session_id)
        return session.messages if session else []
    
    def remove_message(self, session_id: str, message_id: str) -> bool:
        """Remove a message from a session (sync)."""
        self._ensure_initialized()
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        original_length = len(session.messages)
        session.messages = [m for m in session.messages if m.id != message_id]
        
        if len(session.messages) < original_length:
            session.updated_at = datetime.now()
            self._save_session_to_json(session)
            return True
        return False
    
    def update_message(
        self,
        session_id: str,
        message_id: str,
        content: str
    ) -> Optional[ChatMessage]:
        """Update a message content (sync)."""
        self._ensure_initialized()
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        for msg in session.messages:
            if msg.id == message_id:
                msg.content = content
                msg.timestamp = datetime.now()
                session.updated_at = datetime.now()
                self._save_session_to_json(session)
                return msg
        return None
    
    def get_total_usage(self) -> Dict[str, int]:
        """Get total usage across all sessions (sync)."""
        self._ensure_initialized()
        total_tokens = sum(s.total_tokens_used for s in self.sessions.values())
        total_messages = sum(len(s.messages) for s in self.sessions.values())
        return {
            "total_tokens": total_tokens,
            "total_messages": total_messages,
            "total_sessions": len(self.sessions),
        }
    
    def search_sessions(self, query: str) -> List[ChatSession]:
        """Search sessions by message content (sync)."""
        self._ensure_initialized()
        query_lower = query.lower()
        results = []
        
        for session in self.sessions.values():
            # Check session name
            if query_lower in session.name.lower():
                results.append(session)
                continue
            
            # Check messages
            for msg in session.messages:
                if query_lower in msg.content.lower():
                    results.append(session)
                    break
        
        return results
    
    # ============ Async methods (PostgreSQL) ============
    
    async def create_session_async(
        self,
        name: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        system_prompt: str = "You are a helpful AI assistant."
    ) -> ChatSession:
        """Create a new chat session (async - PostgreSQL)."""
        await self.initialize()
        
        if not self._use_db:
            return self.create_session(name, model, temperature, max_tokens, system_prompt)
        
        session_id = str(uuid.uuid4())
        
        async with get_db_session() as db:
            db_session = DBSession(
                id=session_id,
                name=name,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                system_prompt=system_prompt,
            )
            db.add(db_session)
        
        return ChatSession(
            id=session_id,
            name=name,
            model=model,
            messages=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt,
        )
    
    async def get_all_sessions_async(self) -> List[ChatSession]:
        """Get all sessions (async - PostgreSQL)."""
        await self.initialize()
        
        if not self._use_db:
            return self.get_all_sessions()
        
        async with get_db_session() as db:
            result = await db.execute(
                select(DBSession)
                .options(selectinload(DBSession.messages))
                .order_by(DBSession.updated_at.desc())
            )
            db_sessions = result.scalars().all()
            
            return [self._db_to_pydantic(s) for s in db_sessions]
    
    def _db_to_pydantic(self, db_session: DBSession) -> ChatSession:
        """Convert database session to Pydantic model."""
        messages = [
            ChatMessage(
                id=m.id,
                role=MessageRole(m.role),
                content=m.content,
                timestamp=m.timestamp,
                sources=m.sources,
                token_count=m.token_count,
            )
            for m in sorted(db_session.messages, key=lambda x: x.timestamp)
        ]
        
        return ChatSession(
            id=db_session.id,
            name=db_session.name,
            model=db_session.model,
            messages=messages,
            created_at=db_session.created_at,
            updated_at=db_session.updated_at,
            temperature=db_session.temperature,
            max_tokens=db_session.max_tokens,
            system_prompt=db_session.system_prompt,
            total_tokens_used=db_session.total_tokens_used,
        )


session_service = SessionService()
