"""RAG service for document indexing and retrieval."""
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
import json

# We'll use a simple in-memory approach for demo, but can be extended with ChromaDB
from dataclasses import dataclass, field


@dataclass
class Document:
    """A document chunk for RAG."""
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None


class RAGService:
    """Service for RAG operations."""
    
    def __init__(self):
        self.documents: Dict[str, Document] = {}
        self.indexed_directories: Dict[str, List[str]] = {}
        self._load_index()
    
    def _load_index(self):
        """Load indexed directories from disk."""
        index_path = Path("./data/rag_index.json")
        if index_path.exists():
            try:
                with open(index_path) as f:
                    self.indexed_directories = json.load(f)
            except Exception:
                pass
    
    def _save_index(self):
        """Save indexed directories to disk."""
        index_path = Path("./data/rag_index.json")
        index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(index_path, "w") as f:
            json.dump(self.indexed_directories, f)
    
    def get_indexed_files(self) -> List[Dict[str, Any]]:
        """Get list of indexed files."""
        files = []
        for directory, file_list in self.indexed_directories.items():
            for file_path in file_list:
                try:
                    size = os.path.getsize(file_path)
                    files.append({
                        "path": file_path,
                        "size": size,
                        "indexed": True,
                    })
                except Exception:
                    files.append({
                        "path": file_path,
                        "size": 0,
                        "indexed": True,
                    })
        return files
    
    async def index_directory(self, directory_path: str) -> Dict[str, Any]:
        """Index all supported files in a directory."""
        path = Path(directory_path)
        if not path.exists():
            raise ValueError(f"Directory not found: {directory_path}")
        
        supported_extensions = {".txt", ".md", ".py", ".js", ".ts", ".json", ".pdf"}
        indexed_files = []
        
        for file_path in path.rglob("*"):
            if file_path.is_file() and file_path.suffix in supported_extensions:
                try:
                    content = self._read_file(file_path)
                    if content:
                        doc_id = str(file_path)
                        self.documents[doc_id] = Document(
                            id=doc_id,
                            content=content,
                            metadata={
                                "source": str(file_path),
                                "type": file_path.suffix,
                            }
                        )
                        indexed_files.append(str(file_path))
                except Exception as e:
                    print(f"Error indexing {file_path}: {e}")
        
        self.indexed_directories[directory_path] = indexed_files
        self._save_index()
        
        return {
            "directory": directory_path,
            "files_indexed": len(indexed_files),
            "files": indexed_files,
        }
    
    def _read_file(self, file_path: Path) -> str:
        """Read content from a file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""
    
    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Simple keyword search (can be replaced with vector search)."""
        results = []
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        for doc_id, doc in self.documents.items():
            content_lower = doc.content.lower()
            
            # Simple relevance scoring based on word matches
            score = sum(1 for word in query_words if word in content_lower)
            
            if score > 0:
                # Extract relevant snippet
                snippet = self._extract_snippet(doc.content, query_words)
                results.append({
                    "id": doc_id,
                    "content": snippet,
                    "metadata": doc.metadata,
                    "score": score,
                })
        
        # Sort by score and return top_k
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
    
    def _extract_snippet(self, content: str, query_words: set, context_chars: int = 200) -> str:
        """Extract a relevant snippet from content."""
        content_lower = content.lower()
        
        # Find the first occurrence of any query word
        best_pos = len(content)
        for word in query_words:
            pos = content_lower.find(word)
            if 0 <= pos < best_pos:
                best_pos = pos
        
        if best_pos == len(content):
            return content[:context_chars * 2]
        
        start = max(0, best_pos - context_chars)
        end = min(len(content), best_pos + context_chars)
        
        snippet = content[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."
        
        return snippet
    
    def remove_directory(self, directory_path: str) -> bool:
        """Remove a directory from the index."""
        if directory_path in self.indexed_directories:
            files = self.indexed_directories[directory_path]
            for file_path in files:
                if file_path in self.documents:
                    del self.documents[file_path]
            del self.indexed_directories[directory_path]
            self._save_index()
            return True
        return False


rag_service = RAGService()

