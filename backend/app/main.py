from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.modules.auth.router import router as auth_router
from app.modules.parser.router import router as parser_router
from app.modules.ai_generator.router import router as ai_generator_router
from app.modules.exam_engine.router import router as exam_engine_router
from app.modules.tutor_analytics.router import router as tutor_analytics_router

# Initialize FastAPI application instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    description="Smart Quiz — AI-Powered Online Assessment Platform Backend API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS Middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/", tags=["Root"])
def root():
    """Root entry point providing API status and docs link."""
    return {
        "project": settings.PROJECT_NAME,
        "version": "0.1.0",
        "docs_url": "/docs",
        "api_v1_prefix": settings.API_V1_STR,
    }


@app.get("/health", tags=["Root"])
def health_check():
    """System-level health check."""
    return {"status": "ok", "project": settings.PROJECT_NAME}


# Mount all 5 module routers under API v1 prefix
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(parser_router, prefix=settings.API_V1_STR)
app.include_router(ai_generator_router, prefix=settings.API_V1_STR)
app.include_router(exam_engine_router, prefix=settings.API_V1_STR)
app.include_router(tutor_analytics_router, prefix=settings.API_V1_STR)
