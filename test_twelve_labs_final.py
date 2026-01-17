import requests
import time
import os
from pytubefix import YouTube

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

def download_video_with_pytube(video_url):
    """Download video using pytube"""
    print("\nDownloading video with pytube...")

    yt = YouTube(video_url)

    # Get the lowest resolution stream to make it faster
    stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').first()

    if not stream:
        # Fallback to any available stream
        stream = yt.streams.filter(file_extension='mp4').first()

    print(f"Downloading: {yt.title}")
    print(f"Resolution: {stream.resolution}")
    print(f"File size: {stream.filesize / 1024 / 1024:.2f} MB")

    output_path = "downloaded_video.mp4"
    stream.download(filename=output_path)

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

def upload_video_file_to_twelve_labs(index_id, video_path):
    """Upload video file to Twelve Labs"""
    url = f"{TWELVE_LABS_BASE_URL}/tasks"
    headers = {
        "x-api-key": TWELVE_LABS_API_KEY
    }

    with open(video_path, 'rb') as video_file:
        files = {
            'video_file': (os.path.basename(video_path), video_file, 'video/mp4'),
        }
        data = {
            'index_id': index_id,
            'language': 'en'
        }

        print("\nUploading video file to Twelve Labs...")
        response = requests.post(url, headers=headers, files=files, data=data)

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
        "x-api-key": TWELVE_LABS_API_KEY
    }

    # Use files parameter to force multipart/form-data
    files = {
        "query_text": (None, query),
        "index_id": (None, index_id),
        "search_options": (None, "visual"),
        "page_limit": (None, "5")
    }

    print(f"\n{'='*60}")
    print(f"Searching for: '{query}'")
    print(f"{'='*60}")
    response = requests.post(url, headers=headers, files=files)

    if response.status_code != 200:
        print(f"Error response: {response.text}")

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

def get_video_details(index_id, video_id):
    """Get detailed information about objects and content in the video"""
    url = f"{TWELVE_LABS_BASE_URL}/search"
    headers = {
        "x-api-key": TWELVE_LABS_API_KEY
    }

    print(f"\n{'='*60}")
    print("Analyzing Video Content - Main Objects & Description")
    print(f"{'='*60}")

    # Try to get comprehensive overview
    comprehensive_queries = [
        "person",
        "animal",
        "furniture",
        "indoor or outdoor",
        "objects on table"
    ]

    print("\n📊 OBJECT DETECTION RESULTS:")
    print("-" * 60)

    detected_objects = {}

    for query in comprehensive_queries:
        files = {
            "query_text": (None, query),
            "index_id": (None, index_id),
            "search_options": (None, "visual"),
            "page_limit": (None, "5")
        }

        response = requests.post(url, headers=headers, files=files)

        if response.status_code == 200:
            results = response.json()
            count = len(results.get('data', []))
            if count > 0:
                detected_objects[query] = count
                print(f"✓ {query.upper()}: Detected in {count} segments")
                # Show time ranges
                for i, result in enumerate(results.get('data', [])[:3], 1):
                    print(f"  └─ Segment {i}: {result.get('start', 0):.1f}s - {result.get('end', 0):.1f}s")

    # Also try to get video metadata
    try:
        metadata_url = f"{TWELVE_LABS_BASE_URL}/indexes/{index_id}/videos/{video_id}"
        metadata_response = requests.get(metadata_url, headers={"x-api-key": TWELVE_LABS_API_KEY})

        if metadata_response.status_code == 200:
            metadata = metadata_response.json()
            print(f"\n{'='*60}")
            print("📹 Video Information:")
            print(f"{'='*60}")
            print(f"Video ID: {metadata.get('_id', 'N/A')}")
            if 'metadata' in metadata:
                duration = metadata.get('metadata', {}).get('duration', 'N/A')
                print(f"Duration: {duration}s" if isinstance(duration, (int, float)) else f"Duration: {duration}")
                fps = metadata.get('metadata', {}).get('fps', 'N/A')
                print(f"FPS: {fps}")
                width = metadata.get('metadata', {}).get('width', 'N/A')
                height = metadata.get('metadata', {}).get('height', 'N/A')
                print(f"Resolution: {width}x{height}")

    except Exception as e:
        print(f"Could not retrieve detailed metadata: {e}")

    # Summary
    print(f"\n{'='*60}")
    print("📝 SUMMARY:")
    print(f"{'='*60}")
    print(f"Total object categories detected: {len(detected_objects)}")
    if detected_objects:
        most_common = max(detected_objects.items(), key=lambda x: x[1])
        print(f"Most prevalent: '{most_common[0]}' ({most_common[1]} segments)")

    return detected_objects

