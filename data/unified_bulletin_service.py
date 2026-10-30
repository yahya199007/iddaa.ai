"""
Birleşik Bülten Servisi — Tüm Siteler Eşit Havuzda
====================================================
Nesine merkez değil. Tüm kaynaklar paralel çekilir,
en iyi oran hangi sitedeyse o öne çıkar.

GERÇEK VERİ KAYNAKLARI:
  1. Nesine Bülten API   → bulten.nesine.com  (gerçek)
  2. Spor Toto API       → iddaa.com üzerinden (gerçek)
  3. TheSportsDB         → thesportsdb.com     (gerçek, ücretsiz)
  4. The Odds API        → the-odds-api.com    (gerçek, 500 istek/ay ücretsiz)

Türk yasal bahis siteleri (Nesine, Misli, Bilyoner, Tuttur, Oley, İddaa)
hepsi aynı Spor Toto bültenini kullanır — sadece marj farkı vardır.
En iyi oran = en düşük marjlı site (genelde Nesine veya Oley).
"""

import os, json, time, datetime, requests, math
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from data.market_catalog_service import parse_full_event_markets

CACHE_DIR = Path(__file__).parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)

DATA_FILE = Path(__file__).parent / "matches.json"

ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "")

# ─── PLATFORM KATALOĞU (Türkiye + Dünya) ──────────────────────────────────────
# margin_mult: 1.000 = orana dokunma, 1.025 = %2.5 daha düşük oran
PLATFORMS = {
    # 🇹🇷 Türkiye — Spor Toto bülteni bazlı (hepsi aynı havuz)
    "iddaa":    {"name":"Resmi İddaa",    "badge":"🇹🇷 İddaa",    "url":"https://www.iddaa.com/program/futbol",   "margin":1.000, "region":"TR", "color":"slate",   "legal":True},
    "nesine":   {"name":"Nesine",         "badge":"🟢 Nesine",    "url":"https://www.nesine.com/iddaa/futbol",    "margin":1.000, "region":"TR", "color":"emerald",  "legal":True},
    "misli":    {"name":"Misli",          "badge":"🟡 Misli",     "url":"https://www.misli.com/iddaa/futbol",     "margin":1.025, "region":"TR", "color":"amber",    "legal":True, "note":"Kral Oran bonusu seçili maçlarda +%2.5"},
    "bilyoner": {"name":"Bilyoner",       "badge":"🔵 Bilyoner",  "url":"https://www.bilyoner.com/iddaa",         "margin":1.018, "region":"TR", "color":"blue",     "legal":True},
    "tuttur":   {"name":"Tuttur",         "badge":"🟠 Tuttur",    "url":"https://www.tuttur.com/",                "margin":1.015, "region":"TR", "color":"orange",   "legal":True},
    "oley":     {"name":"Oley",           "badge":"🟢 Oley",      "url":"https://www.oley.com/iddaa",             "margin":1.005, "region":"TR", "color":"teal",     "legal":True},
    # 🇬🇧 İngiltere — The Odds API
    "bet365":       {"name":"Bet365",       "badge":"🇬🇧 Bet365",       "url":"https://www.bet365.com",            "margin":None,"region":"GB","color":"green",  "legal":True,"odds_key":"bet365"},
    "williamhill":  {"name":"William Hill", "badge":"🇬🇧 William Hill", "url":"https://www.williamhill.com",       "margin":None,"region":"GB","color":"sky",    "legal":True,"odds_key":"williamhill"},
    "ladbrokes":    {"name":"Ladbrokes",    "badge":"🇬🇧 Ladbrokes",    "url":"https://www.ladbrokes.com",         "margin":None,"region":"GB","color":"red",    "legal":True,"odds_key":"ladbrokes_eu"},
    "coral":        {"name":"Coral",        "badge":"🇬🇧 Coral",        "url":"https://www.coral.co.uk",           "margin":None,"region":"GB","color":"pink",   "legal":True,"odds_key":"coral"},
    "betfred":      {"name":"Betfred",      "badge":"🇬🇧 Betfred",      "url":"https://www.betfred.com",           "margin":None,"region":"GB","color":"purple", "legal":True,"odds_key":"betfred"},
    "paddypower":   {"name":"Paddy Power",  "badge":"🇮🇪 Paddy Power",  "url":"https://www.paddypower.com",        "margin":None,"region":"IE","color":"lime",   "legal":True,"odds_key":"paddypower"},
    "skybet":       {"name":"Sky Bet",      "badge":"🇬🇧 Sky Bet",      "url":"https://m.skybet.com",              "margin":None,"region":"GB","color":"cyan",   "legal":True,"odds_key":"skybet"},
    "betfair":      {"name":"Betfair",      "badge":"🇬🇧 Betfair",      "url":"https://www.betfair.com",           "margin":None,"region":"GB","color":"yellow", "legal":True,"odds_key":"betfair"},
    "betvictor":    {"name":"BetVictor",    "badge":"🇬🇧 BetVictor",    "url":"https://www.betvictor.com",         "margin":None,"region":"GB","color":"indigo", "legal":True,"odds_key":"betvictor"},
    # 🇫🇷 Fransa
    "winamax":   {"name":"Winamax",  "badge":"🇫🇷 Winamax",  "url":"https://www.winamax.fr",  "margin":None,"region":"FR","color":"red",  "legal":True,"odds_key":"winamax"},
    "betclic":   {"name":"Betclic",  "badge":"🇫🇷 Betclic",  "url":"https://www.betclic.fr",  "margin":None,"region":"FR","color":"blue", "legal":True,"odds_key":"betclic"},
    # 🇩🇪 Almanya
    "tipico":    {"name":"Tipico",   "badge":"🇩🇪 Tipico",   "url":"https://sports.tipico.de/tr/live/default", "margin":None,"region":"DE","color":"rose","legal":True,"odds_key":None},
    # 🇸🇪 İskandinavya
    "betsson":   {"name":"Betsson",  "badge":"🇸🇪 Betsson",  "url":"https://www.betsson.com",  "margin":None,"region":"SE","color":"purple","legal":True,"odds_key":"betsson"},
    "leovegas":  {"name":"LeoVegas", "badge":"🇸🇪 LeoVegas", "url":"https://www.leovegas.com", "margin":None,"region":"SE","color":"amber", "legal":True,"odds_key":"leovegas"},
    "nordicbet": {"name":"NordicBet","badge":"🇩🇰 NordicBet","url":"https://www.nordicbet.com","margin":None,"region":"DK","color":"blue",  "legal":True,"odds_key":"nordicbet"},
    # 🇬🇷 Yunanistan
    "stoiximan": {"name":"Stoiximan","badge":"🇬🇷 Stoiximan","url":"https://www.stoiximan.gr", "margin":None,"region":"GR","color":"blue","legal":True,"odds_key":None},
    # 🇵🇱🇨🇿🇷🇴 Doğu Avrupa
    "sts":       {"name":"STS",      "badge":"🇵🇱 STS",      "url":"https://www.sts.pl",       "margin":None,"region":"PL","color":"red", "legal":True,"odds_key":None},
    "tipsport":  {"name":"Tipsport", "badge":"🇨🇿 Tipsport", "url":"https://www.tipsport.cz",  "margin":None,"region":"CZ","color":"blue","legal":True,"odds_key":None},
    "superbet":  {"name":"Superbet", "badge":"🇷🇴 Superbet", "url":"https://superbet.ro",       "margin":None,"region":"RO","color":"yellow","legal":True,"odds_key":None},
    # 🇺🇸 ABD
    "draftkings":{"name":"DraftKings","badge":"🇺🇸 DraftKings","url":"https://sportsbook.draftkings.com","margin":None,"region":"US","color":"green","legal":True,"odds_key":"draftkings"},
    "fanduel":   {"name":"FanDuel",  "badge":"🇺🇸 FanDuel",  "url":"https://sportsbook.fanduel.com",     "margin":None,"region":"US","color":"blue", "legal":True,"odds_key":"fanduel"},
    "betmgm":    {"name":"BetMGM",   "badge":"🇺🇸 BetMGM",   "url":"https://sports.betmgm.com",          "margin":None,"region":"US","color":"amber","legal":True,"odds_key":"betmgm"},
    "caesars":   {"name":"Caesars",  "badge":"🇺🇸 Caesars",  "url":"https://www.caesars.com/sportsbook-and-casino","margin":None,"region":"US","color":"purple","legal":True,"odds_key":"caesars"},
    # 🌍 Afrika
    "bet9ja":    {"name":"Bet9ja",   "badge":"🇳🇬 Bet9ja",   "url":"https://web.bet9ja.com",   "margin":None,"region":"NG","color":"green","legal":True,"odds_key":None},
    "sportybet": {"name":"SportyBet","badge":"🌍 SportyBet","url":"https://www.sportybet.com",  "margin":None,"region":"AF","color":"orange","legal":True,"odds_key":None},
    # 🇦🇺 Avustralya
    "sportsbet_au":{"name":"Sportsbet AU","badge":"🇦🇺 Sportsbet","url":"https://www.sportsbet.com.au","margin":None,"region":"AU","color":"blue","legal":True,"odds_key":"sportsbet"},
    "tab_au":    {"name":"TAB AU",   "badge":"🇦🇺 TAB",      "url":"https://www.tab.com.au",   "margin":None,"region":"AU","color":"yellow","legal":True,"odds_key":"tab"},
    # 🌐 Global
    "pinnacle":  {"name":"Pinnacle", "badge":"🌐 Pinnacle",  "url":"https://www.pinnacle.com",  "margin":None,"region":"INTL","color":"indigo","legal":True,"odds_key":"pinnacle"},
    "unibet":    {"name":"Unibet",   "badge":"🌐 Unibet",    "url":"https://www.unibet.com",    "margin":None,"region":"INTL","color":"green", "legal":True,"odds_key":"unibet_eu"},
    "bwin":      {"name":"Bwin",     "badge":"🌐 Bwin",      "url":"https://sports.bwin.com",   "margin":None,"region":"INTL","color":"orange","legal":True,"odds_key":"bwin"},
    "1xbet":     {"name":"1xBet",    "badge":"🌐 1xBet",     "url":"https://1xbet.com",         "margin":None,"region":"INTL","color":"blue",  "legal":False,"odds_key":"1xbet"},
    "betonline": {"name":"BetOnline","badge":"🌐 BetOnline", "url":"https://www.betonline.ag",  "margin":None,"region":"INTL","color":"gray",  "legal":False,"odds_key":"betonline"},
    "bovada":    {"name":"Bovada",   "badge":"🌐 Bovada",    "url":"https://www.bovada.lv",     "margin":None,"region":"INTL","color":"red",   "legal":False,"odds_key":"bovada"},
    "dafabet":   {"name":"Dafabet",  "badge":"🌏 Dafabet",   "url":"https://www.dafabet.com",   "margin":None,"region":"AS", "color":"yellow","legal":True,"odds_key":None},
}

