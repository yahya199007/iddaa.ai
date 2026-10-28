import json
import math

with open('data/matches.json', encoding='utf-8') as f:
    matches = json.load(f)

def poisson_prob(lmb, k):
    return (math.exp(-lmb) * (lmb ** k)) / math.factorial(k)

def calc_half_goals(xg_h, xg_a):
    # Roughly 45% of xG occurs in 1st half, 55% in 2nd half
    h_h1 = xg_h * 0.44
    a_h1 = xg_a * 0.44
    h_h2 = xg_h * 0.56
    a_h2 = xg_a * 0.56
    
    # Prob of 0 goals in 1st half
    p_0_h1 = math.exp(-(h_h1 + a_h1))
    p_atleast1_h1 = 1.0 - p_0_h1
    
    # Prob of 0 goals in 2nd half
    p_0_h2 = math.exp(-(h_h2 + a_h2))
    p_atleast1_h2 = 1.0 - p_0_h2
    
    # Both halves have at least 1 goal (Her İki Yarıda Gol Olur: Evet)
    p_both_halves_goal = p_atleast1_h1 * p_atleast1_h2
    
    # Home scores in both halves
    p_home_h1 = 1.0 - math.exp(-h_h1)
    p_home_h2 = 1.0 - math.exp(-h_h2)
    p_home_both_halves = p_home_h1 * p_home_h2
    
    # Away scores in both halves
    p_away_h1 = 1.0 - math.exp(-a_h1)
    p_away_h2 = 1.0 - math.exp(-a_h2)
    p_away_both_halves = p_away_h1 * p_away_h2
    
    # HT/FT: 1/1 prob (Home leads at HT and wins FT)
    # Simulation across scores 0-4
    p_ht1_ft1 = 0.0
    p_ht2_ft2 = 0.0
    for h1 in range(5):
        for a1 in range(5):
            prob_h1 = poisson_prob(h_h1, h1) * poisson_prob(a_h1, a1)
            for h2 in range(5):
                for a2 in range(5):
                    prob_h2 = poisson_prob(h_h2, h2) * poisson_prob(a_h2, a2)
                    total_prob = prob_h1 * prob_h2
                    # 1/1 condition: h1 > a1 AND (h1 + h2) > (a1 + a2)
                    if h1 > a1 and (h1 + h2) > (a1 + a2):
                        p_ht1_ft1 += total_prob
                    # 2/2 condition: a1 > h1 AND (a1 + a2) > (h1 + h2)
                    if a1 > h1 and (a1 + a2) > (h1 + h2):
                        p_ht2_ft2 += total_prob

    return {
        'both_halves_goal': p_both_halves_goal * 100,
        'home_both_halves': p_home_both_halves * 100,
        'away_both_halves': p_away_both_halves * 100,
        'ht1_ft1': p_ht1_ft1 * 100,
        'ht2_ft2': p_ht2_ft2 * 100,
        'ht_atleast1': p_atleast1_h1 * 100
    }

results = []

