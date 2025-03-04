from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from datetime import datetime
import logging
from typing import Optional

from app.api.routes import router as api_router
from app.api.dependencies import rate_limit, check_api_key
from app.database.database import init_db
from app.config import settings
from app.utils.logger import setup_logger

# Initialize FastAPI app
app = FastAPI(
    title="Professional Cocktail Advisor",
    description="An AI-powered cocktail recommendation system",
    version="1.0.0"
)

# Setup logging
logger = setup_logger(__name__)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize templates
templates = Jinja2Templates(directory="templates")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(
    api_router,
    prefix="/api",
    dependencies=[Depends(rate_limit)]
)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise

@app.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    user: Optional[str] = "ramalMr"
):
    """Render home page"""
    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "user": user,
            "current_time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        }
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    return {
        "status": "ready",
        "timestamp": datetime.utcnow(),
        "version": settings.app_version
    }

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    # Implement your metrics collection here
    return {
        "total_requests": 0,  # Replace with actual metrics
        "active_users": 0,
        "response_time_avg": 0,
        "error_rate": 0
    }

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom exception handler"""
    logger.error(f"HTTP error occurred: {exc.detail}")
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "error_code": exc.status_code,
            "error_message": exc.detail
        },
        status_code=exc.status_code
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )