import os
import time
from groq import Groq, RateLimitError, InternalServerError, APIStatusError
from dotenv import load_dotenv

# Load API Key
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)

MODEL_PRIMARY = "llama-3.1-8b-instant"
MODEL_FALLBACK = "mixtral-8x7b-32768"

def test_pro_streaming(query_index, query_text):
    print(f"\n--- 🧪 Pro-Level Test {query_index}: '{query_text}' ---")
    
    personality = "You are a helpful TCM assistant. Speak briefly."
    messages = [
        {"role": "system", "content": personality},
        {"role": "user", "content": query_text}
    ]

    print("📡 Contacting Groq (Streaming Enabled)...")
    full_response = ""
    start_time = time.time()
    
    try:
        completion = client.chat.completions.create(
            model=MODEL_PRIMARY,
            messages=messages,
            max_tokens=100,
            temperature=0.7,
            stream=True
        )

        print("🌊 Stream received: ", end="", flush=True)
        for chunk in completion:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response += content
                print(content, end="", flush=True)
        
        duration = time.time() - start_time
        print(f"\n\n✅ Success! Response received in {duration:.2f}s")
        
    except (RateLimitError, InternalServerError, APIStatusError) as e:
        print(f"\n⚠️ Caught expected API error: {type(e).__name__}. Attempting Fallback...")
        # Fallback simulation
        try:
            completion = client.chat.completions.create(
                model=MODEL_FALLBACK,
                messages=messages,
                max_tokens=100,
                temperature=0.7,
                stream=True
            )
            print("🌊 Fallback Stream received: ", end="", flush=True)
            for chunk in completion:
                if chunk.choices[0].delta.content:
                    print(chunk.choices[0].delta.content, end="", flush=True)
            print("\n✅ Fallback Success!")
        except Exception as fe:
            print(f"❌ Fallback also failed: {fe}")
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")

if __name__ == "__main__":
    queries = [
        "What is Qi?",
        "Best herb for sleep?",
        "How to balance Yin and Yang?"
    ]
    
    for i, q in enumerate(queries, 1):
        test_pro_streaming(i, q)
        time.sleep(1) # Respect rate limits between tests
