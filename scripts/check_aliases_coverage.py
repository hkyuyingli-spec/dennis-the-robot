import json, os

def report(path, expected_count=None):
    with open(path,'r',encoding='utf-8') as f:
        data = json.load(f)
    entries = data if isinstance(data, list) else data.get('entries', data)
    print(f"\nFile: {path}")
    print(f"Total entries: {len(entries)}")
    missing = []
    empty = []
    for e in entries:
        eid = e.get('id')
        aliases = e.get('aliases') or {}
        id_aliases = aliases.get('id') if isinstance(aliases, dict) else None
        has = bool(id_aliases and isinstance(id_aliases, list) and len(id_aliases)>0)
        status = 'OK' if has else ('EMPTY' if id_aliases is not None else 'MISSING')
        print(f"- {eid}: {status}")
        if status == 'MISSING':
            missing.append(eid)
        if status == 'EMPTY':
            empty.append(eid)
    if missing or empty:
        print('\nIssues:')
        if missing:
            print(' Missing aliases field for IDs:', ', '.join(missing))
        if empty:
            print(' Empty aliases.id for IDs:', ', '.join(empty))
    else:
        print('\nAll entries have non-empty aliases.id arrays.')

if __name__ == '__main__':
    cwd = os.path.abspath(os.path.dirname(__file__) + os.sep + '..')
    cpath = os.path.join(cwd, 'data', 'tcm_constitutions.json')
    hpath = os.path.join(cwd, 'data', 'tcm_herbs_formulas.json')
    report(cpath)
    report(hpath)
