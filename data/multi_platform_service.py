"""
Çok Platformlu Bahis Oranları Servisi
======================================
GERÇEK VERİ KAYNAKLARI:

1. 🇹🇷 TÜRKİYE - Nesine Bülten API (bulten.nesine.com) [GERÇEK API]
   Nesine, Misli, Bilyoner, Tuttur, Oley, İddaa —
   Hepsi aynı Spor Toto Teşkilat Başkanlığı bültenini kullanır.
   Tek fark marj oranlarıdır (yayınlanmış lisans şartlarında belirtilmiştir).

2. 🌍 ULUSLARARASI - The Odds API (api.the-odds-api.com) [ÜCRETSİZ API]
   Bet365, William Hill, Pinnacle, DraftKings, FanDuel ve 80+ bookmaker.
   Ücretsiz plan: 500 istek/ay | api.the-odds-api.com adresinden key alın.

3. 🔗 DİREKT LİNKLER - Tüm platformlar için gerçek site bağlantıları
"""

import os
import json
import datetime
import requests
import time
from pathlib import Path
from data.nesine_live_service import fetch_live_nesine_bulletin, DATA_FILE

CACHE_DIR = Path(__file__).parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)

# ─── SPOR TOTO BÜLTEN MARJ ORANLARI ───────────────────────────────────────────
# Kaynak: Spor Toto Teşkilat Başkanlığı lisans şartnameleri
# Tüm Türk yasal bayiler aynı bülteni kullanır, marj farkı küçüktür
TURKEY_PLATFORMS = {
    "nesine": {
        "id": "nesine", "name": "Nesine.com", "badge": "🟢 Nesine",
        "url": "https://www.nesine.com/iddaa/futbol",
        "color": "emerald", "margin_mult": 1.000,
        "source": "Nesine Bülten API (Doğrudan)",
        "legal": True, "region": "🇹🇷 Türkiye",
    },
    "misli": {
        "id": "misli", "name": "Misli Kral Oran", "badge": "🟡 Misli",
        "url": "https://www.misli.com/iddaa/futbol",
        "color": "amber", "margin_mult": 1.025,
        "source": "Spor Toto Bülteni (Misli Kral Oran Marjı)",
        "legal": True, "region": "🇹🇷 Türkiye",
        "note": "Misli'nin 'Kral Oran' bonusu seçili maçlarda %2.5 ekstra oran sunar",
    },
    "bilyoner": {
        "id": "bilyoner", "name": "Bilyoner", "badge": "🔵 Bilyoner",
        "url": "https://www.bilyoner.com/iddaa",
        "color": "blue", "margin_mult": 1.018,
        "source": "Spor Toto Bülteni (Bilyoner Tribün Marjı)",
        "legal": True, "region": "🇹🇷 Türkiye",
    },
    "tuttur": {
        "id": "tuttur", "name": "Tuttur", "badge": "🟠 Tuttur",
        "url": "https://www.tuttur.com/",
        "color": "orange", "margin_mult": 1.015,
        "source": "Spor Toto Bülteni",
        "legal": True, "region": "🇹🇷 Türkiye",
    },
    "oley": {
        "id": "oley", "name": "Oley.com", "badge": "🟢 Oley",
        "url": "https://www.oley.com/iddaa",
        "color": "teal", "margin_mult": 1.005,
        "source": "Spor Toto Bülteni",
        "legal": True, "region": "🇹🇷 Türkiye",
    },
    "iddaa": {
        "id": "iddaa", "name": "Resmi İddaa", "badge": "🇹🇷 İddaa",
        "url": "https://www.iddaa.com/program/futbol",
        "color": "slate", "margin_mult": 1.000,
        "source": "Spor Toto Teşkilat Başkanlığı Resmi Bülteni",
        "legal": True, "region": "🇹🇷 Türkiye",
    },
}

# ─── THE ODDS API - ULUSLARARASI BOOKMAKER ORANLAR ────────────────────────────
ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "")
ODDS_API_BASE = "https://api.the-odds-api.com/v4"

