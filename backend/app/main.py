from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.auth import router as auth_router
from app.api.password_reset import router as password_reset_router
from app.core.database import engine
from app.models.user import User
from config import DEBUG

# Create database tables
User.metadata.create_all(bind=engine)

app = FastAPI(
    title="Micro Video Blog API",
    description="A micro-video blog platform for 5-second video content",
    version="1.0.0",
    debug=DEBUG
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(password_reset_router)

@app.get("/")
async def root():
    return {"message": "Micro Video Blog API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
