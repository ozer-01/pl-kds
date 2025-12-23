"""
=============================================================================
CONFIG.PY - SABİTLER VE YAPILANDIRMA AYARLARI
=============================================================================

Bu modül, uygulama genelinde kullanılan tüm sabit değerleri,
taktik konfigürasyonlarını ve renk şemalarını içerir.

FC26 verisine göre ALT POZİSYONLAR desteklenir:
- GK: Kaleci
- CB: Stoper (Central Back)
- LB: Sol Bek (Left Back)
- RB: Sağ Bek (Right Back)
- DM: Defansif Orta Saha (Defensive Midfielder)
- CM: Merkez Orta Saha (Central Midfielder)
- CAM: Ofansif Orta Saha (Central Attacking Midfielder)
- LM: Sol Kanat Orta Saha (Left Midfielder)
- RM: Sağ Kanat Orta Saha (Right Midfielder)
- LW: Sol Kanat (Left Wing)
- RW: Sağ Kanat (Right Wing)
- ST: Santrafor (Striker)
=============================================================================
"""

# =============================================================================
# ALT POZİSYON GRUPLARI
# =============================================================================

# Ana kategoriler ve içerdiği alt pozisyonlar
POSITION_GROUPS = {
    'GK': ['GK'],
    'DEF': ['CB', 'LB', 'RB'],
    'MID': ['DM', 'CM', 'CAM', 'LM', 'RM'],
    'FWD': ['LW', 'RW', 'ST']
}

# Alt pozisyondan ana gruba çeviri
SUB_POS_TO_GROUP = {
    'GK': 'GK',
    'CB': 'DEF', 'LB': 'DEF', 'RB': 'DEF',
    'DM': 'MID', 'CM': 'MID', 'CAM': 'MID', 'LM': 'MID', 'RM': 'MID',
    'LW': 'FWD', 'RW': 'FWD', 'ST': 'FWD'
}

# Esnek pozisyon eşleştirmesi: Bir POZİSYONA hangi oyuncular ATANABİLİR
# GERÇEKÇI KURALLAR:
# - Defans pozisyonları KATI (LB sadece LB, RB sadece RB, CB sadece CB)
# - Orta saha biraz esnek (DM/CM/CAM arası geçiş olabilir)
# - Kanatlar esnek (LM/LW, RM/RW arası geçiş olabilir)
# - Forvetler esnek (ST, kanatlardan oyuncu alabilir)
POSITION_CAN_BE_FILLED_BY = {
    # KATI DEFANS - Robertson (LB) sadece LB'de!
    'GK': ['GK'],
    'CB': ['CB'],
    'LB': ['LB'],                          # SADECE LB - Robertson, Kerkez burada
    'RB': ['RB'],                          # SADECE RB - Alexander-Arnold, Frimpong burada
    
    # ESNEK ORTA SAHA
    'DM': ['DM', 'CM'],                    # DM veya CM oynayabilir
    'CM': ['CM', 'DM', 'CAM'],             # CM esnek
    'CAM': ['CAM', 'CM'],                  # CAM veya CM
    
    # ESNEK KANATLAR
    'LM': ['LM', 'LW'],                    # Sol taraf oyuncuları
    'RM': ['RM', 'RW'],                    # Sağ taraf oyuncuları
    
    # ESNEK HÜCUM
    'LW': ['LW', 'LM', 'ST'],              # Sol kanat veya forvet
    'RW': ['RW', 'RM', 'ST'],              # Sağ kanat veya forvet
    'ST': ['ST', 'LW', 'RW', 'CAM']        # Santrafor, kanatlar veya ofansif orta
}

# Geriye uyumluluk için - bir oyuncu hangi pozisyonlarda oynayabilir
FLEXIBLE_POSITIONS = POSITION_CAN_BE_FILLED_BY.copy()

# =============================================================================
# TAKTİK KONFİGÜRASYONLARI (ALT POZİSYONLU)
# =============================================================================

