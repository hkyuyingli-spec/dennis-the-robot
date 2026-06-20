import os
import chatbot
from google import genai
from dotenv import load_dotenv
from nutribot import i18n

# determine language
current_lang = os.getenv('NUTRIBOT_LANG') or 'en'

def test_config():
    print(i18n.translate('verify_config_header', current_lang))
    
    # 1. Check model_id in chatbot.py
    print(i18n.translate('checking_model_id', current_lang).format(model_id=chatbot.model_id))
    if chatbot.model_id == "gemini-1.5-flash":
        print(i18n.translate('model_id_correct', current_lang))
    else:
        print(i18n.translate('model_id_incorrect', current_lang).format(model_id=chatbot.model_id))

    # 2. Check for the mandatory comment in app.py
    print("\n" + i18n.translate('checking_mandatory_comment', current_lang))
    with open("app.py", "r") as f:
        content = f.read()
        if 'model_id = "gemini-1.5-flash"  # DO NOT CHANGE THIS MODEL (1500 free requests/day)' in content:
            print(i18n.translate('mandatory_comment_found', current_lang))
        else:
            print(i18n.translate('mandatory_comment_not_found', current_lang))

    # 3. Test API Connectivity and Model usage
    print("\n" + i18n.translate('testing_api_connectivity', current_lang))
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print(i18n.translate('gemini_api_key_missing', current_lang))
        return

    client = genai.Client(api_key=api_key)
    try:
        # Simple prompt to verify the model
        response = client.models.generate_content(
            model=chatbot.model_id,
            contents="Say 'Beep Boop' if you are Gemini 1.5 Flash."
        )
        print(i18n.translate('response_from_model', current_lang).format(model=chatbot.model_id, text=response.text))
        print(i18n.translate('api_connectivity_success', current_lang))
    except Exception as e:
        print(i18n.translate('api_test_failed', current_lang).format(error=e))
        print(i18n.translate('attempting_fallback_test', current_lang))
        try:
            response = client.models.generate_content(
                model="gemini-1.5-flash-latest",
                contents="Say 'Beep Boop' if you are Gemini 1.5 Flash Latest."
            )
            print(i18n.translate('response_from_model', current_lang).format(model='gemini-1.5-flash-latest', text=response.text))
            print(i18n.translate('fallback_api_connectivity_success', current_lang))
        except Exception as e2:
            print(i18n.translate('fallback_api_test_failed', current_lang).format(error=e2))

if __name__ == "__main__":
    test_config()
