import sys
import os
# Ensure project root is on sys.path so `nutribot` can be imported when running this script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from nutribot import i18n

def run_tests():
    langs = ['en', 'id', 'zh']
    keys = list(i18n._LOCALES.get('en', {}).keys())
    for lang in langs:
        print(f"--- Testing {lang} ---")
        for i in range(3):
            print(f"Run {i+1}:")
            for k in keys:
                v = i18n.translate(k, lang)
                print(f"{k} -> {v}")
            print()

if __name__ == '__main__':
    run_tests()
