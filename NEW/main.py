import uvicorn
from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from langchain.schema import HumanMessage
from agents.router_agent import router_executor

load_dotenv()

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

@app.post("/api/chat")
async def chat_endpoint(query: str):
    try:
        response = router_executor.invoke({"input": query})
        return {"response": response}
    except Exception as e:
        logger.error(f"Error during chat invocation: {e}")
        return {"error": str(e)}, 500

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
