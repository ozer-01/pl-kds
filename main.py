"""
=============================================================================
PREMIER LEAGUE KADRO OPTİMİZASYONU - KARAR DESTEK SİSTEMİ
=============================================================================

Proje: Üniversite Final Projesi - Karar Destek Sistemleri (Decision Support Systems)

Bu uygulama, Doğrusal Programlama (Linear Programming) kullanarak
kullanıcının belirlediği taktik ve bütçe kısıtlarına göre
en optimum futbol kadrosunu (İlk 11) oluşturur.

PREMIER LEAGUE VERİSİ:
- Oyuncu pozisyonları detaylı alt pozisyonlar ile tanımlı (CB, RB, LB, DM, CM, CAM, LM, RM, LW, RW, ST)
- Rating bazlı Fiyat, Form, Ofans, Defans hesaplaması

Kullanılan Teknikler:
- PuLP: Matematiksel Optimizasyon (LP/MILP)
- Streamlit: Web Arayüzü
- Pandas/NumPy: Veri İşleme
- Plotly: Görselleştirme

Çalıştırmak için: streamlit run main.py
=============================================================================
"""

import streamlit as st

# Modüller
from src.config import (
    PAGE_CONFIG, FORMATIONS, FORMATION_DESCRIPTIONS,
    STRATEGY_DESCRIPTIONS, PLOTLY_CONFIG, POSITION_COLORS,
    POSITIONAL_WEIGHTS
)
from src.data_handler import load_fc26_data, normalize_data
from src.optimizer import solve_optimal_lineup, check_formation_availability, calculate_position_score
from src.visualizer import create_football_pitch, create_team_table, create_position_stats_table
from src.ui_components import (
    apply_custom_css, render_main_title, render_metric_card,
    render_info_box, render_footer, render_sidebar_info
)


# =============================================================================
# SAYFA YAPILANDIRMASI
# =============================================================================
st.set_page_config(**PAGE_CONFIG)


