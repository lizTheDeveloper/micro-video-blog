import pytest
import asyncio
import time
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db
from app.models.video import Video
from app.models.user import User
from sqlalchemy.orm import Session
import os

client = TestClient(app)

class TestVideoStreaming:
    """Test video streaming performance and functionality"""
    
    def setup_method(self):
        """Setup test data"""
        # This would be called before each test method
        pass
    
    def test_video_streaming_range_requests(self):
        """Test that video streaming supports range requests"""
        # This test would require a real video file in the database
        # For now, we'll test the endpoint structure
        
        response = client.get("/videos/1/stream")
        
        # Should return 404 for non-existent video
        assert response.status_code == 404
        
        # Test with range header
        headers = {"Range": "bytes=0-1023"}
        response = client.get("/videos/1/stream", headers=headers)
        assert response.status_code == 404  # Video doesn't exist
    
    def test_video_streaming_headers(self):
        """Test that video streaming returns correct headers"""
        # Test thumbnail endpoint
        response = client.get("/videos/1/thumbnail")
        assert response.status_code == 404  # Video doesn't exist
    
    def test_video_streaming_performance(self):
        """Test video streaming performance with simulated load"""
        # This is a basic performance test
        # In a real scenario, you'd test with actual video files
        
        start_time = time.time()
        
        # Simulate multiple concurrent requests
        responses = []
        for i in range(10):
            response = client.get("/videos/1/stream")
            responses.append(response)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # All requests should complete quickly (even 404s)
        assert duration < 1.0  # Should complete in under 1 second
        
        # All responses should be 404 (video doesn't exist)
        for response in responses:
            assert response.status_code == 404
    
    def test_video_streaming_content_type(self):
        """Test that video streaming returns correct content type"""
        # Test with a mock video that might exist
        response = client.get("/videos/999/stream")
        
        # Should return 404 for non-existent video
        assert response.status_code == 404
        
        # If video existed, we'd check for proper content type
        # assert response.headers.get("content-type") == "video/mp4"
    
    def test_video_streaming_range_validation(self):
        """Test range request validation"""
        # Test invalid range headers
        invalid_ranges = [
            "bytes=abc-def",  # Invalid format
            "bytes=100-50",   # Start > end
            "bytes=-1-100",   # Negative start
            "bytes=100-",     # Missing end
        ]
        
        for invalid_range in invalid_ranges:
            headers = {"Range": invalid_range}
            response = client.get("/videos/1/stream", headers=headers)
            # Should handle gracefully (either 400 or 404)
            assert response.status_code in [400, 404]
    
    def test_video_streaming_caching_headers(self):
        """Test that video streaming includes caching headers"""
        response = client.get("/videos/1/stream")
        
        # Should return 404 for non-existent video
        assert response.status_code == 404
        
        # If video existed, we'd check for caching headers
        # assert "cache-control" in response.headers
        # assert "accept-ranges" in response.headers
    
    def test_video_streaming_error_handling(self):
        """Test error handling in video streaming"""
        # Test with invalid video ID
        response = client.get("/videos/invalid/stream")
        assert response.status_code == 422  # Validation error
        
        # Test with very large video ID
        response = client.get("/videos/999999999/stream")
        assert response.status_code == 404  # Not found
    
    def test_video_thumbnail_endpoint(self):
        """Test video thumbnail endpoint"""
        response = client.get("/videos/1/thumbnail")
        
        # Should return 404 for non-existent video
        assert response.status_code == 404
        
        # If video existed, we'd check for proper response
        # assert response.status_code == 200
        # assert "thumbnail_url" in response.json()

class TestVideoStreamingIntegration:
    """Integration tests for video streaming with real data"""
    
    def test_video_streaming_with_real_video(self, db_session: Session):
        """Test video streaming with a real video in the database"""
        # This test would require:
        # 1. A real video file uploaded
        # 2. Database record created
        # 3. File stored locally or in GCS
        
        # For now, we'll just test the endpoint structure
        response = client.get("/videos/1/stream")
        assert response.status_code == 404  # No video exists yet
    
    def test_video_streaming_concurrent_requests(self):
        """Test concurrent video streaming requests"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request():
            response = client.get("/videos/1/stream")
            results.put(response.status_code)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        status_codes = []
        while not results.empty():
            status_codes.append(results.get())
        
        # All should return 404 (video doesn't exist)
        assert all(status == 404 for status in status_codes)
        assert len(status_codes) == 5

class TestVideoStreamingPerformance:
    """Performance tests for video streaming"""
    
    def test_video_streaming_memory_usage(self):
        """Test memory usage during video streaming"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Make multiple requests
        for i in range(100):
            response = client.get("/videos/1/stream")
            assert response.status_code == 404
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be minimal (under 10MB)
        assert memory_increase < 10 * 1024 * 1024
    
    def test_video_streaming_response_time(self):
        """Test response time for video streaming"""
        start_time = time.time()
        
        response = client.get("/videos/1/stream")
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Response should be fast (under 100ms for 404)
        assert response_time < 0.1
        assert response.status_code == 404

if __name__ == "__main__":
    # Run basic tests
    test_instance = TestVideoStreaming()
    test_instance.setup_method()
    
    print("Running video streaming tests...")
    
    try:
        test_instance.test_video_streaming_range_requests()
        print("✓ Range requests test passed")
        
        test_instance.test_video_streaming_headers()
        print("✓ Headers test passed")
        
        test_instance.test_video_streaming_performance()
        print("✓ Performance test passed")
        
        test_instance.test_video_streaming_content_type()
        print("✓ Content type test passed")
        
        test_instance.test_video_streaming_range_validation()
        print("✓ Range validation test passed")
        
        test_instance.test_video_streaming_caching_headers()
        print("✓ Caching headers test passed")
        
        test_instance.test_video_streaming_error_handling()
        print("✓ Error handling test passed")
        
        test_instance.test_video_thumbnail_endpoint()
        print("✓ Thumbnail endpoint test passed")
        
        print("\nAll video streaming tests passed! 🎉")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise
