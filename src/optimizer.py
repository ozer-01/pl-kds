"""
=============================================================================
OPTIMIZER.PY - DOĞRUSAL PROGRAMLAMA MODELİ (CORE ENGINE)
=============================================================================

Bu modül, projenin kalbini oluşturur: PuLP kütüphanesi ile
Doğrusal Programlama (Linear Programming) optimizasyonu.

YENİ MODEL: POZİSYON-OYUNCU ATAMA (Assignment Problem)
=====================================================
Her oyuncu sadece BİR pozisyona atanabilir ve her pozisyona
sadece uyumlu oyuncular atanabilir.

SKORLAMA (YENİ):
Her pozisyon için tanımlanan Ağırlıklı Formüller kullanılır (LB = Tackles * 0.3 + ...)
Eğer istatistik verisi yoksa, eski Rating bazlı sisteme fallback yapar.

Karar Değişkenleri:
    y[i,p] ∈ {0, 1} : Oyuncu i, pozisyon p'ye atandı mı?

Kısıtlar:
    1. Her oyuncu en fazla 1 pozisyona atanabilir: Σ y[i,p] <= 1 (∀i)
    2. Her pozisyon için tam gereken sayıda: Σ y[i,p] = required[p] (∀p)
    3. Toplam 11 oyuncu: ΣΣ y[i,p] = 11
    4. Bütçe: Σ (Fiyat_i × Σ y[i,p]) <= Budget
    5. Uyumluluk: y[i,p] = 0 eğer oyuncu i, pozisyon p'ye uygun değilse
=============================================================================
"""

import pandas as pd
from typing import Tuple, Optional, Dict, List
from pulp import (
    LpProblem, LpMaximize, LpVariable, 
    lpSum, LpBinary, LpStatus, PULP_CBC_CMD
)

from .config import (
    FORMATIONS, 
    STRATEGY_WEIGHTS, 
    POSITION_CAN_BE_FILLED_BY,
    POSITIONAL_WEIGHTS
)


def calculate_position_score(row: pd.Series, position: str, strategy: str = 'Dengeli') -> float:
    """
    Bir oyuncunun belirli bir pozisyon için uygunluk skorunu hesaplar.
    
    YENİ MANTIK: Hibrit Skor + Strateji Ağırlıkları
    Score = (Base_Rating_Score * 0.7) + (Data_Score * 0.3)
    
    Strateji ağırlıkları:
    - Ofansif: ofans %50, defans %20, form %30
    - Defansif: ofans %20, defans %50, form %30
    - Dengeli: ofans %35, defans %35, form %30
    
    Args:
        row: Oyuncu verisi
        position: Atanacak pozisyon
        strategy: Takım stratejisi (Dengeli/Ofansif/Defansif)
    """
    
    # 1. Strateji ağırlıklarını al
    strategy_weights = STRATEGY_WEIGHTS.get(strategy, STRATEGY_WEIGHTS['Dengeli'])
    base_offense = strategy_weights['ofans']
    base_defense = strategy_weights['defans']
    form_weight = strategy_weights['form']
    
    # 2. Pozisyona göre ağırlıkları ayarla
    # Strateji ağırlıklarını pozisyona göre modifiye et
    if position in ['CB', 'LB', 'RB', 'GK', 'DM']:
        # Defansif pozisyonlar - defans ağırlığını artır
        offense_weight = base_offense * 0.6
        defense_weight = base_defense * 1.4
    elif position in ['ST', 'LW', 'RW', 'CAM']:
        # Ofansif pozisyonlar - ofans ağırlığını artır
        offense_weight = base_offense * 1.4
        defense_weight = base_defense * 0.6
    else:
        # Orta saha pozisyonları - strateji ağırlıklarını aynen kullan
        offense_weight = base_offense
        defense_weight = base_defense
    
    # Ağırlıkları normalize et (toplam ~1 olsun)
    total = offense_weight + defense_weight + form_weight
    offense_weight /= total
    defense_weight /= total
    form_weight /= total
        
    # Rating skoru (0-100 arası olması bekleniyor ama normalizasyona bağlı)
    # Norm değerler 0-1 arasında.
    base_score = (
        offense_weight * row.get('Ofans_Gucu_Norm', 0.5) +
        defense_weight * row.get('Defans_Gucu_Norm', 0.5) +
        form_weight * row.get('Form_Norm', 0.5)
    ) * 100
    
    # 2. Veri Bazlı Skor Hesapla (Varsa)
    data_score = 0.0
    weights = POSITIONAL_WEIGHTS.get(position, {})
    used_stats = False
    
    for metric, weight in weights.items():
        col_name = f"stat_{metric}_Norm"
        if col_name in row.index:
            val = row[col_name]
            data_score += val * weight
            if val > 0:
                used_stats = True
    
    # Data score da 0-1 aralığından geliyor, onu da 100'lük sisteme çekelim
    # Ancak data_score toplamı weights toplamı (genelde 1.0) kadar olabilir.
    data_score_100 = data_score * 100
    
    # 3. Final Skor
    if used_stats and data_score > 0:
        # Hibrit yaklaşım (GÜNCEL): %30 Rating, %70 İstatistik
        # Kullanıcı isteği: "İstatistiğe göre olsun yıldız oyuncu kötü oynuyorsa girmesin"
        # Amaç: İyi oynayan 75'lik oyuncu > Kötü oynayan 90'lık oyuncu > Hiç oynamayan (0 veri) oyuncu.
        
        final_score = (base_score * 0.3) + (data_score_100 * 0.7)
        
        return final_score
    else:
        # Veri yoksa (0 maç veya null), Rating'e güven ama ciddi ceza kes
        # Çünkü veri sıfırsa bu oyuncu muhtemelen yedek veya hiç oynamıyor.
        # base_score * 0.3 (Sadece potansiyeli var ama icraat yok)
        return base_score * 0.3


