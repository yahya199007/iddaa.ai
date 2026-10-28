"""
The Odds API Entegrasyonu
https://the-odds-api.com/
- Ücretsiz plan: 500 istek/ay
- 80+ bookmaker'dan gerçek oranlar (Bet365, William Hill, Pinnacle, DraftKings vb.)
- Futbol, basketbol, tenis ve daha fazlası

API Key almak için: https://the-odds-api.com/ (ücretsiz kayıt)
API Key'inizi aşağıya girin veya ODDS_API_KEY ortam değişkeni olarak ayarlayın.
"""

import os
import json
import requests
import datetime
import time
from pathlib import Path

# ─── API KEY AYARI ─────────────────────────────────────────────────────────────
# Ücretsiz API key için: https://the-odds-api.com/
# Aşağıya direkt yazabilir veya .env dosyasına ODDS_API_KEY=xxxx yazabilirsiniz
ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "")  # Buraya API key'inizi girin

ODDS_API_BASE = "https://api.the-odds-api.com/v4"

CACHE_DIR = Path(__file__).parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)

# The Odds API'deki bookmaker key'leri (desteklenen siteler)
BOOKMAKER_KEYS = [
    "bet365", "williamhill", "ladbrokes_eu", "coral", "betfred",
    "paddypower", "skybet", "betfair", "betvictor",
    "pinnacle", "unibet_eu", "bwin", "betsson", "nordicbet",
    "draftkings", "fanduel", "betmgm", "caesars", "betrivers",
    "winamax", "betclic", "leovegas",
    "sportsbet", "tab", "pointsbet",
    "1xbet", "betonline", "bovada",
]

# Futbol (soccer) spor key'leri - The Odds API'nin desteklediği ligler
SOCCER_SPORT_KEYS = {
    "Süper Lig": "soccer_turkey_super_lig",
    "Premier League": "soccer_england_league1",  # Gerçekte: soccer_epl
    "Premier League (İngiltere)": "soccer_epl",
    "La Liga": "soccer_spain_la_liga",
    "Bundesliga": "soccer_germany_bundesliga",
    "Serie A": "soccer_italy_serie_a",
    "Ligue 1": "soccer_france_ligue_one",
    "Eredivisie": "soccer_netherlands_eredivisie",
    "Champions League": "soccer_uefa_champs_league",
    "Europa League": "soccer_uefa_europa_league",
    "Conference League": "soccer_uefa_europa_conference_league",
    "Dünya Futbolu": "soccer_fifa_world_cup",
    "MLS": "soccer_usa_mls",
    "Liga MX": "soccer_mexico_ligamx",
    "Primera Division (Arjantin)": "soccer_argentina_primera_division",
    "Scottish Premiership": "soccer_scotland_premiership",
}


def get_cached(key, ttl_minutes=15):
    cache_file = CACHE_DIR / f"odds_api_{key}.json"
    if cache_file.exists():
        age = (time.time() - cache_file.stat().st_mtime) / 60
        if age < ttl_minutes:
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
    return None


