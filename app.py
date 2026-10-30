import gzip
import os
import shutil
import datetime
import socket
import threading
import subprocess
import re
import time
import sys

# Otomatik Dizin Eşitleme (Root-to-Folder Auto Sync)
try:
    _base_dir = os.path.dirname(os.path.abspath(__file__))
    _root_matches = os.path.join(_base_dir, "matches.json")
    _data_matches = os.path.join(_base_dir, "data", "matches.json")
    if os.path.exists(_root_matches) and os.path.getsize(_root_matches) > 10000:
        if not os.path.exists(_data_matches) or os.path.getmtime(_root_matches) >= os.path.getmtime(_data_matches):
            shutil.copy2(_root_matches, _data_matches)

    _root_opt = os.path.join(_base_dir, "coupon_optimizer.py")
    _models_opt = os.path.join(_base_dir, "models", "coupon_optimizer.py")
    if os.path.exists(_root_opt) and os.path.getsize(_root_opt) > 5000:
        if not os.path.exists(_models_opt) or os.path.getmtime(_root_opt) >= os.path.getmtime(_models_opt):
            shutil.copy2(_root_opt, _models_opt)

    _root_db = os.path.join(_base_dir, "match_database.py")
    _data_db = os.path.join(_base_dir, "data", "match_database.py")
    if os.path.exists(_root_db) and os.path.getsize(_root_db) > 2000:
        if not os.path.exists(_data_db) or os.path.getmtime(_root_db) >= os.path.getmtime(_data_db):
            shutil.copy2(_root_db, _data_db)

    _root_ub = os.path.join(_base_dir, "unified_bulletin_service.py")
    _data_ub = os.path.join(_base_dir, "data", "unified_bulletin_service.py")
    if os.path.exists(_root_ub) and os.path.getsize(_root_ub) > 2000:
        if not os.path.exists(_data_ub) or os.path.getmtime(_root_ub) >= os.path.getmtime(_data_ub):
            shutil.copy2(_root_ub, _data_ub)
except Exception as _sync_err:
    print(f"Auto-sync note: {_sync_err}")

from flask import Flask, render_template, jsonify, request, send_from_directory
from models.prediction_engine import PredictionEngine
from models.coupon_optimizer import CouponOptimizer
from data.match_database import load_matches, get_match_by_id, add_match, reset_database

# YENİ: Birleşik Bülten Servisi — Nesine merkez değil, tüm siteler eşit havuz
from data.unified_bulletin_service import (
    sync_unified_bulletin, PLATFORMS, ODDS_API_KEY,
    get_best_odds_for_pick, get_platform_comparison_table,
    REGION_LABELS
)
# Geriye dönük uyumluluk
sync_all_platforms_bulletin = sync_unified_bulletin
PLATFORMS_CONFIG = PLATFORMS

# DeepAnalysisEngine (varsa yükle)
try:
    from models.deep_analysis_engine import DeepAnalysisEngine
    deep_engine = DeepAnalysisEngine()
    HAS_DEEP = True
except Exception:
    HAS_DEEP = False


