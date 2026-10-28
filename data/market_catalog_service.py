import json

NESINE_MTID_MAP = {
    1: {"name": "Maç Sonucu (1-X-2)", "category": "Ana Bahisler"},
    3: {"name": "Çifte Şans", "category": "Ana Bahisler"},
    5: {"name": "İlk Yarı / Maç Sonucu (İY/MS)", "category": "İY/MS Kombinasyonları"},
    7: {"name": "1. Yarı Sonucu", "category": "Devre Bahisleri"},
    8: {"name": "1. Yarı Çifte Şans", "category": "Devre Bahisleri"},
    9: {"name": "2. Yarı Sonucu", "category": "Devre Bahisleri"},
    11: {"name": "1.5 Gol Alt/Üst", "category": "Gol Bahisleri"},
    12: {"name": "2.5 Gol Alt/Üst", "category": "Gol Bahisleri"},
    13: {"name": "3.5 Gol Alt/Üst", "category": "Gol Bahisleri"},
    14: {"name": "1. Yarı 1.5 Gol Alt/Üst", "category": "Devre Bahisleri"},
    15: {"name": "2. Yarı 2.5 Gol Alt/Üst", "category": "Devre Bahisleri"},
    20: {"name": "2. Yarı 1.5 Gol Alt/Üst", "category": "Devre Bahisleri"},
    29: {"name": "Deplasman Toplam Gol Alt/Üst", "category": "Takım Golleri"},
    38: {"name": "Karşılıklı Gol Var/Yok (KG)", "category": "Gol Bahisleri"},
    43: {"name": "Hangi Yarıda Daha Çok Gol Olur", "category": "Devre Bahisleri"},
    48: {"name": "Ev Sahibi Toplam Gol Alt/Üst", "category": "Takım Golleri"},
    49: {"name": "Toplam Gol Tek/Çift", "category": "Gol Bahisleri"},
    60: {"name": "1. Yarı Toplam Gol Alt/Üst", "category": "Devre Bahisleri"},
    67: {"name": "2.5 Gol Alt/Üst", "category": "Gol Bahisleri"},
    70: {"name": "1. Yarı 1.5 Gol Alt/Üst", "category": "Devre Bahisleri"},
    85: {"name": "Toplam Gol Aralığı", "category": "Gol Bahisleri"},
    100: {"name": "Handikaplı Maç Sonucu", "category": "Handikap Bahisleri"},
    101: {"name": "Toplam Gol Alt/Üst Çizgileri", "category": "Gol Bahisleri"},
    155: {"name": "4.5 Gol Alt/Üst", "category": "Gol Bahisleri"},
    209: {"name": "1. Yarı 0.5 Gol Alt/Üst", "category": "Devre Bahisleri"},
    212: {"name": "0.5 Gol Alt/Üst", "category": "Gol Bahisleri"},
    216: {"name": "Toplam Korner Sayısı", "category": "Korner & Kart"},
    218: {"name": "1. Yarı Korner Sayısı", "category": "Korner & Kart"},
    220: {"name": "İlk Golü Hangi Takım Atar", "category": "Özel Bahisler"},
    222: {"name": "Son Golü Hangi Takım Atar", "category": "Özel Bahisler"},
    224: {"name": "Hangi Yarıda Daha Çok Gol Olur", "category": "Devre Bahisleri"},
    256: {"name": "Ev Sahibi 0.5 Üst/Alt", "category": "Takım Golleri"},
    268: {"name": "Handikaplı Maç Sonucu (HMS)", "category": "Handikap Bahisleri"},
    272: {"name": "Maç Sonucu & Toplam Gol Kombine", "category": "Kombin Bahisler"},
    276: {"name": "1. Yarı Skoru", "category": "Skor Bahisleri"},
    287: {"name": "Karşılıklı Gol", "category": "Gol Bahisleri"},
    288: {"name": "1. Yarı Karşılıklı Gol", "category": "Devre Bahisleri"},
    291: {"name": "Beraberlikte İade", "category": "Ana Bahisler"},
    295: {"name": "Ev Sahibi Her İki Yarıda Gol Atar mı", "category": "Takım Golleri"},
    296: {"name": "Ev Sahibi İki Yarıyı da Kazanır mı", "category": "Özel Bahisler"},
    299: {"name": "Deplasman İki Yarıyı da Kazanır mı", "category": "Özel Bahisler"},
    301: {"name": "Korner Alt/Üst Çizgisi", "category": "Korner & Kart"},
    326: {"name": "2.5 Gol Alt/Üst", "category": "Gol Bahisleri"},
    328: {"name": "2. Yarı 2.5 Gol Alt/Üst", "category": "Devre Bahisleri"},
    338: {"name": "1. Yarı Çifte Şans", "category": "Devre Bahisleri"},
    340: {"name": "2. Yarı Çifte Şans", "category": "Devre Bahisleri"},
    342: {"name": "Maç Sonucu ve 1.5 Alt/Üst", "category": "Kombin Bahisler"},
    343: {"name": "Maç Sonucu ve 2.5 Alt/Üst", "category": "Kombin Bahisler"},
    414: {"name": "Maç Sonucu ve Karşılıklı Gol", "category": "Kombin Bahisler"},
    416: {"name": "Maç Sonucu ve Toplam Gol Kombine", "category": "Kombin Bahisler"},
    446: {"name": "Toplam Gol 4 Farklı Seçenek", "category": "Gol Bahisleri"},
    448: {"name": "1. Yarı Skoru", "category": "Skor Bahisleri"},
    450: {"name": "Tek / Çift Gol", "category": "Gol Bahisleri"},
    452: {"name": "1. Yarı Karşılıklı Gol Var/Yok", "category": "Devre Bahisleri"},
    455: {"name": "Deplasman 0.5 Gol Üst/Alt", "category": "Takım Golleri"},
    457: {"name": "1. Yarı Deplasman 0.5 Üst/Alt", "category": "Takım Golleri"},
    459: {"name": "1. Yarı Sonucu & 1.5 Gol Alt/Üst", "category": "Devre Bahisleri"},
    528: {"name": "Kendi Kalesine Gol Olur mu", "category": "Özel Bahisler"},
    529: {"name": "Penaltı ve Kırmızı Kart Kombinasyonu", "category": "Özel Bahisler"},
    571: {"name": "Maçın İlk Gol Zaman Aralığı", "category": "Özel Bahisler"},
    578: {"name": "1.5 Gol Alt/Üst", "category": "Gol Bahisleri"},
    579: {"name": "2.5 Gol Alt/Üst", "category": "Gol Bahisleri"},
    580: {"name": "3.5 Gol Alt/Üst", "category": "Gol Bahisleri"},
    584: {"name": "Penaltı Olur mu", "category": "Özel Bahisler"},
    585: {"name": "VAR İncelemesi Olur mu", "category": "Özel Bahisler"},
    586: {"name": "Kırmızı Kart Olur mu", "category": "Korner & Kart"},
    587: {"name": "Toplam Kart Sayısı", "category": "Korner & Kart"},
    588: {"name": "Toplam Gol Sayısı Aralığı", "category": "Gol Bahisleri"},
    591: {"name": "Uzatmalara Gider mi", "category": "Özel Bahisler"},
    592: {"name": "Maçta Hat-Trick Olur mu", "category": "Özel Bahisler"},
    593: {"name": "Karşılıklı Gol Var & 2.5 Üst", "category": "Kombin Bahisler"},
    599: {"name": "1. Yarıda Kırmızı Kart Olur mu", "category": "Korner & Kart"},
    601: {"name": "Toplam Korner Çizgisi", "category": "Korner & Kart"},
    602: {"name": "Ev Sahibi Korner Alt/Üst", "category": "Korner & Kart"},
    603: {"name": "Deplasman Korner Alt/Üst", "category": "Korner & Kart"},
    703: {"name": "İlk Golü Atan Oyuncu", "category": "Oyuncu Bahisleri"},
    704: {"name": "Son Golü Atan Oyuncu", "category": "Oyuncu Bahisleri"},
    706: {"name": "Maçta Gol Atan Oyuncu (Herhangi Bir Zaman)", "category": "Oyuncu Bahisleri"},
    707: {"name": "2 veya Daha Fazla Gol Atan Oyuncu", "category": "Oyuncu Bahisleri"},
    709: {"name": "Oyuncu Kart Görür mü", "category": "Oyuncu Bahisleri"},
    712: {"name": "Oyuncu İsabetli Şut Sayısı", "category": "Oyuncu Bahisleri"},
    713: {"name": "İlk Golü Atar ve Takımı Kazanır", "category": "Oyuncu Bahisleri"},
    714: {"name": "Oyuncu Toplam Şut Sayısı", "category": "Oyuncu Bahisleri"},
    740: {"name": "Oyuncu Özel İstatistikleri (Şut/Pas)", "category": "Oyuncu Bahisleri"},
    765: {"name": "Oyuncu Asist Yapar mı", "category": "Oyuncu Bahisleri"},
    777: {"name": "Maç Skoru", "category": "Skor Bahisleri"},
    779: {"name": "1. Yarı Skoru", "category": "Skor Bahisleri"},
    798: {"name": "Asya Handikap Ev Sahibi", "category": "Handikap Bahisleri"},
    799: {"name": "Asya Handikap Deplasman", "category": "Handikap Bahisleri"},
    800: {"name": "Asya Toplam Gol Çizgisi", "category": "Gol Bahisleri"},
    801: {"name": "Her İki Yarıda Karşılıklı Gol (Evet/Evet)", "category": "Devre Bahisleri"},
    803: {"name": "Kaleci Kurtarış Sayısı Alt/Üst", "category": "Oyuncu Bahisleri"},
    890: {"name": "Oyuncu Kafayla Gol Atar mı", "category": "Oyuncu Bahisleri"}
}

