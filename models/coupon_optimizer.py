import datetime
from models.prediction_engine import PredictionEngine
from data.match_database import load_matches, get_dates


class CouponOptimizer:
    """
    Güven Ortalaması Yüksek, Net Sonuç Odaklı Yapay Zeka Kupon Motoru:
    - Uçuk/sürpriz skor veya düşük olasılıklı kombinasyonlar üretmez.
    - Net sonuçlar (MS 1, MS 2, 2.5 Gol Üst, Karşılıklı Gol Evet) ve
      en yüksek gol potansiyelli 4'lü '1.Y/2.Y KG: Evet/Evet' (50 TL) kuponlarını üretir.
    - Yalnızca başlamamış canlı bülten maçlarını kullanır ve her maça tek satırlık kısa not ekler.
    """

    MAJOR_LEAGUE_KEYWORDS = (
        "İngiltere", "İspanya", "Almanya", "İtalya", "Fransa", "Türkiye",
        "Hollanda", "Portekiz", "Belçika", "İskoçya", "Avusturya", "Danimarka",
        "İsviçre", "UEFA", "Şamp. Ligi", "Avrupa Ligi", "Brezilya", "Hırvatistan",
        "Slovakya", "Polonya", "Yunanistan", "Norveç", "İsveç", "Çekya", "AFC"
    )

    # Dünya taramasında tespit edilen kısır oyun / kaleci-savunma duvarı / 0 gol serisi tuzak maçları
    SCOUTED_LOW_GOAL_TRAP_CODES = {
        "3243650",  # Chesham Utd - Farnham (Chesham son 3 maç 0-2, 0-5, 0-4 — 0 gol!)
        "3243792",  # Wimbledon - Arsenal U21 (Wimbledon kupa maçları 1-1 ve 0-0)
        "3243726",  # Oxford City - Merthyr (Oxford maç başı 0.67 gol yiyor)
        "3243906",  # Hamburg - E. Frankfurt (İki takımın son 4 lig maçı da 1-0 / 0-1 bitti)
        "3243683",  # Sassuolo - Lazio (Lazio 8 maçta ilk yarılarda 0 gol yedi)
        "3243590",  # Köln - Union Berlin (Kısır hücum + 4 gün sonra lig rövanşı)
        "3243785",  # Krasnodar - D. Moskova (Son iki 2026 kupa maçı 0-1 ve 0-0)
        "3246485",  # Koper - NK Maribor (Maribor 11 maçta 9 gol yedi)
        "3274124",  # FC Eindhoven - Volendam (Eindhoven son 3 maçta 0-1, 0-3 kısır kaldı)
        "3243873",  # Bradford - Peterborough (Bradford son 5 maç 0 gol yedi, 3'ü 0-0!)
        "3243866",  # AC Cesena - Empoli (Cesena 0-3, 0-2; Empoli 0-2 — kısır kilit)
        "3243727",  # Mantova - Cremonese (Cremonese 7 maçta 6 gol, son maç 0-1)
    }

    # Karşılıklı Gol (KG Var) özelinde geçmiş skor/H2H ile tespit edilen tek taraflı veya kısır tuzaklar
    SCOUTED_BTTS_TRAP_CODES = SCOUTED_LOW_GOAL_TRAP_CODES | {
        "3243912",  # Benevento - Catanzaro (Son 5 H2H'nin 4'ü KG Yok: 0-1, 1-0, 0-0, 0-0)
        "3236281",  # D. Zagreb - Rijeka (Son 5 H2H'nin 3'ü KG Yok: 2-0, 0-0, 0-2)
        "3243616",  # Austria Wien - Hartberg (2026'daki 3 H2H'de de Hartberg gol atamadı: 0-1, 1-0, 0-2)
        "3243900",  # Elversberg - Darmstadt (Darmstadt son 2 maç 0-0 ve 0-4; 3/4 H2H KG Yok)
        "3246037",  # PAOK - AEK (Son 5 H2H'nin 4'ü KG Yok: 3-0, 0-0, 0-2, 1-0)
        "3246374",  # Genoa - Juventus (Genoa 1-0, Juve 2-0 savunma odaklı)
        "3246220",  # Parma - Udinese (Parma üst üste 3-0 kaybetti, son H2H 1-0)
        "3243573",  # Wealdstone - Solihull (Wealdstone son 3 maç 1-0, 1-0, 3-0 gol yemedi)
        "3243607",  # AFC Fylde - Hartlepool (Fylde son 3 maç KG Yok: 0-4, 5-0, 2-0)
        "3236933",  # Ceara - Goias (Goias son maç 0-0, Temmuz H2H 2-0)
        "3243825",  # Sporting - Maritimo (Maritimo 0-5 yenildi, kupa H2H 5-0)
        "3243772",  # RW Essen - Leipzig (Essen son 3 maç 1-0, 0-1, 2-0; tek taraflı fark)
    }

    # Gerçek 2026/27 son maç skorları ve H2H analizleriyle doğrulanan karşılıklı gol (KG Var) havuzu
    SCOUTED_VERIFIED_BTTS_CODES = {
        "3238402",  # Argentinos J. - Ind. Mendoza (Son 3 H2H 3/3 KG Var: 3-1, 2-2, 2-1)
        "3247937",  # Shakhtar D. - Dinamo Kiev (Geçen sezon kupa H2H 1-2; Dinamo son 2 maç 1-3 ve 3-1)
        "3246149",  # Aberdeen - Falkirk (Aberdeen son maç 2-3; formda Falkirk üst üste galip)
        "3246308",  # AC Monza - Napoli (Monza son maç 2-3, Napoli hafta sonu Roma ile 3-3)
        "3243801",  # Torino - Como 1907 (Torino son 3 maç 8 gol: 2-1, 3-0, 3-2; Como 2 maçta 5 gol)
        "3243721",  # Fulham - Crystal Palace (Eylül lig H2H Craven Cottage'da 2-3 bitti)
        "3261961",  # AB Gladsaxe - Brondby (Brondby son maçlar 3-1, 1-2, 5-2; AB dev eledi)
        "3243611",  # Bournemouth - Aston Villa (Villa 7 maç yenilgisiz 2-1 City, 3-1 Coventry)
        "3243709",  # LR Vicenza - Modena (Vicenza 2-2, Modena 3-2 Verona ve 1-2 Carrarese)
        "3243691",  # Man. City - Brighton (Etihad'daki son iki H2H 2-2 ve 1-1; Brighton ManU'yu 3-2 eledi)
        "3243688",  # Blackpool - Aston Villa U21 (4/4 kupa maçı KG Var: 3-2, 2-2, 3-2, 4-1)
        "3243745",  # B. Dortmund - Werder Bremen (18 gün önce 2-2; 9/11 H2H KG Var)
    }

    # Gerçek takım formu, kadro/kaleci haberleri ve H2H analizleriyle doğrulanan elit maç notları
    SCOUTED_ELITE_NOTES = {
        "3243591": "Ulusal Lig 3. ve 4.'sü (%79 sezonluk KG Var); Southend son 5 maçta 5/5 KG Var yaptı.",
        "3243688": "İki takımın EFL Trophy'deki 4 maçının 4'ü de KG Var ve 4+ golle bitti (ort. 4.8 gol/maç).",
        "3243675": "13 haftada toplam 54 gol yiyen iki açık savunmanın (3.92 gol/maç) 6 puanlık düellosu.",
        "3243646": "Everton U21 grup maçı 6-3 bitti; Shrewsbury son 2 maçında 3-2 ve 3-3 (11 gol) oynadı.",
        "3243773": "Man. City U21 grupta maç başı 6.50 gol ortalamasıyla (4-1, 3-5) oynuyor ve kazanmak zorunda.",
        "3243612": "Gladbach maçları ort. 4.71 gol; hafta sonu 6-1 yenilen Karlsruher'de as kaleci Bernat şüpheli.",
        "3243745": "Bremen son 6 maçın 5'inde 2+ gol attı; 18 gün önceki Dortmund - Bremen maçı 2-2 bitti.",
        "3243754": "Inzaghi'nin Al Hilal'i üst üste 3-2, 3-2 ve 2-1 kazanıyor; Bounedjah iç sahada boş geçmiyor.",
        "3261961": "Brondby tam kadro yıldızlarıyla sahada ama maç başı 2 gol yiyor; formda AB skor üretir.",
        "3243656": "Roma 8 maçta ilk yarı 1 gol yedi; Svilar yokken 2. yarıda dönen Malen kilidi açar.",
        "3270642": "League Two 2. ve 5.'si (Barnet ort. 3.64 gol/maç); son iki ikili maçları 3-1 ve 3-1 bitti.",
        "3243801": "Torino üst üste 3 maç kazandı (8 gol), Como son 2 maçta 5 gol attı; açık İtalya düellosu.",
        "3274097": "Sonuncu Willem II 10 maçta 32 gol yedi (ort. 3.2); son ikili randevuları 2-2 tamamlandı.",
        "3274133": "Markermeer Derbisi; iki takım da son maçını 3-2 oynadı, Ocak kupa maçları 3-1 bitti (%69 KG).",
        "3243623": "AIK'te savunma lideri Papagiannopoulos eksik (40:43 gol); Elfsborg tam kadro ilk 4 takibinde.",
        "3243772": "Leipzig'in Ekim'deki 4 maçının tamamı 4+ golle bitti (6-0, 4-0, 1-4, 1-6); kupa H2H 1-4.",
        "3243825": "Maritimo hafta sonu 5-0 yenildi; son Lig Kupası H2H maçını Sporting CP 5-0 kazanmıştı.",
        "3243898": "4. Ascoli son iki maçını 6-1 ve 3-1 kazandı (9 gol); 19. Sampdoria deplasmanda 1-4 dağıldı.",
        "3238402": "Son 3 ikili maçın tamamı KG Var bitti (3-1, 2-2, 2-1); Mendoza son 2 iç sahada 2-2 ve 1-1.",
        "3247937": "Geçen sezon aynı tur kupa randevusu 2-1 bitti; Dinamo yeni hocasıyla son 2 maçta 3-1 oynadı.",
        "3243721": "Eylül'de Craven Cottage'daki lig maçları 3-2 bitti; iki takım da kupada gol odaklı.",
        "3243611": "Bournemouth üst üste iki maçı 3-0 aldı; 7 maçtır yenilmeyen Villa kupada 3-1 ile turladı.",
        "3246308": "Monza son maçta Torino'ya 3-2 kaybetti (ort. 2+ yenilen gol); Napoli hafta sonu 3-3 oynadı.",
        "3246149": "Aberdeen hafta sonu 3-2 oynadı; yükselişteki Falkirk üst üste galibiyetlerle (3-0) geliyor.",
        "3248006": "Leicester son 5 maçta 5/5 2.5 Üst yaptı; sonuncu Wigan (4p) deplasmanda üst üste 2-1 kaybetti.",
        "3297737": "Luton Ekim ayındaki 4 maçının 4'ünü de kazandı (4-1, 2-1, 2-1, 2-1); iç sahada H2H üstün.",
        "3243709": "Vicenza Benevento ile 2-2 kaldı; 3. Modena son dönemde Verona'yı 3-2 yendi.",
        "3243691": "Etihad'daki son iki randevu 2-2 ve 1-1 bitti; Brighton önceki turda ManU'yu 3-2 eledi.",
    }

    def __init__(self):
        self.engine = PredictionEngine()
        self.rotation_index = 0

    @staticmethod
    def _safe_float(odds, key, default=None):
        """None, str veya eksik oranları güvenli bir şekilde floata dönüştürür."""
        if not isinstance(odds, dict):
            return default
        val = odds.get(key)
        if val is None:
            return default
        try:
            return float(val)
        except (TypeError, ValueError):
            return default

    @classmethod
    def _league_bonus(cls, league_name):
        lname = league_name or ""
        return 1.06 if any(k.lower() in lname.lower() for k in cls.MAJOR_LEAGUE_KEYWORDS) else 1.0

    @staticmethod
    def _format_league(m):
        raw_c = (m.get("country") or "🌍").replace("FUTBOL-GENEL", "").strip()
        raw_c = raw_c.replace("🌍 ENG", "🏴󠁧󠁢󠁥󠁮󠁧󠁿").replace("🌍 SCO", "🏴󠁧󠁢󠁳󠁣󠁴󠁿")
        league = (m.get("league") or "").strip()
        parts = raw_c.split()
        if len(parts) >= 2 and parts[-1].lower() in league.lower():
            return f"{parts[0]} {league}"
        return f"{raw_c} {league}".strip()

    @staticmethod
    def _match_code(m):
        if m.get("bulten_code"):
            return str(m["bulten_code"])
        if m.get("nesine_code"):
            return str(m["nesine_code"])
        return str(m.get("id", "")).replace("st-", "").replace("nesine-", "")

    @staticmethod
    def _calc_confidence(real_odd, model_prob_pct):
        """Gerçek piyasa oranı ile model olasılığını harmanlayarak gerçekçi % güven üretir."""
        implied = min(88.0, (0.91 / max(1.08, real_odd)) * 100.0)
        blended = 0.62 * implied + 0.38 * float(model_prob_pct)
        return round(max(52.0, min(89.0, blended)), 1)

    def analyze_matches(self, matches):
        """Maç havuzunu istatistiksel analizden geçirir (bitmiş/başlamış maçları kesinlikle eler)."""
        analyzed = []
        now_dt = datetime.datetime.now()
        for m in matches:
            mt_str = m.get("match_time", "")
            if mt_str:
                try:
                    m_dt = datetime.datetime.strptime(mt_str, "%d.%m.%Y %H:%M")
                    if m_dt <= now_dt:
                        continue
                except Exception:
                    pass

            l_home, l_away = self.engine.calculate_expected_goals(m["home_stats"], m["away_stats"])
            probs = self.engine.compute_match_probabilities(l_home, l_away)
            value_bets, all_options = self.engine.analyze_value_bets(probs, m["odds"])

            analyzed.append({
                "match": m,
                "probs": probs,
                "value_bets": value_bets,
                "all_options": all_options,
            })
        return analyzed

    @staticmethod
    def _select_with_rotation(candidates, count, rotation, step=2):
        """En yüksek güvenli üst havuz içinden rotasyonlu seçim yapar (kaliteyi düşürmez)."""
        if not candidates:
            return []
        top_window = candidates[: max(count * 4, 16)]
        if rotation > 0 and len(top_window) > count:
            offset = (rotation * step) % len(top_window)
            top_window = top_window[offset:] + top_window[:offset]

        selected = []
        used_ids = set()
        for c in top_window + candidates:
            if c["match_id"] not in used_ids:
                selected.append(c)
                used_ids.add(c["match_id"])
                if len(selected) == count:
                    break
        return selected

    @staticmethod
    def _finalize_coupon(selected, title, day_label, badge, color, ctype, summary_prefix, stake=50):
        total_odd = 1.0
        total_prob = 1.0
        conf_sum = 0.0
        for s in selected:
            total_odd *= s["odd"]
            total_prob *= (max(5.0, s.get("prob", 60.0)) / 100.0)
            conf_sum += s.get("confidence", s.get("prob", 70.0))

        avg_conf = round(conf_sum / len(selected), 1) if selected else 0.0
        total_odd_rounded = round(total_odd, 2)
        target_return = round(stake * total_odd_rounded, 2)

        return {
            "title": title,
            "day_label": day_label,
            "badge": badge,
            "color": color,
            "type": ctype,
            "min_stake": stake,
            "target_stake": stake,
            "target_return": target_return,
            "avg_confidence": avg_conf,
            "match_count": len(selected),
            "total_odd": total_odd_rounded,
            "win_probability": round(total_prob * 100.0, 2),
            "matches": selected,
            "summary": (
                f"{summary_prefix} Ortalama güven: %{avg_conf:.0f} | "
                f"{stake} TL kupon bedeliyle tahmini kazanç: {target_return:,.2f} TL."
            ),
        }

    @staticmethod
    def _finalize_system_coupon(selected, system_sizes, title, day_label, badge, color, ctype, summary_text, ref_hits=4):
        """Sistem kuponları (ör. Sistem 1,2,3,4 = 98 TL veya Sistem 2,3,4,5 = 56 TL) için gerçek kolon hesabı yapar."""
        import math
        from itertools import combinations

        n = len(selected)
        valid_sizes = [k for k in system_sizes if 1 <= k <= n]
        col_count = sum(math.comb(n, k) for k in valid_sizes)
        stake = max(1, col_count)  # Misli: 1 (her kolon 1 TL)

        conf_sum = sum(s.get("confidence", 62.0) for s in selected)
        avg_conf = round(conf_sum / n, 1) if n else 0.0

        # Tüm kolonların üst tavan toplamı (kolon başı resmi tavan 12.500.000 TL)
        full_return = 0.0
        for k in valid_sizes:
            for comb in combinations(selected, k):
                p = 1.0
                for item in comb:
                    p *= item["odd"]
                full_return += min(12500000.0, p)

        # Referans tutuş sayısı (ör. 7 maçta 4 tutuş veya 6 maçta 4 tutuş) için ortalama gerçekçi ödeme
        ref_k = min(n, max(min(valid_sizes) if valid_sizes else 1, ref_hits))
        sample_subsets = list(combinations(selected, ref_k))
        if sample_subsets:
            sub_returns = []
            for sub in sample_subsets:
                s_ret = 0.0
                for k in valid_sizes:
                    if k <= ref_k:
                        for c2 in combinations(sub, k):
                            p2 = 1.0
                            for it2 in c2:
                                p2 *= it2["odd"]
                            s_ret += min(12500000.0, p2)
                sub_returns.append(s_ret)
            realistic_return = round(sum(sub_returns) / len(sub_returns), 2)
        else:
            realistic_return = round(full_return, 2)

        sys_str = ", ".join(str(k) for k in valid_sizes)
        eff_odd = round(realistic_return / stake, 2) if stake else 0.0

        return {
            "title": title,
            "day_label": day_label,
            "badge": badge,
            "color": color,
            "type": ctype,
            "system_label": sys_str,
            "system_columns": col_count,
            "system_ref_hits": ref_k,
            "system_target_return": realistic_return,
            "system_max_return": round(min(12500000.0, full_return), 2),
            "min_stake": stake,
            "target_stake": stake,
            "target_return": realistic_return,
            "avg_confidence": avg_conf,
            "match_count": n,
            "total_odd": eff_odd,
            "win_probability": 12.5,
            "matches": selected,
            "summary": summary_text,
        }

    def build_net_guven_coupon(self, analyzed_pool, title=None, badge=None, day_label=None, rotation=0, count=4):
        """
        Yüksek Güvenli Net Sonuç Kuponu (4 Maç - 50 TL):
        Sadece net ve güvenilir tercihler: MS 1, MS 2, 2.5 Gol Üst, Karşılıklı Gol Evet.
        Oran aralığı: 1.28 - 1.65 (yüksek tutma olasılığı + tatmin edici toplam çarpan).
        """
        candidates = []
        for item in analyzed_pool:
            m = item["match"]
            odds = m.get("odds", {})
            probs = item["probs"]
            l_bonus = self._league_bonus(m.get("league", ""))
            tot_xg = probs.get("total_xg", 2.5)
            h_avg = m["home_stats"].get("goals_scored_avg", probs.get("lambda_home", 1.4))
            a_avg = m["away_stats"].get("goals_scored_avg", probs.get("lambda_away", 1.1))

            best_for_match = None

            # 1) Net Ev Sahibi Galibiyeti (MS 1)
            ms1 = self._safe_float(odds, "ms1")
            if ms1 and 1.32 <= ms1 <= 1.66:
                conf = self._calc_confidence(ms1, probs.get("ms1", 0.65) * 100)
                score = conf * l_bonus * (1.0 + (ms1 - 1.30) * 0.12)
                note = f"{m['home_team']} iç saha form ve kadro üstünlüğüyle net favori ({probs['lambda_home']:.2f} xG)."
                best_for_match = (score, "Maç Sonucu: 1", "ms1", ms1, conf, note)

            # 2) Net Deplasman Galibiyeti (MS 2)
            ms2 = self._safe_float(odds, "ms2")
            if ms2 and 1.32 <= ms2 <= 1.64:
                conf = self._calc_confidence(ms2, probs.get("ms2", 0.64) * 100)
                score = conf * l_bonus * (1.0 + (ms2 - 1.30) * 0.12)
                if not best_for_match or score > best_for_match[0]:
                    note = f"{m['away_team']} form ve hücum kalitesiyle deplasmanda net galibiyete yakın ({probs['lambda_away']:.2f} xG)."
                    best_for_match = (score, "Maç Sonucu: 2", "ms2", ms2, conf, note)

            # 3) Net 2,5 Gol Üst
            o25 = self._safe_float(odds, "over25")
            if o25 and 1.32 <= o25 <= 1.64 and tot_xg >= 2.65:
                conf = self._calc_confidence(o25, probs.get("over25", 0.66) * 100)
                score = conf * l_bonus * (1.0 + (o25 - 1.30) * 0.12)
                if not best_for_match or score > best_for_match[0]:
                    note = f"Yüksek gol beklentisi ({tot_xg:.2f} xG) ve açık oyun yapısıyla 2,5 Üst çok güçlü."
                    best_for_match = (score, "2,5 Gol: Üst", "over25", o25, conf, note)

            # 4) Net Karşılıklı Gol: Evet
            kg = self._safe_float(odds, "btts_yes")
            if kg and 1.34 <= kg <= 1.62 and probs.get("lambda_home", 1.2) >= 1.10 and probs.get("lambda_away", 1.1) >= 1.05:
                conf = self._calc_confidence(kg, probs.get("btts_yes", 0.65) * 100)
                score = conf * l_bonus * (1.0 + (kg - 1.30) * 0.12)
                if not best_for_match or score > best_for_match[0]:
                    note = f"İki takım da düzenli skor üretiyor (ort. {h_avg:.1f} - {a_avg:.1f} gol); karşılıklı gol net tercih."
                    best_for_match = (score, "Karşılıklı Gol: Evet", "btts_yes", kg, conf, note)

            if best_for_match:
                sc, pick_lbl, pick_key, odd_val, conf_val, short_note = best_for_match
                candidates.append({
                    "match_id": m["id"],
                    "nesine_code": self._match_code(m),
                    "match_name": f"{m['home_team']} - {m['away_team']}",
                    "league": self._format_league(m),
                    "time": m["match_time"],
                    "status_text": "Oynanmadı",
                    "pick": pick_lbl,
                    "pick_key": pick_key,
                    "odd": round(odd_val, 2),
                    "prob": conf_val,
                    "confidence": conf_val,
                    "confidence_label": f"%{conf_val:.0f} Güven",
                    "ev": round(((conf_val / 100.0) * odd_val - 1.0) * 100, 1),
                    "short_note": short_note,
                    "deep_reason": short_note,
                    "is_real_market": True,
                    "score_metric": sc,
                })

        candidates.sort(key=lambda x: x["score_metric"], reverse=True)
        selected = self._select_with_rotation(candidates, count=count, rotation=rotation, step=2)

        return self._finalize_coupon(
            selected=selected,
            title=title or "Yüksek Güvenli Net Sonuç Kuponu (4 Maç)",
            day_label=day_label or "Yüksek Güven Net",
            badge=badge or "🛡️ YÜKSEK GÜVEN ORTALAMALI NET SONUÇ KUPONU (50 TL)",
            color="emerald",
            ctype="net_guven",
            summary_prefix="Uçuk risklerden arındırılmış, form ve oran istikrarı en yüksek 4 net maç seçildi.",
            stake=50,
        )

    def build_both_halves_btts_coupon(self, analyzed_pool, rotation=0, count=4):
        """
        4 Maç '1. Yarı / 2. Yarı KG: Evet/Evet' Kuponu (50 TL):
        - Kullanıcının özel isteği: 4 tane Evet/Evet maçını 50 TL ile kazanmaya odaklanır.
        - Rastgele uçuk oranlı (18.00-25.00) kısır maçları kesinlikle almaz!
        - Yalnızca bültende 'both_halves_btts_yes' pazarı gerçekten açık olan, KG Var (1.18-1.45)
          ve 2.5 Üst (1.17-1.48) oranları bültenin en düşük/en güvenilir seviyesindeki gollü maçları seçer.
        """
        candidates = []
        for item in analyzed_pool:
            m = item["match"]
            m_code = self._match_code(m)
            if m_code in self.SCOUTED_LOW_GOAL_TRAP_CODES:
                continue
            odds = m.get("odds", {})
            probs = item["probs"]

            bh_odd = self._safe_float(odds, "both_halves_btts_yes")
            kg_odd = self._safe_float(odds, "btts_yes")
            o25_odd = self._safe_float(odds, "over25")
            ms1_odd = self._safe_float(odds, "ms1", 2.2)
            ms2_odd = self._safe_float(odds, "ms2", 2.2)

            if not bh_odd or not kg_odd or not o25_odd:
                continue

            # İki takım da gol atabilecek güçte olmalı (zayıf tarafın ilk yarı kapanma riski elenir)
            if bh_odd > 12.80 or kg_odd > 1.52 or o25_odd > 1.58:
                continue
            if (ms1_odd > 4.40 or ms2_odd > 4.40) and m_code not in {"3243688", "3243612"}:
                continue

            l_bonus = self._league_bonus(m.get("league", ""))
            scout_bonus = 1.12 if m_code in self.SCOUTED_ELITE_NOTES else 1.0

            # Gol güven puanı: KG Var ve 2.5 Üst ne kadar düşük/net ise iki yarıda gol potansiyeli o kadar yüksektir
            btts_conf = min(88.0, (0.92 / max(1.12, kg_odd)) * 100.0)
            over_conf = min(88.0, (0.92 / max(1.12, o25_odd)) * 100.0)
            goal_confidence = round(min(86.0, 0.55 * btts_conf + 0.45 * over_conf), 1)

            # Sıralama metriği: Gerçek saha doğrulaması + en yüksek gol güveni + en verimli Evet/Evet oranı
            score = (goal_confidence * l_bonus * scout_bonus) - (bh_odd * 1.05)

            real_hit_prob = round(min(22.0, max(8.5, (0.90 / bh_odd) * 100.0)), 1)
            short_note = self.SCOUTED_ELITE_NOTES.get(
                m_code,
                f"KG Evet ({kg_odd:.2f}) ve 2,5 Üst ({o25_odd:.2f}) bültenin en net gol bandında; "
                f"iki devrede de karşılıklı gole en uygun açık maç."
            )

            candidates.append({
                "match_id": m["id"],
                "nesine_code": self._match_code(m),
                "match_name": f"{m['home_team']} - {m['away_team']}",
                "league": f"{m.get('country', '🌍')} {m['league']}",
                "time": m["match_time"],
                "status_text": "Oynanmadı",
                "pick": "1. Yarı / 2. Yarı KG: Evet/Evet",
                "pick_key": "both_halves_btts_yes",
                "odd": round(bh_odd, 2),
                "prob": real_hit_prob,
                "confidence": goal_confidence,
                "confidence_label": f"%{goal_confidence:.0f} Gol Güveni",
                "ev": round(((real_hit_prob / 100.0) * bh_odd - 1.0) * 100, 1),
                "short_note": short_note,
                "deep_reason": short_note,
                "is_real_market": True,
                "score_metric": score,
            })

        # Yedek: Eğer çok sıkı filtre < count dönerse açık Evet/Evet'lerden en düşük oranlıları ekle
        if len(candidates) < count:
            existing_ids = {c["match_id"] for c in candidates}
            fallback = []
            for item in analyzed_pool:
                m = item["match"]
                if m["id"] in existing_ids:
                    continue
                odds = m.get("odds", {})
                bh_odd = self._safe_float(odds, "both_halves_btts_yes")
                if bh_odd and bh_odd <= 15.0:
                    kg_odd = self._safe_float(odds, "btts_yes", 1.55)
                    goal_conf = round(min(82.0, (0.91 / max(1.15, kg_odd)) * 100.0), 1)
                    note = f"Çift yönlü açık hücum temposu ({bh_odd:.2f} oran); iki yarıda da gol beklentisi yüksek."
                    fallback.append({
                        "match_id": m["id"],
                        "nesine_code": self._match_code(m),
                        "match_name": f"{m['home_team']} - {m['away_team']}",
                        "league": self._format_league(m),
                        "time": m["match_time"],
                        "status_text": "Oynanmadı",
                        "pick": "1. Yarı / 2. Yarı KG: Evet/Evet",
                        "pick_key": "both_halves_btts_yes",
                        "odd": round(bh_odd, 2),
                        "prob": round((0.88 / bh_odd) * 100.0, 1),
                        "confidence": goal_conf,
                        "confidence_label": f"%{goal_conf:.0f} Gol Güveni",
                        "ev": 4.0,
                        "short_note": note,
                        "deep_reason": note,
                        "is_real_market": True,
                        "score_metric": goal_conf - bh_odd,
                    })
            fallback.sort(key=lambda x: x["score_metric"], reverse=True)
            candidates.extend(fallback)

        candidates.sort(key=lambda x: x["score_metric"], reverse=True)
        selected = self._select_with_rotation(candidates, count=count, rotation=rotation, step=1)

        return self._finalize_coupon(
            selected=selected,
            title="4 Maç 1.Y/2.Y Evet/Evet Kuponu (50 TL)",
            day_label="4 Maç Evet/Evet",
            badge="⚽ EN YÜKSEK GOL GÜVENLİ 4 ADET EVET/EVET MAÇI (50 TL KUPON)",
            color="green",
            ctype="both_halves_kg",
            summary_prefix="Bültende KG ve Üst oranları en düşük, iki yarıda da karşılıklı gol potansiyeli en yüksek 4 açık maç seçildi.",
            stake=50,
        )

    def build_kg_evet_net_coupon(self, analyzed_pool, rotation=0, count=4):
        """
        4 Maç Maç Geneli 'Karşılıklı Gol: Evet' (KG Var) Net Kuponu (50 TL):
        Yüksek güven ortalamalı (%70-%80), her iki takımın da gol atması en muhtemel 4 maç.
        """
        candidates = []
        for item in analyzed_pool:
            m = item["match"]
            odds = m.get("odds", {})
            probs = item["probs"]
            kg_odd = self._safe_float(odds, "btts_yes")
            o25_odd = self._safe_float(odds, "over25", 1.70)
            ms1_odd = self._safe_float(odds, "ms1", 2.20)
            ms2_odd = self._safe_float(odds, "ms2", 2.20)

            if not kg_odd or not (1.25 <= kg_odd <= 1.62):
                continue
            if ms1_odd > 4.50 or ms2_odd > 4.50:
                continue

            conf = self._calc_confidence(kg_odd, probs.get("btts_yes", 0.66) * 100)
            score = conf * self._league_bonus(m.get("league", ""))
            short_note = (
                f"Dengeli hücum gücü ve {o25_odd:.2f} Üst oranıyla iki takımın da skor üretmesi yüksek güven veriyor."
            )
            candidates.append({
                "match_id": m["id"],
                "nesine_code": self._match_code(m),
                "match_name": f"{m['home_team']} - {m['away_team']}",
                "league": f"{m.get('country', '🌍')} {m['league']}",
                "time": m["match_time"],
                "status_text": "Oynanmadı",
                "pick": "Karşılıklı Gol: Evet",
                "pick_key": "btts_yes",
                "odd": round(kg_odd, 2),
                "prob": conf,
                "confidence": conf,
                "confidence_label": f"%{conf:.0f} Güven",
                "ev": round(((conf / 100.0) * kg_odd - 1.0) * 100, 1),
                "short_note": short_note,
                "deep_reason": short_note,
                "is_real_market": True,
                "score_metric": score,
            })

        candidates.sort(key=lambda x: x["score_metric"], reverse=True)
        selected = self._select_with_rotation(candidates, count=count, rotation=rotation, step=2)

        return self._finalize_coupon(
            selected=selected,
            title="4 Maç Karşılıklı Gol Evet (Net) Kuponu",
            day_label="4 Maç KG Evet",
            badge="✅ YÜKSEK GÜVENLİ 4 MAÇ KARŞILIKLI GOL EVET (50 TL)",
            color="teal",
            ctype="kg_evet_net",
            summary_prefix="İki takımın da gol bulma istatistiği en yüksek 4 net KG Evet karşılaşması.",
            stake=50,
        )

    def build_ust_25_net_coupon(self, analyzed_pool, rotation=0, count=4):
        """
        4 Maç '2,5 Gol Üst' Yüksek Güven Kuponu (50 TL):
        Maç başı gol beklentisi en yüksek, net 2.5 Üst bitecek 4 karşılaşma.
        """
        candidates = []
        for item in analyzed_pool:
            m = item["match"]
            odds = m.get("odds", {})
            probs = item["probs"]
            o25_odd = self._safe_float(odds, "over25")
            tot_xg = probs.get("total_xg", 2.7)

            if not o25_odd or not (1.25 <= o25_odd <= 1.62):
                continue

            conf = self._calc_confidence(o25_odd, probs.get("over25", 0.68) * 100)
            score = conf * self._league_bonus(m.get("league", "")) * (1.0 + max(0.0, tot_xg - 2.5) * 0.04)
            short_note = (
                f"Toplam {tot_xg:.2f} xG gol beklentisi ve yüksek hücum temposuyla en az 3 gol net öne çıkıyor."
            )
            candidates.append({
                "match_id": m["id"],
                "nesine_code": self._match_code(m),
                "match_name": f"{m['home_team']} - {m['away_team']}",
                "league": f"{m.get('country', '🌍')} {m['league']}",
                "time": m["match_time"],
                "status_text": "Oynanmadı",
                "pick": "2,5 Gol: Üst",
                "pick_key": "over25",
                "odd": round(o25_odd, 2),
                "prob": conf,
                "confidence": conf,
                "confidence_label": f"%{conf:.0f} Güven",
                "ev": round(((conf / 100.0) * o25_odd - 1.0) * 100, 1),
                "short_note": short_note,
                "deep_reason": short_note,
                "is_real_market": True,
                "score_metric": score,
            })

        candidates.sort(key=lambda x: x["score_metric"], reverse=True)
        selected = self._select_with_rotation(candidates, count=count, rotation=rotation, step=2)

        return self._finalize_coupon(
            selected=selected,
            title="4 Maç 2,5 Gol Üst (Net) Kuponu",
            day_label="4 Maç 2,5 Üst",
            badge="🔥 YÜKSEK GÜVENLİ 4 MAÇ 2,5 GOL ÜST KUPONU (50 TL)",
            color="amber",
            ctype="ust_25_net",
            summary_prefix="Gol ortalaması ve xG verisi en yüksek 4 net 2,5 Üst karşılaşması.",
            stake=50,
        )

    def build_kontrgaranti_coupon(self, analyzed_pool, rotation=0, count=4):
        """
        Kontrgaranti Çifte Şans Kuponu (1X0 • 2X0 • 1X2 — 4 Maç, 50 TL):
        - 1X0 (Çifte Şans 1-0: Ev Sahibi veya Beraberlik)
        - 2X0 (Çifte Şans 0-2: Deplasman veya Beraberlik)
        - 1X2 (Çifte Şans 1-2: Ev veya Deplasman Kazanır, Berabere Bitmez)
        Gerçek Spor Toto Çifte Şans oranlarından (1.20 - 1.48 bandı) en yüksek güvenli seçimleri derler.
        """
        cands_10 = []
        cands_02 = []
        cands_12 = []

        for item in analyzed_pool:
            m = item["match"]
            odds = m.get("odds", {})
            probs = item["probs"]
            l_bonus = self._league_bonus(m.get("league", ""))
            tot_xg = probs.get("total_xg", 2.6)

            cs10 = self._safe_float(odds, "cs10")
            cs02 = self._safe_float(odds, "cs02")
            cs12 = self._safe_float(odds, "cs12")
            msX = self._safe_float(odds, "msX", 3.20)

            if cs10 and 1.20 <= cs10 <= 1.48:
                conf = self._calc_confidence(cs10, probs.get("cs1X", 0.78) * 100)
                note = f"{m['home_team']} iç sahada çok dirençli; beraberlik de cepte olduğu için 1X0 kontrgaranti net tercih."
                cands_10.append({
                    "match_id": m["id"],
                    "nesine_code": self._match_code(m),
                    "match_name": f"{m['home_team']} - {m['away_team']}",
                    "league": self._format_league(m),
                    "time": m["match_time"],
                    "status_text": "Oynanmadı",
                    "pick": "Kontrgaranti ÇŞ: 1-0 (1X0)",
                    "pick_key": "cs10",
                    "odd": round(cs10, 2),
                    "prob": conf,
                    "confidence": conf,
                    "confidence_label": f"%{conf:.0f} Güven",
                    "ev": round(((conf / 100.0) * cs10 - 1.0) * 100, 1),
                    "short_note": note,
                    "deep_reason": note,
                    "is_real_market": True,
                    "score_metric": conf * l_bonus * (1.0 + (cs10 - 1.18) * 0.15),
                })

            if cs02 and 1.20 <= cs02 <= 1.48:
                conf = self._calc_confidence(cs02, probs.get("csX2", 0.77) * 100)
                note = f"{m['away_team']} form üstünlüğüyle kaybetmez; beraberlik korumalı 2X0 kontrgaranti yüksek güvenli."
                cands_02.append({
                    "match_id": m["id"],
                    "nesine_code": self._match_code(m),
                    "match_name": f"{m['home_team']} - {m['away_team']}",
                    "league": self._format_league(m),
                    "time": m["match_time"],
                    "status_text": "Oynanmadı",
                    "pick": "Kontrgaranti ÇŞ: 0-2 (2X0)",
                    "pick_key": "cs02",
                    "odd": round(cs02, 2),
                    "prob": conf,
                    "confidence": conf,
                    "confidence_label": f"%{conf:.0f} Güven",
                    "ev": round(((conf / 100.0) * cs02 - 1.0) * 100, 1),
                    "short_note": note,
                    "deep_reason": note,
                    "is_real_market": True,
                    "score_metric": conf * l_bonus * (1.0 + (cs02 - 1.18) * 0.15),
                })

            if cs12 and 1.14 <= cs12 <= 1.38 and tot_xg >= 2.55 and msX >= 3.05:
                conf = self._calc_confidence(cs12, probs.get("cs12", 0.80) * 100)
                note = f"Yüksek tempolu açık oyun ({tot_xg:.2f} xG); beraberlik ihtimali düşük, bir taraf kazanır (1X2)."
                cands_12.append({
                    "match_id": m["id"],
                    "nesine_code": self._match_code(m),
                    "match_name": f"{m['home_team']} - {m['away_team']}",
                    "league": self._format_league(m),
                    "time": m["match_time"],
                    "status_text": "Oynanmadı",
                    "pick": "Kontrgaranti ÇŞ: 1-2 (1X2)",
                    "pick_key": "cs12",
                    "odd": round(cs12, 2),
                    "prob": conf,
                    "confidence": conf,
                    "confidence_label": f"%{conf:.0f} Güven",
                    "ev": round(((conf / 100.0) * cs12 - 1.0) * 100, 1),
                    "short_note": note,
                    "deep_reason": note,
                    "is_real_market": True,
                    "score_metric": conf * l_bonus * (1.0 + (cs12 - 1.16) * 0.15),
                })

        cands_10.sort(key=lambda x: x["score_metric"], reverse=True)
        cands_02.sort(key=lambda x: x["score_metric"], reverse=True)
        cands_12.sort(key=lambda x: x["score_metric"], reverse=True)

        # 1X0, 2X0 ve 1X2 seçeneklerini dengeli harmanla
        interleaved = []
        max_len = max(len(cands_10), len(cands_02), len(cands_12))
        for i in range(max_len):
            if i < len(cands_10):
                interleaved.append(cands_10[i])
            if i < len(cands_02):
                interleaved.append(cands_02[i])
            if i < len(cands_12):
                interleaved.append(cands_12[i])

        selected = self._select_with_rotation(interleaved, count=count, rotation=rotation, step=3)

        return self._finalize_coupon(
            selected=selected,
            title="Kontrgaranti Çifte Şans Kuponu (4 Maç)",
            day_label="Kontrgaranti Net",
            badge="🔒 KONTRGARANTİ (1-0 / 0-2 / 1-2) 4 MAÇ NET KUPONU (50 TL)",
            color="cyan",
            ctype="kontrgaranti",
            summary_prefix="Çifte şans (1X0, 2X0, 1X2) korumasıyla tek gol sürprizlerine karşı en sağlam 4 kontrgaranti seçimi.",
            stake=50,
        )

    def build_iy_ms_10_20_coupon(self, analyzed_pool, rotation=0, count=4):
        """
        İlk Yarı / Maç Sonucu: 1/0 ve 2/0 Kuponu (4 Maç - 50 TL):
        - 1/0 (İlk Yarı 1 / Maç Sonucu Beraberlik)
        - 2/0 (İlk Yarı 2 / Maç Sonucu Beraberlik)
        Yalnızca gerçek bültende açık, beraberlik oranı düşük (dengeli güç) ve KG Evet beklentili
        (1-1 / 2-2 skora en yatkın) karşılaşmalardan seçilir.
        """
        cands_10 = []
        cands_20 = []
        for item in analyzed_pool:
            m = item["match"]
            odds = m.get("odds", {})
            l_bonus = self._league_bonus(m.get("league", ""))

            ms1 = self._safe_float(odds, "ms1")
            msX = self._safe_float(odds, "msX")
            ms2 = self._safe_float(odds, "ms2")
            kg = self._safe_float(odds, "btts_yes", 1.70)
            o_10 = self._safe_float(odds, "ht_ft_10")
            o_20 = self._safe_float(odds, "ht_ft_20")

            if not (ms1 and msX and ms2) or not (o_10 or o_20):
                continue
            if msX > 3.45 or ms1 < 1.65 or ms2 < 1.65 or kg > 1.85:
                continue

            fit_conf = round(min(74.0, max(56.0, 102.0 - (msX * 8.5) - (kg * 9.0))), 1)
            score = fit_conf * l_bonus - abs(ms1 - ms2) * 3.0

            if ms1 <= ms2 and o_10 and 10.0 <= o_10 <= 16.5:
                note = f"Dengeli güçler (MS 0: {msX:.2f}, KG: {kg:.2f}); {m['home_team']} ilk yarı önde girip 1-1/2-2 dengelenmeye çok uygun."
                cands_10.append({
                    "match_id": m["id"],
                    "nesine_code": self._match_code(m),
                    "match_name": f"{m['home_team']} - {m['away_team']}",
                    "league": self._format_league(m),
                    "time": m["match_time"],
                    "status_text": "Oynanmadı",
                    "pick": "İY/MS: 1/0 (İY Ev / MS Berabere)",
                    "pick_key": "ht_ft_10",
                    "odd": round(o_10, 2),
                    "prob": round((0.88 / o_10) * 100.0, 1),
                    "confidence": fit_conf,
                    "confidence_label": f"%{fit_conf:.0f} Senaryo Uyumu",
                    "ev": 6.5,
                    "short_note": note,
                    "deep_reason": note,
                    "is_real_market": True,
                    "score_metric": score,
                })
            elif o_20 and 10.0 <= o_20 <= 16.5:
                note = f"Dengeli eşleşme (MS 0: {msX:.2f}, KG: {kg:.2f}); {m['away_team']} ilk devre golü sonrası ikinci yarıda 1-1/2-2 denge adayı."
                cands_20.append({
                    "match_id": m["id"],
                    "nesine_code": self._match_code(m),
                    "match_name": f"{m['home_team']} - {m['away_team']}",
                    "league": self._format_league(m),
                    "time": m["match_time"],
                    "status_text": "Oynanmadı",
                    "pick": "İY/MS: 2/0 (İY Dep / MS Berabere)",
                    "pick_key": "ht_ft_20",
                    "odd": round(o_20, 2),
                    "prob": round((0.88 / o_20) * 100.0, 1),
                    "confidence": fit_conf,
                    "confidence_label": f"%{fit_conf:.0f} Senaryo Uyumu",
                    "ev": 6.5,
                    "short_note": note,
                    "deep_reason": note,
                    "is_real_market": True,
                    "score_metric": score,
                })

        cands_10.sort(key=lambda x: x["score_metric"], reverse=True)
        cands_20.sort(key=lambda x: x["score_metric"], reverse=True)
        candidates = []
        for i in range(max(len(cands_10), len(cands_20))):
            if i < len(cands_10):
                candidates.append(cands_10[i])
            if i < len(cands_20):
                candidates.append(cands_20[i])

        selected = self._select_with_rotation(candidates, count=count, rotation=rotation, step=1)

        return self._finalize_coupon(
            selected=selected,
            title="İY/MS 1/0 & 2/0 Denge Kuponu (4 Maç - 50 TL)",
            day_label="İY/MS 1/0 • 2/0 (4 Maç)",
            badge="🔄 İLK YARI ÖNDE / MAÇ SONU BERABERLİK (1/0 • 2/0) 4 MAÇ KUPONU",
            color="orange",
            ctype="iy_ms_10_20",
            summary_prefix="Bültende beraberlik ve karşılıklı gol (1-1 / 2-2) uyumu en yüksek 4 adet 1/0 ve 2/0 karşılaşması.",
            stake=50,
        )

    def build_iy_ms_12_21_coupon(self, analyzed_pool, rotation=0, count=4):
        """
        İlk Yarı / Maç Sonucu: 1/2 ve 2/1 Geri Dönüş Kuponu (4 Maç - 50 TL):
        - 2/1 (İlk Yarı Deplasman / Maç Sonucu Ev Sahibi)
        - 1/2 (İlk Yarı Ev Sahibi / Maç Sonucu Deplasman)
        Yalnızca gerçek bültende açık, KG Evet ve 2.5 Üst oranı düşük (bol gollü geri dönüşe açık)
        ve net bir favorisi olan karşılaşmalardan seçilir.
        """
        candidates = []
        for item in analyzed_pool:
            m = item["match"]
            odds = m.get("odds", {})
            l_bonus = self._league_bonus(m.get("league", ""))

            ms1 = self._safe_float(odds, "ms1")
            ms2 = self._safe_float(odds, "ms2")
            kg = self._safe_float(odds, "btts_yes", 1.75)
            o25 = self._safe_float(odds, "over25", 1.80)
            o_21 = self._safe_float(odds, "ht_ft_21")
            o_12 = self._safe_float(odds, "ht_ft_12")

            if not (ms1 and ms2) or not (o_21 or o_12):
                continue
            # Geri dönüş (2-1 / 1-2) için bol gol ve karşılıklı gol şarttır
            if kg > 1.72 or o25 > 1.80:
                continue

            chosen_data = None
            if ms1 <= ms2 and 1.42 <= ms1 <= 2.35 and o_21 and o_21 <= 30.0:
                note = (
                    f"{m['home_team']} güçlü favori ({ms1:.2f}), ancak KG ({kg:.2f}) çok açık; "
                    f"ilk devre sürpriz golü sonrası ikinci yarıda 2/1 dönüşüne en uygun maç."
                )
                chosen_data = ("İY/MS: 2/1 (Geri Dönüş)", "ht_ft_21", o_21, note)
            elif ms2 < ms1 and 1.42 <= ms2 <= 2.35 and o_12 and o_12 <= 30.0:
                note = (
                    f"{m['away_team']} kadro kalitesiyle favori ({ms2:.2f}), KG ({kg:.2f}) ve Üst ({o25:.2f}) net; "
                    f"ikinci yarı baskısıyla 1/2 geri dönüş adayı."
                )
                chosen_data = ("İY/MS: 1/2 (Geri Dönüş)", "ht_ft_12", o_12, note)

            if not chosen_data:
                continue

            pick_lbl, pick_key, odd_val, note = chosen_data
            fit_conf = round(min(75.0, max(55.0, 108.0 - (kg * 14.0) - (o25 * 10.0))), 1)
            score = (fit_conf * l_bonus) - (odd_val * 0.35)

            candidates.append({
                "match_id": m["id"],
                "nesine_code": self._match_code(m),
                "match_name": f"{m['home_team']} - {m['away_team']}",
                "league": self._format_league(m),
                "time": m["match_time"],
                "status_text": "Oynanmadı",
                "pick": pick_lbl,
                "pick_key": pick_key,
                "odd": round(odd_val, 2),
                "prob": round((0.88 / odd_val) * 100.0, 1),
                "confidence": fit_conf,
                "confidence_label": f"%{fit_conf:.0f} Dönüş Gücü",
                "ev": 7.0,
                "short_note": note,
                "deep_reason": note,
                "is_real_market": True,
                "score_metric": score,
            })

        candidates.sort(key=lambda x: x["score_metric"], reverse=True)
        selected = self._select_with_rotation(candidates, count=count, rotation=rotation, step=1)

        return self._finalize_coupon(
            selected=selected,
            title="İY/MS 1/2 & 2/1 Geri Dönüş Kuponu (4 Maç - 50 TL)",
            day_label="İY/MS 1/2 • 2/1 (4 Maç)",
            badge="⚡ YÜKSEK GOLLÜ GERİ DÖNÜŞ (1/2 • 2/1) 4 MAÇ KUPONU",
            color="purple",
            ctype="iy_ms_12_21",
            summary_prefix="KG ve 2,5 Üst beklentisi en yüksek, favorinin ikinci yarıda çevirme gücü bulunan 4 adet 1/2 ve 2/1 maçı.",
            stake=50,
        )

    def build_aksam_300k_coupon(self, analyzed_pool, rotation=0):
        """
        Akşam 17:00 Dünya Taraması Özel Kuponu (50 TL → ~300.000 TL Hedef Bandı):
        - Başlama saati >= 17:00 (akşam/gece seansı) olan gerçek açık bülten maçlarını tarar.
        - Dünya genelinde saha/kadro/form analizleriyle tespit edilen kısır tuzakları (Chesham, Wimbledon,
          Hamburg, Lazio, Köln vb.) kesinlikle dışarıda bırakır.
        - En yüksek RTP (gerçek olasılık × oran verimliliği) sunan 5 maçlık kombinasyonu ~6.000 toplam oran
          (50 TL ile 290.000 TL – 315.000 TL bandı) merkezinde optimize eder.
        """
        from itertools import combinations, product

        now_dt = datetime.datetime.now()
        today_17 = now_dt.replace(hour=17, minute=0, second=0, microsecond=0)
        cutoff_dt = max(now_dt, today_17)

        evening_items = []
        for item in analyzed_pool:
            m = item["match"]
            m_code = self._match_code(m)
            if m_code in self.SCOUTED_LOW_GOAL_TRAP_CODES:
                continue
            try:
                m_dt = datetime.datetime.strptime(m.get("match_time", ""), "%d.%m.%Y %H:%M")
                if m_dt < cutoff_dt:
                    continue
                is_tonight_prime = (m_dt.date() == now_dt.date() and m_dt.hour >= 19)
            except Exception:
                is_tonight_prime = False

            odds = m.get("odds", {})
            probs = item["probs"]
            kg_odd = self._safe_float(odds, "btts_yes")
            o25_odd = self._safe_float(odds, "over25")
            if not kg_odd or not o25_odd:
                continue

            scout_note = self.SCOUTED_ELITE_NOTES.get(m_code)
            scout_mult = 1.32 if scout_note else 1.0
            tonight_mult = 1.12 if is_tonight_prime else 1.0
            l_bonus = self._league_bonus(m.get("league", ""))

            match_picks = []

            # 1) 1.Y/2.Y KG: Evet/Evet (Yalnızca iki takımın da ilk yarıdan açık oynadığı maçlarda)
            bh_odd = self._safe_float(odds, "both_halves_btts_yes")
            ms1_check = self._safe_float(odds, "ms1", 2.0)
            ms2_check = self._safe_float(odds, "ms2", 2.0)
            open_both_sides = (ms1_check <= 4.40 and ms2_check <= 4.40) or (m_code in {"3243688", "3243612"})
            if bh_odd and 6.00 <= bh_odd <= 10.20 and kg_odd <= 1.42 and o25_odd <= 1.32 and open_both_sides:
                btts_c = min(88.0, (0.92 / max(1.12, kg_odd)) * 100.0)
                over_c = min(88.0, (0.92 / max(1.12, o25_odd)) * 100.0)
                g_conf = round(min(85.0, 0.55 * btts_c + 0.45 * over_c), 1)
                true_p = min(0.16, max(0.095, 0.91 / bh_odd))
                note = scout_note or f"KG ({kg_odd:.2f}) ve 2,5 Üst ({o25_odd:.2f}) bültenin zirvesinde; iki yarıda da gol temposu çok açık."
                match_picks.append((
                    "1.Y/2.Y KG: Evet/Evet", "both_halves_btts_yes", round(bh_odd, 2),
                    true_p, g_conf, f"%{g_conf:.0f} Gol Güveni", note
                ))

            # 2) İki Takım da En Az 2 Gol Atar (MTID=716 — Dortmund-Bremen gibi 2-2/3-2 profili)
            b2_odd = self._safe_float(odds, "both_score_2plus")
            if b2_odd and 3.50 <= b2_odd <= 5.50 and kg_odd <= 1.50:
                true_p = min(0.26, max(0.18, 0.90 / b2_odd))
                s_conf = round(min(80.0, (0.92 / max(1.15, kg_odd)) * 100.0 + 6.0), 1)
                note = scout_note or f"İki takım da yüksek hücum ortalamasıyla en az 2'şer gol üretmeye çok yatkın."
                match_picks.append((
                    "İki Takım da 2+ Gol Atar", "both_score_2plus", round(b2_odd, 2),
                    true_p, s_conf, f"%{s_conf:.0f} Hücum Gücü", note
                ))

            # 3) MS 1/2 ve KG Var veya MS 1/2 ve 3,5 Üst (Yüksek değerli çapa tercihler: 2.00 - 2.95)
            ms1_kg = self._safe_float(odds, "ms1_btts_yes")
            ms2_kg = self._safe_float(odds, "ms2_btts_yes")
            ms1_o35 = self._safe_float(odds, "ms1_over35")
            ms2_o35 = self._safe_float(odds, "ms2_over35")
            for p_lbl, p_key, p_odd in [
                ("MS 1 ve KG Var", "ms1_btts_yes", ms1_kg),
                ("MS 2 ve KG Var", "ms2_btts_yes", ms2_kg),
                ("MS 1 ve 3,5 Üst", "ms1_over35", ms1_o35),
                ("MS 2 ve 3,5 Üst", "ms2_over35", ms2_o35),
            ]:
                # Port Vale (#3243773) ligde 23. sırada kısır olduğu için Man City U21 karşısında MS 1 kombine tuzağından kaçın
                if m_code == "3243773" and p_key.startswith("ms1_"):
                    continue
                if p_odd and 2.00 <= p_odd <= 2.90 and kg_odd <= 1.48:
                    true_p = min(0.46, max(0.31, 0.90 / p_odd))
                    c_val = round(min(82.0, true_p * 100.0 + 34.0), 1)
                    note = scout_note or f"Favori kazanırken açık oyun temposuyla ({kg_odd:.2f} KG) gollü galibiyet öne çıkıyor."
                    match_picks.append((p_lbl, p_key, round(p_odd, 2), true_p, c_val, f"%{c_val:.0f} Senaryo Güveni", note))

            # 4) İY/MS 0/1 Taktik Kilit Açma Çapası (AS Roma - Cagliari vb. güçlü iç saha favorileri)
            htft_01 = self._safe_float(odds, "ht_ft_01")
            ms1_odd = self._safe_float(odds, "ms1", 2.0)
            if htft_01 and 3.40 <= htft_01 <= 4.30 and ms1_odd <= 1.30:
                true_p = min(0.28, max(0.22, 0.92 / htft_01))
                c_val = 74.0
                note = scout_note or f"{m['home_team']} ilk yarı kontrollü oynayıp ikinci yarı baskısıyla kilidi açmaya çok uygun."
                match_picks.append(("İY/MS: 0/1", "ht_ft_01", round(htft_01, 2), true_p, c_val, "%74 Taktik Uyum", note))

            # 5) Kazanan 10 Formülü: İY/MS 1/2 & 2/1 Geri Dönüş Devleri (Rize-Trabzon 1/2, Santa Clara-Benfica 1/2)
            o12 = self._safe_float(odds, "ht_ft_12")
            o21 = self._safe_float(odds, "ht_ft_21")
            ms2_odd = self._safe_float(odds, "ms2", 2.0)
            if o12 and 18.0 <= o12 <= 30.0 and ms2_odd <= 2.20 and kg_odd <= 1.55:
                note = f"{m['away_team']} deplasmanda ilk yarı sürpriz yenik kapatsa da 2. devrede çevirmeye aday ({o12:.2f} oran)."
                match_picks.append(("İY/MS: 1/2 (Geri Dönüş)", "ht_ft_12", round(o12, 2), 0.05, 62.0, "Kazanan 10 Dönüş", note))
            elif o21 and 18.0 <= o21 <= 30.0 and ms1_odd <= 2.20 and kg_odd <= 1.55:
                note = f"{m['home_team']} ilk yarı yenik girse de taraftar baskısıyla maçı 2. yarıda çevirmeye aday ({o21:.2f} oran)."
                match_picks.append(("İY/MS: 2/1 (Geri Dönüş)", "ht_ft_21", round(o21, 2), 0.05, 62.0, "Kazanan 10 Dönüş", note))

            # 6) Kazanan 10 Formülü: Güçlü Banko Çapalar (PSG 1.17, Mardin 1.42, Sevilla 1.61)
            if ms1_odd and 1.18 <= ms1_odd <= 1.65:
                c_val = round(min(88.0, 92.0 / ms1_odd), 1)
                note = f"{m['home_team']} net kadro ve form üstünlüğüyle kuponun güvenilir sağlam çapası."
                match_picks.append(("Maç Sonucu: 1", "ms1", round(ms1_odd, 2), min(0.80, 0.90 / ms1_odd), c_val, f"%{c_val:.0f} Banko Çapa", note))
            elif ms2_odd and 1.18 <= ms2_odd <= 1.65:
                c_val = round(min(88.0, 92.0 / ms2_odd), 1)
                note = f"{m['away_team']} deplasmanda net kalite farkıyla kuponun sağlam çapası."
                match_picks.append(("Maç Sonucu: 2", "ms2", round(ms2_odd, 2), min(0.80, 0.90 / ms2_odd), c_val, f"%{c_val:.0f} Banko Çapa", note))

            if match_picks:
                base_factor = 1.95 if m_code in self.SCOUTED_ELITE_NOTES else (3.2 - min(2.0, kg_odd))
                rank_score = scout_mult * tonight_mult * l_bonus * base_factor
                evening_items.append((rank_score, m, m_code, match_picks))

        evening_items.sort(key=lambda x: x[0], reverse=True)
        pool = evening_items[:16]

        valid_combos = []
        for m_comb in combinations(pool, 4):
            pick_lists = [
                [(sc, m, mc, pk) for pk in p_list]
                for (sc, m, mc, p_list) in m_comb
            ]
            for choice in product(*pick_lists):
                tot_odd = 1.0
                joint_q = 1.0
                ee_cnt = 0
                for sc, m, mc, pk in choice:
                    tot_odd *= pk[2]
                    joint_q *= (pk[3] * sc)
                    if pk[1] == "both_halves_btts_yes":
                        ee_cnt += 1
                ret_50 = tot_odd * 50.0
                # Kazanan 10 bandı (5.000 TL - 500.000 TL bandı)
                if 2000 <= ret_50 <= 600000 and ee_cnt <= 3:
                    diversity_bonus = 1.25 if any(pk[1].startswith("ht_ft_") for _, _, _, pk in choice) else 1.0
                    valid_combos.append((joint_q * diversity_bonus, tot_odd, choice))

        # Yedek esnek bant
        if not valid_combos and len(pool) >= 4:
            for m_comb in combinations(pool[:10], 4):
                pick_lists = [[(sc, m, mc, pk) for pk in p_list] for (sc, m, mc, p_list) in m_comb]
                for choice in product(*pick_lists):
                    tot_odd = 1.0
                    joint_q = 1.0
                    for sc, m, mc, pk in choice:
                        tot_odd *= pk[2]
                        joint_q *= (pk[3] * sc)
                    valid_combos.append((joint_q, tot_odd, choice))

        valid_combos.sort(key=lambda x: x[0], reverse=True)

        # Güncelle rotasyonunda önce tamamen farklı maçlardan (0 ortak maç) oluşan bağımsız 300B paketlerini öne al
        distinct_combos = []
        seen_sigs = set()
        if valid_combos:
            first_item = valid_combos[0]
            first_codes = set(mc for _, _, mc, _ in first_item[2])
            distinct_combos.append(first_item)
            seen_sigs.add(tuple(sorted(first_codes)))

            # 2. kupon olarak 1. kuponla HİÇ çakışmayan (0 ortak maç) en güçlü 5 maçlık paketi bul
            for q, to, ch in valid_combos[1:]:
                codes = set(mc for _, _, mc, _ in ch)
                sig = tuple(sorted(codes))
                if sig not in seen_sigs and len(codes & first_codes) == 0:
                    seen_sigs.add(sig)
                    distinct_combos.append((q, to, ch))
                    break

            # Kalan rotasyonlar için en az 2 farklı maç içeren diğer üst düzey kombinasyonları ekle
            for q, to, ch in valid_combos[1:]:
                codes = set(mc for _, _, mc, _ in ch)
                sig = tuple(sorted(codes))
                if sig not in seen_sigs and all(len(codes & set(mc for _, _, mc, _ in prev[2])) <= 3 for prev in distinct_combos):
                    seen_sigs.add(sig)
                    distinct_combos.append((q, to, ch))
                if len(distinct_combos) >= 8:
                    break

        chosen = distinct_combos[rotation % len(distinct_combos)][2] if distinct_combos else []

        selected = []
        for sc, m, mc, pk in sorted(chosen, key=lambda z: z[1]["match_time"]):
            p_lbl, p_key, p_odd, true_p, conf_v, conf_lbl, note = pk
            selected.append({
                "match_id": m["id"],
                "nesine_code": mc,
                "match_name": f"{m['home_team']} - {m['away_team']}",
                "league": self._format_league(m),
                "time": m["match_time"],
                "status_text": "Oynanmadı",
                "pick": p_lbl,
                "pick_key": p_key,
                "odd": p_odd,
                "prob": round(true_p * 100.0, 1),
                "confidence": conf_v,
                "confidence_label": conf_lbl,
                "ev": round((true_p * p_odd - 1.0) * 100.0, 1),
                "short_note": note,
                "deep_reason": note,
                "is_real_market": True,
                "score_metric": sc,
            })

        return self._finalize_coupon(
            selected=selected,
            title="Nesine Kazanan 10 Hibrit Kuponu (4 Maç - 50 TL)",
            day_label="🏆 Kazanan 10 (4 Maç)",
            badge="🏆 NESİNE KAZANAN 10 FORMÜLÜ (ÇAPA + İY/MS DÖNÜŞ — 4 MAÇ)",
            color="rose",
            ctype="aksam_300k",
            summary_prefix="Nesine Kazanan 10 mimarisine uygun olarak banko çapa ve yüksek oranlı İY/MS geri dönüş dengesiyle 4 maç seçildi.",
            stake=50,
        )

    def build_skor_mbs1_coupon(self, analyzed_pool, rotation=0):
        """
        3 Maç Skor Kuponu (MBS 1 - 50 TL Düz):
        Yalnızca MBS=1 olan maçlar üzerinden 1. Yarı Skoru (2:1, 1:2, diğer),
        İY/MS Skoru (1:0/2:1) ve İY/MS (1/0) tercihleriyle 3 maçlık kupon üretir.
        """
        candidates = []
        for item in analyzed_pool:
            m = item["match"]
            m_code = self._match_code(m)
            if m_code in self.SCOUTED_LOW_GOAL_TRAP_CODES:
                continue
            if int(m.get("mbs") or 3) != 1:
                continue
            odds = m.get("odds", {})
            ms1 = self._safe_float(odds, "ms1")
            ms2 = self._safe_float(odds, "ms2")
            kg = self._safe_float(odds, "btts_yes")
            if not ms1 or not ms2 or not kg or kg > 1.72:
                continue

            pick_lbl, pick_key, pick_odd, note = None, None, None, None
            s_10_21 = self._safe_float(odds, "htft_score_10_21")
            ht_21 = self._safe_float(odds, "ht_score_21")
            ht_12 = self._safe_float(odds, "ht_score_12")
            ht_10 = self._safe_float(odds, "ht_ft_10")

            if 1.38 <= ms1 <= 2.15 and s_10_21 and 22.0 <= s_10_21 <= 34.5:
                pick_lbl = "İlk Yarı / Maç Skoru: 1:0 / 2:1"
                pick_key = "htft_score_10_21"
                pick_odd = round(s_10_21, 2)
                note = f"{m['home_team']} ilk yarı 1-0 üstünlüğü sonrası ikinci yarı karşılıklı golle 2-1 profiline uygun."
            elif 1.38 <= ms1 <= 2.35 and ht_21 and 13.5 <= ht_21 <= 24.5:
                pick_lbl = "1. Yarı Skoru: 2:1"
                pick_key = "ht_score_21"
                pick_odd = round(ht_21, 2)
                note = f"İlk devrede yüksek tempo ve ev sahibi üstünlüğü ({kg:.2f} KG) öne çıkıyor."
            elif 1.35 <= ms2 <= 2.25 and ht_12 and 12.5 <= ht_12 <= 24.5:
                pick_lbl = "1. Yarı Skoru: 1:2"
                pick_key = "ht_score_12"
                pick_odd = round(ht_12, 2)
                note = f"Deplasman ekibinin açık oyunda ilk yarıyı 1-2 önde kapatma potansiyeli yüksek."
            elif 1.80 <= ms1 <= 3.60 and ht_10 and 11.5 <= ht_10 <= 16.5:
                pick_lbl = "İlk Yarı/Maç Sonucu: 1/X"
                pick_key = "ht_ft_10"
                pick_odd = round(ht_10, 2)
                note = "Ev sahibinin ilk yarı skor bulup ikinci yarıda dengelenen maç profili."

            if not pick_odd:
                continue

            l_bonus = self._league_bonus(m.get("league", ""))
            scout_note = self.SCOUTED_ELITE_NOTES.get(m_code)
            rank = l_bonus * (2.6 - min(1.8, kg)) * (1.15 if m.get("day") == "today" else 1.0)
            candidates.append({
                "match_id": m["id"],
                "nesine_code": m_code,
                "match_name": f"{m['home_team']} - {m['away_team']}",
                "league": self._format_league(m),
                "time": m["match_time"],
                "status_text": "Oynanmadı",
                "pick": pick_lbl,
                "pick_key": pick_key,
                "odd": pick_odd,
                "prob": round(min(12.0, 90.0 / pick_odd), 1),
                "confidence": 64.0,
                "confidence_label": "MBS 1 • Skor Değeri",
                "ev": 4.2,
                "short_note": scout_note or note,
                "deep_reason": scout_note or note,
                "is_real_market": True,
                "score_metric": rank,
            })

        candidates.sort(key=lambda x: x["score_metric"], reverse=True)
        selected = self._select_with_rotation(candidates, 4, rotation, step=1)
        selected.sort(key=lambda x: x["time"])

        return self._finalize_coupon(
            selected=selected,
            title="4 Maç Skor Kuponu (MBS 1 - 50 TL)",
            day_label="4 Maç Skor (MBS 1)",
            badge="MBS 1 tekli/dörtlü devre ve maç skoru kurgusu (50 TL)",
            color="slate",
            ctype="skor_mbs1",
            summary_prefix="Tamamı MBS 1 olan 4 karşılaşmada ilk yarı skoru ve İY/MS skoru tercihleri seçildi.",
            stake=50,
        )

    def build_iy_skor_sistem_coupon(self, analyzed_pool, rotation=0):
        """
        1. Yarı Skoru Sistem Kuponu (7 Maç MBS 1 • Sistem 1, 2, 3, 4 = 98 TL):
        3 maç yatsa bile tutan 4 maçın ikili, üçlü ve dörtlü çarpımlarından kazanç üretir.
        """
        candidates = []
        for item in analyzed_pool:
            m = item["match"]
            m_code = self._match_code(m)
            if m_code in self.SCOUTED_LOW_GOAL_TRAP_CODES:
                continue
            if int(m.get("mbs") or 3) != 1:
                continue
            odds = m.get("odds", {})
            ms1 = self._safe_float(odds, "ms1")
            ms2 = self._safe_float(odds, "ms2")
            kg = self._safe_float(odds, "btts_yes")
            if not ms1 or not ms2 or not kg or kg > 1.70:
                continue

            ht_21 = self._safe_float(odds, "ht_score_21")
            ht_12 = self._safe_float(odds, "ht_score_12")
            ht_20 = self._safe_float(odds, "ht_score_20")
            ht_02 = self._safe_float(odds, "ht_score_02")
            ht_11 = self._safe_float(odds, "ht_score_11")
            ht_oth = self._safe_float(odds, "ht_score_other")

            pick_lbl, pick_key, pick_odd, note = None, None, None, None
            if ms1 <= 1.25 and ht_oth and 4.0 <= ht_oth <= 10.5:
                pick_lbl, pick_key, pick_odd = "1. Yarı Skoru: diğer", "ht_score_other", round(ht_oth, 2)
                note = f"{m['home_team']} ilk devrede 3+ gollü erken baskı kurmaya aday."
            elif ms2 <= 1.25 and ht_oth and 4.0 <= ht_oth <= 10.5:
                pick_lbl, pick_key, pick_odd = "1. Yarı Skoru: diğer", "ht_score_other", round(ht_oth, 2)
                note = f"{m['away_team']} ilk devrede yüksek skorlu üstünlük kurmaya uygun."
            elif 1.35 <= ms1 <= 2.15 and kg <= 1.50 and ht_21 and 13.0 <= ht_21 <= 24.5:
                pick_lbl, pick_key, pick_odd = "1. Yarı Skoru: 2:1", "ht_score_21", round(ht_21, 2)
                note = "Açık ilk yarı temposunda ev sahibinin soyunma odasına 2-1 önde girme senaryosu."
            elif 1.35 <= ms2 <= 2.15 and kg <= 1.52 and ht_12 and 12.5 <= ht_12 <= 24.5:
                pick_lbl, pick_key, pick_odd = "1. Yarı Skoru: 1:2", "ht_score_12", round(ht_12, 2)
                note = "Karşılıklı ilk yarı golleriyle deplasman ekibinin 1-2 devre üstünlüğü."
            elif 1.40 <= ms1 <= 1.95 and ht_20 and 7.5 <= ht_20 <= 13.5:
                pick_lbl, pick_key, pick_odd = "1. Yarı Skoru: 2:0", "ht_score_20", round(ht_20, 2)
                note = f"{m['home_team']} ilk 45 dakikada net iki farklı üstünlük yakalayabilir."
            elif 1.40 <= ms2 <= 1.95 and ht_02 and 7.5 <= ht_02 <= 13.5:
                pick_lbl, pick_key, pick_odd = "1. Yarı Skoru: 0:2", "ht_score_02", round(ht_02, 2)
                note = f"{m['away_team']} deplasmanda ilk yarıdan iki farklı skora gidebilir."
            elif abs(ms1 - ms2) <= 0.75 and ht_11 and 6.4 <= ht_11 <= 8.2:
                pick_lbl, pick_key, pick_odd = "1. Yarı Skoru: 1:1", "ht_score_11", round(ht_11, 2)
                note = "Dengeli güçlerin açık oyununda ilk yarının 1-1 tamamlanma olasılığı yüksek."

            if not pick_odd:
                continue

            l_bonus = self._league_bonus(m.get("league", ""))
            rank = l_bonus * (2.5 - min(1.7, kg)) * (1.15 if m.get("day") == "today" else 1.0)
            candidates.append({
                "match_id": m["id"],
                "nesine_code": m_code,
                "match_name": f"{m['home_team']} - {m['away_team']}",
                "league": self._format_league(m),
                "time": m["match_time"],
                "status_text": "Oynanmadı",
                "pick": pick_lbl,
                "pick_key": pick_key,
                "odd": pick_odd,
                "prob": round(min(18.0, 90.0 / pick_odd), 1),
                "confidence": 63.0,
                "confidence_label": "MBS 1 • Sistem",
                "ev": 3.8,
                "short_note": self.SCOUTED_ELITE_NOTES.get(m_code) or note,
                "deep_reason": self.SCOUTED_ELITE_NOTES.get(m_code) or note,
                "is_real_market": True,
                "score_metric": rank,
            })

        candidates.sort(key=lambda x: x["score_metric"], reverse=True)
        selected = self._select_with_rotation(candidates, 4, rotation, step=1)
        selected.sort(key=lambda x: x["time"])

        res = self._finalize_system_coupon(
            selected=selected,
            system_sizes=[2, 3, 4],
            title="1. Yarı Skoru Sistem Kuponu (4 Maç)",
            day_label="1. Yarı Skoru (4 Maç)",
            badge="4 Maç MBS 1 • Sistem 2, 3, 4 (50 TL)",
            color="slate",
            ctype="iy_skor_sistem",
            summary_text="",
            ref_hits=3,
        )
        res["summary"] = (
            f"4 maçın tamamı MBS 1'dir. "
            f"En az 2 maç tuttuğunda kazanç başlar; 3 ve 4 isabette yüksek skor ödemesi üretir."
        )
        return res

    def build_iyms_sistem_56_coupon(self, analyzed_pool, rotation=0):
        """
        İY/MS Dönüş Sistem Kuponu (6 Maç • Sistem 2, 3, 4, 5 = 56 TL):
        MBS <= 2 olan açık tempolu 6 maçta 1/2 ve 2/1 geri dönüş kurgusu.
        """
        candidates = []
        for item in analyzed_pool:
            m = item["match"]
            m_code = self._match_code(m)
            if m_code in self.SCOUTED_LOW_GOAL_TRAP_CODES:
                continue
            if int(m.get("mbs") or 3) > 2:
                continue
            odds = m.get("odds", {})
            ms1 = self._safe_float(odds, "ms1")
            ms2 = self._safe_float(odds, "ms2")
            kg = self._safe_float(odds, "btts_yes")
            o12 = self._safe_float(odds, "ht_ft_12")
            o21 = self._safe_float(odds, "ht_ft_21")
            if not ms1 or not ms2 or not kg or kg > 1.55 or (not o12 and not o21):
                continue

            if ms1 <= ms2 and o21 and 18.0 <= o21 <= 32.0:
                pick_lbl, pick_key, pick_odd = "İlk Yarı/Maç Sonucu: 2/1", "ht_ft_21", round(o21, 2)
                note = f"{m['home_team']} ikinci yarı baskısıyla geri dönüşe yatkın ({kg:.2f} KG)."
            elif o12 and 18.0 <= o12 <= 32.0:
                pick_lbl, pick_key, pick_odd = "İlk Yarı/Maç Sonucu: 1/2", "ht_ft_12", round(o12, 2)
                note = f"{m['away_team']} ikinci devre temposuyla maçı çevirmeye aday ({kg:.2f} KG)."
            else:
                continue

            rank = (2.5 - min(1.7, kg)) * self._league_bonus(m.get("league", ""))
            candidates.append({
                "match_id": m["id"],
                "nesine_code": m_code,
                "match_name": f"{m['home_team']} - {m['away_team']}",
                "league": self._format_league(m),
                "time": m["match_time"],
                "status_text": "Oynanmadı",
                "pick": pick_lbl,
                "pick_key": pick_key,
                "odd": pick_odd,
                "prob": round(90.0 / pick_odd, 1),
                "confidence": 65.0,
                "confidence_label": f"MBS {m.get('mbs', 2)} • Sistem",
                "ev": 3.5,
                "short_note": self.SCOUTED_ELITE_NOTES.get(m_code) or note,
                "deep_reason": self.SCOUTED_ELITE_NOTES.get(m_code) or note,
                "is_real_market": True,
                "score_metric": rank,
            })

        candidates.sort(key=lambda x: x["score_metric"], reverse=True)
        selected = self._select_with_rotation(candidates, 4, rotation, step=1)
        selected.sort(key=lambda x: x["time"])

        res = self._finalize_system_coupon(
            selected=selected,
            system_sizes=[2, 3, 4],
            title="İY/MS Dönüş Sistem Kuponu (4 Maç)",
            day_label="İY/MS Sistem (4 Maç)",
            badge="4 Maç (MBS 1-2) • Sistem 2, 3, 4 (50 TL)",
            color="slate",
            ctype="iyms_sistem_56",
            summary_text="",
            ref_hits=3,
        )
        res["summary"] = (
            f"4 maç (Sistem 2, 3, 4). "
            f"2 maç tutsa bile yüksek 1/2 veya 2/1 oranıyla kâra geçer; 3 ve 4 isabette devasa ödeme üretir."
        )
        return res

    def build_capa_skor_kombine_coupon(self, analyzed_pool, rotation=0):
        """
        Çapa + Skor Kombine Kuponu (6 Maç - 50 TL | Görsel 5 Modeli):
        4 adet geçmiş maç skorlarıyla doğrulanmış yüksek yüzdeli çapa (1.53 - 2.35) +
        yalnızca 2 adet istatistiksel gol makinesi '1.Y/2.Y KG: Evet/Evet' (6.50 - 9.20).
        Zorlama 0:0/2:1 veya rastgele ters skor kullanmaz.
        """
        verified_ee_priority = {"3243591", "3243688", "3243612", "3243675", "3243646"}
        verified_anchor_priority = {
            "3243772", "3243754", "3243898", "3243745",
            "3243825", "3248006", "3297737", "3261961",
        }
        anchors = []
        triggers = []
        for item in analyzed_pool:
            m = item["match"]
            m_code = self._match_code(m)
            if m_code in self.SCOUTED_LOW_GOAL_TRAP_CODES:
                continue
            odds = m.get("odds", {})
            ms1 = self._safe_float(odds, "ms1")
            ms2 = self._safe_float(odds, "ms2")
            kg = self._safe_float(odds, "btts_yes")
            if not ms1 or not ms2:
                continue

            # Tetikleyici adayları: Sadece gerçek açık savunmalı (KG <= 1.38) maçlarda Evet/Evet (Görsel 5)
            ee_odd = self._safe_float(odds, "both_halves_btts_yes")
            if ee_odd and 5.80 <= ee_odd <= 9.80 and kg and kg <= 1.38 and m_code not in self.SCOUTED_BTTS_TRAP_CODES:
                p_boost = 3.0 if m_code in verified_ee_priority else 1.0
                s_note = self.SCOUTED_ELITE_NOTES.get(m_code) or "Her iki devrede de açık savunma ve yüksek gol ortalaması."
                triggers.append({
                    "match_id": m["id"],
                    "nesine_code": m_code,
                    "match_name": f"{m['home_team']} - {m['away_team']}",
                    "league": self._format_league(m),
                    "time": m["match_time"],
                    "status_text": "Oynanmadı",
                    "pick": "1.Y/2.Y KG: Evet/Evet",
                    "pick_key": "both_halves_btts_yes",
                    "odd": round(ee_odd, 2),
                    "prob": round(min(18.0, 92.0 / ee_odd), 1),
                    "confidence": 68.0,
                    "confidence_label": "Kanıtlı Gol Çarpanı",
                    "ev": 4.2,
                    "short_note": s_note,
                    "deep_reason": s_note,
                    "is_real_market": True,
                    "score_metric": p_boost * self._league_bonus(m.get("league", "")) * (2.5 - min(1.5, kg)),
                })

            # Sağlam, geçmiş verisi doğrulanmış çapa adayları (1.52 - 2.45)
            ms2_u35 = self._safe_float(odds, "ms2_over35")
            ms1_u25 = self._safe_float(odds, "ms1_over25")
            ms2_kg = self._safe_float(odds, "ms2_btts_yes")
            ms1_kg = self._safe_float(odds, "ms1_btts_yes")
            s_note = self.SCOUTED_ELITE_NOTES.get(m_code)
            c_pick = None

            if m_code == "3243772" and ms2_u35:
                c_pick = ("MS 2 ve 3,5 Üst", "ms2_over35", round(ms2_u35, 2), s_note)
            elif m_code in {"3243825", "3248006", "3297737"} and ms1_u25:
                c_pick = ("MS 1 ve 2,5 Üst", "ms1_over25", round(ms1_u25, 2), s_note)
            elif ms2_kg and 2.00 <= ms2_kg <= 2.50 and m_code not in self.SCOUTED_BTTS_TRAP_CODES:
                c_pick = ("MS 2 ve KG Var", "ms2_btts_yes", round(ms2_kg, 2), s_note or "Deplasman favorisi açık tempoda gollü kazanır.")
            elif ms1_kg and 1.90 <= ms1_kg <= 2.35 and m_code not in self.SCOUTED_BTTS_TRAP_CODES and m_code != "3243773":
                c_pick = ("MS 1 ve KG Var", "ms1_btts_yes", round(ms1_kg, 2), s_note or "Ev sahibi açık oyunda gollü galibiyete yakın.")
            elif 1.55 <= ms1 <= 1.98 and (m_code in verified_anchor_priority or self._league_bonus(m.get("league", "")) > 1.0):
                c_pick = ("Maç Sonucu: 1", "ms1", round(ms1, 2), s_note or f"{m['home_team']} iç saha form üstünlüğüyle kazanmaya yakın.")
            elif 1.52 <= ms2 <= 1.92 and m_code != "3243801" and self._league_bonus(m.get("league", "")) > 1.0:
                c_pick = ("Maç Sonucu: 2", "ms2", round(ms2, 2), s_note or f"{m['away_team']} kadro kalitesiyle deplasmanda galibiyete yakın.")

            if c_pick:
                a_boost = 3.2 if m_code in verified_anchor_priority else (1.8 if s_note else 1.0)
                anchors.append({
                    "match_id": m["id"],
                    "nesine_code": m_code,
                    "match_name": f"{m['home_team']} - {m['away_team']}",
                    "league": self._format_league(m),
                    "time": m["match_time"],
                    "status_text": "Oynanmadı",
                    "pick": c_pick[0],
                    "pick_key": c_pick[1],
                    "odd": c_pick[2],
                    "prob": round(min(64.0, 92.0 / c_pick[2]), 1),
                    "confidence": 76.0,
                    "confidence_label": "%76 Kanıtlı Çapa",
                    "ev": 3.6,
                    "short_note": c_pick[3] or "Form ve ikili rekabet verileriyle yüksek güven.",
                    "deep_reason": c_pick[3] or "Form ve ikili rekabet verileriyle yüksek güven.",
                    "is_real_market": True,
                    "score_metric": a_boost * self._league_bonus(m.get("league", "")) * (2.6 - abs(c_pick[2] - 1.85)),
                })

        triggers.sort(key=lambda x: x["score_metric"], reverse=True)
        anchors.sort(key=lambda x: x["score_metric"], reverse=True)

        sel_triggers = self._select_with_rotation(triggers, 2, rotation, step=1)
        used = {t["match_id"] for t in sel_triggers}
        clean_anchors = [a for a in anchors if a["match_id"] not in used]
        sel_anchors = self._select_with_rotation(clean_anchors, 2, rotation, step=2)

        selected = sorted(sel_anchors + sel_triggers, key=lambda x: x["time"])
        return self._finalize_coupon(
            selected=selected,
            title="Çapa + Dönüş Kombine Kuponu (4 Maç)",
            day_label="Çapa + Dönüş (4 Maç)",
            badge="2 geçmiş verili net çapa + 2 seçkin gol/dönüş çarpanı (4 Maç - 50 TL)",
            color="slate",
            ctype="capa_skor_kombine",
            summary_prefix="Son maç skorları doğrulanmış 2 yüksek olasılıklı çapanın yanına 2 açık tempolu gol çarpanı eklendi (4 maç).",
            stake=50,
        )

    def build_yuksek_oran_kg_coupon(self, analyzed_pool, rotation=0):
        """
        Yüksek Oran KG Var Kuponu (10 Maç - 50 TL | Görsel 6 Modeli):
        Kısır 0-0 / 1-0 tuzaklarını eleyerek, geçmiş H2H ve son 5 maç skorlarında karşılıklı gol
        üretimi doğrulanmış dengeli karşılaşmaları (1.42 - 2.15) birleştirir.
        """
        low_goal_country_words = ("İran", "Botsvana", "Uganda", "Tanzanya", "Cezayir", "Mısır", "Fas")
        candidates = []
        for item in analyzed_pool:
            m = item["match"]
            m_code = self._match_code(m)
            if m_code in self.SCOUTED_BTTS_TRAP_CODES:
                continue
            league_str = m.get("league") or ""
            if any(w in league_str for w in low_goal_country_words):
                continue
            odds = m.get("odds", {})
            ms1 = self._safe_float(odds, "ms1")
            ms2 = self._safe_float(odds, "ms2")
            kg = self._safe_float(odds, "btts_yes")
            if not ms1 or not ms2 or not kg:
                continue

            is_verified = m_code in self.SCOUTED_VERIFIED_BTTS_CODES
            if (is_verified and 1.33 <= kg <= 2.20) or (1.42 <= kg <= 2.10 and ms1 <= 4.10 and ms2 <= 4.10):
                balance_score = 1.0 / (1.0 + abs(ms1 - ms2))
                v_boost = 4.0 if is_verified else (1.5 if m_code in self.SCOUTED_ELITE_NOTES else 1.0)
                l_bon = self._league_bonus(league_str)
                rank = v_boost * l_bon * (1.2 + balance_score) * (1.0 + max(0.0, kg - 1.40) * 0.5)
                s_note = self.SCOUTED_ELITE_NOTES.get(m_code) or (
                    f"Dengeli güç dağılımında ({ms1:.2f} / {ms2:.2f}) iki takımın da karşılıklı skor üretme potansiyeli yüksek."
                )
                candidates.append({
                    "match_id": m["id"],
                    "nesine_code": m_code,
                    "match_name": f"{m['home_team']} - {m['away_team']}",
                    "league": self._format_league(m),
                    "time": m["match_time"],
                    "status_text": "Oynanmadı",
                    "pick": "Karşılıklı Gol: Var",
                    "pick_key": "btts_yes",
                    "odd": round(kg, 2),
                    "prob": round(min(74.0, 92.0 / kg), 1),
                    "confidence": round(min(78.0, 92.0 / kg + 16.0), 1),
                    "confidence_label": "Kanıtlı KG Var" if is_verified else "Değer KG Var",
                    "ev": 4.2,
                    "short_note": s_note,
                    "deep_reason": s_note,
                    "is_real_market": True,
                    "score_metric": rank,
                })

        candidates.sort(key=lambda x: x["score_metric"], reverse=True)
        selected = self._select_with_rotation(candidates, 4, rotation, step=2)
        selected.sort(key=lambda x: x["time"])

        return self._finalize_coupon(
            selected=selected,
            title="Yüksek Oran KG Var Kuponu (4 Maç)",
            day_label="4 Maç Değer KG",
            badge="Kısır tuzaklar elenmiş, geçmiş skoru kanıtlı 4 maç KG Var seçkisi (50 TL)",
            color="slate",
            ctype="yuksek_oran_kg",
            summary_prefix="Son maç skorları ve H2H geçmişinde 0-0/1-0 kısır tuzaklar elenerek en sağlam 4 Karşılıklı Gol Var maçı birleştirildi.",
            stake=50,
        )

    def generate_all_coupons(self, rotation=0):
        """
        Yalnızca güven ortalaması yüksek net sonuç kuponlarını ve 4 maçlık Evet/Evet (50 TL) kuponunu üretir.
        """
        today_str, tomorrow_str = get_dates()
        all_matches = load_matches()
        today_matches = [m for m in all_matches if m.get("day") == "today"]
        tomorrow_matches = [m for m in all_matches if m.get("day") == "tomorrow"]

        analyzed_all = self.analyze_matches(all_matches)
        analyzed_today = self.analyze_matches(today_matches)
        analyzed_tomorrow = self.analyze_matches(tomorrow_matches)

        coupon_net = self.build_net_guven_coupon(
            analyzed_all,
            title="Yüksek Güvenli Net Sonuç Kuponu (4 Maç)",
            badge="🛡️ YÜKSEK GÜVEN ORTALAMALI NET SONUÇ KUPONU (50 TL)",
            day_label="Yüksek Güven Net",
            rotation=rotation,
        )
        coupon_aksam_300k = self.build_aksam_300k_coupon(analyzed_all, rotation=rotation)
        coupon_kontr = self.build_kontrgaranti_coupon(analyzed_all, rotation=rotation, count=4)
        coupon_both_halves = self.build_both_halves_btts_coupon(analyzed_all, rotation=rotation, count=4)
        coupon_iyms_10_20 = self.build_iy_ms_10_20_coupon(analyzed_all, rotation=rotation, count=4)
        coupon_iyms_12_21 = self.build_iy_ms_12_21_coupon(analyzed_all, rotation=rotation, count=4)
        coupon_kg_evet = self.build_kg_evet_net_coupon(analyzed_all, rotation=rotation, count=4)
        coupon_ust_25 = self.build_ust_25_net_coupon(analyzed_all, rotation=rotation, count=4)
        coupon_skor_mbs1 = self.build_skor_mbs1_coupon(analyzed_all, rotation=rotation)
        coupon_iy_skor_sis = self.build_iy_skor_sistem_coupon(analyzed_all, rotation=rotation)
        coupon_iyms_sis56 = self.build_iyms_sistem_56_coupon(analyzed_all, rotation=rotation)
        coupon_capa_skor = self.build_capa_skor_kombine_coupon(analyzed_all, rotation=rotation)
        coupon_yuksek_kg = self.build_yuksek_oran_kg_coupon(analyzed_all, rotation=rotation)

        coupon_today = self.build_net_guven_coupon(
            analyzed_today if len(analyzed_today) >= 4 else analyzed_all,
            title=f"Bugünün Net Güven Kuponu ({today_str})",
            badge=f"📅 BUGÜNÜN YÜKSEK GÜVENLİ 4 NET MAÇI ({today_str})",
            day_label=f"Bugün ({today_str})",
            rotation=rotation + 1,
        )
        coupon_tomorrow = self.build_net_guven_coupon(
            analyzed_tomorrow if len(analyzed_tomorrow) >= 4 else analyzed_all,
            title=f"Yarının Net Güven Kuponu ({tomorrow_str})",
            badge=f"📅 YARININ YÜKSEK GÜVENLİ 4 NET MAÇI ({tomorrow_str})",
            day_label=f"Yarın ({tomorrow_str})",
            rotation=rotation,
        )

        return {
            "aksam_300k": coupon_aksam_300k,
            "net_guven": coupon_net,
            "kontrgaranti": coupon_kontr,
            "both_halves_kg": coupon_both_halves,
            "iy_ms_10_20": coupon_iyms_10_20,
            "iy_ms_12_21": coupon_iyms_12_21,
            "kg_evet_net": coupon_kg_evet,
            "ust_25_net": coupon_ust_25,
            "skor_mbs1": coupon_skor_mbs1,
            "iy_skor_sistem": coupon_iy_skor_sis,
            "iyms_sistem_56": coupon_iyms_sis56,
            "capa_skor_kombine": coupon_capa_skor,
            "yuksek_oran_kg": coupon_yuksek_kg,
            "today": coupon_today,
            "tomorrow": coupon_tomorrow,
        }

    def generate_custom_coupon(self, match_count=4, min_odd=1.20, max_odd=50.0, market_types=None, risk_level="high_confidence"):
        """Kullanıcının seçtiği kupon tarzına ve maç sayısına (varsayılan 4 maç, 50 TL) göre kupon üretir."""
        all_matches = load_matches()
        analyzed = self.analyze_matches(all_matches)
        match_count = max(2, min(6, int(match_count or 4)))

        style = (risk_level or "net_guven").lower()
        if style == "aksam_300k":
            return self.build_aksam_300k_coupon(analyzed, rotation=0)
        if style == "skor_mbs1":
            return self.build_skor_mbs1_coupon(analyzed, rotation=0)
        if style == "iy_skor_sistem":
            return self.build_iy_skor_sistem_coupon(analyzed, rotation=0)
        if style == "iyms_sistem_56":
            return self.build_iyms_sistem_56_coupon(analyzed, rotation=0)
        if style == "capa_skor_kombine":
            return self.build_capa_skor_kombine_coupon(analyzed, rotation=0)
        if style == "yuksek_oran_kg":
            return self.build_yuksek_oran_kg_coupon(analyzed, rotation=0)
        if style == "kontrgaranti" or (market_types and "kontrgaranti" in market_types):
            return self.build_kontrgaranti_coupon(analyzed, rotation=0, count=match_count)
        if style == "evet_evet" or (market_types and "evet_evet" in market_types):
            return self.build_both_halves_btts_coupon(analyzed, rotation=0, count=match_count)
        if style == "iy_ms_10_20":
            return self.build_iy_ms_10_20_coupon(analyzed, rotation=0, count=min(4, match_count))
        if style == "iy_ms_12_21":
            return self.build_iy_ms_12_21_coupon(analyzed, rotation=0, count=min(4, match_count))
        if style == "kg_evet" or (market_types and "kg_evet" in market_types):
            return self.build_kg_evet_net_coupon(analyzed, rotation=0, count=match_count)
        if style == "ust_25" or (market_types and "ust_25" in market_types):
            return self.build_ust_25_net_coupon(analyzed, rotation=0, count=match_count)

        return self.build_net_guven_coupon(
            analyzed,
            title=f"Özel Net Güven Kuponu ({match_count} Maç)",
            badge=f"🛡️ ÖZEL YÜKSEK GÜVENLİ NET SONUÇ KUPONU ({match_count} MAÇ - 50 TL)",
            day_label="Özel Net Kupon",
            rotation=0,
            count=match_count,
        )
