import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import json

from agents.router_agent import router_executor  

# Initialize FastAPI app
app = FastAPI(
    title="Helios Dynamics ERP Agent API",
    description="A backend API that uses a router agent to handle and delegate ERP-related queries.",
    version="1.0.0",
)

# Configure CORS to allow Streamlit frontend
origins = [
    "http://localhost",
    "http://localhost:8501",  # Streamlit default
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class ChatRequest(BaseModel):
    prompt: str

class ChatResponse(BaseModel):
    response: str
    chart_spec: Optional[Dict[str, Any]] = None

# Chat endpoint
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Handles user prompts by routing them to the router agent.
    """
    try:
        # Use invoke() instead of run() for AgentExecutor
        agent_output = router_executor.invoke(request.prompt)
        
        # router_executor.invoke returns a dict: {"output": "text"}
        response_text = agent_output.get("output", "")
        
        # Optional: parse chart_spec if returned as JSON
        chart_spec = None
        if "chart_spec" in response_text:
            try:
                chart_spec = json.loads(response_text.split("chart_spec:")[1].strip())
            except Exception:
                pass

        return ChatResponse(response=response_text, chart_spec=chart_spec)
    
    except Exception as e:
        return ChatResponse(response=f"An error occurred: {str(e)}", chart_spec=None)

# Run via uvicorn: uvicorn main:app --reload
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