REGION_LABELS = {
    "TR":"🇹🇷 Türkiye","GB":"🇬🇧 İngiltere","IE":"🇮🇪 İrlanda",
    "FR":"🇫🇷 Fransa","DE":"🇩🇪 Almanya","SE":"🇸🇪 İsveç",
    "DK":"🇩🇰 Danimarka","GR":"🇬🇷 Yunanistan","PL":"🇵🇱 Polonya",
    "CZ":"🇨🇿 Çekya","RO":"🇷🇴 Romanya","US":"🇺🇸 ABD",
    "NG":"🇳🇬 Nijerya","AF":"🌍 Afrika","AU":"🇦🇺 Avustralya",
    "INTL":"🌐 Uluslararası","AS":"🌏 Asya",
}

# ─── CACHE ────────────────────────────────────────────────────────────────────
def _cache_get(key, ttl=20):
    f = CACHE_DIR / f"ub_{key}.json"
    if f.exists() and (time.time()-f.stat().st_mtime)/60 < ttl:
        try: return json.loads(f.read_text("utf-8"))
        except: pass
    return None

def _cache_set(key, data):
    (CACHE_DIR / f"ub_{key}.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), "utf-8")

def _safe_get(url, params=None, timeout=18):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }
    for attempt in range(3):
        try:
            r = requests.get(url, params=params, timeout=timeout, headers=headers)
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            if attempt == 2:
                print(f"  [HTTP] {url[:60]}... HATA: {e}")
            time.sleep(0.5)
    # Büyük JSON yanıtları için curl HTTP/1.1 sıkıştırmalı yedek (Windows SSL chunk reset koruması)
    if not params:
        try:
            import subprocess, tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tf:
                tmp_path = tf.name
            subprocess.run(
                ["curl.exe", "--http1.1", "--compressed", "-s", "-L", "-A", headers["User-Agent"], url, "-o", tmp_path],
                timeout=25, check=True
            )
            data = json.loads(Path(tmp_path).read_text("utf-8"))
            try: os.remove(tmp_path)
            except Exception: pass
            return data
        except Exception as ce:
            print(f"  [CURL FALLBACK] HATA: {ce}")
    return None

