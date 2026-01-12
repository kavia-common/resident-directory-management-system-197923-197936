from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.core.config import settings
from src.api.routers.auth import router as auth_router
from src.api.routers.residents import router as residents_router
from src.api.routers.uploads import router as uploads_router

openapi_tags = [
    {"name": "health", "description": "Service health and diagnostics."},
    {"name": "auth", "description": "User registration/login and token lifecycle."},
    {"name": "residents", "description": "Resident directory CRUD and search."},
    {"name": "uploads", "description": "Upload-related endpoints (Cloudinary stub)."},
]

app = FastAPI(
    title=settings.app_name,
    description="Backend API for the Resident Directory app (auth + resident management).",
    version=settings.app_version,
    openapi_tags=openapi_tags,
)

# Allow React dev server (port 3000) to call the API (port 3001).
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allow_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/health",
    tags=["health"],
    summary="Health check",
    description="Simple health endpoint for uptime checks and local development verification.",
    operation_id="health_check",
)
def health_check() -> dict:
    """Return service health status."""
    return {"status": "ok"}


# Mount routers
app.include_router(auth_router)
app.include_router(residents_router)
app.include_router(uploads_router)
