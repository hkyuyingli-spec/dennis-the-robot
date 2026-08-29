import os
import sys
import json

sys.path.insert(0, os.path.abspath("."))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Import from app
from app import (
    tcm_constitutions_db,
    tcm_herbs_db,
    find_relevant_constitutions,
    find_relevant_herbs_formulas,
    build_rag_context
)

test_prompts = [
    "Tell me about Ginseng and its traditional uses.",
    "What is Sijunzi Tang used for and who should avoid it?",
    "I am pregnant and have cold hands. Can I take Cinnamon tea?",
    "I suffer from severe acne, oily skin, and a bitter mouth taste.",
    "What is the weather forecast for Jakarta tomorrow?"
]

print("=== TESTING DUAL-KNOWLEDGE BASE RAG PIPELINE (CONSTITUTIONS + HERBS/FORMULAS) ===\n")

for prompt in test_prompts:
    matched_c = find_relevant_constitutions(prompt, tcm_constitutions_db, current_lang='en')
    matched_h = find_relevant_herbs_formulas(prompt, tcm_herbs_db, matched_constitutions=matched_c, current_lang='en')
    
    c_names = [f"{m['name_english']} ({m['name_chinese']})" for m in matched_c]
    h_names = [f"{h['name_english']} ({h['name_chinese']})" for h in matched_h]
    
    print(f"User Prompt: '{prompt}'")
    print(f"[RAG Debug Log] Constitutions ({len(matched_c)}): {c_names}")
    print(f"[RAG Debug Log] Herbs & Formulas ({len(matched_h)}): {h_names}")
    
    context = build_rag_context(matched_c, matched_h)
    if context:
        print("--- Generated RAG Context Block Snippet ---")
        print(context[:450] + "...\n")
    else:
        print("--- No RAG Context (Fallback to general guidance) ---\n")
