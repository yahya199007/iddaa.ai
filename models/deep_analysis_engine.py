"""
Derin Futbol Analiz Motoru
- Son 5 maç performansı
- Sakat/Cezalı kadro analizi
- Motivasyon faktörü
- H2H tarihsel üstünlük
- Fikstür yoğunluğu
- İç saha/deplasman performansı
"""


class DeepAnalysisEngine:

    def analyze_form(self, last5_results):
        """Son 5 maç formunu analiz eder"""
        if not last5_results:
            return {"score": 50, "trend": "Bilinmiyor", "detail": "Veri yok", "form_string": "?????",
                    "points": 0, "max_points": 0, "wins": 0, "draws": 0, "losses": 0}

        points = 0
        total = 0
        for r in last5_results:
            result = r.get("result", "?")
            if result == "W":
                points += 3
            elif result == "D":
                points += 1
            total += 3

        form_pct = round((points / total * 100) if total > 0 else 50)

        # Son 3 maç trendi
        recent = [r.get("result", "?") for r in last5_results[:3]]
        if recent.count("W") >= 2:
            trend = "📈 Yükselişte"
        elif recent.count("L") >= 2:
            trend = "📉 Düşüşte"
        else:
            trend = "➡️ Stabil"

        # Form string
        form_str = "".join([r.get("result", "?") for r in last5_results[:5]])

        return {
            "score": form_pct,
            "trend": trend,
            "form_string": form_str,
            "points": points,
            "max_points": total,
            "wins": sum(1 for r in last5_results if r.get("result") == "W"),
            "draws": sum(1 for r in last5_results if r.get("result") == "D"),
            "losses": sum(1 for r in last5_results if r.get("result") == "L"),
        }

    def analyze_squad_status(self, home_stats, away_stats):
        """Kadro durumunu analiz eder"""
        home_injured = home_stats.get("injuries", [])
        home_suspended = home_stats.get("suspended", [])
        home_doubtful = home_stats.get("doubtful", [])

        away_injured = away_stats.get("injuries", [])
        away_suspended = away_stats.get("suspended", [])
        away_doubtful = away_stats.get("doubtful", [])

        # Eksik oyuncu sayısına göre etki puanı
        home_impact = len(home_injured) * 2 + len(home_suspended) * 3 + len(home_doubtful)
        away_impact = len(away_injured) * 2 + len(away_suspended) * 3 + len(away_doubtful)

        return {
            "home": {
                "injured": home_injured,
                "suspended": home_suspended,
                "doubtful": home_doubtful,
                "total_missing": len(home_injured) + len(home_suspended),
                "impact_score": home_impact,
                "status": "⚠️ Ciddi Eksik" if home_impact >= 6 else ("🟡 Bazı Eksikler" if home_impact >= 2 else "✅ Tam Kadro")
            },
            "away": {
                "injured": away_injured,
                "suspended": away_suspended,
                "doubtful": away_doubtful,
                "total_missing": len(away_injured) + len(away_suspended),
                "impact_score": away_impact,
                "status": "⚠️ Ciddi Eksik" if away_impact >= 6 else ("🟡 Bazı Eksikler" if away_impact >= 2 else "✅ Tam Kadro")
            }
        }

    def analyze_h2h(self, h2h_records, home_team, away_team):
        """H2H geçmişini analiz eder"""
        if not h2h_records:
            return {"summary": "H2H verisi bulunamadı", "home_wins": 0, "away_wins": 0, "draws": 0, "recent": []}

        home_wins = 0
        away_wins = 0
        draws = 0

        for record in h2h_records:
            score = record.get("score", "?-?")
            home = record.get("home", "")

            try:
                parts = score.split("-")
                home_goals = int(parts[0])
                away_goals = int(parts[1])

                # Hangi takım ev sahibiydi?
                if home_team.lower() in home.lower() or home.lower() in home_team.lower():
                    if home_goals > away_goals:
                        home_wins += 1
                    elif home_goals < away_goals:
                        away_wins += 1
                    else:
                        draws += 1
                else:
                    if away_goals > home_goals:
                        home_wins += 1
                    elif away_goals < home_goals:
                        away_wins += 1
                    else:
                        draws += 1
            except Exception:
                draws += 1

        total = home_wins + away_wins + draws
        if total == 0:
            return {"summary": "H2H analiz edilemedi", "home_wins": 0, "away_wins": 0, "draws": 0, "recent": h2h_records}

        if home_wins > away_wins:
            dominant = f"✅ {home_team} üstün ({home_wins}G-{draws}B-{away_wins}M)"
        elif away_wins > home_wins:
            dominant = f"✅ {away_team} üstün ({away_wins}G-{draws}B-{home_wins}M)"
        else:
            dominant = f"⚖️ Dengeli ({home_wins}G-{draws}B-{away_wins}M)"

        return {
            "summary": dominant,
            "home_wins": home_wins,
            "away_wins": away_wins,
            "draws": draws,
            "total": total,
            "recent": h2h_records[:5]
        }

    def analyze_fixture_load(self, home_upcoming, away_upcoming):
        """Fikstür yoğunluğunu analiz eder"""
        home_load = len(home_upcoming)
        away_load = len(away_upcoming)

        home_has_euro = any(
            "champions" in e.get("competition", "").lower() or
            "europa" in e.get("competition", "").lower() or
            "conference" in e.get("competition", "").lower()
            for e in home_upcoming
        )
        away_has_euro = any(
            "champions" in e.get("competition", "").lower() or
            "europa" in e.get("competition", "").lower() or
            "conference" in e.get("competition", "").lower()
            for e in away_upcoming
        )

        return {
            "home": {
                "upcoming_count": home_load,
                "has_european": home_has_euro,
                "fatigue_risk": "🔴 Yorgunluk Riski" if home_has_euro or home_load >= 3 else ("🟡 Orta Yük" if home_load >= 2 else "🟢 Dinç"),
                "upcoming": home_upcoming
            },
            "away": {
                "upcoming_count": away_load,
                "has_european": away_has_euro,
                "fatigue_risk": "🔴 Yorgunluk Riski" if away_has_euro or away_load >= 3 else ("🟡 Orta Yük" if away_load >= 2 else "🟢 Dinç"),
                "upcoming": away_upcoming
            }
        }

    def generate_full_analysis(self, match):
        """Maç için tam derinlemesine analiz üretir"""
        home_stats = match.get("home_stats", {})
        away_stats = match.get("away_stats", {})

        home_last5 = home_stats.get("last_5", [])
        away_last5 = away_stats.get("last_5", [])

        home_form = self.analyze_form(home_last5)
        away_form = self.analyze_form(away_last5)

        squad_status = self.analyze_squad_status(home_stats, away_stats)

        h2h = self.analyze_h2h(
            match.get("head_to_head", []),
            match.get("home_team", ""),
            match.get("away_team", "")
        )

        fixture_load = self.analyze_fixture_load(
            home_stats.get("upcoming_fixtures", []),
            away_stats.get("upcoming_fixtures", [])
        )

        # Gol istatistikleri
        home_goals_scored_avg = home_stats.get("goals_scored_avg", 1.2)
        away_goals_scored_avg = away_stats.get("goals_scored_avg", 1.0)
        home_goals_conceded_avg = home_stats.get("goals_conceded_avg", 1.1)
        away_goals_conceded_avg = away_stats.get("goals_conceded_avg", 1.2)

        total_avg_goals = home_goals_scored_avg + away_goals_scored_avg

        # Güçlü tahmin önerileri oluştur
        recommendations = []

        # Form bazlı öneri
        if home_form["score"] > 65 and away_form["score"] < 40:
            recommendations.append({
                "pick": f"MS1 ({match.get('home_team', '')} Galibiyeti)",
                "confidence": "Yüksek",
                "reason": f"Ev sahibi son 5 maçta %{home_form['score']} puan oranıyla {home_form['trend']} formdayken, deplasman %{away_form['score']} ile {away_form['trend']}.",
                "odd_key": "ms1",
                "icon": "🏠"
            })
        elif away_form["score"] > 65 and home_form["score"] < 40:
            recommendations.append({
                "pick": f"MS2 ({match.get('away_team', '')} Galibiyeti)",
                "confidence": "Yüksek",
                "reason": f"Deplasman son 5 maçta %{away_form['score']} puan oranıyla {away_form['trend']} formdayken, ev sahibi %{home_form['score']} ile {home_form['trend']}.",
                "odd_key": "ms2",
                "icon": "✈️"
            })

        # Gol ortalamasına dayalı öneri
        if total_avg_goals >= 2.7:
            recommendations.append({
                "pick": "2.5 Üst",
                "confidence": "Orta-Yüksek",
                "reason": f"İki takım ortalaması {total_avg_goals:.1f} gol/maç. Ev sahibi ort. {home_goals_scored_avg} gol atıyor, deplasman {away_goals_scored_avg}.",
                "odd_key": "over25",
                "icon": "⚽"
            })
        elif total_avg_goals <= 2.0:
            recommendations.append({
                "pick": "2.5 Alt",
                "confidence": "Orta-Yüksek",
                "reason": f"İki takım ortalaması sadece {total_avg_goals:.1f} gol/maç ile kısır profil. Her iki savunma da güçlü.",
                "odd_key": "under25",
                "icon": "🔒"
            })

        # KG Var/Yok önerisi
        if home_goals_conceded_avg >= 1.2 and away_goals_scored_avg >= 1.0:
            recommendations.append({
                "pick": "KG Var",
                "confidence": "Orta",
                "reason": f"Ev sahibi maç başına {home_goals_conceded_avg} gol yiyor, deplasman {away_goals_scored_avg} gol atıyor.",
                "odd_key": "btts_yes",
                "icon": "🎯"
            })

        # Eksik oyuncu etkisi
        if squad_status["home"]["impact_score"] >= 4:
            recommendations.append({
                "pick": "Dikkat: Ev Sahibi Eksikli",
                "confidence": "Bilgi",
                "reason": f"Ev sahibi {squad_status['home']['total_missing']} kritik oyuncudan yoksun ({squad_status['home']['status']}). Bu faktör oranları etkileyebilir.",
                "odd_key": None,
                "icon": "🚑"
            })

        # Real data durumu bildirimi
        real_data = match.get("real_data_fetched", False)
        data_source = "✅ TheSportsDB Gerçek Verisi" if real_data else "⚠️ Nesine Oran Modeli (Tahmini)"

        # İY / MS Skor Analizi (Devre ve Maç Skoru Modeli)
        import math
        l_h = max(0.4, float(home_goals_scored_avg))
        l_a = max(0.4, float(away_goals_scored_avg))
        l_h1 = l_h * 0.44
        l_a1 = l_a * 0.44

        # En olası ilk yarı skorları
        ht_cands = [
            ("0-0", math.exp(-l_h1) * math.exp(-l_a1)),
            ("1-0", (l_h1 * math.exp(-l_h1)) * math.exp(-l_a1)),
            ("0-1", math.exp(-l_h1) * (l_a1 * math.exp(-l_a1))),
            ("1-1", (l_h1 * math.exp(-l_h1)) * (l_a1 * math.exp(-l_a1))),
            ("2-0", ((l_h1**2 / 2.0) * math.exp(-l_h1)) * math.exp(-l_a1)),
        ]
        ht_cands.sort(key=lambda x: x[1], reverse=True)
        top_ht = [{"score": s, "prob": round(p * 100, 1)} for s, p in ht_cands[:3]]

        # En olası maç sonu skorları
        ft_cands = [
            ("1-0", (l_h * math.exp(-l_h)) * math.exp(-l_a)),
            ("2-0", ((l_h**2 / 2.0) * math.exp(-l_h)) * math.exp(-l_a)),
            ("2-1", ((l_h**2 / 2.0) * math.exp(-l_h)) * (l_a * math.exp(-l_a))),
            ("1-1", (l_h * math.exp(-l_h)) * (l_a * math.exp(-l_a))),
            ("0-1", math.exp(-l_h) * (l_a * math.exp(-l_a))),
            ("0-2", math.exp(-l_h) * ((l_a**2 / 2.0) * math.exp(-l_a))),
            ("1-2", (l_h * math.exp(-l_h)) * ((l_a**2 / 2.0) * math.exp(-l_a))),
            ("0-0", math.exp(-l_h) * math.exp(-l_a)),
        ]
        ft_cands.sort(key=lambda x: x[1], reverse=True)
        top_ft = [{"score": s, "prob": round(p * 100, 1)} for s, p in ft_cands[:3]]

        pred_ht = top_ht[0]["score"]
        pred_ft = top_ft[0]["score"]
        nesine_score_display = f"{pred_ft} (İY: {pred_ht})"

        return {
            "home_form": home_form,
            "away_form": away_form,
            "squad_status": squad_status,
            "h2h": h2h,
            "fixture_load": fixture_load,
            "goal_stats": {
                "home_scored_avg": home_goals_scored_avg,
                "home_conceded_avg": home_goals_conceded_avg,
                "away_scored_avg": away_goals_scored_avg,
                "away_conceded_avg": away_goals_conceded_avg,
                "total_avg": round(total_avg_goals, 2)
            },
            "iyms_scores": {
                "top_ht": top_ht,
                "top_ft": top_ft,
                "predicted_ht": pred_ht,
                "predicted_ft": pred_ft,
                "display": nesine_score_display
            },
            "recommendations": recommendations,
            "data_source": data_source,
            "real_data_timestamp": match.get("real_data_timestamp", ""),
        }