for m in matches:
    code = m.get('bulten_code')
    home = m.get('home_team')
    away = m.get('away_team')
    leg = m.get('league')
    time = m.get('match_time')
    odds = m.get('odds', {})
    
    # Extract xG
    h_stat = m.get('home_stats', {})
    a_stat = m.get('away_stats', {})
    xg_h = h_stat.get('goals_scored_avg', 1.4) * h_stat.get('home_advantage', 1.1)
    xg_a = a_stat.get('goals_scored_avg', 1.1)
    
    # If expected_total_xg is present
    tot_xg = m.get('expected_total_xg')
    if tot_xg:
        ratio = tot_xg / (xg_h + xg_a) if (xg_h + xg_a) > 0 else 1.0
        xg_h *= ratio
        xg_a *= ratio
        
    sim = calc_half_goals(xg_h, xg_a)
    
    # Check all_markets for actual odds
    all_mkts = m.get('all_markets', [])
    mkt_odds = {}
    for mkt in all_mkts:
        mtid = mkt.get('mtid')
        title = mkt.get('title')
        for o in mkt.get('outcomes', []):
            label = o.get('label')
            odd = o.get('odd')
            if mtid == 5: # İY/MS
                mkt_odds[f"iy_ms_{label}"] = odd
            elif mtid == 295: # Ev Sahibi Her İki Yarıda Gol Atar mı
                mkt_odds[f"ev_iki_yari_gol_{label}"] = odd
            elif mtid == 801: # Her İki Yarıda Karşılıklı Gol
                mkt_odds[f"iki_yari_kg_{label}"] = odd
            elif mtid == 593: # KG & 2.5 Üst
                mkt_odds[f"kg_25_{label}"] = odd
            elif mtid == 209: # 1. Yarı 0.5 Gol Üst
                mkt_odds[f"iy_05_{label}"] = odd

    results.append({
        'code': code,
        'match': f"{home} vs {away}",
        'league': leg,
        'time': time,
        'xg_h': round(xg_h, 2),
        'xg_a': round(xg_a, 2),
        'tot_xg': round(xg_h + xg_a, 2),
        'sim': sim,
        'odds': odds,
        'mkt_odds': mkt_odds
    })

print(f"Calculated simulations for {len(results)} matches.")

# 1. Top Her İki Yarıda Gol Olur (Evet - Evet)
print("\n=== TOP HER İKİ YARIDA GOL OLUR (EVET) >= 70% GÜVEN ===")
both_halves = sorted([r for r in results if r['sim']['both_halves_goal'] >= 70], key=lambda x: x['sim']['both_halves_goal'], reverse=True)
for r in both_halves[:10]:
    odd = r['odds'].get('over25', 1.55) # correlated proxy if exact mkt not priced
    print(f"[{r['time']}] #{r['code']} {r['match']} ({r['league']}) | xG: {r['tot_xg']} | Olasılık: %{r['sim']['both_halves_goal']:.1f}")

# 2. Top İY 1 / MS 1 & İY 2 / MS 2 >= 65-75% GÜVEN
print("\n=== TOP İY 1 / MS 1 ve İY 2 / MS 2 GÜVENİ ===")
ht_ft = sorted([r for r in results if max(r['sim']['ht1_ft1'], r['sim']['ht2_ft2']) >= 50], 
               key=lambda x: max(x['sim']['ht1_ft1'], x['sim']['ht2_ft2']), reverse=True)
for r in ht_ft[:10]:
    is_home = r['sim']['ht1_ft1'] > r['sim']['ht2_ft2']
    pick = "İY 1 / MS 1" if is_home else "İY 2 / MS 2"
    prob = r['sim']['ht1_ft1'] if is_home else r['sim']['ht2_ft2']
    odd_direct = r['mkt_odds'].get('iy_ms_1/1' if is_home else 'iy_ms_2/2', 'N/A')
    print(f"[{r['time']}] #{r['code']} {r['match']} ({r['league']}) | Tercih: {pick} | Güven: %{prob:.1f} | Oran: {odd_direct}")

# 3. Top Ev Sahibi / Deplasman Her İki Yarıda da Gol Atar (Evet)
print("\n=== TOP HER İKİ YARIDA DA GOL ATAR (EVET) ===")
team_halves = sorted([r for r in results if max(r['sim']['home_both_halves'], r['sim']['away_both_halves']) >= 50],
                     key=lambda x: max(x['sim']['home_both_halves'], x['sim']['away_both_halves']), reverse=True)
for r in team_halves[:10]:
    is_home = r['sim']['home_both_halves'] > r['sim']['away_both_halves']
    prob = r['sim']['home_both_halves'] if is_home else r['sim']['away_both_halves']
    team = r['match'].split(' vs ')[0] if is_home else r['match'].split(' vs ')[1]
    print(f"[{r['time']}] #{r['code']} {r['match']} | Takım: {team} Her İki Yarıda Gol Atar | Güven: %{prob:.1f}")
