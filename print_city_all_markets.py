import json

with open('data/matches.json', encoding='utf-8') as f:
    matches = json.load(f)

for m in matches:
    if str(m.get('bulten_code')) == '3243691':
        for idx, mkt in enumerate(m.get('all_markets', [])):
            outcomes_str = ", ".join([f"{o.get('label')}: {o.get('odd')}" for o in mkt.get('outcomes', [])[:4]])
            print(f"{idx+1}. [{mkt.get('category')}] {mkt.get('title')} (mtid: {mkt.get('mtid')}): {outcomes_str}")
        break
