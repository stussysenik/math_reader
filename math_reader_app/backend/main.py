from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import time
import uvicorn
import logging

from core.memory import MemoryEngine, MemoryNode, ContextQuery
from core.llm_gateway import gateway, GenerationRequest
from core.tracker import tracker, ProgressState

# Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main_api")

app = FastAPI(title="Math Reader AI", version="0.1")
memory = MemoryEngine()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class IngestRequest(BaseModel):
    text: str
    chapter: int
    page: int
    doc_id: str

class QueryRequest(BaseModel):
    selected_text: str
    current_chapter: int
    current_page: int
    prompt_override: str = None

@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": time.time(), "modules": ["memory", "gateway", "tracker"]}

@app.get("/progress/{book_id}")
async def get_progress(book_id: str):
    return tracker.get_progress(book_id)

@app.post("/progress")
async def update_progress(state: ProgressState):
    """Update reading progress."""
    return tracker.update_progress(state.book_id, state.current_chapter, state.current_page)

@app.post("/ingest")
async def ingest_chunk(req: IngestRequest):
    """Ingest a chunk of text into memory (simulate 'reading' it)."""
    node = MemoryNode(
        node_id=f"{req.doc_id}_c{req.chapter}_p{req.page}_{int(time.time())}",
        text=req.text,
        source_chapter=req.chapter,
        page_number=req.page,
        node_type="text_chunk"
    )
    memory.add_node(node)
    return {"status": "ingested", "node_id": node.node_id}

@app.post("/generate")
async def generate_insight(req: QueryRequest):
    """
    Generate insight for selected text.
    1. Retrieve context from PREVIOUS chapters.
    2. Stream LLM response.
    """
    start_time = time.time()
    
    # 1. Retrieval
    context_nodes = memory.retrieve_context(ContextQuery(
        current_text=req.selected_text,
        current_chapter=req.current_chapter
    ))
    
    logger.info(f"Retrieved {len(context_nodes)} context nodes in {time.time() - start_time:.4f}s")
    
    # 2. Generation
    prompt = req.prompt_override or f"Explain this concept: '{req.selected_text}'. Connect it to previous chapters if possible."
    
    gen_req = GenerationRequest(
        prompt=prompt,
        context_nodes=[n.dict() for n in context_nodes]
    )
    
    async def stream_generator():
        # First yield metadata event with FULL context for the "Thinking Cache" debug view
        import json
        meta_payload = {
            "latency_overhead": (time.time() - start_time) * 1000,
            "context_count": len(context_nodes),
            "context_nodes": [n.dict() for n in context_nodes]
        }
        yield f"event: meta\ndata: {json.dumps(meta_payload)}\n\n"
        
        async for chunk in gateway.generate_stream(gen_req):
            yield f"event: token\ndata: {chunk}\n\n"
            
        yield "event: done\ndata: [DONE]\n\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
