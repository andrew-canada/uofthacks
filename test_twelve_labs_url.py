import requests
import time

# API Keys
TWELVE_LABS_API_KEY = "tlk_0SSK9QC10TMHG02CYXS7T0EW9R8M"
YOUTUBE_API_KEY = "AIzaSyDKp4kZ_OscfS3JK9GEofSlXNcS2J1VGXg"

# Twelve Labs API endpoints
TWELVE_LABS_BASE_URL = "https://api.twelvelabs.io/v1.3"

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

def create_index():
    """Create a Twelve Labs index"""
    url = f"{TWELVE_LABS_BASE_URL}/indexes"
    headers = {
        "x-api-key": TWELVE_LABS_API_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "index_name": f"test_index_{int(time.time())}",
        "models": [
            {
                "model_name": "marengo3.0",
                "model_options": ["visual", "audio"]
            }
        ]
    }

    print("\nCreating Twelve Labs index...")
    response = requests.post(url, headers=headers, json=data)

    if response.status_code != 200:
        print(f"Error response: {response.text}")

    response.raise_for_status()

    index_id = response.json()['_id']
    print(f"Index created: {index_id}")
    return index_id

def upload_video_url_to_twelve_labs(index_id, video_url):
    """Upload video to Twelve Labs using URL"""
    url = f"{TWELVE_LABS_BASE_URL}/tasks"
    headers = {
        "x-api-key": TWELVE_LABS_API_KEY
    }

    # Using files parameter to force multipart/form-data encoding
    files = {
        'index_id': (None, index_id),
        'video_url': (None, video_url),
        'language': (None, 'en')
    }

    print("\nUploading video URL to Twelve Labs...")
    response = requests.post(url, headers=headers, files=files)

    if response.status_code != 201:
        print(f"Error response: {response.text}")

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

    print("\nWaiting for video to be processed...")
    while True:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        status = response.json()['status']
        print(f"Task status: {status}")

        if status == 'ready':
            video_id = response.json()['video_id']
            print(f"\nVideo processed successfully! Video ID: {video_id}")
            return video_id
        elif status == 'failed':
            print("\nTask failed!")
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
        "search_options": ["visual", "conversation", "text_in_video"],
        "page_limit": 5
    }

    print(f"\n{'='*60}")
    print(f"Searching for: '{query}'")
    print(f"{'='*60}")
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()

    results = response.json()
    print(f"\nFound {len(results.get('data', []))} results")

    for i, result in enumerate(results.get('data', [])[:5]):
        print(f"\n--- Result {i+1} ---")
        print(f"  Confidence Score: {result.get('score', 'N/A')}")
        print(f"  Time Range: {result.get('start', 'N/A')}s - {result.get('end', 'N/A')}s")
        if 'metadata' in result:
            print(f"  Metadata: {result['metadata']}")

    return results

def generate_text(video_id):
    """Generate text summary using Twelve Labs"""
    url = f"{TWELVE_LABS_BASE_URL}/generate"
    headers = {
        "x-api-key": TWELVE_LABS_API_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "video_id": video_id,
        "prompt": "Describe what happens in this video in detail."
    }

    print(f"\n{'='*60}")
    print("Generating video description...")
    print(f"{'='*60}")
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()

    result = response.json()
    description = result.get('data', 'No description generated')
    print(f"\nVideo Description:")
    print(f"{description}")

    return description

def main():
    try:
        # Step 1: Find a short YouTube video
        print("="*60)
        print("STEP 1: Finding a short YouTube video")
        print("="*60)
        video_url = search_short_youtube_video()
        if not video_url:
            print("No video found!")
            return

        # Step 2: Create a Twelve Labs index
        print("\n" + "="*60)
        print("STEP 2: Creating Twelve Labs Index")
        print("="*60)
        index_id = create_index()

        # Step 3: Upload video URL to Twelve Labs
        print("\n" + "="*60)
        print("STEP 3: Uploading Video to Twelve Labs")
        print("="*60)
        task_id = upload_video_url_to_twelve_labs(index_id, video_url)

        # Step 4: Wait for processing to complete
        print("\n" + "="*60)
        print("STEP 4: Processing Video")
        print("="*60)
        video_id = check_task_status(task_id)

        if video_id:
            # Step 5: Generate a description
            print("\n" + "="*60)
            print("STEP 5: Generating Video Description")
            print("="*60)
            generate_text(video_id)

            # Step 6: Try searching the video
            print("\n" + "="*60)
            print("STEP 6: Searching Video Content")
            print("="*60)
            search_video(index_id, "cat")

            print("\n" + "="*60)
            print("SUCCESS! Video analyzed by Twelve Labs")
            print("="*60)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
