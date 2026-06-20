import os
import uuid
import json
import time
from firebase_admin import credentials, firestore, initialize_app, get_app
from dotenv import load_dotenv
from nutribot import i18n
import os

current_lang = os.getenv('NUTRIBOT_LANG') or 'en'

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
    print(i18n.translate('firebase_connectivity_header', current_lang))
    
    # 1. Initialize Firebase
    try:
        if os.path.exists("serviceAccountKey.json"):
            cred = credentials.Certificate("serviceAccountKey.json")
            initialize_app(cred)
            print(i18n.translate('firebase_initialized', current_lang))
        else:
            print(i18n.translate('service_account_not_found', current_lang))
            return
    except Exception as e:
        print(i18n.translate('firebase_init_failed', current_lang).format(error=e))
        return

    db = firestore.client()
    session_id = str(uuid.uuid4())
    print(i18n.translate('test_session_id_label', current_lang).format(session_id=session_id) + "\n")

    test_queries = [
        "I need help with my dry skin.",
        "Tell me about Ginseng benefits in TCM.",
        "What should I eat for better digestion?"
    ]

    # 2. Test 3 Log Entries
    for i, query in enumerate(test_queries, 1):
        print(i18n.translate('attempt_logging_query', current_lang).format(i=i, query=query))
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
            print(i18n.translate('logged_to_nutribot_logs', current_lang).format(doc_id=log_ref[1].id))
            
            # Log a mock metric for the first one
            if i == 1:
                metric_ref = db.collection("nutribot_metrics").add({
                    "event_type": "goal_selection",
                    "goal": "Better Skin",
                    "session_id": session_id,
                    "timestamp": firestore.SERVER_TIMESTAMP,
                    "test_run": True
                })
                print(i18n.translate('logged_interaction_nutribot_metrics', current_lang).format(metric_id=metric_ref[1].id))
            
            time.sleep(1) # Small delay
        except Exception as e:
            print(i18n.translate('failed_to_log_entry', current_lang).format(i=i, error=e))

    print("\n" + i18n.translate('connectivity_test_complete', current_lang))
    print(i18n.translate('check_firebase_console', current_lang))

if __name__ == "__main__":
    test_connectivity()