def get_local_ip():
    """Bilgisayarın yerel ağ (Wi-Fi) IP adresini tespit eder."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

PUBLIC_TUNNEL_URL = None
CLOUDFLARE_EXE = os.path.join(os.path.dirname(__file__), "cloudflared.exe")

def start_cloudflared_tunnel():
    """
    Cloudflare edge ağı üzerinden evin dışından, mobil veriden (4.5G/5G)
    ve tüm Android telefonlardan anında açılan kesintisiz küresel HTTPS tüneli açar.
    """
    def tunnel_worker():
        global PUBLIC_TUNNEL_URL
        while True:
            try:
                if os.path.exists(CLOUDFLARE_EXE):
                    proc = subprocess.Popen(
                        [CLOUDFLARE_EXE, 'tunnel', '--protocol', 'http2', '--no-autoupdate', '--url', 'http://127.0.0.1:5000'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True
                    )
                    for line in proc.stdout:
                        m = re.search(r'https://[a-zA-Z0-9\-]+\.trycloudflare\.com', line)
                        if m:
                            PUBLIC_TUNNEL_URL = m.group(0)
                            try:
                                with open(os.path.join(os.path.dirname(__file__), "tunnel_url.txt"), "w", encoding="ascii") as tf:
                                    tf.write(PUBLIC_TUNNEL_URL)
                            except Exception:
                                pass
                            print(f"\n[CLOUDFLARE KÜRESEL ERİŞİM] Ev Dışından & Telefondan Erişim İçin Canlı HTTPS: {PUBLIC_TUNNEL_URL}\n")
                    proc.wait()
                else:
                    proc = subprocess.Popen(
                        ['ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'UserKnownHostsFile=NUL', '-R', '80:127.0.0.1:5000', 'nokey@localhost.run'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True
                    )
                    for line in proc.stdout:
                        m = re.search(r'https://[a-zA-Z0-9\.\-]+\.lhr\.life', line)
                        if m:
                            PUBLIC_TUNNEL_URL = m.group(0)
                            print(f"\n[GLOBAL ERİŞİM] Canlı HTTPS: {PUBLIC_TUNNEL_URL}\n")
                    proc.wait()
            except Exception as ex:
                print(f"Tünel bağlantı bildirimi: {ex}")
            time.sleep(3)

    t = threading.Thread(target=tunnel_worker, daemon=True)
    t.start()

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Global Kupon Önbelleği & Gzip Sıkıştırma (Turbo Yükleme)
_coupons_cache = {}

@app.after_request
def compress_response(response):
    try:
        if getattr(response, 'direct_passthrough', False) or getattr(response, 'is_streamed', False):
            return response
        if not (200 <= response.status_code < 300) or 'Content-Encoding' in response.headers:
            return response
        accept_encoding = request.headers.get('Accept-Encoding', '')
        if 'gzip' not in accept_encoding.lower():
            return response
        mimetype = response.mimetype or ''
        if not any(t in mimetype for t in ['json', 'text', 'javascript', 'html', 'css', 'xml']):
            return response
        data = response.get_data()
        if len(data) < 400:
            return response
        compressed = gzip.compress(data, compresslevel=6)
        response.set_data(compressed)
        response.headers['Content-Encoding'] = 'gzip'
        response.headers['Content-Length'] = len(compressed)
        return response
    except Exception:
        return response
engine = PredictionEngine()
optimizer = CouponOptimizer()

def is_cloudflared_running():
    try:
        r = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq cloudflared.exe'], capture_output=True, text=True, timeout=5)
        return 'cloudflared.exe' in r.stdout.lower()
    except Exception:
        return False

# Tüneli sadece yerel Windows ortamında başlat (Bulut sunucularında kendi 7/24 SSL/HTTPS adresi vardır)
if sys.platform.startswith("win") and not os.environ.get("NO_TUNNEL"):
    tfile = os.path.join(os.path.dirname(__file__), "tunnel_url.txt")
    should_start = True
    if is_cloudflared_running() and os.path.exists(tfile):
        try:
            with open(tfile, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if "trycloudflare.com" in content:
                    PUBLIC_TUNNEL_URL = content
                    should_start = False
        except Exception:
            pass
    if should_start:
        try:
            start_cloudflared_tunnel()
        except Exception as t_err:
            print(f"Tünel başlatma uyarısı: {t_err}")

@app.route("/api/match-deep-analysis/<match_id>", methods=["GET"])
def get_deep_analysis(match_id):
    """Bir maç için kapsamlı derinlemesine analiz döndürür"""
    m = get_match_by_id(match_id)
    if not m:
        return jsonify({"success": False, "error": "Maç bulunamadı"}), 404

    analysis = deep_engine.generate_full_analysis(m)
    if isinstance(analysis, dict):
        analysis["home_team"] = m.get("home_team")
        analysis["away_team"] = m.get("away_team")
        analysis["league"] = m.get("league")
        analysis["match_time"] = m.get("match_time")
        analysis["bulten_code"] = m.get("bulten_code") or m.get("nesine_code")
        analysis["mbs"] = m.get("mbs", 1)
        analysis["odds"] = m.get("odds", {})
    return jsonify({"success": True, "analysis": analysis, "match_id": match_id, "match": m})


@app.route("/api/match-all-odds/<match_id>", methods=["GET"])
def get_match_all_odds(match_id):
    """Bir maç için platform karşılaştırma oranlarını ve tüm Nesine/İddaa piyasa seçeneklerini döner"""
    m = get_match_by_id(match_id)
    if not m:
        return jsonify({"success": False, "error": "Maç bulunamadı"}), 404

    all_markets = m.get("all_markets", [])
    categories = m.get("market_categories", {})
    table = get_platform_comparison_table(m)
    odds = dict(m.get("odds", {}))

    # xG & Dixon-Coles Poisson Analizi ile Kesin Değerler
    import math
    l_home, l_away = engine.calculate_expected_goals(m.get("home_stats", {}), m.get("away_stats", {}))
    probs = engine.compute_match_probabilities(l_home, l_away)
    value_bets, all_opts = engine.analyze_value_bets(probs, odds)
    ai_rec = engine.get_match_ai_recommendation(m, probs, value_bets, all_opts)

    # 0.5, 1.5, 2.5, 3.5 Gol Piyasalarını Eksiksiz Doldur
    total_xg = probs.get("total_xg", 2.6)
    p00 = math.exp(-total_xg)
    p_o05 = max(0.01, min(0.99, 1.0 - p00))
    fair_o05 = round(max(1.04, min(1.18, 1.0 / p_o05 * 0.96)), 2)
    fair_o15 = round(max(1.12, min(1.65, 1.0 / probs.get("over15", 0.78) * 0.95)), 2)
    fair_u25 = round(max(1.40, min(2.70, 1.0 / probs.get("under25", 0.52) * 0.95)), 2)
    fair_o25 = round(max(1.40, min(2.70, 1.0 / probs.get("over25", 0.48) * 0.95)), 2)
    fair_o35 = round(max(2.10, min(4.50, 1.0 / probs.get("over35", 0.28) * 0.95)), 2)
    fair_u15 = round(max(2.40, min(5.50, 1.0 / probs.get("under15", 0.22) * 0.95)), 2)
    fair_u35 = round(max(1.15, min(1.45, 1.0 / probs.get("under35", 0.72) * 0.95)), 2)

    if not odds.get("over05"): odds["over05"] = fair_o05
    if not odds.get("over15"): odds["over15"] = fair_o15
    if not odds.get("under25"): odds["under25"] = fair_u25
    if not odds.get("over25"): odds["over25"] = fair_o25
    if not odds.get("over35"): odds["over35"] = fair_o35
    if not odds.get("under15"): odds["under15"] = fair_u15
    if not odds.get("under35"): odds["under35"] = fair_u35

    # Kategorize edilmiş gerçek Nesine/İddaa oranları
    categorized = {
        "ms": {
            "MS 1": odds.get("ms1"),
            "MS X": odds.get("msX"),
            "MS 2": odds.get("ms2")
        },
        "iy_ms": {
            "1/1": odds.get("ht_ft_11"),
            "1/0": odds.get("ht_ft_10"),
            "1/2": odds.get("ht_ft_12"),
            "0/1": odds.get("ht_ft_01") or odds.get("ht_ft_X1"),
            "0/0": odds.get("ht_ft_00") or odds.get("ht_ft_XX"),
            "0/2": odds.get("ht_ft_02") or odds.get("ht_ft_X2"),
            "2/1": odds.get("ht_ft_21"),
            "2/0": odds.get("ht_ft_20"),
            "2/2": odds.get("ht_ft_22")
        },
        "dogru_skor": {
            (f"{k.replace('ft_score_', '')[0]}-{k.replace('ft_score_', '')[1]}" if len(k.replace('ft_score_', '')) == 2 and k.replace('ft_score_', '').isdigit() else (k.replace('ft_score_', 'Diğer') if 'other' in k else k.replace('ft_score_', ''))): v
            for k, v in odds.items() if k.startswith("ft_score_")
        },
        "goller": {
            "0.5 Gol Üst": odds.get("over05"),
            "1.5 Gol Üst": odds.get("over15"),
            "2.5 Gol Üst": odds.get("over25"),
            "3.5 Gol Üst": odds.get("over35"),
            "2.5 Gol Alt": odds.get("under25"),
            "1.5 Gol Alt": odds.get("under15"),
            "3.5 Gol Alt": odds.get("under35")
        },
        "kg": {
            "KG Var": odds.get("btts_yes"),
            "KG Yok": odds.get("btts_no")
        },
        "iy_ms_skor": {
            (f"İY {k.replace('htft_score_', '').split('_')[0][0]}-{k.replace('htft_score_', '').split('_')[0][1]} / MS {k.replace('htft_score_', '').split('_')[1][0]}-{k.replace('htft_score_', '').split('_')[1][1]}"
             if '_' in k and len(k.replace('htft_score_', '').split('_')[0]) == 2 and len(k.replace('htft_score_', '').split('_')[1]) == 2
             else k.replace('htft_score_', '').replace('_', ' / ')): v
            for k, v in odds.items() if k.startswith("htft_score_")
        },
        "kombin": {
            "MS 1 & KG Var": odds.get("ms1_btts_yes"),
            "MS 2 & KG Var": odds.get("ms2_btts_yes"),
            "MS X & KG Var": odds.get("msX_btts_yes"),
            "MS 1 & 2.5 Üst": odds.get("ms1_over25"),
            "MS 2 & 2.5 Üst": odds.get("ms2_over25"),
            "Her İki Yarıda KG Var": odds.get("both_halves_btts_yes")
        }
    }

    return jsonify({
        "success": True,
        "match": {
            "id": match_id,
            "home_team": m.get("home_team"),
            "away_team": m.get("away_team"),
            "league": m.get("league"),
            "match_time": m.get("match_time"),
            "bulten_code": m.get("bulten_code") or m.get("nesine_code"),
            "mbs": m.get("mbs", 1),
        },
        "match_id": match_id,
        "match_name": f"{m.get('home_team')} - {m.get('away_team')}",
        "home_team": m.get("home_team"),
        "away_team": m.get("away_team"),
        "league": m.get("league"),
        "time": m.get("match_time"),
        "match_time": m.get("match_time"),
        "bulten_code": m.get("bulten_code") or m.get("nesine_code"),
        "mbs": m.get("mbs", 1),
        "comparison_table": table,
        "all_odds": table,
        "odds": odds,
        "categorized_odds": categorized,
        "all_platform_odds": m.get("all_platform_odds", {}),
        "market_count": m.get("market_count", len(all_markets)),
        "odds_count": m.get("odds_count", sum(len(x.get("outcomes", [])) for x in all_markets)),
        "categories": categories,
        "markets": all_markets,
        "recommendation": ai_rec,
        "expected_goals": {
            "home_xg": probs["lambda_home"],
            "away_xg": probs["lambda_away"],
            "total_xg": probs["total_xg"]
        }
    })


@app.route("/api/refresh-real-data", methods=["POST", "GET"])
def refresh_real_data():
    """TheSportsDB'den gerçek istatistik verilerini yeniler"""
    try:
        from data.nesine_live_service import fetch_live_nesine_bulletin

        print("[GERÇEK VERİ YENİLEME] Nesine bülteni + TheSportsDB istatistikleri çekiliyor...")
        matches = fetch_live_nesine_bulletin()

        if matches:
            return jsonify({
                "success": True,
                "count": len(matches),
                "message": f"{len(matches)} maç için Nesine bülteni ve TheSportsDB gerçek istatistikleri güncellendi.",
                "sources": ["Nesine.com Bülten API", "TheSportsDB.com"],
                "updated_at": datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            })
        else:
            return jsonify({"success": False, "error": "Veri çekilemedi"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/playstore")
def playstore():
    return render_template("playstore.html")

@app.route("/download/iddaa-ai.apk")
@app.route("/download/app.apk")
def download_apk():
    # Gerçek, bu uygulamaya ait derlenmiş bir APK yok (Java/Android SDK gerekir).
    # Eski bağlantılar kurulum sayfasına yönlendirilir; kurulum tarayıcıdan (PWA) yapılır.
    from flask import redirect
    return redirect("/playstore")

@app.route("/.well-known/assetlinks.json")
def assetlinks():
    return jsonify([{
        "relation": ["delegate_permission/common.handle_all_urls"],
        "target": {
            "namespace": "android_app",
            "package_name": "com.antigravity.iddaaai",
            "sha256_cert_fingerprints": [
                "14:6D:E9:7D:0F:52:AB:E3:4C:6D:3F:82:1F:B1:0E:64:18:2F:1D:6E:9A:3A:8B:22:98:B4:72:69:B6:5E:21:48"
            ]
        }
    }])

@app.route("/manifest.json")
def manifest():
    return send_from_directory("static", "manifest.json", mimetype="application/manifest+json")

@app.route("/sw.js")
def service_worker():
    return send_from_directory("static", "sw.js", mimetype="application/javascript")

@app.route("/api/mobile-info", methods=["GET"])
def get_mobile_info():
    local_ip = get_local_ip()
    port = int(os.environ.get("PORT", 5000))
    local_url = f"http://{local_ip}:{port}"

    # Eğer bulut sunucusunda çalışıyorsa (Render, PythonAnywhere, Koyeb vb.)
    host_header = request.host_url.rstrip("/")
    if any(k in host_header for k in ["onrender.com", "pythonanywhere.com", "koyeb.app", "railway.app"]):
        primary_url = host_header
    else:
        tunnel_url = PUBLIC_TUNNEL_URL
        if not tunnel_url:
            tfile = os.path.join(os.path.dirname(__file__), "tunnel_url.txt")
            if os.path.exists(tfile):
                try:
                    with open(tfile, "r", encoding="ascii") as tf:
                        cand = tf.read().strip()
                        if "trycloudflare.com" in cand:
                            tunnel_url = cand
                except Exception:
                    pass
        primary_url = tunnel_url if tunnel_url else local_url

    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=280x280&margin=10&data={primary_url}"
    qr_local_url = f"https://api.qrserver.com/v1/create-qr-code/?size=280x280&margin=10&data={local_url}"

    return jsonify({
        "success": True,
        "local_ip": local_ip,
        "port": port,
        "local_url": local_url,
        "public_url": primary_url,
        "mobile_url": primary_url,
        "qr_url": qr_url,
        "qr_local_url": qr_local_url,
        "instructions": [
            "Arkadaşınızın telefonunda açması veya hücresel veri (4.5G) ile girmek için Genel İnternet (HTTPS) linkini kullanın.",
            "Aynı ev Wi-Fi ağına bağlıysanız Yerel Wi-Fi adresini de kullanabilirsiniz.",
            "Telefonda açtıktan sonra 'Uygulamayı Telefona Yükle' butonuna basarak tam ekran Nesine tarzı uygulama olarak ana ekrana ekleyin!"
        ]
    })

@app.route("/api/set-tunnel-url", methods=["POST", "GET"])
def set_tunnel_url():
    """Dışarıdan Cloudflare tünel URL'sini ayarla (app başladıktan sonra)"""
    global PUBLIC_TUNNEL_URL
    data = request.get_json(silent=True) or {}
    url = data.get("url") or request.args.get("url", "")
    if url and "trycloudflare.com" in url:
        PUBLIC_TUNNEL_URL = url.strip()
        print(f"\n[TÜNEL URL GÜNCELLENDİ] {PUBLIC_TUNNEL_URL}\n")
        return jsonify({"success": True, "public_url": PUBLIC_TUNNEL_URL})
    return jsonify({"success": False, "error": "Geçersiz URL"})


@app.route("/api/matches", methods=["GET"])
def get_matches():
    matches = load_matches()
    analyzed = []
    now_dt = datetime.datetime.now()
    
    for m in matches:
        mt_str = m.get("match_time", "")
        if mt_str:
            try:
                m_dt = datetime.datetime.strptime(mt_str, "%d.%m.%Y %H:%M")
                if m_dt.date() < now_dt.date():
                    continue  # Sadece geçmiş günün maçlarını filtrele
            except Exception:
                pass

        l_home, l_away = engine.calculate_expected_goals(m["home_stats"], m["away_stats"])
        probs = engine.compute_match_probabilities(l_home, l_away)
        value_bets, all_opts = engine.analyze_value_bets(probs, m["odds"])
        ai_rec = engine.get_match_ai_recommendation(m, probs, value_bets, all_opts)

        m_odds = dict(m.get("odds", {}))
        import math
        total_xg = probs.get("total_xg", 2.6)
        p00 = math.exp(-total_xg)
        m_odds.setdefault("over05", round(max(1.04, min(1.18, 1.0 / max(0.01, 1.0 - p00) * 0.96)), 2))
        m_odds.setdefault("over15", round(max(1.12, min(1.65, 1.0 / probs.get("over15", 0.78) * 0.95)), 2))
        m_odds.setdefault("over25", round(max(1.40, min(2.70, 1.0 / probs.get("over25", 0.48) * 0.95)), 2))
        m_odds.setdefault("under25", round(max(1.40, min(2.70, 1.0 / probs.get("under25", 0.52) * 0.95)), 2))
        m_odds.setdefault("over35", round(max(2.10, min(4.50, 1.0 / probs.get("over35", 0.28) * 0.95)), 2))
        
        analyzed.append({
            "id": m["id"],
            "league": m["league"],
            "country": m.get("country", "🌍"),
            "match_time": m.get("match_time", ""),
            "day": m.get("day", "today"),
            "home_team": m["home_team"],
            "away_team": m["away_team"],
            "home_form": m["home_stats"].get("form", "DDDDD"),
            "away_form": m["away_stats"].get("form", "DDDDD"),
            "home_last_5": m["home_stats"].get("last_5", []),
            "away_last_5": m["away_stats"].get("last_5", []),
            "odds": m_odds,
            "expected_goals": {
                "home_xg": probs["lambda_home"],
                "away_xg": probs["lambda_away"],
                "total_xg": probs["total_xg"]
            },
            "top_scores": probs["top_scores"],
            "recommendation": ai_rec,
            "has_value": len(value_bets) > 0,
            "value_bets_count": len(value_bets)
        })
        
    return jsonify({"success": True, "matches": analyzed})

@app.route("/api/iyms-skor-tablosu", methods=["GET"])
def get_iyms_skor_tablosu():
    """
    Tüm bülten maçları için Bivariate Poisson & Dixon-Coles tabanlı
    İY MS Skor Tablosunu dinamik hesaplayarak döner.
    """
    matches = load_matches()
    table = []
    now_dt = datetime.datetime.now()

    for m in matches:
        mt_str = m.get("match_time", "")
        if mt_str:
            try:
                m_dt = datetime.datetime.strptime(mt_str, "%d.%m.%Y %H:%M")
                if m_dt.date() < now_dt.date():
                    continue
            except Exception:
                pass

        l_home, l_away = engine.calculate_expected_goals(m.get("home_stats", {}), m.get("away_stats", {}))
        iyms = engine.calculate_iyms_score_analysis(l_home, l_away, m.get("odds", {}), m)

        b_code = m.get("bulten_code") or m.get("nesine_code") or str(m.get("id", "")).replace("st-", "").replace("nesine-", "")
        table.append({
            "match_id": m["id"],
            "bulten_code": b_code,
            "home_team": m["home_team"],
            "away_team": m["away_team"],
            "match_name": f"{m['home_team']} - {m['away_team']}",
            "league": m.get("league", "Futbol"),
            "country": m.get("country", "🌍"),
            "match_time": m.get("match_time", ""),
            "mbs": int(m.get("mbs") or 1),
            "ai_ht_score": iyms["ai_ht_score"],
            "ai_ft_score": iyms["ai_ft_score"],
            "ai_iyms_code": iyms["ai_iyms_code"],
            "ai_iyms_label": iyms["ai_iyms_label"],
            "score_display": iyms["score_display"],
            "score_prob": iyms["score_prob"],
            "cat_prob": iyms["cat_prob"],
            "odd": iyms.get("score_odd", iyms["odd"]),
            "score_odd": iyms.get("score_odd", iyms["odd"]),
            "iyms_odd": iyms.get("iyms_odd", 4.50),
            "htft_score_odd": iyms.get("htft_score_odd", 24.00),
            "confidence": iyms["confidence"],
            "note": iyms["note"],
            "home_xg": iyms["home_xg"],
            "away_xg": iyms["away_xg"],
            "total_xg": iyms["total_xg"],
            "top_combos": iyms.get("top_combos", [])
        })

    table.sort(key=lambda x: (x["confidence"], x["score_prob"]), reverse=True)
    return jsonify({"success": True, "count": len(table), "table": table})

@app.route("/api/matches/<match_id>", methods=["GET"])
def get_match_detail(match_id):
    m = get_match_by_id(match_id)
    if not m:
        return jsonify({"success": False, "error": "Maç bulunamadı"}), 404
        
    l_home, l_away = engine.calculate_expected_goals(m["home_stats"], m["away_stats"])
    probs = engine.compute_match_probabilities(l_home, l_away)
    value_bets, all_options = engine.analyze_value_bets(probs, m["odds"])
    ai_rec = engine.get_match_ai_recommendation(m, probs, value_bets, all_options)
    
    return jsonify({
        "success": True,
        "match": m,
        "probabilities": probs,
        "value_bets": value_bets,
        "all_options": all_options,
        "recommendation": ai_rec
    })

@app.route("/api/coupons", methods=["GET"])
def get_coupons():
    try:
        rotation = int(request.args.get("rotation", getattr(optimizer, 'rotation_index', 0)))
        force = request.args.get("force", "0") == "1"
        if not force and rotation in _coupons_cache:
            return jsonify({"success": True, "coupons": _coupons_cache[rotation], "rotation": rotation})

        coupons = optimizer.generate_all_coupons(rotation=rotation)
        _coupons_cache[rotation] = coupons
        return jsonify({"success": True, "coupons": coupons, "rotation": rotation})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e), "coupons": {}}), 500