# Her formasyon için detaylı alt pozisyon gereksinimleri
FORMATIONS = {
    '4-4-2': {
        'GK': 1,
        'CB': 2, 'LB': 1, 'RB': 1,           # 4 Defans
        'CM': 2, 'LM': 1, 'RM': 1,           # 4 Orta Saha
        'ST': 2                               # 2 Forvet
    },
    '4-3-3': {
        'GK': 1,
        'CB': 2, 'LB': 1, 'RB': 1,           # 4 Defans
        'CM': 2, 'DM': 1,                     # 3 Orta Saha (1 DM + 2 CM)
        'LW': 1, 'RW': 1, 'ST': 1            # 3 Forvet
    },
    '3-5-2': {
        'GK': 1,
        'CB': 3,                              # 3 Stoper
        'LM': 1, 'RM': 1, 'CM': 2, 'DM': 1,  # 5 Orta Saha (Kanat bekler dahil)
        'ST': 2                               # 2 Forvet
    },
    '5-3-2': {
        'GK': 1,
        'CB': 3, 'LB': 1, 'RB': 1,           # 5 Defans
        'CM': 2, 'DM': 1,                     # 3 Orta Saha
        'ST': 2                               # 2 Forvet
    },
    '4-2-3-1': {
        'GK': 1,
        'CB': 2, 'LB': 1, 'RB': 1,           # 4 Defans
        'DM': 2, 'CAM': 1, 'LM': 1, 'RM': 1, # 5 Orta Saha (2 DM + 1 CAM + 2 Kanat)
        'ST': 1                               # 1 Forvet
    },
    '3-4-3': {
        'GK': 1,
        'CB': 3,                              # 3 Stoper
        'LM': 1, 'RM': 1, 'CM': 2,           # 4 Orta Saha
        'LW': 1, 'RW': 1, 'ST': 1            # 3 Forvet
    }
}

# Her formasyondaki toplam ana grup sayıları (doğrulama için)
FORMATION_GROUPS = {
    '4-4-2': {'GK': 1, 'DEF': 4, 'MID': 4, 'FWD': 2},
    '4-3-3': {'GK': 1, 'DEF': 4, 'MID': 3, 'FWD': 3},
    '3-5-2': {'GK': 1, 'DEF': 3, 'MID': 5, 'FWD': 2},
    '5-3-2': {'GK': 1, 'DEF': 5, 'MID': 3, 'FWD': 2},
    '4-2-3-1': {'GK': 1, 'DEF': 4, 'MID': 5, 'FWD': 1},
    '3-4-3': {'GK': 1, 'DEF': 3, 'MID': 4, 'FWD': 3}
}

# Formasyon açıklamaları (UI için)
FORMATION_DESCRIPTIONS = {
    '4-4-2': "Klasik ve dengeli diziliş - 2 CB, 2 Bek, 2 CM, 2 Kanat, 2 ST",
    '4-3-3': "Ofansif, kanat ataklarına uygun - DM destekli, 3 forvet",
    '3-5-2': "Orta saha hakimiyeti - 3 stoper, 5 orta saha (kanat bekler)",
    '5-3-2': "Savunma odaklı, kontra atak - 5 savunmacı, 2 santrafor",
    '4-2-3-1': "Modern, kontrol odaklı - Çifte DM, tek santrafor",
    '3-4-3': "Çok ofansif, risk yüksek - 3 stoper, 3 forvet"
}

# =============================================================================
# SAHA ÜZERİNDEKİ POZİSYON KOORDİNATLARI (ALT POZİSYONLU)
# =============================================================================

