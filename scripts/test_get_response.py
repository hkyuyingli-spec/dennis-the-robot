import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from chatbot import get_response
from nutribot import i18n

languages = ["en", "id", "zh"]

prompts = [
    "What's my daily calorie goal?",
    "Recommend a TCM herb for digestion.",
    "Calculate ROI: invest 100, return 150.",
]

for lang in languages:
    print("\n=== Testing language:", lang, "===")
    print(i18n.translate("startup_header", lang).format(model_id="gemini-1.5-flash"))
    for i in range(3):
        prompt = prompts[i % len(prompts)]
        resp = get_response(prompt, lang=lang)
        if "error" in resp:
            print(f"ERROR ({lang}): {resp['error']}")
        else:
            print(f"Prompt ({lang}): {prompt}")
            print(f"Response ({lang}): {resp['text']}")
