from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import mimetypes
from app.core.database import get_db
from app.models.video import Video
from app.models.user import User
from app.schemas.video import (
    VideoCreate, 
    VideoUpdate, 
    Video as VideoSchema, 
    VideoUploadResponse,
    VideoListResponse
)
from app.services.video_service import VideoProcessingService
from app.services.cloud_storage import CloudStorageService
from app.core.security import get_current_user
from config import DEBUG, USE_CLOUD_STORAGE

router = APIRouter(prefix="/videos", tags=["videos"])

video_service = VideoProcessingService()
storage_service = CloudStorageService()

@router.post("/upload", response_model=VideoUploadResponse)
async def upload_video(
    title: str = Form(..., min_length=1, max_length=200),
    description: Optional[str] = Form(None, max_length=1000),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a new video with processing and optimization"""
    try:
        video_data = VideoCreate(title=title, description=description)
        video = await video_service.process_video_upload(file, video_data, current_user.id, db)
        
        return VideoUploadResponse(
            video_id=video.id,
            message="Video uploaded successfully",
            processing_status=video.processing_status
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/", response_model=VideoListResponse)
async def get_videos(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    creator_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Get paginated list of public videos"""
    query = db.query(Video).filter(
        Video.is_public == True,
        Video.is_deleted == False,
        Video.processing_status == "completed"
    )
    
    if creator_id:
        query = query.filter(Video.creator_id == creator_id)
    
    total = query.count()
    videos = query.offset((page - 1) * page_size).limit(page_size).all()
    
    # Convert to response format
    video_schemas = []
    for video in videos:
        video_dict = {
            "id": video.id,
            "title": video.title,
            "description": video.description,
            "filename": video.filename,
            "original_filename": video.original_filename,
            "file_size": video.file_size,
            "duration": video.duration,
            "width": video.width,
            "height": video.height,
            "format": video.format,
            "thumbnail_url": video.thumbnail_url,
            "video_url": video.video_url,
            "processing_status": video.processing_status,
            "is_public": video.is_public,
            "is_deleted": video.is_deleted,
            "creator_id": video.creator_id,
            "created_at": video.created_at,
            "updated_at": video.updated_at,
            "creator_username": video.creator.username if video.creator else None
        }
        video_schemas.append(VideoSchema(**video_dict))
    
    return VideoListResponse(
        videos=video_schemas,
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total
    )

@router.get("/my-videos", response_model=VideoListResponse)
async def get_my_videos(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's videos"""
    query = db.query(Video).filter(
        Video.creator_id == current_user.id,
        Video.is_deleted == False
    )
    
    total = query.count()
    videos = query.offset((page - 1) * page_size).limit(page_size).all()
    
    # Convert to response format
    video_schemas = []
    for video in videos:
        video_dict = {
            "id": video.id,
            "title": video.title,
            "description": video.description,
            "filename": video.filename,
            "original_filename": video.original_filename,
            "file_size": video.file_size,
            "duration": video.duration,
            "width": video.width,
            "height": video.height,
            "format": video.format,
            "thumbnail_url": video.thumbnail_url,
            "video_url": video.video_url,
            "processing_status": video.processing_status,
            "is_public": video.is_public,
            "is_deleted": video.is_deleted,
            "creator_id": video.creator_id,
            "created_at": video.created_at,
            "updated_at": video.updated_at,
            "creator_username": video.creator.username if video.creator else None
        }
        video_schemas.append(VideoSchema(**video_dict))
    
    return VideoListResponse(
        videos=video_schemas,
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total
    )

@router.get("/{video_id}", response_model=VideoSchema)
async def get_video(
    video_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific video by ID"""
    video = db.query(Video).filter(
        Video.id == video_id,
        Video.is_public == True,
        Video.is_deleted == False,
        Video.processing_status == "completed"
    ).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    video_dict = {
        "id": video.id,
        "title": video.title,
        "description": video.description,
        "filename": video.filename,
        "original_filename": video.original_filename,
        "file_size": video.file_size,
        "duration": video.duration,
        "width": video.width,
        "height": video.height,
        "format": video.format,
        "thumbnail_url": video.thumbnail_url,
        "video_url": video.video_url,
        "processing_status": video.processing_status,
        "is_public": video.is_public,
        "is_deleted": video.is_deleted,
        "creator_id": video.creator_id,
        "created_at": video.created_at,
        "updated_at": video.updated_at,
        "creator_username": video.creator.username if video.creator else None
    }
    
    return VideoSchema(**video_dict)

@router.put("/{video_id}", response_model=VideoSchema)
async def update_video(
    video_id: int,
    video_update: VideoUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update video metadata"""
    video = db.query(Video).filter(
        Video.id == video_id,
        Video.creator_id == current_user.id,
        Video.is_deleted == False
    ).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Update fields
    if video_update.title is not None:
        video.title = video_update.title
    if video_update.description is not None:
        video.description = video_update.description
    if video_update.is_public is not None:
        video.is_public = video_update.is_public
    
    db.commit()
    db.refresh(video)
    
    video_dict = {
        "id": video.id,
        "title": video.title,
        "description": video.description,
        "filename": video.filename,
        "original_filename": video.original_filename,
        "file_size": video.file_size,
        "duration": video.duration,
        "width": video.width,
        "height": video.height,
        "format": video.format,
        "thumbnail_url": video.thumbnail_url,
        "video_url": video.video_url,
        "processing_status": video.processing_status,
        "is_public": video.is_public,
        "is_deleted": video.is_deleted,
        "creator_id": video.creator_id,
        "created_at": video.created_at,
        "updated_at": video.updated_at,
        "creator_username": video.creator.username if video.creator else None
    }
    
    return VideoSchema(**video_dict)

@router.delete("/{video_id}")
async def delete_video(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a video"""
    success = await video_service.delete_video(video_id, current_user.id, db)
    
    if not success:
        raise HTTPException(status_code=404, detail="Video not found or not authorized")
    
    return {"message": "Video deleted successfully"}

@router.get("/{video_id}/stream")
async def stream_video(
    video_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Stream video file with range request support for efficient video delivery"""
    video = db.query(Video).filter(
        Video.id == video_id,
        Video.is_public == True,
        Video.is_deleted == False,
        Video.processing_status == "completed"
    ).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Get video file path
    if USE_CLOUD_STORAGE:
        # For GCS, we'll redirect to the public URL for now
        # In production, you might want to implement signed URLs or proxy through your server
        return {"video_url": video.video_url, "filename": video.filename}
    else:
        # For local storage, implement range request support
        return await _stream_local_video(video, request)

async def _stream_local_video(video: Video, request: Request):
    """Stream video from local storage with range request support"""
    try:
        # Get local file path
        local_video_dir = "uploads/videos"
        file_path = os.path.join(local_video_dir, video.filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Video file not found")
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Parse range header
        range_header = request.headers.get('Range')
        
        if range_header:
            # Parse range header (e.g., "bytes=0-1023")
            range_match = range_header.replace('bytes=', '').split('-')
            start = int(range_match[0]) if range_match[0] else 0
            end = int(range_match[1]) if range_match[1] else file_size - 1
            
            # Ensure end doesn't exceed file size
            end = min(end, file_size - 1)
            
            # Calculate content length
            content_length = end - start + 1
            
            # Create file generator for range
            def file_generator():
                with open(file_path, 'rb') as f:
                    f.seek(start)
                    remaining = content_length
                    while remaining > 0:
                        chunk_size = min(8192, remaining)  # 8KB chunks
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        remaining -= len(chunk)
                        yield chunk
            
            # Get content type
            content_type, _ = mimetypes.guess_type(video.filename)
            if not content_type:
                content_type = 'video/mp4'
            
            # Return streaming response with range
            return StreamingResponse(
                file_generator(),
                status_code=206,  # Partial Content
                headers={
                    'Content-Type': content_type,
                    'Content-Length': str(content_length),
                    'Content-Range': f'bytes {start}-{end}/{file_size}',
                    'Accept-Ranges': 'bytes',
                    'Cache-Control': 'public, max-age=3600'
                }
            )
        else:
            # No range header, return full file
            def file_generator():
                with open(file_path, 'rb') as f:
                    while True:
                        chunk = f.read(8192)  # 8KB chunks
                        if not chunk:
                            break
                        yield chunk
            
            # Get content type
            content_type, _ = mimetypes.guess_type(video.filename)
            if not content_type:
                content_type = 'video/mp4'
            
            return StreamingResponse(
                file_generator(),
                media_type=content_type,
                headers={
                    'Content-Length': str(file_size),
                    'Accept-Ranges': 'bytes',
                    'Cache-Control': 'public, max-age=3600'
                }
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error streaming video: {str(e)}")

@router.get("/{video_id}/thumbnail")
async def get_video_thumbnail(
    video_id: int,
    db: Session = Depends(get_db)
):
    """Get video thumbnail"""
    video = db.query(Video).filter(
        Video.id == video_id,
        Video.is_public == True,
        Video.is_deleted == False,
        Video.processing_status == "completed"
    ).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    if not video.thumbnail_url:
        raise HTTPException(status_code=404, detail="Thumbnail not available")
    
    return {"thumbnail_url": video.thumbnail_url}