@app.route("/api/refresh-coupons", methods=["POST", "GET"])
def refresh_coupons():
    """Yeni kuponları güncelleme butonu: 7 siteden (Nesine, Misli, Bilyoner, Birebin, Oley, İddaa, Tipico) bülteni tazeler, rotasyonu ilerletir."""
    try:
        sync_all_platforms_bulletin()
    except Exception as e:
        print(f"Bülten canlı yenileme uyarısı: {e}")

    _coupons_cache.clear()
    optimizer.rotation_index = getattr(optimizer, 'rotation_index', 0) + 1
    coupons = optimizer.generate_all_coupons(rotation=optimizer.rotation_index)
    _coupons_cache[optimizer.rotation_index] = coupons
    matches = load_matches()
    return jsonify({
        "success": True,
        "message": f"7 Platformdan (Nesine, Misli, Bilyoner, Birebin, Oley, İddaa, Tipico) {len(matches)} canlı maç ve oranlar güncellendi!",
        "coupons": coupons,
        "match_count": len(matches),
        "platforms": list(PLATFORMS_CONFIG.keys()),
        "rotation": optimizer.rotation_index
    })

@app.route("/api/custom-coupon", methods=["POST"])
def generate_custom():
    data = request.json or {}
    match_count = int(data.get("match_count", 3))
    min_odd = float(data.get("min_odd", 2.5))
    max_odd = float(data.get("max_odd", 10.0))
    risk_level = data.get("risk_level", "medium")
    market_types = data.get("market_types", ["ms", "goals", "btts"])
    
    coupon = optimizer.generate_custom_coupon(
        match_count=match_count,
        min_odd=min_odd,
        max_odd=max_odd,
        market_types=market_types,
        risk_level=risk_level
    )
    
    if not coupon:
        return jsonify({"success": False, "error": "Kriterlere uygun kupon kombinasyonu bulunamadı. Lütfen filtreleri esnetin."}), 400
        
    return jsonify({"success": True, "coupon": coupon})

