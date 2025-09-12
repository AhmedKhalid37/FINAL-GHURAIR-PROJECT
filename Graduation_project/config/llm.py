from langchain_google_genai import ChatGoogleGenerativeAI
import os


def get_llm():
    """Get configured LLM instance -general- (Gemini 1.5 Flash)"""
    api_key = os.getenv("GOOGLE_API_KEY")  # TODO: set via environment, do not hardcode
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY not set. Export it in your environment.")
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0.1,
        google_api_key=api_key,
    )


def get_router_llm():
    """Get LLM for router decisions (deterministic)"""
    api_key = os.getenv("GOOGLE_API_KEY")  # TODO: set via environment, do not hardcode
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY not set. Export it in your environment.")
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0.0,
        google_api_key=api_key,
    )