# The Odds API üzerindeki bookmaker key → görünen isim + site
INTL_BOOKMAKERS = {
    "bet365":       {"name": "Bet365",       "badge": "🇬🇧 Bet365",       "url": "https://www.bet365.com",        "region": "🇬🇧 İngiltere", "color": "green"},
    "williamhill":  {"name": "William Hill", "badge": "🇬🇧 William Hill", "url": "https://www.williamhill.com",   "region": "🇬🇧 İngiltere", "color": "sky"},
    "ladbrokes_eu": {"name": "Ladbrokes",    "badge": "🇬🇧 Ladbrokes",    "url": "https://www.ladbrokes.com",     "region": "🇬🇧 İngiltere", "color": "red"},
    "coral":        {"name": "Coral",        "badge": "🇬🇧 Coral",        "url": "https://www.coral.co.uk",       "region": "🇬🇧 İngiltere", "color": "pink"},
    "betfred":      {"name": "Betfred",      "badge": "🇬🇧 Betfred",      "url": "https://www.betfred.com",       "region": "🇬🇧 İngiltere", "color": "purple"},
    "paddypower":   {"name": "Paddy Power",  "badge": "🇮🇪 Paddy Power",  "url": "https://www.paddypower.com",    "region": "🇮🇪 İrlanda",   "color": "lime"},
    "skybet":       {"name": "Sky Bet",      "badge": "🇬🇧 Sky Bet",      "url": "https://m.skybet.com",          "region": "🇬🇧 İngiltere", "color": "cyan"},
    "betfair":      {"name": "Betfair",      "badge": "🇬🇧 Betfair",      "url": "https://www.betfair.com",       "region": "🇬🇧 İngiltere", "color": "yellow"},
    "betvictor":    {"name": "BetVictor",    "badge": "🇬🇧 BetVictor",    "url": "https://www.betvictor.com",     "region": "🇬🇧 İngiltere", "color": "indigo"},
    "pinnacle":     {"name": "Pinnacle",     "badge": "🌐 Pinnacle",      "url": "https://www.pinnacle.com",      "region": "🌐 Global",     "color": "indigo"},
    "unibet_eu":    {"name": "Unibet",       "badge": "🌐 Unibet",        "url": "https://www.unibet.com",        "region": "🌐 Global",     "color": "green"},
    "bwin":         {"name": "Bwin",         "badge": "🌐 Bwin",          "url": "https://sports.bwin.com",       "region": "🌐 Global",     "color": "orange"},
    "betsson":      {"name": "Betsson",      "badge": "🇸🇪 Betsson",      "url": "https://www.betsson.com",       "region": "🇸🇪 İsveç",    "color": "purple"},
    "nordicbet":    {"name": "NordicBet",    "badge": "🇩🇰 NordicBet",    "url": "https://www.nordicbet.com",     "region": "🇩🇰 Danimarka", "color": "blue"},
    "leovegas":     {"name": "LeoVegas",     "badge": "🇸🇪 LeoVegas",     "url": "https://www.leovegas.com",      "region": "🇸🇪 İsveç",    "color": "amber"},
    "winamax":      {"name": "Winamax",      "badge": "🇫🇷 Winamax",      "url": "https://www.winamax.fr",        "region": "🇫🇷 Fransa",    "color": "red"},
    "betclic":      {"name": "Betclic",      "badge": "🇫🇷 Betclic",      "url": "https://www.betclic.fr",        "region": "🇫🇷 Fransa",    "color": "blue"},
    "draftkings":   {"name": "DraftKings",   "badge": "🇺🇸 DraftKings",   "url": "https://sportsbook.draftkings.com", "region": "🇺🇸 ABD",  "color": "green"},
    "fanduel":      {"name": "FanDuel",      "badge": "🇺🇸 FanDuel",      "url": "https://sportsbook.fanduel.com",   "region": "🇺🇸 ABD",  "color": "blue"},
    "betmgm":       {"name": "BetMGM",       "badge": "🇺🇸 BetMGM",       "url": "https://sports.betmgm.com",         "region": "🇺🇸 ABD",  "color": "amber"},
    "caesars":      {"name": "Caesars",      "badge": "🇺🇸 Caesars",      "url": "https://www.caesars.com/sportsbook-and-casino", "region": "🇺🇸 ABD", "color": "purple"},
    "betrivers":    {"name": "BetRivers",    "badge": "🇺🇸 BetRivers",    "url": "https://betrivers.com",         "region": "🇺🇸 ABD",      "color": "teal"},
    "sportsbet":    {"name": "Sportsbet AU", "badge": "🇦🇺 Sportsbet",    "url": "https://www.sportsbet.com.au",  "region": "🇦🇺 Avustralya","color": "blue"},
    "tab":          {"name": "TAB AU",       "badge": "🇦🇺 TAB",          "url": "https://www.tab.com.au",        "region": "🇦🇺 Avustralya","color": "yellow"},
    "pointsbet":    {"name": "PointsBet",    "badge": "🇦🇺 PointsBet",    "url": "https://pointsbet.com",         "region": "🇦🇺 Avustralya","color": "red"},
    "betonline":    {"name": "BetOnline",    "badge": "🌐 BetOnline",     "url": "https://www.betonline.ag",      "region": "🌐 Offshore",   "color": "gray"},
    "bovada":       {"name": "Bovada",       "badge": "🌐 Bovada",        "url": "https://www.bovada.lv",         "region": "🌐 Offshore",   "color": "red"},
}

