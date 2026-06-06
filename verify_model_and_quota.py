import os
import chatbot
from google import genai
from dotenv import load_dotenv

def test_config():
    print("--- 🔍 Dennis Configuration Verification 🔍 ---")
    
    # 1. Check model_id in chatbot.py
    print(f"Checking model_id in chatbot.py: {chatbot.model_id}")
    if chatbot.model_id == "gemini-1.5-flash":
        print("✅ model_id is correctly set to gemini-1.5-flash")
    else:
        print(f"❌ model_id is {chatbot.model_id}, expected gemini-1.5-flash")

    # 2. Check for the mandatory comment in app.py
    print("\nChecking for mandatory comment in app.py...")
    with open("app.py", "r") as f:
        content = f.read()
        if 'model_id = "gemini-1.5-flash"  # DO NOT CHANGE THIS MODEL (1500 free requests/day)' in content:
            print("✅ Mandatory comment found in app.py")
        else:
            print("❌ Mandatory comment NOT found in app.py")

    # 3. Test API Connectivity and Model usage
    print("\nTesting API Connectivity...")
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found in .env")
        return

    client = genai.Client(api_key=api_key)
    try:
        # Simple prompt to verify the model
        response = client.models.generate_content(
            model=chatbot.model_id,
            contents="Say 'Beep Boop' if you are Gemini 1.5 Flash."
        )
        print(f"Response from {chatbot.model_id}: {response.text}")
        print("✅ API Connectivity successful!")
    except Exception as e:
        print(f"❌ API Test failed: {e}")
        print("Attempting fallback test...")
        try:
            response = client.models.generate_content(
                model="gemini-1.5-flash-latest",
                contents="Say 'Beep Boop' if you are Gemini 1.5 Flash Latest."
            )
            print(f"Response from gemini-1.5-flash-latest: {response.text}")
            print("✅ Fallback API Connectivity successful!")
        except Exception as e2:
            print(f"❌ Fallback API Test failed: {e2}")

if __name__ == "__main__":
    test_config()
