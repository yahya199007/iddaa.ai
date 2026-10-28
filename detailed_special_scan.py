import json
import math

with open('data/matches.json', encoding='utf-8') as f:
    matches = json.load(f)

def poisson_prob(lmb, k):
    return (math.exp(-lmb) * (lmb ** k)) / math.factorial(k)

# Scan for:
# Category 1: "Evet / Evet" (Her İki Yarıda Gol Olur: Evet) -> Highest xG matches
# Category 2: "1. Yarı 0.5 Üst (İlk Yarıda Gol Olur: Evet)" -> %75-%84 Güven, Oran ~1.30-1.45
# Category 3: "İY 1 / MS 1 ve İY 2 / MS 2" (Favori İlk Yarıdan Bitirir) -> %68-%75 Güven, Oran ~1.45-1.70
# Category 4: "1/2 ve 2/1 Geri Dönüş (Comeback) Taraması" -> En yüksek geri dönüş profili ve 25.00 - 35.00 oran potansiyeli
# Category 5: "KG Var & 2.5 Üst" -> Yüksek xG karşılıklı gol maçları

scanned = []

for m in matches:
    code = m.get('bulten_code')
    home = m.get('home_team')
    away = m.get('away_team')
    leg = m.get('league')
    time = m.get('match_time')
    odds = m.get('odds', {})
    
    h_stat = m.get('home_stats', {})
    a_stat = m.get('away_stats', {})
    xg_h = h_stat.get('goals_scored_avg', 1.4) * h_stat.get('home_advantage', 1.1)
    xg_a = a_stat.get('goals_scored_avg', 1.1)
    
    tot_xg = m.get('expected_total_xg')
    if tot_xg:
        ratio = tot_xg / (xg_h + xg_a) if (xg_h + xg_a) > 0 else 1.0
        xg_h *= ratio
        xg_a *= ratio
    else:
        tot_xg = xg_h + xg_a

    # Half goals
    h_h1 = xg_h * 0.44
    a_h1 = xg_a * 0.44
    h_h2 = xg_h * 0.56
    a_h2 = xg_a * 0.56
    
    # Prob of >=1 in 1st half
    p_1h_over05 = (1.0 - math.exp(-(h_h1 + a_h1))) * 100
    # Prob of >=1 in 2nd half
    p_2h_over05 = (1.0 - math.exp(-(h_h2 + a_h2))) * 100
    # Prob of both halves have >=1 goal (Evet / Evet)
    p_both_halves = (p_1h_over05 / 100.0) * (p_2h_over05 / 100.0) * 100
    
    # Simulation for 1/1, 2/2, 1/2, 2/1
    p_ht1_ft1 = 0.0
    p_ht2_ft2 = 0.0
    p_1_2 = 0.0 # HT 1, FT 2
    p_2_1 = 0.0 # HT 2, FT 1
    
    for h1 in range(5):
        for a1 in range(5):
            prob_h1 = poisson_prob(h_h1, h1) * poisson_prob(a_h1, a1)
            for h2 in range(5):
                for a2 in range(5):
                    prob_h2 = poisson_prob(h_h2, h2) * poisson_prob(a_h2, a2)
                    tp = prob_h1 * prob_h2
                    # 1/1
                    if h1 > a1 and (h1 + h2) > (a1 + a2):
                        p_ht1_ft1 += tp
                    # 2/2
                    if a1 > h1 and (a1 + a2) > (h1 + h2):
                        p_ht2_ft2 += tp
                    # 1/2 (HT Home leads, FT Away wins)
                    if h1 > a1 and (h1 + h2) < (a1 + a2):
                        p_1_2 += tp
                    # 2/1 (HT Away leads, FT Home wins)
                    if a1 > h1 and (h1 + h2) > (a1 + a2):
                        p_2_1 += tp

    # Check markets
    all_mkts = m.get('all_markets', [])
    mkt_odds = {}
    for mkt in all_mkts:
        mtid = mkt.get('mtid')
        for o in mkt.get('outcomes', []):
            label = o.get('label')
            odd = o.get('odd')
            if mtid == 5: # İY/MS
                mkt_odds[f"iyms_{label}"] = odd
            elif mtid == 209: # 1. Yarı 0.5 Üst
                mkt_odds[f"iy05_{label}"] = odd

    scanned.append({
        'code': code,
        'match': f"{home} vs {away}",
        'league': leg,
        'time': time,
        'tot_xg': round(tot_xg, 2),
        'p_1h_over05': round(p_1h_over05, 1),
        'p_2h_over05': round(p_2h_over05, 1),
        'p_both_halves': round(p_both_halves, 1),
        'p_1_1': round(p_ht1_ft1 * 100, 1),
        'p_2_2': round(p_ht2_ft2 * 100, 1),
        'p_1_2': round(p_1_2 * 100, 2),
        'p_2_1': round(p_2_1 * 100, 2),
        'odds': odds,
        'mkt_odds': mkt_odds
    })