# Her formasyon için alt pozisyon koordinatları (x, y)
# Saha boyutları: 120x80, orta nokta: (60, 40)
FORMATION_POSITIONS = {
    '4-4-2': {
        'GK': [(10, 40)],
        'CB': [(30, 30), (30, 50)],               # 2 Stoper
        'LB': [(30, 70)],                          # Sol Bek
        'RB': [(30, 10)],                          # Sağ Bek
        'CM': [(55, 30), (55, 50)],               # 2 Merkez Orta Saha
        'LM': [(55, 70)],                          # Sol Kanat
        'RM': [(55, 10)],                          # Sağ Kanat
        'ST': [(90, 30), (90, 50)]                # 2 Santrafor
    },
    '4-3-3': {
        'GK': [(10, 40)],
        'CB': [(28, 30), (28, 50)],
        'LB': [(28, 70)],
        'RB': [(28, 10)],
        'DM': [(50, 40)],                          # Defansif Orta Saha
        'CM': [(60, 25), (60, 55)],               # 2 Merkez Orta Saha
        'LW': [(90, 65)],                          # Sol Kanat
        'RW': [(90, 15)],                          # Sağ Kanat
        'ST': [(95, 40)]                           # Santrafor
    },
    '3-5-2': {
        'GK': [(10, 40)],
        'CB': [(28, 25), (28, 40), (28, 55)],     # 3 Stoper
        'LM': [(55, 72)],                          # Sol Kanat Bek
        'RM': [(55, 8)],                           # Sağ Kanat Bek
        'DM': [(50, 40)],                          # Defansif Orta Saha
        'CM': [(60, 28), (60, 52)],               # 2 Merkez Orta Saha
        'ST': [(90, 30), (90, 50)]                # 2 Santrafor
    },
    '5-3-2': {
        'GK': [(10, 40)],
        'CB': [(28, 25), (28, 40), (28, 55)],     # 3 Stoper
        'LB': [(32, 72)],                          # Sol Bek
        'RB': [(32, 8)],                           # Sağ Bek
        'DM': [(50, 40)],                          # Defansif Orta Saha
        'CM': [(60, 28), (60, 52)],               # 2 Merkez Orta Saha
        'ST': [(90, 30), (90, 50)]                # 2 Santrafor
    },
    '4-2-3-1': {
        'GK': [(10, 40)],
        'CB': [(28, 30), (28, 50)],
        'LB': [(28, 70)],
        'RB': [(28, 10)],
        'DM': [(48, 30), (48, 50)],               # 2 Defansif Orta Saha
        'CAM': [(68, 40)],                         # Ofansif Orta Saha
        'LM': [(70, 68)],                          # Sol Kanat
        'RM': [(70, 12)],                          # Sağ Kanat
        'ST': [(95, 40)]                           # Santrafor
    },
    '3-4-3': {
        'GK': [(10, 40)],
        'CB': [(28, 25), (28, 40), (28, 55)],     # 3 Stoper
        'LM': [(55, 70)],                          # Sol Kanat
        'RM': [(55, 10)],                          # Sağ Kanat
        'CM': [(55, 32), (55, 48)],               # 2 Merkez Orta Saha
        'LW': [(90, 65)],                          # Sol Kanat Forvet
        'RW': [(90, 15)],                          # Sağ Kanat Forvet
        'ST': [(95, 40)]                           # Santrafor
    }
}

# =============================================================================
# STRATEJİ AĞIRLIKLARI
# =============================================================================

# Optimizasyon için strateji bazlı ağırlık katsayıları
STRATEGY_WEIGHTS = {
    'Ofansif': {'ofans': 0.5, 'defans': 0.2, 'form': 0.3},
    'Defansif': {'ofans': 0.2, 'defans': 0.5, 'form': 0.3},
    'Dengeli': {'ofans': 0.35, 'defans': 0.35, 'form': 0.3}
}

# Strateji açıklamaları (UI için)
STRATEGY_DESCRIPTIONS = {
    'Ofansif': "⚔️ Ofans: 50% | 🛡️ Defans: 20% | 📊 Form: 30%",
    'Defansif': "⚔️ Ofans: 20% | 🛡️ Defans: 50% | 📊 Form: 30%",
    'Dengeli': "⚔️ Ofans: 35% | 🛡️ Defans: 35% | 📊 Form: 30%"
}

