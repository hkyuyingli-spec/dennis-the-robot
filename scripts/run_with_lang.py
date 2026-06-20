import sys
import os
import runpy
import sys
import os

# ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def main():
    lang = sys.argv[1] if len(sys.argv) > 1 else 'en'
    os.environ['NUTRIBOT_LANG'] = lang
    print(f"Running test_firebase_connectivity.py with NUTRIBOT_LANG={lang}\n")
    runpy.run_path('test_firebase_connectivity.py', run_name='__main__')

if __name__ == '__main__':
    main()
