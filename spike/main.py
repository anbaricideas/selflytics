"""Minimal FastAPI application for spike validation."""

import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from spike.chat_agent import run_chat
from spike.viz_generator import VizGenerator

app = FastAPI(title="Selflytics Spike")
viz_gen = VizGenerator()

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


@app.get("/viz/{viz_id}")
async def get_visualization(viz_id: str):
    """Serve generated visualization."""
    viz_path = Path(f"spike/cache/viz_{viz_id}.png")
    if not viz_path.exists():
        raise HTTPException(status_code=404, detail="Visualization not found")
    return FileResponse(viz_path, media_type="image/png")


@app.post("/generate-viz")
async def generate_viz():
    """Test endpoint for visualization generation (spike validation)."""
    # Mock data: pace over 7 days
    data = [
        ("Nov 4", 6.30),
        ("Nov 5", 6.25),
        ("Nov 6", 6.15),
        ("Nov 7", 6.20),
        ("Nov 8", 6.10),
        ("Nov 9", 6.05),
        ("Nov 10", 6.00),
    ]

    start = time.time()
    viz_id = viz_gen.generate_line_chart(
        data=data,
        title="Running Pace - Last 7 Days",
        x_label="Date",
        y_label="Pace (min/km)",
    )
    elapsed = time.time() - start

    return {
        "viz_id": viz_id,
        "url": f"/viz/{viz_id}",
        "generation_time_ms": int(elapsed * 1000),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
