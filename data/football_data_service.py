"""
TheSportsDB Gerçek Futbol Veri Servisi
- Ücretsiz, API key gerektirmez
- Cache mekanizması ile rate-limit koruması
- Graceful fallback: TheSportsDB bulamazsa Nesine oran verisi kullanılır
"""
import requests
import json
import os
import datetime
import time
import hashlib
from pathlib import Path

CACHE_DIR = Path(__file__).parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)

THESPORTS_BASE = "https://www.thesportsdb.com/api/v1/json/3"
OPENLIGADB_BASE = "https://api.openligadb.de"


def get_cached(key, ttl_minutes=30):
    """Cache mekanizması - aynı veriyi tekrar tekrar çekmemek için"""
    cache_file = CACHE_DIR / f"{key}.json"
    if cache_file.exists():
        age = (time.time() - cache_file.stat().st_mtime) / 60
        if age < ttl_minutes:
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
    return None


def set_cached(key, data):
    cache_file = CACHE_DIR / f"{key}.json"
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[CACHE YAZMA HATASI] {e}")


def safe_get(url, headers=None, timeout=10, params=None):
    """Güvenli HTTP GET - timeout ve hata yönetimi ile"""
    try:
        h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0'}
        if headers:
            h.update(headers)
        r = requests.get(url, headers=h, timeout=timeout, params=params)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[HATA] {url}: {e}")
    return None


def fetch_team_last5_results(team_name):
    """
    TheSportsDB'den takımın son 5 maç sonucunu gerçek olarak çeker.
    Takım adıyla arama yapar.
    Returns: list of {opp, score, date, result} veya []
    """
    cache_key = f"last5_{hashlib.md5(team_name.encode()).hexdigest()}"
    cached = get_cached(cache_key, ttl_minutes=120)
    if cached is not None:
        return cached

    # TheSportsDB'de takımı ara
    search_url = f"{THESPORTS_BASE}/searchteams.php"
    data = safe_get(search_url, params={"t": team_name})

    results = []
    if data and data.get("teams"):
        team = data["teams"][0]
        team_id = team.get("idTeam")

        if team_id:
            # Son 5 maç sonuçları
            events_url = f"{THESPORTS_BASE}/eventslast.php"
            events_data = safe_get(events_url, params={"id": team_id})

            if events_data and events_data.get("results"):
                for ev in events_data["results"][:5]:
                    home = ev.get("strHomeTeam", "")
                    away = ev.get("strAwayTeam", "")
                    score_home = ev.get("intHomeScore", "?")
                    score_away = ev.get("intAwayScore", "?")
                    date = ev.get("dateEvent", "")

                    is_home = home.lower() in team_name.lower() or team_name.lower() in home.lower()

                    if is_home:
                        score_str = f"{score_home}-{score_away}"
                        opp = away
                        try:
                            result = "W" if int(score_home) > int(score_away) else ("D" if int(score_home) == int(score_away) else "L")
                        except Exception:
                            result = "?"
                    else:
                        score_str = f"{score_away}-{score_home}"  # Takımın skoru önce
                        opp = home
                        try:
                            result = "W" if int(score_away) > int(score_home) else ("D" if int(score_away) == int(score_home) else "L")
                        except Exception:
                            result = "?"

                    results.append({
                        "opp": opp,
                        "score": score_str,
                        "date": date,
                        "result": result,
                        "is_home": is_home,
                        "btts_both": False,
                        "clean_sheet": score_away == "0" if is_home else score_home == "0",
                        "ht": "?-?",
                        "sh": "?-?"
                    })

    if results:
        set_cached(cache_key, results)
    return results


