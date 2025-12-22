"""
=============================================================================
NARRATIVE_BUILDER.PY - KADROYA İLİŞKİN AÇIKLAMALAR & HİKAYE OLUŞTURMA
=============================================================================

Narrative Generation:
- Kadraya ilişkin hikaye oluştur
- Formation seçimini açıkla
- Pozisyon stratejisini açıkla
- İnsan tarafından anlaşılır raporlar

Bu modül:
1. Kadro hakkında hikaye yaz
2. Taktik açıklamalar
3. Riskleri açıkla
4. Fırsat analizi
=============================================================================
"""

import pandas as pd
from typing import Dict, List


class NarrativeBuilder:
    """Kadraya ilişkin hikaye ve açıklamalar oluşturur."""
    
    def __init__(self, squad_df: pd.DataFrame, formation: str, budget: float):
        self.squad_df = squad_df
        self.formation = formation
        self.budget = budget
    
    def generate_executive_summary(self) -> str:
        """Yönetici özeti - 3-5 cümle."""
        avg_rating = self.squad_df['Rating'].mean()
        total_cost = self.squad_df['Fiyat_M'].sum()
        budget_util = (total_cost / self.budget) * 100
        
        summary = "**Kadro Özeti:**\n\n"
        
        # Rating seviyesi
        if avg_rating >= 85:
            summary += f"🌟 **Elite Kadro**: Ortalama {avg_rating:.0f} rating ile çok yüksek kaliteli oyunculardan oluşan bir takım. "
        elif avg_rating >= 80:
            summary += f"⭐ **Güçlü Kadro**: Ortalama {avg_rating:.0f} rating ile istikrarlı yüksek performans beklenir. "
        elif avg_rating >= 75:
            summary += f"✓ **Dengeli Kadro**: Ortalama {avg_rating:.0f} rating ile ölçülü bir takım. "
        else:
            summary += f"⚠️ **Orta Seviye Kadro**: Ortalama {avg_rating:.0f} rating ile bazı zayıflıklar var. "
        
        # Maliyet
        summary += f"\n💰 **Bütçe Kullanımı**: £{total_cost:.1f}M ({budget_util:.0f}% kullanılmış). "
        
        if budget_util < 80:
            summary += f"Kalan £{self.budget - total_cost:.1f}M ile daha iyi oyuncular almak mümkün."
        else:
            summary += f"Bütçe verimli kullanılmış."
        
        return summary
    
    def explain_formation_choice(self) -> str:
        """Formation seçimini açıkla."""
        pos_col = 'Alt_Pozisyon' if 'Alt_Pozisyon' in self.squad_df.columns else 'Atanan_Pozisyon'
        pos_counts = self.squad_df[pos_col].value_counts()
        
        explanation = f"**{self.formation} Formasyonu Açıklaması:**\n\n"
        
        formation_info = {
            '4-3-3': "Dengeli bir formasyondur. 4 savunmacı, 3 orta sahaçı ve 3 forvet ile saldırı ve defans arasında denge sağlar.",
            '4-4-2': "Klasik İngiliz formasyonu. Sağlam savunma ve güçlü orta saha yapısı vardır. Direkt oyuna uygun.",
            '3-5-2': "Saldırgan formasyondur. 3 merkez savunmacı, 5 orta sahaçı ve 2 forvet ile geniş sahada oyun oynar.",
            '5-3-2': "Defansif formasyondur. 5 savunmacı, 3 orta sahaçı ve 2 forvet ile güvenli bir strateji sunar.",
        }
        
        explanation += formation_info.get(self.formation, "Seçilen formasyondur.\n")
        
        explanation += f"\n**Kadro Dağılımı:**\n"
        for pos, count in pos_counts.items():
            explanation += f"- {pos}: {count} oyuncu\n"
        
        return explanation
    
    def identify_key_players(self, top_n: int = 3) -> str:
        """Kilit oyuncuları belirle."""
        narrative = "**Kilit Oyuncular:**\n\n"
        
        top_players = self.squad_df.nlargest(top_n, 'Rating')
        
        for idx, (_, player) in enumerate(top_players.iterrows(), 1):
            name = player.get('Oyuncu_Adi', player.get('Oyuncu', 'Unknown'))
            rating = player.get('Rating', 0)
            pos = player.get('Alt_Pozisyon', player.get('Atanan_Pozisyon', 'Unknown'))
            form = player.get('Form', 0)
            team = player.get('Takim', player.get('Team', ''))
            
            narrative += f"{idx}. **{name}** ({team}, {pos})\n"
            narrative += f"   - Rating: {rating:.0f} | Form: {form:.1f}/10\n"
            narrative += f"   - Rol: Kadroun omurgasını oluşturuyor. Başarısı takımın başarısını belirler.\n\n"
        
        return narrative
    
    def analyze_strengths_weaknesses(self) -> str:
        """Güçlü ve zayıf yönleri detaylı analiz et."""
        narrative = "**Detaylı Analiz:**\n\n"
        
        # Güçlü yönler
        narrative += "💪 **Güçlü Yönler:**\n\n"
        
        avg_rating = self.squad_df['Rating'].mean()
        if avg_rating > 82:
            narrative += f"- Çok yüksek kalite seviyesi ({avg_rating:.0f}). Tüm oyuncular elit seviye.\n"
        elif avg_rating > 78:
            narrative += f"- Üstün performans beklentisi ({avg_rating:.0f}). İstikrarlı şekilde iyi sonuçlar.\n"
        
        avg_form = self.squad_df['Form'].mean()
        if avg_form > 7.5:
            narrative += f"- Mükemmel form durumu ({avg_form:.1f}/10). Oyuncular şu anda çok iyi oynuyor.\n"
        
        avg_offense = self.squad_df['Ofans_Gucu'].mean()
        if avg_offense > 75:
            narrative += f"- Güçlü hücum gücü ({avg_offense:.0f}). Gol atma potansiyeli yüksek.\n"
        
        avg_defense = self.squad_df['Defans_Gucu'].mean()
        if avg_defense > 75:
            narrative += f"- Sağlam savunma ({avg_defense:.0f}). Düşük gol yeme riski.\n"
        
        narrative += "\n"
        
        # Zayıf yönler
        narrative += "⚠️ **Zayıf Yönler & Riskler:**\n\n"
        
        low_form = len(self.squad_df[self.squad_df['Form'] < 6])
        if low_form > 0:
            narrative += f"- {low_form} oyuncu kötü formda. Forma gelmelerini beklemek gerekiyor.\n"
        
        injured = len(self.squad_df[self.squad_df.get('Sakatlik', 0) == 1])
        if injured > 0:
            narrative += f"- {injured} oyuncu sakat. Yoklukları ayakta tutan oyuncuları zorlayabilir.\n"
        
        high_cost = len(self.squad_df[self.squad_df['Fiyat_M'] > 10])
        if high_cost > 3:
            narrative += f"- {high_cost} pahalı oyuncu. Yaralanma riski yüksek çünkü çok önemli roller oynuyorlar.\n"
        
        if avg_form < 6.5:
            narrative += f"- Genel olarak düşük form ({avg_form:.1f}). İlk maçlar zor olabilir.\n"
        
        return narrative
    
    def generate_recommendations(self) -> str:
        """Tavsiyeleri oluştur."""
        recommendations = "**Tavsiyeler:**\n\n"
        
        total_cost = self.squad_df['Fiyat_M'].sum()
        remaining = self.budget - total_cost
        
        if remaining > 10:
            recommendations += f"1. 💡 **Bütçe Ayırın**: £{remaining:.1f}M kalan bütçeniz var. Yaralanma durumunda yedek oyuncu almaya hazırlıklı olun.\n\n"
        
        low_form_count = len(self.squad_df[self.squad_df['Form'] < 6])
        if low_form_count > 1:
            recommendations += f"2. 🔄 **Forma Bekleme**: {low_form_count} oyuncu düşük formda. Sonraki haftalar onları forma getirmek için sabırlı olun.\n\n"
        
        high_price = self.squad_df.nlargest(1, 'Fiyat_M').iloc[0] if len(self.squad_df) > 0 else None
        if high_price is not None and high_price.get('Fiyat_M', 0) > 12:
            name = high_price.get('Oyuncu_Adi', high_price.get('Oyuncu', 'Unknown'))
            recommendations += f"3. 🛡️ **Kilit Oyuncuyu Koruyun**: {name} en pahalı oyuncu. Yaralanma riski en yüksek. Rotasyon düşünün.\n\n"
        
        avg_defense = self.squad_df['Defans_Gucu'].mean()
        if avg_defense < 70:
            recommendations += "4. 🎯 **Savunmayı Güçlendirin**: Defans gücü zayıf. Set-piece'te dikkatli olun.\n\n"
        
        avg_offense = self.squad_df['Ofans_Gucu'].mean()
        if avg_offense > 78:
            recommendations += "5. ⚡ **Saldırıdan Yaralanın**: Takımın hücum potansiyeli yüksek. Hücum oyuncularına maç enerjisine sahip çıkın.\n\n"
        
        return recommendations
    
    def generate_full_report(self) -> str:
        """Tam rapor oluştur."""
        report = ""
        report += self.generate_executive_summary()
        report += "\n\n---\n\n"
        report += self.explain_formation_choice()
        report += "\n\n---\n\n"
        report += self.identify_key_players(top_n=3)
        report += "\n---\n\n"
        report += self.analyze_strengths_weaknesses()
        report += "\n---\n\n"
        report += self.generate_recommendations()
        
        return report
    
    def get_quick_insights(self) -> List[str]:
        """Hızlı içgörüler (bullet points)."""
        insights = []
        
        # Rating insight
        avg_rating = self.squad_df['Rating'].mean()
        insights.append(f"📊 Ortalama Rating: {avg_rating:.0f}")
        
        # Form insight
        avg_form = self.squad_df['Form'].mean()
        if avg_form > 7:
            insights.append(f"🔥 Form: Çok İyi ({avg_form:.1f})")
        elif avg_form < 6:
            insights.append(f"📉 Form: Kötü ({avg_form:.1f}) - İyileşme gerekli")
        else:
            insights.append(f"✓ Form: Normal ({avg_form:.1f})")
        
        # Cost insight
        total_cost = self.squad_df['Fiyat_M'].sum()
        insights.append(f"💰 Maliyet: £{total_cost:.1f}M")
        
        # Position balance
        pos_col = 'Alt_Pozisyon' if 'Alt_Pozisyon' in self.squad_df.columns else 'Atanan_Pozisyon'
        pos_std = self.squad_df[pos_col].value_counts().std()
        if pos_std < 1.5:
            insights.append(f"⚖️ Pozisyon Dengesi: Mükemmel")
        else:
            insights.append(f"⚖️ Pozisyon Dengesi: Dengesiz")
        
        # Risk
        low_form = len(self.squad_df[self.squad_df['Form'] < 6])
        if low_form > 0:
            insights.append(f"⚠️ Risk: {low_form} oyuncu düşük formda")
        else:
            insights.append(f"✓ Risk: Minimal")
        
        return insights
