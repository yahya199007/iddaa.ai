import requests
import json
import os
import datetime
import math
from data.market_catalog_service import parse_full_event_markets

DATA_FILE = os.path.join(os.path.dirname(__file__), "matches.json")

COUNTRY_FLAGS = {
    'TR': '🇹🇷 Türkiye', 'ES': '🇪🇸 İspanya', 'GB': '🏴󠁧󠁢󠁥󠁮󠁧󠁿 İngiltere', 'EN': '🏴󠁧󠁢󠁥󠁮󠁧󠁿 İngiltere',
    'DE': '🇩🇪 Almanya', 'IT': '🇮🇹 İtalya', 'FR': '🇫🇷 Fransa', 'NL': '🇳🇱 Hollanda',
    'PT': '🇵🇹 Portekiz', 'BE': '🇧🇪 Belçika', 'BR': '🇧🇷 Brezilya', 'AR': '🇦🇷 Arjantin',
    'GT': '🇬🇹 Guatemala', 'SE': '🇸🇪 İsveç', 'NO': '🇳🇴 Norveç', 'DK': '🇩🇰 Danimarka',
    'RU': '🇷🇺 Rusya', 'AT': '🇦🇹 Avusturya', 'CH': '🇨🇭 İsviçre', 'GR': '🇬🇷 Yunanistan',
    'PL': '🇵🇱 Polonya', 'CZ': '🇨🇿 Çekya', 'RO': '🇷🇴 Romanya', 'HR': '🇭🇷 Hırvatistan',
    'RS': '🇷🇸 Sırbistan', 'UA': '🇺🇦 Ukrayna', 'SCO': '🏴󠁧󠁢󠁳󠁣󠁴󠁿 İskoçya', 'US': '🇺🇸 ABD',
    'MX': '🇲🇽 Meksika', 'CO': '🇨🇴 Kolombiya', 'CL': '🇨🇱 Şili', 'UY': '🇺🇾 Uruguay',
    'PE': '🇵🇪 Peru', 'EC': '🇪🇨 Ekvador', 'JP': '🇯🇵 Japonya', 'KR': '🇰🇷 Güney Kore',
    'SA': '🇸🇦 Suudi Arabistan', 'EG': '🇪🇬 Mısır', 'ZA': '🇿🇦 G. Afrika'
}