def solve_optimal_lineup(
    df: pd.DataFrame,
    formation: str,
    budget: float,
    strategy: str,
    use_flexible_positions: bool = True
) -> Tuple[Optional[pd.DataFrame], float, float, str]:
    """
    PuLP ile POZİSYON-OYUNCU ATAMA modeli kurarak optimal kadroyu belirler.
    """
    
    # =========================================================================
    # GİRDİ DOĞRULAMA
    # =========================================================================
    
    if formation not in FORMATIONS:
        raise ValueError(f"Geçersiz formasyon: {formation}")
    
    if strategy not in STRATEGY_WEIGHTS:
        raise ValueError(f"Geçersiz strateji: {strategy}")
    
    # =========================================================================
    # HAZIRLIK
    # =========================================================================
    
    formation_req = FORMATIONS[formation]
    
    # Sadece sağlıklı oyuncuları al
    df = df.copy()
    df = df[df['Sakatlik'] == 0].copy()
    
    if len(df) < 11:
        return None, 0, 0, 'Infeasible'
    
    players = df.index.tolist()
    positions = list(formation_req.keys())
    
    # SKOR MATRİSİNİ HESAPLA: Scores[i, p]
    # Bu işlem biraz maliyetli olabilir ama 600 oyuncu x 11 pozisyon = 6600 işlem (hızlı)
    scores = {}
    for i in players:
        row = df.loc[i]
        for p in positions:
            # Oyuncunun bu pozisyona uygun olup olmadığını kontrol et
            # Eğer uygun değilse skor hesaplamaya bile gerek yok (veya 0 ver)
            eligible_positions = POSITION_CAN_BE_FILLED_BY.get(p, [p])
            if row['Alt_Pozisyon'] in eligible_positions:
                scores[(i, p)] = calculate_position_score(row, p, strategy)
            else:
                scores[(i, p)] = -1000 # Cezalı puan (veya constraint ile engellenecek)

    # =========================================================================
    # LP MODELİ - POZİSYON ATAMA
    # =========================================================================
    
    model = LpProblem(name="Squad_Assignment", sense=LpMaximize)
    
    # Karar değişkenleri: y[i,p] = oyuncu i, pozisyon p'ye atandı mı?
    y = {}
    for i in players:
        for p in positions:
            y[(i, p)] = LpVariable(name=f"y_{i}_{p}", cat=LpBinary)
    
    # =========================================================================
    # AMAÇ FONKSİYONU
    # =========================================================================
    
    # Toplam skoru maksimize et
    # Uyumsuz atamalar (score < 0) zaten elenecek
    model += lpSum(
        scores[(i, p)] * y[(i, p)] 
        for i in players 
        for p in positions
        if scores[(i, p)] > -500 # Sadece geçerli skorları topla
    ), "Total_Score"
    
    # =========================================================================
    # KISITLAR
    # =========================================================================
    
    # Kısıt 1: Her oyuncu EN FAZLA 1 pozisyona atanabilir
    for i in players:
        model += lpSum(y[(i, p)] for p in positions) <= 1, f"Player_{i}_Max_One_Position"
    
    # Kısıt 2: Her pozisyon için TAM gereken sayıda oyuncu
    for p, required in formation_req.items():
        model += lpSum(y[(i, p)] for i in players) == required, f"Position_{p}_Exact"
    
    # Kısıt 3: Toplam 11 oyuncu
    model += lpSum(y[(i, p)] for i in players for p in positions) == 11, "Total_11"
    
    # Kısıt 4: Bütçe
    model += lpSum(
        df.loc[i, 'Fiyat_M'] * lpSum(y[(i, p)] for p in positions)
        for i in players
    ) <= budget, "Budget"
    
    # Kısıt 5: UYUMLULUK
    for i in players:
        for p in positions:
            if scores[(i, p)] < -500:
                model += y[(i, p)] == 0, f"Compat_{i}_{p}"
    
    # =========================================================================
    # ÇÖZÜM
    # =========================================================================
    
    solver = PULP_CBC_CMD(msg=0)
    model.solve(solver)
    
    status = LpStatus[model.status]
    
    if status != 'Optimal':
        return None, 0, 0, status
    
    # =========================================================================
    # SONUÇLARI ÇIKAR
    # =========================================================================
    
    selected_data = []
    total_score = 0
    
    for i in players:
        for p in positions:
            if y[(i, p)].varValue == 1:
                row_data = df.loc[i].to_dict()
                row_data['Atanan_Pozisyon'] = p
                # Hesaplanan skoru da kaydet (görselleştirme için)
                row_data['Pozisyon_Skoru'] = scores[(i, p)]
                selected_data.append(row_data)
                total_score += scores[(i, p)]
                break
    
    if len(selected_data) != 11:
        return None, 0, 0, 'Infeasible'
    
    selected_df = pd.DataFrame(selected_data)
    total_cost = selected_df['Fiyat_M'].sum()
    
    return selected_df, total_score, total_cost, status


