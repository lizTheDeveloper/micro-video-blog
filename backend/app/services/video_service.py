import os
import uuid
import asyncio
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException
import cv2
from PIL import Image
import aiofiles
from app.models.video import Video
from app.schemas.video import VideoCreate, VideoProcessingStatus
from app.services.cloud_storage import CloudStorageService
from config import DEBUG

class VideoProcessingService:
    def __init__(self):
        self.max_duration = 5.0  # 5 seconds
        self.allowed_formats = ["mp4", "webm", "mov"]
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        
        # Initialize cloud storage service
        self.storage_service = CloudStorageService()
    
    async def validate_video_file(self, file: UploadFile) -> Tuple[bool, str]:
        """Validate video file format, size, and duration"""
        # Check file extension
        file_extension = file.filename.split('.')[-1].lower() if file.filename else ""
        if file_extension not in self.allowed_formats:
            return False, f"Unsupported format. Allowed formats: {', '.join(self.allowed_formats)}"
        
        # Check file size
        if file.size and file.size > self.max_file_size:
            return False, f"File too large. Maximum size: {self.max_file_size // (1024*1024)}MB"
        
        return True, ""
    
    async def get_video_duration(self, file_path: str) -> float:
        """Get video duration using OpenCV"""
        try:
            cap = cv2.VideoCapture(file_path)
            if not cap.isOpened():
                raise ValueError("Could not open video file")
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            duration = frame_count / fps if fps > 0 else 0
            
            cap.release()
            return duration
        except Exception as e:
            raise ValueError(f"Error getting video duration: {str(e)}")
    
    async def get_video_dimensions(self, file_path: str) -> Tuple[int, int]:
        """Get video dimensions using OpenCV"""
        try:
            cap = cv2.VideoCapture(file_path)
            if not cap.isOpened():
                raise ValueError("Could not open video file")
            
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            cap.release()
            return width, height
        except Exception as e:
            raise ValueError(f"Error getting video dimensions: {str(e)}")
    
    async def generate_thumbnail(self, video_path: str, output_path: str) -> str:
        """Generate thumbnail from video using OpenCV"""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError("Could not open video file")
            
            # Get frame at 1 second mark
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_number = int(fps) if fps > 0 else 30  # 1 second or frame 30
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            
            ret, frame = cap.read()
            if not ret:
                # If we can't get frame at 1 second, get first frame
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
            
            cap.release()
            
            if ret:
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Resize to standard thumbnail size (320x240)
                height, width = frame_rgb.shape[:2]
                aspect_ratio = width / height
                
                if aspect_ratio > 1:
                    new_width = 320
                    new_height = int(320 / aspect_ratio)
                else:
                    new_height = 240
                    new_width = int(240 * aspect_ratio)
                
                resized_frame = cv2.resize(frame_rgb, (new_width, new_height))
                
                # Convert to PIL Image and save
                image = Image.fromarray(resized_frame)
                image.save(output_path, "JPEG", quality=85)
                
                return output_path
            else:
                raise ValueError("Could not extract frame from video")
                
        except Exception as e:
            raise ValueError(f"Error generating thumbnail: {str(e)}")
    
    async def optimize_video(self, input_path: str, output_path: str) -> str:
        """Optimize video for web delivery using OpenCV"""
        try:
            cap = cv2.VideoCapture(input_path)
            if not cap.isOpened():
                raise ValueError("Could not open video file")
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Calculate new dimensions (max 720p)
            max_width = 1280
            max_height = 720
            
            if width > max_width or height > max_height:
                aspect_ratio = width / height
                if aspect_ratio > max_width / max_height:
                    new_width = max_width
                    new_height = int(max_width / aspect_ratio)
                else:
                    new_height = max_height
                    new_width = int(max_height * aspect_ratio)
            else:
                new_width = width
                new_height = height
            
            # Define codec and create VideoWriter
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (new_width, new_height))
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Resize frame
                resized_frame = cv2.resize(frame, (new_width, new_height))
                out.write(resized_frame)
            
            cap.release()
            out.release()
            
            return output_path
            
        except Exception as e:
            raise ValueError(f"Error optimizing video: {str(e)}")
    
    async def process_video_upload(
        self, 
        file: UploadFile, 
        video_data: VideoCreate, 
        creator_id: int,
        db: Session
    ) -> Video:
        """Process video upload with validation, optimization, and thumbnail generation"""
        
        # Validate file
        is_valid, error_message = await self.validate_video_file(file)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_message)
        
        # Generate unique filename
        file_extension = file.filename.split('.')[-1].lower()
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        temp_path = f"temp_{unique_filename}"
        
        try:
            # Read file content
            content = await file.read()
            
            # Save temporarily for processing
            temp_file_path = os.path.join("uploads", temp_path)
            os.makedirs("uploads", exist_ok=True)
            async with aiofiles.open(temp_file_path, 'wb') as f:
                await f.write(content)
            
            # Get video properties
            duration = await self.get_video_duration(temp_file_path)
            if duration > self.max_duration:
                os.remove(temp_file_path)
                raise HTTPException(
                    status_code=400, 
                    detail=f"Video duration ({duration:.1f}s) exceeds maximum allowed duration ({self.max_duration}s)"
                )
            
            width, height = await self.get_video_dimensions(temp_file_path)
            
            # Optimize video
            optimized_filename = f"optimized_{unique_filename}"
            optimized_path = os.path.join("uploads", optimized_filename)
            await self.optimize_video(temp_file_path, optimized_path)
            
            # Read optimized video content
            with open(optimized_path, 'rb') as f:
                optimized_content = f.read()
            
            # Upload optimized video to cloud storage
            video_filename, video_url = self.storage_service.upload_file(
                optimized_content, file_extension, "videos"
            )
            
            # Generate thumbnail
            thumbnail_filename = f"{uuid.uuid4()}.jpg"
            thumbnail_path = os.path.join("uploads", f"temp_{thumbnail_filename}")
            await self.generate_thumbnail(optimized_path, thumbnail_path)
            
            # Read thumbnail content and upload
            with open(thumbnail_path, 'rb') as f:
                thumbnail_content = f.read()
            
            thumbnail_filename, thumbnail_url = self.storage_service.upload_file(
                thumbnail_content, "jpg", "thumbnails"
            )
            
            # Create video record in database
            video = Video(
                title=video_data.title,
                description=video_data.description,
                filename=video_filename,
                original_filename=file.filename,
                file_size=len(content),
                duration=duration,
                width=width,
                height=height,
                format=file_extension,
                thumbnail_url=thumbnail_url,
                video_url=video_url,
                processing_status=VideoProcessingStatus.COMPLETED,
                creator_id=creator_id
            )
            
            db.add(video)
            db.commit()
            db.refresh(video)
            
            # Clean up temp files
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            if os.path.exists(optimized_path):
                os.remove(optimized_path)
            if os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
            
            return video
            
        except Exception as e:
            # Clean up files on error
            temp_file_path = os.path.join("uploads", temp_path)
            optimized_path = os.path.join("uploads", f"optimized_{unique_filename}")
            thumbnail_path = os.path.join("uploads", f"temp_{thumbnail_filename}")
            
            for file_path in [temp_file_path, optimized_path, thumbnail_path]:
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            raise HTTPException(status_code=500, detail=f"Video processing failed: {str(e)}")
    
    async def delete_video(self, video_id: int, creator_id: int, db: Session) -> bool:
        """Delete video and associated files"""
        video = db.query(Video).filter(
            Video.id == video_id,
            Video.creator_id == creator_id,
            Video.is_deleted == False
        ).first()
        
        if not video:
            return False
        
        # Mark as deleted in database
        video.is_deleted = True
        db.commit()
        
        # Delete files from cloud storage
        try:
            # Delete video file
            self.storage_service.delete_file(video.filename, "videos")
            
            # Delete thumbnail file
            if video.thumbnail_url:
                thumbnail_filename = video.thumbnail_url.split('/')[-1]
                self.storage_service.delete_file(thumbnail_filename, "thumbnails")
        except Exception as e:
            # Log error but don't fail the deletion
            print(f"Error deleting video files: {str(e)}")
        
        return True
