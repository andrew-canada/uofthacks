#The purpose of this file is to be a manager of the incoming data from the trends from perplexity and the video analysis of the twelve labs script. 
import sys

from shopify.storeinfo import pullstoreinfo
from trend_identification.trends import fetch_genz_trends
from video_analysis.analyze_trending_videos import analyze_trend
from pymongo import MongoClient
from config import MONGODB_CONNECTION_STRING
from datetime import datetime    
ANALYZED_VIDEOS_COUNT_AT_A_TIME = 1
TRENDS_IDENTIFIED_COUNT_AT_A_TIME = 10

def initMongoDB():
            
    client = MongoClient(MONGODB_CONNECTION_STRING)

    # Create/access database
    db = client['thewinningteam']

    # Create/access collection
    collection = db['trends']

    try:
        client.admin.command('ping')
        print("Successfully connected to MongoDB Atlas!")
    except Exception as a:
        print(a)
        sys.exit()
        

    return collection


def updateandInitDBWithTrends(db):
    print("Starting trend update...")
    
    trendsJson = fetch_genz_trends(count=TRENDS_IDENTIFIED_COUNT_AT_A_TIME)
    print(f"Fetched {len(trendsJson['trends'])} trends")
    
    for idx, trend in enumerate(trendsJson["trends"], 1):
        print(f"\nProcessing trend {idx}: {trend['name']}")
        
        # Check if trend exists in database
        existing_count = db.count_documents({"name": trend["name"]})
        
        if existing_count == 0:
            print(f"Inserting new trend: {trend['name']}")
            db.insert_one(trend | {"analyzed_videos": [], "last_analyzed":None })
        else:
            print(f"Trend already exists in database")
        
        # Retrieve the trend document
        trendJson = db.find_one({"name": trend["name"]})
        existingVids = trendJson["analyzed_videos"]
        print(f"Found {len(existingVids)} existing videos")
        
        # Analyze trend and get videos
        print(f"Analyzing videos for {trend['name']}...")
        vidResults = analyze_trend(trend["name"], count=ANALYZED_VIDEOS_COUNT_AT_A_TIME)
        print(f"Got {len(vidResults['sample_videos'])} sample videos")
        
        # Add new videos
        new_videos_added = 0
        for video in vidResults["sample_videos"]:
            if video["title"] not in [i["title"] for i in existingVids]:
                existingVids.append(video)
                new_videos_added += 1
        
        print(f"Added {new_videos_added} new videos")
        
        # Update the database
        print(f"Updating database...")
        result = db.update_one(
            {"name": trend["name"]},
            {"$set": {"analyzed_videos": existingVids}},

        )
        result = db.update_one(
            {"name": trend["name"]},
             {"$set":{"last_analyzed": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}},

        )


                   
        print(f"Updated {result.modified_count} documents")
    
    print("\nFinished updating trends")



if __name__ == "__main__":
    db=initMongoDB()
    updateandInitDBWithTrends(db)