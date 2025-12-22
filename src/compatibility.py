"""
=============================================================================
COMPATIBILITY.PY - OYUNCU UYUMLULUĞU & TAKIM KİMYASI ANALİZİ
=============================================================================

Player Compatibility Analysis:
- Aynı takımdan oyuncuların kimyası
- Tamamlayıcı pozisyon çiftleri
- Takım içi istatistikleri
- Sinerji puanları

Bu modül:
1. Oyuncu çiftlerinin uyumluluğunu hesapla
2. Takım kimyasını analiz et
3. Sinerji puanı ver
4. İdeal kombinasyonları öner
=============================================================================
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional


class CompatibilityAnalyzer:
    """Oyuncu uyumluluğu analizi."""
    
    # Pozisyon çiftleri ve uyumlulukları
    POSITION_SYNERGIES = {
        ('CB', 'CB'): 0.95,      # Merkez savunmacılar iyi çalışır
        ('CB', 'GK'): 0.90,      # Kaleci-savunma uyumu
        ('RB', 'CB'): 0.85,      # Sağ bek - merkez savunma
        ('LB', 'CB'): 0.85,      # Sol bek - merkez savunma
        ('RB', 'LB'): 0.70,      # Bekler arası (az uyum)
        ('DM', 'CM'): 0.88,      # Defansif-merkezli orta saha
        ('CM', 'CAM'): 0.85,     # Merkezli-ofansif orta saha
        ('CM', 'RM'): 0.75,      # Merkezli-kanat (düşük uyum)
        ('CAM', 'ST'): 0.92,     # Ofansif orta-forvet (en yüksek)
        ('RW', 'ST'): 0.90,      # Sağ kanat-forvet
        ('LW', 'ST'): 0.90,      # Sol kanat-forvet
        ('RM', 'RW'): 0.88,      # Sağ kanat-sağ iyeri
        ('LM', 'LW'): 0.88,      # Sol kanat-sol iyeri
    }
    
    # Takım içi uyum bonus'u
    SAME_TEAM_BONUS = 0.15  # Aynı takımdan oyuncuların bonus'u
    
    def __init__(self, squad_df: pd.DataFrame):
        self.squad_df = squad_df
        self.compatibility_matrix = self._build_compatibility_matrix()
    
    def _build_compatibility_matrix(self) -> pd.DataFrame:
        """Kadroda tüm oyuncu çiftlerinin uyumluluğu matrisini oluştur."""
        n_players = len(self.squad_df)
        player_names = self.squad_df['Oyuncu_Adi'].tolist() if 'Oyuncu_Adi' in self.squad_df.columns else self.squad_df['Oyuncu'].tolist()
        
        matrix = pd.DataFrame(
            np.zeros((n_players, n_players)),
            index=player_names,
            columns=player_names
        )
        
        for i, (_, p1) in enumerate(self.squad_df.iterrows()):
            for j, (_, p2) in enumerate(self.squad_df.iterrows()):
                if i != j:
                    compatibility = self.calculate_pair_compatibility(p1, p2)
                    p1_name = p1.get('Oyuncu_Adi', p1.get('Oyuncu', f'Player_{i}'))
                    p2_name = p2.get('Oyuncu_Adi', p2.get('Oyuncu', f'Player_{j}'))
                    matrix.loc[p1_name, p2_name] = compatibility
        
        return matrix
    
    def calculate_pair_compatibility(self, player1: pd.Series, player2: pd.Series) -> float:
        """
        İki oyuncunun uyumluluğu hesapla (0-100).
        
        Faktörler:
        - Pozisyon tamamlayıcılığı
        - Takım kimyası
        - Performans simetrisi
        - Rating dengesi
        """
        base_score = 50.0  # Temel skor
        
        # 1. Pozisyon uyumluluğu
        pos1 = player1.get('Alt_Pozisyon', player1.get('Atanan_Pozisyon', ''))
        pos2 = player2.get('Alt_Pozisyon', player2.get('Atanan_Pozisyon', ''))
        
        position_bonus = self._get_position_synergy(pos1, pos2) * 20
        
        # 2. Takım kimyası
        team1 = player1.get('Takim', player1.get('Team', ''))
        team2 = player2.get('Takim', player2.get('Team', ''))
        team_bonus = self.SAME_TEAM_BONUS * 100 if team1 == team2 else 0
        
        # 3. Rating dengesi (benzer seviye oyuncuların uyumluluğu daha iyi)
        rating1 = player1.get('Rating', 75)
        rating2 = player2.get('Rating', 75)
        rating_diff = abs(rating1 - rating2)
        
        if rating_diff <= 5:
            rating_bonus = 10
        elif rating_diff <= 10:
            rating_bonus = 5
        else:
            rating_bonus = -5
        
        # 4. Form uyumluluğu
        form1 = player1.get('Form', 6)
        form2 = player2.get('Form', 6)
        form_diff = abs(form1 - form2)
        
        if form_diff <= 1:
            form_bonus = 8
        elif form_diff <= 2:
            form_bonus = 4
        else:
            form_bonus = 0
        
        # Son skor
        total_score = base_score + position_bonus + team_bonus + rating_bonus + form_bonus
        
        return round(min(100, max(0, total_score)), 1)
    
    def _get_position_synergy(self, pos1: str, pos2: str) -> float:
        """İki pozisyon arasındaki sinerji (0-1)."""
        # Simetrik ara
        synergy = self.POSITION_SYNERGIES.get(
            (pos1, pos2),
            self.POSITION_SYNERGIES.get((pos2, pos1), 0.60)
        )
        return synergy
    
    def get_best_pairs(self, top_n: int = 5) -> List[Dict]:
        """
        En uyumlu oyuncu çiftlerini bulma.
        
        Returns:
            List: En iyi uyumlu çiftler
        """
        pairs = []
        
        for i, (_, p1) in enumerate(self.squad_df.iterrows()):
            for _, p2 in self.squad_df.iloc[i+1:].iterrows():
                p1_name = p1.get('Oyuncu_Adi', p1.get('Oyuncu', 'Unknown'))
                p2_name = p2.get('Oyuncu_Adi', p2.get('Oyuncu', 'Unknown'))
                
                compatibility = self.calculate_pair_compatibility(p1, p2)
                
                pos1 = p1.get('Alt_Pozisyon', p1.get('Atanan_Pozisyon', ''))
                pos2 = p2.get('Alt_Pozisyon', p2.get('Atanan_Pozisyon', ''))
                
                team1 = p1.get('Takim', p1.get('Team', ''))
                team2 = p2.get('Takim', p2.get('Team', ''))
                same_team = "✓ Aynı Takım" if team1 == team2 else "✗ Farklı Takım"
                
                pairs.append({
                    'Oyuncu 1': p1_name,
                    'Oyuncu 2': p2_name,
                    'Pozisyon 1': pos1,
                    'Pozisyon 2': pos2,
                    'Uyumluluk': compatibility,
                    'Takım': same_team,
                    'Ortalama Rating': round((p1.get('Rating', 75) + p2.get('Rating', 75)) / 2, 1)
                })
        
        # Uyumluluğa göre sırala
        pairs_df = pd.DataFrame(pairs).sort_values('Uyumluluk', ascending=False)
        
        return pairs_df.head(top_n).to_dict('records')
    
    def get_weak_pairs(self, top_n: int = 5) -> List[Dict]:
        """
        En az uyumlu oyuncu çiftlerini bulma.
        
        Returns:
            List: Zayıf uyumlu çiftler (muhtemelen problem olabilir)
        """
        pairs = []
        
        for i, (_, p1) in enumerate(self.squad_df.iterrows()):
            for _, p2 in self.squad_df.iloc[i+1:].iterrows():
                p1_name = p1.get('Oyuncu_Adi', p1.get('Oyuncu', 'Unknown'))
                p2_name = p2.get('Oyuncu_Adi', p2.get('Oyuncu', 'Unknown'))
                
                compatibility = self.calculate_pair_compatibility(p1, p2)
                
                pos1 = p1.get('Alt_Pozisyon', p1.get('Atanan_Pozisyon', ''))
                pos2 = p2.get('Alt_Pozisyon', p2.get('Atanan_Pozisyon', ''))
                
                pairs.append({
                    'Oyuncu 1': p1_name,
                    'Oyuncu 2': p2_name,
                    'Pozisyon 1': pos1,
                    'Pozisyon 2': pos2,
                    'Uyumluluk': compatibility,
                    'Problem': self._identify_compatibility_issue(p1, p2)
                })
        
        # Uyumluluğa göre sırala (en düşük önce)
        pairs_df = pd.DataFrame(pairs).sort_values('Uyumluluk', ascending=True)
        
        return pairs_df[pairs_df['Uyumluluk'] < 60].head(top_n).to_dict('records')
    
    def _identify_compatibility_issue(self, p1: pd.Series, p2: pd.Series) -> str:
        """Uyumsuzluğun sebebi nedir?"""
        pos1 = p1.get('Alt_Pozisyon', p1.get('Atanan_Pozisyon', ''))
        pos2 = p2.get('Alt_Pozisyon', p2.get('Atanan_Pozisyon', ''))
        
        # Pozisyon uyumsuzluğu
        if self._get_position_synergy(pos1, pos2) < 0.70:
            return f"Pozisyon uyumsuzluğu: {pos1} ↔ {pos2}"
        
        # Rating dengesizliği
        rating_diff = abs(p1.get('Rating', 75) - p2.get('Rating', 75))
        if rating_diff > 15:
            return f"Gücü fark: {rating_diff:.0f} puan"
        
        # Form dengesizliği
        form_diff = abs(p1.get('Form', 6) - p2.get('Form', 6))
        if form_diff > 3:
            return f"Form farkı: {form_diff:.1f} puan"
        
        return "Hafif uyumsuzluk"
    
    def get_team_chemistry_score(self) -> Dict:
        """
        Tüm kadroya ilişkin takım kimyası skoru.
        
        Returns:
            Dict: Genel takım kimyası metrikleri
        """
        # Tüm çiftlerin ortalama uyumluluğu
        all_scores = []
        
        for i, (_, p1) in enumerate(self.squad_df.iterrows()):
            for _, p2 in self.squad_df.iloc[i+1:].iterrows():
                score = self.calculate_pair_compatibility(p1, p2)
                all_scores.append(score)
        
        avg_compatibility = np.mean(all_scores) if all_scores else 0
        
        # Same-team oyuncu sayısı
        pos_col = 'Alt_Pozisyon' if 'Alt_Pozisyon' in self.squad_df.columns else 'Atanan_Pozisyon'
        team_col = 'Takim' if 'Takim' in self.squad_df.columns else 'Team'
        
        team_counts = self.squad_df[team_col].value_counts()
        same_team_pairs = sum([c * (c - 1) / 2 for c in team_counts.values])
        total_pairs = len(self.squad_df) * (len(self.squad_df) - 1) / 2
        same_team_ratio = (same_team_pairs / total_pairs) * 100 if total_pairs > 0 else 0
        
        # Pozisyon dağılım dengesi
        pos_counts = self.squad_df[pos_col].value_counts()
        position_balance = 100 - (pos_counts.std() * 10)  # Düşük std = iyi denge
        position_balance = max(0, min(100, position_balance))
        
        return {
            'ortalama_uyumluluk': round(avg_compatibility, 2),
            'takım_kimyası_seviyesi': self._rate_chemistry(avg_compatibility),
            'aynı_takımdan_oyuncu_oranı': round(same_team_ratio, 1),
            'pozisyon_dengesi_skoru': round(position_balance, 1),
            'genel_sinerji': round((avg_compatibility + position_balance) / 2, 2),
            'tavsiye': self._get_chemistry_recommendation(avg_compatibility, same_team_ratio, position_balance)
        }
    
    def _rate_chemistry(self, avg_score: float) -> str:
        """Kimya seviyesini derecelendir."""
        if avg_score >= 75:
            return "🟢 Mükemmel"
        elif avg_score >= 65:
            return "🟡 İyi"
        elif avg_score >= 55:
            return "🟠 Orta"
        else:
            return "🔴 Zayıf"
    
    def _get_chemistry_recommendation(self, avg_compat: float, same_team_ratio: float, pos_balance: float) -> str:
        """Takım kimyasına ilişkin tavsiye."""
        if avg_compat < 55:
            return "⚠️ Kadronun uyumluluğu düşük - Seçimleri gözden geçirin"
        
        if same_team_ratio < 5:
            return "💡 Aynı takımdan daha fazla oyuncu eklemek sinerjiyi arttırabilir"
        
        if pos_balance < 50:
            return "🎯 Pozisyon dağılımını daha dengeli yapın"
        
        return "✓ Takım kimyası iyi dengeli"
    
    def suggest_swap(self, problem_player_id: str, all_players: pd.DataFrame) -> Optional[Dict]:
        """
        Problemli oyuncu için en iyi alternatifi öner.
        
        Args:
            problem_player_id: Değiştirilmesi istenen oyuncu
            all_players: Tüm oyuncular (yedekler)
            
        Returns:
            Dict: Önerilen takas
        """
        problem_player = self.squad_df[self.squad_df['ID'] == problem_player_id]
        
        if problem_player.empty:
            return None
        
        problem_player = problem_player.iloc[0]
        problem_pos = problem_player.get('Alt_Pozisyon', problem_player.get('Atanan_Pozisyon', ''))
        
        # Aynı pozisyonda diğer oyuncuları ara
        pos_col = 'Alt_Pozisyon' if 'Alt_Pozisyon' in all_players.columns else 'Atanan_Pozisyon'
        candidates = all_players[
            (all_players[pos_col] == problem_pos) &
            (all_players['ID'] != problem_player_id)
        ].copy()
        
        if candidates.empty:
            return None
        
        # En iyi adayları score'la
        best_candidates = []
        for _, candidate in candidates.iterrows():
            # Bu adayın kadraya katkısı ne olur?
            temp_squad = self.squad_df.copy()
            temp_squad = temp_squad[temp_squad['ID'] != problem_player_id]
            
            compat_score = 0
            for _, existing in temp_squad.iterrows():
                compat = CompatibilityAnalyzer(pd.DataFrame([candidate])).calculate_pair_compatibility(candidate, existing)
                compat_score += compat
            
            avg_compat = compat_score / len(temp_squad) if len(temp_squad) > 0 else 0
            
            best_candidates.append({
                'candidate_name': candidate.get('Oyuncu_Adi', candidate.get('Oyuncu', 'Unknown')),
                'rating': candidate.get('Rating', 0),
                'avg_compatibility': round(avg_compat, 1),
                'price': candidate.get('Fiyat_M', 0),
                'form': candidate.get('Form', 0)
            })
        
        if not best_candidates:
            return None
        
        best = sorted(best_candidates, key=lambda x: x['avg_compatibility'], reverse=True)[0]
        
        return {
            'problem_oyuncu': problem_player.get('Oyuncu_Adi', problem_player.get('Oyuncu', 'Unknown')),
            'problem_uyumluluk': round(
                sum([self.calculate_pair_compatibility(problem_player, p) for _, p in self.squad_df.iterrows()]) / len(self.squad_df),
                1
            ),
            'önerilen_oyuncu': best['candidate_name'],
            'önerilen_uyumluluk': best['avg_compatibility'],
            'fiyat_farkı': round(best['price'] - problem_player.get('Fiyat_M', 0), 1),
            'neden': f"Kadraya daha iyi uyum sağlar ({best['avg_compatibility']} uyumluluk)"
        }