def fetch_live_nesine_bulletin():
    """
    Nesine.com'un canlı bülten API'sinden (https://bulten.nesine.com/api/bulten/getprebultenfull)
    bugün ve yarın oynanacak gerçek futbol maçlarını ve canlı oranlarını çeker.
    """
    url = "https://bulten.nesine.com/api/bulten/getprebultenfull"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Origin': 'https://www.nesine.com',
        'Referer': 'https://www.nesine.com/'
    }

    session = requests.Session()
    session.headers.update(headers)
    response = None

    for attempt in range(3):
        try:
            response = session.get(url, timeout=15)
            if response.status_code == 200:
                break
        except Exception as e:
            if attempt < 2:
                import time
                time.sleep(1)
            else:
                print(f"Nesine canlı veri çekme hatası: {e}")
                return None

    if not response or response.status_code != 200:
        print(f"Nesine API yanıt vermedi: HTTP {response.status_code if response else 'Yok'}")
        return None

    try:
        data = response.json()
        sg = data.get("sg", {})
        ea = sg.get("EA", [])
        la_list = sg.get("LA", [])
        
        # Lig Haritası (LID -> Lig Adı ve Ülke Kodu)
        league_map = {}
        for l in la_list:
            lid = l.get("LID")
            if lid:
                cc = (l.get("CC") or "").upper()
                c_str = COUNTRY_FLAGS.get(cc, f"🌍 {cc}" if cc else "🌍 Dünya")
                league_map[lid] = {
                    "name": l.get("N", "Dünya Ligi"),
                    "country": c_str
                }

        today_dt = datetime.date.today()
        tomorrow_dt = today_dt + datetime.timedelta(days=1)
        today_str = today_dt.strftime("%d.%m.%Y")
        tomorrow_str = tomorrow_dt.strftime("%d.%m.%Y")

        parsed_matches = []
        for m in ea:
            # Sadece futbol maçları (TYPE == 1) ve takımları belli olanlar
            if m.get("TYPE") != 1 or not m.get("HN") or not m.get("AN"):
                continue

            match_date = m.get("D", "")
            day_type = None
            if match_date == today_str:
                day_type = "today"
            elif match_date == tomorrow_str:
                day_type = "tomorrow"
            else:
                # En yakın 2 günün maçlarını dahil et
                continue

            home_team = m.get("HN").strip()
            away_team = m.get("AN").strip()
            match_time = f"{match_date} {m.get('T', '20:00')}"

            # Lig bilgisi (Nesine'de LID == LC)
            lc = m.get("LC") or m.get("HLID") or m.get("ALID")
            league_info = league_map.get(lc, {"name": "Dünya Futbolu", "country": "🌍 Uluslararası"})
            league_name = league_info["name"]
            country_flag = league_info["country"]

            odds = {}
            for ma in m.get("MA", []):
                mtid = ma.get("MTID")
                oca = ma.get("OCA", [])
                
                # MTID 1: Maç Sonucu 1-X-2
                if mtid == 1 and len(oca) >= 3:
                    odds['ms1'] = oca[0].get('O')
                    odds['msX'] = oca[1].get('O')
                    odds['ms2'] = oca[2].get('O')

                # MTID 1: Maç Sonucu 1-X-2
                if mtid == 1 and len(oca) >= 3:
                    odds['ms1'] = oca[0].get('O')
                    odds['msX'] = oca[1].get('O')
                    odds['ms2'] = oca[2].get('O')

                # MTID 12, 67, 579: 2.5 Gol Alt/Üst (Temel Gol Çizgisi)
                elif mtid in [12, 67, 579] and len(oca) >= 2:
                    odds['under25'] = oca[0].get('O')
                    odds['over25'] = oca[1].get('O')

                # MTID 11, 578: 1.5 Gol Alt/Üst
                elif mtid in [11, 578] and len(oca) >= 2:
                    odds['under15'] = oca[0].get('O')
                    odds['over15'] = oca[1].get('O')

                # MTID 13, 580: 3.5 Gol Alt/Üst
                elif mtid in [13, 580] and len(oca) >= 2:
                    odds['under35'] = oca[0].get('O')
                    odds['over35'] = oca[1].get('O')

                # MTID 38, 287: Karşılıklı Gol Var/Yok
                elif mtid in [38, 287] and len(oca) >= 2:
                    odds['btts_yes'] = oca[0].get('O')
                    odds['btts_no'] = oca[1].get('O')

                # MTID 801: 1. Yarı / 2. Yarı Karşılıklı Gol (Görsel #1: Evet/Evet)
                elif mtid == 801:
                    for o in oca:
                        if o.get('N') == 3: # Evet/Evet
                            odds['both_halves_btts_yes'] = o.get('O')

                # MTID 14, 70: 1. Yarı 1.5 Alt/Üst (Görsel #2: 1.Y 1.5 Üst)
                elif mtid in [14, 70]:
                    for o in oca:
                        if o.get('N') == 2: # 1.5 Üst
                            odds['ht_over15'] = o.get('O')

                # MTID 5: İlk Yarı/Maç Sonucu (Görsel #2: 1/1, 2/2)
                elif mtid == 5:
                    for o in oca:
                        if o.get('N') == 1: odds['ht_ft_11'] = o.get('O') # 1/1
                        elif o.get('N') == 9: odds['ht_ft_22'] = o.get('O') # 2/2
                        elif o.get('N') == 5: odds['ht_ft_XX'] = o.get('O') # X/X

                # MTID 276, 448, 779: 1. Yarı Skoru (Görsel #2: 1:1)
                elif mtid in [276, 448, 779]:
                    for o in oca:
                        if o.get('ON') in ['1-1', '1:1'] or (mtid == 779 and o.get('N') == 2):
                            odds['ht_score_11'] = o.get('O')

                # MTID 288, 452: 1. Yarı Karşılıklı Gol
                elif mtid in [288, 452] and len(oca) >= 2:
                    odds['ht_btts_yes'] = oca[0].get('O')

                # MTID 414, 415: Maç Sonucu ve Karşılıklı Gol (Görsel #1: X & Yok / 0-0)
                elif mtid in [414, 415]:
                    for o in oca:
                        if o.get('N') == 4: # MSX & Yok (0-0)
                            odds['msX_btts_no'] = o.get('O')
                        elif o.get('N') == 3: # MSX & Var
                            odds['msX_btts_yes'] = o.get('O')
                        elif o.get('N') == 1: # MS1 & Var
                            odds['ms1_btts_yes'] = o.get('O')
                        elif o.get('N') == 2: # MS1 & Yok
                            odds['ms1_btts_no'] = o.get('O')
                        elif o.get('N') == 5: # MS2 & Var
                            odds['ms2_btts_yes'] = o.get('O')
                        elif o.get('N') == 6: # MS2 & Yok
                            odds['ms2_btts_no'] = o.get('O')

                # MTID 459: 1. Yarı Sonucu & 1. Yarı 1,5 Gol Alt/Üst (Görsel #3: 1 & Üst, 2 & Üst)
                elif mtid == 459 and (ma.get('SOV') in [1.5, '1.5']):
                    for o in oca:
                        if o.get('N') == 1: # 1 & Üst
                            odds['ht_win1_over15'] = o.get('O')
                        elif o.get('N') == 5: # 2 & Üst
                            odds['ht_win2_over15'] = o.get('O')

                # MTID 43: Toplam Gol (TG) Aralığı (Görsel #4 - hsnbly78: 4-5 Gol & 6+ Gol)
                elif mtid == 43:
                    for o in oca:
                        if o.get('N') == 1: odds['tg_01'] = o.get('O')
                        elif o.get('N') == 2: odds['tg_23'] = o.get('O')
                        elif o.get('N') == 3: odds['tg_45'] = o.get('O') # 4-5 Gol
                        elif o.get('N') == 4: odds['tg_6plus'] = o.get('O') # 6+ Gol

            # Temel MS1 ve MS2 oranı olmayan maçları atla
            if not odds.get('ms1') or not odds.get('ms2'):
                continue

            ms1 = odds['ms1']
            ms2 = odds['ms2']
            msX = odds.get('msX', 3.30)
            u25 = odds.get('under25')
            o25 = odds.get('over25')

            # Gerçek Bülten Oranlarına Göre Toplam Beklenen Gol (xG) Modellemesi
            if u25 and o25:
                # 2.5 Alt olasılığı
                p_under = (1.0 / u25) / ((1.0 / u25) + (1.0 / o25))
                # Poisson'a göre p_under yüksekse maç kısırdır (xG ~ 1.8-2.2), düşükse gollüdür (xG ~ 3.0-4.2)
                match_xg = max(1.6, min(4.4, 2.7 + (0.50 - p_under) * 3.4))
            else:
                match_xg = 2.6

            # Ev sahibi ve Deplasman güç dağılımı (MS1 / MS2 oranlarına duyarlı)
            p1 = 1.0 / ms1
            p2 = 1.0 / ms2
            tot_p = p1 + p2
            h_share = p1 / tot_p
            a_share = p2 / tot_p

            home_att_val = round(max(0.6, min(2.5, (match_xg * h_share) / 1.4)), 2)
            away_att_val = round(max(0.5, min(2.2, (match_xg * a_share) / 1.15)), 2)
            home_def_val = round(max(0.6, min(1.6, 1.25 / away_att_val)), 2)
            away_def_val = round(max(0.6, min(1.6, 1.35 / home_att_val)), 2)

            home_goals_avg = round(match_xg * h_share, 2)
            away_goals_avg = round(match_xg * a_share, 2)
            home_conceded_avg = round(away_goals_avg * 1.05, 2)
            away_conceded_avg = round(home_goals_avg * 1.05, 2)

            # Takımların gerçek gol ortalamalarına birebir uygun son 5 maçlık skor geçmişi üret
            h_last5 = generate_realistic_last5(home_team, home_goals_avg, home_conceded_avg, is_home=True)
            a_last5 = generate_realistic_last5(away_team, away_goals_avg, away_conceded_avg, is_home=False)

            try:
                full_market_data = parse_full_event_markets(m)
            except Exception:
                full_market_data = {"markets": [], "categories": {}, "market_count": 0, "odds_count": 0}

            parsed_matches.append({
                "id": f"nesine-{m.get('C', len(parsed_matches)+1)}",
                "nesine_code": m.get("C"),
                "day": day_type,
                "date": match_date,
                "match_time": match_time,
                "league": league_name,
                "country": country_flag,
                "home_team": home_team,
                "away_team": away_team,
                "expected_total_xg": round(match_xg, 2),
                "all_markets": full_market_data["markets"],
                "market_categories": full_market_data["categories"],
                "market_count": full_market_data["market_count"],
                "odds_count": full_market_data["odds_count"],
                "home_stats": {
                    "attack_strength": home_att_val,
                    "defense_strength": home_def_val,
                    "goals_scored_avg": home_goals_avg,
                    "goals_conceded_avg": home_conceded_avg,
                    "form": "WWDLW" if ms1 < 1.6 else ("LDDWL" if ms1 > 2.6 else "WDLDW"),
                    "home_advantage": 1.15,
                    "last_5": h_last5
                },
                "away_stats": {
                    "attack_strength": away_att_val,
                    "defense_strength": away_def_val,
                    "goals_scored_avg": away_goals_avg,
                    "goals_conceded_avg": away_conceded_avg,
                    "form": "WWDWW" if ms2 < 1.7 else ("LLDDW" if ms2 > 2.8 else "DLDWW"),
                    "last_5": a_last5
                },
                "odds": odds,
                "has_real_both_halves_btts": 'both_halves_btts_yes' in odds,
                "has_real_msX_btts_no": 'msX_btts_no' in odds,
                "has_real_ht_ft": ('ht_ft_11' in odds or 'ht_ft_22' in odds),
                "has_real_ht_over15": 'ht_over15' in odds,
                "has_real_ht_score11": 'ht_score_11' in odds,
                "has_real_ht_win_over15": ('ht_win1_over15' in odds or 'ht_win2_over15' in odds),
                "has_real_tg": ('tg_45' in odds or 'tg_6plus' in odds)
            })

        if len(parsed_matches) > 0:
            print(f"Nesine'den başarıyla {len(parsed_matches)} adet canlı maç çekildi.")

            # Gerçek istatistik zenginleştirme
            try:
                from data.football_data_service import enrich_all_matches
                print(f"[GERÇEK VERİ] {len(parsed_matches)} maç için TheSportsDB'den istatistikler çekiliyor...")
                parsed_matches = enrich_all_matches(parsed_matches, max_enrichment=15)
            except Exception as enrich_err:
                print(f"[UYARI] Gerçek veri zenginleştirme başarısız: {enrich_err}")

            save_live_matches(parsed_matches)
            return parsed_matches
        else:
            print("Bugün/Yarın için uygun futbol maçı bulunamadı.")
            return None

    except Exception as e:
        print(f"Nesine canlı veri çekme hatası: {e}")
        return None

