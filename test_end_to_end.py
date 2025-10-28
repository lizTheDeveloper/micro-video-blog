#!/usr/bin/env python3
"""
End-to-end test for video upload functionality
"""

import requests
import json
import tempfile
import os
import cv2
import numpy as np

# API base URL
API_BASE = "http://localhost:8000"

def create_test_video(duration_seconds=3.0):
    """Create a simple test video file"""
    # Video properties
    width, height = 320, 240
    fps = 10
    total_frames = int(duration_seconds * fps)
    
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
        output_path = temp_file.name
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    # Generate frames
    for frame_num in range(total_frames):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        center_x = int((frame_num / total_frames) * (width - 100) + 50)
        center_y = height // 2
        cv2.circle(frame, (center_x, center_y), 20, (0, 255, 0), -1)
        cv2.putText(frame, f"Frame {frame_num}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        out.write(frame)
    
    out.release()
    return output_path

def test_end_to_end():
    """Test the complete video upload flow"""
    print("🧪 Testing end-to-end video upload flow...")
    
    # Step 1: Register a test user
    print("1. Registering test user...")
    register_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "test123",
        "full_name": "Test User"
    }
    
    response = requests.post(f"{API_BASE}/auth/register", json=register_data)
    if response.status_code in [200, 201]:
        print("✅ User registered successfully")
    elif response.status_code == 400 and ("already exists" in response.json().get("detail", "") or "already registered" in response.json().get("detail", "")):
        print("ℹ️  User already exists, continuing...")
    else:
        print(f"❌ Registration failed: {response.status_code} - {response.text}")
        return False
    
    # Step 2: Login
    print("2. Logging in...")
    login_data = {
        "email": "test@example.com",
        "password": "test123"
    }
    
    response = requests.post(f"{API_BASE}/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return False
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login successful")
    
    # Step 3: Create test video
    print("3. Creating test video...")
    video_path = create_test_video(duration_seconds=3.0)
    print(f"✅ Test video created: {video_path}")
    
    try:
        # Step 4: Upload video
        print("4. Uploading video...")
        with open(video_path, 'rb') as video_file:
            files = {"file": ("test_video.mp4", video_file, "video/mp4")}
            data = {
                "title": "Test Video Upload",
                "description": "This is a test video for the micro video blog platform"
            }
            
            response = requests.post(
                f"{API_BASE}/videos/upload",
                headers=headers,
                files=files,
                data=data
            )
        
        if response.status_code == 200:
            upload_result = response.json()
            print(f"✅ Video uploaded successfully!")
            print(f"   Video ID: {upload_result['video_id']}")
            print(f"   Status: {upload_result['processing_status']}")
            video_id = upload_result['video_id']
        else:
            print(f"❌ Upload failed: {response.status_code} - {response.text}")
            return False
        
        # Step 5: Get video list
        print("5. Fetching video list...")
        response = requests.get(f"{API_BASE}/videos/")
        if response.status_code == 200:
            videos = response.json()
            print(f"✅ Found {videos['total']} videos")
            if videos['videos']:
                video = videos['videos'][0]
                print(f"   First video: {video['title']} by {video['creator_username']}")
        else:
            print(f"❌ Failed to fetch videos: {response.status_code}")
            return False
        
        # Step 6: Get my videos
        print("6. Fetching my videos...")
        response = requests.get(f"{API_BASE}/videos/my-videos", headers=headers)
        if response.status_code == 200:
            my_videos = response.json()
            print(f"✅ Found {my_videos['total']} of my videos")
        else:
            print(f"❌ Failed to fetch my videos: {response.status_code}")
            return False
        
        # Step 7: Get specific video
        print("7. Fetching specific video...")
        response = requests.get(f"{API_BASE}/videos/{video_id}")
        if response.status_code == 200:
            video_details = response.json()
            print(f"✅ Video details: {video_details['title']}")
            print(f"   Duration: {video_details['duration']}s")
            print(f"   Dimensions: {video_details['width']}x{video_details['height']}")
            print(f"   Video URL: {video_details['video_url']}")
            print(f"   Thumbnail URL: {video_details['thumbnail_url']}")
        else:
            print(f"❌ Failed to fetch video details: {response.status_code}")
            return False
        
        print("\n🎉 All tests passed! Video upload functionality is working correctly.")
        return True
        
    finally:
        # Cleanup
        if os.path.exists(video_path):
            os.remove(video_path)
            print(f"🧹 Cleaned up test video: {video_path}")

if __name__ == "__main__":
    success = test_end_to_end()
    exit(0 if success else 1)
