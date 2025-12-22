"""
=============================================================================
DECISION_ANALYZER.PY - TOPSIS & ÇOKLU KRİTER KARAR VERME ANALİZİ
=============================================================================

TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)
- En iyi ve en kötü çözüme benzerliğe göre alternatifleri sırala
- Çok boyutlu veri setini normalize ederek karşılaştırma yapabilir

Bu modül:
1. Alternatif kadrolar arasında TOPSIS analizi
2. Kadroya ilişkin detaylı karar raporu
3. Risk analizi ve uyarılar
4. Kadroya ilişkin öneriler
=============================================================================
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


def calculate_weighted_score(squad_df: pd.DataFrame, 
                             weights: Dict[str, float]) -> float:
    """
    Ağırlıklı skor hesapla (TOPSIS-benzeri metrik).
    
    Args:
        squad_df: Kadroya ait oyuncu DataFrame'i
        weights: Ağırlıklandırma (rating, form, offense, defense, cost_penalty)
        
    Returns:
        float: 0-100 arası skor
    """
    score_components = {
        'rating': (squad_df['Rating'].mean() / 100) * weights.get('rating', 0.25),
        'form': (squad_df['Form'].mean() / 10) * weights.get('form', 0.20),
        'offense': (squad_df['Ofans_Gucu'].mean() / 100) * weights.get('offense', 0.20),
        'defense': (squad_df['Defans_Gucu'].mean() / 100) * weights.get('defense', 0.20),
    }
    
    subtotal = sum(score_components.values())
    
    # Maliyeti düşün (daha az maliyet = daha iyi)
    total_cost = squad_df['Fiyat_M'].sum()
    cost_factor = 1 - (total_cost / 200) * weights.get('cost_penalty', 0.15)
    cost_factor = max(0.5, cost_factor)  # Minimum 0.5 çarpan
    
    final_score = (subtotal / 0.85) * 100 * cost_factor
    return min(100, max(0, final_score))


def calculate_squad_metrics(squad_df: pd.DataFrame) -> Dict:
    """
    Kadroya ilişkin tüm metrikler hesapla.
    """
    pos_col = 'Atanan_Pozisyon' if 'Atanan_Pozisyon' in squad_df.columns else 'Alt_Pozisyon'
    
    metrics = {
        'total_cost': squad_df['Fiyat_M'].sum(),
        'squad_size': len(squad_df),
        'avg_rating': squad_df['Rating'].mean() if 'Rating' in squad_df.columns else 0,
        'min_rating': squad_df['Rating'].min() if 'Rating' in squad_df.columns else 0,
        'max_rating': squad_df['Rating'].max() if 'Rating' in squad_df.columns else 0,
        'rating_std': squad_df['Rating'].std() if 'Rating' in squad_df.columns else 0,
        'avg_form': squad_df['Form'].mean(),
        'avg_offense': squad_df['Ofans_Gucu'].mean(),
        'avg_defense': squad_df['Defans_Gucu'].mean(),
        'position_distribution': squad_df[pos_col].value_counts().to_dict() if pos_col in squad_df.columns else {},
    }
    
    return metrics


def rank_alternative_solutions(solutions: List[Tuple[str, pd.DataFrame]], 
                              weights: Dict[str, float]) -> pd.DataFrame:
    """
    Alternatif çözümleri sırala ve karşılaştır.
    
    Args:
        solutions: [(isim, DataFrame), ...] listesi
        weights: Ağırlıklandırma parametreleri
        
    Returns:
        DataFrame: Sıralanmış çözümler
    """
    results = []
    
    for idx, (name, squad) in enumerate(solutions):
        score = calculate_weighted_score(squad, weights)
        metrics = calculate_squad_metrics(squad)
        
        results.append({
            'Sıra': idx + 1,
            'İsim': name,
            'Skor': round(score, 2),
            'Fiyat': round(metrics['total_cost'], 1),
            'Ort. Rating': round(metrics['avg_rating'], 1),
            'Ort. Form': round(metrics['avg_form'], 1),
            'Ort. Ofans': round(metrics['avg_offense'], 1),
            'Ort. Defans': round(metrics['avg_defense'], 1),
            'Kadro': squad
        })
    
    df_results = pd.DataFrame(results).sort_values('Skor', ascending=False).reset_index(drop=True)
    df_results['Sıra'] = range(1, len(df_results) + 1)
    
    return df_results


def generate_decision_report(squad_df: pd.DataFrame, 
                            total_score: float, 
                            budget: float, 
                            formation: str,
                            weights: Dict[str, float]) -> Dict:
    """
    Kadroya ilişkin detaylı karar raporu oluştur.
    """
    metrics = calculate_squad_metrics(squad_df)
    
    report = {
        'formation': formation,
        'squad_size': metrics['squad_size'],
        'total_score': round(total_score, 2),
        'total_cost': round(metrics['total_cost'], 1),
        'budget_utilization': round((metrics['total_cost'] / budget) * 100, 1),
        'remaining_budget': round(budget - metrics['total_cost'], 1),
        
        # Oyuncu metrikleri
        'avg_rating': round(metrics['avg_rating'], 1),
        'min_rating': int(metrics['min_rating']),
        'max_rating': int(metrics['max_rating']),
        'rating_std': round(metrics['rating_std'], 1),
        
        'avg_form': round(metrics['avg_form'], 1),
        'avg_offense': round(metrics['avg_offense'], 1),
        'avg_defense': round(metrics['avg_defense'], 1),
        
        # Pozisyon dağılımı
        'position_distribution': metrics['position_distribution'],
        
        # Risk analizi
        'low_form_count': len(squad_df[squad_df['Form'] < 6]),
        'very_low_form_count': len(squad_df[squad_df['Form'] < 5]),
        'high_cost_players': len(squad_df[squad_df['Fiyat_M'] > 10]),
        
        # Analiz verileri
        'strengths': get_squad_strengths(squad_df),
        'weaknesses': get_squad_weaknesses(squad_df),
        'recommendations': get_recommendations(squad_df, budget, formation),
        'risk_alerts': get_risk_alerts(squad_df)
    }
    
    return report


def get_squad_strengths(squad_df: pd.DataFrame) -> List[str]:
    """Kadronun güçlü yönlerini belirle."""
    strengths = []
    
    rating_avg = squad_df['Rating'].mean()
    if rating_avg > 82:
        strengths.append(f"⭐ Çok Yüksek Rating Ortalaması ({rating_avg:.1f})")
    elif rating_avg > 78:
        strengths.append(f"✓ Yüksek Rating Ortalaması ({rating_avg:.1f})")
    
    offense_avg = squad_df['Ofans_Gucu'].mean()
    if offense_avg > 78:
        strengths.append(f"✓ Güçlü Hücum Gücü ({offense_avg:.1f})")
    
    defense_avg = squad_df['Defans_Gucu'].mean()
    if defense_avg > 78:
        strengths.append(f"✓ Güçlü Savunma ({defense_avg:.1f})")
    
    form_avg = squad_df['Form'].mean()
    if form_avg > 7.5:
        strengths.append(f"✓ Mükemmel Form Durumu ({form_avg:.1f})")
    elif form_avg > 7:
        strengths.append(f"✓ İyi Form Durumu ({form_avg:.1f})")
    
    consistency = squad_df['Rating'].std()
    if consistency < 5 and 'Rating' in squad_df.columns:
        strengths.append(f"✓ Yüksek Konsistansi (Std: {consistency:.1f})")
    
    if not strengths:
        strengths.append("• Dengeli orta seviye kadro")
    
    return strengths


def get_squad_weaknesses(squad_df: pd.DataFrame) -> List[str]:
    """Kadronun zayıf yönlerini belirle."""
    weaknesses = []
    
    rating_avg = squad_df['Rating'].mean()
    if rating_avg < 75:
        weaknesses.append(f"✗ Düşük Rating ({rating_avg:.1f})")
    
    offense_avg = squad_df['Ofans_Gucu'].mean()
    if offense_avg < 70:
        weaknesses.append(f"✗ Zayıf Hücum ({offense_avg:.1f})")
    
    defense_avg = squad_df['Defans_Gucu'].mean()
    if defense_avg < 70:
        weaknesses.append(f"✗ Zayıf Savunma ({defense_avg:.1f})")
    
    form_avg = squad_df['Form'].mean()
    if form_avg < 6:
        weaknesses.append(f"✗ Kötü Form Durumu ({form_avg:.1f})")
    elif form_avg < 6.5:
        weaknesses.append(f"⚠️ Düşük Form Durumu ({form_avg:.1f})")
    
    consistency = squad_df['Rating'].std()
    if consistency > 8 and 'Rating' in squad_df.columns:
        weaknesses.append(f"⚠️ Düşük Konsistansi (Std: {consistency:.1f})")
    
    if not weaknesses:
        weaknesses.append("• Belirgin zayıflık yok")
    
    return weaknesses


def get_recommendations(squad_df: pd.DataFrame, budget: float, formation: str) -> List[str]:
    """Kadroya ilişkin öneriler sun."""
    recommendations = []
    
    remaining = budget - squad_df['Fiyat_M'].sum()
    if remaining > 5:
        recommendations.append(f"💡 Kalan bütçe: £{remaining:.1f}M - Daha iyi oyuncular alabilirsiniz")
    elif remaining > 0:
        recommendations.append(f"💡 Bütçeniz verimli kullanılıyor (Kalan: £{remaining:.1f}M)")
    
    low_form_count = len(squad_df[squad_df['Form'] < 6])
    if low_form_count > 2:
        recommendations.append(f"⚠️ {low_form_count} oyuncu kötü formda - Forma gelmesi bekleniyor")
    
    rating_avg = squad_df['Rating'].mean()
    if rating_avg < 75:
        recommendations.append("💡 Daha yüksek rated oyuncular almayı düşünün")
    elif rating_avg > 85:
        recommendations.append("✓ Yüksek kaliteli oyunculardan oluşan elit kadro")
    
    high_cost = len(squad_df[squad_df['Fiyat_M'] > 10])
    if high_cost > 5:
        recommendations.append(f"⚠️ {high_cost} pahalı oyuncu - Yaralanma riski göz önüne alınız")
    
    if not recommendations:
        recommendations.append("✓ Kadro dengeli ve iyi optimize edilmiş")
    
    return recommendations


def get_risk_alerts(squad_df: pd.DataFrame) -> List[Dict]:
    """
    Kadro için risk uyarıları oluştur.
    """
    alerts = []
    
    # Kötü form riski
    bad_form = squad_df[squad_df['Form'] < 5]
    if len(bad_form) > 0:
        alerts.append({
            'level': 'high',
            'type': 'Form Riski',
            'message': f"{len(bad_form)} oyuncu çok kötü formda",
            'players': bad_form['Oyuncu_Adi'].tolist() if 'Oyuncu_Adi' in bad_form.columns else []
        })
    
    # Rating dağılımı
    if 'Rating' in squad_df.columns:
        rating_std = squad_df['Rating'].std()
        if rating_std > 10:
            alerts.append({
                'level': 'medium',
                'type': 'Kalite Tutarsızlığı',
                'message': f"Kadro içinde Rating farkı fazla (Std: {rating_std:.1f})"
            })
    
    # Yüksek maliyet riski
    high_cost_count = len(squad_df[squad_df['Fiyat_M'] > 12])
    if high_cost_count > 4:
        alerts.append({
            'level': 'medium',
            'type': 'Maliyet Riski',
            'message': f"{high_cost_count} pahalı oyuncuya bağlı risk"
        })
    
    # Düşük Rating
    low_rating = len(squad_df[squad_df['Rating'] < 70])
    if low_rating > 3:
        alerts.append({
            'level': 'medium',
            'type': 'Kalite Sorunu',
            'message': f"{low_rating} oyuncu düşük rating'e sahip"
        })
    
    return alerts
