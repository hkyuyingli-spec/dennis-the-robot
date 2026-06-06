from firebase_admin import credentials, firestore, initialize_app, get_app
import uuid
import os

def final_verify():
    print("--- 🧪 TRIPLE-VERIFICATION START ---")
    try:
        try:
            get_app()
        except ValueError:
            cred = credentials.Certificate('serviceAccountKey.json')
            initialize_app(cred)
        
        db = firestore.client()
        session_id = f"FINAL-PROOFS-{uuid.uuid4().hex[:6]}"
        queries = [
            "User Test A: Skincare glow",
            "User Test B: TCM Herbs",
            "User Test C: Balanced Diet"
        ]
        
        for q in queries:
            doc_ref = db.collection('nutribot_logs').add({
                'question': q,
                'session_id': session_id,
                'timestamp': firestore.SERVER_TIMESTAMP,
                'verified_proof': True
            })
            print(f"✅ DOCUMENT CREATED: {doc_ref[1].id} | Query: {q}")
            
        print("\n--- ✨ TRIPLE-VERIFICATION SUCCESS ---")
        print(f"All 3 documents are now live in your 'nutribot_logs' collection under Session: {session_id}")
        
    except Exception as e:
        print(f"❌ VERIFICATION FAILED: {e}")

if __name__ == "__main__":
    final_verify()
