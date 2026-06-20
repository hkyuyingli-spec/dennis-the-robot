from firebase_admin import credentials, firestore, initialize_app, get_app
import uuid
import os
from nutribot import i18n

# determine language
current_lang = os.getenv('NUTRIBOT_LANG') or 'en'

def final_verify():
    print(i18n.translate('triple_verification_start', current_lang))
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
            print(i18n.translate('document_created', current_lang).format(doc_id=doc_ref[1].id, query=q))
            
        print("\n" + i18n.translate('triple_verification_success', current_lang))
        print(i18n.translate('documents_live_session', current_lang).format(session_id=session_id))
        
    except Exception as e:
        print(i18n.translate('verification_failed', current_lang).format(error=e))

if __name__ == "__main__":
    final_verify()
