import uvicorn
import logging
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage
# Lazy import to avoid heavy deps and env checks at startup
router_executor = None

load_dotenv()

logger = logging.getLogger("backend")
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Helios Dynamics Agent-Driven ERP",
    description="Backend API for the agent-driven ERP system.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Helios Dynamics ERP API!"}

class ChatRequest(BaseModel):
    prompt: str


@app.post("/api/chat")
async def chat_endpoint(payload: ChatRequest):
    try:
        global router_executor
        if router_executor is None:
            from agents.router_agent import router_executor as _rexec
            router_executor = _rexec
        result = router_executor.invoke({"input": payload.prompt})
        # AgentExecutor returns a dict with 'output'
        if isinstance(result, dict) and "output" in result:
            return {"response": result["output"]}
        return {"response": result}
    except Exception as e:
        logger.error(f"Error during chat invocation: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
