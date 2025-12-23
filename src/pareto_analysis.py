"""
=============================================================================
PARETO_ANALYSIS.PY - PARETO FRONTIER & MULTI-OBJECTIVE OPTİMİZASYON
=============================================================================

Multi-Objective Optimization:
- Birden fazla hedefe optimize et (Rating ↑, Maliyet ↓)
- Pareto Frontier'i bul (optimal trade-off'lar)
- Efficient frontier kadrolar
- Trade-off analizi

Bu modül:
1. Pareto optimal çözümleri üret
2. Trade-off eğrilerini çiz
3. Efficient frontier'i göster
4. Karar vericiye en iyi seçenekleri sun
=============================================================================
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional


class ParetoAnalyzer:
    """Multi-objective optimizasyon ve Pareto analizi."""
    
    def __init__(self, all_players: pd.DataFrame, budget: float = 100.0):
        self.all_players = all_players
        self.budget = budget
    
    def generate_pareto_frontier(self, num_solutions: int = 20) -> pd.DataFrame:
        """
        Pareto frontier'ını oluştur.
        
        Hedefler:
        - Maksimize: Ortalama Rating
        - Minimize: Toplam Maliyet
        
        Returns:
            DataFrame: Pareto optimal kadrolar
        """
        pareto_solutions = []
        
        # Farklı ağırlık kombinasyonları ile çözüm bul
        for i in range(num_solutions):
            weight_rating = i / (num_solutions - 1) if num_solutions > 1 else 0.5
            weight_cost = 1 - weight_rating
            
            # Oyunculara skor ver
            self.all_players['_pareto_score'] = (
                (self.all_players['Rating'] / 100) * weight_rating -
                (self.all_players['Fiyat_M'] / self.budget) * weight_cost
            )
            
            # En iyi 11'i seç (basit seçim)
            selected = self.all_players.nlargest(11, '_pareto_score').copy()
            
            total_cost = selected['Fiyat_M'].sum()
            
            # Bütçe içinde mi?
            if total_cost <= self.budget:
                avg_rating = selected['Rating'].mean()
                
                # Bu çözüm zaten bulundu mu?
                is_dominated = False
                for sol in pareto_solutions:
                    if (sol['avg_rating'] >= avg_rating and sol['total_cost'] <= total_cost):
                        is_dominated = True
                        break
                
                if not is_dominated:
                    # Eski çözümleri kontrol et (bu yeni çözüm onları dominate ediyor mu?)
                    pareto_solutions = [
                        sol for sol in pareto_solutions
                        if not (avg_rating >= sol['avg_rating'] and total_cost <= sol['total_cost'])
                    ]
                    
                    pareto_solutions.append({
                        'avg_rating': round(avg_rating, 1),
                        'total_cost': round(total_cost, 1),
                        'squad': selected,
                        'budget_utilization': round((total_cost / self.budget) * 100, 1),
                        'solution_id': i
                    })
        
        # Sırala
        pareto_solutions = sorted(pareto_solutions, key=lambda x: x['avg_rating'], reverse=True)
        
        # DataFrame'e dönüştür
        results = []
        for i, sol in enumerate(pareto_solutions):
            results.append({
                'Sıra': i + 1,
                'Ortalama Rating': sol['avg_rating'],
                'Toplam Maliyet': f"£{sol['total_cost']:.1f}M",
                'Bütçe Kullanımı': f"{sol['budget_utilization']:.1f}%",
                'Kalan Bütçe': f"£{self.budget - sol['total_cost']:.1f}M",
                'Kadro': sol['squad'],
                '_raw_cost': sol['total_cost']
            })
        
        return pd.DataFrame(results)
    
    def analyze_trade_offs(self, solution1: pd.DataFrame, solution2: pd.DataFrame) -> Dict:
        """
        İki çözüm arasındaki trade-off analizi.
        
        Args:
            solution1: İlk kadro
            solution2: İkinci kadro
            
        Returns:
            Dict: Trade-off analizi
        """
        rating1 = solution1['Rating'].mean()
        cost1 = solution1['Fiyat_M'].sum()
        
        rating2 = solution2['Rating'].mean()
        cost2 = solution2['Fiyat_M'].sum()
        
        rating_diff = rating2 - rating1
        cost_diff = cost2 - cost1
        
        # Trade-off oranı (Rating/Maliyet)
        if cost_diff != 0:
            trade_off_ratio = rating_diff / cost_diff
        else:
            trade_off_ratio = float('inf')
        
        analysis = {
            'Çözüm 1': {
                'Rating': round(rating1, 1),
                'Maliyet': round(cost1, 1)
            },
            'Çözüm 2': {
                'Rating': round(rating2, 1),
                'Maliyet': round(cost2, 1)
            },
            'Farklar': {
                'Rating Farkı': round(rating_diff, 1),
                'Maliyet Farkı': round(cost_diff, 1),
                'Trade-off Oranı': round(trade_off_ratio, 3) if trade_off_ratio != float('inf') else 'Sınırsız'
            },
            'Tavsiye': self._get_trade_off_recommendation(rating_diff, cost_diff)
        }
        
        return analysis
    
    def _get_trade_off_recommendation(self, rating_diff: float, cost_diff: float) -> str:
        """Trade-off tavsiyesi."""
        if rating_diff > 5 and cost_diff > 10:
            return "💰 Çözüm 1 daha ekonomik, Çözüm 2 çok daha kaliteli"
        elif rating_diff > 5:
            return "✓ Çözüm 2 daha kaliteli, minimal maliyet artışı"
        elif rating_diff < -5 and cost_diff < -10:
            return "💡 Çözüm 1 daha kaliteli ve daha ekonomik"
        elif cost_diff < -10:
            return "🎯 Çözüm 1 çok daha ekonomik, minimal kalite kaybı"
        else:
            return "⚖️ Her iki çözüm de dengeli seçenekler"
    
    def calculate_efficiency_score(self, squad_df: pd.DataFrame) -> Dict:
        """
        Kadroya ilişkin verimlilik skoru (Rating/Maliyet oranı).
        
        Returns:
            Dict: Verimlilik metrikleri
        """
        total_cost = squad_df['Fiyat_M'].sum()
        avg_rating = squad_df['Rating'].mean()
        
        # Verimlilik = Rating / Maliyet
        efficiency = avg_rating / (total_cost / 10) if total_cost > 0 else 0
        
        return {
            'ortalama_rating': round(avg_rating, 1),
            'toplam_maliyet': round(total_cost, 1),
            'rating_per_milyon': round(avg_rating / (total_cost / 10), 2),
            'verimlilik_skoru': round(efficiency, 2),
            'verimlilik_derecesi': self._rate_efficiency(efficiency)
        }
    
    def _rate_efficiency(self, efficiency: float) -> str:
        """Verimlilik derecesi."""
        if efficiency > 8.5:
            return "🟢 Çok İyi"
        elif efficiency > 7.5:
            return "🟢 İyi"
        elif efficiency > 6.5:
            return "🟡 Orta"
        elif efficiency > 5.5:
            return "🟠 Zayıf"
        else:
            return "🔴 Çok Zayıf"
    
    def find_efficient_alternatives(self, 
                                   target_squad: pd.DataFrame,
                                   all_players: pd.DataFrame,
                                   num_alternatives: int = 3) -> List[Dict]:
        """
        Hedef kadroya alternatif verimli çözümler bul.
        
        Args:
            target_squad: Referans kadro
            all_players: Tüm oyuncular
            num_alternatives: Kaç alternatif istenir
            
        Returns:
            List: Alternatif kadrolar ve analiz
        """
        target_rating = target_squad['Rating'].mean()
        target_cost = target_squad['Fiyat_M'].sum()
        
        alternatives = []
        
        # Farklı cost levels'te optimal rating ara
        cost_targets = [
            target_cost * 0.9,  # %10 daha ucuz
            target_cost,        # Aynı
            target_cost * 1.1   # %10 daha pahalı
        ]
        
        for cost_target in cost_targets:
            # Oyunculara skor ver (rating maksimum, cost minimize)
            all_players['_efficiency_score'] = (
                all_players['Rating'] / 100 -
                (all_players['Fiyat_M'] / cost_target) * 0.1
            )
            
            # En iyi 11'i seç
            selected = all_players.nlargest(11, '_efficiency_score').copy()
            total_cost = selected['Fiyat_M'].sum()
            
            if total_cost <= self.budget:
                avg_rating = selected['Rating'].mean()
                efficiency = self.calculate_efficiency_score(selected)
                
                is_duplicate = any(
                    abs(alt['Ortalama Rating'] - avg_rating) < 1 and
                    abs(alt['Toplam Maliyet'] - total_cost) < 2
                    for alt in alternatives
                )
                
                if not is_duplicate:
                    alternatives.append({
                        'Ortalama Rating': round(avg_rating, 1),
                        'Toplam Maliyet': round(total_cost, 1),
                        'Bütçe Kullanımı': round((total_cost / self.budget) * 100, 1),
                        'Verimlilik': efficiency['rating_per_milyon'],
                        'Fark (Rating)': round(avg_rating - target_rating, 1),
                        'Fark (Maliyet)': round(total_cost - target_cost, 1),
                        'Kadro': selected
                    })
        
        return sorted(alternatives, key=lambda x: x['Verimlilik'], reverse=True)[:num_alternatives]
    
    def sensitivity_to_objectives(self, base_squad: pd.DataFrame) -> pd.DataFrame:
        """
        Amaçlar değişirse sonuçlar nasıl değişir?
        
        Returns:
            DataFrame: Farklı amaç ağırlıkları ile sonuçlar
        """
        results = []
        
        for weight_rating in np.arange(0, 1.1, 0.25):
            weight_cost = 1 - weight_rating
            
            # Oyunculara skor ver
            self.all_players['_weighted_score'] = (
                (self.all_players['Rating'] / 100) * weight_rating -
                (self.all_players['Fiyat_M'] / self.budget) * weight_cost
            )
            
            # En iyi 11'i seç
            selected = self.all_players.nlargest(11, '_weighted_score')
            
            if len(selected) == 11:
                total_cost = selected['Fiyat_M'].sum()
                
                if total_cost <= self.budget:
                    results.append({
                        'Rating Ağırlığı': f"{weight_rating*100:.0f}%",
                        'Maliyet Ağırlığı': f"{weight_cost*100:.0f}%",
                        'Ortalama Rating': round(selected['Rating'].mean(), 1),
                        'Toplam Maliyet': round(total_cost, 1),
                        'Verimlilik': round(selected['Rating'].mean() / (total_cost / 10), 2)
                    })
        
        return pd.DataFrame(results)
    
    def visualize_pareto_frontier(self, pareto_solutions: pd.DataFrame) -> Dict:
        """
        Pareto frontier'ı görselleştirme için veri hazırla.
        
        Returns:
            Dict: Plotly için gerekli veri
        """
        if pareto_solutions.empty:
            return {}
        
        # Rating ve Maliyet verilerini çıkar
        x_data = pareto_solutions['_raw_cost'].tolist() if '_raw_cost' in pareto_solutions.columns else []
        y_data = pareto_solutions['Ortalama Rating'].tolist() if 'Ortalama Rating' in pareto_solutions.columns else []
        
        if not x_data or not y_data:
            return {}
        
        return {
            'x': x_data,
            'y': y_data,
            'title': 'Pareto Frontier (Rating vs Maliyet)',
            'xaxis_title': 'Toplam Maliyet (£M)',
            'yaxis_title': 'Ortalama Rating',
            'type': 'scatter'
        }