# =============================================================================
# RENK ŞEMALARI
# =============================================================================

# Ana tema renkleri
COLORS = {
    'primary_green': '#1a472a',
    'secondary_green': '#2d5a3d',
    'accent_gold': '#d4af37',
    'light_green': '#90ee90',
    'pitch_green': '#228B22',
    'dark_bg': '#0d2818'
}

# Pozisyon renkleri (Alt pozisyonlar dahil)
POSITION_COLORS = {
    # Kaleci
    'GK': '#ff6b6b',
    # Defans
    'CB': '#4dabf7',
    'LB': '#74c0fc',
    'RB': '#74c0fc',
    # Orta Saha
    'DM': '#69db7c',
    'CM': '#51cf66',
    'CAM': '#40c057',
    'LM': '#8ce99a',
    'RM': '#8ce99a',
    # Forvet
    'LW': '#ffe066',
    'RW': '#ffe066',
    'ST': '#ffd43b'
}

# Ana grup renkleri (basit görünüm için)
GROUP_COLORS = {
    'GK': '#ff6b6b',   # Kırmızı - Kaleci
    'DEF': '#4dabf7',  # Mavi - Defans
    'MID': '#51cf66',  # Yeşil - Orta Saha
    'FWD': '#ffd43b'   # Sarı - Forvet
}

# =============================================================================
# SAHA BOYUTLARI
# =============================================================================

PITCH_LENGTH = 120
PITCH_WIDTH = 80
PITCH_MARGIN = 3

# =============================================================================
# FC26 RATING BAZLI HESAPLAMALAR
# =============================================================================

# Rating'e göre fiyat çarpanları
RATING_PRICE_MULTIPLIER = {
    (90, 100): 80.0,   # 90+ rating: 80M+ baz
    (85, 90): 50.0,    # 85-89: 50M+ baz
    (80, 85): 25.0,    # 80-84: 25M+ baz
    (75, 80): 12.0,    # 75-79: 12M+ baz
    (70, 75): 5.0,     # 70-74: 5M+ baz
    (0, 70): 2.0       # 70 altı: 2M+ baz
}

# Pozisyon bazlı fiyat çarpanı
POSITION_PRICE_MULTIPLIER = {
    'GK': 0.7,
    'CB': 0.9, 'LB': 0.85, 'RB': 0.85,
    'DM': 1.0, 'CM': 1.1, 'CAM': 1.15, 'LM': 0.9, 'RM': 0.9,
    'LW': 1.2, 'RW': 1.2, 'ST': 1.3
}

# =============================================================================
# UI AYARLARI
# =============================================================================

PAGE_CONFIG = {
    'page_title': "⚽ Premier Lig Kadro Optimizasyonu KDS",
    'page_icon': "⚽",
    'layout': "wide",
    'initial_sidebar_state': "expanded"
}

# Plotly grafik ayarları
PLOTLY_CONFIG = {
    'displayModeBar': True,
    'displaylogo': False,
    'modeBarButtonsToRemove': ['autoScale2d', 'resetScale2d'],
    'staticPlot': False,
    'responsive': True
}

PITCH_FIGURE_SIZE = {
    'width': 750,
    'height': 500
}

# =============================================================================
# VERİ SETİ AYARLARI
# =============================================================================

# FC26 veri dosyası
FC26_DATA_FILE = "Player-positions.csv"
MARKET_VALUE_FILE = "premier_league_players_tf.csv"

