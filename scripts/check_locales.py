import json
from pathlib import Path
p = Path('locales')

en = json.loads(p.joinpath('en.json').read_text(encoding='utf-8'))
idn = json.loads(p.joinpath('id.json').read_text(encoding='utf-8'))
zh = json.loads(p.joinpath('zh.json').read_text(encoding='utf-8'))

en_keys = set(en.keys())
id_keys = set(idn.keys())
zh_keys = set(zh.keys())

missing_in_id = sorted(list(en_keys - id_keys))
missing_in_zh = sorted(list(en_keys - zh_keys))

print('Missing in id.json:')
for k in missing_in_id:
    print('-', k)

print('\nMissing in zh.json:')
for k in missing_in_zh:
    print('-', k)