def main():
    """
    Streamlit uygulamasının ana fonksiyonu.
    Kullanıcı arayüzünü oluşturur ve optimizasyon sürecini yönetir.
    """
    
    # CSS stillerini uygula
    apply_custom_css()
    
    # Ana başlık
    render_main_title()
    
    # =========================================================================
    # VERİ YÜKLEME
    # =========================================================================
    
    # FC26 oyuncu verilerini yükle
    df_raw = load_fc26_data()
    df_full = normalize_data(df_raw)
    
    # Takım listesini al (alfabetik sırala)
    teams = sorted(df_full['Takim'].unique().tolist())
    
    # =========================================================================
    # SIDEBAR - KONTROL PANELİ
    # =========================================================================
    
    with st.sidebar:
        st.markdown("## 🎮 Kontrol Paneli")
        st.markdown("---")
        
        # =====================================================================
        # TAKIM SEÇİMİ
        # =====================================================================
        st.markdown("### 🏟️ Takım Seçimi")
        
        # Varsayılan takım (Manchester City varsa)
        default_team_idx = teams.index("Manchester City") if "Manchester City" in teams else 0
        
        selected_team = st.selectbox(
            "Takım seçin:",
            options=teams,
            index=default_team_idx,
            help="Kadro bu takımın oyuncularından oluşturulacak"
        )
        
        # Seçilen takımın oyuncu istatistikleri
        team_df = df_full[df_full['Takim'] == selected_team]
        team_healthy = len(team_df[team_df['Sakatlik'] == 0])
        
        st.caption(f"👥 {len(team_df)} oyuncu | ✅ {team_healthy} sağlıklı")
        
        # Alt pozisyon dağılımı
        pos_counts = team_df['Alt_Pozisyon'].value_counts()
        pos_text = " | ".join([f"{p}: {c}" for p, c in pos_counts.items()])
        st.caption(f"📊 {pos_text}")
        
        st.markdown("---")
        
        # =====================================================================
        # TAKTİK SEÇİMİ
        # =====================================================================
        st.markdown("### 📋 Taktik Dizilişi")
        formation = st.selectbox(
            "Formasyon seçin:",
            options=list(FORMATIONS.keys()),
            index=0,
            help="Her formasyon farklı alt pozisyonlar gerektirir"
        )
        st.caption(f"ℹ️ {FORMATION_DESCRIPTIONS[formation]}")
        
        # Formasyon uygunluk kontrolü
        team_healthy_df = team_df[team_df['Sakatlik'] == 0]
        availability = check_formation_availability(team_healthy_df, formation)
        
        if not availability['uygun']:
            st.warning("⚠️ Bu formasyon için bazı pozisyonlarda eksik var!")
            for pos, info in availability['pozisyonlar'].items():
                if not info['yeterli']:
                    st.caption(f"❌ {pos}: {info['mevcut']}/{info['gerekli']}")
        
        st.markdown("---")
        
        # =====================================================================
        # BÜTÇE SLIDER
        # =====================================================================
        st.markdown("### 💰 Bütçe Limiti")
        
        # Takım bazlı bütçe hesapla
        team_min = team_df['Fiyat_M'].nsmallest(11).sum() if len(team_df) >= 11 else team_df['Fiyat_M'].sum()
        team_max = team_df['Fiyat_M'].nlargest(11).sum() if len(team_df) >= 11 else team_df['Fiyat_M'].sum()
        
        budget = st.slider(
            "Maksimum harcama (Milyon £):",
            min_value=float(round(team_min)),
            max_value=float(round(team_max + 20)),
            value=float(round(team_max)),  # Varsayılan: maksimum
            step=5.0,
            help="Kadro için harcanabilecek maksimum tutar"
        )
        st.caption(f"💡 Takım toplam değer: £{team_df['Fiyat_M'].sum():.1f}M")
        
        st.markdown("---")
        
        # =====================================================================
        # STRATEJİ SEÇİMİ
        # =====================================================================
        st.markdown("### 🎯 Oyun Stratejisi")
        strategy = st.radio(
            "Takım stratejisini seçin:",
            options=['Dengeli', 'Ofansif', 'Defansif'],
            index=0,
            help="Seçime göre ofans/defans puanlarının ağırlığı değişir"
        )
        st.caption(f"📐 {STRATEGY_DESCRIPTIONS[strategy]}")
        
        st.markdown("---")
        
        # =====================================================================
        # OPTİMİZE ET BUTONU
        # =====================================================================
        optimize_btn = st.button(
            "🚀 Kadroyu Optimize Et",
            use_container_width=True,
            type="primary"
        )
        
        st.markdown("---")
        
        # Bilgi kutusu
        st.markdown("### 📖 Hakkında")
        render_sidebar_info()
    
    # =========================================================================
    # TAKIM VERİSİNİ FİLTRELE
    # =========================================================================
    
    df = df_full[df_full['Takim'] == selected_team].copy()
    
    # =========================================================================
    # ANA EKRAN - OPTİMİZASYON
    # =========================================================================
    
    # Parametre değişikliği kontrolü
    current_params = f"{selected_team}_{formation}_{budget}_{strategy}"
    
    needs_optimization = (
        'last_params' not in st.session_state or 
        st.session_state.last_params != current_params or
        optimize_btn
    )
    
    if needs_optimization:
        st.session_state.last_params = current_params
        
        # Yeterli sağlıklı oyuncu kontrolü
        healthy_count = len(df[df['Sakatlik'] == 0])
        if healthy_count < 11:
            st.error(
                f"❌ {selected_team} takımında yeterli sağlıklı oyuncu yok!\n\n"
                f"Sağlıklı oyuncu sayısı: {healthy_count} (en az 11 gerekli)\n\n"
                "Lütfen başka bir takım seçin."
            )
            return
        
        with st.spinner(f"🔄 {selected_team} için optimal kadro hesaplanıyor..."):
            selected_df, total_score, total_cost, status = solve_optimal_lineup(
                df, formation, budget, strategy, use_flexible_positions=True
            )
        
        if status == 'Optimal' and selected_df is not None:
            st.session_state.selected_df = selected_df
            st.session_state.total_score = total_score
            st.session_state.total_cost = total_cost
            st.session_state.status = status
            st.session_state.formation = formation
            st.session_state.team = selected_team
        else:
            st.error(
                f"❌ Optimizasyon başarısız! Status: {status}\n\n"
                "Muhtemel sebepler:\n"
                "- Bütçe çok düşük\n"
                "- Bazı pozisyonlarda yeterli oyuncu yok\n"
                "- Formasyon gereksinimleri karşılanamıyor\n\n"
                "Lütfen bütçeyi artırın veya farklı bir taktik deneyin."
            )
            return
    
    # =========================================================================
    # SONUÇLARI GÖSTER
    # =========================================================================
    
    if hasattr(st.session_state, 'selected_df'):
        selected_df = st.session_state.selected_df
        total_score = st.session_state.total_score
        total_cost = st.session_state.total_cost
        current_team = st.session_state.get('team', selected_team)
        current_formation = st.session_state.get('formation', formation)
        
        # Takım ve formasyon başlığı
        st.markdown(f"### ⚽ {current_team} - {current_formation} Optimal Kadro")
        
        # Ortalama rating varsa göster
        avg_rating = selected_df['Rating'].mean() if 'Rating' in selected_df.columns else 0
        
        # =====================================================================
        # METRİK KARTLARI
        # =====================================================================
        st.markdown("#### 📊 Kadro Özeti")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            render_metric_card(f"{total_score:.3f}", "Takım Skoru")
        with col2:
            render_metric_card(f"£{total_cost:.1f}M", "Toplam Maliyet")
        with col3:
            render_metric_card(f"{avg_rating:.1f}", "Ort. Rating")
        with col4:
            render_metric_card(f"{selected_df['Form'].mean():.1f}", "Ort. Form")
        with col5:
            render_metric_card(f"£{budget - total_cost:.1f}M", "Kalan Bütçe")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # =====================================================================
        # SEKMELER
        # =====================================================================
        tab1, tab2, tab3, tab4 = st.tabs([
            "🏟️ Saha Görünümü", 
            "📋 Kadro Listesi",
            "📈 Takım Kadrosu",
            "⭐ Oyuncu Önerileri"
        ])
        
        # -----------------------------------------------------------------
        # TAB 1: SAHA GÖRÜNÜMÜ
        # -----------------------------------------------------------------
        with tab1:
            # Pozisyon dağılımı debug
            if 'Atanan_Pozisyon' in selected_df.columns:
                pos_counts = selected_df['Atanan_Pozisyon'].value_counts().to_dict()
            else:
                pos_counts = selected_df['Alt_Pozisyon'].value_counts().to_dict()
            
            debug_text = " | ".join([f"{k}: {v}" for k, v in sorted(pos_counts.items())])
            st.caption(f"📋 {debug_text} | Toplam: {len(selected_df)}")
            
            # Futbol sahası - Ortalamak için boş kolonlar kullan
            col_left, col_center, col_right = st.columns([1, 6, 1])
            
            with col_center:
                fig = create_football_pitch(selected_df, current_formation)
                
                # Session state'de chart key'i tut (secimi temizlemek icin)
                if 'chart_key' not in st.session_state:
                    st.session_state.chart_key = 0
                
                # Selection event'i yakala
                selection = st.plotly_chart(
                    fig, 
                    use_container_width=False,
                    config=PLOTLY_CONFIG,
                    on_select="rerun",
                    key=f"pitch_chart_{st.session_state.chart_key}" # Dinamik key
                )
            
            # Secilen oyunculari goster
            if selection and "selection" in selection and selection["selection"]["points"]:
                selected_points = selection["selection"]["points"]
                
                # Customdata'dan isimleri ayikla
                selected_names = []
                for p in selected_points:
                    if "customdata" in p:
                        try:
                            raw_html = p["customdata"]
                            if "<b>" in raw_html and "</b>" in raw_html:
                                name = raw_html.split("<b>")[1].split("</b>")[0]
                                selected_names.append(name)
                        except:
                            continue
                
                if selected_names:
                    # Baslik ve temizle butonu yan yana
                    col_title, col_clear = st.columns([6, 1])
                    with col_title:
                        st.markdown(f"##### ✨ Seçilen Oyuncular ({len(selected_names)})")
                    with col_clear:
                        if st.button("❌", help="Seçimi Temizle", key="clear_sel_btn"):
                            st.session_state.chart_key += 1
                            st.rerun()
                    
                    # Secilenleri dataframe'den filtrele
                    subset_df = selected_df[selected_df['Oyuncu'].isin(selected_names)]
                    
                    # Detay tablosu
                    display_sub = create_team_table(subset_df)
                    st.dataframe(display_sub, use_container_width=True, hide_index=True)
            
            # Renk kodları açıklaması
            render_info_box_with_sub_positions()
        
        # -----------------------------------------------------------------
        # TAB 2: KADRO LİSTESİ
        # -----------------------------------------------------------------
        with tab2:
            display_df = create_team_table(selected_df)
            st.dataframe(display_df, use_container_width=True, hide_index=True, height=450)
            
            st.markdown("#### 📊 Pozisyon Bazlı İstatistikler")
            pos_stats = create_position_stats_table(selected_df)
            st.dataframe(pos_stats, use_container_width=True)
        
        # -----------------------------------------------------------------
        # TAB 3: TÜM TAKIM KADROSU
        # -----------------------------------------------------------------
        with tab3:
            st.markdown(f"#### 🔍 {selected_team} - Tüm Oyuncular")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                pos_filter = st.multiselect(
                    "Pozisyon Filtresi:",
                    options=['GK', 'CB', 'RB', 'LB', 'DM', 'CM', 'CAM', 'RM', 'LM', 'RW', 'LW', 'ST'],
                    default=['GK', 'CB', 'RB', 'LB', 'DM', 'CM', 'CAM', 'RM', 'LM', 'RW', 'LW', 'ST']
                )
            with col2:
                injury_filter = st.selectbox(
                    "Sakatlık Durumu:",
                    options=['Tümü', 'Sadece Sağlıklı', 'Sadece Sakat']
                )
            with col3:
                sort_by = st.selectbox(
                    "Sıralama:",
                    options=['Rating', 'Fiyat_M', 'Form', 'Ofans_Gucu', 'Defans_Gucu']
                )
            
            # Filtreleme
            filtered_df = df[df['Alt_Pozisyon'].isin(pos_filter)].copy()
            
            if injury_filter == 'Sadece Sağlıklı':
                filtered_df = filtered_df[filtered_df['Sakatlik'] == 0]
            elif injury_filter == 'Sadece Sakat':
                filtered_df = filtered_df[filtered_df['Sakatlik'] == 1]
            
            filtered_df = filtered_df.sort_values(sort_by, ascending=False)
            filtered_df['Durum'] = filtered_df['Sakatlik'].map({0: '✅', 1: '🤕'})
            filtered_df['Seçildi'] = filtered_df['ID'].isin(selected_df['ID']).map({True: '⭐', False: ''})
            
            # Gösterilecek sütunlar
            display_all = filtered_df[[
                'Seçildi', 'Oyuncu', 'Alt_Pozisyon', 'Rating', 'Fiyat_M',
                'Form', 'Ofans_Gucu', 'Defans_Gucu', 'Durum'
            ]].copy()
            
            display_all.columns = ['✓', 'Oyuncu', 'Poz', 'OVR', '£M', 'Form', 'Ofans', 'Defans', '']
            
            st.dataframe(display_all, use_container_width=True, hide_index=True, height=400)
            st.caption(f"📋 {len(filtered_df)} oyuncu | ⭐ = İlk 11'de")

        # -----------------------------------------------------------------
        # TAB 4: OYUNCU ÖNERİLERİ
        # -----------------------------------------------------------------
        with tab4:
            st.markdown("### ⭐ Alternatif Oyuncu Önerileri")
            st.markdown("Gerçek Maç İstatistiklerine (xG, xA, Tackles, vb.) dayalı akıllı öneri sistemi.")
            
            col_rec1, col_rec2 = st.columns([1, 2])
            
            with col_rec1:
                rec_pos = st.selectbox(
                    "Hangi Mevki İçin Öneri İstiyorsunuz?",
                    options=list(POSITIONAL_WEIGHTS.keys()),
                    index=list(POSITIONAL_WEIGHTS.keys()).index('ST') # Default ST
                )
                
                st.info(f"""
                **{rec_pos} İçin Kullanılan Metrikler:**
                """ + "\n".join([f"- {k}: %{v*100:.0f}" for k, v in POSITIONAL_WEIGHTS[rec_pos].items()]))

            with col_rec2:
                # Sadece bu pozisyona uygun oyuncuları filtrele
                from src.config import POSITION_CAN_BE_FILLED_BY
                eligible_positions = POSITION_CAN_BE_FILLED_BY.get(rec_pos, [rec_pos])
                rec_candidates = df_full[df_full['Alt_Pozisyon'].isin(eligible_positions)].copy()
                
                # Skor hesapla
                rec_candidates['Recommendation_Score'] = rec_candidates.apply(
                    lambda row: calculate_position_score(row, rec_pos), axis=1
                )
                
                # Sırala
                top_candidates = rec_candidates.sort_values('Recommendation_Score', ascending=False).head(10)
                
                # Tablo Gösterimi
                st.markdown(f"#### 🏆 En İyi {rec_pos} Oyuncuları")
                
                # Gösterilecek dinamik sütunlar (o pozisyon için önemli olanlar)
                important_stats = list(POSITIONAL_WEIGHTS[rec_pos].keys())
                display_cols = ['Oyuncu', 'Takim', 'Recommendation_Score', 'Fiyat_M']
                
                # Stat sütunlarını ekle (raw values)
                for stat in important_stats:
                    stat_col = f"stat_{stat}"
                    if stat_col in top_candidates.columns:
                        display_cols.append(stat_col)
                
                display_rec = top_candidates[display_cols].copy()
                
                # Formatlama
                display_rec['Recommendation_Score'] = display_rec['Recommendation_Score'].map('{:.1f}'.format)
                display_rec['Fiyat_M'] = display_rec['Fiyat_M'].map('£{:.1f}M'.format)
                
                st.dataframe(
                    display_rec,
                    column_config={
                        "Recommendation_Score": st.column_config.ProgressColumn(
                            "Skor (0-100)",
                            help="Pozisyonel ağırlıklara göre hesaplanan gerçek performans skoru",
                            format="%s",
                            min_value=0,
                            max_value=100,
                        ),
                    },
                    hide_index=True,
                    use_container_width=True
                )
    
    # Footer
    render_footer()


def render_info_box_with_sub_positions():
    """Alt pozisyonlu bilgi kutusu"""
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #1a472a, #0d2818);
        border-radius: 10px;
        padding: 1rem;
        border: 2px solid #d4af37;
        margin: 1rem 0;
        color: white;
    ">
        <strong style="color: #d4af37;">💡 İpucu:</strong> Oyuncuların üzerine gelerek detaylı bilgi görebilirsiniz.
        <br><br>
        <strong style="color: #d4af37;">Pozisyon Renkleri:</strong><br>
        <span style="color: #ff6b6b;">● GK</span> | 
        <span style="color: #4dabf7;">● CB</span> | 
        <span style="color: #74c0fc;">● RB/LB</span> | 
        <span style="color: #69db7c;">● DM</span> | 
        <span style="color: #51cf66;">● CM</span> | 
        <span style="color: #40c057;">● CAM</span> | 
        <span style="color: #8ce99a;">● RM/LM</span> | 
        <span style="color: #ffd43b;">● ST</span>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# UYGULAMA GİRİŞ NOKTASI
# =============================================================================

if __name__ == "__main__":
    main()