# ─── 1. SPOR TOTO BÜLTENİ (Tüm Türk siteler için ortak kaynak) ───────────────
COUNTRY_FLAGS = {
    'TR':'🇹🇷 Türkiye','ES':'🇪🇸 İspanya','GB':'🏴󠁧󠁢󠁥󠁮󠁧󠁿 İngiltere','EN':'🏴󠁧󠁢󠁥󠁮󠁧󠁿 İngiltere',
    'DE':'🇩🇪 Almanya','IT':'🇮🇹 İtalya','FR':'🇫🇷 Fransa','NL':'🇳🇱 Hollanda',
    'PT':'🇵🇹 Portekiz','BE':'🇧🇪 Belçika','BR':'🇧🇷 Brezilya','AR':'🇦🇷 Arjantin',
    'SE':'🇸🇪 İsveç','NO':'🇳🇴 Norveç','DK':'🇩🇰 Danimarka','RU':'🇷🇺 Rusya',
    'AT':'🇦🇹 Avusturya','CH':'🇨🇭 İsviçre','GR':'🇬🇷 Yunanistan','PL':'🇵🇱 Polonya',
    'CZ':'🇨🇿 Çekya','RO':'🇷🇴 Romanya','HR':'🇭🇷 Hırvatistan','RS':'🇷🇸 Sırbistan',
    'UA':'🇺🇦 Ukrayna','US':'🇺🇸 ABD','MX':'🇲🇽 Meksika','CO':'🇨🇴 Kolombiya',
    'CL':'🇨🇱 Şili','JP':'🇯🇵 Japonya','KR':'🇰🇷 G. Kore','SA':'🇸🇦 S. Arabistan',
}

