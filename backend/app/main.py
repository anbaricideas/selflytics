"""FastAPI application entry point for Selflytics."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import auth


app = FastAPI(
    title="Selflytics API",
    description="AI-powered analysis for quantified self data",
    version="0.1.0",
)

# CORS middleware (development only)
if settings.debug:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include routers
app.include_router(auth.router)


@app.get("/health")
async def health_check():
    """Health check endpoint.

    Returns:
        Health status and service name
    """
    return {"status": "healthy", "service": "selflytics"}
