import requests
import time
import os
import json
import random
import re
from pytubefix import YouTube

# ==========================================
# CONFIGURATION
# ==========================================
try:
    from config import TWELVE_LABS_API_KEY, YOUTUBE_API_KEY, TWELVE_LABS_BASE_URL
except ImportError:
    print("❌ Error: config.py not found! Please ensure your keys are set.")
    # You can set defaults here if needed for testing
    TWELVE_LABS_BASE_URL = "https://api.twelvelabs.io/v1.2" 
    exit(1)

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def parse_duration(duration_str):
    """Parse ISO 8601 duration format (PT#M#S) to seconds"""
    pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
    match = re.match(pattern, duration_str)
    if not match:
        return 0

    # Safely convert matched groups (they may be None)
    hours = int(match.group(1)) if match.group(1) is not None else 0
    minutes = int(match.group(2)) if match.group(2) is not None else 0
    seconds = int(match.group(3)) if match.group(3) is not None else 0
    return hours * 3600 + minutes * 60 + seconds

def clean_text(text):
    """Cleans up API output"""
    if not text: return ""
    return text.strip().replace('"', '').replace("'", "").replace("\n", " ")

# ==========================================
# YOUTUBE SEARCH
# ==========================================

def get_trending_videos(max_results=2, trend_filter=None):
    """Fetches trending Shorts."""
    print(f"\n🔎 Searching for videos related to: '{trend_filter}'...")

    search_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        'part': 'snippet',
        'q': trend_filter,
        'type': 'video',
        'videoDuration': 'short',
        'maxResults': 15,
        'order': 'relevance', 
        'key': YOUTUBE_API_KEY
    }
    
    try:
        res = requests.get(search_url, params=params)
        res.raise_for_status()
        search_items = res.json().get('items', [])
    except Exception as e:
        print(f"  ❌ YouTube API Error: {e}")
        return []

    video_ids = [item['id']['videoId'] for item in search_items]
    if not video_ids:
        print("  ⚠️ No videos found.")
        return []

    # Get details to filter by duration/views
    details_url = "https://www.googleapis.com/youtube/v3/videos"
    details_params = {
        'part': 'snippet,statistics,contentDetails',
        'id': ','.join(video_ids),
        'key': YOUTUBE_API_KEY
    }
    
    details_res = requests.get(details_url, params=details_params)
    details_data = details_res.json().get('items', [])

    valid_videos = []
    for item in details_data:
        duration = parse_duration(item['contentDetails'].get('duration', 'PT0S'))
        if 0 < duration <= 90: # Allow slightly longer shorts
            title = item['snippet']['title']
            # Filter out music videos which often block downloads or have no "content"
            if "official music video" not in title.lower():
                valid_videos.append({
                    'video_id': item['id'],
                    'url': f"https://www.youtube.com/watch?v={item['id']}",
                    'title': title,
                    'tags': item['snippet'].get('tags', []),
                    'views': int(item['statistics'].get('viewCount', 0)),
                    'likes': int(item['statistics'].get('likeCount', 0))
                })

    valid_videos.sort(key=lambda x: x['views'], reverse=True)
    return valid_videos[:max_results]

def download_video(url, filename):
    try:
        yt = YouTube(url)
        # Try getting highest resolution mp4, fallback to first
        stream = yt.streams.filter(file_extension='mp4').get_highest_resolution()
        if not stream:
            stream = yt.streams.filter(file_extension='mp4').first()
            
        print(f"  ⬇️  Downloading: {yt.title[:30]}...")
        stream.download(filename=filename)
        return True
    except Exception as e:
        print(f"  ❌ Download failed: {e}")
        return False

# ==========================================
# TWELVE LABS (ROBUST)
# ==========================================