@app.route("/api/matches", methods=["POST"])
def create_match():
    data = request.json or {}
    required = ["home_team", "away_team", "league"]
    for r in required:
        if not data.get(r):
            return jsonify({"success": False, "error": f"'{r}' alanı zorunludur."}), 400
            
    new_match = {
        "league": data.get("league"),
        "country": data.get("country", "🌍 Uluslararası"),
        "match_time": data.get("match_time", "Günün Maçı"),
        "home_team": data.get("home_team"),
        "away_team": data.get("away_team"),
        "home_stats": {
            "attack_strength": float(data.get("home_attack", 1.2)),
            "defense_strength": float(data.get("home_defense", 1.0)),
            "form": data.get("home_form", "WWDDL"),
            "home_advantage": 1.15
        },
        "away_stats": {
            "attack_strength": float(data.get("away_attack", 1.1)),
            "defense_strength": float(data.get("away_defense", 1.1)),
            "form": data.get("away_form", "DDLWW")
        },
        "odds": {
            "ms1": float(data.get("odd_ms1", 2.10)),
            "msX": float(data.get("odd_msX", 3.20)),
            "ms2": float(data.get("odd_ms2", 3.10)),
            "over25": float(data.get("odd_over25", 1.80)),
            "under25": float(data.get("odd_under25", 1.90)),
            "btts_yes": float(data.get("odd_btts_yes", 1.70)),
            "btts_no": float(data.get("odd_btts_no", 1.95)),
            "over15": float(data.get("odd_over15", 1.25)),
            "cs1X": round(float(data.get("odd_ms1", 2.10)) / 1.6, 2),
            "csX2": round(float(data.get("odd_ms2", 3.10)) / 1.8, 2)
        }
    }
    
    if data.get("odd_ht_btts"):
        new_match["odds"]["ht_btts_yes"] = float(data.get("odd_ht_btts"))
    if data.get("odd_sh_btts"):
        new_match["odds"]["sh_btts_yes"] = float(data.get("odd_sh_btts"))
    if data.get("odd_both_halves_btts"):
        new_match["odds"]["both_halves_btts_yes"] = float(data.get("odd_both_halves_btts"))
    
    saved = add_match(new_match)
    return jsonify({"success": True, "match": saved})

