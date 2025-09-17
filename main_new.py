"""
Main FastAPI application with organized imports
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine
from app.models import Base, create_views
from app.core.config import APP_CONFIG, API_TAGS, SWAGGER_UI_PARAMETERS, CORS_CONFIG
from app.routers import (
    auth_router,
    wallet_router,
    offers_router,
    coupons_router,
    pdv_router
)

# Create FastAPI app with configuration
app = FastAPI(
    **APP_CONFIG,
    openapi_tags=API_TAGS
)

# Configure Swagger UI
app.swagger_ui_parameters = SWAGGER_UI_PARAMETERS

# Add CORS middleware
app.add_middleware(CORSMiddleware, **CORS_CONFIG)

# Include routers
app.include_router(auth_router)
app.include_router(wallet_router)
app.include_router(offers_router)
app.include_router(coupons_router)
app.include_router(pdv_router)

@app.on_event("startup")
def create_tables():
    """Create database tables and views on startup"""
    # Create all tables defined in models
    Base.metadata.create_all(bind=engine)
    
    # Create SQL views
    create_views(engine)
        
    print("Database tables and views created successfully")

@app.get("/", tags=["root"])
def read_root():
    """Root endpoint with API information"""
    return {
        "message": "Fidelity API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health", tags=["health"])
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