def solve_with_fallback(
    df: pd.DataFrame,
    formation: str,
    budget: float,
    strategy: str
) -> Tuple[Optional[pd.DataFrame], float, float, str]:
    """
    Önce normal mod, başarısız olursa daha yüksek bütçe ile dener.
    """
    result = solve_optimal_lineup(df, formation, budget, strategy)
    
    if result[3] == 'Optimal':
        return result
    
    # Bütçeyi artırıp tekrar dene
    return solve_optimal_lineup(df, formation, budget * 1.5, strategy)


def check_formation_availability(df: pd.DataFrame, formation: str) -> dict:
    """
    Bir formasyon için yeterli oyuncu olup olmadığını kontrol eder.
    
    Args:
        df: Oyuncu verileri
        formation: Formasyon adı
        
    Returns:
        dict: Her pozisyon için mevcut/gerekli sayılar
    """
    formation_req = FORMATIONS[formation]
    healthy_df = df[df['Sakatlik'] == 0] if 'Sakatlik' in df.columns else df
    
    result = {
        'formation': formation,
        'pozisyonlar': {},
        'uygun': True
    }
    
    for position, required in formation_req.items():
        # Bu pozisyona atanabilecek oyuncu pozisyonları
        eligible = POSITION_CAN_BE_FILLED_BY.get(position, [position])
        
        # Bu pozisyonlardaki oyuncu sayısı
        available = len(healthy_df[healthy_df['Alt_Pozisyon'].isin(eligible)])
        
        is_ok = available >= required
        result['pozisyonlar'][position] = {
            'gerekli': required,
            'mevcut': available,
            'yeterli': is_ok
        }
        
        if not is_ok:
            result['uygun'] = False
    
    return result