def parse_full_event_markets(ev):
    """
    Nesine'nin tek bir maç için sunduğu 90+ piyasa ve 400-500+ oran seçeneğini
    tamamen çözümler ve kategorize eder.
    """
    ma_list = ev.get('MA', [])
    categories = {}
    total_odds_count = 0
    
    iyms_labels = {1: '1/1', 2: '1/X', 3: '1/2', 4: 'X/1', 5: 'X/X', 6: 'X/2', 7: '2/1', 8: '2/X', 9: '2/2'}
    cs_labels = {1: '1-X', 2: '1-2', 3: 'X-2'}
    ms_labels = {1: 'MS 1', 2: 'MS X', 3: 'MS 2'}
    uo_labels = {1: 'Alt', 2: 'Üst'}
    kg_labels = {1: 'Var', 2: 'Yok'}
    tc_labels = {1: 'Tek', 2: 'Çift'}
    
    parsed_markets = []
    for ma in ma_list:
        mtid = ma.get('MTID')
        sov = ma.get('SOV')
        mbs = ma.get('MBS', 1)
        oca = ma.get('OCA', [])
        
        info = NESINE_MTID_MAP.get(mtid, {"name": f"Piyasa #{mtid}", "category": "Diğer Bahisler"})
        market_name = info["name"]
        category = info["category"]
        
        sov_str = f" ({sov})" if (sov is not None and sov != 0.0) else ""
        full_title = f"{market_name}{sov_str}"
        
        outcomes = []
        for o in oca:
            n = o.get('N')
            odd_val = o.get('O')
            on = o.get('ON')
            
            if on:
                label = str(on)
            elif mtid == 1:
                label = ms_labels.get(n, f"Seçenek {n}")
            elif mtid == 3:
                label = cs_labels.get(n, f"ÇŞ {n}")
            elif mtid == 5:
                label = iyms_labels.get(n, f"İY/MS {n}")
            elif mtid in [11, 12, 13, 14, 15, 20, 155, 209, 326, 328, 578, 579, 580]:
                label = uo_labels.get(n, f"Gol {n}")
            elif mtid in [38, 287, 288, 452]:
                label = kg_labels.get(n, f"KG {n}")
            elif mtid in [49, 450]:
                label = tc_labels.get(n, f"T/Ç {n}")
            elif mtid in [7, 9]:
                label = f"{'1.Y' if mtid==7 else '2.Y'} {ms_labels.get(n, n)}"
            else:
                label = f"Seçenek {n}"
                
            outcomes.append({
                "n": n,
                "label": label,
                "odd": float(odd_val) if odd_val is not None else 1.0
            })
            total_odds_count += 1
            
        market_obj = {
            "mtid": mtid,
            "title": full_title,
            "category": category,
            "mbs": mbs,
            "outcomes": outcomes
        }
        parsed_markets.append(market_obj)
        
        if category not in categories:
            categories[category] = []
        categories[category].append(market_obj)
        
    return {
        "market_count": len(parsed_markets),
        "odds_count": total_odds_count,
        "categories": categories,
        "markets": parsed_markets
    }
