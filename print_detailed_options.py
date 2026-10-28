import json

with open('data/matches.json', encoding='utf-8') as f:
    matches = json.load(f)

detailed_picks = []

for m in matches:
    code = m.get('bulten_code')
    home = m.get('home_team')
    away = m.get('away_team')
    leg = m.get('league')
    time = m.get('match_time')
    date = m.get('date')
    xg = m.get('expected_total_xg', 0)
    all_mkts = m.get('all_markets', [])
    
    match_data = {
        'code': code, 'match': f"{home} vs {away}", 'league': leg, 'time': time, 'xg': xg,
        'iyms_12': None, 'iyms_21': None, 'iyms_1X': None, 'iyms_2X': None, 'iyms_11': None, 'iyms_22': None,
        'evet_evet_kg': None, 'ev_iki_yari_gol': None, 'kg_25_ust': None
    }
    
    for mkt in all_mkts:
        mtid = mkt.get('mtid')
        outcomes = mkt.get('outcomes', [])
        
        # MTID 5: İY/MS
        if mtid == 5:
            for o in outcomes:
                lbl = o.get('label')
                odd = o.get('odd')
                if lbl == '1/2': match_data['iyms_12'] = odd
                elif lbl == '2/1': match_data['iyms_21'] = odd
                elif lbl == '1/X': match_data['iyms_1X'] = odd
                elif lbl == '2/X': match_data['iyms_2X'] = odd
                elif lbl == '1/1': match_data['iyms_11'] = odd
                elif lbl == '2/2': match_data['iyms_22'] = odd
                
        # MTID 801: Her İki Yarıda Karşılıklı Gol (Evet/Evet is option 4)
        if mtid == 801:
            if len(outcomes) >= 4:
                match_data['evet_evet_kg'] = outcomes[3].get('odd')
                
        # MTID 295: Ev Sahibi Her İki Yarıda Gol Atar mı (Seçenek 1 = Evet)
        if mtid == 295:
            if len(outcomes) >= 1:
                match_data['ev_iki_yari_gol'] = outcomes[0].get('odd')
                
        # MTID 593: KG Var & 2.5 Üst (Seçenek 1 = Evet)
        if mtid == 593:
            if len(outcomes) >= 1:
                match_data['kg_25_ust'] = outcomes[0].get('odd')

    if match_data['iyms_12'] or match_data['evet_evet_kg']:
        detailed_picks.append(match_data)

print(f"Total matches with detailed markets: {len(detailed_picks)}")

# Let's sort and print top 10 for 1/2, 2/1 and Evet/Evet
print("\n=== TOP 1/2 VE 2/1 GERİ DÖNÜŞ MAÇLARI ===")
for p in detailed_picks[:12]:
    print(f"[{p['time']}] #{p['code']} {p['match']} ({p['league']})")
    print(f"   -> 1/2: {p['iyms_12']} | 2/1: {p['iyms_21']} | 1/X: {p['iyms_1X']} | 2/X: {p['iyms_2X']}")
    print(f"   -> Her İki Yarıda KG (Evet/Evet): {p['evet_evet_kg']} | Ev İki Yarı Gol: {p['ev_iki_yari_gol']} | KG&2.5 Üst: {p['kg_25_ust']}")
