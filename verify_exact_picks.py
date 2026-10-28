import json

with open('data/matches.json', encoding='utf-8') as f:
    matches = json.load(f)

check_codes = [
    '3243691', '3246154', '3243611', '3261956', '3243716', 
    '3246337', '3246061', '3264601', '3243713', '3243596', 
    '3246308', '3245972'
]

for m in matches:
    code = str(m.get('bulten_code'))
    if code in check_codes:
        odds = m.get('odds', {})
        print(f"Code: {code} | {m.get('match_time')} | {m.get('home_team')} vs {m.get('away_team')} | League: {m.get('league')}")
        print(f"   Odds: ms1={odds.get('ms1')}, msX={odds.get('msX')}, ms2={odds.get('ms2')}, cs10={odds.get('cs10')}, cs02={odds.get('cs02')}, o15={odds.get('over15')}")