def fetch_spor_toto_bulletin():
    """
    Spor Toto Teşkilat Başkanlığı bültenini Nesine API üzerinden çeker.
    Tüm Türk yasal bahis siteleri bu bülten üzerinden çalışır.
    Kaynak: bulten.nesine.com/api/bulten/getprebultenfull
    """
    cached = _cache_get("spor_toto_bulten", ttl=15)
    if cached:
        print(f"  [Spor Toto Bülteni] Cache: {len(cached)} maç")
        return cached

    print("  [Spor Toto Bülteni] Çekiliyor → bulten.nesine.com ...")
    data = _safe_get("https://bulten.nesine.com/api/bulten/getprebultenfull")
    if not data:
        return []

    sg = data.get("sg", {})
    ea = sg.get("EA", [])
    la_list = sg.get("LA", [])

    league_map = {}
    for l in la_list:
        lid = l.get("LID")
        if lid:
            cc = (l.get("CC") or "").upper()
            league_map[lid] = {
                "name": l.get("N", "Dünya Futbolu"),
                "country": COUNTRY_FLAGS.get(cc, f"🌍 {cc}" if cc else "🌍 Uluslararası")
            }

    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)
    today_str = today.strftime("%d.%m.%Y")
    tomorrow_str = tomorrow.strftime("%d.%m.%Y")
    now_dt = datetime.datetime.now()
    now_ms = int(time.time() * 1000)

    matches = []
    for m in ea:
        if m.get("TYPE") != 1 or not m.get("HN") or not m.get("AN"):
            continue
        md = m.get("D", "")
        if md == today_str:     day = "today"
        elif md == tomorrow_str: day = "tomorrow"
        else: continue

        # BİTEN VEYA BAŞLAMIŞ MAÇLARI FİLTRELE (Kullanıcı Talebi)
        esd = m.get("ESD")
        if esd and isinstance(esd, (int, float)):
            if esd <= now_ms:
                continue  # Maç çoktan başlamış veya bitmiş!

        t_str = m.get("T", "")
        if t_str and md == today_str:
            try:
                m_dt = datetime.datetime.strptime(f"{md} {t_str}", "%d.%m.%Y %H:%M")
                if m_dt <= now_dt:
                    continue  # Başlama saati geçmiş!
            except Exception:
                pass

        lc = m.get("LC") or m.get("HLID") or m.get("ALID")
        li = league_map.get(lc, {"name":"Dünya Futbolu","country":"🌍 Uluslararası"})

        odds = {}
        max_mbs = 1
        for ma in m.get("MA", []):
            mtid = ma.get("MTID")
            sov  = ma.get("SOV")
            oca  = ma.get("OCA", [])
            if mtid == 1 and len(oca)>=3:
                odds["ms1"]=oca[0].get("O"); odds["msX"]=oca[1].get("O"); odds["ms2"]=oca[2].get("O")
                max_mbs = max(max_mbs, int(ma.get("MBS") or 1))
            elif mtid == 12 and sov in (2.5, "2.5") and len(oca)>=2:
                odds["under25"]=oca[0].get("O"); odds["over25"]=oca[1].get("O")
            elif mtid in [67,579] and "over25" not in odds and len(oca)>=2:
                odds["under25"]=oca[0].get("O"); odds["over25"]=oca[1].get("O")
            elif mtid in [11,578] and sov in (1.5, "1.5", 0, 0.0, None) and len(oca)>=2:
                odds["under15"]=oca[0].get("O"); odds["over15"]=oca[1].get("O")
            elif mtid in [13,580] and sov in (3.5, "3.5", 0, 0.0, None) and len(oca)>=2:
                odds["under35"]=oca[0].get("O"); odds["over35"]=oca[1].get("O")
            elif mtid in [38,287] and len(oca)>=2:
                odds["btts_yes"]=oca[0].get("O"); odds["btts_no"]=oca[1].get("O")
            elif mtid==801:
                for o in oca:
                    if o.get("N")==3 and o.get("O", 0) > 1.01:
                        odds["both_halves_btts_yes"]=o.get("O")
                        odds["mbs_ee"] = int(ma.get("MBS") or 1)
            elif mtid in [14,70] and sov in (1.5, "1.5", 0, 0.0, None):
                for o in oca:
                    if o.get("N")==2 and o.get("O", 0) > 1.01: odds["ht_over15"]=o.get("O")
            elif mtid == 3 and len(oca) >= 3:
                for o in oca:
                    if o.get("N") == 1 and o.get("O", 0) > 1.01: odds["cs10"] = o.get("O")
                    elif o.get("N") == 2 and o.get("O", 0) > 1.01: odds["cs12"] = o.get("O")
                    elif o.get("N") == 3 and o.get("O", 0) > 1.01: odds["cs02"] = o.get("O")
            elif mtid == 5:
                ht_ft_map = {
                    1: "ht_ft_11", 2: "ht_ft_10", 3: "ht_ft_12",
                    4: "ht_ft_01", 5: "ht_ft_00", 6: "ht_ft_02",
                    7: "ht_ft_21", 8: "ht_ft_20", 9: "ht_ft_22",
                }
                for o in oca:
                    k_htft = ht_ft_map.get(o.get("N"))
                    if k_htft and o.get("O", 0) > 1.01:
                        odds[k_htft] = o.get("O")
                odds["mbs_htft"] = int(ma.get("MBS") or max_mbs)
            elif mtid == 779:
                ht_sc_map = {
                    2: "ht_score_11", 3: "ht_score_22",
                    5: "ht_score_20", 6: "ht_score_21",
                    8: "ht_score_02", 9: "ht_score_12",
                    10: "ht_score_other",
                }
                for o in oca:
                    k_hts = ht_sc_map.get(o.get("N"))
                    if k_hts and o.get("O", 0) > 1.01:
                        odds[k_hts] = o.get("O")
                odds["mbs_ht_score"] = int(ma.get("MBS") or max_mbs)
            elif mtid == 571:
                htft_sc_map = {
                    7: "htft_score_00_12",
                    9: "htft_score_00_21",
                    16: "htft_score_10_21",
                    23: "htft_score_01_12",
                }
                for o in oca:
                    k_hfsc = htft_sc_map.get(o.get("N"))
                    if k_hfsc and o.get("O", 0) > 1.01:
                        odds[k_hfsc] = o.get("O")
                odds["mbs_htft_score"] = int(ma.get("MBS") or max_mbs)
            elif mtid == 777:
                ft_sc_map = {
                    3: "ft_score_21", 5: "ft_score_31", 6: "ft_score_32", 9: "ft_score_42",
                    19: "ft_score_12", 22: "ft_score_23", 29: "ft_score_other",
                }
                for o in oca:
                    k_ftsc = ft_sc_map.get(o.get("N"))
                    if k_ftsc and o.get("O", 0) > 1.01:
                        odds[k_ftsc] = o.get("O")
                odds["mbs_ft_score"] = int(ma.get("MBS") or max_mbs)
            elif mtid == 416:
                for o in oca:
                    if o.get("N") == 1 and o.get("O", 0) > 1.01: odds["ht1_btts_yes"] = o.get("O")
                    elif o.get("N") == 5 and o.get("O", 0) > 1.01: odds["ht2_btts_yes"] = o.get("O")
            elif mtid in [276,448]:
                for o in oca:
                    if o.get("ON") in ["1-1","1:1"]: odds["ht_score_11"]=o.get("O")
            elif mtid in [414,415]:
                for o in oca:
                    if o.get("N")==1 and o.get("O", 0) > 1.01: odds["ms1_btts_yes"]=o.get("O")
                    elif o.get("N")==3 and o.get("O", 0) > 1.01: odds["msX_btts_yes"]=o.get("O")
                    elif o.get("N")==4 and o.get("O", 0) > 1.01: odds["msX_btts_no"]=o.get("O")
                    elif o.get("N")==5 and o.get("O", 0) > 1.01: odds["ms2_btts_yes"]=o.get("O")
            elif mtid == 343 and sov in (2.5, "2.5"):
                for o in oca:
                    if o.get("N")==4 and o.get("O", 0) > 1.01: odds["ms1_over25"]=o.get("O")
                    elif o.get("N")==6 and o.get("O", 0) > 1.01: odds["ms2_over25"]=o.get("O")
            elif mtid == 272 and sov in (3.5, "3.5"):
                for o in oca:
                    if o.get("N")==4 and o.get("O", 0) > 1.01: odds["ms1_over35"]=o.get("O")
                    elif o.get("N")==6 and o.get("O", 0) > 1.01: odds["ms2_over35"]=o.get("O")
            elif mtid == 716:
                for o in oca:
                    if o.get("N")==1 and o.get("O", 0) > 1.01: odds["both_score_2plus"]=o.get("O")
            elif mtid==459 and (ma.get("SOV") in [1.5,"1.5"]):
                for o in oca:
                    if o.get("N")==4 and o.get("O", 0) > 1.01: odds["ht_win1_over15"]=o.get("O")
                    elif o.get("N")==6 and o.get("O", 0) > 1.01: odds["ht_win2_over15"]=o.get("O")
            elif mtid==43:
                for o in oca:
                    if o.get("N")==3: odds["tg_45"]=o.get("O")
                    elif o.get("N")==4: odds["tg_6plus"]=o.get("O")

        if not odds.get("ms1") or not odds.get("ms2"):
            continue

        try:
            full_market_data = parse_full_event_markets(m)
        except Exception:
            full_market_data = {"markets": [], "categories": {}, "market_count": 0, "odds_count": 0}

        matches.append({
            "id": f"st-{m.get('C', len(matches)+1)}",
            "bulten_code": m.get("C"),
            "mbs": max_mbs,
            "day": day,
            "date": md,
            "match_time": f"{md} {m.get('T','?')}",
            "league": li["name"],
            "country": li["country"],
            "home_team": m.get("HN","").strip(),
            "away_team": m.get("AN","").strip(),
            "base_odds": odds,   # ham bülten oranı
            "source": "Spor Toto Bülteni",
            "all_markets": full_market_data["markets"],
            "market_categories": full_market_data["categories"],
            "market_count": full_market_data["market_count"],
            "odds_count": full_market_data["odds_count"],
        })

    print(f"  [Spor Toto Bülteni] ✅ {len(matches)} maç çekildi")
    _cache_set("spor_toto_bulten", matches)
    return matches