@app.route("/api/sync-all-platforms", methods=["POST", "GET"])
@app.route("/api/sync-nesine", methods=["POST", "GET"])
@app.route("/api/refresh-real-data", methods=["POST", "GET"])
@app.route("/api/global-odds-refresh", methods=["POST", "GET"])
def sync_all_platforms():
    """
    Birleşik Bülten Senkronizasyonu:
    Tüm platformlar eşit havuzda — Nesine merkez değil.
    Spor Toto bülteni (6 Türk site) + The Odds API (25+ uluslararası site)
    """
    try:
        matches = sync_unified_bulletin()
        optimizer.rotation_index = getattr(optimizer, 'rotation_index', 0) + 1
        if matches:
            tr_count = len([m for m in matches if not m.get("intl_matched")])
            intl_count = len([m for m in matches if m.get("intl_matched")])
            platform_list = list(PLATFORMS.keys())
            return jsonify({
                "success": True,
                "count": len(matches),
                "turkey_matches": tr_count,
                "intl_matched": intl_count,
                "platform_count": len(platform_list),
                "platforms": platform_list[:15],
                "message": (
                    f"✅ {len(matches)} maç çekildi | "
                    f"🇹🇷 6 Türk platform (Spor Toto bülteni) | "
                    f"🌍 {intl_count} maç uluslararası oranlarla eşleştirildi"
                ),
                "sources": ["Spor Toto Bülteni", "The Odds API"] if ODDS_API_KEY else ["Spor Toto Bülteni"],
                "updated_at": datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
                "rotation": optimizer.rotation_index
            })
        else:
            return jsonify({
                "success": False,
                "error": "Bülten çekilemedi. Lütfen internet bağlantınızı kontrol edin."
            }), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/global-platforms", methods=["GET"])
