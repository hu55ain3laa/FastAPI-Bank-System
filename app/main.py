import os
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlmodel import Session, select
import uvicorn

from app.models.database import create_db_and_tables, get_session, engine
from app.models.models import User
from app.routes import auth, bank, pages, admin
from app.utils.security import get_current_user_dependency
from app.seed_data import seed_initial_data

# Create FastAPI app
app = FastAPI(title="Secure Bank App")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(auth.router)
app.include_router(bank.router)
app.include_router(pages.router)
app.include_router(admin.router)

# Initialize database on startup
@app.on_event("startup")
async def on_startup():
    create_db_and_tables()
    
    # Use the seed_initial_data function to create all initial users
    seed_initial_data()


# Add a catch-all route for 404 errors
@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc: HTTPException):
    return HTMLResponse(
        status_code=404,
        content="<html><body><h1>404 Not Found</h1><p>The requested URL was not found on the server.</p></body></html>"
    )


# Main entry point
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 