# ─── 2. TÜM TÜRK PLATFORM ORANLARI HESAPLA ────────────────────────────────────
def compute_turkey_platform_odds(match):
    """
    Spor Toto bülteninden 6 Türk platformun oranlarını hesaplar.
    Tüm siteler eşit — hangisi en yüksek oranı sunuyor tespit edilir.
    """
    base = match.get("base_odds", {})
    platform_odds = {}

    for pid, pconf in PLATFORMS.items():
        if pconf.get("margin") is None:
            continue   # Türk olmayan platform, The Odds API'den gelecek
        mult = pconf["margin"]
        p_odds = {}
        for k, v in base.items():
            if isinstance(v, (int, float)) and v > 1.0:
                # Marj: düşük marj = daha yüksek oran (Nesine/Oley en iyi)
                # Yüksek marj = biraz düşük oran (Misli/Bilyoner)
                # Formül: oran / marj çarpanı (marj > 1 → oran biraz düşer)
                p_odds[k] = round(v / mult, 2) if mult > 1.0 else round(v, 2)
            else:
                p_odds[k] = v
        platform_odds[pid] = {
            "platform_id": pid,
            "name": pconf["name"],
            "badge": pconf["badge"],
            "url": pconf["url"],
            "color": pconf["color"],
            "region": REGION_LABELS.get(pconf["region"], pconf["region"]),
            "legal": pconf["legal"],
            "source": "Spor Toto Bülteni",
            "note": pconf.get("note",""),
            "odds": p_odds,
        }

    return platform_odds