# Premier League takımları (FC26 verisinden)
PREMIER_LEAGUE_TEAMS = [
    "Arsenal", "Aston Villa", "AFC Bournemouth", "Brentford", "Brighton & Hove Albion",
    "Burnley", "Chelsea", "Crystal Palace", "Everton", "Fulham",
    "Leeds United", "Liverpool", "Manchester City", "Manchester United",
    "Newcastle United", "Nottingham Forest", "Southampton", "Sunderland",
    "Tottenham Hotspur", "West Ham United", "Wolverhampton Wanderers"
]

# Sakatlık oranı (rastgele atama için)
INJURY_PROBABILITY = 0.08

# =============================================================================
# YENİ İSTATİSTİK VERİSİ AYARLARI
# =============================================================================

# CSV'deki sütun isimleri ile bizim metricslerimiz arasındaki eşleştirme
# Sol taraf: Bizim kodda kullanacağımız isim
# Sağ taraf: CSV dosyasındaki gerçek sütun ismi
CSV_COLUMN_MAPPING = {
    'Player': 'web_name',          # Veya 'second_name'
    'Team': 'team_code',           # Takım kodu (eşleştirme gerekecek)
    'xG': 'expected_goals',
    'xA': 'expected_assists',
    'goals': 'goals_scored',
    'assists': 'assists',
    'clean_sheets': 'clean_sheets',
    'goals_conceded': 'goals_conceded',
    'own_goals': 'own_goals',
    'penalties_saved': 'penalties_saved',
    'penalties_missed': 'penalties_missed',
    'yellow_cards': 'yellow_cards',
    'red_cards': 'red_cards',
    'saves': 'saves',
    'bonus': 'bonus',
    'bps': 'bps',
    'influence': 'influence',
    'creativity': 'creativity',
    'threat': 'threat',
    'ict_index': 'ict_index',
    'starts': 'starts',
    'minutes': 'minutes',
    
    # Savunma Metrikleri (Mevcutsa)
    'tackles': 'tackles',
    'recoveries': 'recoveries', # Interceptions yerine proxy
    
    # Oranlar (Hesaplanacak)
    # 'xG_per_90': 'expected_goals_per_90',
    # 'xA_per_90': 'expected_assists_per_90'
}

# Kullanıcının tanımladığı Pozisyonel Ağırlıklar
# Eğer bir metrik CSV'de yoksa, data_handler'da 0 kabul edilecek
POSITIONAL_WEIGHTS = {
    # DEFANS
    'LB': {
        'tackles': 0.25, 
        'recoveries': 0.25,      # Defensive duels proxy
        'creativity': 0.2,       # Progressive carries/dribbles proxy
        'clean_sheets': 0.15,
        'xA': 0.15
    },
    'RB': {
        'tackles': 0.25, 
        'recoveries': 0.25, 
        'creativity': 0.2, 
        'clean_sheets': 0.15,
        'xA': 0.15
    },
    'CB': {
        'tackles': 0.3,
        'recoveries': 0.3,
        'clean_sheets': 0.2,
        'blocks': 0.1,           # Blocks yoksa 0 gelir
        'aerial_won': 0.1        # Eğer yoksa 0
    },
    'GK': {
        'clean_sheets': 0.4,
        'saves': 0.4,
        'bonus': 0.2
    },
    
    # ORTA SAHA
    'DM': {
        'tackles': 0.3,
        'recoveries': 0.3,       # Interceptions proxy
        'bps': 0.2,
        'pass_completion': 0.2   # Eğer yoksa ict_index veya influence kullanılabilir
    },
    'CM': {
        'influence': 0.3, 
        'creativity': 0.3,
        'tackles': 0.2,
        'xA': 0.2
    },
    'CAM': {
        'creativity': 0.3,        # Key passes proxy
        'xA': 0.3,
        'threat': 0.2,            # SCA proxy
        'goals': 0.1,
        'assists': 0.1
    },
    'LM': {
        'creativity': 0.3,
        'threat': 0.3,
        'xA': 0.2,
        'goals': 0.2
    },
    'RM': {
        'creativity': 0.3,
        'threat': 0.3,
        'xA': 0.2,
        'goals': 0.2
    },
    
    # FORVET
    'LW': {
        'xG': 0.3,
        'goals': 0.3,
        'threat': 0.2,
        'creativity': 0.1,
        'touches_in_box': 0.1
    },
    'RW': {
        'xG': 0.3,
        'goals': 0.3,
        'threat': 0.2,
        'creativity': 0.1,
        'touches_in_box': 0.1
    },
    'ST': {
        'xG': 0.4,
        'goals': 0.3,
        'threat': 0.2,         # Shots proxy
        'bps': 0.1
    }
}