def fetch_team_injuries_suspensions(team_name):
    """
    TheSportsDB'den sakatlık/ceza bilgisi çeker.
    Returns: {"injured": [], "suspended": [], "doubtful": []}
    """
    cache_key = f"injuries_{hashlib.md5(team_name.encode()).hexdigest()}"
    cached = get_cached(cache_key, ttl_minutes=60)
    if cached is not None:
        return cached

    # TheSportsDB player search - takımın oyuncularına bak
    search_url = f"{THESPORTS_BASE}/searchteams.php"
    data = safe_get(search_url, params={"t": team_name})

    result = {"injured": [], "suspended": [], "doubtful": [], "source": "TheSportsDB"}

    if data and data.get("teams"):
        team = data["teams"][0]
        team_id = team.get("idTeam")

        if team_id:
            # Oyuncuları çek
            players_url = f"{THESPORTS_BASE}/lookup_all_players.php"
            players_data = safe_get(players_url, params={"id": team_id})

            if players_data and players_data.get("player"):
                for p in players_data["player"]:
                    status = p.get("strStatus", "").lower()
                    name = p.get("strPlayer", "")
                    position = p.get("strPosition", "")

                    if "injured" in status or "injury" in status:
                        result["injured"].append({"name": name, "position": position, "status": "Sakat"})
                    elif "suspended" in status or "banned" in status:
                        result["suspended"].append({"name": name, "position": position, "status": "Cezalı"})
                    elif "doubt" in status or "unknown" in status:
                        result["doubtful"].append({"name": name, "position": position, "status": "Şüpheli"})

    set_cached(cache_key, result)
    return result


def fetch_head_to_head(home_team, away_team):
    """
    İki takımın son 5 karşılaşmasını TheSportsDB'den çeker.
    """
    cache_key = f"h2h_{hashlib.md5((home_team + away_team).encode()).hexdigest()}"
    cached = get_cached(cache_key, ttl_minutes=180)
    if cached is not None:
        return cached

    # Home team ID'si al
    home_data = safe_get(f"{THESPORTS_BASE}/searchteams.php", params={"t": home_team})
    away_data = safe_get(f"{THESPORTS_BASE}/searchteams.php", params={"t": away_team})

    h2h = []

    if home_data and home_data.get("teams") and away_data and away_data.get("teams"):
        home_id = home_data["teams"][0].get("idTeam")
        away_id = away_data["teams"][0].get("idTeam")

        # TheSportsDB H2H endpoint
        h2h_url = f"{THESPORTS_BASE}/eventsh2h.php"
        h2h_data = safe_get(h2h_url, params={"idHomeTeam": home_id, "idAwayTeam": away_id})

        if h2h_data and h2h_data.get("results"):
            for ev in h2h_data["results"][:5]:
                h2h.append({
                    "date": ev.get("dateEvent", ""),
                    "home": ev.get("strHomeTeam", ""),
                    "away": ev.get("strAwayTeam", ""),
                    "score": f"{ev.get('intHomeScore', '?')}-{ev.get('intAwayScore', '?')}",
                    "league": ev.get("strLeague", "")
                })

    set_cached(cache_key, h2h)
    return h2h


def fetch_upcoming_events(team_name):
    """Takımın yaklaşan maçlarını çeker (fikstür yoğunluğu için)"""
    cache_key = f"upcoming_{hashlib.md5(team_name.encode()).hexdigest()}"
    cached = get_cached(cache_key, ttl_minutes=120)
    if cached is not None:
        return cached

    search_data = safe_get(f"{THESPORTS_BASE}/searchteams.php", params={"t": team_name})
    events = []

    if search_data and search_data.get("teams"):
        team_id = search_data["teams"][0].get("idTeam")
        if team_id:
            next_data = safe_get(f"{THESPORTS_BASE}/eventsnext.php", params={"id": team_id})
            if next_data and next_data.get("events"):
                for ev in next_data["events"][:3]:
                    events.append({
                        "date": ev.get("dateEvent", ""),
                        "opponent": ev.get("strAwayTeam") if ev.get("strHomeTeam", "").lower() in team_name.lower() else ev.get("strHomeTeam", ""),
                        "competition": ev.get("strLeague", "")
                    })

    set_cached(cache_key, events)
    return events


