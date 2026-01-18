"""
MongoDB Storage Module
Stores each Gemini trend recommendation as a separate document in MongoDB
"""

from pymongo import MongoClient
from datetime import datetime
import json
import sys
import os

# Add parent directory to path to import config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'video_analysis'))
from config import MONGODB_CONNECTION_STRING


def store_gemini_recommendations(recommendations_json_path):
    """
    Stores each trend as a separate document in MongoDB
    Each trend becomes its own document with all fields flattened

    Args:
        recommendations_json_path: Path to Gemini recommendations JSON file

    Returns:
        list: List of MongoDB document IDs
    """

    print("Loading recommendations...")

    # Load recommendations
    try:
        with open(recommendations_json_path, 'r') as f:
            data = json.load(f)
        print(f"✓ Loaded recommendations ({len(data.get('trends', []))} trends)")
    except FileNotFoundError:
        print(f"✗ Error: {recommendations_json_path} not found")
        raise
    except json.JSONDecodeError as e:
        print(f"✗ Error parsing {recommendations_json_path}: {e}")
        raise

    # Connect to MongoDB
    print("Connecting to MongoDB...")
    try:
        client = MongoClient(MONGODB_CONNECTION_STRING)

        # Test connection
        client.admin.command('ping')
        print("✓ Connected to MongoDB Atlas")

        # Access database and collection
        db = client["thewinningteam"]
        collection = db["trends"]  # Changed to "trends" collection

    except Exception as e:
        print(f"✗ Error connecting to MongoDB: {e}")
        raise

    print(f"Storing individual trend documents in MongoDB...")

    try:
        # Clear old trends (overwrite strategy)
        delete_result = collection.delete_many({})
        print(f"✓ Cleared {delete_result.deleted_count} old trend(s)")

        # Insert each trend as a separate document
        inserted_ids = []
        trends = data.get("trends", [])

        for trend in trends:
            # Create document with trend data + metadata
            trend_document = {
                **trend,  # Spread all trend fields (id, name, description, etc.)
                "last_updated": data.get("last_updated"),
                "source": data.get("source", "Gemini Analysis"),
                "version": data.get("version", "1.0"),
                "created_at": datetime.now()
            }

            result = collection.insert_one(trend_document)
            inserted_ids.append(str(result.inserted_id))
            print(f"  ✓ Stored trend: {trend.get('name')} (ID: {result.inserted_id})")

        print(f"\n✓ Stored {len(inserted_ids)} trend documents successfully")

        return inserted_ids

    except Exception as e:
        print(f"✗ Error storing recommendations in MongoDB: {e}")
        raise
    finally:
        client.close()


def retrieve_all_trends():
    """
    Retrieves all trend documents from MongoDB

    Returns:
        list: List of trend documents
    """

    print("Connecting to MongoDB...")
    try:
        client = MongoClient(MONGODB_CONNECTION_STRING)
        client.admin.command('ping')

        db = client["thewinningteam"]
        collection = db["trends"]

        # Get all trend documents, sorted by created_at
        trends = list(collection.find().sort("created_at", -1))

        if not trends:
            print("✗ No trends found in MongoDB")
            return []

        print(f"✓ Retrieved {len(trends)} trend documents")

        return trends

    except Exception as e:
        print(f"✗ Error retrieving trends: {e}")
        raise
    finally:
        client.close()


def retrieve_trend_by_id(trend_id):
    """
    Retrieves a specific trend by ID

    Args:
        trend_id: The trend ID (e.g., "1", "2", etc.)

    Returns:
        dict: Trend document or None
    """

    try:
        client = MongoClient(MONGODB_CONNECTION_STRING)
        client.admin.command('ping')

        db = client["thewinningteam"]
        collection = db["trends"]

        # Find trend by id field
        trend = collection.find_one({"id": trend_id})

        if trend:
            print(f"✓ Retrieved trend: {trend.get('name')}")
        else:
            print(f"✗ Trend with ID {trend_id} not found")

        return trend

    except Exception as e:
        print(f"✗ Error retrieving trend: {e}")
        raise
    finally:
        client.close()


if __name__ == "__main__":
    # Test the module
    print("Testing MongoDB Storage...")
    print("=" * 60)

    # Test storing
    try:
        doc_ids = store_gemini_recommendations("gemini_recommendations.json")
        print(f"\n✓ Stored {len(doc_ids)} trend documents")
    except Exception as e:
        print(f"\n✗ Storage test failed: {e}")
        sys.exit(1)

    # Test retrieving all
    try:
        print("\n" + "=" * 60)
        print("Testing retrieval of all trends...")
        print("=" * 60)
        trends = retrieve_all_trends()
        if trends:
            print(f"\nFirst trend example:")
            first = trends[0]
            print(f"  Name: {first.get('name')}")
            print(f"  ID: {first.get('id')}")
            print(f"  Keywords: {first.get('keywords')}")
            print(f"  Target Products: {first.get('target_products')}")
            print(f"  Popularity Score: {first.get('popularity_score')}")
    except Exception as e:
        print(f"\n✗ Retrieval test failed: {e}")
        sys.exit(1)

    # Test retrieving specific trend
    try:
        print("\n" + "=" * 60)
        print("Testing retrieval of specific trend (ID: 2)...")
        print("=" * 60)
        trend = retrieve_trend_by_id("2")
        if trend:
            print(f"  Name: {trend.get('name')}")
            print(f"  Description: {trend.get('description')}")
    except Exception as e:
        print(f"\n✗ Specific retrieval test failed: {e}")
        sys.exit(1)
