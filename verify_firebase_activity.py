import os
import sys
import json
from datetime import datetime

# Set stdout encoding to UTF-8 for Windows console support
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Import helper functions from analyze_firebase
try:
    from analyze_firebase import init_firebase, fetch_collections
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def default_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)

def verify_firestore():
    print("=== Firebase Firestore Activity Verification ===")
    print("Connecting to Firestore using serviceAccountKey.json...")
    
    try:
        db = init_firebase()
        print(" Successfully connected to Firestore.\n")
    except Exception as e:
        print(f" Failed to connect to Firestore: {e}")
        sys.exit(1)

    print("Fetching collection data...")
    collections_map = {
        "users": "users",
        "nutribot_logs": "logs",
        "nutribot_metrics": "metrics"
    }

    try:
        data = fetch_collections(db)
        print(" Data fetched successfully.\n")
    except Exception as e:
        print(f" Failed to fetch collections: {e}")
        sys.exit(1)

    for col_name, key in collections_map.items():
        docs = data.get(key, [])
        doc_count = len(docs)
        print("--------------------------------------------------")
        print(f" Collection: '{col_name}' (Mapped Key: '{key}')")
        print(f" Total Documents: {doc_count}")

        if doc_count > 0:
            sample_doc = docs[0]
            print(f" Sample Document (ID: {sample_doc.get('id', 'N/A')}):")
            # Create a clean preview of document fields
            sample_preview = {k: v for k, v in sample_doc.items() if k != 'id'}
            print(json.dumps(sample_preview, indent=4, default=default_serializer))
        else:
            print(" No documents found in this collection.")
        print()

if __name__ == "__main__":
    verify_firestore()
