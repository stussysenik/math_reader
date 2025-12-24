import asyncio
from typing import AsyncGenerator, Dict, Any, Optional
import ollama
from pydantic import BaseModel
import logging
import time

logger = logging.getLogger("llm_gateway")

class GenerationRequest(BaseModel):
    prompt: str
    model: str = "glm-4.7" # Default desired model
    fallback_model: str = "llama3.2" # Local fallback
    stream: bool = True
    context_nodes: list = [] # Memory nodes to inject

class LLMGateway:
    def __init__(self):
        self.primary_api_healthy = True # Simple circuit breaker state
        self.last_failure_time = 0.0

    async def generate_stream(self, request: GenerationRequest) -> AsyncGenerator[str, None]:
        """
        Generates text stream. Tries primary API first, falls back to Local Ollama.
        """
        
        # Construct the "Preserved Thinking" prompt
        context_str = "\n".join([f"[Chapter {n['source_chapter']}] {n['text']}" for n in request.context_nodes])
        full_system_prompt = f"""You are an expert Math Tutor. 
        Your memory retrieval system shows you've previously learned:
        {context_str}
        
        Use this context to answer the user's query about the current text via the 'Margin is the Model' method.
        Keep answers concise, insightful, and formatted for a narrow margin."""
        
        full_prompt = f"{full_system_prompt}\n\nUser: {request.prompt}"

        # 1. Try Primary API (Mocked for now as we don't have keys)
        # In real impl, this would be an HTTP call to Z.ai or OpenAI
        try:
            if not self.primary_api_healthy and (time.time() - self.last_failure_time < 60):
                raise Exception("Circuit breaker open")
                
            # Simulate API call (replace with real implementation)
            # await real_api_call(full_prompt)
            # yield "API Response..."
            
            # For this MVP, we default to "Simulated Failure" to test Fallback immediately
            # or just go straight to Ollama if user asked for "fastest/local" option
            raise Exception("API not configured, falling back")

        except Exception as e:
            logger.warning(f"Primary API failed: {e}. Switching to Ollama ({request.fallback_model})")
            self.primary_api_healthy = False
            self.last_failure_time = time.time()
            
            # 2. Fallback to Local Ollama
            try:
                # wrapper for async/sync ollama
                stream = ollama.chat(
                    model=request.fallback_model,
                    messages=[{'role': 'user', 'content': full_prompt}],
                    stream=True
                )
                
                for chunk in stream:
                    content = chunk['message']['content']
                    yield content
                    # Small sleep to simulate network variability if needed, 
                    # but for local we want max speed.
                    await asyncio.sleep(0) 

            except Exception as local_e:
                logger.error(f"Ollama failed: {local_e}")
                # Fallback to Mock for Demo purposes if no local LLM found
                mock_response = f" [Mock AI] retrieving context... Found related theorem from Chapter {request.context_nodes[0]['source_chapter'] if request.context_nodes else '?'}. The Mean Value Theorem generalizes the result from Chapter 1. It states that for a continuous function..."
                
                tokens = mock_response.split(" ")
                for token in tokens:
                    yield token + " "
                    await asyncio.sleep(0.05) # Simulate typing speed


gateway = LLMGateway()
