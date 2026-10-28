import json

with open('data/matches.json', encoding='utf-8') as f:
    matches = json.load(f)

print(f"Total matches to scan: {len(matches)}")

found_special_markets = []

for m in matches:
    mid = m.get('id')
    code = m.get('bulten_code')
    home = m.get('home_team')
    away = m.get('away_team')
    leg = m.get('league')
    time = m.get('match_time')
    xg = m.get('expected_total_xg', 0)
    
    # Check all markets in market_categories
    cats = m.get('market_categories', {})
    
    match_picks = []
    
    # Search each category
    for cat_name, market_list in cats.items():
        for mkt in market_list:
            title = mkt.get('title', '')
            options = mkt.get('options', [])
            
            # Check for:
            # 1. Her İki Yarıda Karşılıklı Gol (Evet/Evet)
            if 'Her İki Yarıda Karşılıklı Gol' in title or 'İki Yarıda' in title:
                for opt in options:
                    match_picks.append(('Her İki Yarı', title, opt.get('name'), opt.get('odd')))
            
            # 2. İY/MS
            if 'İlk Yarı / Maç Sonucu' in title or 'İY/MS' in title:
                for opt in options:
                    name = opt.get('name')
                    odd = opt.get('odd')
                    if name in ['1/1', '2/2', '1/2', '2/1', 'X/1', 'X/2']:
                        match_picks.append(('İY/MS', title, name, odd))
                        
            # 3. Ev Sahibi Her İki Yarıda Gol Atar mı / Ev Sahibi İki Yarıyı da Kazanır mı
            if 'İki Yarı' in title and ('Kazanır' in title or 'Gol Atar' in title):
                for opt in options:
                    if 'Evet' in opt.get('name', ''):
                        match_picks.append(('İki Yarı Kazanır/Gol', title, opt.get('name'), opt.get('odd')))
                        
            # 4. Karşılıklı Gol Var & 2.5 Üst
            if 'Karşılıklı Gol Var & 2.5 Üst' in title or ('KG' in title and '2.5' in title):
                for opt in options:
                    if 'Evet' in opt.get('name', '') or 'Var' in opt.get('name', ''):
                        match_picks.append(('KG&2.5', title, opt.get('name'), opt.get('odd')))

    if match_picks:
        found_special_markets.append({
            'code': code,
            'match': f"{home} vs {away}",
            'league': leg,
            'time': time,
            'xg': xg,
            'picks': match_picks
        })

print(f"Matches with special markets: {len(found_special_markets)}")
for item in found_special_markets[:10]:
    print(f"\n[{item['time']}] #{item['code']} {item['match']} ({item['league']}) - xG: {item['xg']}")
    for p in item['picks'][:8]:
        print(f"   -> [{p[0]}] {p[1]} | {p[2]} = {p[3]}")
