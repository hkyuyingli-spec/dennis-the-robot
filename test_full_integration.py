import os
import uuid
import time
from groq import Groq
from firebase_admin import credentials, firestore, initialize_app, get_app
from dotenv import load_dotenv
from nutribot import i18n
import os

# language
current_lang = os.getenv('NUTRIBOT_LANG') or 'en'

# --- MOCKING LOGIC FROM APP.PY ---
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

def test_full_cycle():
    print(i18n.translate('integration_test_header', current_lang))
    
    # 1. Setup
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")
    client = Groq(api_key=api_key)
    
    try:
        if not get_app():
            cred = credentials.Certificate("serviceAccountKey.json")
            initialize_app(cred)
    except ValueError:
        cred = credentials.Certificate("serviceAccountKey.json")
        initialize_app(cred)
    
    db = firestore.client()
    session_id = f"INTEGRATION-TEST-{uuid.uuid4().hex[:8]}"
    print(i18n.translate('session_id_label', current_lang).format(session_id=session_id) + "\n")

    test_scenarios = [
        {"q": "My skin is glowing but a bit dry.", "expected": "Skincare"},
        {"q": "What is the Five Elements theory?", "expected": "TCM"},
        {"q": "Best recipe for protein-rich diet.", "expected": "Nutrition"}
    ]

    for i, scenario in enumerate(test_scenarios, 1):
        query = scenario["q"]
        print(i18n.translate('step_query', current_lang).format(step=i, query=query))
        
        # A. Test AI Response (Streaming)
        print(i18n.translate('ai_response_prefix', current_lang), end="", flush=True)
        full_reply = ""
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": query}],
            stream=True
        )
        for chunk in completion:
            if chunk.choices[0].delta.content:
                text = chunk.choices[0].delta.content
                full_reply += text
                print(text, end="", flush=True)
        print("\n")

        # B. Test Database Logging
        print(i18n.translate('writing_to_database', current_lang))
        category = detect_category(query)
        try:
            doc_ref = db.collection("nutribot_logs").add({
                "question": query,
                "answer_preview": full_reply[:50] + "...",
                "category": category,
                "session_id": session_id,
                "timestamp": firestore.SERVER_TIMESTAMP,
                "is_integration_test": True
            })
            print(i18n.translate('success_document_id', current_lang).format(doc_id=doc_ref[1].id))
            print(i18n.translate('detected_category', current_lang).format(category=category, expected=scenario['expected']))
        except Exception as e:
            print(i18n.translate('database_write_failed', current_lang).format(error=e))
        print("-" * 40)
        time.sleep(1)

    print("\n✨ ALL TESTS PASSED: AI is responding and Database is recording.")

if __name__ == "__main__":
    test_full_cycle()
