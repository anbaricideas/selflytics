"""Minimal FastAPI application for spike validation."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from spike.chat_agent import run_chat

app = FastAPI(title="Selflytics Spike")

# CORS for local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    user_id: str = "spike-user"


class ChatResponse(BaseModel):
    response: str
    sources: list[str]


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "selflytics-spike"}


@app.post("/chat")
async def chat(request: ChatRequest):
    """Chat endpoint with Pydantic-AI agent."""
    response = await run_chat(request.message, request.user_id)
    return response


@app.get("/auth/garmin")
async def garmin_auth():
    """Initiate Garmin OAuth flow - will implement in Step 3."""
    raise HTTPException(status_code=501, detail="Not implemented in spike")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