def enrich_match_with_real_data(match):
    """
    Nesine bülteninden gelen maç verisini gerçek istatistiklerle zenginleştirir.
    TheSportsDB API kullanır.
    """
    home_team = match.get("home_team", "")
    away_team = match.get("away_team", "")

    print(f"[GERÇEK VERİ] {home_team} vs {away_team} analiz ediliyor...")

    # 1. Son 5 maç sonuçları (gerçek)
    home_last5 = fetch_team_last5_results(home_team)
    away_last5 = fetch_team_last5_results(away_team)

    # 2. Sakatlık/Ceza bilgileri (gerçek)
    home_squad = fetch_team_injuries_suspensions(home_team)
    away_squad = fetch_team_injuries_suspensions(away_team)

    # 3. H2H geçmişi (gerçek)
    h2h = fetch_head_to_head(home_team, away_team)

    # 4. Fikstür yoğunluğu (yaklaşan maçlar)
    home_upcoming = fetch_upcoming_events(home_team)
    away_upcoming = fetch_upcoming_events(away_team)

    # Gerçek form analizi (son 5 maçtan)
    if home_last5:
        home_form_str = "".join([g.get("result", "?") for g in home_last5[:5]])
        home_goals_scored = []
        home_goals_conceded = []
        for g in home_last5:
            try:
                parts = g["score"].split("-")
                home_goals_scored.append(int(parts[0]))
                home_goals_conceded.append(int(parts[1]))
            except Exception:
                pass
        home_avg_scored = round(sum(home_goals_scored) / len(home_goals_scored), 2) if home_goals_scored else match["home_stats"].get("goals_scored_avg", 1.2)
        home_avg_conceded = round(sum(home_goals_conceded) / len(home_goals_conceded), 2) if home_goals_conceded else match["home_stats"].get("goals_conceded_avg", 1.1)
    else:
        home_form_str = match["home_stats"].get("form", "WDLDW")
        home_avg_scored = match["home_stats"].get("goals_scored_avg", 1.2)
        home_avg_conceded = match["home_stats"].get("goals_conceded_avg", 1.1)
        home_last5 = match["home_stats"].get("last_5", [])

    if away_last5:
        away_form_str = "".join([g.get("result", "?") for g in away_last5[:5]])
        away_goals_scored = []
        away_goals_conceded = []
        for g in away_last5:
            try:
                parts = g["score"].split("-")
                away_goals_scored.append(int(parts[0]))
                away_goals_conceded.append(int(parts[1]))
            except Exception:
                pass
        away_avg_scored = round(sum(away_goals_scored) / len(away_goals_scored), 2) if away_goals_scored else match["away_stats"].get("goals_scored_avg", 1.0)
        away_avg_conceded = round(sum(away_goals_conceded) / len(away_goals_conceded), 2) if away_goals_conceded else match["away_stats"].get("goals_conceded_avg", 1.2)
    else:
        away_form_str = match["away_stats"].get("form", "DLDWW")
        away_avg_scored = match["away_stats"].get("goals_scored_avg", 1.0)
        away_avg_conceded = match["away_stats"].get("goals_conceded_avg", 1.2)
        away_last5 = match["away_stats"].get("last_5", [])

    # Mevcut verileri gerçek verilerle güncelle
    match["home_stats"]["form"] = home_form_str
    match["home_stats"]["goals_scored_avg"] = home_avg_scored
    match["home_stats"]["goals_conceded_avg"] = home_avg_conceded
    match["home_stats"]["last_5"] = home_last5
    match["home_stats"]["injuries"] = home_squad.get("injured", [])
    match["home_stats"]["suspended"] = home_squad.get("suspended", [])
    match["home_stats"]["doubtful"] = home_squad.get("doubtful", [])
    match["home_stats"]["upcoming_fixtures"] = home_upcoming

    match["away_stats"]["form"] = away_form_str
    match["away_stats"]["goals_scored_avg"] = away_avg_scored
    match["away_stats"]["goals_conceded_avg"] = away_avg_conceded
    match["away_stats"]["last_5"] = away_last5
    match["away_stats"]["injuries"] = away_squad.get("injured", [])
    match["away_stats"]["suspended"] = away_squad.get("suspended", [])
    match["away_stats"]["doubtful"] = away_squad.get("doubtful", [])
    match["away_stats"]["upcoming_fixtures"] = away_upcoming

    match["head_to_head"] = h2h
    match["real_data_fetched"] = True
    match["real_data_timestamp"] = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")

    return match


def enrich_all_matches(matches, max_enrichment=20):
    """Tüm maçları gerçek verilerle zenginleştirir (rate limit için maksimum sınır)"""
    enriched = []
    for i, m in enumerate(matches[:max_enrichment]):
        try:
            enriched.append(enrich_match_with_real_data(m))
            if i < len(matches) - 1:
                time.sleep(0.3)  # Rate limit koruması
        except Exception as e:
            print(f"[UYARI] {m.get('home_team')} veri zenginleştirme hatası: {e}")
            enriched.append(m)

    # Eğer 20'den fazla maç varsa geri kalanları olduğu gibi ekle
    enriched.extend(matches[max_enrichment:])
    return enriched