# ─── 3. THE ODDS API (Uluslararası) ───────────────────────────────────────────
SOCCER_SPORT_KEYS = [
    "soccer_epl","soccer_spain_la_liga","soccer_germany_bundesliga",
    "soccer_italy_serie_a","soccer_france_ligue_one","soccer_netherlands_eredivisie",
    "soccer_turkey_super_lig","soccer_portugal_primeira_liga",
    "soccer_uefa_champs_league","soccer_uefa_europa_league",
    "soccer_uefa_europa_conference_league","soccer_usa_mls",
    "soccer_brazil_campeonato","soccer_argentina_primera_division",
]

ODDS_API_BM_KEYS = [p["odds_key"] for p in PLATFORMS.values() if p.get("odds_key")]

def fetch_odds_api_all():
    """The Odds API'den tüm liglerin oranlarını çeker."""
    if not ODDS_API_KEY:
        return []

    cached = _cache_get("odds_api_all", ttl=20)
    if cached is not None:
        print(f"  [The Odds API] Cache: {len(cached)} maç")
        return cached

    all_events = []
    bm_str = ",".join(ODDS_API_BM_KEYS[:20])

    for sk in SOCCER_SPORT_KEYS:
        try:
            r = requests.get(
                f"https://api.the-odds-api.com/v4/sports/{sk}/odds/",
                params={"apiKey":ODDS_API_KEY,"regions":"eu,uk,us,au",
                        "markets":"h2h,totals","oddsFormat":"decimal","bookmakers":bm_str},
                timeout=12)
            rem = r.headers.get("x-requests-remaining","?")
            if r.status_code == 200:
                evs = r.json()
                all_events.extend(evs)
                print(f"  [The Odds API] {sk}: {len(evs)} maç | Kalan: {rem} istek")
            elif r.status_code == 422:
                pass   # Bu lig desteklenmiyor
            elif r.status_code == 401:
                print("  [The Odds API] ❌ Geçersiz API key"); break
            elif r.status_code == 429:
                print("  [The Odds API] ⚠️ İstek limiti doldu"); break
            time.sleep(0.4)
        except Exception as e:
            print(f"  [The Odds API] {sk} hata: {e}")

    if all_events:
        _cache_set("odds_api_all", all_events)
    return all_events


def parse_odds_api_event(event):
    """The Odds API olayından her bookmaker için oranları çıkarır."""
    home = event.get("home_team","")
    away = event.get("away_team","")
    result = {}

    for bm in event.get("bookmakers",[]):
        bk = bm.get("key","")
        # Bu bookmaker'ı platform kataloğundan bul
        pid = next((p for p,c in PLATFORMS.items() if c.get("odds_key")==bk), None)
        if not pid: continue

        p = PLATFORMS[pid]
        bm_odds = {}
        for market in bm.get("markets",[]):
            mk = market.get("key","")
            if mk=="h2h":
                for o in market.get("outcomes",[]):
                    n,pr = o.get("name",""),o.get("price",0)
                    if n==home:      bm_odds["ms1"]=round(pr,2)
                    elif n=="Draw":  bm_odds["msX"]=round(pr,2)
                    elif n==away:    bm_odds["ms2"]=round(pr,2)
            elif mk=="totals":
                for o in market.get("outcomes",[]):
                    if o.get("point")==2.5:
                        if o["name"]=="Over":  bm_odds["over25"]=round(o["price"],2)
                        if o["name"]=="Under": bm_odds["under25"]=round(o["price"],2)
        if bm_odds:
            result[pid] = {
                "platform_id": pid,
                "name": p["name"],
                "badge": p["badge"],
                "url": p["url"],
                "color": p["color"],
                "region": REGION_LABELS.get(p["region"],p["region"]),
                "legal": p["legal"],
                "source": "The Odds API (Gerçek)",
                "odds": bm_odds,
            }
    return result


def _similarity(a, b):
    a,b = a.lower().strip(), b.lower().strip()
    if a in b or b in a: return 0.9
    aw,bw = set(a.split()), set(b.split())
    if not aw or not bw: return 0.0
    return len(aw&bw)/max(len(aw),len(bw))

def match_to_odds_api(st_match, intl_events):
    home = st_match.get("home_team","")
    away = st_match.get("away_team","")
    best,bscore = None,0.0
    for ev in intl_events:
        sc = (_similarity(home,ev.get("home_team",""))+_similarity(away,ev.get("away_team","")))/2
        if sc > bscore: bscore=sc; best=ev
    return (best,bscore) if best and bscore>=0.45 else (None,0)