def create_smart_index():
    """Attempts to create a Pegasus index, falls back to Marengo if failed."""
    url = f"{TWELVE_LABS_BASE_URL}/indexes"
    headers = {"x-api-key": TWELVE_LABS_API_KEY, "Content-Type": "application/json"}
    
    index_name = f"trend_analysis_{int(time.time())}"
    
    # 1. Try PEGASUS (Generative)
    try:
        print("  ⚙️  Attempting to create Pegasus-1 index (Best for details)...")
        data = {
            "index_name": index_name + "_pegasus",
            "models": [{"model_name": "pegasus1.2", "model_options": ["visual", "audio"]}]
        }
        res = requests.post(url, headers=headers, json=data)
        if res.status_code == 201:
            print("  ✅ Pegasus Index Created!")
            return res.json()['_id']
        else:
            print(f"  ⚠️ Pegasus creation failed ({res.status_code}): {res.text}")
    except Exception as e:
        print(f"  ⚠️ Connection error: {e}")

    # 2. Fallback to MARENGO (Standard)
    print("  ⚙️  Falling back to Marengo-2.6 index...")
    data = {
        "index_name": index_name + "_marengo",
        "models": [{"model_name": "marengo2.6", "model_options": ["visual", "audio"]}]
    }
    try:
        res = requests.post(url, headers=headers, json=data)
        res.raise_for_status()
        print("  ✅ Marengo Index Created!")
        return res.json()['_id']
    except Exception as e:
        print(f"  ❌ CRITICAL: Could not create any index. {e}")
        if 'res' in locals(): print(f"  API Response: {res.text}")
        return None

def index_video(index_id, video_path):
    url = f"{TWELVE_LABS_BASE_URL}/tasks"
    headers = {"x-api-key": TWELVE_LABS_API_KEY}
    
    with open(video_path, 'rb') as f:
        files = {'video_file': (os.path.basename(video_path), f, 'video/mp4')}
        data = {'index_id': index_id, 'language': 'en'}
        try:
            res = requests.post(url, headers=headers, files=files, data=data)
            res.raise_for_status()
            return res.json().get('_id')
        except Exception as e:
            print(f"  ❌ Upload failed: {e}")
            print(f"  Response: {res.text}")
            return None

def wait_for_task(task_id):
    url = f"{TWELVE_LABS_BASE_URL}/tasks/{task_id}"
    headers = {"x-api-key": TWELVE_LABS_API_KEY}
    
    print("  ⏳ Processing...", end="", flush=True)
    while True:
        res = requests.get(url, headers=headers)
        status = res.json().get('status')
        if status == 'ready':
            print(" Done!")
            # WARM UP: Give the index a moment to propagate
            time.sleep(2)
            return res.json().get('video_id')
        if status == 'failed':
            print(f" Failed! Reason: {res.json().get('process_result')}")
            return None
        time.sleep(2)
        print(".", end="", flush=True)

def generate_text_robust(video_id, prompt):
    """
    Tries Generate endpoint with stream=False to avoid JSON errors.
    Fallback to stream parsing if API ignores the flag.
    """
    headers = {"x-api-key": TWELVE_LABS_API_KEY, "Content-Type": "application/json"}
    
    # STRATEGY A: /analyze endpoint (Detailed)
    url_gen = f"{TWELVE_LABS_BASE_URL}/analyze"
    payload_gen = {
        "video_id": video_id,
        "prompt": prompt,
        "temperature": 0.5,
        "stream": False  # <--- FIX: Disable streaming to get a single JSON object
    }
    
    try:
        res = requests.post(url_gen, headers=headers, json=payload_gen)
        
        if res.status_code == 200:
            try:
                # Try standard parsing
                return res.json().get('data', '')
            except json.JSONDecodeError:
                # ROBUSTNESS: If API returns stream despite stream=False, parse line-by-line
                # The error "Extra data" means multiple JSON objects are present
                print("  ⚠️ Streaming response detected, assembling manually...")
                full_text = []
                for line in res.text.strip().split('\n'):
                    try:
                        if line.strip():
                            obj = json.loads(line)
                            if 'data' in obj:
                                full_text.append(obj['data'])
                    except:
                        continue
                return "".join(full_text)
        else:
            print(f"\n  ⚠️ Generate API Error ({res.status_code}): {res.text}")
    except Exception as e:
        print(f"\n  ⚠️ Request Error: {e}")

    # STRATEGY B: /summarize endpoint (Fallback)
    print("  🔄 Switching to Summarize endpoint...")
    url_sum = f"{TWELVE_LABS_BASE_URL}/summarize"
    payload_sum = {
        "video_id": video_id,
        "type": "summary" 
    }
    
    try:
        res = requests.post(url_sum, headers=headers, json=payload_sum)
        if res.status_code == 200:
            return res.json().get('summary', '')
        else:
            print(f"  ❌ Summarize API Error ({res.status_code}): {res.text}")
            return f"Error analyzing video: API returned {res.status_code}"
    except:
        return "Error analyzing video: Connection failed."

