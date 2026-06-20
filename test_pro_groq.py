import os
import time
from groq import Groq, RateLimitError, InternalServerError, APIStatusError
from dotenv import load_dotenv
from nutribot import i18n
import os

current_lang = os.getenv('NUTRIBOT_LANG') or 'en'

# Load API Key
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)

MODEL_PRIMARY = "llama-3.1-8b-instant"
MODEL_FALLBACK = "mixtral-8x7b-32768"

def test_pro_streaming(query_index, query_text):
    print(i18n.translate('pro_test_header', current_lang).format(index=query_index, query=query_text))
    
    personality = "You are a helpful TCM assistant. Speak briefly."
    messages = [
        {"role": "system", "content": personality},
        {"role": "user", "content": query_text}
    ]

    print(i18n.translate('contacting_groq', current_lang))
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

        print(i18n.translate('stream_received', current_lang), end="", flush=True)
        for chunk in completion:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response += content
                print(content, end="", flush=True)
        
        duration = time.time() - start_time
        print(i18n.translate('success_response_time', current_lang).format(duration=duration))
        
    except (RateLimitError, InternalServerError, APIStatusError) as e:
        print(i18n.translate('caught_api_error_attempting_fallback', current_lang).format(error_type=type(e).__name__))
        # Fallback simulation
        try:
            completion = client.chat.completions.create(
                model=MODEL_FALLBACK,
                messages=messages,
                max_tokens=100,
                temperature=0.7,
                stream=True
            )
            print(i18n.translate('fallback_stream_received', current_lang), end="", flush=True)
            for chunk in completion:
                if chunk.choices[0].delta.content:
                    print(chunk.choices[0].delta.content, end="", flush=True)
            print(i18n.translate('fallback_success', current_lang))
        except Exception as fe:
            print(i18n.translate('fallback_failed', current_lang).format(error=fe))
    except Exception as e:
        print(i18n.translate('unexpected_error', current_lang).format(error=e))

if __name__ == "__main__":
    queries = [
        "What is Qi?",
        "Best herb for sleep?",
        "How to balance Yin and Yang?"
    ]
    
    for i, q in enumerate(queries, 1):
        test_pro_streaming(i, q)
        time.sleep(1) # Respect rate limits between tests
