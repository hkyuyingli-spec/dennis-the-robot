import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from nutribot.rag import (
    load_cancer_education,
    find_relevant_cancer_education,
    is_personal_symptom_query,
    cancer_personal_redirect_response,
)


def run_tests():
    data = load_cancer_education()
    tests = [
        ("What is cancer?", True),
        ("I have a lump, is it dangerous?", False)
    ]
    for prompt, expect_general in tests:
        print("\n=== Prompt ===")
        print(prompt)
        personal = is_personal_symptom_query(prompt)
        print("Detected personal-symptom:", personal)
        if personal:
            print("Response (redirect):\n", cancer_personal_redirect_response())
        else:
            matches = find_relevant_cancer_education(prompt, data)
            print("Matches found:", len(matches))
            for m in matches:
                print("-", m.get("topic_id"), m.get("topic_name"))


if __name__ == '__main__':
    run_tests()
