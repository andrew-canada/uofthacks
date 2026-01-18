from bson.json_util import dumps, loads
import json
from google import genai
from pymongo import MongoClient
from config import MONGODB_CONNECTION_STRING

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

def get_collection_as_json(collection):
    """
    Retrieves all documents from a MongoDB collection and returns them as JSON

    Args:
        collection: PyMongo collection object
        
    Returns:
        JSON string of all documents
    """
    # Get all documents from collection
    cursor = collection.find({})

    # Convert cursor to list of documents
    documents = list(cursor)

    # Convert to JSON string (handles ObjectId and other BSON types)
    json_data = dumps(documents, indent=2)

    return json_data

def gemini_transform(json_data):

    # The client gets the API key from the environment variable `GEMINI_API_KEY`.
    client = genai.Client(api_key="AIzaSyDYBGLh42TmXtTV5IjVZ8XsV29Cxz_35_Q")

    response = client.models.generate_content(
        model="gemini-3-flash-preview", contents="""
        
        Your job is to re-structure given data into another format, using the information we provided. The marketing angle will be directed towards shopify shop owners who will use these trends and advice to shape their products and be more marketable, choose the words you use to describe with that consideration. 


        The output should look like: 
        {
        "id": "trend_001",
        "name": "Aura Aesthetic",
        "description": "The 'aura' trend focuses on mysterious, ethereal vibes with dark academia influences. Think moody colors, vintage-inspired pieces, and an air of sophistication.",
        "keywords": ["mysterious", "ethereal", "dark academia", "moody", "vintage", "sophisticated", "timeless"],
        "color_palette": ["deep burgundy", "forest green", "charcoal", "cream", "navy"],
        "target_products": ["trench coats", "blazers", "turtlenecks", "wide-leg pants", "wool coats", "oxford shoes"],
        "marketing_angle": "Emphasize mystery, sophistication, and timeless elegance. Use phrases like 'cultivate your aura', 'mysterious elegance', 'timeless sophistication'",
        "popularity_score": 95,
        "platforms": ["TikTok", "Instagram", "Pinterest"],
        "demographics": ["Gen Z", "Young Millennials"],
        "hashtags": ["#aura", "#darkacademia", "#mysterious", "#ethereal"]
        },

        output ONLY JSON. Input:\n
        """+json.dumps(json_data)
    )
    return json.loads( response.text)


def write_to_data(data):
    with open(r"C:\Users\Atilla\Desktop\Code\UoftHacks13\uofthacks\backend\data\foundtrends.json", "w") as file:
        json.dump(data, file)


if __name__ =="__main__":
    db = initMongoDB()
    json_data = get_collection_as_json(db)
    new_json_data = gemini_transform(json_data)
    write_to_data(new_json_data)
