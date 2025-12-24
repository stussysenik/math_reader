from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import time
import chromadb
from chromadb.config import Settings
import logging

# Setup Logging
logger = logging.getLogger("memory_engine")

# --- Schemas ---

class MemoryNode(BaseModel):
    """Represents a learned concept, theorem, or definition."""
    node_id: str = Field(..., description="Unique ID of the node")
    text: str = Field(..., description="The content text")
    source_chapter: int = Field(..., description="Chapter context")
    page_number: int = Field(..., description="Page number")
    node_type: str = Field("concept", description="theorem, definition, example, etc.")
    embedding: Optional[List[float]] = None
    created_at: float = Field(default_factory=time.time)

class ContextQuery(BaseModel):
    """Query context for retrieval."""
    current_text: str
    current_chapter: int
    limit: int = 5

# --- Core Logic ---

class MemoryEngine:
    def __init__(self, db_path: str = "./data/db/chroma_db"):
        self.client = chromadb.PersistentClient(path=db_path, settings=Settings(allow_reset=True))
        self.collection = self.client.get_or_create_collection(name="math_memory")
        logger.info(f"Memory Engine initialized at {db_path}")

    def add_node(self, node: MemoryNode):
        """Adds a memory node to the vector store."""
        # In a real app, we'd generate embedding here if None using Ollama
        # For now, we assume embedding is handled by the embedding service or allow Chroma's default
        self.collection.add(
            documents=[node.text],
            metadatas=[{
                "source_chapter": node.source_chapter,
                "page_number": node.page_number,
                "node_type": node.node_type,
                "created_at": node.created_at
            }],
            ids=[node.node_id]
        )
        logger.info(f"Added node {node.node_id} to memory.")

    def retrieve_context(self, query: ContextQuery) -> List[MemoryNode]:
        """
        Retrieves relevant nodes from PREVIOUS chapters/context.
        The 'Preserved Thinking' core: only fetch things we've already 'read'.
        """
        # Filter: source_chapter < current_chapter (or <= if we want current chapter context)
        # ChromaDB where filter
        results = self.collection.query(
            query_texts=[query.current_text],
            n_results=query.limit,
            where={"source_chapter": {"$lt": query.current_chapter}} 
        )

        nodes = []
        if results['ids']:
            for i, id_ in enumerate(results['ids'][0]):
                meta = results['metadatas'][0][i]
                nodes.append(MemoryNode(
                    node_id=id_,
                    text=results['documents'][0][i],
                    source_chapter=meta['source_chapter'],
                    page_number=meta['page_number'],
                    node_type=meta['node_type'],
                    created_at=meta['created_at']
                ))
        
        return nodes

    def get_chapter_summary(self, chapter: int) -> str:
        """Simple retrieval of all nodes in a chapter (for inspection)."""
        results = self.collection.get(
            where={"source_chapter": chapter}
        )
        return f"Chapter {chapter} has {len(results['ids'])} memory nodes."
