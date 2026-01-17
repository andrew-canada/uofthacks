import os
import requests
import time
from pathlib import Path

# API Keys
TWELVE_LABS_API_KEY = "tlk_0SSK9QC10TMHG02CYXS7T0EW9R8M"
YOUTUBE_API_KEY = "AIzaSyDKp4kZ_OscfS3JK9GEofSlXNcS2J1VGXg"

# Twelve Labs API endpoints
TWELVE_LABS_BASE_URL = "https://api.twelvelabs.io/v1.2"

def search_short_youtube_video():
    """Search for a short YouTube video"""
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        'part': 'snippet',
        'q': 'cat funny',
        'type': 'video',
        'videoDuration': 'short',  # Videos less than 4 minutes
        'maxResults': 1,
        'key': YOUTUBE_API_KEY
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    if data['items']:
        video_id = data['items'][0]['id']['videoId']
        title = data['items'][0]['snippet']['title']
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        print(f"Found video: {title}")
        print(f"URL: {video_url}")
        return video_url
    return None

def download_video(video_url):
    """Download video using yt-dlp"""
    output_path = "test_video.mp4"

    # Using yt-dlp command line
    import subprocess

    cmd = [
        'yt-dlp',
        '-f', 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best',
        '--merge-output-format', 'mp4',
        '-o', output_path,
        '--no-check-certificates',
        video_url
    ]

    print("Downloading video...")
    subprocess.run(cmd, check=True)
    print(f"Video downloaded to {output_path}")
    return output_path

def create_index():
    """Create a Twelve Labs index"""
    url = f"{TWELVE_LABS_BASE_URL}/indexes"
    headers = {
        "x-api-key": TWELVE_LABS_API_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "engine_id": "marengo2.6",
        "index_options": ["visual", "conversation", "text_in_video"],
        "index_name": f"test_index_{int(time.time())}"
    }

    print("Creating Twelve Labs index...")
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()

    index_id = response.json()['_id']
    print(f"Index created: {index_id}")
    return index_id

def upload_video_to_twelve_labs(index_id, video_path):
    """Upload video to Twelve Labs"""
    url = f"{TWELVE_LABS_BASE_URL}/tasks"
    headers = {
        "x-api-key": TWELVE_LABS_API_KEY
    }

    with open(video_path, 'rb') as f:
        files = {
            'video_file': (os.path.basename(video_path), f, 'video/mp4')
        }
        data = {
            'index_id': index_id
        }

        print("Uploading video to Twelve Labs...")
        response = requests.post(url, headers=headers, files=files, data=data)
        response.raise_for_status()

        task_id = response.json()['_id']
        print(f"Upload task created: {task_id}")
        return task_id

def check_task_status(task_id):
    """Check the status of the upload task"""
    url = f"{TWELVE_LABS_BASE_URL}/tasks/{task_id}"
    headers = {
        "x-api-key": TWELVE_LABS_API_KEY
    }

    while True:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        status = response.json()['status']
        print(f"Task status: {status}")

        if status == 'ready':
            video_id = response.json()['video_id']
            print(f"Video processed successfully! Video ID: {video_id}")
            return video_id
        elif status == 'failed':
            print("Task failed!")
            print(response.json())
            return None

        time.sleep(5)

def search_video(index_id, query):
    """Search the video using Twelve Labs"""
    url = f"{TWELVE_LABS_BASE_URL}/search"
    headers = {
        "x-api-key": TWELVE_LABS_API_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "query": query,
        "index_id": index_id,
        "search_options": ["visual", "conversation", "text_in_video"]
    }

    print(f"\nSearching for: '{query}'")
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()

    results = response.json()
    print("\nSearch Results:")
    print(f"Found {len(results.get('data', []))} results")

    for i, result in enumerate(results.get('data', [])[:3]):
        print(f"\nResult {i+1}:")
        print(f"  Score: {result.get('score', 'N/A')}")
        print(f"  Start: {result.get('start', 'N/A')}s")
        print(f"  End: {result.get('end', 'N/A')}s")
        if 'metadata' in result:
            print(f"  Metadata: {result['metadata']}")

def main():
    try:
        # Step 1: Find a short YouTube video
        video_url = search_short_youtube_video()
        if not video_url:
            print("No video found!")
            return

        # Step 2: Download the video
        video_path = download_video(video_url)

        # Step 3: Create a Twelve Labs index
        index_id = create_index()

        # Step 4: Upload video to Twelve Labs
        task_id = upload_video_to_twelve_labs(index_id, video_path)

        # Step 5: Wait for processing to complete
        video_id = check_task_status(task_id)

        if video_id:
            # Step 6: Try searching the video
            search_video(index_id, "what happens in this video")

        # Clean up
        if os.path.exists(video_path):
            os.remove(video_path)
            print(f"\nCleaned up: {video_path}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
