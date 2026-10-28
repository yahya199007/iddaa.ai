import json

with open('data/matches.json', encoding='utf-8') as f:
    matches = json.load(f)

print(f"Total matches: {len(matches)}")

evet_evet_matches = []
iyms_turnaround_matches = []

for m in matches:
    code = m.get('bulten_code')
    home = m.get('home_team')
    away = m.get('away_team')
    leg = m.get('league')
    time = m.get('match_time')
    date = m.get('date')
    all_mkts = m.get('all_markets', [])
    xg = m.get('expected_total_xg', 0)
    
    # 1. Look for Evet / Evet in all markets
    for mkt in all_mkts:
        mtid = mkt.get('mtid')
        title = mkt.get('title')
        cat = mkt.get('category')
        for o in mkt.get('outcomes', []):
            label = o.get('label', '')
            odd = o.get('odd')
            # Check mtid 801: Her İki Yarıda Karşılıklı Gol (Evet/Evet)
            if mtid == 801:
                evet_evet_matches.append({
                    'code': code, 'match': f"{home} vs {away}", 'league': leg, 'time': time,
                    'type': 'Her İki Yarıda Karşılıklı Gol', 'option': label, 'odd': odd, 'xg': xg
                })
            # Check mtid 295: Ev Sahibi Her İki Yarıda Gol Atar mı (Evet)
            elif mtid == 295 and 'Evet' in label:
                evet_evet_matches.append({
                    'code': code, 'match': f"{home} vs {away}", 'league': leg, 'time': time,
                    'type': 'Ev Sahibi Her İki Yarıda Gol Atar (Evet)', 'option': label, 'odd': odd, 'xg': xg
                })
            # Check mtid 593: Karşılıklı Gol Var & 2.5 Üst (Evet)
            elif mtid == 593 and ('Evet' in label or 'Var' in label):
                evet_evet_matches.append({
                    'code': code, 'match': f"{home} vs {away}", 'league': leg, 'time': time,
                    'type': 'KG Var & 2.5 Üst (Evet)', 'option': label, 'odd': odd, 'xg': xg
                })
            # Check mtid 5: İY/MS for 1/2 or 2/1
            elif mtid == 5:
                if label in ['1/2', '2/1']:
                    iyms_turnaround_matches.append({
                        'code': code, 'match': f"{home} vs {away}", 'league': leg, 'time': time,
                        'type': f'İY/MS {label}', 'option': label, 'odd': odd, 'xg': xg
                    })

print(f"Found {len(evet_evet_matches)} Evet/Evet options.")
print(f"Found {len(iyms_turnaround_matches)} 1/2 and 2/1 options.")

print("\n--- SAMPLE EVET / EVET PICKS ---")
for e in evet_evet_matches[:15]:
    print(f"[{e['time']}] #{e['code']} {e['match']} ({e['league']}) -> {e['type']}: {e['option']} | Oran: {e['odd']}")

print("\n--- SAMPLE 1/2 ve 2/1 PICKS ---")
for t in iyms_turnaround_matches[:15]:
    print(f"[{t['time']}] #{t['code']} {t['match']} ({t['league']}) -> {t['type']} | Oran: {t['odd']}")
