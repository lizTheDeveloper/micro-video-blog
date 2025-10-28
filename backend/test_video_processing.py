#!/usr/bin/env python3
"""
Simple test script for video processing functionality
This creates a minimal test video and tests the processing pipeline
"""

import os
import sys
import asyncio
import tempfile
import cv2
import numpy as np
from pathlib import Path

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.video_service import VideoProcessingService
from app.services.cloud_storage import CloudStorageService

def create_test_video(output_path: str, duration_seconds: float = 3.0):
    """Create a simple test video file"""
    # Video properties
    width, height = 640, 480
    fps = 30
    total_frames = int(duration_seconds * fps)
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    # Generate frames
    for frame_num in range(total_frames):
        # Create a simple animated frame
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Add a moving circle
        center_x = int((frame_num / total_frames) * (width - 100) + 50)
        center_y = height // 2
        cv2.circle(frame, (center_x, center_y), 30, (0, 255, 0), -1)
        
        # Add frame number text
        cv2.putText(frame, f"Frame {frame_num}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        out.write(frame)
    
    out.release()
    print(f"Created test video: {output_path}")

async def test_video_processing():
    """Test the video processing pipeline"""
    print("Testing video processing pipeline...")
    
    # Create test video
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
        test_video_path = temp_file.name
    
    try:
        create_test_video(test_video_path, duration_seconds=3.0)
        
        # Test video service
        video_service = VideoProcessingService()
        
        # Test duration validation
        duration = await video_service.get_video_duration(test_video_path)
        print(f"Video duration: {duration:.2f} seconds")
        
        # Test dimensions
        width, height = await video_service.get_video_dimensions(test_video_path)
        print(f"Video dimensions: {width}x{height}")
        
        # Test thumbnail generation
        thumbnail_path = test_video_path.replace('.mp4', '_thumb.jpg')
        await video_service.generate_thumbnail(test_video_path, thumbnail_path)
        print(f"Generated thumbnail: {thumbnail_path}")
        
        # Test video optimization
        optimized_path = test_video_path.replace('.mp4', '_optimized.mp4')
        await video_service.optimize_video(test_video_path, optimized_path)
        print(f"Generated optimized video: {optimized_path}")
        
        # Test cloud storage service
        print("\nTesting cloud storage service...")
        storage_service = CloudStorageService()
        
        # Read test video content
        with open(test_video_path, 'rb') as f:
            video_content = f.read()
        
        # Upload to storage
        filename, url = storage_service.upload_file(video_content, 'mp4', 'videos')
        print(f"Uploaded video: {filename}")
        print(f"Public URL: {url}")
        
        # Test deletion
        deleted = storage_service.delete_file(filename, 'videos')
        print(f"Deleted video: {deleted}")
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        for file_path in [test_video_path, thumbnail_path, optimized_path]:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Cleaned up: {file_path}")

if __name__ == "__main__":
    asyncio.run(test_video_processing())
