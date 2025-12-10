"""
=============================================================================
DATA_HANDLER.PY - PREMIER LEAGUE VERİ YÜKLEME VE İŞLEME
=============================================================================

Bu modül, oyundan çekilen veriyi işler:
- Player-positions.csv dosyasını yükler
- Rating'den Form, Fiyat, Ofans, Defans hesaplar
- Alt pozisyonları (Sub_Pos) kullanır
- Min-Max Normalizasyon uygular
- GitHub'dan alınan GERÇEK İSTATİSTİKLERİ (xG, xA, vb.) entegre eder

ALT POZİSYONLAR:
- GK: Kaleci
- CB, LB, RB: Defans
- DM, CM, CAM, LM, RM: Orta Saha  
- LW, RW, ST: Forvet
=============================================================================
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional
from difflib import get_close_matches

from .config import (
    POSITION_PRICE_MULTIPLIER, 
    SUB_POS_TO_GROUP,
    INJURY_PROBABILITY,
    PREMIER_LEAGUE_TEAMS,
    MARKET_VALUE_FILE,
    CSV_COLUMN_MAPPING,
    POSITIONAL_WEIGHTS
)


def _parse_market_value(value_str: str) -> float:
    """
    Format stringini float'a çevirir (Milyon Euro cinsinden).
    Örnekler:
    - '€180.00m' -> 180.0
    - '€350k' -> 0.35
    - '€1.50m' -> 1.5
    """
    if pd.isna(value_str) or not isinstance(value_str, str):
        return 0.0
        
    # Temizle
    s = value_str.lower().replace('€', '').strip()
    
    try:
        if 'm' in s:
            return float(s.replace('m', '').strip())
        elif 'k' in s:
            return float(s.replace('k', '').strip()) / 1000.0
        else:
            return float(s)
    except:
        return 0.0


def load_market_values() -> Optional[pd.DataFrame]:
    """
    Gerçek piyasa değerlerini içeren CSV'yi yükler.
    """
    try:
        base_path = Path(__file__).parent.parent
        csv_path = base_path / "data" / MARKET_VALUE_FILE
        
        if not csv_path.exists():
            print(f"Uyarı: {MARKET_VALUE_FILE} bulunamadı.")
            return None
            
        df = pd.read_csv(csv_path)
        
        # Piyasa değeri sütununu parse et (Market Value)
        if 'Market Value' in df.columns:
            df['parsed_value'] = df['Market Value'].apply(_parse_market_value)
            
        return df
    except Exception as e:
        print(f"Market value yükleme hatası: {e}")
        return None


def merge_market_values(fc26_df: pd.DataFrame, market_df: pd.DataFrame) -> pd.DataFrame:
    """
    Oyun veri seti ile gerçek piyasa değerlerini birleştirir.
    """
    if market_df is None or 'parsed_value' not in market_df.columns:
        return fc26_df
        
    market_df = market_df.copy()
    
    # İsim listeleri
    market_names = market_df['Player Name'].tolist() if 'Player Name' in market_df.columns else []
    
    def find_price(row):
        player_name = row['Oyuncu']
        
        # 1. Tam eşleşme
        match = market_df[market_df['Player Name'] == player_name]
        if not match.empty:
            return match.iloc[0]['parsed_value']
            
        # 2. Fuzzy match
        matches = get_close_matches(player_name, market_names, n=1, cutoff=0.7)
        if matches:
            return market_df[market_df['Player Name'] == matches[0]].iloc[0]['parsed_value']
            
        return None

    matches_found = 0
    
    # Fiyat sütununu güncelle (önce mevcut hesaplanan fiyatı yedekle istersen)
    # Biz direkt üzerine yazacağız ama eşleşme varsa. Yoksa eski calculated kalır.
    
    for idx, row in fc26_df.iterrows():
        real_price = find_price(row)
        
        if real_price is not None and real_price > 0:
            # Euro'dan Sterlin'e çevirelim mi? Şimdilik direkt alıyoruz (Birim £ kabul edelim)
            # Eğer veri Euro ise ve oyun Sterlin ise yaklaşık 0.85 ile çarpabiliriz.
            # Veri '€' içeriyor, oyun £ kullanıyor.
            converted_price = real_price * 0.85
            fc26_df.at[idx, 'Fiyat_M'] = round(converted_price, 1)
            matches_found += 1
            
    print(f"Toplam {len(fc26_df)} oyuncudan {matches_found} tanesinin piyasa değeri güncellendi.")
    
    return fc26_df


def load_fc26_data(csv_path: str = None) -> pd.DataFrame:
    """
    Oyundan çekilen oyuncu verilerini yükler ve işler.
    
    Bu fonksiyon CSV dosyasındaki ham veriyi alır ve optimizasyon için
    gerekli formata dönüştürür:
    - Sub_Pos'u standartlaştırır (CDM -> DM)
    - Rating'den Fiyat, Form, Ofans, Defans puanları hesaplar
    - Rastgele sakatlık durumu atar
    - GERÇEK SEZON İSTATİSTİKLERİNİ EKLER
    
    Args:
        csv_path: CSV dosya yolu (varsayılan: data/Player-positions.csv)
        
    Returns:
        pd.DataFrame: İşlenmiş oyuncu verileri
    """
    
    # Varsayılan dosya yolu
    if csv_path is None:
        base_path = Path(__file__).parent.parent
        csv_path = base_path / "data" / "Player-positions.csv"
    
    # CSV dosyasını oku
    df = pd.read_csv(csv_path)
    
    # ==========================================================================
    # SÜTUN İSİMLERİNİ STANDARTLAŞTIR
    # ==========================================================================
    
    df = df.rename(columns={
        'Player': 'Oyuncu',
        'Team': 'Takim',
        'Sub_Pos': 'Alt_Pozisyon',
        'Group': 'Mevki'
    })
    
    # ==========================================================================
    # ALT POZİSYON STANDARTLAŞTIRMA
    # ==========================================================================
    
    def standardize_sub_pos(pos):
        """CDM -> DM dönüşümü ve diğer standartlaştırmalar"""
        pos = str(pos).upper().strip()
        
        # CDM -> DM dönüşümü (Oyunda CDM kullanılıyor)
        if pos == 'CDM':
            return 'DM'
        
        # Diğer geçerli pozisyonlar
        valid_positions = ['GK', 'CB', 'LB', 'RB', 'DM', 'CM', 'CAM', 'LM', 'RM', 'LW', 'RW', 'ST']
        
        if pos in valid_positions:
            return pos
        
        # Varsayılan
        return 'CM'
    
    df['Alt_Pozisyon'] = df['Alt_Pozisyon'].apply(standardize_sub_pos)
    
    # ==========================================================================
    # SADECE PREMIER LEAGUE TAKIMLARINI FİLTRELE
    # ==========================================================================
    
    # Premier League takımlarını filtrele (isteğe bağlı)
    # df = df[df['Takim'].isin(PREMIER_LEAGUE_TEAMS)].copy()
    
    # ==========================================================================
    # FİYAT HESAPLAMA (Rating'e Dayalı)
    # ==========================================================================
    
    def calculate_price(row):
        """
        Oyuncunun piyasa değerini Rating'e göre hesaplar (Milyon £).
        
        Formül:
        - Baz fiyat = Rating'e göre kademeli
        - Pozisyon çarpanı ile çarp
        - Küçük rastgelelik ekle
        """
        rating = row['Rating']
        sub_pos = row['Alt_Pozisyon']
        
        # Rating bazlı baz fiyat (kademeli)
        if rating >= 90:
            base = 80 + (rating - 90) * 15
        elif rating >= 85:
            base = 45 + (rating - 85) * 7
        elif rating >= 80:
            base = 20 + (rating - 80) * 5
        elif rating >= 75:
            base = 8 + (rating - 75) * 2.4
        elif rating >= 70:
            base = 3 + (rating - 70) * 1
        else:
            base = 1 + (rating - 60) * 0.2
        
        # Pozisyon çarpanı
        pos_multiplier = POSITION_PRICE_MULTIPLIER.get(sub_pos, 1.0)
        
        # Rastgele varyasyon (%10)
        np.random.seed(hash(row['Oyuncu']) % 2**32)
        variation = np.random.uniform(0.9, 1.1)
        
        price = base * pos_multiplier * variation
        
        return round(max(1.0, min(200.0, price)), 1)
    
    df['Fiyat_M'] = df.apply(calculate_price, axis=1)
    
    # ==========================================================================
    # FORM PUANI HESAPLAMA (Rating'e Dayalı, 0-100)
    # ==========================================================================
    
    def calculate_form(row):
        """
        Oyuncunun form puanını Rating'e göre hesaplar.
        Yüksek Rating = Yüksek Form (ama biraz rastgelelik ile)
        """
        rating = row['Rating']
        
        # Rating'i form'a çevir (60-91 -> 50-100)
        base_form = 50 + (rating - 60) * (50 / 31)
        
        # Rastgele varyasyon (±10)
        np.random.seed(hash(row['Oyuncu'] + 'form') % 2**32)
        variation = np.random.randint(-10, 10)
        
        form = base_form + variation
        
        return round(max(40, min(100, form)), 0)
    
    df['Form'] = df.apply(calculate_form, axis=1)
    
    # ==========================================================================
    # OFANS GÜCÜ HESAPLAMA (Pozisyon + Rating Bazlı, 0-100)
    # ==========================================================================
    
    def calculate_offense(row):
        """
        Oyuncunun ofansif gücünü hesaplar.
        Forvet/Kanatlar yüksek, Defans düşük
        """
        rating = row['Rating']
        sub_pos = row['Alt_Pozisyon']
        
        # Pozisyon bazlı ofansif eğilim (0-1 arası)
        offense_tendency = {
            'GK': 0.1,
            'CB': 0.25, 'LB': 0.4, 'RB': 0.4,
            'DM': 0.45, 'CM': 0.55, 'CAM': 0.8, 'LM': 0.65, 'RM': 0.65,
            'LW': 0.85, 'RW': 0.85, 'ST': 0.95
        }.get(sub_pos, 0.5)
        
        # Rating'den baz ofans puanı
        base_offense = (rating - 60) * (100 / 31) * offense_tendency
        
        # Minimum değer (herkes biraz hücum yapabilir)
        min_offense = 15 + offense_tendency * 20
        
        # Rastgele varyasyon
        np.random.seed(hash(row['Oyuncu'] + 'off') % 2**32)
        variation = np.random.randint(-8, 8)
        
        offense = max(min_offense, base_offense) + variation
        
        return round(max(10, min(98, offense)), 0)
    
    df['Ofans_Gucu'] = df.apply(calculate_offense, axis=1)
    
    # ==========================================================================
    # DEFANS GÜCÜ HESAPLAMA (Pozisyon + Rating Bazlı, 0-100)
    # ==========================================================================
    
    def calculate_defense(row):
        """
        Oyuncunun defansif gücünü hesaplar.
        Defans/DM yüksek, Forvet düşük
        """
        rating = row['Rating']
        sub_pos = row['Alt_Pozisyon']
        
        # Pozisyon bazlı defansif eğilim (0-1 arası)
        defense_tendency = {
            'GK': 0.95,
            'CB': 0.9, 'LB': 0.75, 'RB': 0.75,
            'DM': 0.7, 'CM': 0.5, 'CAM': 0.3, 'LM': 0.4, 'RM': 0.4,
            'LW': 0.2, 'RW': 0.2, 'ST': 0.15
        }.get(sub_pos, 0.5)
        
        # Rating'den baz defans puanı
        base_defense = (rating - 60) * (100 / 31) * defense_tendency
        
        # Minimum değer
        min_defense = 10 + defense_tendency * 25
        
        # Rastgele varyasyon
        np.random.seed(hash(row['Oyuncu'] + 'def') % 2**32)
        variation = np.random.randint(-8, 8)
        
        defense = max(min_defense, base_defense) + variation
        
        return round(max(10, min(95, defense)), 0)
    
    df['Defans_Gucu'] = df.apply(calculate_defense, axis=1)
    
    # ==========================================================================
    # SAKATLIK DURUMU (Rastgele)
    # ==========================================================================
    
    def determine_injury(row):
        """
        Rastgele sakatlık durumu atar.
        """
        np.random.seed(hash(row['Oyuncu'] + 'inj') % 2**32)
        
        # Düşük rating'li oyuncuların sakatlık ihtimali biraz daha yüksek
        injury_prob = INJURY_PROBABILITY
        if row['Rating'] < 70:
            injury_prob *= 1.5
        
        return 1 if np.random.random() < injury_prob else 0
    
    df['Sakatlik'] = df.apply(determine_injury, axis=1)
    
    # ==========================================================================
    # GERÇEK SEZON İSTATİSTİKLERİNİ YÜKLE VE BİRLEŞTİR
    # ==========================================================================
    
    stats_df = load_real_stats_data()
    
    if stats_df is not None:
        df = merge_stats_data(df, stats_df)
        
    # ==========================================================================
    # GERÇEK PİYASA DEĞERLERİNİ YÜKLE VE BİRLEŞTİR
    # ==========================================================================
    
    market_df = load_market_values()
    
    if market_df is not None:
        df = merge_market_values(df, market_df)
    
    # ==========================================================================
    # FİNAL DATAFRAME
    # ==========================================================================
    
    # ID ekle
    df = df.reset_index(drop=True)
    df['ID'] = range(1, len(df) + 1)
    
    # Gerekli ana sütunları seç (stat sütunlarını koru)
    core_columns = [
        'ID', 'Oyuncu', 'Alt_Pozisyon', 'Mevki', 'Takim', 
        'Rating', 'Fiyat_M', 'Form', 'Ofans_Gucu', 'Defans_Gucu', 'Sakatlik'
    ]
    
    # Stat sütunları: "stat_" ile başlayanlar
    stat_cols = [c for c in df.columns if c.startswith("stat_")]
    final_cols = core_columns + stat_cols
    
    result_df = df[final_cols].copy()
    
    return result_df


def load_real_stats_data() -> Optional[pd.DataFrame]:
    """
    GitHub'dan indirilen real stat CSV'sini yükler.
    """
    try:
        base_path = Path(__file__).parent.parent
        csv_path = base_path / "data" / "playerstats_2025.csv"
        
        if not csv_path.exists():
            print("Uyarı: playerstats_2025.csv bulunamadı.")
            return None
            
        return pd.read_csv(csv_path)
    except Exception as e:
        print(f"Stats yükleme hatası: {e}")
        return None


def merge_stats_data(fc26_df: pd.DataFrame, stats_df: pd.DataFrame) -> pd.DataFrame:
    """
    Oyun veri seti ile gerçek istatistikleri oyuncu ismine göre birleştirir.
    Fuzzy matching kullanılır.
    """
    # İstatistik sütunlarını hazırla
    mapped_stats = {}
    
    # Config'deki mapping'e göre sütunları seç
    for internal_name, csv_col in CSV_COLUMN_MAPPING.items():
        if internal_name in ['Player', 'Team']: continue # Bunları stat olarak almayız
        
        if csv_col in stats_df.columns:
            stats_df[csv_col] = pd.to_numeric(stats_df[csv_col], errors='coerce').fillna(0)
            mapped_stats[internal_name] = csv_col
    
    # Stats DF'i hazırla: web_name bizim primary key olacak
    stats_names = stats_df['web_name'].tolist()
    # Ayrıca full name'i de tutalım (first + second)
    if 'first_name' in stats_df.columns and 'second_name' in stats_df.columns:
        stats_df['full_name'] = stats_df['first_name'] + " " + stats_df['second_name']
        stats_full_names = stats_df['full_name'].tolist()
    else:
        stats_full_names = []
        
    # Her oyuncu için eşleşme ara
    def find_match(row):
        player_name = row['Oyuncu']
        
        # 1. Tam eşleşme (web_name)
        match = stats_df[stats_df['web_name'] == player_name]
        if not match.empty:
            return match.iloc[0]
            
        # 2. Tam eşleşme (full_name içeriyor mu?)
        # Örn: "Erling Haaland" vs "Haaland"
        for idx, full in enumerate(stats_full_names):
            if player_name.lower() == full.lower():
                return stats_df.iloc[idx]
        
        # 3. Fuzzy match (web_name)
        # Sadece benzerlik oranı çok yüksekse (%80+)
        matches = get_close_matches(player_name, stats_names, n=1, cutoff=0.7)
        if matches:
            return stats_df[stats_df['web_name'] == matches[0]].iloc[0]
            
        # 4. Fuzzy match (full_name) - Daha pahalı işlem
        if stats_full_names:
            matches_full = get_close_matches(player_name, stats_full_names, n=1, cutoff=0.7)
            if matches_full:
                idx = stats_full_names.index(matches_full[0])
                return stats_df.iloc[idx]
                
        return None

    # Eşleşen verileri yeni sütunlara yaz
    # "stat_" prefix'i ekle ki karışmasın
    for internal_name in mapped_stats.keys():
        fc26_df[f'stat_{internal_name}'] = 0.0

    matches_found = 0
    
    for idx, row in fc26_df.iterrows():
        match_row = find_match(row)
        
        if match_row is not None:
            matches_found += 1
            for internal_name, csv_col in mapped_stats.items():
                if csv_col in match_row:
                    fc26_df.at[idx, f'stat_{internal_name}'] = float(match_row[csv_col])
    
    print(f"Toplam {len(fc26_df)} oyuncudan {matches_found} tanesi gerçek verilerle eşleştirildi.")
    
    return fc26_df


def normalize_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Min-Max Scaling ile sayısal değerleri 0-1 arasına normalize eder.
    
    Normalizasyon formülü: 
        X_norm = (X - X_min) / (X_max - X_min)
    
    Bu işlem, farklı ölçeklerdeki değişkenlerin optimizasyon 
    modeline eşit katkı sağlaması için kritiktir.
    
    Args:
        df: Ham veri DataFrame'i
        
    Returns:
        pd.DataFrame: Normalize edilmiş değerleri içeren DataFrame
    """
    df_normalized = df.copy()
    
    # Normalize edilecek sütunlar (Mevcut + Yeni Statlar)
    columns_to_normalize = ['Form', 'Ofans_Gucu', 'Defans_Gucu']
    
    # Stat sütunlarını da normalize et
    stat_cols = [c for c in df.columns if c.startswith("stat_")]
    columns_to_normalize.extend(stat_cols)
    
    for col in columns_to_normalize:
        if col not in df.columns: continue
        
        min_val = df[col].min()
        max_val = df[col].max()
        
        # Min-Max Scaling
        if max_val - min_val > 0:
            df_normalized[f'{col}_Norm'] = (df[col] - min_val) / (max_val - min_val)
        else:
            df_normalized[f'{col}_Norm'] = 0.0 # Eğer varyasyon yoksa 0 (veya 0.5)
            
            # Statlar için 0 daha mantıklı (herkes 0 çektiyse kimsede o özellik yoktur)
            if not col.startswith("stat_"):
                 df_normalized[f'{col}_Norm'] = 0.5
    
    return df_normalized


