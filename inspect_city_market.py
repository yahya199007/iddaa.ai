import json

with open('data/matches.json', encoding='utf-8') as f:
    matches = json.load(f)

for m in matches:
    if str(m.get('bulten_code')) == '3243691':
        print("Found Man City match!")
        print("all_markets len:", len(m.get('all_markets', [])))
        print("Sample market:", m.get('all_markets', [])[0])
        print("Sample market 10:", m.get('all_markets', [])[10])
        break
