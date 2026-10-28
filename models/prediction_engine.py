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
