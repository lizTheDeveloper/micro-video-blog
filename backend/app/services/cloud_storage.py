import os
import uuid
from typing import Optional, Tuple
from google.cloud import storage
from config import GCS_BUCKET_NAME, GCS_PROJECT_ID, USE_CLOUD_STORAGE, DEBUG

class CloudStorageService:
    def __init__(self):
        self.use_cloud = USE_CLOUD_STORAGE
        self.bucket_name = GCS_BUCKET_NAME
        self.project_id = GCS_PROJECT_ID
        
        # Local storage paths
        self.local_video_dir = "uploads/videos"
        self.local_thumbnail_dir = "uploads/thumbnails"
        
        # Create local directories
        os.makedirs(self.local_video_dir, exist_ok=True)
        os.makedirs(self.local_thumbnail_dir, exist_ok=True)
        
        # Initialize GCS client if using cloud storage
        self.gcs_client = None
        if self.use_cloud:
            try:
                self.gcs_client = storage.Client(project=self.project_id)
                # Test connection and create bucket if it doesn't exist
                self._ensure_bucket_exists()
            except Exception as e:
                print(f"Warning: Could not initialize GCS client: {e}")
                print("Falling back to local storage")
                self.use_cloud = False
    
    def _ensure_bucket_exists(self):
        """Ensure the GCS bucket exists, create if it doesn't"""
        try:
            bucket = self.gcs_client.bucket(self.bucket_name)
            if not bucket.exists():
                print(f"Creating bucket {self.bucket_name}...")
                bucket = self.gcs_client.create_bucket(self.bucket_name, location="us-central1")
                print(f"Bucket {self.bucket_name} created successfully")
            else:
                print(f"Bucket {self.bucket_name} already exists")
        except Exception as e:
            print(f"Error ensuring bucket exists: {e}")
            raise
    
    def upload_file(self, file_data: bytes, file_extension: str, folder: str = "videos") -> Tuple[str, str]:
        """
        Upload file to storage and return (filename, public_url)
        """
        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        
        if self.use_cloud and self.gcs_client:
            return self._upload_to_gcs(file_data, unique_filename, folder)
        else:
            return self._upload_to_local(file_data, unique_filename, folder)
    
    def _upload_to_gcs(self, file_data: bytes, filename: str, folder: str) -> Tuple[str, str]:
        """Upload file to Google Cloud Storage"""
        try:
            bucket = self.gcs_client.bucket(self.bucket_name)
            blob_name = f"{folder}/{filename}"
            blob = bucket.blob(blob_name)
            
            # Upload file
            blob.upload_from_string(file_data, content_type=self._get_content_type(filename))
            
            # Make blob publicly readable
            blob.make_public()
            
            # Return filename and public URL
            public_url = f"https://storage.googleapis.com/{self.bucket_name}/{blob_name}"
            return filename, public_url
            
        except Exception as e:
            print(f"Error uploading to GCS: {e}")
            # Fallback to local storage
            return self._upload_to_local(file_data, filename, folder)
    
    def _upload_to_local(self, file_data: bytes, filename: str, folder: str) -> Tuple[str, str]:
        """Upload file to local storage"""
        try:
            # Determine local directory
            if folder == "videos":
                local_dir = self.local_video_dir
            elif folder == "thumbnails":
                local_dir = self.local_thumbnail_dir
            else:
                local_dir = "uploads"
            
            # Ensure directory exists
            os.makedirs(local_dir, exist_ok=True)
            
            # Write file
            file_path = os.path.join(local_dir, filename)
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            # Return filename and local URL
            public_url = f"/{folder}/{filename}"
            return filename, public_url
            
        except Exception as e:
            print(f"Error uploading to local storage: {e}")
            raise
    
    def delete_file(self, filename: str, folder: str = "videos") -> bool:
        """Delete file from storage"""
        try:
            if self.use_cloud and self.gcs_client:
                return self._delete_from_gcs(filename, folder)
            else:
                return self._delete_from_local(filename, folder)
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False
    
    def _delete_from_gcs(self, filename: str, folder: str) -> bool:
        """Delete file from Google Cloud Storage"""
        try:
            bucket = self.gcs_client.bucket(self.bucket_name)
            blob_name = f"{folder}/{filename}"
            blob = bucket.blob(blob_name)
            
            if blob.exists():
                blob.delete()
                return True
            return False
            
        except Exception as e:
            print(f"Error deleting from GCS: {e}")
            return False
    
    def _delete_from_local(self, filename: str, folder: str) -> bool:
        """Delete file from local storage"""
        try:
            # Determine local directory
            if folder == "videos":
                local_dir = self.local_video_dir
            elif folder == "thumbnails":
                local_dir = self.local_thumbnail_dir
            else:
                local_dir = "uploads"
            
            file_path = os.path.join(local_dir, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
            
        except Exception as e:
            print(f"Error deleting from local storage: {e}")
            return False
    
    def _get_content_type(self, filename: str) -> str:
        """Get content type based on file extension"""
        extension = filename.lower().split('.')[-1]
        content_types = {
            'mp4': 'video/mp4',
            'webm': 'video/webm',
            'mov': 'video/quicktime',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png'
        }
        return content_types.get(extension, 'application/octet-stream')
    
    def get_public_url(self, filename: str, folder: str = "videos") -> str:
        """Get public URL for a file"""
        if self.use_cloud and self.gcs_client:
            return f"https://storage.googleapis.com/{self.bucket_name}/{folder}/{filename}"
        else:
            return f"/{folder}/{filename}"
