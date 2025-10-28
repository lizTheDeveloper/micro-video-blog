from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)  # Size in bytes
    duration = Column(Float, nullable=False)  # Duration in seconds
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    format = Column(String(10), nullable=False)  # mp4, webm, mov
    thumbnail_url = Column(String(500), nullable=True)
    video_url = Column(String(500), nullable=False)
    processing_status = Column(String(20), default="pending")  # pending, processing, completed, failed
    is_public = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    
    # Foreign keys
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    creator = relationship("User", back_populates="videos")

# Add the relationship to User model
from app.models.user import User
User.videos = relationship("Video", back_populates="creator")