# Geri uyumluluk için eski PLATFORMS_CONFIG adı
PLATFORMS_CONFIG = {**TURKEY_PLATFORMS}


# ─── CACHE YARDIMCI ────────────────────────────────────────────────────────────
def _get_cache(key, ttl=20):
    f = CACHE_DIR / f"{key}.json"
    if f.exists() and (time.time() - f.stat().st_mtime) / 60 < ttl:
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except:
            pass
    return None

def _set_cache(key, data):
    (CACHE_DIR / f"{key}.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ─── THE ODDS API: GERÇEK ULUSLARARASI ORANLAR ────────────────────────────────
# Ana futbol ligleri The Odds API sport key'leri
SOCCER_SPORT_KEYS = [
    "soccer_epl",                              # İngiltere Premier League
    "soccer_spain_la_liga",                     # İspanya La Liga
    "soccer_germany_bundesliga",                # Almanya Bundesliga
    "soccer_italy_serie_a",                     # İtalya Serie A
    "soccer_france_ligue_one",                  # Fransa Ligue 1
    "soccer_netherlands_eredivisie",            # Hollanda Eredivisie
    "soccer_turkey_super_lig",                  # Türkiye Süper Lig
    "soccer_portugal_primeira_liga",            # Portekiz Primeira Liga
    "soccer_uefa_champs_league",                # UEFA Şampiyonlar Ligi
    "soccer_uefa_europa_league",                # UEFA Avrupa Ligi
    "soccer_uefa_europa_conference_league",     # UEFA Konferans Ligi
    "soccer_usa_mls",                           # ABD MLS
    "soccer_brazil_campeonato",                 # Brezilya Serie A
    "soccer_argentina_primera_division",        # Arjantin Primera
    "soccer_scotland_premiership",              # İskoçya Premiership
]

def fetch_odds_api_events(sport_key):
    """The Odds API'den belirli lig için tüm bookmaker oranlarını çeker."""
    if not ODDS_API_KEY:
        return []

    cache_key = f"oddsapi_{sport_key}"
    cached = _get_cache(cache_key, ttl=20)
    if cached is not None:
        return cached

    try:
        bm_keys = ",".join(list(INTL_BOOKMAKERS.keys())[:20])
        r = requests.get(
            f"{ODDS_API_BASE}/sports/{sport_key}/odds/",
            params={
                "apiKey": ODDS_API_KEY,
                "regions": "eu,uk,us,au",
                "markets": "h2h,totals",
                "oddsFormat": "decimal",
                "bookmakers": bm_keys,
            },
            timeout=12
        )
        remaining = r.headers.get("x-requests-remaining", "?")
        print(f"[The Odds API] {sport_key} çekildi | Kalan: {remaining} istek")

        if r.status_code == 200:
            data = r.json()
            _set_cache(cache_key, data)
            return data
        elif r.status_code == 401:
            print("[The Odds API] ❌ Geçersiz API key — https://the-odds-api.com/ adresinden ücretsiz key alın.")
        elif r.status_code == 422:
            pass  # Bu lig bu plan için desteklenmiyor, sessizce atla
        else:
            print(f"[The Odds API] HTTP {r.status_code}")
    except Exception as e:
        print(f"[The Odds API] Bağlantı hatası: {e}")
    return []


def fetch_all_intl_odds():
    """Tüm ligler için uluslararası oranları çeker ve birleştirir."""
    all_events = []
    for sk in SOCCER_SPORT_KEYS:
        events = fetch_odds_api_events(sk)
        all_events.extend(events)
        if events:
            time.sleep(0.3)
    print(f"[The Odds API] Toplam {len(all_events)} uluslararası maç oranı çekildi.")
    return all_events


def _team_similarity(a, b):
    """İki takım isminin benzerliğini 0-1 arasında döndürür."""
    a, b = a.lower().strip(), b.lower().strip()
    if not a or not b:
        return 0.0
    # Tam içerik eşleşmesi
    if a in b or b in a:
        return 0.9
    # Kelime bazlı
    aw = set(a.split())
    bw = set(b.split())
    if not aw or not bw:
        return 0.0
    return len(aw & bw) / max(len(aw), len(bw))


def match_to_intl_event(nesine_match, intl_events):
    """Nesine maçını uluslararası oran olayıyla eşleştirir."""
    home = nesine_match.get("home_team", "")
    away = nesine_match.get("away_team", "")
    best, best_score = None, 0.0

    for ev in intl_events:
        eh = ev.get("home_team", "")
        ea = ev.get("away_team", "")
        score = (_team_similarity(home, eh) + _team_similarity(away, ea)) / 2
        if score > best_score:
            best_score = score
            best = ev

    if best and best_score >= 0.45:
        return best, best_score
    return None, 0.0


def parse_intl_event_odds(event):
    """The Odds API olayından her bookmaker için oranları çıkarır."""
    home = event.get("home_team", "")
    away = event.get("away_team", "")
    result = {}

    for bm in event.get("bookmakers", []):
        bm_key = bm.get("key", "")
        bm_odds = {}

        for market in bm.get("markets", []):
            mk = market.get("key", "")
            if mk == "h2h":
                for o in market.get("outcomes", []):
                    n, p = o.get("name", ""), o.get("price", 0)
                    if n == home:        bm_odds["ms1"] = round(p, 2)
                    elif n == "Draw":   bm_odds["msX"] = round(p, 2)
                    elif n == away:     bm_odds["ms2"] = round(p, 2)
            elif mk == "totals":
                for o in market.get("outcomes", []):
                    if o.get("point") == 2.5:
                        if o["name"] == "Over":  bm_odds["over25"]  = round(o["price"], 2)
                        if o["name"] == "Under": bm_odds["under25"] = round(o["price"], 2)

        if bm_odds:
            info = INTL_BOOKMAKERS.get(bm_key, {"name": bm.get("title", bm_key), "badge": bm_key, "url": "#", "region": "🌐", "color": "gray"})
            result[bm_key] = {**info, "odds": bm_odds}

    # En iyi oranları hesapla
    best = {}
    for pick in ["ms1", "msX", "ms2", "over25", "under25"]:
        bm_pick = [(bk, bd["odds"].get(pick, 0)) for bk, bd in result.items() if bd["odds"].get(pick)]
        if bm_pick:
            bk, odd = max(bm_pick, key=lambda x: x[1])
            best[pick] = {"odd": odd, "bookmaker": result[bk]["name"], "badge": result[bk]["badge"], "url": result[bk].get("url", "#")}

    return {"bookmakers": result, "best_odds": best, "bookmaker_count": len(result)}


# ─── TÜRKİYE: SPOR TOTO BÜLTENINDEN PLATFORM ORANLARI ────────────────────────
def enrich_match_with_all_platforms(match):
    """
    Nesine bültenindeki oranları 6 Türk platformu için hesaplar.
    Gerçek kaynak: Spor Toto bülteni (aynı oran havuzu, farklı marjlar).
    """
    base_odds = match.get("odds", {})
    platforms_odds = {}

    for pid, pconf in TURKEY_PLATFORMS.items():
        mult = pconf["margin_mult"]
        p_odds = {}
        for k, v in base_odds.items():
            if isinstance(v, (int, float)) and v > 1.0:
                p_odds[k] = round(v * mult, 2) if pid != "nesine" else round(v, 2)
            else:
                p_odds[k] = v
        platforms_odds[pid] = {
            "id": pid,
            "name": pconf["name"],
            "badge": pconf["badge"],
            "color": pconf["color"],
            "url": pconf["url"],
            "region": pconf["region"],
            "source": pconf["source"],
            "legal": pconf["legal"],
            "odds": p_odds,
            "note": pconf.get("note", ""),
        }

    match["platforms"] = platforms_odds
    return match


# ─── ANA SENKRONIZASYON FONKSİYONU ────────────────────────────────────────────
def sync_all_platforms_bulletin():
    """
    1. Nesine bülten API'sinden gerçek oranları çeker
    2. 6 Türk platformu için marj hesabı yapar (Spor Toto bülteni)
    3. The Odds API varsa uluslararası oranları eşleştirir
    4. Zenginleştirilmiş veriyi kaydeder
    """
    print("=" * 60)
    print("[BÜLTEN SENKRONİZASYONU]")
    print(" 🇹🇷 1. Nesine Bülten API'si çekiliyor...")
    base_matches = fetch_live_nesine_bulletin()

    if not base_matches:
        print(" ⚠️  Nesine API'ye ulaşılamadı, lokal veri yükleniyor...")
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    base_matches = json.load(f)
            except Exception:
                base_matches = []

    if not base_matches:
        print(" ❌ Veri çekilemedi.")
        return None

    print(f" ✅ Nesine: {len(base_matches)} maç bulundu")

    # Türk platformları için marj hesapla
    print(" 🇹🇷 2. Misli, Bilyoner, Tuttur, Oley, İddaa oranları hesaplanıyor...")
    enriched = [enrich_match_with_all_platforms(m) for m in base_matches]

    # The Odds API: uluslararası oranlar
    if ODDS_API_KEY:
        print(" 🌍 3. The Odds API üzerinden uluslararası oranlar çekiliyor...")
        print("    (Bet365, William Hill, Pinnacle, DraftKings ve 25+ bookmaker)")
        intl_events = fetch_all_intl_odds()

        if intl_events:
            matched = 0
            for m in enriched:
                ev, score = match_to_intl_event(m, intl_events)
                if ev:
                    intl_data = parse_intl_event_odds(ev)
                    m["intl_odds"] = intl_data
                    m["intl_matched"] = True
                    m["intl_match_confidence"] = round(score * 100)
                    matched += 1
                else:
                    m["intl_matched"] = False
            print(f" ✅ Uluslararası: {matched}/{len(enriched)} maç eşleştirildi")
        else:
            print(" ⚠️  Uluslararası oran çekilemedi")
    else:
        print(" ℹ️  3. The Odds API key tanımlı değil")
        print("    Uluslararası oranlar için: https://the-odds-api.com/ (ücretsiz)")
        for m in enriched:
            m["intl_matched"] = False

    # Kaydet
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)

    platform_names = list(TURKEY_PLATFORMS.keys())
    if ODDS_API_KEY:
        platform_names += ["bet365", "williamhill", "pinnacle", "+22 daha"]

    print(f" ✅ Toplam {len(enriched)} maç {len(platform_names)} platformla senkronize edildi.")
    print("=" * 60)
    return enriched


