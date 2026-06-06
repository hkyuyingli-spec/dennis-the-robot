import os
import uuid
import json
import time
from firebase_admin import credentials, firestore, initialize_app, get_app
from dotenv import load_dotenv

# Mocking the category detection from app.py
def detect_category(text):
    text = text.lower()
    keywords = {
        "Skincare": ["skin", "acne", "complexion", "glow", "dermatology", "ritual"],
        "TCM": ["qi", "meridians", "yin", "yang", "tongue", "pulse", "herbs", "bencao", "huangdi"],
        "Nutrition": ["diet", "food", "protein", "vitamin", "calories", "eating", "recipe"],
        "Wellness": ["stress", "sleep", "meditation", "mental", "anxiety", "constitution"],
        "Fitness": ["workout", "exercise", "gym", "muscle", "cardio", "activity"]
    }
    for category, tags in keywords.items():
        if any(tag in text for tag in tags):
            return category
    return "General"

def test_connectivity():
    print("--- 🧪 NutriBot Firebase Connectivity Test ---")
    
    # 1. Initialize Firebase
    try:
        if os.path.exists("serviceAccountKey.json"):
            cred = credentials.Certificate("serviceAccountKey.json")
            initialize_app(cred)
            print("✅ Firebase Initialized with serviceAccountKey.json")
        else:
            print("❌ Error: serviceAccountKey.json not found.")
            return
    except Exception as e:
        print(f"❌ Firebase Initialization Failed: {e}")
        return

    db = firestore.client()
    session_id = str(uuid.uuid4())
    print(f"🔹 Test Session ID: {session_id}\n")

    test_queries = [
        "I need help with my dry skin.",
        "Tell me about Ginseng benefits in TCM.",
        "What should I eat for better digestion?"
    ]

    # 2. Test 3 Log Entries
    for i, query in enumerate(test_queries, 1):
        print(f"Attempt {i}: Logging query -> '{query}'")
        try:
            category = detect_category(query)
            # Log to nutribot_logs
            log_ref = db.collection("nutribot_logs").add({
                "question": query,
                "category": category,
                "session_id": session_id,
                "timestamp": firestore.SERVER_TIMESTAMP,
                "test_run": True
            })
            print(f"   ✅ Logged to 'nutribot_logs' (ID: {log_ref[1].id})")
            
            # Log a mock metric for the first one
            if i == 1:
                metric_ref = db.collection("nutribot_metrics").add({
                    "event_type": "goal_selection",
                    "goal": "Better Skin",
                    "session_id": session_id,
                    "timestamp": firestore.SERVER_TIMESTAMP,
                    "test_run": True
                })
                print(f"   ✅ Logged interaction to 'nutribot_metrics' (ID: {metric_ref[1].id})")
            
            time.sleep(1) # Small delay
        except Exception as e:
            print(f"   ❌ Failed to log entry {i}: {e}")

    print("\n--- ✨ Connectivity Test Complete ---")
    print("Please check your Firebase Console to see the 3 documents in 'nutribot_logs' and 1 in 'nutribot_metrics'.")

if __name__ == "__main__":
    test_connectivity()
