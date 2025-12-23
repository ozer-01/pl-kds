"""
=============================================================================
SENSITIVITY_ANALYZER.PY - DUYARLILIK ANALİZİ & SENARYO PLANLAMA
=============================================================================

Duyarlılık analizi (Sensitivity Analysis):
- Ağırlıkları değiştirince kadroya ne oluyor?
- Hangi parametre kadraya en çok etki ediyor?
- Best/Worst case senaryolar

Bu modül:
1. Tek parametreli duyarlılık analizi
2. Senaryo karşılaştırması (Conservative, Balanced, Aggressive)
3. Break-even analizi
4. Ağırlık optimizasyonu
=============================================================================
"""

import pandas as pd
import numpy as np
from typing import Dict
from .decision_analyzer import calculate_weighted_score


class SensitivityAnalyzer:
    """Duyarlılık analizi ve senaryo planlama."""
    
    def __init__(self, squad_df: pd.DataFrame, budget: float, base_weights: Dict[str, float]):
        self.squad_df = squad_df
        self.budget = budget
        self.base_weights = base_weights.copy()
        self.base_score = calculate_weighted_score(squad_df, base_weights)
    
    def analyze_weight_sensitivity(self, 
                                  parameter: str, 
                                  step: float = 0.05) -> pd.DataFrame:
        """
        Tek parametreli duyarlılık analizi.
        
        Args:
            parameter: Değiştirilecek ağırlık parametresi (rating, form, vb)
            step: Her adımda yapılacak değişim (0.05 = %5)
            
        Returns:
            DataFrame: Parametre değerleri vs. çıktı skoru
        """
        results = []
        
        # -50% ile +50% arasında test et
        for percentage in np.arange(-0.5, 0.55, step):
            # Ağırlıkları klonla
            test_weights = self.base_weights.copy()
            
            # Parametreyi değiştir
            original_value = test_weights.get(parameter, 0.20)
            new_value = original_value * (1 + percentage)
            new_value = max(0, min(1, new_value))  # Sınırları kontrol et
            
            test_weights[parameter] = new_value
            
            # Skoru hesapla
            score = calculate_weighted_score(self.squad_df, test_weights)
            change = ((score - self.base_score) / self.base_score) * 100 if self.base_score > 0 else 0
            
            results.append({
                'Yüzde_Değişim': f"{percentage*100:+.0f}%",
                f'{parameter}_Değeri': round(new_value, 3),
                'Skor': round(score, 2),
                'Skor_Değişimi': round(change, 2),
            })
        
        return pd.DataFrame(results)
    
    def tornado_analysis(self) -> pd.DataFrame:
        """
        Tornado analizi - Her parametrenin etki büyüklüğünü göster.
        
        Returns:
            DataFrame: Parametreleri etki büyüklüğüne göre sırala
        """
        tornado_results = []
        parameters = ['rating', 'form', 'offense', 'defense', 'cost_penalty']
        
        for param in parameters:
            # En düşük değer (-50%)
            test_weights_low = self.base_weights.copy()
            test_weights_low[param] = self.base_weights.get(param, 0.20) * 0.5
            score_low = calculate_weighted_score(self.squad_df, test_weights_low)
            
            # En yüksek değer (+50%)
            test_weights_high = self.base_weights.copy()
            test_weights_high[param] = self.base_weights.get(param, 0.20) * 1.5
            score_high = calculate_weighted_score(self.squad_df, test_weights_high)
            
            impact = score_high - score_low
            
            tornado_results.append({
                'Parametre': param.capitalize(),
                'En_Düşük_Skor': round(score_low, 2),
                'En_Yüksek_Skor': round(score_high, 2),
                'Etki_Büyüklüğü': round(impact, 2),
                'Yüzde_Etki': round((impact / self.base_score) * 100, 2),
            })
        
        return pd.DataFrame(tornado_results).sort_values('Etki_Büyüklüğü', ascending=False)
    
    def parameter_ranking(self) -> pd.DataFrame:
        """
        Parametreleri önem derecesine göre sırala (tornado analizi tabanlı).
        """
        tornado = self.tornado_analysis()
        
        ranking = tornado[['Parametre', 'Etki_Büyüklüğü', 'Yüzde_Etki']].copy()
        ranking['Sıra'] = range(1, len(ranking) + 1)
        ranking['Önem_Derecesi'] = ranking['Sıra'].apply(
            lambda x: '🔴 Çok Yüksek' if x == 1 else ('🟠 Yüksek' if x <= 2 else '🟡 Orta')
        )
        
        return ranking[['Sıra', 'Parametre', 'Önem_Derecesi', 'Etki_Büyüklüğü', 'Yüzde_Etki']]
