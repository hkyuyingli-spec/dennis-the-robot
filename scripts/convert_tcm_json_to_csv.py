import sys
import json
import pandas as pd

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

json_path = 'data/tcm_constitutions.json'
csv_path = 'data/tcm_constitutions.csv'

with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

flattened = []
for item in data:
    flattened.append({
        'id': item['id'],
        'name_english': item['name_english'],
        'name_chinese': item['name_chinese'],
        'pinyin': item['pinyin'],
        'key_characteristics': ' | '.join(item['key_characteristics']),
        'susceptibility_conditions': ' | '.join(item['susceptibility_conditions']),
        'dietary_beneficial': ' | '.join(item['dietary_recommendations']['beneficial']),
        'dietary_avoid': ' | '.join(item['dietary_recommendations']['avoid']),
        'lifestyle_rituals': ' | '.join(item['lifestyle_rituals']),
        'herbal_teas_formulas': ' | '.join(item['herbal_teas_formulas'])
    })

df = pd.DataFrame(flattened)
df.to_csv(csv_path, index=False, encoding='utf-8-sig')
print(f"Successfully generated {csv_path} with {len(df)} rows.")
