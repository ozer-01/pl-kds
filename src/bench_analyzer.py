"""
=============================================================================
BENCH_ANALYZER.PY - YEDEK & BENCH OYUNCULAR ANALIZI
=============================================================================

Bench Analysis:
- Starter 11'de problem varsa kimin yerine girmeli?
- Bench gücü analizi
- Pozisyon başına yedek seçenekleri
- Taktik değişiklikler için yedekler

Bu modül:
1. Pozisyon başına en iyi yedekleri bul
2. Bench kadrası oluştur
3. Yaralanma senaryolarında çözümleri sun
4. Squad derinliğini analiz et
=============================================================================
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple


class BenchAnalyzer:
    """Yedek ve bench oyuncuları analiz eder."""
    
    def __init__(self, starter_squad: pd.DataFrame, all_players: pd.DataFrame):
        self.starter_squad = starter_squad
        self.all_players = all_players
        
        # Bench oyuncularını belirle
        starter_ids = set(starter_squad['ID'].tolist())
        self.bench = all_players[~all_players['ID'].isin(starter_ids)].copy()
    
    def find_position_backups(self, position: str, top_n: int = 3) -> pd.DataFrame:
        """
        Belirli bir pozisyon için en iyi yedekleri bul.
        
        Args:
            position: Pozisyon (CB, ST, vb)
            top_n: Kaç yedek gösterilsin
            
        Returns:
            DataFrame: En iyi yedekler
        """
        pos_col = 'Alt_Pozisyon' if 'Alt_Pozisyon' in self.bench.columns else 'Atanan_Pozisyon'

        # Oyuncu adı kolonu: önce Oyuncu_Adi, yoksa Oyuncu, yoksa ilk kolon
        name_candidates = ['Oyuncu_Adi', 'Oyuncu']
        name_col = None
        for cand in name_candidates:
            if cand in self.bench.columns:
                name_col = cand
                break
        if name_col is None:
            name_col = self.bench.columns[0]
        
        # Bu pozisyondan yedekleri bul
        backups = self.bench[self.bench[pos_col] == position].copy()
        
        if backups.empty:
            return pd.DataFrame()
        
        # Rating'e göre sırala
        selected_cols = [c for c in [name_col, 'Rating', 'Form', 'Fiyat_M', 'Ofans_Gucu', 'Defans_Gucu'] if c in backups.columns]
        backups = backups.nlargest(top_n, 'Rating')[selected_cols].copy()

        # Sütunları standart isimlere dönüştür
        rename_map = {name_col: 'Oyuncu', 'Fiyat_M': 'Fiyat', 'Ofans_Gucu': 'Ofans', 'Defans_Gucu': 'Defans'}
        backups = backups.rename(columns=rename_map)
        backups['Sıra'] = range(1, len(backups) + 1)
        
        keep_cols = [c for c in ['Sıra', 'Oyuncu', 'Rating', 'Form', 'Fiyat', 'Ofans', 'Defans'] if c in backups.columns]
        return backups[keep_cols]
    
    def build_bench_squad(self, max_players: int = 12) -> pd.DataFrame:
        """
        Optimal bench kadrası oluştur (11-12 oyuncu).
        
        Returns:
            DataFrame: Bench kadrası
        """
        pos_col = 'Alt_Pozisyon' if 'Alt_Pozisyon' in self.bench.columns else 'Atanan_Pozisyon'
        
        bench_squad = []
        
        # Pozisyon başına en iyi oyuncuyu seç
        positions = self.starter_squad[pos_col].unique().tolist()
        
        for pos in positions:
            available = self.bench[self.bench[pos_col] == pos].nlargest(1, 'Rating')
            if not available.empty:
                bench_squad.append(available.iloc[0].to_dict())
        
        if len(bench_squad) < max_players:
            # Eğer yeterli yoksa, başka iyi oyuncuları ekle
            used_ids = {p.get('ID') for p in bench_squad}
            remaining = self.bench[~self.bench['ID'].isin(used_ids)].nlargest(
                max_players - len(bench_squad), 'Rating'
            )
            bench_squad.extend(remaining.to_dict('records'))
        
        # Karışık tipleri normalize et (Series/dict)
        normalized = []
        for item in bench_squad:
            if isinstance(item, pd.Series):
                normalized.append(item.to_dict())
            elif isinstance(item, dict):
                normalized.append(item)
        
        return pd.DataFrame.from_records(normalized).head(max_players)
    
    def analyze_injury_scenarios(self, player_id: str, all_players: pd.DataFrame) -> Dict:
        """
        Belirli bir oyuncu sakat olursa ne olur?
        
        Args:
            player_id: Sakat olacak oyuncu
            all_players: Tüm oyuncular
            
        Returns:
            Dict: Senaryo analizi
        """
        injured_player = self.starter_squad[self.starter_squad['ID'] == player_id]
        
        if injured_player.empty:
            return {'error': 'Oyuncu kadrada bulunamadı'}
        
        injured_player = injured_player.iloc[0]
        pos = injured_player.get('Alt_Pozisyon', injured_player.get('Atanan_Pozisyon', ''))
        
        pos_col = 'Alt_Pozisyon' if 'Alt_Pozisyon' in all_players.columns else 'Atanan_Pozisyon'
        
        # En iyi yedek
        best_backup = all_players[
            (all_players[pos_col] == pos) &
            (all_players['ID'] != player_id)
        ].nlargest(1, 'Rating')
        
        if best_backup.empty:
            return {
                'sakat_oyuncu': injured_player.get('Oyuncu_Adi', injured_player.get('Oyuncu', 'Unknown')),
                'pozisyon': pos,
                'recommendation': '⚠️ Yedek oyuncu yok! Formasyonu değiştirmek gerekebilir.'
            }
        
        backup = best_backup.iloc[0]
        
        # Karşılaştırma
        rating_diff = injured_player.get('Rating', 0) - backup.get('Rating', 0)
        
        return {
            'sakat_oyuncu': injured_player.get('Oyuncu_Adi', injured_player.get('Oyuncu', 'Unknown')),
            'pozisyon': pos,
            'yedek': backup.get('Oyuncu_Adi', backup.get('Oyuncu', 'Unknown')),
            'rating_farkı': round(rating_diff, 1),
            'recommendation': self._get_injury_recommendation(rating_diff),
            'impact': self._assess_impact(injured_player, backup)
        }
    
    def _get_injury_recommendation(self, rating_diff: float) -> str:
        """Sakatlık durumundaki tavsiye."""
        if rating_diff <= 2:
            return "✓ Yedek benzer seviyede. Minimal etki."
        elif rating_diff <= 5:
            return "⚠️ Yedek biraz daha zayıf. Kısa vadede uyum sağlanabilir."
        else:
            return "🔴 Yedek çok daha zayıf. Ciddi performans kaybı beklenir."
    
    def _assess_impact(self, starter: pd.Series, backup: pd.Series) -> Dict:
        """Sakatlığın kadro üzerindeki etkisi."""
        starter_offense = starter.get('Ofans_Gucu', 75)
        backup_offense = backup.get('Ofans_Gucu', 75)
        
        starter_defense = starter.get('Defans_Gucu', 75)
        backup_defense = backup.get('Defans_Gucu', 75)
        
        return {
            'ofans_kaybı': round(starter_offense - backup_offense, 1),
            'defans_kaybı': round(starter_defense - backup_defense, 1),
            'toplam_etki': round((starter_offense - backup_offense + starter_defense - backup_defense) / 2, 1)
        }
    
    def analyze_squad_depth(self) -> Dict:
        """
        Kadronun derinliğini analiz et.
        
        Returns:
            Dict: Derinlik analizi
        """
        pos_col = 'Alt_Pozisyon' if 'Alt_Pozisyon' in self.starter_squad.columns else 'Atanan_Pozisyon'
        
        depth_analysis = {}
        
        for pos in self.starter_squad[pos_col].unique():
            starter_count = len(self.starter_squad[self.starter_squad[pos_col] == pos])
            backup_count = len(self.bench[self.bench[pos_col] == pos])
            total = starter_count + backup_count
            
            if total == 1:
                depth = "🔴 Kritik - Yedek yok"
            elif total == 2:
                depth = "🟠 Zayıf - Sadece 1 yedek"
            elif total >= 3:
                depth = "🟢 İyi - Derinlik var"
            else:
                depth = "❓ Tanımlanamadı"
            
            depth_analysis[pos] = {
                'starter': starter_count,
                'backup': backup_count,
                'total': total,
                'derinlik': depth
            }
        
        return depth_analysis
    
    def suggest_emergency_formation(self, 
                                   injured_positions: List[str],
                                   all_players: pd.DataFrame) -> Optional[Dict]:
        """
        Acil durumlarda formasyonu değiştir (örn: 3+ oyuncu sakat).
        
        Args:
            injured_positions: Sakat oyuncuların pozisyonları
            all_players: Tüm oyuncular
            
        Returns:
            Dict: Alternatif formasyonlar
        """
        if len(injured_positions) < 2:
            return None
        
        # Yedekleri bul
        pos_col = 'Alt_Pozisyon' if 'Alt_Pozisyon' in all_players.columns else 'Atanan_Pozisyon'
        
        available_backups = {}
        for pos in injured_positions:
            backups = all_players[all_players[pos_col] == pos].nlargest(2, 'Rating')
            available_backups[pos] = len(backups)
        
        # Yedek yok mu?
        critical_positions = [pos for pos, count in available_backups.items() if count == 0]
        
        suggestions = {
            'kritik_durumda_pozisyonlar': critical_positions,
            'önerilen_formasyonlar': []
        }
        
        if critical_positions:
            suggestions['önerilen_formasyonlar'] = [
                "4-4-2 (daha sağlam savunma)",
                "5-4-1 (çok savunmacı)"
            ]
        
        return suggestions
    
    def get_bench_squad_summary(self) -> str:
        """Bench kadrası özeti."""
        bench = self.build_bench_squad()
        
        if bench.empty:
            return "Bench kadrası oluşturulamadı - yeterli yedek oyuncu yok."
        
        avg_rating = bench['Rating'].mean()
        total_cost = bench['Fiyat_M'].sum()
        
        summary = f"📋 **Bench Kadrası Özeti:**\n\n"
        summary += f"- Oyuncu Sayısı: {len(bench)}\n"
        summary += f"- Ortalama Rating: {avg_rating:.0f}\n"
        summary += f"- Toplam Değeri: £{total_cost:.1f}M\n"
        summary += f"- Kalite: "
        
        if avg_rating >= 75:
            summary += "✓ İyi\n"
        elif avg_rating >= 70:
            summary += "⚠️ Orta\n"
        else:
            summary += "🔴 Zayıf\n"
        
        return summary
