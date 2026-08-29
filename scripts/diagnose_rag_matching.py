import os
import sys
import json

sys.path.insert(0, os.path.abspath("."))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Load dataset
json_path = os.path.join("data", "tcm_constitutions.json")
with open(json_path, "r", encoding="utf-8") as f:
    constitutions_db = json.load(f)

prompt = "I bruise easily and my lips look dark purple."
prompt_lower = prompt.lower()

print("=== DIAGNOSING MATCHING LOGIC FOR QUERY ===")
print(f"Query: '{prompt}'\n")

for item in constitutions_db:
    cid = item['id']
    name = f"{item['name_english']} ({item['name_chinese']})"
    matches = []
    total_score = 0
    
    # 1. Names & pinyin
    names = [item.get("name_english", "").lower(), item.get("name_chinese", "").lower(), item.get("pinyin", "").lower(), item.get("id", "").lower()]
    for n in names:
        if n and n in prompt_lower:
            total_score += 5
            matches.append((5, f"Name match: '{n}'"))
            
    # 2. Key characteristics
    for trait in item.get("key_characteristics", []):
        words = [w for w in trait.lower().split() if len(w) > 3]
        for w in words:
            if w in prompt_lower:
                total_score += 1
                matches.append((1, f"Trait word match '{w}' in trait: '{trait}'"))

    # 3. Susceptibility conditions
    for cond in item.get("susceptibility_conditions", []):
        words = [w for w in cond.lower().split() if len(w) > 3]
        for w in words:
            if w in prompt_lower:
                total_score += 1
                matches.append((1, f"Susceptibility word match '{w}' in cond: '{cond}'"))

    # 4. Keyword boosts
    keyword_boosts = {
        "pinghe": ["balanced", "healthy", "normal", "pinghe", "平和"],
        "qixu": ["fatigue", "tired", "shortness of breath", "sweating", "weak", "qi deficiency", "qixu", "气虚"],
        "yangxu": ["cold", "cold hands", "cold feet", "chilly", "warmth", "yang deficiency", "yangxu", "阳虚"],
        "yinxu": ["dry", "dry skin", "dry eyes", "night sweat", "five center", "heat", "yin deficiency", "yinxu", "阴虚"],
        "tan-shi": ["weight", "obesity", "fatty", "oily skin", "phlegm", "dampness", "tan-shi", "痰湿"],
        "shi-re": ["acne", "breakouts", "oily", "bitter", "damp-heat", "damp heat", "shi-re", "湿热"],
        "xue-yu": ["bruise", "dark spots", "purple", "pain", "stasis", "blood stasis", "xue-yu", "血瘀"],
        "qi-yu": ["mood", "anxiety", "depression", "sighing", "stress", "stagnation", "qi-yu", "气郁"],
        "te-bing": ["allergy", "allergic", "hives", "sneezing", "asthma", "te-bing", "特禀"]
    }
    if cid in keyword_boosts:
        for kw in keyword_boosts[cid]:
            if kw in prompt_lower:
                total_score += 3
                matches.append((3, f"Keyword boost match: '{kw}'"))
                
    if total_score > 0:
        print(f"Constitution: {name} (ID: {cid}) | Total Score: {total_score}")
        for score_val, reason in matches:
            print(f"   - [{score_val} pts] {reason}")
        print()
