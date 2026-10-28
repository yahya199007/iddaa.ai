import sys
from models.coupon_optimizer import CouponOptimizer
from models.prediction_engine import PredictionEngine
from data.match_database import load_matches, get_dates

def print_header():
    today_str, tomorrow_str = get_dates()
    print("=" * 70)
    print("      🎯 İDDAA AI MEGA PRO - REKOR KUPON SİSTEMİ (25.000+ ORAN) 🎯")
    print("    1.Y/2.Y KG Evet/Evet | MS & KG (0-0 X & Yok) | Son 5 Maç Analizi")
    print(f"       Tarihler: Bugün ({today_str}) & Yarın ({tomorrow_str})")
    print("=" * 70)

def display_coupon(c):
    print("\n" + "#" * 70)
    print(f"▶ {c['title'].upper()} ({c['badge']})")
    print(f"  Toplam Oran: {c['total_odd']:,.2f} | Model İhtimali: %{c['win_probability']}")
    print(f"  🔥 50 TL ile Tahmini Getiri (Nesine Min. 50 TL): {c['total_odd']*50:,.0f} TL")
    print(f"  💰 100 TL ile Tahmini Getiri: {c['total_odd']*100:,.0f} TL")
    print("-" * 70)
    for i, m in enumerate(c['matches'], 1):
        print(f"  [{i}] {m['match_name']} ({m['league']})")
        print(f"      ⚽ Tercih: {m['pick']}  |  Oran: {m['odd']:.2f}")
        print(f"      💡 Derin Analiz: {m['deep_reason']}")
    print("#" * 70)

def display_bulletin():
    matches = load_matches()
    print("\n" + "=" * 70)
    print("           🌍 NESİNE.COM CANLI BÜLTENİ & SON 5 MAÇIN DEVRE SKORLARI")
    print(f"                       Toplam {len(matches)} Canlı Maç")
    print("=" * 70)
    for m in matches[:20]:
        day_text = "BUGÜN" if m.get("day") == "today" else "YARIN"
        nesine_code = m.get("nesine_code", m["id"])
        print(f"\n📌 [{day_text}] {m['home_team']} vs {m['away_team']} (#{nesine_code} - {m['country']} {m['league']} - {m['match_time']})")
        print(f"   Oranlar -> 1.Y/2.Y KG: {m['odds'].get('both_halves_btts_yes', '-')} | MS & KG (0-0): {m['odds'].get('msX_btts_no', '-')}")
        
        # Son 5 maç özeti
        h_last5 = m['home_stats'].get('last_5', [])
        a_last5 = m['away_stats'].get('last_5', [])
        if h_last5:
            scores_h = " | ".join([f"{g['opp']} {g['score']} (İY:{g['ht']})" for g in h_last5[:3]])
            print(f"   {m['home_team']} Son 3: {scores_h}")
        if a_last5:
            scores_a = " | ".join([f"{g['opp']} {g['score']} (İY:{g['ht']})" for g in a_last5[:3]])
            print(f"   {m['away_team']} Son 3: {scores_a}")

def main():
    optimizer = CouponOptimizer()
    print_header()

    while True:
        today_str, tomorrow_str = get_dates()
        print("\n[MENÜ]:")
        print(f"  1 - Bugünün Efsane Kuponunu Göster (4 Maç 25.000+ Oran - {today_str})")
        print(f"  2 - Yarının Efsane Kuponunu Göster (4 Maç 25.000+ Oran - {tomorrow_str})")
        print(f"  3 - 843.000+ Rekor Sistem Kuponunu Göster (Görsel #2)")
        print(f"  4 - Haftanın Rekor Kombinasyonunu Göster")
        print(f"  5 - Nesine.com Canlı Bültenini İncele")
        print(f"  6 - Nesine.com'dan Canlı Bülteni Yenile / Senkronize Et")
        print(f"  7 - Web Dashboard'u Başlat (Görsel Arayüz)")
        print(f"  0 - Çıkış")
        
        choice = input("\nSeçiminiz (0-7): ").strip()

        if choice == '1':
            coupons = optimizer.generate_all_coupons()
            display_coupon(coupons['today'])
        elif choice == '2':
            coupons = optimizer.generate_all_coupons()
            display_coupon(coupons['tomorrow'])
        elif choice == '3':
            coupons = optimizer.generate_all_coupons()
            display_coupon(coupons['sistem_800k'])
        elif choice == '4':
            coupons = optimizer.generate_all_coupons()
            display_coupon(coupons['mega_all'])
        elif choice == '5':
            display_bulletin()
        elif choice == '6':
            from data.nesine_live_service import fetch_live_nesine_bulletin
            print("Nesine.com'dan canlı bülten çekiliyor...")
            res = fetch_live_nesine_bulletin()
            print(f"✓ Başarıyla {len(res) if res else 0} maç güncellendi.")
        elif choice == '7':
            print("\nWeb Dashboard başlatılıyor... Tarayıcınızda açın: http://127.0.0.1:5000")
            from app import app
            app.run(host="127.0.0.1", port=5000, debug=False)
        elif choice == '0':
            print("\nBol şanslar dileriz!")
            break
        else:
            print("Geçersiz seçim. Lütfen tekrar deneyin.")

if __name__ == "__main__":
    main()
