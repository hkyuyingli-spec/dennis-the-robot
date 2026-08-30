"""Read-only analysis: calculate RAG coverage for real user questions stored in Firestore.

Usage: python scripts/analyze_logs_coverage.py

This script initializes Firebase using analyze_firebase.init_firebase(),
loads the current knowledge base via nutribot.rag loaders, fetches all
documents from the `nutribot_logs` collection, and reports match coverage
using find_relevant_constitutions() and find_relevant_herbs_formulas().
It is read-only and will not modify any data.
"""
import sys
import os
from pathlib import Path

# Ensure project root is on sys.path for standalone script execution
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from collections import Counter, defaultdict
import firebase_admin
from firebase_admin import credentials, firestore
from nutribot.rag import (
    load_tcm_constitutions,
    load_tcm_herbs_formulas,
    find_relevant_constitutions,
    find_relevant_herbs_formulas,
)


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
    print("Initializing Firebase (read-only)...")
    SERVICE_ACCOUNT_PATH = PROJECT_ROOT / "serviceAccountKey.json"
    if not SERVICE_ACCOUNT_PATH.exists():
        raise FileNotFoundError(f"serviceAccountKey.json not found at {SERVICE_ACCOUNT_PATH}. Cannot connect to Firestore.")
    # Initialize firebase app if needed
    if not firebase_admin._apps:
        cred = credentials.Certificate(str(SERVICE_ACCOUNT_PATH))
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Loading RAG KB data...")
    tcm_const = load_tcm_constitutions()
    tcm_herbs = load_tcm_herbs_formulas()

    print("Fetching nutribot_logs documents...")
    docs = list(db.collection("nutribot_logs").stream())
    # Filter out test runs if present
    records = []
    for d in docs:
        obj = d.to_dict()
        if obj.get("test_run"):
            continue
        q = obj.get("question") or obj.get("prompt") or obj.get("text") or ""
        records.append({"id": d.id, "question": q})

    total = len(records)
    print(f"Total real questions fetched: {total}")
    if total == 0:
        print("No questions found. Exiting.")
        return

    matched_count = 0
    unmatched = []
    per_record_matches = []

    for r in records:
        q = r["question"]
        # Use English as default language for matching; the KB contains aliases per-language if available
        const_matches = find_relevant_constitutions(q, tcm_const, current_lang='en')
        herb_matches = find_relevant_herbs_formulas(q, tcm_herbs, matched_constitutions=const_matches, current_lang='en')
        has_match = bool(const_matches or herb_matches)
        per_record_matches.append({"id": r["id"], "question": q, "const_matches": [c.get("id") for c in const_matches], "herb_matches": [h.get("id") for h in herb_matches]})
        if has_match:
            matched_count += 1
        else:
            unmatched.append(q)

    matched_pct = matched_count / total * 100.0
    unmatched_pct = 100.0 - matched_pct

    print("\n=== Coverage Summary ===")
    print(f"Total questions: {total}")
    print(f"Questions with ≥1 match: {matched_count} ({matched_pct:.1f}%)")
    print(f"Questions with 0 matches: {len(unmatched)} ({unmatched_pct:.1f}%)")

    print("\n=== Unmatched Questions (full list) ===")
    for q in unmatched:
        print(f"- {q}")

    # Simple clustering of unmatched questions
    cluster_counts = Counter()
    cluster_examples = defaultdict(list)
    for q in unmatched:
        cl = cluster_question(q)
        cluster_counts[cl] += 1
        if len(cluster_examples[cl]) < 5:
            cluster_examples[cl].append(q)

    print("\n=== Unmatched Clusters ===")
    for cl, cnt in cluster_counts.most_common():
        print(f"{cl}: {cnt}")
        for ex in cluster_examples.get(cl, []):
            print(f"  example: {ex}")


if __name__ == '__main__':
    main()
