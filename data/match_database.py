import json
import os
import datetime

def get_dates():
    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)
    return today.strftime("%d.%m.%Y"), tomorrow.strftime("%d.%m.%Y")

def get_default_matches():
    today_str, tomorrow_str = get_dates()
    
    return [
        # ========================================================
        # BUGÜNÜN MAÇLARI (TODAY) - DÜNYA FUTBOLU
        # ========================================================
        {
            "id": "match-today-01",
            "day": "today",
            "date": today_str,
            "match_time": f"{today_str} 17:15",
            "league": "La Liga",
            "country": "🇪🇸 İspanya",
            "home_team": "Villarreal",
            "away_team": "Elche",
            "home_stats": {
                "attack_strength": 1.10,
                "defense_strength": 0.82,
                "form": "DDWLD",
                "home_advantage": 1.12,
                "last_5": [
                    {"opp": "Getafe", "score": "0-0", "ht": "0-0", "sh": "0-0", "btts_both": False, "clean_sheet": True},
                    {"opp": "Mallorca", "score": "1-0", "ht": "0-0", "sh": "1-0", "btts_both": False, "clean_sheet": True},
                    {"opp": "Cadiz", "score": "0-0", "ht": "0-0", "sh": "0-0", "btts_both": False, "clean_sheet": True},
                    {"opp": "Sevilla", "score": "1-1", "ht": "1-0", "sh": "0-1", "btts_both": False, "clean_sheet": False},
                    {"opp": "Alaves", "score": "0-1", "ht": "0-1", "sh": "0-0", "btts_both": False, "clean_sheet": False}
                ]
            },
            "away_stats": {
                "attack_strength": 0.65,
                "defense_strength": 0.88,
                "form": "LDDLD",
                "last_5": [
                    {"opp": "Rayo", "score": "0-0", "ht": "0-0", "sh": "0-0", "btts_both": False, "clean_sheet": True},
                    {"opp": "Osasuna", "score": "0-1", "ht": "0-0", "sh": "0-1", "btts_both": False, "clean_sheet": False},
                    {"opp": "Valladolid", "score": "1-1", "ht": "0-0", "sh": "1-1", "btts_both": False, "clean_sheet": False},
                    {"opp": "Granada", "score": "0-0", "ht": "0-0", "sh": "0-0", "btts_both": False, "clean_sheet": True},
                    {"opp": "Espanyol", "score": "0-2", "ht": "0-1", "sh": "0-1", "btts_both": False, "clean_sheet": False}
                ]
            },
            "odds": {
                "ms1": 1.55, "msX": 4.10, "ms2": 6.20,
                "over25": 2.15, "under25": 1.70,
                "btts_yes": 2.10, "btts_no": 1.65,
                "msX_btts_no": 14.85, # 0-0 Beraberlik (Görseldeki Tercih)
                "both_halves_btts_yes": 18.00,
                "over15": 1.30, "cs1X": 1.12, "csX2": 2.30
            }
        },
        {
            "id": "match-today-02",
            "day": "today",
            "date": today_str,
            "match_time": f"{today_str} 18:30",
            "league": "Allsvenskan",
            "country": "🇸🇪 İsveç",
            "home_team": "AIK Solna",
            "away_team": "IFK Göteborg",
            "home_stats": {
                "attack_strength": 1.40,
                "defense_strength": 1.20,
                "form": "WWDWW",
                "home_advantage": 1.15,
                "last_5": [
                    {"opp": "Hammarby", "score": "2-2", "ht": "1-1", "sh": "1-1", "btts_both": True, "clean_sheet": False},
                    {"opp": "Malmö", "score": "3-2", "ht": "2-1", "sh": "1-1", "btts_both": True, "clean_sheet": False},
                    {"opp": "Djurgarden", "score": "2-1", "ht": "1-1", "sh": "1-0", "btts_both": False, "clean_sheet": False},
                    {"opp": "Häcken", "score": "3-3", "ht": "1-1", "sh": "2-2", "btts_both": True, "clean_sheet": False},
                    {"opp": "Kalmar", "score": "4-2", "ht": "2-1", "sh": "2-1", "btts_both": True, "clean_sheet": False}
                ]
            },
            "away_stats": {
                "attack_strength": 1.35,
                "defense_strength": 1.25,
                "form": "DWWLD",
                "last_5": [
                    {"opp": "Norrköping", "score": "2-2", "ht": "1-1", "sh": "1-1", "btts_both": True, "clean_sheet": False},
                    {"opp": "Elfsborg", "score": "3-2", "ht": "1-1", "sh": "2-1", "btts_both": True, "clean_sheet": False},
                    {"opp": "Sirius", "score": "1-2", "ht": "1-1", "sh": "0-1", "btts_both": False, "clean_sheet": False},
                    {"opp": "Degerfors", "score": "3-1", "ht": "2-1", "sh": "1-0", "btts_both": False, "clean_sheet": False},
                    {"opp": "Värnamo", "score": "2-2", "ht": "1-1", "sh": "1-1", "btts_both": True, "clean_sheet": False}
                ]
            },
            "odds": {
                "ms1": 2.10, "msX": 3.40, "ms2": 3.30,
                "over25": 1.65, "under25": 2.15,
                "btts_yes": 1.55, "btts_no": 2.25,
                "both_halves_btts_yes": 10.65, # Görseldeki Tercih
                "msX_btts_no": 12.50,
                "over15": 1.20, "cs1X": 1.28, "csX2": 1.65
            }
        },
        {
            "id": "match-today-03",
            "day": "today",
            "date": today_str,
            "match_time": f"{today_str} 19:30",
            "league": "Premier League",
            "country": "🇷🇺 Rusya",
            "home_team": "Lokomotiv Moskova",
            "away_team": "Krasnodar",
            "home_stats": {
                "attack_strength": 1.45,
                "defense_strength": 1.30,
                "form": "WWDLW",
                "home_advantage": 1.14,
                "last_5": [
                    {"opp": "Spartak", "score": "3-3", "ht": "1-1", "sh": "2-2", "btts_both": True, "clean_sheet": False},
                    {"opp": "CSKA", "score": "2-2", "ht": "1-1", "sh": "1-1", "btts_both": True, "clean_sheet": False},
                    {"opp": "Zenit", "score": "1-2", "ht": "0-1", "sh": "1-1", "btts_both": False, "clean_sheet": False},
                    {"opp": "Rostov", "score": "3-2", "ht": "2-1", "sh": "1-1", "btts_both": True, "clean_sheet": False},
                    {"opp": "Rubin", "score": "2-1", "ht": "1-0", "sh": "1-1", "btts_both": False, "clean_sheet": False}
                ]
            },
            "away_stats": {
                "attack_strength": 1.50,
                "defense_strength": 1.15,
                "form": "WWWWW",
                "last_5": [
                    {"opp": "Dynamo Moskova", "score": "2-2", "ht": "1-1", "sh": "1-1", "btts_both": True, "clean_sheet": False},
                    {"opp": "Samara", "score": "3-1", "ht": "1-1", "sh": "2-0", "btts_both": False, "clean_sheet": False},
                    {"opp": "Sochi", "score": "3-2", "ht": "2-1", "sh": "1-1", "btts_both": True, "clean_sheet": False},
                    {"opp": "Akhmat", "score": "2-1", "ht": "1-1", "sh": "1-0", "btts_both": False, "clean_sheet": False},
                    {"opp": "Ural", "score": "4-2", "ht": "2-1", "sh": "2-1", "btts_both": True, "clean_sheet": False}
                ]
            },
            "odds": {
                "ms1": 2.65, "msX": 3.45, "ms2": 2.50,
                "over25": 1.60, "under25": 2.20,
                "btts_yes": 1.50, "btts_no": 2.35,
                "both_halves_btts_yes": 14.15, # Görseldeki Tercih
                "msX_btts_no": 13.00,
                "over15": 1.18, "cs1X": 1.45, "csX2": 1.40
            }
        },
        {
            "id": "match-today-04",
            "day": "today",
            "date": today_str,
            "match_time": f"{today_str} 20:30",
            "league": "Bundesliga",
            "country": "🇦🇹 Avusturya",
            "home_team": "SV Ried",
            "away_team": "Austria Wien",
            "home_stats": {
                "attack_strength": 1.30,
                "defense_strength": 1.35,
                "form": "LDWWL",
                "home_advantage": 1.15,
                "last_5": [
                    {"opp": "Salzburg", "score": "2-3", "ht": "1-1", "sh": "1-2", "btts_both": True, "clean_sheet": False},
                    {"opp": "LASK", "score": "2-2", "ht": "1-1", "sh": "1-1", "btts_both": True, "clean_sheet": False},
                    {"opp": "Wolfsberger", "score": "3-1", "ht": "2-0", "sh": "1-1", "btts_both": False, "clean_sheet": False},
                    {"opp": "Hartberg", "score": "2-1", "ht": "1-1", "sh": "1-0", "btts_both": False, "clean_sheet": False},
                    {"opp": "Altach", "score": "1-2", "ht": "0-1", "sh": "1-1", "btts_both": False, "clean_sheet": False}
                ]
            },
            "away_stats": {
                "attack_strength": 1.45,
                "defense_strength": 1.20,
                "form": "WDWWW",
                "last_5": [
                    {"opp": "Sturm Graz", "score": "2-2", "ht": "1-1", "sh": "1-1", "btts_both": True, "clean_sheet": False},
                    {"opp": "Rapid Wien", "score": "3-2", "ht": "2-1", "sh": "1-1", "btts_both": True, "clean_sheet": False},
                    {"opp": "Klagenfurt", "score": "2-1", "ht": "1-1", "sh": "1-0", "btts_both": False, "clean_sheet": False},
                    {"opp": "Tirol", "score": "3-1", "ht": "1-1", "sh": "2-0", "btts_both": False, "clean_sheet": False},
                    {"opp": "Lustenau", "score": "4-2", "ht": "2-1", "sh": "2-1", "btts_both": True, "clean_sheet": False}
                ]
            },
            "odds": {
                "ms1": 3.10, "msX": 3.50, "ms2": 2.15,
                "over25": 1.60, "under25": 2.25,
                "btts_yes": 1.52, "btts_no": 2.30,
                "both_halves_btts_yes": 11.55, # Görseldeki Tercih
                "msX_btts_no": 12.00,
                "over15": 1.18, "cs1X": 1.60, "csX2": 1.30
            }
        },
        {
            "id": "match-today-05",
            "day": "today",
            "date": today_str,
            "match_time": f"{today_str} 15:30",
            "league": "Eredivisie",
            "country": "🇳🇱 Hollanda",
            "home_team": "Ajax",
            "away_team": "Feyenoord",
            "home_stats": {
                "attack_strength": 1.55,
                "defense_strength": 1.15,
                "form": "WWWDW",
                "home_advantage": 1.18,
                "last_5": [
                    {"opp": "PSV", "score": "3-2", "ht": "1-1", "sh": "2-1", "btts_both": True, "clean_sheet": False},
                    {"opp": "AZ Alkmaar", "score": "2-2", "ht": "1-1", "sh": "1-1", "btts_both": True, "clean_sheet": False},
                    {"opp": "Twente", "score": "3-1", "ht": "2-1", "sh": "1-0", "btts_both": False, "clean_sheet": False},
                    {"opp": "Utrecht", "score": "4-3", "ht": "2-2", "sh": "2-1", "btts_both": True, "clean_sheet": False},
                    {"opp": "Heerenveen", "score": "2-1", "ht": "1-1", "sh": "1-0", "btts_both": False, "clean_sheet": False}
                ]
            },
            "away_stats": {
                "attack_strength": 1.50,
                "defense_strength": 1.10,
                "form": "WWDWW",
                "last_5": [
                    {"opp": "Vitesse", "score": "3-2", "ht": "2-1", "sh": "1-1", "btts_both": True, "clean_sheet": False},
                    {"opp": "Sparta", "score": "2-2", "ht": "1-1", "sh": "1-1", "btts_both": True, "clean_sheet": False},
                    {"opp": "Groningen", "score": "3-1", "ht": "1-1", "sh": "2-0", "btts_both": False, "clean_sheet": False},
                    {"opp": "Fortuna", "score": "4-2", "ht": "2-1", "sh": "2-1", "btts_both": True, "clean_sheet": False},
                    {"opp": "NEC", "score": "2-1", "ht": "1-0", "sh": "1-1", "btts_both": False, "clean_sheet": False}
                ]
            },
            "odds": {
                "ms1": 2.25, "msX": 3.75, "ms2": 2.80,
                "over25": 1.45, "under25": 2.55,
                "btts_yes": 1.42, "btts_no": 2.65,
                "both_halves_btts_yes": 9.80,
                "msX_btts_no": 15.00,
                "over15": 1.12, "cs1X": 1.38, "csX2": 1.55
            }
        },
        {
            "id": "match-today-06",
            "day": "today",
            "date": today_str,
            "match_time": f"{today_str} 19:00",
            "league": "Trendyol Süper Lig",
            "country": "🇹🇷 Türkiye",
            "home_team": "Galatasaray",
            "away_team": "Beşiktaş",
            "home_stats": {
                "attack_strength": 1.50,
                "defense_strength": 0.90,
                "form": "WWWWW",
                "home_advantage": 1.22,
                "last_5": [
                    {"opp": "Fenerbahçe", "score": "3-1", "ht": "2-0", "sh": "1-1", "btts_both": False, "clean_sheet": False},
                    {"opp": "Trabzonspor", "score": "2-1", "ht": "1-1", "sh": "1-0", "btts_both": False, "clean_sheet": False},
                    {"opp": "Kasımpaşa", "score": "3-3", "ht": "3-1", "sh": "0-2", "btts_both": False, "clean_sheet": False},
                    {"opp": "Alanyaspor", "score": "2-1", "ht": "1-1", "sh": "1-0", "btts_both": False, "clean_sheet": False},
                    {"opp": "Rizespor", "score": "5-0", "ht": "2-0", "sh": "3-0", "btts_both": False, "clean_sheet": True}
                ]
            },
            "away_stats": {
                "attack_strength": 1.30,
                "defense_strength": 1.00,
                "form": "WWDWW",
                "last_5": [
                    {"opp": "Eyüpspor", "score": "2-1", "ht": "1-0", "sh": "1-1", "btts_both": False, "clean_sheet": False},
                    {"opp": "Kayserispor", "score": "3-0", "ht": "0-0", "sh": "3-0", "btts_both": False, "clean_sheet": True},
                    {"opp": "Göztepe", "score": "2-2", "ht": "1-1", "sh": "1-1", "btts_both": True, "clean_sheet": False},
                    {"opp": "Trabzonspor", "score": "1-1", "ht": "1-1", "sh": "0-0", "btts_both": False, "clean_sheet": False},
                    {"opp": "Sivasspor", "score": "2-0", "ht": "1-0", "sh": "1-0", "btts_both": False, "clean_sheet": True}
                ]
            },
            "odds": {
                "ms1": 1.78, "msX": 3.70, "ms2": 3.85,
                "over25": 1.58, "under25": 2.15,
                "btts_yes": 1.55, "btts_no": 2.20,
                "both_halves_btts_yes": 11.50,
                "msX_btts_no": 12.00,
                "over15": 1.18, "cs1X": 1.20, "csX2": 1.75
            }
        },

        # ========================================================
        # YARININ MAÇLARI (TOMORROW) - DÜNYA FUTBOLU
        # ========================================================
        {
            "id": "match-tom-01",
            "day": "tomorrow",
            "date": tomorrow_str,
            "match_time": f"{tomorrow_str} 21:45",
            "league": "Serie A",
            "country": "🇮🇹 İtalya",
            "home_team": "Roma",
            "away_team": "Inter",
            "home_stats": {
                "attack_strength": 1.35,
                "defense_strength": 1.15,
                "form": "DWWLD",
                "home_advantage": 1.14,
                "last_5": [
                    {"opp": "Monza", "score": "1-1", "ht": "0-0", "sh": "1-1", "btts_both": False, "clean_sheet": False},
                    {"opp": "Venezia", "score": "2-1", "ht": "0-1", "sh": "2-0", "btts_both": False, "clean_sheet": False},
                    {"opp": "Udinese", "score": "3-0", "ht": "1-0", "sh": "2-0", "btts_both": False, "clean_sheet": True},
                    {"opp": "Genoa", "score": "1-1", "ht": "1-0", "sh": "0-1", "btts_both": False, "clean_sheet": False},
                    {"opp": "Juventus", "score": "0-0", "ht": "0-0", "sh": "0-0", "btts_both": False, "clean_sheet": True}
                ]
            },
            "away_stats": {
                "attack_strength": 1.50,
                "defense_strength": 0.95,
                "form": "WWWDW",
                "last_5": [
                    {"opp": "Torino", "score": "3-2", "ht": "2-1", "sh": "1-1", "btts_both": True, "clean_sheet": False},
                    {"opp": "Udinese", "score": "3-2", "ht": "2-1", "sh": "1-1", "btts_both": True, "clean_sheet": False},
                    {"opp": "Milan", "score": "1-2", "ht": "1-1", "sh": "0-1", "btts_both": False, "clean_sheet": False},
                    {"opp": "Monza", "score": "1-1", "ht": "0-0", "sh": "1-1", "btts_both": False, "clean_sheet": False},
                    {"opp": "Atalanta", "score": "4-0", "ht": "2-0", "sh": "2-0", "btts_both": False, "clean_sheet": True}
                ]
            },
            "odds": {
                "ms1": 3.60, "msX": 3.65, "ms2": 2.00,
                "over25": 1.70, "under25": 2.05,
                "btts_yes": 1.62, "btts_no": 2.10,
                "both_halves_btts_yes": 12.50,
                "msX_btts_no": 12.80,
                "over15": 1.22, "cs1X": 1.70, "csX2": 1.25
            }
        },
        {
            "id": "match-tom-02",
            "day": "tomorrow",
            "date": tomorrow_str,
            "match_time": f"{tomorrow_str} 22:00",
            "league": "Premier League",
            "country": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 İngiltere",
            "home_team": "Nottingham Forest",
            "away_team": "Crystal Palace",
            "home_stats": {
                "attack_strength": 0.85,
                "defense_strength": 0.80,
                "form": "DDWLD",
                "home_advantage": 1.12,
                "last_5": [
                    {"opp": "Chelsea", "score": "1-1", "ht": "0-0", "sh": "1-1", "btts_both": False, "clean_sheet": False},
                    {"opp": "Fulham", "score": "0-1", "ht": "0-0", "sh": "0-1", "btts_both": False, "clean_sheet": False},
                    {"opp": "Brighton", "score": "2-2", "ht": "1-2", "sh": "1-0", "btts_both": False, "clean_sheet": False},
                    {"opp": "Liverpool", "score": "1-0", "ht": "0-0", "sh": "1-0", "btts_both": False, "clean_sheet": True},
                    {"opp": "Wolves", "score": "1-1", "ht": "1-1", "sh": "0-0", "btts_both": False, "clean_sheet": False}
                ]
            },
            "away_stats": {
                "attack_strength": 0.75,
                "defense_strength": 0.85,
                "form": "LLDDL",
                "last_5": [
                    {"opp": "Liverpool", "score": "0-1", "ht": "0-1", "sh": "0-0", "btts_both": False, "clean_sheet": False},
                    {"opp": "Everton", "score": "1-2", "ht": "1-0", "sh": "0-2", "btts_both": False, "clean_sheet": False},
                    {"opp": "Man United", "score": "0-0", "ht": "0-0", "sh": "0-0", "btts_both": False, "clean_sheet": True},
                    {"opp": "Leicester", "score": "2-2", "ht": "0-1", "sh": "2-1", "btts_both": False, "clean_sheet": False},
                    {"opp": "Chelsea", "score": "1-1", "ht": "0-1", "sh": "1-0", "btts_both": False, "clean_sheet": False}
                ]
            },
            "odds": {
                "ms1": 2.40, "msX": 3.25, "ms2": 3.00,
                "over25": 2.10, "under25": 1.70,
                "btts_yes": 1.85, "btts_no": 1.85,
                "msX_btts_no": 13.50, # 0-0 Beraberlik Fırsatı
                "both_halves_btts_yes": 19.00,
                "over15": 1.34, "cs1X": 1.35, "csX2": 1.50
            }
        },
        {
            "id": "match-tom-03",
            "day": "tomorrow",
            "date": tomorrow_str,
            "match_time": f"{tomorrow_str} 20:00",
            "league": "Superliga",
            "country": "🇩🇰 Danimarka",
            "home_team": "Aarhus GF",
            "away_team": "Brøndby IF",
            "home_stats": {
                "attack_strength": 1.35,
                "defense_strength": 1.20,
                "form": "DDWWW",
                "home_advantage": 1.15,
                "last_5": [
                    {"opp": "Viborg", "score": "2-2", "ht": "1-1", "sh": "1-1", "btts_both": True, "clean_sheet": False},
                    {"opp": "Randers", "score": "2-2", "ht": "1-1", "sh": "1-1", "btts_both": True, "clean_sheet": False},
                    {"opp": "Silkeborg", "score": "1-1", "ht": "1-1", "sh": "0-0", "btts_both": False, "clean_sheet": False},
                    {"opp": "Nordsjælland", "score": "4-2", "ht": "2-1", "sh": "2-1", "btts_both": True, "clean_sheet": False},
                    {"opp": "Vejle", "score": "3-2", "ht": "1-1", "sh": "2-1", "btts_both": True, "clean_sheet": False}
                ]
            },
            "away_stats": {
                "attack_strength": 1.45,
                "defense_strength": 1.25,
                "form": "WWLDW",
                "last_5": [
                    {"opp": "Midtjylland", "score": "2-2", "ht": "1-1", "sh": "1-1", "btts_both": True, "clean_sheet": False},
                    {"opp": "Copenhagen", "score": "3-1", "ht": "1-1", "sh": "2-0", "btts_both": False, "clean_sheet": False},
                    {"opp": "Silkeborg", "score": "3-3", "ht": "2-1", "sh": "1-2", "btts_both": True, "clean_sheet": False},
                    {"opp": "Randers", "score": "2-1", "ht": "1-1", "sh": "1-0", "btts_both": False, "clean_sheet": False},
                    {"opp": "Vejle", "score": "2-2", "ht": "1-1", "sh": "1-1", "btts_both": True, "clean_sheet": False}
                ]
            },
            "odds": {
                "ms1": 2.60, "msX": 3.45, "ms2": 2.50,
                "over25": 1.62, "under25": 2.15,
                "btts_yes": 1.52, "btts_no": 2.30,
                "both_halves_btts_yes": 11.20, # 1.Y/2.Y KG Evet/Evet
                "msX_btts_no": 12.00,
                "over15": 1.18, "cs1X": 1.45, "csX2": 1.40
            }
        },
        {
            "id": "match-tom-04",
            "day": "tomorrow",
            "date": tomorrow_str,
            "match_time": f"{tomorrow_str} 21:15",
            "league": "Primeira Liga",
            "country": "🇵🇹 Portekiz",
            "home_team": "Braga",
            "away_team": "Sporting CP",
            "home_stats": {
                "attack_strength": 1.40,
                "defense_strength": 1.20,
                "form": "WWDLW",
                "home_advantage": 1.15,
                "last_5": [
                    {"opp": "Porto", "score": "1-2", "ht": "1-1", "sh": "0-1", "btts_both": False, "clean_sheet": False},
                    {"opp": "Rio Ave", "score": "4-0", "ht": "2-0", "sh": "2-0", "btts_both": False, "clean_sheet": True},
                    {"opp": "Nacional", "score": "3-2", "ht": "1-1", "sh": "2-1", "btts_both": True, "clean_sheet": False},
                    {"opp": "Guimaraes", "score": "2-2", "ht": "1-1", "sh": "1-1", "btts_both": True, "clean_sheet": False},
                    {"opp": "Gil Vicente", "score": "0-0", "ht": "0-0", "sh": "0-0", "btts_both": False, "clean_sheet": True}
                ]
            },
            "away_stats": {
                "attack_strength": 1.65,
                "defense_strength": 0.85,
                "form": "WWWWW",
                "last_5": [
                    {"opp": "Casa Pia", "score": "2-0", "ht": "1-0", "sh": "1-0", "btts_both": False, "clean_sheet": True},
                    {"opp": "Estoril", "score": "3-0", "ht": "2-0", "sh": "1-0", "btts_both": False, "clean_sheet": True},
                    {"opp": "AVS", "score": "3-2", "ht": "1-1", "sh": "2-1", "btts_both": True, "clean_sheet": False},
                    {"opp": "Porto", "score": "2-1", "ht": "1-1", "sh": "1-0", "btts_both": False, "clean_sheet": False},
                    {"opp": "Farense", "score": "5-1", "ht": "2-1", "sh": "3-0", "btts_both": False, "clean_sheet": False}
                ]
            },
            "odds": {
                "ms1": 3.75, "msX": 3.80, "ms2": 1.85,
                "over25": 1.55, "under25": 2.30,
                "btts_yes": 1.55, "btts_no": 2.25,
                "both_halves_btts_yes": 12.00, # 1.Y/2.Y KG Evet/Evet
                "msX_btts_no": 14.00,
                "over15": 1.15, "cs1X": 1.78, "csX2": 1.22
            }
        },
        {
            "id": "match-tom-05",
            "day": "tomorrow",
            "date": tomorrow_str,
            "match_time": f"{tomorrow_str} 20:00",
            "league": "Trendyol Süper Lig",
            "country": "🇹🇷 Türkiye",
            "home_team": "Başakşehir",
            "away_team": "Konyaspor",
            "home_stats": {
                "attack_strength": 1.20,
                "defense_strength": 1.10,
                "form": "WLDWD",
                "home_advantage": 1.15,
                "last_5": [
                    {"opp": "Kayserispor", "score": "1-1", "ht": "0-1", "sh": "1-0", "btts_both": False, "clean_sheet": False},
                    {"opp": "Sivasspor", "score": "2-1", "ht": "1-1", "sh": "1-0", "btts_both": False, "clean_sheet": False},
                    {"opp": "Göztepe", "score": "0-0", "ht": "0-0", "sh": "0-0", "btts_both": False, "clean_sheet": True},
                    {"opp": "Trabzonspor", "score": "0-1", "ht": "0-0", "sh": "0-1", "btts_both": False, "clean_sheet": False},
                    {"opp": "Bodrum", "score": "1-0", "ht": "0-0", "sh": "1-0", "btts_both": False, "clean_sheet": True}
                ]
            },
            "away_stats": {
                "attack_strength": 0.90,
                "defense_strength": 1.15,
                "form": "LLWDL",
                "last_5": [
                    {"opp": "Eyüpspor", "score": "2-1", "ht": "1-0", "sh": "1-1", "btts_both": False, "clean_sheet": False},
                    {"opp": "Trabzonspor", "score": "2-3", "ht": "1-1", "sh": "1-2", "btts_both": True, "clean_sheet": False},
                    {"opp": "Sivasspor", "score": "0-0", "ht": "0-0", "sh": "0-0", "btts_both": False, "clean_sheet": True},
                    {"opp": "Samsunspor", "score": "0-1", "ht": "0-1", "sh": "0-0", "btts_both": False, "clean_sheet": False},
                    {"opp": "Kayserispor", "score": "0-0", "ht": "0-0", "sh": "0-0", "btts_both": False, "clean_sheet": True}
                ]
            },
            "odds": {
                "ms1": 1.80, "msX": 3.45, "ms2": 4.10,
                "over25": 1.85, "under25": 1.85,
                "btts_yes": 1.78, "btts_no": 1.90,
                "msX_btts_no": 11.00,
                "both_halves_btts_yes": 15.00,
                "over15": 1.25, "cs1X": 1.20, "csX2": 1.78
            }
        },
        {
            "id": "match-tom-06",
            "day": "tomorrow",
            "date": tomorrow_str,
            "match_time": f"{tomorrow_str} 21:00",
            "league": "2. Bundesliga",
            "country": "🇩🇪 Almanya",
            "home_team": "Hamburger SV",
            "away_team": "Magdeburg",
            "home_stats": {
                "attack_strength": 1.55,
                "defense_strength": 1.25,
                "form": "WDWWW",
                "home_advantage": 1.20,
                "last_5": [
                    {"opp": "Düsseldorf", "score": "3-2", "ht": "1-1", "sh": "2-1", "btts_both": True, "clean_sheet": False},
                    {"opp": "Paderborn", "score": "2-2", "ht": "1-1", "sh": "1-1", "btts_both": True, "clean_sheet": False},
                    {"opp": "Kaiserslautern", "score": "2-2", "ht": "1-1", "sh": "1-1", "btts_both": True, "clean_sheet": False},
                    {"opp": "Regensburg", "score": "5-0", "ht": "2-0", "sh": "3-0", "btts_both": False, "clean_sheet": True},
                    {"opp": "Münster", "score": "4-1", "ht": "2-1", "sh": "2-0", "btts_both": False, "clean_sheet": False}
                ]
            },
            "away_stats": {
                "attack_strength": 1.45,
                "defense_strength": 1.20,
                "form": "DWWDW",
                "last_5": [
                    {"opp": "Greuther Fürth", "score": "2-2", "ht": "1-1", "sh": "1-1", "btts_both": True, "clean_sheet": False},
                    {"opp": "Darmstadt", "score": "2-1", "ht": "1-1", "sh": "1-0", "btts_both": False, "clean_sheet": False},
                    {"opp": "Karlsruhe", "score": "2-2", "ht": "1-1", "sh": "1-1", "btts_both": True, "clean_sheet": False},
                    {"opp": "Köln", "score": "2-1", "ht": "0-1", "sh": "2-0", "btts_both": False, "clean_sheet": False},
                    {"opp": "Nürnberg", "score": "4-0", "ht": "1-0", "sh": "3-0", "btts_both": False, "clean_sheet": True}
                ]
            },
            "odds": {
                "ms1": 1.95, "msX": 3.85, "ms2": 3.25,
                "over25": 1.45, "under25": 2.50,
                "btts_yes": 1.42, "btts_no": 2.60,
                "both_halves_btts_yes": 9.50,
                "msX_btts_no": 16.00,
                "over15": 1.12, "cs1X": 1.28, "csX2": 1.72
            }
        }
    ]

DATA_FILE = os.path.join(os.path.dirname(__file__), "matches.json")

def load_matches():
    # Günlük dinamik maçları yükle
    default_matches = get_default_matches()
    if not os.path.exists(DATA_FILE):
        save_matches(default_matches)
        return default_matches
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Eğer eski format veya boşsa sıfırla
            if not data or len(data) < 5 or "day" not in data[0]:
                save_matches(default_matches)
                return default_matches
            return data
    except Exception:
        save_matches(default_matches)
        return default_matches

def save_matches(matches):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(matches, f, ensure_ascii=False, indent=2)

def get_matches_by_day(day="today"):
    matches = load_matches()
    return [m for m in matches if m.get("day") == day]

def get_match_by_id(match_id):
    matches = load_matches()
    for m in matches:
        if m["id"] == match_id:
            return m
    return None

def add_match(match_data):
    matches = load_matches()
    match_id = f"custom-{len(matches) + 1}"
    match_data["id"] = match_id
    matches.append(match_data)
    save_matches(matches)
    return match_data

def reset_database():
    default_matches = get_default_matches()
    save_matches(default_matches)
    return default_matches