# Print top 1. Yarı 0.5 Üst (%75 - %85 Güven)
print("=== 1. YARI 0.5 GOL ÜST (İLK YARIDA EN AZ 1 GOL OLUR: EVET) ===")
top_1h = sorted(scanned, key=lambda x: x['p_1h_over05'], reverse=True)[:8]
for x in top_1h:
    print(f"[{x['time']}] #{x['code']} {x['match']} ({x['league']}) | xG: {x['tot_xg']} | 1.Y 0.5 Üst Güveni: %{x['p_1h_over05']} | Oran: {x['mkt_odds'].get('iy05_Üst', '1.32-1.38')}")

print("\n=== HER İKİ YARIDA DA GOL OLUR (EVET / EVET SEÇENEĞİ) ===")
top_both = sorted(scanned, key=lambda x: x['p_both_halves'], reverse=True)[:8]
for x in top_both:
    print(f"[{x['time']}] #{x['code']} {x['match']} ({x['league']}) | xG: {x['tot_xg']} | Her İki Yarı Gol Güveni: %{x['p_both_halves']} | Tahmini Oran: 1.55-1.70")

print("\n=== İY/MS: 1/1 ve 2/2 (FAVORİ İLK YARIDAN BİTİRİR) ===")
top_htft = sorted(scanned, key=lambda x: max(x['p_1_1'], x['p_2_2']), reverse=True)[:8]
for x in top_htft:
    is_home = x['p_1_1'] > x['p_2_2']
    pick = "1/1" if is_home else "2/2"
    val = x['p_1_1'] if is_home else x['p_2_2']
    odd = x['mkt_odds'].get(f"iyms_{pick}", '1.45-1.60')
    print(f"[{x['time']}] #{x['code']} {x['match']} ({x['league']}) | Tercih: {pick} | Güven: %{val} | Oran: {odd}")

print("\n=== İY/MS: 1/2 ve 2/1 (GERİ DÖNÜŞ / BOMBA TARAMASI) ===")
top_comeback = sorted(scanned, key=lambda x: max(x['p_1_2'], x['p_2_1']), reverse=True)[:8]
for x in top_comeback:
    is_2_1 = x['p_2_1'] > x['p_1_2']
    pick = "2/1 (İlk Yarı Dep Önde, Maç Sonu Ev Kazanır)" if is_2_1 else "1/2 (İlk Yarı Ev Önde, Maç Sonu Dep Kazanır)"
    prob = x['p_2_1'] if is_2_1 else x['p_1_2']
    odd = x['mkt_odds'].get("iyms_2/1" if is_2_1 else "iyms_1/2", "26.0 - 34.0")
    print(f"[{x['time']}] #{x['code']} {x['match']} ({x['league']}) | Potansiyel: {pick} | Model Olasılığı: %{prob} | Oran: {odd}")
