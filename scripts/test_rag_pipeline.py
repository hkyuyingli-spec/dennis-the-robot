import os
import sys
import json

sys.path.insert(0, os.path.abspath("."))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Load dataset directly
json_path = os.path.join("data", "tcm_constitutions.json")
with open(json_path, "r", encoding="utf-8") as f:
    constitutions_db = json.load(f)

# Import functions from app
from app import find_relevant_constitutions, build_rag_context

test_prompts = [
    "I am always tired, short of breath, and catch colds easily. What constitution am I?",
    "My hands and feet are constantly cold and I love hot drinks.",
    "I suffer from oily skin, bitter mouth taste, and bad acne breakouts.",
    "I bruise easily and my lips look dark purple.",
    "What is the best recipe for baking chocolate cake?"
]

print("=== TESTING RAG RETRIEVAL & GROUNDING CONTEXT GENERATION ===\n")

for prompt in test_prompts:
    matches = find_relevant_constitutions(prompt, constitutions_db, current_lang='en')
    matched_names = [f"{m['name_english']} ({m['name_chinese']})" for m in matches]
    print(f"User Prompt: '{prompt}'")
    print(f"[RAG Debug Log] Matched ({len(matches)}): {matched_names}")
    
    context = build_rag_context(matches)
    if context:
        print("--- Generated Reference Context Snippet ---")
        print(context[:250] + "...\n")
    else:
        print("--- No RAG Context (Fallback to general guidance) ---\n")
