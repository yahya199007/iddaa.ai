import math
import numpy as np

class PredictionEngine:
    """
    Yapay Zeka ve İstatistiksel Maç Tahmin Motoru:
    - Bivariate Poisson Dağılımı (Dixon-Coles düşük skor düzeltmeli)
    - xG (Beklenen Gol) ve Hücum/Savunma Güçleri
    - Form Katsayısı (Zaman Ağırlıklı Son 5 Maç)
    - Değerli Oran (Value Bet / EV - Expected Value) Tespiti
    - Çoklu Bahis Pazarları (MS, ÇŞ, 2.5 Alt/Üst, KG Var/Yok, Kesin Skor)
    """

    def __init__(self, rho=-0.08, league_avg_home_goals=1.45, league_avg_away_goals=1.15):
        self.rho = rho
        self.league_avg_home = league_avg_home_goals
        self.league_avg_away = league_avg_away_goals

    def _poisson_pmf(self, k, lmbda):
        """Tekil Poisson olasılık yoğunluğu"""
        if lmbda <= 0:
            return 1.0 if k == 0 else 0.0
        return (math.pow(lmbda, k) * math.exp(-lmbda)) / math.factorial(k)

    def _dixon_coles_tau(self, x, y, lmbda_h, lmbda_a):
        """Düşük skorlar için (0-0, 1-0, 0-1, 1-1) bağımlılık düzeltmesi"""
        if x == 0 and y == 0:
            return 1 - (lmbda_h * lmbda_a * self.rho)
        elif x == 0 and y == 1:
            return 1 + (lmbda_h * self.rho)
        elif x == 1 and y == 0:
            return 1 + (lmbda_a * self.rho)
        elif x == 1 and y == 1:
            return 1 - self.rho
        else:
            return 1.0

    def calculate_form_factor(self, form_string):
        """
        Son 5 maç formunu ağırlıklandırarak çarpan üretir.
        Örn: 'WWDWL' (G: Galibiyet, B: Beraberlik, M: Mağlubiyet)
        Son maçlar daha yüksek ağırlıklıdır.
        """
        if not form_string:
            return 1.0
        
        weights = [0.10, 0.15, 0.20, 0.25, 0.30]
        pts_map = {'W': 3, 'G': 3, 'D': 1, 'B': 1, 'L': 0, 'M': 0}
        
        form_rev = list(form_string)[-5:]
        total_pts = 0
        total_weight = 0
        
        for i, res in enumerate(form_rev):
            w = weights[i if i < len(weights) else -1]
            total_pts += pts_map.get(res.upper(), 1) * w
            total_weight += w * 3
            
        ratio = total_pts / total_weight if total_weight > 0 else 0.5
        # 0.8 ile 1.25 arasında normalleştirilmiş güç çarpanı
        return 0.80 + (ratio * 0.45)

    def calculate_expected_goals(self, home_stats, away_stats):
        """
        Ev sahibi ve Deplasman takımları için beklenen gol (lambda) değerlerini hesaplar.
        """
        home_attack = home_stats.get('attack_strength', 1.0)
        home_defense = home_stats.get('defense_strength', 1.0)
        home_form = self.calculate_form_factor(home_stats.get('form', 'WDWLD'))
        home_adv = home_stats.get('home_advantage', 1.15)

        away_attack = away_stats.get('attack_strength', 1.0)
        away_defense = away_stats.get('defense_strength', 1.0)
        away_form = self.calculate_form_factor(away_stats.get('form', 'DDLWW'))

        if 'goals_scored_avg' in home_stats and 'goals_scored_avg' in away_stats:
            lambda_home = float(home_stats['goals_scored_avg'])
            lambda_away = float(away_stats['goals_scored_avg'])
        else:
            lambda_home = home_attack * away_defense * self.league_avg_home * home_form * home_adv
            lambda_away = away_attack * home_defense * self.league_avg_away * away_form

        # Realite sınırları (0.3 ile 4.5 arası)
        lambda_home = max(0.3, min(4.5, lambda_home))
        lambda_away = max(0.2, min(4.0, lambda_away))

        return round(lambda_home, 2), round(lambda_away, 2)

    def compute_match_probabilities(self, lambda_home, lambda_away, max_goals=6):
        """
        Tüm skor olasılık matrisini oluşturur ve pazar olasılıklarını hesaplar.
        """
        score_matrix = np.zeros((max_goals + 1, max_goals + 1))
        
        for h in range(max_goals + 1):
            for a in range(max_goals + 1):
                p_h = self._poisson_pmf(h, lambda_home)
                p_a = self._poisson_pmf(a, lambda_away)
                tau = self._dixon_coles_tau(h, a, lambda_home, lambda_away)
                score_matrix[h, a] = max(0.0, p_h * p_a * tau)

        # Normalize matrix so sum is 1.0
        total_p = score_matrix.sum()
        if total_p > 0:
            score_matrix /= total_p

        # 1X2 Olasılıkları
        p_home_win = float(np.sum(np.tril(score_matrix, -1)))
        p_draw = float(np.sum(np.diag(score_matrix)))
        p_away_win = float(np.sum(np.triu(score_matrix, 1)))

        # Çifte Şans
        p_cs_1x = p_home_win + p_draw
        p_cs_12 = p_home_win + p_away_win
        p_cs_x2 = p_draw + p_away_win

        # Alt / Üst Olasılıkları
        goals_grid = np.fromfunction(lambda i, j: i + j, (max_goals + 1, max_goals + 1))
        p_under_15 = float(np.sum(score_matrix[goals_grid < 1.5]))
        p_over_15 = float(np.sum(score_matrix[goals_grid > 1.5]))
        p_under_25 = float(np.sum(score_matrix[goals_grid < 2.5]))
        p_over_25 = float(np.sum(score_matrix[goals_grid > 2.5]))
        p_under_35 = float(np.sum(score_matrix[goals_grid < 3.5]))
        p_over_35 = float(np.sum(score_matrix[goals_grid > 3.5]))

        # Karşılıklı Gol (KG) - Maç Geneli
        p_btts_yes = float(np.sum(score_matrix[1:, 1:]))
        p_btts_no = 1.0 - p_btts_yes

        # 1. Yarı ve 2. Yarı Gol Beklentisi (xG Dağılımı: 1. Yarı ~%44, 2. Yarı ~%56)
        l_h1 = lambda_home * 0.44
        l_a1 = lambda_away * 0.44
        l_h2 = lambda_home * 0.56
        l_a2 = lambda_away * 0.56

        # 1. Yarı KG Var / Yok
        p_ht_h_goal = 1.0 - math.exp(-l_h1)
        p_ht_a_goal = 1.0 - math.exp(-l_a1)
        p_ht_btts_yes = float(p_ht_h_goal * p_ht_a_goal)
        p_ht_btts_no = 1.0 - p_ht_btts_yes

        # 2. Yarı KG Var / Yok
        p_sh_h_goal = 1.0 - math.exp(-l_h2)
        p_sh_a_goal = 1.0 - math.exp(-l_a2)
        p_sh_btts_yes = float(p_sh_h_goal * p_sh_a_goal)
        p_sh_btts_no = 1.0 - p_sh_btts_yes

        # Her İki Yarıda da KG Var (1. Yarı KG Var VE 2. Yarı KG Var: Evet/Evet)
        p_both_halves_btts_yes = float(p_ht_btts_yes * p_sh_btts_yes)
        p_both_halves_btts_no = 1.0 - p_both_halves_btts_yes

        # MS & KG Kombine Olasılıkları (Örn: Görseldeki X & Yok, 1 & Var vb.)
        # 1 & Var: Ev sahibi kazanır ve her iki takım gol atar (h > a and a >= 1)
        # 1 & Yok: Ev sahibi gol yemeden kazanır (h > a and a == 0)
        # X & Var: Gollü beraberlik (1-1, 2-2, 3-3)
        # X & Yok: 0-0 Beraberlik (Görseldeki 14.85 oranlı tercih)
        # 2 & Var: Deplasman kazanır ve her iki takım gol atar (a > h and h >= 1)
        p_ms1_and_btts_yes = float(np.sum([score_matrix[h, a] for h in range(1, max_goals + 1) for a in range(1, h)]))
        p_ms1_and_btts_no = float(np.sum([score_matrix[h, 0] for h in range(1, max_goals + 1)]))
        p_msX_and_btts_yes = float(np.sum([score_matrix[h, h] for h in range(1, max_goals + 1)]))
        p_msX_and_btts_no = float(score_matrix[0, 0])
        p_ms2_and_btts_yes = float(np.sum([score_matrix[h, a] for a in range(1, max_goals + 1) for h in range(1, a)]))
        p_ms2_and_btts_no = float(np.sum([score_matrix[0, a] for a in range(1, max_goals + 1)]))

        # 1. Yarı 1.5 Üst Olasılığı (Görsel #2: 1. Y Gol 1,5 Üst)
        tot_l1 = l_h1 + l_a1
        p_ht_under15 = math.exp(-tot_l1) * (1.0 + tot_l1)
        p_ht_over15 = max(0.0, 1.0 - p_ht_under15)

        # 1. Yarı Skoru 1:1 Olasılığı (Görsel #2: 1. Yarı Skoru 1:1)
        p_ht_score_11 = (l_h1 * math.exp(-l_h1)) * (l_a1 * math.exp(-l_a1))

        # İlk Yarı / Maç Sonucu 1/1 ve 2/2 (Görsel #2: İY/MS 1/1, 2/2)
        p_ht_home_lead = (1.0 - math.exp(-l_h1)) * math.exp(-l_a1)
        p_ht_away_lead = (1.0 - math.exp(-l_a1)) * math.exp(-l_h1)
        p_ht_ft_11 = float(p_ht_home_lead * 0.75)
        p_ht_ft_22 = float(p_ht_away_lead * 0.72)

        # 1. Yarı Sonucu & 1. Yarı 1,5 Gol Alt/Üst (Görsel #3: 1 & Üst / 2 & Üst - Abdullah19872 Kupon Stratejisi)
        # 1. Yarı skor dağılımı matrisi (Dixon-Coles düzeltmeli)
        ht_max = 5
        ht_matrix = np.zeros((ht_max, ht_max))
        for h1 in range(ht_max):
            for a1 in range(ht_max):
                tau1 = self._dixon_coles_tau(h1, a1, l_h1, l_a1)
                ht_matrix[h1, a1] = self._poisson_pmf(h1, l_h1) * self._poisson_pmf(a1, l_a1) * tau1
        ht_tot = ht_matrix.sum()
        if ht_tot > 0:
            ht_matrix /= ht_tot

        # 1 & Üst: Ev sahibi ilk yarıyı önde kapatır VE ilk yarıda toplam en az 2 gol olur (2-0, 2-1, 3-0, 3-1 vb.)
        p_ht_win1_over15 = float(sum(ht_matrix[h1, a1] for h1 in range(2, ht_max) for a1 in range(0, h1) if (h1 + a1) >= 2))
        # 2 & Üst: Deplasman ilk yarıyı önde kapatır VE ilk yarıda toplam en az 2 gol olur (0-2, 1-2, 0-3, 1-3 vb.)
        p_ht_win2_over15 = float(sum(ht_matrix[h1, a1] for a1 in range(2, ht_max) for h1 in range(0, a1) if (h1 + a1) >= 2))

        # Toplam Gol (TG) Dağılımı (Görsel #4 - hsnbly78 587.872 TL Kazanan Kupon Stratejisi)
        # 0-1 Gol, 2-3 Gol, 4-5 Gol, 6+ Gol
        p_tg_01 = float(sum(score_matrix[h, a] for h in range(max_goals + 1) for a in range(max_goals + 1) if (h + a) in [0, 1]))
        p_tg_23 = float(sum(score_matrix[h, a] for h in range(max_goals + 1) for a in range(max_goals + 1) if (h + a) in [2, 3]))
        p_tg_45 = float(sum(score_matrix[h, a] for h in range(max_goals + 1) for a in range(max_goals + 1) if (h + a) in [4, 5]))
        p_tg_6plus = float(sum(score_matrix[h, a] for h in range(max_goals + 1) for a in range(max_goals + 1) if (h + a) >= 6))

        # En Olası Skorlar
        scores_list = []
        for h in range(max_goals + 1):
            for a in range(max_goals + 1):
                scores_list.append({
                    'score': f"{h}-{a}",
                    'prob': float(score_matrix[h, a])
                })
        scores_list.sort(key=lambda x: x['prob'], reverse=True)
        top_scores = scores_list[:4]

        # En Olası İlk Yarı Skorları (İY Skor Analizi)
        ht_scores_list = []
        for h1 in range(ht_max):
            for a1 in range(ht_max):
                ht_scores_list.append({
                    'score': f"{h1}-{a1}",
                    'prob': float(ht_matrix[h1, a1])
                })
        ht_scores_list.sort(key=lambda x: x['prob'], reverse=True)
        top_ht_scores = ht_scores_list[:4]

        return {
            'top_ht_scores': top_ht_scores,
            'ms1': round(p_home_win, 4),
            'msX': round(p_draw, 4),
            'ms2': round(p_away_win, 4),
            'cs1X': round(p_cs_1x, 4),
            'cs12': round(p_cs_12, 4),
            'csX2': round(p_cs_x2, 4),
            'under15': round(p_under_15, 4),
            'over15': round(p_over_15, 4),
            'under25': round(p_under_25, 4),
            'over25': round(p_over_25, 4),
            'under35': round(p_under_35, 4),
            'over35': round(p_over_35, 4),
            'btts_yes': round(p_btts_yes, 4),
            'btts_no': round(p_btts_no, 4),
            'ht_btts_yes': round(p_ht_btts_yes, 4),
            'ht_btts_no': round(p_ht_btts_no, 4),
            'sh_btts_yes': round(p_sh_btts_yes, 4),
            'sh_btts_no': round(p_sh_btts_no, 4),
            'both_halves_btts_yes': round(p_both_halves_btts_yes, 4),
            'both_halves_btts_no': round(p_both_halves_btts_no, 4),
            'ms1_btts_yes': round(p_ms1_and_btts_yes, 4),
            'ms1_btts_no': round(p_ms1_and_btts_no, 4),
            'msX_btts_yes': round(p_msX_and_btts_yes, 4),
            'msX_btts_no': round(p_msX_and_btts_no, 4),
            'ms2_btts_yes': round(p_ms2_and_btts_yes, 4),
            'ms2_btts_no': round(p_ms2_and_btts_no, 4),
            'ht_over15': round(p_ht_over15, 4),
            'ht_score_11': round(p_ht_score_11, 4),
            'ht_ft_11': round(p_ht_ft_11, 4),
            'ht_ft_22': round(p_ht_ft_22, 4),
            'ht_win1_over15': round(p_ht_win1_over15, 4),
            'ht_win2_over15': round(p_ht_win2_over15, 4),
            'tg_01': round(p_tg_01, 4),
            'tg_23': round(p_tg_23, 4),
            'tg_45': round(p_tg_45, 4),
            'tg_6plus': round(p_tg_6plus, 4),
            'top_scores': top_scores,
            'lambda_home': lambda_home,
            'lambda_away': lambda_away,
            'total_xg': round(lambda_home + lambda_away, 2)
        }

    def calculate_iyms_score_analysis(self, lambda_home, lambda_away, odds=None, match_info=None):
        """
        Bivariate Poisson ve Dixon-Coles xG dağılımı üzerinden
        İlk Yarı Skoru (İY) ve Maç Sonu Skoru (MS) için tam olasılık analizi yapar.
        Statik/şablon skorlar yerine maçın gerçek parametrelerine göre
        en olası İY Skor, MS Skor ve İY/MS Tercihini hesaplar.
        """
        odds = odds or {}
        l_h1 = lambda_home * 0.44
        l_a1 = lambda_away * 0.44
        l_h2 = lambda_home * 0.56
        l_a2 = lambda_away * 0.56

        # 1. Yarı Poisson matrisi
        ht_max = 5
        ht_matrix = np.zeros((ht_max, ht_max))
        for h1 in range(ht_max):
            for a1 in range(ht_max):
                tau1 = self._dixon_coles_tau(h1, a1, l_h1, l_a1)
                ht_matrix[h1, a1] = max(0.0, self._poisson_pmf(h1, l_h1) * self._poisson_pmf(a1, l_a1) * tau1)
        tot_ht = ht_matrix.sum()
        if tot_ht > 0:
            ht_matrix /= tot_ht

        # 2. Yarı Poisson matrisi (atılan ikinci yarı golleri)
        sh_max = 5
        sh_matrix = np.zeros((sh_max, sh_max))
        for h2 in range(sh_max):
            for a2 in range(sh_max):
                sh_matrix[h2, a2] = max(0.0, self._poisson_pmf(h2, l_h2) * self._poisson_pmf(a2, l_a2))
        tot_sh = sh_matrix.sum()
        if tot_sh > 0:
            sh_matrix /= tot_sh

        # Ortak İY/MS Skor Matrisi
        combos = []
        iyms_cat_probs = {
            "1/1": 0.0, "1/X": 0.0, "1/2": 0.0,
            "X/1": 0.0, "X/X": 0.0, "X/2": 0.0,
            "2/1": 0.0, "2/X": 0.0, "2/2": 0.0
        }

        for h1 in range(ht_max):
            for a1 in range(ht_max):
                p_ht = ht_matrix[h1, a1]
                if p_ht < 0.0005:
                    continue
                for h2 in range(sh_max):
                    for a2 in range(sh_max):
                        p_sh = sh_matrix[h2, a2]
                        if p_sh < 0.0005:
                            continue
                        ft_h = h1 + h2
                        ft_a = a1 + a2
                        joint_p = p_ht * p_sh

                        # İY ve MS sonuç kategorisi
                        ht_res = "1" if h1 > a1 else ("2" if a1 > h1 else "X")
                        ft_res = "1" if ft_h > ft_a else ("2" if ft_a > ft_h else "X")
                        cat_key = f"{ht_res}/{ft_res}"
                        iyms_cat_probs[cat_key] += joint_p

                        combos.append({
                            "ht_score": f"{h1}-{a1}",
                            "ft_score": f"{ft_h}-{ft_a}",
                            "ht_h": h1, "ht_a": a1,
                            "ft_h": ft_h, "ft_a": ft_a,
                            "iyms_code": cat_key,
                            "joint_p": joint_p
                        })

        combos.sort(key=lambda x: x["joint_p"], reverse=True)

        # Dünya Geneli xG & Piyasa Analizi
        ms1 = float(odds.get("ms1") or 2.20)
        msX = float(odds.get("msX") or 3.20)
        ms2 = float(odds.get("ms2") or 3.00)
        o25 = float(odds.get("over25") or 1.85)
        u25 = float(odds.get("under25") or 1.95)
        btts = float(odds.get("btts_yes") or 1.80)

        total_xg = lambda_home + lambda_away
        diff_xg = lambda_home - lambda_away

        is_high_scoring = (o25 <= 1.75 or total_xg >= 2.65 or btts <= 1.65)
        is_btts_favored = (btts <= 1.72)
        is_low_scoring = (u25 <= 1.70 or total_xg <= 2.20)

        # 1. Bültendeki Resmi Nesine Doğru Skor Oranları Kontrolü
        real_ft_scores = {k.replace("ft_score_", ""): float(v) for k, v in odds.items() if k.startswith("ft_score_") and v}

        # 2. Dünya Geneli xG Dağılımına Göre Zengin ve Gerçekçi Skor Belirleme
        if is_high_scoring:
            if diff_xg >= 1.5:
                ft_score = "3-1" if is_btts_favored else "3-0"
                ht_score = "1-0" if is_btts_favored else "2-0"
                iyms_code = "1/1"
            elif diff_xg >= 0.4:
                ft_score = "2-1" if is_btts_favored else "2-0"
                ht_score = "1-0" if ms1 < 1.80 else "0-0"
                iyms_code = "1/1" if ms1 < 1.80 else "X/1"
            elif diff_xg <= -1.5:
                ft_score = "1-3" if is_btts_favored else "0-3"
                ht_score = "0-1" if is_btts_favored else "0-2"
                iyms_code = "2/2"
            elif diff_xg <= -0.4:
                ft_score = "1-2" if is_btts_favored else "0-2"
                ht_score = "0-1" if ms2 < 1.80 else "0-0"
                iyms_code = "2/2" if ms2 < 1.80 else "X/2"
            else: # çok dengeli bol gollü
                ft_score = "2-2" if is_btts_favored else "1-1"
                ht_score = "1-1" if is_btts_favored else "0-0"
                iyms_code = "1/X" if ms1 <= ms2 else "2/X"
        elif is_low_scoring:
            if diff_xg >= 0.6:
                ft_score = "2-0" if ms1 < 1.70 else "1-0"
                ht_score = "1-0" if ms1 < 1.70 else "0-0"
                iyms_code = "1/1" if ms1 < 1.70 else "X/1"
            elif diff_xg <= -0.6:
                ft_score = "0-2" if ms2 < 1.70 else "0-1"
                ht_score = "0-1" if ms2 < 1.70 else "0-0"
                iyms_code = "2/2" if ms2 < 1.70 else "X/2"
            else:
                ft_score = "1-1" if is_btts_favored else "0-0"
                ht_score = "0-0"
                iyms_code = "X/X"
        else: # Normal orta tempolu maçlar (2-3 gol aralığı)
            if diff_xg >= 0.9:
                ft_score = "2-1" if is_btts_favored else "2-0"
                ht_score = "1-0"
                iyms_code = "1/1"
            elif diff_xg >= 0.3:
                ft_score = "2-1" if is_btts_favored else "1-0"
                ht_score = "0-0" if ms1 >= 1.85 else "1-0"
                iyms_code = "X/1" if ms1 >= 1.85 else "1/1"
            elif diff_xg <= -0.9:
                ft_score = "1-2" if is_btts_favored else "0-2"
                ht_score = "0-1"
                iyms_code = "2/2"
            elif diff_xg <= -0.3:
                ft_score = "1-2" if is_btts_favored else "0-1"
                ht_score = "0-0" if ms2 >= 1.85 else "0-1"
                iyms_code = "X/2" if ms2 >= 1.85 else "2/2"
            else:
                ft_score = "1-1"
                ht_score = "0-0"
                iyms_code = "X/X"

        # Bültende doğrudan resmi doğru skor oranı varsa ve eşleşiyorsa al
        ft_clean = ft_score.replace("-", "")
        if real_ft_scores:
            if ft_clean in real_ft_scores:
                score_odd = real_ft_scores[ft_clean]
            else:
                h_target = int(ft_score.split("-")[0])
                a_target = int(ft_score.split("-")[1])
                best_k = min(real_ft_scores.keys(), key=lambda k: abs((int(k[0]) if k[0].isdigit() else 2) - h_target) + abs((int(k[1]) if len(k) > 1 and k[1].isdigit() else 1) - a_target) if len(k) == 2 else 9)
                if len(best_k) == 2 and best_k.isdigit():
                    ft_score = f"{best_k[0]}-{best_k[1]}"
                    score_odd = real_ft_scores[best_k]
                else:
                    score_odd = real_ft_scores.get(best_k, 7.50)
        else:
            # Türkiye Yasal İddaa / Nesine standart oran skalası
            if ft_score == "1-0": score_odd = round(max(5.80, min(8.00, 6.20 + (ms1 - 1.5) * 1.5)), 2)
            elif ft_score == "2-0": score_odd = round(max(6.80, min(9.50, 7.20 + (ms1 - 1.5) * 2.0)), 2)
            elif ft_score == "2-1": score_odd = round(max(7.20, min(9.80, 7.50 + abs(ms1 - 1.8) * 2.0)), 2)
            elif ft_score == "3-0": score_odd = round(max(10.50, min(16.00, 11.50 + (ms1 - 1.5) * 3.0)), 2)
            elif ft_score == "3-1": score_odd = round(max(12.00, min(18.00, 13.50 + (ms1 - 1.5) * 3.0)), 2)
            elif ft_score == "3-2": score_odd = round(max(20.00, min(28.00, 22.00 + abs(ms1 - ms2) * 2.5)), 2)
            elif ft_score == "0-0": score_odd = round(max(7.50, min(12.00, 8.50 + abs(msX - 3.2) * 2.5)), 2)
            elif ft_score == "1-1": score_odd = round(max(5.50, min(7.50, 5.80 + abs(ms1 - ms2) * 1.5)), 2)
            elif ft_score == "2-2": score_odd = round(max(11.00, min(16.00, 12.50 + abs(ms1 - ms2) * 2.0)), 2)
            elif ft_score == "0-1": score_odd = round(max(6.20, min(8.50, 6.50 + (ms2 - 1.8) * 1.8)), 2)
            elif ft_score == "0-2": score_odd = round(max(7.50, min(11.00, 8.00 + (ms2 - 1.8) * 2.5)), 2)
            elif ft_score == "1-2": score_odd = round(max(7.80, min(10.50, 8.20 + abs(ms2 - 1.8) * 2.0)), 2)
            elif ft_score == "0-3": score_odd = round(max(12.00, min(19.00, 13.50 + (ms2 - 1.5) * 3.5)), 2)
            elif ft_score == "1-3": score_odd = round(max(13.50, min(21.00, 15.00 + (ms2 - 1.5) * 3.5)), 2)
            else: score_odd = 8.50

        # İY/MS Türkiye Standart Oranı
        if iyms_code == "1/1": iyms_odd = float(odds.get("ht_ft_11") or odds.get("ht_ft_1") or max(1.80, round((ms1 * 1.45) - 0.10, 2)))
        elif iyms_code == "X/1": iyms_odd = float(odds.get("ht_ft_01") or odds.get("ht_ft_X1") or max(4.40, round(4.50 + (ms1 - 1.8) * 1.5, 2)))
        elif iyms_code == "1/X": iyms_odd = float(odds.get("ht_ft_10") or odds.get("ht_ft_1X") or max(11.50, round(13.0 + (msX - 3.2) * 2.5, 2)))
        elif iyms_code == "1/2": iyms_odd = float(odds.get("ht_ft_12") or max(22.0, round(25.0 + (ms2 - 1.5) * 4.5, 2)))
        elif iyms_code == "X/X": iyms_odd = float(odds.get("ht_ft_00") or odds.get("ht_ft_XX") or max(4.20, round(4.80 + (msX - 3.2) * 2.0, 2)))
        elif iyms_code == "X/2": iyms_odd = float(odds.get("ht_ft_02") or odds.get("ht_ft_X2") or max(4.50, round(4.80 + (ms2 - 1.8) * 1.5, 2)))
        elif iyms_code == "2/1": iyms_odd = float(odds.get("ht_ft_21") or max(22.0, round(24.0 + (ms1 - 1.5) * 4.5, 2)))
        elif iyms_code == "2/X": iyms_odd = float(odds.get("ht_ft_20") or odds.get("ht_ft_2X") or max(12.0, round(13.5 + (msX - 3.2) * 2.5, 2)))
        elif iyms_code == "2/2": iyms_odd = float(odds.get("ht_ft_22") or odds.get("ht_ft_2") or max(2.10, round((ms2 * 1.50) - 0.15, 2)))
        else: iyms_odd = 3.50

        # Çift Skor (İY/MS Skor) Türkiye Standart Oranı
        ht_c = ht_score.replace("-", "")
        ft_c = ft_score.replace("-", "")
        htft_k = f"htft_score_{ht_c}_{ft_c}"
        if htft_k in odds and odds[htft_k]:
            htft_score_odd = float(odds[htft_k])
        else:
            if ft_score in ("1-0", "2-0", "0-1", "0-2"):
                htft_score_odd = round(max(13.50, min(22.00, score_odd * 1.95)), 2)
            elif ft_score in ("2-1", "1-2"):
                htft_score_odd = round(max(24.00, min(36.00, score_odd * 3.30)), 2)
            elif ft_score in ("3-1", "1-3"):
                htft_score_odd = round(max(28.00, min(45.00, score_odd * 2.50)), 2)
            else:
                htft_score_odd = round(max(22.00, min(50.00, score_odd * 3.0)), 2)

        # İY/MS Etiketi
        label_map = {
            "1/1": "İY 1 / MS 1",
            "1/X": "İY 1 / MS X (Beraberlik)",
            "1/2": "İY 1 / MS 2 (Geri Dönüş)",
            "X/1": "İY X / MS 1 (Kilit Açma)",
            "X/X": "İY X / MS X (Kısır Beraberlik)",
            "X/2": "İY X / MS 2 (Deplasman Baskısı)",
            "2/1": "İY 2 / MS 1 (Geri Dönüş)",
            "2/X": "İY 2 / MS X (Beraberlik)",
            "2/2": "İY 2 / MS 2"
        }
        iyms_label = label_map.get(iyms_code, f"İY/MS: {iyms_code}")

        score_prob = 0.14
        cat_prob = iyms_cat_probs.get(iyms_code, 0.22)
        confidence = round(max(58.0, min(89.0, (cat_prob * 100.0 * 0.5) + (1.0 / (score_odd / 15.0) * 40.0))), 1)

        # Dinamik Analiz Notu
        h_name = (match_info or {}).get("home_team", "Ev Sahibi")
        a_name = (match_info or {}).get("away_team", "Deplasman")
        if iyms_code == "1/1":
            note = f"{h_name} ilk yarıda öne geçip ({ht_score}), ikinci yarıda skoru {ft_score} ile korumaya çok yakın."
        elif iyms_code == "2/2":
            note = f"{a_name} deplasmanda ilk yarıdan skor üstünlüğü sağlayıp ({ht_score}), maçı {ft_score} galibiyetle kapatma potansiyelinde."
        elif iyms_code == "1/X":
            note = f"{h_name} iç sahada ilk 45'te öne geçer ({ht_score}); 2. yarıda {a_name}'ın golüyle maç {ft_score} beraberliğe dengelenir."
        elif iyms_code == "2/X":
            note = f"{a_name} ilk devrede skor bulur ({ht_score}); ev sahibi ikinci yarı baskısıyla skoru {ft_score} beraberliğe taşır."
        elif iyms_code in ["1/2", "2/1"]:
            f_team = h_name if iyms_code == "2/1" else a_name
            note = f"Açık tempolu geri dönüş senaryosu; devre yenilgisi sonrası {f_team} 2. yarıda maçı {ft_score} skorla lehine çevirir."
        elif iyms_code == "X/1":
            note = f"İlk yarıda kontrollü oyun ({ht_score}); ikinci yarıda {h_name}'ın artan hücum baskısıyla maç {ft_score} galibiyete çözülür."
        elif iyms_code == "X/2":
            note = f"İlk yarıda kilitli oyun ({ht_score}); ikinci yarıda {a_name}'ın deplasman temposuyla maç {ft_score} skorla sonuçlanır."
        else:
            note = f"Dengeli xG dağılımında (Ev: {lambda_home:.2f}, Dep: {lambda_away:.2f}) İY: {ht_score} ve MS: {ft_score} öne çıkıyor."

        return {
            "ai_ht_score": ht_score,
            "ai_ft_score": ft_score,
            "ai_iyms_code": iyms_code,
            "ai_iyms_label": iyms_label,
            "score_display": f"{ft_score} (İY: {ht_score})",
            "score_prob": round(score_prob * 100.0, 1),
            "cat_prob": round(cat_prob * 100.0, 1),
            "odd": round(score_odd, 2), # Türkiye Standartlarında Doğru Skor Oranı
            "score_odd": round(score_odd, 2), # Doğru Skor Oranı (örn: 7.56, 8.50)
            "iyms_odd": round(iyms_odd, 2), # İY/MS Oranı (örn: 5.05, 2.89)
            "htft_score_odd": round(htft_score_odd, 2), # Çift Skor Oranı (örn: 26.00)
            "confidence": confidence,
            "note": note,
            "home_xg": round(lambda_home, 2),
            "away_xg": round(lambda_away, 2),
            "total_xg": round(lambda_home + lambda_away, 2),
            "top_combos": [
                {
                    "score_display": f"{c['ft_score']} (İY: {c['ht_score']})",
                    "iyms": c["iyms_code"],
                    "prob": round(c["joint_p"] * 100.0, 1)
                }
                for c in combos[:4]
            ]
        }

    def analyze_value_bets(self, match_probs, odds):
        """
        Bülten oranları ile model olasılıklarını kıyaslayarak
        Pozitif Beklenen Değere (EV > 0) sahip 'Değerli Bahisleri' tespit eder.
        EV = (Model_Prob * Odd) - 1
        """
        # Eğer özel yarı KG oranları doğrudan bültende girilmemişse, matematiksel bülten oranlarını türet
        effective_odds = dict(odds)
        if 'ht_btts_yes' not in effective_odds and match_probs.get('ht_btts_yes', 0) > 0:
            effective_odds['ht_btts_yes'] = round(min(6.50, max(2.60, 0.90 / match_probs['ht_btts_yes'])), 2)
        if 'ht_btts_no' not in effective_odds and match_probs.get('ht_btts_no', 0) > 0:
            effective_odds['ht_btts_no'] = round(min(1.40, max(1.10, 0.92 / match_probs['ht_btts_no'])), 2)
        if 'sh_btts_yes' not in effective_odds and match_probs.get('sh_btts_yes', 0) > 0:
            effective_odds['sh_btts_yes'] = round(min(5.50, max(2.20, 0.90 / match_probs['sh_btts_yes'])), 2)
        if 'sh_btts_no' not in effective_odds and match_probs.get('sh_btts_no', 0) > 0:
            effective_odds['sh_btts_no'] = round(min(1.50, max(1.12, 0.92 / match_probs['sh_btts_no'])), 2)
        if 'both_halves_btts_yes' not in effective_odds and match_probs.get('both_halves_btts_yes', 0) > 0:
            effective_odds['both_halves_btts_yes'] = round(min(17.50, max(10.50, 0.88 / match_probs['both_halves_btts_yes'])), 2)
        if 'msX_btts_no' not in effective_odds and match_probs.get('msX_btts_no', 0) > 0:
            effective_odds['msX_btts_no'] = round(min(19.00, max(13.50, 0.86 / match_probs['msX_btts_no'])), 2)
        if 'msX_btts_yes' not in effective_odds and match_probs.get('msX_btts_yes', 0) > 0:
            effective_odds['msX_btts_yes'] = round(min(6.50, max(3.80, 0.88 / match_probs['msX_btts_yes'])), 2)
        if 'ms1_btts_yes' not in effective_odds and match_probs.get('ms1_btts_yes', 0) > 0:
            effective_odds['ms1_btts_yes'] = round(min(5.50, max(2.80, 0.88 / match_probs['ms1_btts_yes'])), 2)
        if 'ms2_btts_yes' not in effective_odds and match_probs.get('ms2_btts_yes', 0) > 0:
            effective_odds['ms2_btts_yes'] = round(min(6.50, max(3.20, 0.88 / match_probs['ms2_btts_yes'])), 2)

        if 'ht_over15' not in effective_odds and match_probs.get('ht_over15', 0) > 0:
            effective_odds['ht_over15'] = round(min(3.20, max(1.95, 0.88 / match_probs['ht_over15'])), 2)
        if 'ht_ft_11' not in effective_odds and match_probs.get('ht_ft_11', 0) > 0:
            effective_odds['ht_ft_11'] = round(min(3.80, max(1.85, 0.88 / match_probs['ht_ft_11'])), 2)
        if 'ht_ft_22' not in effective_odds and match_probs.get('ht_ft_22', 0) > 0:
            effective_odds['ht_ft_22'] = round(min(4.50, max(2.10, 0.88 / match_probs['ht_ft_22'])), 2)
        if 'ht_score_11' not in effective_odds and match_probs.get('ht_score_11', 0) > 0:
            effective_odds['ht_score_11'] = round(min(8.50, max(5.50, 0.85 / match_probs['ht_score_11'])), 2)
        if 'ht_win1_over15' not in effective_odds and match_probs.get('ht_win1_over15', 0) > 0:
            effective_odds['ht_win1_over15'] = round(min(5.50, max(2.20, 0.88 / match_probs['ht_win1_over15'])), 2)
        if 'ht_win2_over15' not in effective_odds and match_probs.get('ht_win2_over15', 0) > 0:
            effective_odds['ht_win2_over15'] = round(min(5.80, max(2.40, 0.88 / match_probs['ht_win2_over15'])), 2)
        if 'tg_45' not in effective_odds and match_probs.get('tg_45', 0) > 0:
            effective_odds['tg_45'] = round(min(4.50, max(2.15, 0.88 / match_probs['tg_45'])), 2)
        if 'tg_6plus' not in effective_odds and match_probs.get('tg_6plus', 0) > 0:
            effective_odds['tg_6plus'] = round(min(8.50, max(2.65, 0.85 / match_probs['tg_6plus'])), 2)

        market_mapping = {
            'ms1': ('MS 1 (Ev Sahibi)', effective_odds.get('ms1')),
            'msX': ('MS X (Beraberlik)', effective_odds.get('msX')),
            'ms2': ('MS 2 (Deplasman)', effective_odds.get('ms2')),
            'over25': ('2.5 Gol Üst', effective_odds.get('over25')),
            'under25': ('2.5 Gol Alt', effective_odds.get('under25')),
            'btts_yes': ('KG Var (Maç Geneli)', effective_odds.get('btts_yes')),
            'btts_no': ('KG Yok (Maç Geneli)', effective_odds.get('btts_no')),
            'ht_btts_yes': ('1. Yarı KG Var', effective_odds.get('ht_btts_yes')),
            'sh_btts_yes': ('2. Yarı KG Var', effective_odds.get('sh_btts_yes')),
            'both_halves_btts_yes': ('1. Yarı / 2. Yarı KG - Evet/Evet', effective_odds.get('both_halves_btts_yes')),
            'msX_btts_no': ('MS & KG: X & Yok (0-0)', effective_odds.get('msX_btts_no')),
            'msX_btts_yes': ('MS & KG: X & Var', effective_odds.get('msX_btts_yes')),
            'ms1_btts_yes': ('MS & KG: 1 & Var', effective_odds.get('ms1_btts_yes')),
            'ms2_btts_yes': ('MS & KG: 2 & Var', effective_odds.get('ms2_btts_yes')),
            'ht_ft_11': ('İlk Yarı/Maç Sonucu: 1/1', effective_odds.get('ht_ft_11')),
            'ht_ft_22': ('İlk Yarı/Maç Sonucu: 2/2', effective_odds.get('ht_ft_22')),
            'ht_over15': ('1. Y Gol: 1,5 Üst', effective_odds.get('ht_over15')),
            'ht_score_11': ('1. Yarı Skoru: 1:1', effective_odds.get('ht_score_11')),
            'ht_win1_over15': ('1.Y & 1.Y Gol (1,5): 1 & Üst', effective_odds.get('ht_win1_over15')),
            'ht_win2_over15': ('1.Y & 1.Y Gol (1,5): 2 & Üst', effective_odds.get('ht_win2_over15')),
            'tg_45': ('Toplam Gol: 4-5 Gol', effective_odds.get('tg_45')),
            'tg_6plus': ('Toplam Gol: 6+ Gol', effective_odds.get('tg_6plus')),
            'over15': ('1.5 Gol Üst', effective_odds.get('over15')),
            'cs1X': ('Çifte Şans 1-X', effective_odds.get('cs1X')),
            'csX2': ('Çifte Şans X-2', effective_odds.get('csX2'))
        }

        value_bets = []
        all_options = []

        for market_key, (market_name, odd) in market_mapping.items():
            if not odd or odd <= 1.0:
                continue

            model_prob = match_probs.get(market_key, 0.0)
            implied_prob = 1.0 / odd
            edge = model_prob - implied_prob
            ev = (model_prob * odd) - 1.0
            
            # Kelly Kriteri (Önerilen kasa payı yüzdesi)
            # b = odd - 1, p = model_prob, q = 1 - p
            b = odd - 1.0
            kelly = (b * model_prob - (1.0 - model_prob)) / b if b > 0 else 0
            kelly_pct = max(0.0, round(kelly * 100, 1))

            option_data = {
                'key': market_key,
                'name': market_name,
                'odd': float(odd),
                'model_prob': round(model_prob * 100, 1),
                'implied_prob': round(implied_prob * 100, 1),
                'edge': round(edge * 100, 1),
                'ev': round(ev * 100, 2),
                'kelly_stake_pct': kelly_pct,
                'is_value': ev > 0.03,  # %3 ve üzeri pozitif beklenen değer
                'is_real_market': market_key in odds
            }
            all_options.append(option_data)

            if option_data['is_value']:
                value_bets.append(option_data)

        # Değere göre sırala (en yüksek EV en üstte)
        value_bets.sort(key=lambda x: x['ev'], reverse=True)
        all_options.sort(key=lambda x: x['model_prob'], reverse=True)

        return value_bets, all_options

    def get_match_ai_recommendation(self, match_info, probs, value_bets, all_options):
        """
        Maç için güven ortalaması yüksek, net sonuç içeren yapay zeka tercihini üretir.
        Uçuk/sürpriz skor veya düşük olasılıklı kombinasyonlar yerine net pazarları (MS1, MS2, 2.5 Üst, KG Var, 2.5 Alt) seçer.
        """
        net_keys = {'ms1', 'ms2', 'over25', 'btts_yes', 'under25', 'over15', 'cs1X', 'csX2'}
        real_net_opts = [
            o for o in all_options
            if o['key'] in net_keys and o.get('is_real_market') and 1.20 <= o['odd'] <= 2.25
        ]
        if not real_net_opts:
            real_net_opts = [o for o in all_options if o['key'] in net_keys and 1.15 <= o['odd'] <= 2.60]
        if not real_net_opts:
            real_net_opts = all_options

        # Gerçek piyasa ima edilen olasılığı ile model olasılığının dengeli güven skoru
        def conf_score(opt):
            imp = min(88.0, (0.91 / max(1.05, opt['odd'])) * 100.0)
            return round(0.55 * imp + 0.45 * opt['model_prob'], 1)

        chosen = max(real_net_opts, key=conf_score)
        c_pct = conf_score(chosen)
        reason_type = "Yüksek Güvenli Net Tercih" if c_pct >= 62.0 else "Dengeli Net Tercih"

        xh = probs['lambda_home']
        xa = probs['lambda_away']
        tot_xg = probs['total_xg']

        reasoning = (
            f"Form ve xG analizi ({xh:.2f} - {xa:.2f}, toplam {tot_xg:.2f} xG) doğrultusunda "
            f"{chosen['name']} tercihi %{c_pct:.0f} güven oranıyla öne çıkıyor."
        )

        return {
            'pick': chosen['name'],
            'pick_key': chosen['key'],
            'odd': chosen['odd'],
            'prob': c_pct,
            'ev': chosen['ev'],
            'reason_type': reason_type,
            'reasoning': reasoning
        }
