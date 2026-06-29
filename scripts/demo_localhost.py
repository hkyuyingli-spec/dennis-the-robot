import sys
import os
import textwrap

# ensure project root on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from nutribot import i18n

def demo(lang='en'):
    os.environ['NUTRIBOT_LANG'] = lang
    header = i18n.translate('startup_header', lang).format(model_id='gemini-1.5-flash')
    prompt = i18n.translate('user_prompt', lang)
    assistant_label = i18n.translate('assistant_label', lang)
    goodbye = i18n.translate('goodbye', lang)

    print(header)
    print(i18n.translate('type_quit', lang))
    print()

    examples = [
        "Hello, what's my daily calorie goal?",
        "Tell me a TCM herb for digestion.",
        "Calculate ROI: invest 100, return 150."
    ]

    for q in examples:
        print(f"{prompt}{q}")
        # Simulated reply (do not call external APIs)
        reply = f"This is a simulated reply to: {q}"
        print(f"{assistant_label} {reply}\n")

    print(goodbye)

if __name__ == '__main__':
    lang = sys.argv[1] if len(sys.argv) > 1 else 'en'
    demo(lang)