def analyze_video_content(video_id, video_metadata):
    # 1. Visual Narrative
    narrative_prompt = (
        "Write a detailed visual description of this video. "
        "Describe specific actions, especially objects, and the setting chronologically. "
        "Do not be generic."
    )
    what_happened = generate_text_robust(video_id, narrative_prompt)
    
    # 2. Trending Analysis
    trend_prompt = (
        "List 3 reasons why this video is engaging based on its visual style and content via a physical, marketable insigths. Identify material descriptions/insights about the trend."
    )
    trend_raw = generate_text_robust(video_id, trend_prompt)
    
    # Parse trend reasons
    reasons = []
    if trend_raw and "Error" not in trend_raw:
        lines = trend_raw.split('\n')
        for line in lines:
            cleaned = line.strip().lstrip('-•123456789. ')
            if len(cleaned) > 10:
                reasons.append(cleaned)
    
    if not reasons:
        reasons = ["Content analysis failed - check API logs"]

    return what_happened, reasons[:3]


def analyze_trend(trend):
       
    # 1. Get Videos
    videos = get_trending_videos(max_results=3+5, trend_filter=trend) # 3 being the targeted amount
    if not videos: return

    # 2. Create Index (Auto-switching)
    index_id = create_smart_index()
    if not index_id: return

    analyzed_data = []
    
    # 3. Process
    counter = 0
    for vid in videos:
        if counter == 3:break
        
        #could implement a buffer trend video logic to fix some of the videos failing issue (having 5 videos to process and processing until 2 of them are ok)
        print(f"\n🎥 Processing: {vid['title'][:50]}...")
        filename = f"temp_{vid['video_id']}.mp4"
        
        if download_video(vid['url'], filename):
            counter +=1
            task_id = index_video(index_id, filename)
            if task_id:
                video_id = wait_for_task(task_id)
                if video_id:
                    print("  🧠 Analyzing content...")
                    what, why = analyze_video_content(video_id, vid)
                    
                    analyzed_data.append({
                        "title": vid['title'],
                        "url": vid['url'],
                        "what_is_happening": what,
                        "why_its_trending": why
                    })
                    print("  ✓ Done")
            
            if os.path.exists(filename): os.remove(filename)

    # 4. Save
    output = {
        "trend_name": trend,
        "sample_videos": analyzed_data
    }
    
    return output
    
# ==========================================
# MAIN EXECUTION
# ==========================================

def main():
    print("\n" + "="*50)
    print(" 🛠️  ROBUST TREND ANALYZER (Debug Mode)")
    print("="*50)
    
    # Explicitly asking for a visually rich trend to test capabilities
    trend = "labubu" 
    
    output = analyze_trend(trend)
    with open("robust_analysis.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print("\n✅ Analysis saved to robust_analysis.json")
    if analyzed_data:
        print("\n--- SAMPLE OUTPUT ---")
        print(f"What: {analyzed_data[0]['what_is_happening'][:150]}...")

if __name__ == "__main__":
    main()