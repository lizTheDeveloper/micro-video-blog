from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from enum import Enum

class VideoProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class VideoFormat(str, Enum):
    MP4 = "mp4"
    WEBM = "webm"
    MOV = "mov"

class VideoBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)

class VideoCreate(VideoBase):
    pass

class VideoUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    is_public: Optional[bool] = None

class VideoInDB(VideoBase):
    id: int
    filename: str
    original_filename: str
    file_size: int
    duration: float
    width: int
    height: int
    format: VideoFormat
    thumbnail_url: Optional[str]
    video_url: str
    processing_status: VideoProcessingStatus
    is_public: bool
    is_deleted: bool
    creator_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class Video(VideoInDB):
    creator_username: Optional[str] = None

class VideoUploadResponse(BaseModel):
    video_id: int
    message: str
    processing_status: VideoProcessingStatus

class VideoListResponse(BaseModel):
    videos: list[Video]
    total: int
    page: int
    page_size: int
    has_next: bool
