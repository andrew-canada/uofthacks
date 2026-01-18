#The purpose of this file is to be a manager of the incoming data from the trends from perplexity and the video analysis of the twelve labs script. 
import sys

from shopify.storeinfo import pullstoreinfo
from trend_identification.trends import fetch_genz_trends
from video_analysis.analyze_trending_videos import analyze_trend
from pymongo import MongoClient
from config import MONGODB_CONNECTION_STRING

client = MongoClient(MONGODB_CONNECTION_STRING)

# Create/access database
db = client['thewinningteam']

# Create/access collection
collection = db['trends']

try:
    client.admin.command('ping')
    print("Successfully connected to MongoDB Atlas!")
except Exception:
    print(Exception)
    sys.exit()
    
ANALYZED_VIDEOS_COUNT_AT_A_TIME = 3
TRENDS_IDENTIFIED_COUNT_AT_A_TIME = 10

def updateandInitDBWithTrends():
    trendsJson = fetch_genz_trends(count=TRENDS_IDENTIFIED_COUNT_AT_A_TIME)
    for trend in trendsJson["trends"]:
        if count_documents({name:trendJson.name})!=0: # to check if not in database, then we initialize
            db.insert_one(trend | {"analyzed_videos":[]})
        trendJson = db.find_one({name:trendJson.name})
        existingVids = trendJson.analyzed_videos
        vidResults = analyze_trend(i["name"], count=ANALYZED_VIDEOS_COUNT_AT_A_TIME)
        for video in vidResults["sample_videos"]:
            if video["title"] not in [i["title"] for i in existingVids]:
                existingVids.append(video)
        trendJson["analyzed_videos"] = existingVids
        db.update_one({name:trendJson.name},trendJson)







