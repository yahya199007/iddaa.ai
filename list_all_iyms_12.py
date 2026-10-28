import json

with open('data/matches.json', encoding='utf-8') as f:
    matches = json.load(f)

iyms_all = []

for m in matches:
    code = m.get('bulten_code')
    home = m.get('home_team')
    away = m.get('away_team')
    leg = m.get('league')
    time = m.get('match_time')
    xg = m.get('expected_total_xg', 0)
    
    odds_12 = None
    odds_21 = None
    odds_1x = None
    odds_2x = None
    odds_11 = None
    odds_22 = None
    evet_kg = None
    ev_2_yari = None
    
    for mkt in m.get('all_markets', []):
        mtid = mkt.get('mtid')
        outcomes = mkt.get('outcomes', [])
        if mtid == 5:
            for o in outcomes:
                l = o.get('label')
                odd = o.get('odd')
                if l == '1/2': odds_12 = odd
                elif l == '2/1': odds_21 = odd
                elif l == '1/X': odds_1x = odd
                elif l == '2/X': odds_2x = odd
                elif l == '1/1': odds_11 = odd
                elif l == '2/2': odds_22 = odd
        elif mtid == 801 and len(outcomes) >= 4:
            evet_kg = outcomes[3].get('odd')
        elif mtid == 295 and len(outcomes) >= 1:
            ev_2_yari = outcomes[0].get('odd')

    if odds_12 or odds_21:
        iyms_all.append({
            'code': code, 'match': f"{home} vs {away}", 'league': leg, 'time': time, 'xg': xg,
            'odd_12': odds_12, 'odd_21': odds_21, 'odd_1x': odds_1x, 'odd_2x': odds_2x,
            'odd_11': odds_11, 'odd_22': odds_22, 'evet_kg': evet_kg, 'ev_2_yari': ev_2_yari
        })

print(f"Total matches with 1/2 and 2/1: {len(iyms_all)}")
for item in iyms_all:
    print(f"[{item['time']}] #{item['code']} {item['match']} ({item['league']})")
    print(f"   -> 1/2: {item['odd_12']} | 2/1: {item['odd_21']} | 1/X: {item['odd_1x']} | 2/X: {item['odd_2x']} | Evet/Evet KG: {item['evet_kg']}")
