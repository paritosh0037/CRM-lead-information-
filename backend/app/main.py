from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import router as api_router
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="CRM Lead prioritization, predictive ML scoring, SHAP explainability, and Next-Best-Action recommendation engine.",
)

# Enable CORS for local Next.js frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API router
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(api_router, prefix="/api")  # Support direct /api paths as well


@app.get("/health", tags=["Health"])
def health_check():
    """Minimal deterministic health check endpoint."""
    return {"status": "ok"}

