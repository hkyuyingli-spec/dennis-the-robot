import sys
import json
import re

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

file_path = "data/tcm_herbs_formulas.json"

with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

print("=== VERIFYING TCM HERBS & FORMULAS KNOWLEDGE BASE ===")
print(f"File: {file_path}\n")

# 1. Metadata check
print("1. Top-Level Metadata Check:")
print(f"   - last_updated: {data.get('last_updated')}")
print(f"   - last_human_reviewed: {data.get('last_human_reviewed')}")
print(f"   - review_status: {data.get('review_status')}\n")

entries = data.get("entries", [])
print(f"2. Total Entries Count: {len(entries)}")

# 2. Field and Safety Check
required_fields = [
    "id", "name_english", "name_chinese", "pinyin", "category",
    "traditional_uses", "typical_preparation", "cautions_and_contraindications",
    "related_constitutions", "source_note"
]

safety_dosage_patterns = [
    r'\b\d+\s*g\b', r'\b\d+\s*grams\b', r'\b\d+\s*mg\b', r'\b\d+\s*tsp\b',
    r'\btwice daily\b', r'\b\d+\s*times a day\b', r'\bdaily dose\b'
]

errors = []
safety_violations = []

for idx, entry in enumerate(entries, 1):
    entry_id = entry.get("id", f"Entry #{idx}")
    # Check required fields
    for field in required_fields:
        if field not in entry or entry[field] is None:
            errors.append(f"Missing field '{field}' in {entry_id}")

    # Check safety rules against prescription / dosage wording
    prep_text = entry.get("typical_preparation", "")
    all_text = json.dumps(entry)
    for pattern in safety_dosage_patterns:
        if re.search(pattern, all_text, re.IGNORECASE):
            safety_violations.append(f"Dosage pattern '{pattern}' found in {entry_id}")

if errors:
    print(f"❌ Found {len(errors)} field errors:")
    for err in errors:
        print(f"   - {err}")
else:
    print("✅ All required fields present across all entries.")

if safety_violations:
    print(f"❌ Safety check failed with {len(safety_violations)} violations:")
    for v in safety_violations:
        print(f"   - {v}")
else:
    print("✅ Safety check passed: 0 specific dosages or prescription wording found.")

print("\nSample Entry Preview:")
print(json.dumps(entries[0], indent=2))
