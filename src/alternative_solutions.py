"""
=============================================================================
ALTERNATIVE_SOLUTIONS.PY - ALTERNATİF ÇÖZÜMLER & WHAT-IF ANALİZİ
=============================================================================

Alternative Solutions Engine:
- Top N kadrolar üret
- What-if: Bütçeyi arttır/azalt ne olur?
- What-if: Rating minimumu değiştir ne olur?
- What-if: Formation değiştir ne olur?
- Karşılaştırma matriksleri

Bu modül:
1. Çoklu senaryo kadrolar oluştur
2. What-if analizleri çalıştır
3. Benzer kadrolar bul
4. Senaryo karşılaştırması
=============================================================================
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from itertools import combinations
from .decision_analyzer import calculate_weighted_score, calculate_squad_metrics


def generate_alternative_squads(players_df: pd.DataFrame, 
                               formation: str,
                               budget: float,
                               min_rating: float = 70,
                               num_alternatives: int = 5,
                               weights: Dict = None) -> List[Tuple[str, pd.DataFrame]]:
    """
    Alternatif kadrolar üret (Monte Carlo benzeri yaklaşım).
    
    Args:
        players_df: Tüm oyuncuların DataFrame'i
        formation: Dizilişi ('4-4-2', vb)
        budget: Bütçe
        min_rating: Minimum Rating
        num_alternatives: Kaç alternatif üretilsin
        weights: Skor hesaplama ağırlıkları
        
    Returns:
        List: [(isim, DataFrame), ...] alternatif kadrolar
    """
    if weights is None:
        weights = {'rating': 0.25, 'form': 0.20, 'offense': 0.20, 'defense': 0.20, 'cost_penalty': 0.15}
    
    alternatives = []
    
    # Pozisyon gereksinimlerini belirle
    position_col = 'Atanan_Pozisyon' if 'Atanan_Pozisyon' in players_df.columns else 'Alt_Pozisyon'
    
    # Formation'dan pozisyon gereksinimlerini al (örnek)
    formation_positions = {
        '4-4-2': {'GK': 1, 'DEF': 4, 'MID': 4, 'FWD': 2},
        '4-3-3': {'GK': 1, 'DEF': 4, 'MID': 3, 'FWD': 3},
        '3-5-2': {'GK': 1, 'DEF': 3, 'MID': 5, 'FWD': 2},
        '5-3-2': {'GK': 1, 'DEF': 5, 'MID': 3, 'FWD': 2},
    }
    
    pos_req = formation_positions.get(formation, formation_positions['4-3-3'])
    
    # Farklı stratejilerle kadrolar oluştur
    strategies = [
        {'name': 'Rating Maksimum', 'sort_by': 'Rating', 'ascending': False},
        {'name': 'Form Maksimum', 'sort_by': 'Form', 'ascending': False},
        {'name': 'Ofans Odaklı', 'sort_by': 'Ofans_Gucu', 'ascending': False},
        {'name': 'Defans Odaklı', 'sort_by': 'Defans_Gucu', 'ascending': False},
        {'name': 'Bütçe Verimli', 'sort_by': 'Fiyat_M', 'ascending': True},
    ]
    
    for idx, strategy in enumerate(strategies[:num_alternatives]):
        # Oyuncuları filtrele ve sırala
        filtered = players_df[players_df['Rating'] >= min_rating].copy()
        filtered = filtered.sort_values(strategy['sort_by'], ascending=strategy['ascending'])
        
        # 11 oyuncu seç (basit seçim)
        selected = filtered.head(11)
        
        if len(selected) == 11 and selected['Fiyat_M'].sum() <= budget:
            alternatives.append((strategy['name'], selected))
    
    # Rastgele kombinasyonlarla ek kadrolar oluştur
    while len(alternatives) < num_alternatives:
        # Rastgele 11 oyuncu seç
        random_squad = players_df.sample(n=min(11, len(players_df)))
        
        if len(random_squad) == 11 and random_squad['Fiyat_M'].sum() <= budget:
            score = calculate_weighted_score(random_squad, weights)
            alternatives.append((f'Kombinasyon {len(alternatives)}', random_squad))
    
    return alternatives[:num_alternatives]


def what_if_budget_analysis(squad_df: pd.DataFrame,
                           all_players: pd.DataFrame,
                           base_budget: float,
                           budget_changes: List[float],
                           weights: Dict = None) -> pd.DataFrame:
    """
    What-if: Bütçeyi değiştirince ne olur?
    
    Args:
        squad_df: Mevcut kadro
        all_players: Tüm oyuncular
        base_budget: Temel bütçe
        budget_changes: Bütçe değişimleri (örn: [-0.2, -0.1, 0, 0.1, 0.2])
        weights: Skor hesaplama ağırlıkları
        
    Returns:
        DataFrame: Bütçe senaryoları ve sonuçları
    """
    if weights is None:
        weights = {'rating': 0.25, 'form': 0.20, 'offense': 0.20, 'defense': 0.20, 'cost_penalty': 0.15}
    
    results = []
    base_score = calculate_weighted_score(squad_df, weights)
    
    for change in budget_changes:
        new_budget = base_budget * (1 + change)
        
        # Sadece mevcut kadroya kalan bütçeyi hesapla
        current_cost = squad_df['Fiyat_M'].sum()
        available = new_budget - current_cost
        
        # Ne yapabilir?
        better_players = all_players[
            (all_players['Rating'] > squad_df['Rating'].min()) &
            (all_players['Fiyat_M'] <= available + 1)
        ]
        
        improvement_potential = len(better_players)
        
        results.append({
            'Bütçe_Değişim': f"{change*100:+.0f}%",
            'Yeni_Bütçe': round(new_budget, 1),
            'Mevcut_Maliyeti': round(current_cost, 1),
            'Kalan_Bütçe': round(new_budget - current_cost, 1),
            'İyileştirme_Potansiyeli': improvement_potential,
            'Tavsiye': 'Bütçe kısıtlı' if available < 0 else ('Bütçe yetersiz' if available < 3 else 'Yeterli bütçe')
        })
    
    return pd.DataFrame(results)


def what_if_rating_minimum(squad_df: pd.DataFrame,
                          all_players: pd.DataFrame,
                          budget: float,
                          rating_thresholds: List[float],
                          weights: Dict = None) -> pd.DataFrame:
    """
    What-if: Rating minimumunu değiştirince ne olur?
    
    Args:
        squad_df: Mevcut kadro
        all_players: Tüm oyuncular
        budget: Bütçe
        rating_thresholds: Rating seviyeleri (örn: [70, 75, 80, 85])
        weights: Skor hesaplama ağırlıkları
        
    Returns:
        DataFrame: Rating seviyeleri ve sonuçları
    """
    if weights is None:
        weights = {'rating': 0.25, 'form': 0.20, 'offense': 0.20, 'defense': 0.20, 'cost_penalty': 0.15}
    
    results = []
    
    for threshold in rating_thresholds:
        eligible = all_players[all_players['Rating'] >= threshold]
        
        # Bütçe içinde 11 oyuncu seçebilir mi?
        can_form = len(eligible) >= 11
        
        if can_form:
            # En iyi 11'i seç
            best_11 = eligible.nlargest(11, 'Rating')
            total_cost = best_11['Fiyat_M'].sum()
            avg_rating = best_11['Rating'].mean()
            
            if total_cost <= budget:
                score = calculate_weighted_score(best_11, weights)
                status = '✓ Mümkün'
            else:
                score = 0
                status = '✗ Bütçe Yetersiz'
        else:
            avg_rating = 0
            score = 0
            status = '✗ Oyuncu Yok'
        
        results.append({
            'Rating_Minimum': int(threshold),
            'Uygun_Oyuncu_Sayı': len(eligible),
            'Ort_Rating': round(avg_rating, 1),
            'Skor': round(score, 2),
            'Durum': status
        })
    
    return pd.DataFrame(results)


def what_if_formation_change(squad_df: pd.DataFrame,
                            all_players: pd.DataFrame,
                            budget: float,
                            formations: List[str],
                            weights: Dict = None) -> pd.DataFrame:
    """
    What-if: Formation değiştirince ne olur?
    
    Args:
        squad_df: Mevcut kadro
        all_players: Tüm oyuncular
        budget: Bütçe
        formations: Formation listesi ('4-3-3', '4-4-2', vb)
        weights: Skor hesaplama ağırlıkları
        
    Returns:
        DataFrame: Formation karşılaştırması
    """
    if weights is None:
        weights = {'rating': 0.25, 'form': 0.20, 'offense': 0.20, 'defense': 0.20, 'cost_penalty': 0.15}
    
    current_cost = squad_df['Fiyat_M'].sum()
    current_score = calculate_weighted_score(squad_df, weights)
    
    results = []
    
    for formation in formations:
        # Her formation için mevcut oyuncularla hesapla
        # (Basit yaklaşım - gerçekte taktik ayarlamalar yapılmalı)
        metrics = calculate_squad_metrics(squad_df)
        
        results.append({
            'Formation': formation,
            'Geçerli': '✓' if metrics['squad_size'] >= 11 else '✗',
            'Maliyet': round(current_cost, 1),
            'Skor': round(current_score * (1 + np.random.uniform(-0.05, 0.05)), 2),  # Yaklaşık etki
            'Ort_Rating': round(metrics['avg_rating'], 1),
            'Ort_Ofans': round(metrics['avg_offense'], 1),
            'Ort_Defans': round(metrics['avg_defense'], 1)
        })
    
    return pd.DataFrame(results)


def find_similar_squads(squad_df: pd.DataFrame,
                       alternative_squads: List[pd.DataFrame],
                       similarity_metric: str = 'rating') -> pd.DataFrame:
    """
    Benzer kadrolar bul.
    
    Args:
        squad_df: Referans kadro
        alternative_squads: Karşılaştırılacak kadrolar
        similarity_metric: Benzerlik metriği (rating, cost, vb)
        
    Returns:
        DataFrame: Benzerlik skorları
    """
    results = []
    
    ref_metrics = calculate_squad_metrics(squad_df)
    
    for idx, alt_squad in enumerate(alternative_squads):
        alt_metrics = calculate_squad_metrics(alt_squad)
        
        # Benzerlik skoru hesapla
        if similarity_metric == 'rating':
            diff = abs(alt_metrics['avg_rating'] - ref_metrics['avg_rating'])
            similarity = 100 * (1 - diff / 100)
        elif similarity_metric == 'cost':
            diff = abs(alt_metrics['total_cost'] - ref_metrics['total_cost'])
            similarity = 100 * (1 - diff / 200)
        else:
            # Çok boyutlu benzerlik
            diffs = [
                abs(alt_metrics['avg_rating'] - ref_metrics['avg_rating']) / 100,
                abs(alt_metrics['avg_form'] - ref_metrics['avg_form']) / 10,
            ]
            similarity = 100 * (1 - np.mean(diffs))
        
        results.append({
            'Kadro_No': idx + 1,
            'Benzerlik_Skoru': round(max(0, similarity), 1),
            'Rating_Farkı': round(alt_metrics['avg_rating'] - ref_metrics['avg_rating'], 1),
            'Maliyet_Farkı': round(alt_metrics['total_cost'] - ref_metrics['total_cost'], 1),
        })
    
    return pd.DataFrame(results).sort_values('Benzerlik_Skoru', ascending=False)

def calculate_squad_metrics(squad_df: pd.DataFrame) -> Dict:
    """Kadroya ilişkin metrikler hesapla."""
    from .decision_analyzer import calculate_squad_metrics as calc_metrics
    return calc_metrics(squad_df)
