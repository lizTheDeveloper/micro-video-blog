from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.auth import router as auth_router
from app.api.password_reset import router as password_reset_router
from app.api.videos import router as videos_router
from app.core.database import engine
from app.models.user import User
from app.models.video import Video
from config import DEBUG
import os

# Create database tables
User.metadata.create_all(bind=engine)
Video.metadata.create_all(bind=engine)

app = FastAPI(
    title="Micro Video Blog API",
    description="A micro-video blog platform for 5-second video content",
    version="1.0.0",
    debug=DEBUG
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3212", "http://127.0.0.1:3212"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(password_reset_router)
app.include_router(videos_router)

# Mount static files for video and thumbnail serving
os.makedirs("uploads/videos", exist_ok=True)
os.makedirs("uploads/thumbnails", exist_ok=True)
app.mount("/static/videos", StaticFiles(directory="uploads/videos"), name="videos")
app.mount("/static/thumbnails", StaticFiles(directory="uploads/thumbnails"), name="thumbnails")

@app.get("/")
async def root():
    return {"message": "Micro Video Blog API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