def set_cached(key, data):
    cache_file = CACHE_DIR / f"odds_api_{key}.json"
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def fetch_odds_for_sport(sport_key, bookmakers=None, markets="h2h,totals"):
    """
    The Odds API'den belirli bir spor için oranları çeker.
    market: 'h2h' = Maç Sonucu 1X2, 'totals' = Alt/Üst 2.5
    """
    if not ODDS_API_KEY:
        print("[The Odds API] API key tanımlı değil. https://the-odds-api.com/ adresinden ücretsiz alabilirsiniz.")
        return None

    cache_key = f"{sport_key}_{markets}"
    cached = get_cached(cache_key, ttl_minutes=15)
    if cached:
        print(f"[The Odds API] Cache'den yüklendi: {sport_key}")
        return cached

    bm_str = ",".join(bookmakers or BOOKMAKER_KEYS[:15])  # İlk 15 bookmaker
    url = f"{ODDS_API_BASE}/sports/{sport_key}/odds/"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "eu,uk,us,au",
        "markets": markets,
        "oddsFormat": "decimal",
        "dateFormat": "iso",
        "bookmakers": bm_str,
    }

    try:
        r = requests.get(url, params=params, timeout=12)
        remaining = r.headers.get("x-requests-remaining", "?")
        used = r.headers.get("x-requests-used", "?")
        print(f"[The Odds API] {sport_key} - Kalan istek: {remaining}/{used}")

        if r.status_code == 200:
            data = r.json()
            set_cached(cache_key, data)
            return data
        elif r.status_code == 401:
            print("[The Odds API] Geçersiz API key! https://the-odds-api.com/ adresinden kontrol edin.")
        elif r.status_code == 429:
            print("[The Odds API] İstek limiti doldu. Ücretsiz plan: 500 istek/ay")
        else:
            print(f"[The Odds API] HTTP {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"[The Odds API] Bağlantı hatası: {e}")

    return None


def fetch_all_soccer_odds():
    """
    Tüm ana futbol ligleri için oranları çeker ve birleştirir.
    """
    all_odds = []
    priority_sports = [
        "soccer_epl",
        "soccer_spain_la_liga",
        "soccer_germany_bundesliga",
        "soccer_italy_serie_a",
        "soccer_france_ligue_one",
        "soccer_uefa_champs_league",
        "soccer_uefa_europa_league",
        "soccer_turkey_super_lig",
    ]

    for sport_key in priority_sports:
        data = fetch_odds_for_sport(sport_key)
        if data:
            all_odds.extend(data)
            time.sleep(0.5)  # Rate limit koruması

    print(f"[The Odds API] Toplam {len(all_odds)} maç için çoklu bookmaker oranı çekildi.")
    return all_odds


def parse_odds_api_match(event):
    """
    The Odds API formatını uygulama formatına dönüştürür.
    Tüm bookmaker oranlarını yapılandırılmış biçimde döndürür.
    """
    bookmakers_data = {}
    best_ms1 = 0
    best_msX = 0
    best_ms2 = 0
    best_over25 = 0
    best_under25 = 0
    best_bookmaker_ms1 = ""
    best_bookmaker_ms2 = ""
    best_bookmaker_over = ""

    for bm in event.get("bookmakers", []):
        bm_key = bm.get("key", "")
        bm_name = bm.get("title", bm_key)
        bm_odds = {}

        for market in bm.get("markets", []):
            market_key = market.get("key", "")

            if market_key == "h2h":
                outcomes = {o["name"]: o["price"] for o in market.get("outcomes", [])}
                home = event.get("home_team", "")
                away = event.get("away_team", "")
                ms1 = outcomes.get(home, 0)
                msX = outcomes.get("Draw", 0)
                ms2 = outcomes.get(away, 0)
                bm_odds["ms1"] = ms1
                bm_odds["msX"] = msX
                bm_odds["ms2"] = ms2

                if ms1 > best_ms1:
                    best_ms1 = ms1
                    best_bookmaker_ms1 = bm_name
                if ms2 > best_ms2:
                    best_ms2 = ms2
                    best_bookmaker_ms2 = bm_name
                if msX > best_msX:
                    best_msX = msX

            elif market_key == "totals":
                for outcome in market.get("outcomes", []):
                    if outcome.get("point") == 2.5:
                        if outcome["name"] == "Over":
                            bm_odds["over25"] = outcome["price"]
                            if outcome["price"] > best_over25:
                                best_over25 = outcome["price"]
                                best_bookmaker_over = bm_name
                        elif outcome["name"] == "Under":
                            bm_odds["under25"] = outcome["price"]
                            if outcome["price"] > best_under25:
                                best_under25 = outcome["price"]

        if bm_odds:
            bookmakers_data[bm_key] = {
                "name": bm_name,
                "odds": bm_odds,
                "url": _get_bookmaker_url(bm_key),
            }

    return {
        "bookmakers": bookmakers_data,
        "best_odds": {
            "ms1": {"odd": round(best_ms1, 2), "bookmaker": best_bookmaker_ms1},
            "msX": {"odd": round(best_msX, 2), "bookmaker": ""},
            "ms2": {"odd": round(best_ms2, 2), "bookmaker": best_bookmaker_ms2},
            "over25": {"odd": round(best_over25, 2), "bookmaker": best_bookmaker_over},
            "under25": {"odd": round(best_under25, 2), "bookmaker": ""},
        },
        "bookmaker_count": len(bookmakers_data),
    }


def _get_bookmaker_url(bm_key):
    urls = {
        "bet365": "https://www.bet365.com",
        "williamhill": "https://www.williamhill.com",
        "ladbrokes_eu": "https://www.ladbrokes.com",
        "coral": "https://www.coral.co.uk",
        "betfred": "https://www.betfred.com",
        "paddypower": "https://www.paddypower.com",
        "skybet": "https://m.skybet.com",
        "betfair": "https://www.betfair.com",
        "betvictor": "https://www.betvictor.com",
        "pinnacle": "https://www.pinnacle.com",
        "unibet_eu": "https://www.unibet.com",
        "bwin": "https://sports.bwin.com",
        "betsson": "https://www.betsson.com",
        "nordicbet": "https://www.nordicbet.com",
        "draftkings": "https://sportsbook.draftkings.com",
        "fanduel": "https://sportsbook.fanduel.com",
        "betmgm": "https://sports.betmgm.com",
        "caesars": "https://www.caesars.com/sportsbook-and-casino",
        "betrivers": "https://betrivers.com",
        "winamax": "https://www.winamax.fr",
        "betclic": "https://www.betclic.fr",
        "leovegas": "https://www.leovegas.com",
        "sportsbet": "https://www.sportsbet.com.au",
        "tab": "https://www.tab.com.au",
        "pointsbet": "https://pointsbet.com",
        "1xbet": "https://1xbet.com",
        "betonline": "https://www.betonline.ag",
        "bovada": "https://www.bovada.lv",
    }
    return urls.get(bm_key, "#")


def match_nesine_to_odds_api(nesine_match, odds_api_events):
    """
    Nesine bültenindeki maçı The Odds API eventleriyle eşleştirir.
    Takım ismi benzerliği kullanır.
    """
    home = nesine_match.get("home_team", "").lower().strip()
    away = nesine_match.get("away_team", "").lower().strip()

    def similarity(a, b):
        """Basit string benzerlik skoru"""
        a_words = set(a.split())
        b_words = set(b.split())
        if not a_words or not b_words:
            return 0
        common = a_words & b_words
        return len(common) / max(len(a_words), len(b_words))

    best_match = None
    best_score = 0.0

    for event in odds_api_events:
        e_home = event.get("home_team", "").lower().strip()
        e_away = event.get("away_team", "").lower().strip()

        # Önce tam eşleşme dene
        if home in e_home or e_home in home:
            if away in e_away or e_away in away:
                score = 1.0
                if score > best_score:
                    best_score = score
                    best_match = event
                    continue

        # Benzerlik skoru
        home_sim = similarity(home, e_home)
        away_sim = similarity(away, e_away)
        total_sim = (home_sim + away_sim) / 2

        if total_sim > best_score and total_sim >= 0.5:
            best_score = total_sim
            best_match = event

    if best_match and best_score >= 0.5:
        return parse_odds_api_match(best_match), best_score

    return None, 0


def enrich_nesine_matches_with_global_odds(nesine_matches):
    """
    Nesine maçlarını global bookmaker oranlarıyla zenginleştirir.
    The Odds API üzerinden 30+ bookmaker'dan en yüksek oranları bulur.
    """
    if not ODDS_API_KEY:
        print("[Global Oranlar] API key yok - sadece Nesine oranları kullanılıyor.")
        print("[Global Oranlar] Ücretsiz API key için: https://the-odds-api.com/")
        return nesine_matches

    # Tüm futbol oranlarını çek
    all_odds_events = fetch_all_soccer_odds()
    if not all_odds_events:
        return nesine_matches

    enriched = []
    matched_count = 0

    for match in nesine_matches:
        global_data, score = match_nesine_to_odds_api(match, all_odds_events)

        if global_data and score >= 0.5:
            match["global_odds"] = global_data
            match["global_odds_matched"] = True
            match["global_odds_confidence"] = round(score * 100)
            matched_count += 1

            # En iyi oranı nesine oranıyla karşılaştır
            best = global_data.get("best_odds", {})
            nesine_ms1 = match.get("odds", {}).get("ms1", 0)
            nesine_ms2 = match.get("odds", {}).get("ms2", 0)

            if best.get("ms1", {}).get("odd", 0) > nesine_ms1:
                match["better_ms1_available"] = {
                    "odd": best["ms1"]["odd"],
                    "bookmaker": best["ms1"]["bookmaker"]
                }
            if best.get("ms2", {}).get("odd", 0) > nesine_ms2:
                match["better_ms2_available"] = {
                    "odd": best["ms2"]["odd"],
                    "bookmaker": best["ms2"]["bookmaker"]
                }
        else:
            match["global_odds_matched"] = False

        enriched.append(match)

    print(f"[Global Oranlar] {matched_count}/{len(nesine_matches)} maç global bookmaker oranlarıyla eşleştirildi.")
    return enriched


def get_odds_api_status():
    """API kullanım durumunu kontrol eder"""
    if not ODDS_API_KEY:
        return {
            "configured": False,
            "message": "API key tanımlı değil",
            "setup_url": "https://the-odds-api.com/",
            "free_plan": "500 istek/ay ücretsiz"
        }

    try:
        r = requests.get(
            f"{ODDS_API_BASE}/sports/",
            params={"apiKey": ODDS_API_KEY},
            timeout=8
        )
        remaining = r.headers.get("x-requests-remaining", "?")
        used = r.headers.get("x-requests-used", "?")

        if r.status_code == 200:
            return {
                "configured": True,
                "valid": True,
                "requests_remaining": remaining,
                "requests_used": used,
                "message": f"✅ API key geçerli | Kalan: {remaining} istek"
            }
        else:
            return {
                "configured": True,
                "valid": False,
                "message": f"❌ API key geçersiz (HTTP {r.status_code})"
            }
    except Exception as e:
        return {
            "configured": True,
            "valid": False,
            "message": f"❌ Bağlantı hatası: {str(e)}"
        }