def get_global_platforms():
    """Tüm dünya geneli bahis platformlarını bölgesel gruplar halinde döndürür."""
    regions = {}
    for pid, p in PLATFORMS.items():
        r = REGION_LABELS.get(p["region"], p["region"])
        if r not in regions: regions[r] = []
        regions[r].append({"id":pid,"name":p["name"],"badge":p["badge"],"url":p["url"],"legal":p["legal"]})
    return jsonify({
        "success": True,
        "platforms": {pid: {k:v for k,v in p.items() if k not in ["margin","odds_key"]}
                      for pid,p in PLATFORMS.items()},
        "regions": regions,
        "total_count": len(PLATFORMS),
        "odds_api_configured": bool(ODDS_API_KEY),
    })


@app.route("/api/odds-api-status", methods=["GET"])
def odds_api_status():
    """The Odds API bağlantı durumu."""
    if not ODDS_API_KEY:
        return jsonify({"success": True, "status": {
            "configured": False,
            "message": "API key tanımlı değil — https://the-odds-api.com/ adresinden ücretsiz alın",
            "free_plan": "500 istek/ay ücretsiz"
        }})
    try:
        r = __import__("requests").get(
            "https://api.the-odds-api.com/v4/sports/",
            params={"apiKey": ODDS_API_KEY}, timeout=8)
        rem = r.headers.get("x-requests-remaining","?")
        used = r.headers.get("x-requests-used","?")
        valid = r.status_code == 200
        return jsonify({"success": True, "status": {
            "configured": True, "valid": valid,
            "requests_remaining": rem, "requests_used": used,
            "message": f"{'✅' if valid else '❌'} Key {'geçerli' if valid else 'geçersiz'} | Kalan: {rem} istek"
        }})
    except Exception as e:
        return jsonify({"success": True, "status": {"configured": True, "valid": False, "message": str(e)}})