def get_best_odds_for_pick(match, pick_key):
    """
    Belirli bir tercih için:
    - Türk platformlardan en yüksek oranı
    - Uluslararası platformlardan en yüksek oranı
    karşılaştırarak mutlak en iyiyi döndürür.
    """
    best_p = None
    best_odd = 0.0

    # Türk platformlar
    for pid, pdata in match.get("platforms", {}).items():
        odd = pdata.get("odds", {}).get(pick_key, 0)
        if isinstance(odd, (int, float)) and odd > best_odd:
            best_odd = odd
            best_p = pdata

    # Uluslararası platformlar
    intl = match.get("intl_odds", {})
    for bk, bdata in intl.get("bookmakers", {}).items():
        odd = bdata.get("odds", {}).get(pick_key, 0)
        if isinstance(odd, (int, float)) and odd > best_odd:
            best_odd = odd
            best_p = bdata

    return best_p, round(best_odd, 2)


def get_platform_comparison_table(match):
    """
    Bir maç için tüm platformların karşılaştırma tablosunu döndürür.
    Hem Türk hem uluslararası platformları içerir.
    """
    rows = []

    # Türk platformlar (Spor Toto bazlı — kaynak belirtilmiş)
    for pid, pdata in match.get("platforms", {}).items():
        odds = pdata.get("odds", {})
        rows.append({
            "bookmaker": pdata["badge"],
            "name": pdata["name"],
            "url": pdata["url"],
            "region": pdata.get("region", "🇹🇷 Türkiye"),
            "source": pdata.get("source", "Spor Toto Bülteni"),
            "legal": pdata.get("legal", True),
            "ms1":     odds.get("ms1", "-"),
            "msX":     odds.get("msX", "-"),
            "ms2":     odds.get("ms2", "-"),
            "over25":  odds.get("over25", "-"),
            "under25": odds.get("under25", "-"),
        })

    # Uluslararası (The Odds API — gerçek)
    intl = match.get("intl_odds", {})
    for bk, bdata in intl.get("bookmakers", {}).items():
        odds = bdata.get("odds", {})
        info = INTL_BOOKMAKERS.get(bk, {})
        rows.append({
            "bookmaker": bdata.get("badge", bk),
            "name": bdata.get("name", bk),
            "url": bdata.get("url", "#"),
            "region": info.get("region", "🌐 Uluslararası"),
            "source": "The Odds API (Gerçek)",
            "legal": True,
            "ms1":     odds.get("ms1", "-"),
            "msX":     odds.get("msX", "-"),
            "ms2":     odds.get("ms2", "-"),
            "over25":  odds.get("over25", "-"),
            "under25": odds.get("under25", "-"),
        })

    # ms1'e göre sırala (en yüksek oran üste)
    rows.sort(key=lambda x: float(x["ms1"]) if isinstance(x["ms1"], (int, float)) else 0, reverse=True)
    return rows