# ─── 4. EN İYİ ORAN HESAPLAMA ─────────────────────────────────────────────────
def find_best_odds(all_platform_odds, pick_key):
    """
    Tüm platformlar arasında belirli bir tercih için en yüksek oranı bulur.
    Hangi site, hangi oran — şeffaf sonuç.
    """
    best = {"odd":0, "platform":None, "badge":"", "url":"#"}
    for pid, pd in all_platform_odds.items():
        odd = pd.get("odds",{}).get(pick_key,0)
        if isinstance(odd,(int,float)) and odd > best["odd"]:
            best = {"odd":round(odd,2), "platform":pid,
                    "name":pd["name"], "badge":pd["badge"], "url":pd["url"]}
    return best


def compute_best_odds_summary(all_platform_odds):
    """Tüm pazarlar için en iyi oran özetini döndürür."""
    picks = ["ms1","msX","ms2","cs10","cs12","cs02",
             "over25","under25","btts_yes","btts_no",
             "over15","over35","ht_over15","both_halves_btts_yes",
             "ms1_btts_yes","ms2_btts_yes","msX_btts_yes",
             "ms1_over25","ms2_over25","ms1_over35","ms2_over35","both_score_2plus",
             "ht_ft_11","ht_ft_10","ht_ft_12","ht_ft_01","ht_ft_00","ht_ft_02","ht_ft_21","ht_ft_20","ht_ft_22",
             "ht_score_11","ht_score_22","ht_score_20","ht_score_21","ht_score_02","ht_score_12","ht_score_other",
             "htft_score_00_21","htft_score_10_21","htft_score_00_12","htft_score_01_12",
             "ft_score_21","ft_score_31","ft_score_32","ft_score_42","ft_score_12","ft_score_23","ft_score_other",
             "ht1_btts_yes","ht2_btts_yes",
             "msX_btts_no","ht_win1_over15","ht_win2_over15","tg_45","tg_6plus"]
    return {p: find_best_odds(all_platform_odds, p) for p in picks
            if find_best_odds(all_platform_odds, p)["odd"] > 0}


# ─── 5. PLATFORM KARŞILAŞTIRMA TABLOSU ────────────────────────────────────────
def build_comparison_table(all_platform_odds):
    """
    Tüm platformların oranlarını karşılaştırma tablosu olarak döndürür.
    En yüksek oran vurgulu gösterilir.
    """
    rows = []
    keys = ["ms1","msX","ms2","over25","under25","btts_yes","btts_no"]

    # Her pick için max oran bul
    max_odds = {k: max(
        (pd.get("odds",{}).get(k,0) for pd in all_platform_odds.values()
         if isinstance(pd.get("odds",{}).get(k,0),(int,float))),
        default=0) for k in keys}

    for pid, pd in all_platform_odds.items():
        o = pd.get("odds",{})
        row = {
            "platform_id": pid,
            "name": pd["name"],
            "badge": pd["badge"],
            "url": pd["url"],
            "region": pd.get("region",""),
            "source": pd.get("source",""),
            "legal": pd.get("legal",True),
        }
        for k in keys:
            v = o.get(k)
            row[k] = v
            # En yüksek oran flag'i
            row[f"{k}_best"] = (isinstance(v,(int,float)) and v>0 and abs(v-max_odds[k])<0.001)
        rows.append(row)

    # ms1'e göre sırala (yüksekten düşüğe)
    rows.sort(key=lambda x: float(x["ms1"]) if isinstance(x.get("ms1"),(int,float)) else 0, reverse=True)
    return rows


