import os
import json
import re

LOCALES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "locales")

def _load_locales():
    locales = {}
    if not os.path.isdir(LOCALES_DIR):
        return locales
    for fname in os.listdir(LOCALES_DIR):
        if fname.endswith('.json'):
            lang = fname[:-5]
            path = os.path.join(LOCALES_DIR, fname)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    locales[lang] = json.load(f)
            except Exception:
                continue
    return locales

_LOCALES = _load_locales()
DEFAULT_LANG = 'en'

def supported_languages():
    return list(_LOCALES.keys())

def translate(key: str, lang: str = DEFAULT_LANG) -> str:
    if lang not in _LOCALES:
        lang = DEFAULT_LANG
    return _LOCALES.get(lang, {}).get(key, _LOCALES.get(DEFAULT_LANG, {}).get(key, key))

def detect_language(text: str | None = None, lang_hint: str | None = None) -> str | None:
    if lang_hint and lang_hint in _LOCALES:
        return lang_hint
    if not text:
        return None
    # Detect Chinese characters
    if re.search(r'[\u4e00-\u9fff]', text):
        return 'zh'
    # Simple Indonesian keyword check
    indonesian_words = ['halo', 'terima', 'terima kasih', 'apa kabar', 'selamat', 'saya', 'kamu', 'makan', 'makanan', 'kalori']
    low = text.lower()
    for w in indonesian_words:
        if w in low:
            return 'id'
    # Fallback to English
    return 'en'
