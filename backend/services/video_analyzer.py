"""
Video Analyzer Service.
Wraps Twelve Labs API for video analysis.
Designed as a stateless service for LangGraph integration.
"""

import requests
import time
from typing import List, Dict, Any, Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config


class VideoAnalyzer:
    """
    Analyzes videos using Twelve Labs API.
    Can be used to extract trends from video content.
    """
    
    def __init__(self):
        self._config = config.ai
        self._base_url = self._config.twelve_labs_base_url
        self._api_key = self._config.twelve_labs_api_key
    
    @property
    def _headers(self) -> Dict[str, str]:
        """Get API headers."""
        return {
            'x-api-key': self._api_key,
            'Content-Type': 'application/json'
        }
    
    def is_available(self) -> bool:
        """Check if Twelve Labs API is configured."""
        return bool(self._api_key)
    
    def create_index(self, index_name: str) -> Optional[str]:
        """
        Create a new video index.
        
        Args:
            index_name: Name for the new index
            
        Returns:
            Index ID or None if failed
        """
        if not self.is_available():
            print("⚠️ Twelve Labs API not configured")
            return None
        
        try:
            url = f"{self._base_url}/indexes"
            data = {
                "index_name": index_name,
                "models": [{
                    "name": "marengo2.6",
                    "options": ["visual", "audio"]
                }]
            }
            
            response = requests.post(url, json=data, headers=self._headers)
            response.raise_for_status()
            
            result = response.json()
            index_id = result.get('_id')
            print(f'✅ Created index: {index_id}')
            return index_id
            
        except Exception as e:
            print(f'❌ Error creating index: {e}')
            return None
    
    def upload_video(self, index_id: str, video_url: str) -> Optional[str]:
        """
        Upload a video to an index via URL.
        
        Args:
            index_id: The index to upload to
            video_url: URL of the video
            
        Returns:
            Task ID for tracking or None
        """
        if not self.is_available():
            return None
        
        try:
            url = f"{self._base_url}/tasks/external-provider"
            data = {
                "index_id": index_id,
                "url": video_url
            }
            
            response = requests.post(url, json=data, headers=self._headers)
            response.raise_for_status()
            
            result = response.json()
            task_id = result.get('_id')
            print(f'✅ Video upload started: {task_id}')
            return task_id
            
        except Exception as e:
            print(f'❌ Error uploading video: {e}')
            return None
    
    def wait_for_processing(
        self, 
        task_id: str, 
        max_wait: int = 600,
        poll_interval: int = 10
    ) -> bool:
        """
        Wait for video processing to complete.
        
        Args:
            task_id: The task to monitor
            max_wait: Maximum seconds to wait
            poll_interval: Seconds between status checks
            
        Returns:
            True if processing completed successfully
        """
        if not self.is_available():
            return False
        
        url = f"{self._base_url}/tasks/{task_id}"
        elapsed = 0
        
        while elapsed < max_wait:
            try:
                response = requests.get(url, headers=self._headers)
                response.raise_for_status()
                
                result = response.json()
                status = result.get('status')
                
                if status == 'ready':
                    print(f'✅ Video processing complete')
                    return True
                elif status == 'failed':
                    print(f'❌ Video processing failed')
                    return False
                
                print(f'⏳ Processing... ({status})')
                time.sleep(poll_interval)
                elapsed += poll_interval
                
            except Exception as e:
                print(f'❌ Error checking status: {e}')
                return False
        
        print(f'⚠️ Timeout waiting for processing')
        return False
    
    def analyze_video_content(
        self, 
        index_id: str, 
        video_id: str,
        search_query: str = "fashion trends style aesthetic"
    ) -> Dict[str, Any]:
        """
        Analyze video content for fashion/style elements.
        
        Args:
            index_id: The index containing the video
            video_id: The video to analyze
            search_query: What to search for in the video
            
        Returns:
            Analysis results
        """
        if not self.is_available():
            return {'success': False, 'error': 'API not configured'}
        
        try:
            url = f"{self._base_url}/search"
            data = {
                "query": search_query,
                "index_id": index_id,
                "search_options": ["visual", "audio"],
                "filter": {"id": [video_id]}
            }
            
            response = requests.post(url, json=data, headers=self._headers)
            response.raise_for_status()
            
            result = response.json()
            
            return {
                'success': True,
                'matches': result.get('data', []),
                'page_info': result.get('page_info', {})
            }
            
        except Exception as e:
            print(f'❌ Error analyzing video: {e}')
            return {'success': False, 'error': str(e)}
    
    def extract_video_themes(self, video_id: str, index_id: str) -> List[str]:
        """
        Extract main themes/topics from a video.
        
        Args:
            video_id: The video to analyze
            index_id: The index containing the video
            
        Returns:
            List of detected themes
        """
        themes = []
        
        # Search for various fashion-related themes
        search_terms = [
            "fashion style clothing",
            "aesthetic mood vibe",
            "color palette design",
            "trend popular viral"
        ]
        
        for term in search_terms:
            result = self.analyze_video_content(index_id, video_id, term)
            if result.get('success') and result.get('matches'):
                for match in result['matches']:
                    confidence = match.get('confidence', 0)
                    if confidence > 0.5:
                        themes.append({
                            'term': term,
                            'confidence': confidence,
                            'timestamp': match.get('start', 0)
                        })
        
        return themes


# Global singleton instance
video_analyzer = VideoAnalyzer()
