import os
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://annhoward@localhost:5432/microvideoblog")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Email Configuration (for password reset)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "your-email@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "your-app-password")

# Cloud Storage Configuration
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "microvideoblog-dev")
GCS_PROJECT_ID = os.getenv("GCS_PROJECT_ID", "multiverseschool")
USE_CLOUD_STORAGE = os.getenv("USE_CLOUD_STORAGE", "False").lower() == "true"

# Application Configuration
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "3211"))