def get_team_players(df: pd.DataFrame, team: str) -> pd.DataFrame:
    """
    Belirli bir takımın oyuncularını döndürür.
    
    Args:
        df: Tüm oyuncuların DataFrame'i
        team: Takım adı
        
    Returns:
        pd.DataFrame: Sadece o takımın oyuncuları
    """
    return df[df['Takim'] == team].copy()


def check_formation_feasibility(df: pd.DataFrame, formation: dict) -> dict:
    """
    Bir takımın belirli bir formasyonu kurabilecek yeterli 
    oyuncuya sahip olup olmadığını kontrol eder.
    
    Args:
        df: Takım oyuncuları (sadece sağlıklı olanlar)
        formation: Formasyon gereksinimleri dict'i
        
    Returns:
        dict: Her pozisyon için mevcut ve gerekli sayılar
    """
    # Sadece sağlıklı oyuncuları al
    healthy = df[df['Sakatlik'] == 0]
    
    result = {}
    all_ok = True
    
    for pos, required in formation.items():
        available = len(healthy[healthy['Alt_Pozisyon'] == pos])
        result[pos] = {
            'gerekli': required,
            'mevcut': available,
            'yeterli': available >= required
        }
        if available < required:
            all_ok = False
    
    result['tum_pozisyonlar_tamam'] = all_ok
    return result
    