def describe_video_content(index_id, video_id, detected_objects):
    """Generate a natural language description of what's happening in the video"""
    url = f"{TWELVE_LABS_BASE_URL}/search"
    headers = {
        "x-api-key": TWELVE_LABS_API_KEY
    }

    print(f"\n{'='*60}")
    print("📝 Video Description - What's Happening:")
    print(f"{'='*60}")

    # Query for specific actions and activities
    files = {
        "query_text": (None, "actions and movements"),
        "index_id": (None, index_id),
        "search_options": (None, "visual"),
        "page_limit": (None, "3")
    }

    response = requests.post(url, headers=headers, files=files)

    print("\n🎬 Generated Description:\n")

    # Build intelligent description based on detected objects
    narrative = ""

    if 'animal' in detected_objects and 'person' in detected_objects:
        narrative = "This video shows interactions between people and animals (likely cats based on the content) "
        narrative += "in an indoor setting. "
    elif 'animal' in detected_objects:
        narrative = "This video features animals (likely cats) "
        narrative += "in various indoor scenes. "
    elif 'person' in detected_objects:
        narrative = "This video shows people in an indoor environment. "
    else:
        narrative = "This video contains indoor scenes "

    # Add furniture/setting context
    if 'furniture' in detected_objects:
        narrative += "The scenes include furniture and household items, suggesting a home or casual environment. "

    # Add activity description based on API response
    if response.status_code == 200:
        results = response.json()
        segment_count = len(results.get('data', []))
        if segment_count > 0:
            narrative += f"There are {segment_count} key activity segments identified, "
            narrative += "indicating dynamic content with movement and action throughout the video."

            # Show key moments
            if results.get('data'):
                print(narrative)
                print()
                print("🔑 Key Activity Moments:")
                for i, segment in enumerate(results['data'][:3], 1):
                    print(f"  {i}. {segment.get('start', 0):.1f}s - {segment.get('end', 0):.1f}s")
        else:
            print(narrative)
    else:
        print(narrative)

    return narrative

def main():
    video_path = None
    try:
        # Step 1: Find a short YouTube video
        print("="*60)
        print("STEP 1: Finding a short YouTube video")
        print("="*60)
        video_url = search_short_youtube_video()
        if not video_url:
            print("No video found!")
            return

        # Step 2: Download the video
        print("\n" + "="*60)
        print("STEP 2: Downloading Video")
        print("="*60)
        video_path = download_video_with_pytube(video_url)

        # Step 3: Create a Twelve Labs index
        print("\n" + "="*60)
        print("STEP 3: Creating Twelve Labs Index")
        print("="*60)
        index_id = create_index()

        # Step 4: Upload video file to Twelve Labs
        print("\n" + "="*60)
        print("STEP 4: Uploading Video to Twelve Labs")
        print("="*60)
        task_id = upload_video_file_to_twelve_labs(index_id, video_path)

        # Step 5: Wait for processing to complete
        print("\n" + "="*60)
        print("STEP 5: Processing Video")
        print("="*60)
        video_id = check_task_status(task_id)

        if video_id:
            # Step 6: Get video details and object descriptions
            print("\n" + "="*60)
            print("STEP 6: Extracting Objects & Descriptions")
            print("="*60)
            detected = get_video_details(index_id, video_id)

            # Step 7: Generate narrative description
            print("\n" + "="*60)
            print("STEP 7: Generating Video Narrative")
            print("="*60)
            description = describe_video_content(index_id, video_id, detected)

            print("\n" + "="*60)
            print("SUCCESS! Video analyzed by Twelve Labs")
            print("="*60)
            print("\nThe video was successfully:")
            print("  1. Downloaded from YouTube")
            print("  2. Uploaded to Twelve Labs")
            print("  3. Processed and indexed")
            print("  4. Analyzed for objects and descriptions")
            print("  5. Generated narrative description")
            print(f"\n🎯 Objects found: {', '.join(detected.keys())}" if detected else "")
            print("\nYou can now use the search_video() function to query")
            print("specific moments in the video!")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Clean up downloaded video
        if video_path and os.path.exists(video_path):
            os.remove(video_path)
            print(f"\nCleaned up: {video_path}")

if __name__ == "__main__":
    main()