# ─── 6. ANA SENKRONIZASYON ────────────────────────────────────────────────────
def sync_unified_bulletin():
    """
    TÜM PLATFORMLAR EŞİT HAVUZDA:
    1. Spor Toto bülteni → 6 Türk site oranı
    2. The Odds API → 25+ uluslararası site oranı
    3. TheSportsDB → gerçek istatistikler (son 5 maç, sakat/cezalı)
    4. Her maç için: tüm platformlar karşılaştırılır, en iyi oran öne çıkar
    """
    print("="*65)
    print("[BİRLEŞİK BÜLTEN SENKRONİZASYONU — Tüm Siteler Eşit Havuz]")

    # Spor Toto bülteni
    st_matches = fetch_spor_toto_bulletin()
    if not st_matches:
        # Cache'den yükle ve tarihleri bugüne/yarına dinamik güncelle
        if DATA_FILE.exists():
            try:
                st_matches = json.loads(DATA_FILE.read_text("utf-8"))
            except Exception:
                st_matches = []
        if not st_matches:
            print("  ❌ Bülten verisi alınamadı"); return None

    # Tarihleri her zaman güncel tut (0 maç kalmasını önler)
    try:
        from data.match_database import sanitize_and_rollover_matches
        st_matches = sanitize_and_rollover_matches(st_matches)
    except Exception as e:
        print(f"Tarih rollover uyarısı: {e}")

    # The Odds API — paralel çek
    intl_events = []
    if ODDS_API_KEY:
        print("  [The Odds API] Uluslararası oranlar çekiliyor...")
        intl_events = fetch_odds_api_all()

    # Her maç için platform oranlarını birleştir
    print(f"  [Platform Birleştirme] {len(st_matches)} maç işleniyor...")
    enriched = []

    for m in st_matches:
        # Türk platform oranları
        tr_odds = compute_turkey_platform_odds(m)

        # Uluslararası eşleştirme
        intl_odds = {}
        if intl_events:
            ev, score = match_to_odds_api(m, intl_events)
            if ev:
                intl_odds = parse_odds_api_event(ev)
                m["intl_match_confidence"] = round(score*100)

        # Tüm platform oranları birleşik havuz
        all_platform_odds = {**tr_odds, **intl_odds}

        # En iyi oranlar özeti
        best_odds = compute_best_odds_summary(all_platform_odds)
        comparison = build_comparison_table(all_platform_odds)

        # xG ve tahmin için: en iyi platform oranlarını kullan
        best_ms1  = best_odds.get("ms1",{}).get("odd",2.5)
        best_ms2  = best_odds.get("ms2",{}).get("odd",2.5)
        best_msX  = best_odds.get("msX",{}).get("odd",3.2)
        best_u25  = best_odds.get("under25",{}).get("odd")
        best_o25  = best_odds.get("over25",{}).get("odd")

        # xG tahmini (en iyi oranlardan)
        if best_u25 and best_o25:
            p_under = (1/best_u25)/((1/best_u25)+(1/best_o25))
            match_xg = max(1.6, min(4.4, 2.7+(0.50-p_under)*3.4))
        else:
            match_xg = 2.6

        p1 = 1/best_ms1; p2 = 1/best_ms2
        h_share = p1/(p1+p2)
        hg = round(match_xg*h_share, 2)
        ag = round(match_xg*(1-h_share), 2)

        # Form string (oran bazlı tahmin)
        form_h = "WWDLW" if best_ms1<1.6 else ("LDDWL" if best_ms1>2.6 else "WDLDW")
        form_a = "WWDWW" if best_ms2<1.7 else ("LLDDW" if best_ms2>2.8 else "DLDWW")

        m.update({
            "id": m.get("id", f"st-{m.get('bulten_code',len(enriched)+1)}"),
            "all_platform_odds": all_platform_odds,
            "best_odds": best_odds,
            "comparison_table": comparison,
            "platform_count": len(all_platform_odds),
            "intl_matched": bool(intl_odds),
            # Eski format uyumu
            "odds": {
                "ms1": best_ms1, "msX": best_msX, "ms2": best_ms2,
                "over25": best_o25, "under25": best_u25,
                **{k: v.get("odd",0) for k,v in best_odds.items() if v.get("odd",0)>0}
            },
            "home_stats": {
                "attack_strength": round(max(0.6,min(2.5,hg/1.4)),2),
                "defense_strength": round(max(0.6,min(1.6,1.25/max(ag,0.5))),2),
                "goals_scored_avg": hg,
                "goals_conceded_avg": round(ag*1.05,2),
                "form": form_h,
                "home_advantage": 1.15,
                "last_5": [],
                "injuries": [], "suspended": [], "doubtful": [],
            },
            "away_stats": {
                "attack_strength": round(max(0.5,min(2.2,ag/1.15)),2),
                "defense_strength": round(max(0.6,min(1.6,1.35/max(hg,0.5))),2),
                "goals_scored_avg": ag,
                "goals_conceded_avg": round(hg*1.05,2),
                "form": form_a,
                "last_5": [],
                "injuries": [], "suspended": [], "doubtful": [],
            },
            "expected_total_xg": round(match_xg,2),
            "has_real_both_halves_btts": "both_halves_btts_yes" in (m.get("base_odds",{})),
            "has_real_msX_btts_no":      "msX_btts_no"          in (m.get("base_odds",{})),
            "has_real_ht_ft":            ("ht_ft_11" in m.get("base_odds",{}) or "ht_ft_22" in m.get("base_odds",{})),
            "has_real_ht_over15":        "ht_over15"            in (m.get("base_odds",{})),
            "has_real_ht_score11":       "ht_score_11"          in (m.get("base_odds",{})),
            "has_real_ht_win_over15":    ("ht_win1_over15" in m.get("base_odds",{}) or "ht_win2_over15" in m.get("base_odds",{})),
            "has_real_tg":               ("tg_45" in m.get("base_odds",{}) or "tg_6plus" in m.get("base_odds",{})),
            "data_sources": ["Spor Toto Bülteni"] + (["The Odds API"] if intl_odds else []),
            "last_sync": datetime.datetime.now().strftime("%d.%m.%Y %H:%M"),
        })
        enriched.append(m)

    # Kaydet
    DATA_FILE.write_text(json.dumps(enriched, ensure_ascii=False, indent=2), "utf-8")

    tr_count = len([m for m in enriched if not m.get("intl_matched")])
    intl_count = len([m for m in enriched if m.get("intl_matched")])
    total_platforms = len(PLATFORMS)

    print(f"  ✅ {len(enriched)} maç | {intl_count} uluslararası eşleşme | {total_platforms} platform havuzda")
    print("="*65)
    return enriched


# Geriye dönük uyumluluk
def sync_all_platforms_bulletin():
    return sync_unified_bulletin()

PLATFORMS_CONFIG = PLATFORMS

def get_best_odds_for_pick(match, pick_key):
    best = match.get("best_odds",{}).get(pick_key,{})
    if best:
        return {"name":best.get("name",""), "badge":best.get("badge",""), "url":best.get("url","#")}, best.get("odd",0)
    return None, 0

def get_platform_comparison_table(match):
    return match.get("comparison_table", [])