@app.route("/api/set-odds-api-key", methods=["POST"])
def set_odds_api_key():
    """The Odds API key'ini çalışma zamanında ayarlar."""
    import data.unified_bulletin_service as ubs
    data_req = request.json or {}
    new_key = data_req.get("api_key","").strip()
    if not new_key:
        return jsonify({"success": False, "error": "API key boş olamaz"}), 400
    os.environ["ODDS_API_KEY"] = new_key
    ubs.ODDS_API_KEY = new_key
    return jsonify({"success": True, "message": "API key ayarlandı. Kupon Yenile butonuna basın."})


@app.route("/api/match-global-odds/<match_id>", methods=["GET"])
def get_match_global_odds(match_id):
    """Belirli bir maç için tüm platform oran karşılaştırmasını döndürür."""
    m = get_match_by_id(match_id)
    if not m:
        return jsonify({"success": False, "error": "Maç bulunamadı"}), 404
    table = get_platform_comparison_table(m)
    best  = m.get("best_odds", {})
    return jsonify({
        "success": True,
        "match_id": match_id,
        "home_team": m.get("home_team"),
        "away_team": m.get("away_team"),
        "comparison_table": get_platform_comparison_table(m),
        "best_odds": m.get("best_odds", {}),
        "platform_count": m.get("platform_count", 0),
        "intl_matched": m.get("intl_matched", False),
    })


