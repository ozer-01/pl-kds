"""
=============================================================================
EXPLAINABILITY.PY - KADROYA İLİŞKİN AÇIKLAMALAR & KARARLAR
=============================================================================

Karar Açıklanabilirliği (Explainable AI):
- Neden bu oyuncu seçildi?
- Hangi metrikleri nedeniyle seçildi?
- Alternatif oyuncular neden reddedildi?
- Kıyafet kombinasyonları niye bu şekilde?

Bu modül:
1. Oyuncu seçim nedenlerini açıkla
2. SHAP benzeri katkı analizi
3. Feature importance per oyuncu
4. Alternatif açıklamalar (neden o değil, bu?)
=============================================================================
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional


class SquadExplainer:
    """Kadroya ilişkin kararları açıklar."""
    
    def __init__(self, squad_df: pd.DataFrame, all_players: pd.DataFrame):
        self.squad_df = squad_df
        self.all_players = all_players
        
        # Oyuncu çiftleri
        self.player_pairs = self._analyze_player_pairs()
    
    def explain_player_selection(self, player_id: str) -> Dict:
        """
        Neden bu oyuncu seçildi? Ayrıntılı açıklama.
        
        Args:
            player_id: Oyuncu ID'si
            
        Returns:
            Dict: Oyuncu seçiminin gerekçesi
        """
        player = self.squad_df[self.squad_df['ID'] == player_id]
        
        if player.empty:
            return {'error': 'Oyuncu kadrada bulunamadı'}
        
        player = player.iloc[0]
        pos = player.get('Alt_Pozisyon', player.get('Atanan_Pozisyon', 'Unknown'))
        
        explanation = {
            'oyuncu': player.get('Oyuncu_Adi', player.get('Oyuncu', 'Unknown')),
            'pozisyon': pos,
            'nedenleri': self._get_selection_reasons(player),
            'metrikleri': self._get_player_metrics(player),
            'rakipleri': self._get_alternatives(player, pos, top_n=3),
            'puan_katkisi': self._calculate_player_contribution(player),
            'risk_faktoru': self._assess_player_risk(player)
        }
        
        return explanation
    
    def _get_selection_reasons(self, player: pd.Series) -> List[str]:
        """Oyuncu neden seçildi?"""
        reasons = []
        
        rating = player.get('Rating', 0)
        if rating > 85:
            reasons.append(f"⭐ Yüksek Rating ({rating:.0f}) - En iyi performans")
        elif rating > 80:
            reasons.append(f"✓ Üstün Rating ({rating:.0f}) - Kaliteli oyuncu")
        
        form = player.get('Form', 0)
        if form > 8:
            reasons.append(f"🔥 Mükemmel Form ({form:.1f}) - Şu anda çok iyi oynuyor")
        elif form > 7:
            reasons.append(f"✓ İyi Form ({form:.1f}) - Consistent performans")
        
        price = player.get('Fiyat_M', 0)
        avg_price = self.squad_df['Fiyat_M'].mean()
        if price < avg_price * 0.7:
            reasons.append(f"💰 Bütçe Verimli (£{price:.1f}M) - İyi fiyat performansı")
        
        pos = player.get('Alt_Pozisyon', player.get('Atanan_Pozisyon', ''))
        position_count = len(self.squad_df[self.squad_df.get('Alt_Pozisyon', self.squad_df.get('Atanan_Pozisyon')) == pos])
        if position_count <= 2:
            reasons.append(f"🎯 Pozisyon İhtiyacı - {pos} mevkisinde eksik vardı")
        
        if not reasons:
            reasons.append("• Balansız kadro yapısında bu oyuncuya ihtiyaç var")
        
        return reasons
    
    def _get_player_metrics(self, player: pd.Series) -> Dict[str, float]:
        """Oyuncunun ana metrikleri."""
        return {
            'Rating': round(player.get('Rating', 0), 1),
            'Form': round(player.get('Form', 0), 1),
            'Ofans_Gücü': round(player.get('Ofans_Gucu', 0), 1),
            'Defans_Gücü': round(player.get('Defans_Gucu', 0), 1),
            'Fiyat (£M)': round(player.get('Fiyat_M', 0), 1)
        }
    
    def _get_alternatives(self, player: pd.Series, position: str, top_n: int = 3) -> List[Dict]:
        """Alternatif oyuncular neden reddedildi?"""
        pos_col = 'Alt_Pozisyon' if 'Alt_Pozisyon' in self.all_players.columns else 'Atanan_Pozisyon'
        
        # Aynı pozisyonda diğer oyuncuları bul
        alternatives = self.all_players[
            (self.all_players[pos_col] == position) &
            (self.all_players['ID'] != player.get('ID'))
        ].copy()
        
        # Sırala (Rating'e göre)
        alternatives = alternatives.nlargest(top_n + 5, 'Rating')
        
        results = []
        for _, alt in alternatives.head(top_n).iterrows():
            reason = self._compare_with_alternative(player, alt)
            
            results.append({
                'oyuncu': alt.get('Oyuncu_Adi', alt.get('Oyuncu', 'Unknown')),
                'rating': round(alt.get('Rating', 0), 1),
                'fiyat': round(alt.get('Fiyat_M', 0), 1),
                'neden_reddedildi': reason
            })
        
        return results
    
    def _compare_with_alternative(self, selected: pd.Series, alternative: pd.Series) -> str:
        """Neden alternatif reddedildi?"""
        # En önemli kriter
        if alternative.get('Rating', 0) < selected.get('Rating', 0):
            diff = selected.get('Rating', 0) - alternative.get('Rating', 0)
            return f"Daha düşük rating (-{diff:.1f})"
        
        if alternative.get('Form', 0) < selected.get('Form', 0):
            diff = selected.get('Form', 0) - alternative.get('Form', 0)
            return f"Daha kötü form (-{diff:.1f})"
        
        if alternative.get('Fiyat_M', 0) > selected.get('Fiyat_M', 0):
            diff = alternative.get('Fiyat_M', 0) - selected.get('Fiyat_M', 0)
            return f"Daha pahalı (+£{diff:.1f}M)"
        
        return "Seçilen oyuncu daha uygun"
    
    def _calculate_player_contribution(self, player: pd.Series) -> Dict:
        """Bu oyuncunun kadro skoruna katkısı."""
        rating_weight = 0.25
        form_weight = 0.20
        
        rating_contrib = (player.get('Rating', 0) / 100) * rating_weight
        form_contrib = (player.get('Form', 0) / 10) * form_weight
        
        total_contrib = (rating_contrib + form_contrib) / (rating_weight + form_weight)
        
        return {
            'skor_katkı': round(total_contrib, 3),
            'oranı': f"{round(total_contrib * 100 / (rating_weight + form_weight), 1)}%"
        }
    
    def _assess_player_risk(self, player: pd.Series) -> Dict:
        """Oyuncuya ilişkin riskler."""
        risks = []
        
        # Sakatlık riski
        if player.get('Sakatlik', 0) == 1:
            risks.append("🤕 Sakat - Oynamayabilir")
        
        # Form riski
        if player.get('Form', 0) < 6:
            risks.append(f"📉 Düşük Form ({player.get('Form', 0):.1f}) - İyileşme bekleniyor")
        
        # Fiyat riski
        if player.get('Fiyat_M', 0) > 10:
            risks.append(f"💸 Pahalı oyuncu - Yaralanma riski yüksek")
        
        # Yaş riski (tahmin)
        # Genç oyuncu mı?
        rating = player.get('Rating', 0)
        if rating < 70:
            risks.append("⚠️ Deneyimsiz oyuncu - Performans değişken")
        
        return {
            'risk_seviyesi': 'Yüksek' if len(risks) >= 2 else ('Orta' if risks else 'Düşük'),
            'riskler': risks if risks else ['✓ Önemli risk yok']
        }
    
    def _analyze_player_pairs(self) -> Dict[Tuple[str, str], float]:
        """Oyuncu çiftlerinin uyumluluğunu analiz et."""
        pairs = {}
        
        for i, (_, p1) in enumerate(self.squad_df.iterrows()):
            for _, p2 in self.squad_df.iloc[i+1:].iterrows():
                team1 = p1.get('Takim', p1.get('Team', ''))
                team2 = p2.get('Takim', p2.get('Team', ''))
                
                # Aynı takımdan mı?
                same_team_bonus = 0.1 if team1 == team2 else 0
                
                # Pozisyon uyumluluğu
                pos1 = p1.get('Alt_Pozisyon', p1.get('Atanan_Pozisyon', ''))
                pos2 = p2.get('Alt_Pozisyon', p2.get('Atanan_Pozisyon', ''))
                
                # Tamamlayıcı mı?
                complementary = self._are_complementary(pos1, pos2)
                
                compatibility = (
                    (p1.get('Rating', 0) + p2.get('Rating', 0)) / 200 +
                    same_team_bonus +
                    (0.05 if complementary else 0)
                )
                
                pairs[(p1.get('ID', ''), p2.get('ID', ''))] = compatibility
        
        return pairs
    
    def _are_complementary(self, pos1: str, pos2: str) -> bool:
        """İki pozisyon birbirini tamamlıyor mu?"""
        complementary_pairs = [
            ('CB', 'GK'),
            ('RB', 'LB'),
            ('DM', 'CM'),
            ('CM', 'CAM'),
            ('ST', 'CM'),
            ('RW', 'LW'),
        ]
        
        return (pos1, pos2) in complementary_pairs or (pos2, pos1) in complementary_pairs
    
    def generate_squad_narrative(self) -> str:
        """Kadroya ilişkin hikaye oluştur."""
        narrative = "**Kadro Yapısı Analizi:**\n\n"
        
        # En yüksek rated oyuncular
        top_players = self.squad_df.nlargest(3, 'Rating')
        narrative += "🌟 **En İyi Oyuncular:**\n"
        for _, p in top_players.iterrows():
            narrative += f"- {p.get('Oyuncu_Adi', p.get('Oyuncu', 'Unknown'))} ({p.get('Rating', 0):.0f} Rating)\n"
        
        narrative += "\n"
        
        # Pozisyon dağılımı
        pos_col = 'Alt_Pozisyon' if 'Alt_Pozisyon' in self.squad_df.columns else 'Atanan_Pozisyon'
        pos_counts = self.squad_df[pos_col].value_counts()
        narrative += "🎯 **Pozisyon Dağılımı:**\n"
        for pos, count in pos_counts.items():
            narrative += f"- {pos}: {count} oyuncu\n"
        
        narrative += "\n"
        
        # Risk analizi
        low_form = len(self.squad_df[self.squad_df['Form'] < 6])
        if low_form > 0:
            narrative += f"⚠️ **Form Riski:** {low_form} oyuncu düşük formda\n"
        
        injured = len(self.squad_df[self.squad_df.get('Sakatlik', 0) == 1])
        if injured > 0:
            narrative += f"🤕 **Sakatlık:** {injured} oyuncu sakat\n"
        
        return narrative


def explain_squad_changes(old_squad: pd.DataFrame, new_squad: pd.DataFrame, all_players: pd.DataFrame) -> List[Dict]:
    """
    Kadro değişikliklerini açıkla.
    
    Args:
        old_squad: Eski kadro
        new_squad: Yeni kadro
        all_players: Tüm oyuncular
        
    Returns:
        List: Değişikliklerin açıklaması
    """
    changes = []
    
    old_ids = set(old_squad['ID'].tolist())
    new_ids = set(new_squad['ID'].tolist())
    
    # Çıkanlar
    removed_ids = old_ids - new_ids
    for rid in removed_ids:
        old_player = old_squad[old_squad['ID'] == rid].iloc[0]
        replacement = new_squad[~new_squad['ID'].isin(old_ids)].iloc[0] if len(new_squad[~new_squad['ID'].isin(old_ids)]) > 0 else None
        
        if replacement is not None:
            changes.append({
                'tip': 'Değişiklik',
                'çıkan': old_player.get('Oyuncu_Adi', old_player.get('Oyuncu', 'Unknown')),
                'gelen': replacement.get('Oyuncu_Adi', replacement.get('Oyuncu', 'Unknown')),
                'neden': f"Rating: {old_player.get('Rating', 0):.0f} → {replacement.get('Rating', 0):.0f}"
            })
    
    return changes
