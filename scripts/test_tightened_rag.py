import os
import sys
import json

sys.path.insert(0, os.path.abspath("."))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

json_path = os.path.join("data", "tcm_constitutions.json")
with open(json_path, "r", encoding="utf-8") as f:
    constitutions_db = json.load(f)

STOP_WORDS = {
    "easily", "look", "looks", "feeling", "feel", "feels", "with", "from", "have", "has",
    "make", "body", "type", "tendency", "prone", "often", "very", "also", "some", "like",
    "soft", "good", "main", "well", "more", "less", "much", "many", "over", "under", "into"
}

def find_relevant_constitutions_tightened(prompt, constitutions_data, max_matches=2):
    if not prompt or not constitutions_data:
        return []
    
    prompt_lower = prompt.lower()
    scored_results = []
    
    for item in constitutions_data:
        score = 0
        cid = item.get("id", "")
        
        # 1. Direct Name / Pinyin Match (+6 points)
        names = [
            item.get("name_english", "").lower(),
            item.get("name_chinese", "").lower(),
            item.get("pinyin", "").lower(),
            cid.lower()
        ]
        for n in names:
            if n and n in prompt_lower:
                score += 6
        
        # 2. Diagnostic Keyword / Symptom Phrase Match (+4 points each)
        diagnostic_keywords = {
            "pinghe": ["pinghe", "平和", "balanced constitution", "harmonious constitution", "healthy constitution"],
            "qixu": [
                "qixu", "气虚", "qi deficiency", "qi-deficiency", "short of breath", "shortness of breath", 
                "spontaneous sweating", "catch cold", "catching cold", "fatigue", "tired", "weak voice"
            ],
            "yangxu": [
                "yangxu", "阳虚", "yang deficiency", "yang-deficiency", "cold hands", "cold feet", "cold limbs", 
                "intolerance to cold", "cold intolerance", "warm drinks", "chilly"
            ],
            "yinxu": [
                "yinxu", "阴虚", "yin deficiency", "yin-deficiency", "five-center heat", "five center heat", 
                "night sweat", "night sweating", "sweat at night", "sweating at night", "sweat a lot at night",
                "dry mouth", "mouth feels dry", "dry throat", "throat feels dry", "chapped lips", "dry eyes"
            ],
            "tan-shi": [
                "tan-shi", "tanshi", "痰湿", "phlegm-dampness", "phlegm dampness", "abdominal obesity", 
                "greasy tongue", "heavy body", "heavy feeling", "sticky taste", "bloated", "bloating"
            ],
            "shi-re": [
                "shi-re", "shire", "湿热", "damp-heat", "damp heat", "acne", "breakout", "breakouts", 
                "bitter taste", "bitter mouth", "sticky stool", "yellow tongue"
            ],
            "xue-yu": [
                "xue-yu", "xueyu", "血瘀", "blood-stasis", "blood stasis", "bruise", "bruising", 
                "dark purple", "purple lips", "stasis spots", "hyperpigmentation"
            ],
            "qi-yu": [
                "qi-yu", "qiyu", "气郁", "qi-stagnation", "qi stagnation", "frequent sighing", 
                "sighing", "chest distension", "globus hystericus", "plum-pit", "moody", "anxious", "anxiety", "melancholy", "mood swings"
            ],
            "te-bing": [
                "te-bing", "tebing", "特禀", "allergic constitution", "special constitution", 
                "allergy", "allergies", "seasonal allergies", "allergic rhinitis", "hives", "rash", "rashes", "skin rash", "skin rashes", "asthma"
            ]
        }
        
        if cid in diagnostic_keywords:
            for kw in diagnostic_keywords[cid]:
                if kw in prompt_lower:
                    score += 4

        # 3. Exact Multi-word Phrase Matches from Characteristics & Susceptibilities (+5 points)
        all_phrases = item.get("key_characteristics", []) + item.get("susceptibility_conditions", [])
        for phrase in all_phrases:
            phrase_clean = phrase.lower()
            if len(phrase_clean) > 8 and phrase_clean in prompt_lower:
                score += 5

        # 4. Filtered Single-Word Overlap (+1 point, excluding STOP_WORDS)
        for trait in item.get("key_characteristics", []):
            words = [w.strip(",.()") for w in trait.lower().split()]
            for w in words:
                if len(w) >= 4 and w not in STOP_WORDS and w in prompt_lower:
                    score += 1

        # Strict Relevance Threshold: require at least score >= 4 (strong signal)
        if score >= 4:
            scored_results.append((score, item))

    scored_results.sort(key=lambda x: x[0], reverse=True)
    return [item for score, item in scored_results[:max_matches]]

original_queries = [
    "I am always tired, short of breath, and catch colds easily. What constitution am I?",
    "My hands and feet are constantly cold and I love hot drinks.",
    "I suffer from oily skin, bitter mouth taste, and bad acne breakouts.",
    "I bruise easily and my lips look dark purple.",
    "What is the best recipe for baking chocolate cake?"
]

new_edge_case_queries = [
    "I have trouble sleeping and feel anxious/moody lately",
    "I sweat a lot at night and my mouth feels dry",
    "What should I eat for breakfast?",
    "I have seasonal allergies and skin rashes",
    "I feel bloated and heavy after eating"
]

print("=== ORIGINAL 5 TEST CASES (REFINED TIGHTENED RAG MATCHING) ===")
for q in original_queries:
    matches = find_relevant_constitutions_tightened(q, constitutions_db)
    names = [f"{m['name_english']} ({m['name_chinese']})" for m in matches]
    print(f"Query: '{q}'")
    print(f"Matched ({len(matches)}): {names}\n")

print("==================================================")
print("=== 5 NEW EDGE-CASE QUERIES (REFINED TIGHTENED RAG MATCHING) ===")
for q in new_edge_case_queries:
    matches = find_relevant_constitutions_tightened(q, constitutions_db)
    names = [f"{m['name_english']} ({m['name_chinese']})" for m in matches]
    print(f"Query: '{q}'")
    print(f"Matched ({len(matches)}): {names}\n")