def get_data_summary(df: pd.DataFrame) -> dict:
    """
    Veri seti hakkında özet istatistikler döndürür.
    """
    summary = {
        'toplam_oyuncu': len(df),
        'alt_pozisyon_dagilimi': df['Alt_Pozisyon'].value_counts().to_dict(),
        'ana_grup_dagilimi': df['Mevki'].value_counts().to_dict(),
        'saglikli_oyuncu': len(df[df['Sakatlik'] == 0]),
        'sakat_oyuncu': len(df[df['Sakatlik'] == 1]),
        'ortalama_rating': df['Rating'].mean(),
        'ortalama_fiyat': df['Fiyat_M'].mean(),
        'min_fiyat': df['Fiyat_M'].min(),
        'max_fiyat': df['Fiyat_M'].max(),
        'toplam_deger': df['Fiyat_M'].sum(),
        'takim_sayisi': df['Takim'].nunique()
    }
    return summary


def get_position_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Her alt pozisyon için istatistik özeti döndürür.
    """
    stats = df.groupby('Alt_Pozisyon').agg({
        'Oyuncu': 'count',
        'Rating': 'mean',
        'Fiyat_M': 'mean',
        'Ofans_Gucu': 'mean',
        'Defans_Gucu': 'mean',
        'Form': 'mean'
    }).round(1)
    
    stats.columns = ['Oyuncu Sayısı', 'Ort. Rating', 'Ort. Fiyat', 
                     'Ort. Ofans', 'Ort. Defans', 'Ort. Form']
    
    return stats.sort_values('Oyuncu Sayısı', ascending=False)


# Geriye uyumluluk için eski fonksiyon adları
def load_premier_league_data(csv_path: str = None) -> pd.DataFrame:
    """Eski fonksiyon adı - geriye uyumluluk için"""
    return load_fc26_data(csv_path)


def create_dummy_dataset(n_players: int = 60) -> pd.DataFrame:
    """Eski fonksiyon - geriye uyumluluk için"""
    return load_fc26_data()
