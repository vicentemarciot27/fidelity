"""
Main FastAPI application with organized imports
"""

print("Alou")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
print("Alou")
from database import engine
print("Alou")
from app.models import Base, create_views
print("Alou")
from app.core.config import APP_CONFIG, API_TAGS, SWAGGER_UI_PARAMETERS, CORS_CONFIG
print("Alou")
from app.routers import (
    auth_router,
    wallet_router,
    offers_router,
    coupons_router,
    pdv_router,
    # Admin routers
    business_router,
    users_router,
    config_router,
    admin_coupons_router,
    catalog_router,
    system_router
)
print("Alou")

# Create FastAPI app with configuration
app = FastAPI(
    **APP_CONFIG,
    openapi_tags=API_TAGS
)

# Configure Swagger UI
app.swagger_ui_parameters = SWAGGER_UI_PARAMETERS

# Add CORS middleware
app.add_middleware(CORSMiddleware, **CORS_CONFIG)

# Include public/marketplace routers
app.include_router(auth_router)
app.include_router(wallet_router)
app.include_router(offers_router)
app.include_router(coupons_router)
app.include_router(pdv_router)

# Include admin routers
app.include_router(business_router)
app.include_router(users_router)
app.include_router(config_router)
app.include_router(admin_coupons_router)
app.include_router(catalog_router)
app.include_router(system_router)

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