def get_optimization_summary(
    selected_df: pd.DataFrame, 
    total_score: float, 
    total_cost: float,
    budget: float
) -> dict:
    """Optimizasyon sonuç özeti."""
    return {
        'toplam_skor': round(total_score, 4),
        'toplam_maliyet': round(total_cost, 1),
        'kalan_butce': round(budget - total_cost, 1),
        'butce_kullanim_orani': round((total_cost / budget) * 100, 1),
        'ortalama_form': round(selected_df['Form'].mean(), 1),
        'ortalama_ofans': round(selected_df['Ofans_Gucu'].mean(), 1),
        'ortalama_defans': round(selected_df['Defans_Gucu'].mean(), 1),
        'ortalama_rating': round(selected_df['Rating'].mean(), 1) if 'Rating' in selected_df.columns else 0,
        'pozisyon_dagilimi': selected_df['Atanan_Pozisyon'].value_counts().to_dict() if 'Atanan_Pozisyon' in selected_df.columns else {}
    }


def solve_alternative_lineup(
    df: pd.DataFrame,
    formation: str,
    budget: float,
    mode: str
) -> Tuple[Optional[pd.DataFrame], float, float, str]:
    """
    Alternatif kadro modları için özel optimizasyon.
    
    Modlar:
    - rating: En yüksek rating'li oyuncuları seç
    - form: En formda oyuncuları seç  
    - budget: En ucuz ama kaliteli kadroyu seç
    
    Args:
        df: Oyuncu verileri
        formation: Formasyon
        budget: Bütçe limiti
        mode: Optimizasyon modu (rating/form/budget)
        
    Returns:
        Tuple: (selected_df, total_score, total_cost, status)
    """
    if formation not in FORMATIONS:
        return None, 0, 0, 'Infeasible'
    
    formation_req = FORMATIONS[formation]
    
    # Sadece sağlıklı oyuncuları al
    df = df.copy()
    df = df[df['Sakatlik'] == 0].copy()
    
    if len(df) < 11:
        return None, 0, 0, 'Infeasible'
    
    # Moda göre sıralama kriteri belirle
    if mode == "rating":
        sort_column = 'Rating'
        ascending = False
    elif mode == "form":
        sort_column = 'Form'
        ascending = False
    elif mode == "budget":
        sort_column = 'Fiyat_M'
        ascending = True  # Ucuzdan pahalıya
    else:
        sort_column = 'Rating'
        ascending = False
    
    positions = list(formation_req.keys())
    selected_players = []
    used_ids = set()
    
    # Her pozisyon için en iyi oyuncuları seç
    for position in positions:
        required = formation_req[position]
        eligible_positions = POSITION_CAN_BE_FILLED_BY.get(position, [position])
        
        # Bu pozisyona uygun oyuncuları bul
        eligible_players = df[
            (df['Alt_Pozisyon'].isin(eligible_positions)) &
            (~df['ID'].isin(used_ids))
        ].sort_values(sort_column, ascending=ascending)
        
        # Gerekli sayıda oyuncu seç
        for _, player in eligible_players.head(required).iterrows():
            player_dict = player.to_dict()
            player_dict['Atanan_Pozisyon'] = position
            selected_players.append(player_dict)
            used_ids.add(player['ID'])
    
    if len(selected_players) != 11:
        return None, 0, 0, 'Infeasible'
    
    selected_df = pd.DataFrame(selected_players)
    
    # Bütçe kontrolü
    total_cost = selected_df['Fiyat_M'].sum()
    if total_cost > budget:
        # Bütçe modu değilse, bütçe aşımı varsa başarısız
        if mode != "budget":
            return None, 0, 0, 'Infeasible'
    
    # Skor hesapla
    total_score = 0
    for _, row in selected_df.iterrows():
        pos = row['Atanan_Pozisyon']
        score = calculate_position_score(row, pos, 'Dengeli')
        total_score += score
        selected_df.loc[selected_df['ID'] == row['ID'], 'Pozisyon_Skoru'] = score
    
    return selected_df, total_score, total_cost, 'Optimal'
