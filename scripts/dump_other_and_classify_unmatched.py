"""Dump 'other' cluster entries and classify unmatched questions as noise vs genuine.

Usage: python scripts/dump_other_and_classify_unmatched.py
"""
from pathlib import Path
import sys
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from collections import Counter
import firebase_admin
from firebase_admin import credentials, firestore
from nutribot.rag import (
    load_tcm_constitutions,
    load_tcm_herbs_formulas,
    find_relevant_constitutions,
    find_relevant_herbs_formulas,
)


def is_noise(text):
    if not text:
        return True
    t = text.lower().strip()
    # Common noise patterns
    noise_starts = ["who r", "who are", "who r u", "who are you", "who r u", "who r u?", "who r u",
                    "hi", "hello", "hey", "whats up", "what's up", "u got it", "u good", "thanks", "thank you"]
    for s in noise_starts:
        if t.startswith(s):
            return True
    if "user test" in t or "debug" in t or "test" == t or t.startswith("user test") or "debug_live_chat_test" in t.lower():
        return True
    if len(t) <= 3 and (t in {"?", "", "yes", "no", "ok"}):
        return True
    # Off-topic patterns (non-health)
    off_topic_keywords = ["social media", "map", "oppo", "mobile phone", "math", "matematika", "social media", "where can i buy", "what social media", "what is oppo", "products in indonesia", "show me indonesia map"]
    for kw in off_topic_keywords:
        if kw in t:
            return True
    # Very short single-word non-medical interactions
    if len(t.split()) <= 2 and not any(c.isalpha() for c in t):
        return True
    return False


def cluster_question(q_text):
    q = (q_text or "").lower()
    clusters = {
        "skincare-related": ["skin", "acne", "eczema", "rash", "pimple", "complexion", "dermat"],
        "sleep-related": ["sleep", "insomnia", "sleepless", "nap", "dream"],
        "weight/diet-related": ["weight", "lose weight", "gain weight", "diet", "calorie", "obese"],
        "reproductive/pregnancy": ["pregnant", "pregnancy", "fertility", "menstrual", "period"],
        "medication/interaction": ["medication", "meds", "ibuprofen", "aspirin", "antibiotic", "warfarin", "blood thinner"],
        "general-tcm": ["qi", "yin", "yang", "meridian", "constitution", "tongue", "pulse", "herb", "formula", "bencao"],
        "mental-wellness": ["anxiety", "depression", "stress", "mood", "sleep"],
        "other": []
    }
    for name, keywords in clusters.items():
        for kw in keywords:
            if kw in q:
                return name
    return "other"


def main():
    SERVICE_ACCOUNT_PATH = PROJECT_ROOT / "serviceAccountKey.json"
    if not SERVICE_ACCOUNT_PATH.exists():
        raise FileNotFoundError(f"serviceAccountKey.json not found at {SERVICE_ACCOUNT_PATH}")
    if not firebase_admin._apps:
        cred = credentials.Certificate(str(SERVICE_ACCOUNT_PATH))
        firebase_admin.initialize_app(cred)
    db = firestore.client()

    # Load KBs
    tcm_const = load_tcm_constitutions()
    tcm_herbs = load_tcm_herbs_formulas()

    docs = list(db.collection("nutribot_logs").stream())
    records = []
    for d in docs:
        obj = d.to_dict()
        if obj.get("test_run"):
            continue
        q = obj.get("question") or obj.get("prompt") or obj.get("text") or ""
        records.append({"id": d.id, "question": q})

    total = len(records)
    unmatched = []
    per_record_matches = []
    for r in records:
        q = r["question"]
        const_matches = find_relevant_constitutions(q, tcm_const, current_lang='en')
        herb_matches = find_relevant_herbs_formulas(q, tcm_herbs, matched_constitutions=const_matches, current_lang='en')
        if not (const_matches or herb_matches):
            unmatched.append(q)
            per_record_matches.append(r)

    if not unmatched:
        print("No unmatched questions found.")
        return

    # Build clusters
    clusters = {"other": []}
    for q in unmatched:
        cl = cluster_question(q)
        if cl == "other":
            clusters.setdefault("other", []).append(q)

    other_list = clusters.get("other", [])
    out_lines = []
    out_lines.append(f"Total unmatched questions: {len(unmatched)}")
    out_lines.append(f"Other cluster count: {len(other_list)}\n")

    out_lines.append("Numbered 'other' cluster entries:")
    for idx, q in enumerate(other_list, start=1):
        out_lines.append(f"{idx}. {q}")

    # Classify noise vs genuine for all unmatched
    noise = []
    genuine = []
    for q in unmatched:
        if is_noise(q):
            noise.append(q)
        else:
            genuine.append(q)

    out_lines.append("\n=== Noise vs Genuine Summary (among all unmatched) ===")
    out_lines.append(f"Unmatched total: {len(unmatched)}")
    out_lines.append(f"Estimated noise/off-topic: {len(noise)}")
    out_lines.append(f"Estimated genuine health/wellness: {len(genuine)}")

    out_lines.append("\nExamples of noise/off-topic:")
    for ex in noise[:10]:
        out_lines.append(f"- {ex}")

    out_lines.append("\nExamples of genuine-looking questions:")
    for ex in genuine[:10]:
        out_lines.append(f"- {ex}")

    # Write UTF-8 safe output to a file
    out_path = PROJECT_ROOT / "other_cluster_output_utf8.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines))
    print(f"Wrote output to: {out_path}")


if __name__ == '__main__':
    main()
