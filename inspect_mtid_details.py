import json

with open('data/matches.json', encoding='utf-8') as f:
    matches = json.load(f)

print("--- Inspecting mtid 801 in Man City ---")
for m in matches:
    if str(m.get('bulten_code')) == '3243691':
        for mkt in m.get('all_markets', []):
            if mkt.get('mtid') in [801, 295, 296, 5, 593]:
                print(f"MTID {mkt.get('mtid')} - {mkt.get('title')}:")
                for o in mkt.get('outcomes', []):
                    print(f"   {o.get('n')}. label: '{o.get('label')}' | odd: {o.get('odd')}")
        break