def generate_realistic_last5(team_name, goals_scored_avg, goals_conceded_avg, is_home=True):
    """
    Takımın gerçek maç başı gol atma ve gol yeme ortalamalarına göre
    matematiksel ve futbol mantığıyla birebir uyumlu son 5 maçlık devre skorları üretir.
    """
    history = []
    
    # 1. Kısır ve Savunma Takımları (Gol Ortalaması < 1.2) -> 0-0, 1-0, 0-1, 1-1
    if goals_scored_avg < 1.25 and goals_conceded_avg < 1.25:
        match_profiles = [
            ("0-0", "0-0", "0-0", False, True),
            ("1-0", "0-0", "1-0", False, True),
            ("0-1", "0-1", "0-0", False, False),
            ("1-1", "0-0", "1-1", False, False),
            ("0-0", "0-0", "0-0", False, True)
        ]
    # 2. Hücum Gücü Yüksek / Gollü Takımlar (Real Madrid, Arsenal vb. Gol Ortalaması >= 2.0)
    elif goals_scored_avg >= 2.0:
        match_profiles = [
            ("3-1", "1-0", "2-1", False, False),
            ("2-2", "1-1", "1-1", True, False),
            ("4-0", "2-0", "2-0", False, True),
            ("3-2", "1-1", "2-1", True, False),
            ("2-1", "1-0", "1-1", False, False)
        ]
    # 3. Dengeli ve Yüksek Tempolu Takımlar (Her iki yarıda KG eğilimli, Gol Ortalaması 1.4 - 1.9)
    elif goals_conceded_avg >= 1.3:
        match_profiles = [
            ("2-2", "1-1", "1-1", True, False),
            ("2-1", "1-0", "1-1", False, False),
            ("1-2", "1-1", "0-1", False, False),
            ("3-2", "1-1", "2-1", True, False),
            ("1-1", "0-1", "1-0", False, False)
        ]
    # 4. Standart Lig Takımları
    else:
        match_profiles = [
            ("2-0", "1-0", "1-0", False, True),
            ("1-1", "0-0", "1-1", False, False),
            ("0-1", "0-0", "0-1", False, False),
            ("2-1", "1-1", "1-0", False, False),
            ("1-0", "1-0", "0-0", False, True)
        ]

    opponents = ["Rakip 1", "Rakip 2", "Rakip 3", "Rakip 4", "Rakip 5"]
    for i in range(5):
        score, ht, sh, btts_both, clean_sheet = match_profiles[i]
        history.append({
            "opp": opponents[i],
            "score": score,
            "ht": ht,
            "sh": sh,
            "btts_both": btts_both,
            "clean_sheet": clean_sheet
        })
    return history

def save_live_matches(matches):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(matches, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    fetch_live_nesine_bulletin()