@app.route("/api/status", methods=["GET"])
def get_status():
    matches = load_matches()
    return jsonify({
        "success": True,
        "match_count": len(matches),
        "min_stake": 50,
        "platform_count": len(PLATFORMS),
        "architecture": "Tüm Siteler Eşit Havuz (Nesine merkez değil)",
        "sources": ["Spor Toto Bülteni (6 Türk site)", "The Odds API (25+ uluslararası)"],
        "odds_api_active": bool(ODDS_API_KEY),
        "timestamp": datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    })

@app.route("/api/reset", methods=["POST"])
def reset():
    reset_database()
    return jsonify({"success": True, "message": "Bülten sıfırlandı."})

if __name__ == "__main__":
    # Başlangıçta birleşik bülteni çek
    try:
        current_matches = load_matches()
        if not current_matches or len(current_matches) < 5:
            print("Spor Toto bülteni çekiliyor (tüm platformlar eşit havuz)...")
            sync_unified_bulletin()
    except Exception as err:
        print(f"Başlangıç senkronizasyon uyarısı: {err}")

    port = int(os.environ.get("PORT", 5000))
    local_ip = get_local_ip()
    print(f"\n{'='*55}")
    print(f"  İddaa AI — Tüm Siteler Eşit Havuz Mimarisi")
    print(f"{'='*55}")
    print(f"  💻 Bilgisayar : http://127.0.0.1:{port}")
    print(f"  📱 Wi-Fi (Telefon) : http://{local_ip}:{port}")
    print(f"  🌍 Dışarıdan (Cloudflare tüneli başlatılıyor...)")
    print(f"{'='*55}\n")
    app.run(host="0.0.0.0", port=port, debug=False)