# =============================================================================
# GÖRSEL İKON TANIMLAMALARI (UI İÇİN)
# =============================================================================

# SADECE GÖRÜNÜM İÇİN İKON EŞLEŞTİRMESİ
# Bu sözlük sadece ekrana yazı yazdırırken kullanılacak.
# Mantık katmanında (optimization) asla bu ikonlu stringler kullanılmamalıdır.
DISPLAY_ICONS = {
    # Mevkiler
    'GK':  '<i class="fas fa-hand-paper"></i>',      # Eldiven
    'CB':  '<i class="fas fa-shield-virus"></i>',    # Kalkan
    'LB':  '<i class="fas fa-shield-alt"></i>',
    'RB':  '<i class="fas fa-shield-alt"></i>',
    'DM':  '<i class="fas fa-anchor"></i>',          # Çapa
    'CM':  '<i class="fas fa-random"></i>',          # Pas/Dağıtım
    'CAM': '<i class="fas fa-magic"></i>',           # Sihirbaz
    'LM':  '<i class="fas fa-bolt"></i>',            # Hız
    'RM':  '<i class="fas fa-bolt"></i>',
    'LW':  '<i class="fas fa-running"></i>',         # Koşu
    'RW':  '<i class="fas fa-running"></i>',
    'ST':  '<i class="fas fa-futbol"></i>',          # Gol
    
    # Gruplar
    'DEF': '<i class="fas fa-shield-alt"></i>',
    'MID': '<i class="fas fa-cogs"></i>',
    'FWD': '<i class="fas fa-bullseye"></i>',
    
    # Metrikler
    'score': '<i class="fas fa-star"></i>',
    'cost': '<i class="fas fa-coins"></i>',
    'rating': '<i class="fas fa-medal"></i>',
    'form': '<i class="fas fa-fire-alt"></i>',
    'money': '<i class="fas fa-sack-dollar"></i>',
    'chart': '<i class="fas fa-chart-line"></i>',
    
    # Genel
    'app_logo': '<i class="fas fa-futbol"></i>',
    'check': '<i class="fas fa-check-circle"></i>',
    'warning': '<i class="fas fa-exclamation-triangle"></i>',
    
    # Yeni Eklenenler (Kullanıcı İsteği)
    'panel': '<i class="fas fa-sliders-h"></i>',
    'stadium': '<i class="fas fa-landmark"></i>',
    'group': '<i class="fas fa-users"></i>',
    'healthy': '<i class="fas fa-user-check"></i>',
    'tactics': '<i class="fas fa-clipboard-list"></i>',
    'info': '<i class="fas fa-info-circle"></i>',
    'budget': '<i class="fas fa-wallet"></i>',
    'bulb': '<i class="fas fa-lightbulb"></i>', # 💡
    'target': '<i class="fas fa-crosshairs"></i>', # 🎯
    'ruler': '<i class="fas fa-ruler-combined"></i>', # 📐
    'book': '<i class="fas fa-book-open"></i>',
    'lock': '<i class="fas fa-lock"></i>',
    'gear': '<i class="fas fa-cog"></i>',
    'search': '<i class="fas fa-search"></i>',
    'sort': '<i class="fas fa-sort"></i>',
    'filter': '<i class="fas fa-filter"></i>'
}
