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
import pandas as pd

# Modüller
from src.config import (
    PAGE_CONFIG, FORMATIONS, FORMATION_DESCRIPTIONS,
    STRATEGY_DESCRIPTIONS, PLOTLY_CONFIG, POSITION_COLORS,
    POSITIONAL_WEIGHTS
)
from src.data_handler import load_fc26_data, normalize_data
from src.optimizer import solve_optimal_lineup, solve_alternative_lineup, check_formation_availability, calculate_position_score
from src.visualizer import create_football_pitch, create_team_table, create_position_stats_table
from src.ui_components import (
    apply_custom_css, render_main_title, render_metric_card,
    render_info_box, render_footer, render_sidebar_info,
    format_position_display, get_icon
)
from src.decision_analyzer import (
    calculate_weighted_score, calculate_squad_metrics, 
    rank_alternative_solutions, generate_decision_report, get_risk_alerts
)
from src.sensitivity_analyzer import SensitivityAnalyzer
from src.alternative_solutions import (
    what_if_budget_analysis, what_if_rating_minimum, 
    what_if_formation_change
)
from src.explainability import SquadExplainer
from src.compatibility import CompatibilityAnalyzer
from src.pareto_analysis import ParetoAnalyzer
from src.narrative_builder import NarrativeBuilder
from src.bench_analyzer import BenchAnalyzer


# =============================================================================
# SAYFA YAPILANDIRMASI
# =============================================================================
st.set_page_config(**PAGE_CONFIG)


# =============================================================================
# PERFORMANS: VERİ ÖNBELLEKLEME (CACHING)
# =============================================================================
@st.cache_data(ttl=3600, show_spinner=False)
def get_cached_data():
    """
    Veriyi bir kez yükler ve 1 saat boyunca önbelleğe alır.
    Bu sayede her butona basıldığında veri tekrar yüklenmez.
    
    Returns:
        pd.DataFrame: Normalize edilmiş oyuncu verileri
    """
    df_raw = load_fc26_data()
    df_full = normalize_data(df_raw)
    return df_full


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
    # VERİ YÜKLEME (CACHED - Performans İyileştirmesi)
    # =========================================================================
    
    # FC26 oyuncu verilerini önbellekten yükle (ilk seferde işlenir, sonra cache'den gelir)
    with st.spinner("Veriler yükleniyor ve işleniyor..."):
        df_full = get_cached_data()
    
    # Takım listesini al (alfabetik sırala)
    teams = sorted(df_full['Takim'].unique().tolist())
    
    # =========================================================================
    # SIDEBAR - KONTROL PANELİ
    # =========================================================================
    
    with st.sidebar:
        st.markdown(f"## {get_icon('panel')} Kontrol Paneli", unsafe_allow_html=True)
        st.markdown("---")
        
        # =====================================================================
        # TAKIM SEÇİMİ
        # =====================================================================
        st.markdown(f"### {get_icon('stadium')} Takım Seçimi", unsafe_allow_html=True)
        
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
        
        st.markdown(f"**{get_icon('group')} {len(team_df)} oyuncu | {get_icon('healthy')} {team_healthy} sağlıklı**", unsafe_allow_html=True)
        
        # Alt pozisyon dağılımı
        pos_counts = team_df['Alt_Pozisyon'].value_counts()
        pos_text = " | ".join([f"{p}: {c}" for p, c in pos_counts.items()])
        st.caption(f"{pos_text}")
        
        st.markdown("---")
        
        # =====================================================================
        # TAKTİK SEÇİMİ
        # =====================================================================
        st.markdown(f"### {get_icon('tactics')} Taktik Dizilişi", unsafe_allow_html=True)
        formation = st.selectbox(
            "Formasyon seçin:",
            options=list(FORMATIONS.keys()),
            index=0,
            help="Her formasyon farklı alt pozisyonlar gerektirir"
        )
        st.caption(f"{FORMATION_DESCRIPTIONS[formation]}")
        
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
        st.markdown(f"### {get_icon('budget')} Bütçe Limiti", unsafe_allow_html=True)
        
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
        st.markdown(f"<small>{get_icon('bulb')} Takım toplam değer: £{team_df['Fiyat_M'].sum():.1f}M</small>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # =====================================================================
        # STRATEJİ SEÇİMİ
        # =====================================================================
        st.markdown(f"### {get_icon('target')} Oyun Stratejisi", unsafe_allow_html=True)
        strategy = st.radio(
            "Takım stratejisini seçin:",
            options=['Dengeli', 'Ofansif', 'Defansif'],
            index=0,
            help="Seçime göre ofans/defans puanlarının ağırlığı değişir"
        )
        st.markdown(f"<small>{get_icon('ruler')} {STRATEGY_DESCRIPTIONS[strategy]}</small>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # =====================================================================
        # ALTERNATİF KADRO BUTONU
        # =====================================================================
        
        # Alternatif kadro modları
        KADRO_MODLARI = [
            {"id": "optimal", "isim": "Optimal Kadro", "icon": "⚡", "aciklama": "Dengeli optimizasyon"},
            {"id": "rating", "isim": "Rating Odaklı", "icon": "⭐", "aciklama": "En yüksek rating'li oyuncular"},
            {"id": "form", "isim": "Form Odaklı", "icon": "🔥", "aciklama": "En formda oyuncular"},
            {"id": "budget", "isim": "Bütçe Dostu", "icon": "💰", "aciklama": "En verimli kadro"},
            {"id": "attack", "isim": "Hücum Ağırlıklı", "icon": "⚔️", "aciklama": "Maksimum hücum gücü"},
            {"id": "defense", "isim": "Defans Ağırlıklı", "icon": "🛡️", "aciklama": "Maksimum defans gücü"},
        ]
        
        # Session state'de mod indeksini tut
        if 'kadro_mod_index' not in st.session_state:
            st.session_state.kadro_mod_index = 0
        
        # Mevcut mod
        current_mod = KADRO_MODLARI[st.session_state.kadro_mod_index]
        
        # Buton - tıklandığında sonraki moda geç
        optimize_btn = st.button(
            "🔄 Alternatif Kadro Göster",
            use_container_width=True,
            type="primary",
            help="Her tıklamada farklı bir optimizasyon stratejisi ile kadro gösterir"
        )
        
        if optimize_btn:
            # Sonraki moda geç
            st.session_state.kadro_mod_index = (st.session_state.kadro_mod_index + 1) % len(KADRO_MODLARI)
            current_mod = KADRO_MODLARI[st.session_state.kadro_mod_index]
        
        # Aktif modu göster
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #1a472a, #0d2818);
            border-radius: 8px;
            padding: 0.5rem;
            margin-top: 0.5rem;
            text-align: center;
            border: 1px solid #2d5a3d;
        ">
            <span style="font-size: 1.2rem;">{current_mod['icon']}</span>
            <span style="color: #ffd700; font-weight: bold;"> {current_mod['isim']}</span>
            <br>
            <small style="color: #98c379;">({st.session_state.kadro_mod_index + 1}/{len(KADRO_MODLARI)}) {current_mod['aciklama']}</small>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Bilgi kutusu
        st.markdown(f"### {get_icon('book')} Hakkında", unsafe_allow_html=True)
        render_sidebar_info()
    
    # =========================================================================
    # TAKIM VERİSİNİ FİLTRELE
    # =========================================================================
    
    df = df_full[df_full['Takim'] == selected_team].copy()
    
    # =========================================================================
    # ANA EKRAN - OPTİMİZASYON
    # =========================================================================
    
    # Parametre değişikliği kontrolü (mod dahil)
    kadro_mod = current_mod['id']
    current_params = f"{selected_team}_{formation}_{budget}_{strategy}_{kadro_mod}"
    
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
        
        # Moda göre strateji ayarla
        effective_strategy = strategy  # Varsayılan: kullanıcının seçtiği strateji
        
        if kadro_mod == "attack":
            effective_strategy = "Ofansif"
        elif kadro_mod == "defense":
            effective_strategy = "Defansif"
        elif kadro_mod == "rating":
            effective_strategy = "Dengeli"  # Rating ağırlıklı (form düşük)
        elif kadro_mod == "form":
            effective_strategy = "Dengeli"  # Form ağırlıklı
        elif kadro_mod == "budget":
            effective_strategy = "Dengeli"  # Bütçe dostu
        
        # Mod bilgisini session_state'e kaydet
        st.session_state.kadro_mod = current_mod
        
        with st.spinner(f"🔄 {selected_team} için {current_mod['isim']} hesaplanıyor..."):
            # Alternatif modlar için özel işlem
            if kadro_mod in ["rating", "form", "budget"]:
                # Bu modlar için sıralama bazlı seçim yap
                selected_df, total_score, total_cost, status = solve_alternative_lineup(
                    df, formation, budget, kadro_mod
                )
            else:
                # Normal optimizasyon
                selected_df, total_score, total_cost, status = solve_optimal_lineup(
                    df, formation, budget, effective_strategy, use_flexible_positions=True
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
        st.markdown(f"### {get_icon('app_logo')} {current_team} - {current_formation} Optimal Kadro", unsafe_allow_html=True)
        
        # Ortalama rating varsa göster
        avg_rating = selected_df['Rating'].mean() if 'Rating' in selected_df.columns else 0
        
        # =====================================================================
        # METRİK KARTLARI
        # =====================================================================
        st.markdown(f"#### {get_icon('chart')} Kadro Özeti", unsafe_allow_html=True)
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            render_metric_card(f"{total_score:.3f}", "Takım Skoru", "score")
        with col2:
            render_metric_card(f"£{total_cost:.1f}M", "Toplam Maliyet", "cost")
        with col3:
            render_metric_card(f"{avg_rating:.1f}", "Ort. Rating", "rating")
        with col4:
            render_metric_card(f"{selected_df['Form'].mean():.1f}", "Ort. Form", "form")
        with col5:
            render_metric_card(f"£{budget - total_cost:.1f}M", "Kalan Bütçe", "money")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # =====================================================================
        # SEKMELER
        # =====================================================================
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
            "Saha Görünümü", 
            "Kadro Listesi",
            "Takım Kadrosu",
            "Oyuncu Önerileri",
            "Karar Destek",
            "Senaryo Analizi",
            "Oyuncu Uyumluluğu",
            "Pareto Frontier",
            "Kadro Raporu",
            "Bench & Yedekler"
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
            st.caption(f"{debug_text} | Toplam: {len(selected_df)}")
            
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
                        st.markdown(f"##### {get_icon('check')} Seçilen Oyuncular ({len(selected_names)})", unsafe_allow_html=True)
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
            
            st.markdown(f"#### {get_icon('chart')} Pozisyon Bazlı İstatistikler", unsafe_allow_html=True)
            pos_stats = create_position_stats_table(selected_df)
            st.dataframe(pos_stats, use_container_width=True)
        
        # -----------------------------------------------------------------
        # TAB 3: TÜM TAKIM KADROSU
        # -----------------------------------------------------------------
        with tab3:
            st.markdown(f"#### {get_icon('search')} {selected_team} - Tüm Oyuncular", unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                pos_filter = st.multiselect(
                    "Pozisyon Filtresi:",
                    options=['GK', 'CB', 'RB', 'LB', 'DM', 'CM', 'CAM', 'RM', 'LM', 'RW', 'LW', 'ST'],
                    default=['GK', 'CB', 'RB', 'LB', 'DM', 'CM', 'CAM', 'RM', 'LM', 'RW', 'LW', 'ST'],
                    format_func=format_position_display
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
            st.markdown(f"<small>{len(filtered_df)} oyuncu | {get_icon('score')} = İlk 11'de</small>", unsafe_allow_html=True)

        # -----------------------------------------------------------------
        # TAB 4: OYUNCU ÖNERİLERİ
        # -----------------------------------------------------------------
        with tab4:
            st.markdown(f"### {get_icon('score')} Alternatif Oyuncu Önerileri", unsafe_allow_html=True)
            st.markdown("Gerçek Maç İstatistiklerine (xG, xA, Tackles, vb.) dayalı akıllı öneri sistemi.")
            
            col_rec1, col_rec2 = st.columns([1, 2])
            
            with col_rec1:
                rec_pos = st.selectbox(
                    "Hangi Mevki İçin Öneri İstiyorsunuz?",
                    options=list(POSITIONAL_WEIGHTS.keys()),
                    index=list(POSITIONAL_WEIGHTS.keys()).index('ST'), # Default ST
                    format_func=format_position_display
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
                st.markdown(f"#### {get_icon('chart')} En İyi {rec_pos} Oyuncuları", unsafe_allow_html=True)
                
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
        
        # -----------------------------------------------------------------
        # TAB 5: KARAR DESTEK ANALİZİ
        # -----------------------------------------------------------------
        with tab5:
            st.markdown(f"### {get_icon('analytics')} Karar Destek Sistemi", unsafe_allow_html=True)
            
            # Karar raporu oluştur
            weights = {'rating': 0.25, 'form': 0.20, 'offense': 0.20, 'defense': 0.20, 'cost_penalty': 0.15}
            decision_report = generate_decision_report(selected_df, total_score, budget, current_formation, weights)
            
            # 1. Kadro Raporu
            st.subheader("📊 Kadro Analiz Raporu")
            
            col_d1, col_d2, col_d3 = st.columns(3)
            with col_d1:
                st.metric("Toplam Skor", f"{decision_report['weighted_score']:.2f}", "0-100 skala")
            with col_d2:
                st.metric("Bütçe Kullanımı", f"{decision_report['budget_utilization']:.1f}%", f"£{decision_report['total_cost']:.1f}M")
            with col_d3:
                st.metric("Risk Sayısı", len(decision_report['risk_alerts']), "Dikkat Noktası")
            
            # 2. Güçlü ve Zayıf Yönler
            col_str1, col_str2 = st.columns(2)
            
            with col_str1:
                st.subheader("💪 Güçlü Yönler")
                for strength in decision_report['strengths']:
                    st.write(strength)
            
            with col_str2:
                st.subheader("⚠️ Zayıf Yönler")
                for weakness in decision_report['weaknesses']:
                    st.write(weakness)
            
            # 3. Risk Uyarıları
            if decision_report['risk_alerts']:
                st.subheader("🚨 Risk Uyarıları")
                for alert in decision_report['risk_alerts']:
                    if alert['level'] == 'high':
                        st.error(f"**{alert['type']}**: {alert['message']}")
                    else:
                        st.warning(f"**{alert['type']}**: {alert['message']}")
            
            # 4. Öneriler
            st.subheader("💡 Tavsiyeler")
            for rec in decision_report['recommendations']:
                st.write(rec)
            
            # 5. Duyarlılık Analizi
            st.divider()
            st.subheader("📈 Duyarlılık Analizi (Sensitivity Analysis)")
            
            col_sens1, col_sens2 = st.columns(2)
            
            with col_sens1:
                st.info("Hangi parametrenin kadraya en çok etki ettiğini görmek için seçin:")
                param_to_analyze = st.selectbox(
                    "Parametre Seçin:",
                    options=['rating', 'form', 'offense', 'defense', 'cost_penalty'],
                    format_func=lambda x: x.replace('_', ' ').title()
                )
            
            with col_sens2:
                st.info(f"Seçilen parametre: {param_to_analyze.replace('_', ' ').title()}")
            
            # Duyarlılık analizi çalıştır
            try:
                sensitivity_analyzer = SensitivityAnalyzer(selected_df, budget, weights)
                tornado_df = sensitivity_analyzer.tornado_analysis()
                ranking_df = sensitivity_analyzer.parameter_ranking()
                
                st.write("**Parametre Etki Sıralaması (Tornado Analizi):**")
                st.dataframe(ranking_df[['Sıra', 'Parametre', 'Etki_Büyüklüğü', 'Yüzde_Etki']], hide_index=True)
                
                # Seçili parametre için detay
                param_sensitivity = sensitivity_analyzer.analyze_weight_sensitivity(param_to_analyze, step=0.05)
                
                col_chart1, col_chart2 = st.columns(2)
                
                with col_chart1:
                    st.write(f"**{param_to_analyze.title()} Parametresinin Etkisi:**")
                    st.dataframe(param_sensitivity, hide_index=True)
                
                with col_chart2:
                    # Grafik oluştur
                    import plotly.graph_objects as go
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=param_sensitivity['Yüzde_Değişim'],
                        y=param_sensitivity['Skor'],
                        mode='lines+markers',
                        name='Skor',
                        line=dict(color='#1a472a', width=3),
                        marker=dict(size=8, color='#d4af37')
                    ))
                    fig.update_layout(
                        title=f"{param_to_analyze.title()} Sensitivitesi",
                        xaxis_title="Parametre Değişimi (%)",
                        yaxis_title="Kadro Skoru",
                        template="plotly_white",
                        height=400,
                        hovermode='x unified'
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            except Exception as e:
                st.error(f"Duyarlılık analizi hesaplanırken hata: {e}")
        
        # -----------------------------------------------------------------
        # TAB 6: SENARYO ANALİZİ
        # -----------------------------------------------------------------
        with tab6:
            st.markdown(f"### {get_icon('scenarios')} What-If Senaryo Analizi", unsafe_allow_html=True)
            st.markdown("Farklı parametreler değiştiğinde kadroya ne olacağını görmek için senaryoları test edin.")
            
            scenario_type = st.selectbox(
                "Analiz Türü Seçin:",
                options=[
                    "Bütçe Senaryoları",
                    "Rating Minimum Seviyeleri",
                    "Formation Değişiklikleri"
                ]
            )
            
            if scenario_type == "Bütçe Senaryoları":
                st.subheader("💰 Bütçe What-If Analizi")
                st.markdown("Bütçeyi %20 azaltır/arttırırsak ne olur?")
                
                budget_scenarios = what_if_budget_analysis(
                    selected_df, 
                    df_full,
                    budget,
                    budget_changes=[-0.2, -0.1, 0, 0.1, 0.2]
                )
                
                st.dataframe(budget_scenarios, hide_index=True, use_container_width=True)
                
                st.markdown("**Sonuç:** Bütçe değişiklikleri kadroya nasıl etki ediyor?")
                for idx, row in budget_scenarios.iterrows():
                    if row['Bütçe_Değişim'] == '+0%':
                        st.info(f"📍 **Mevcut Senaryo**: {row['Tavsiye']}")
            
            elif scenario_type == "Rating Minimum Seviyeleri":
                st.subheader("⭐ Minimum Rating Seviyeleri What-If Analizi")
                st.markdown("Different quality levels (70, 75, 80, 85) ile ne kadrolar oluşturulabilir?")
                
                rating_scenarios = what_if_rating_minimum(
                    selected_df,
                    df_full,
                    budget,
                    rating_thresholds=[70, 75, 80, 85]
                )
                
                st.dataframe(rating_scenarios, hide_index=True, use_container_width=True)
                
                st.markdown("**Sonuç:** Kalite seviyesi arttıkça kaç oyuncu bulunabiliyor?")
            
            elif scenario_type == "Formation Değişiklikleri":
                st.subheader("🎯 Formation What-If Analizi")
                st.markdown("Farklı formasyonlarla ne kadar başarılı olabiliriz?")
                
                formation_scenarios = what_if_formation_change(
                    selected_df,
                    df_full,
                    budget,
                    formations=['4-3-3', '4-4-2', '3-5-2', '5-3-2']
                )
                
                st.dataframe(formation_scenarios, hide_index=True, use_container_width=True)
                
                st.markdown("**Sonuç:** Formation değişiklikleri oyun gücüne nasıl etki ediyor?")
        
        # -----------------------------------------------------------------
        # TAB 7: OYUNCU UYUMLULUĞU ANALİZİ
        # -----------------------------------------------------------------
        with tab7:
            st.markdown(f"### {get_icon('team')} Oyuncu Uyumluluğu & Takım Kimyası", unsafe_allow_html=True)
            
            # Uyumluluk analizi
            compatibility = CompatibilityAnalyzer(selected_df)
            chemistry = compatibility.get_team_chemistry_score()
            
            # Kimya metrikleri
            col_chem1, col_chem2, col_chem3, col_chem4 = st.columns(4)
            
            with col_chem1:
                st.metric("Ortalama Uyumluluk", f"{chemistry['ortalama_uyumluluk']:.1f}/100", chemistry['takım_kimyası_seviyesi'])
            with col_chem2:
                st.metric("Genel Sinerji", f"{chemistry['genel_sinerji']:.1f}/100", "Tüm faktörler")
            with col_chem3:
                st.metric("Aynı Takımdan", f"{chemistry['aynı_takımdan_oyuncu_oranı']:.1f}%", "Kadroda")
            with col_chem4:
                st.metric("Pozisyon Dengesi", f"{chemistry['pozisyon_dengesi_skoru']:.1f}/100", "Dağılım")
            
            st.info(f"💡 **Takım Kimyası Tavsiyesi**: {chemistry['tavsiye']}")
            
            st.divider()
            
            # En iyi ve en kötü çiftler
            col_best, col_worst = st.columns(2)
            
            with col_best:
                st.subheader("✅ En Uyumlu Çiftler")
                best_pairs = compatibility.get_best_pairs(top_n=5)
                if best_pairs:
                    for idx, pair in enumerate(best_pairs, 1):
                        st.write(f"""
                        **{idx}. {pair['Oyuncu 1']} ↔ {pair['Oyuncu 2']}**
                        - Pozisyon: {pair['Pozisyon 1']} ↔ {pair['Pozisyon 2']}
                        - Uyumluluk: {pair['Uyumluluk']:.1f}/100
                        - {pair['Takım']}
                        """)
            
            with col_worst:
                st.subheader("⚠️ Düşük Uyumlu Çiftler")
                weak_pairs = compatibility.get_weak_pairs(top_n=5)
                if weak_pairs:
                    for idx, pair in enumerate(weak_pairs, 1):
                        st.write(f"""
                        **{idx}. {pair['Oyuncu 1']} ↔ {pair['Oyuncu 2']}**
                        - Pozisyon: {pair['Pozisyon 1']} ↔ {pair['Pozisyon 2']}
                        - Uyumluluk: {pair['Uyumluluk']:.1f}/100
                        - Problem: {pair['Problem']}
                        """)
            
            st.divider()
            
            # Uyumluluk matrisi (heatmap benzeri)
            st.subheader("📊 Uyumluluk Matrisi")
            compat_matrix = compatibility.compatibility_matrix
            
            # Matrisi göster (Streamlit dataframe olarak)
            st.write("Oyuncular arası uyumluluk skorları (0-100):")
            st.dataframe(
                compat_matrix.style.format("{:.0f}"),
                use_container_width=True
            )
        
        # -----------------------------------------------------------------
        # TAB 8: PARETO FRONTIER ANALİZİ
        # -----------------------------------------------------------------
        with tab8:
            st.markdown(f"### {get_icon('chart')} Pareto Frontier - Multi-Objective Optimizasyon", unsafe_allow_html=True)
            st.markdown("Rating maksimize et ↔ Maliyet minimize et - En iyi trade-off çözümleri")
            
            # Pareto analizi
            try:
                pareto = ParetoAnalyzer(df_full, budget)
                
                st.subheader("📈 Efficient Frontier Çözümleri")
                
                # Efficiency metrikleri
                efficiency = pareto.calculate_efficiency_score(selected_df)
                
                col_eff1, col_eff2, col_eff3 = st.columns(3)
                
                with col_eff1:
                    st.metric("Verimlilik Skoru", f"{efficiency['verimlilik_skoru']:.2f}", efficiency['verimlilik_derecesi'])
                with col_eff2:
                    st.metric("Rating/Maliyet Oranı", f"{efficiency['rating_per_milyon']:.2f}", "Birim başına Rating")
                with col_eff3:
                    st.metric("Ortalama Rating", f"{efficiency['ortalama_rating']:.1f}", f"£{efficiency['toplam_maliyet']:.1f}M")
                
                st.divider()
                
                st.subheader("🎯 Trade-off Analizi Seçenekleri")
                
                analysis_type = st.selectbox(
                    "Analiz türü seçin:",
                    options=[
                        "Pareto Frontier Çözümleri",
                        "Alternatif Verimli Kadrolar",
                        "Amaç Ağırlıkları Duyarlılığı"
                    ]
                )
                
                if analysis_type == "Pareto Frontier Çözümleri":
                    st.markdown("**En iyi Rating-Maliyet kombinasyonları:**")
                    
                    pareto_frontier = pareto.generate_pareto_frontier(num_solutions=10)
                    
                    if not pareto_frontier.empty:
                        display_pareto = pareto_frontier[[
                            'Sıra', 'Ortalama Rating', 'Toplam Maliyet', 'Bütçe Kullanımı', 'Kalan Bütçe'
                        ]].copy()
                        
                        st.dataframe(display_pareto, hide_index=True, use_container_width=True)
                        
                        st.markdown("**Sonuç:** Daha yüksek rating için daha fazla para harcamanız gerekecek.")
                
                elif analysis_type == "Alternatif Verimli Kadrolar":
                    st.markdown("**Seçilen kadroya alternatif verimli çözümler:**")
                    
                    alternatives = pareto.find_efficient_alternatives(
                        selected_df,
                        df_full,
                        num_alternatives=3
                    )
                    
                    if alternatives:
                        alt_df = pd.DataFrame([{
                            'Ortalama Rating': alt['Ortalama Rating'],
                            'Toplam Maliyet': alt['Toplam Maliyet'],
                            'Verimlilik': alt['Verimlilik'],
                            'Rating Farkı': alt['Fark (Rating)'],
                            'Maliyet Farkı': alt['Fark (Maliyet)']
                        } for alt in alternatives])
                        
                        st.dataframe(alt_df, hide_index=True, use_container_width=True)
                
                else:  # Amaç Ağırlıkları Duyarlılığı
                    st.markdown("**Amaç ağırlıkları değişirse sonuçlar nasıl değişir?**")
                    
                    sensitivity = pareto.sensitivity_to_objectives(selected_df)
                    
                    st.dataframe(sensitivity, hide_index=True, use_container_width=True)
                    
                    st.markdown("""
                    **Açıklama:**
                    - Rating Ağırlığı ↑ → Daha pahalı oyuncuları tercih eder
                    - Maliyet Ağırlığı ↑ → Daha ekonomik oyuncuları tercih eder
                    """)
            
            except Exception as e:
                st.error(f"Pareto analizi hesaplanırken hata: {e}")

        # -----------------------------------------------------------------
        # TAB 9: KADRO RAPORU (NARRATIVE)
        # -----------------------------------------------------------------
        with tab9:
            st.markdown(f"### {get_icon('report')} Kadro Raporu & Analiz", unsafe_allow_html=True)
            
            # Narrative builder
            narrative = NarrativeBuilder(selected_df, current_formation, budget)
            
            # Hızlı içgörüler
            st.subheader("⚡ Hızlı İçgörüler")
            insights = narrative.get_quick_insights()
            
            col_insight1, col_insight2, col_insight3 = st.columns(3)
            with col_insight1:
                for insight in insights[:2]:
                    st.write(insight)
            with col_insight2:
                for insight in insights[2:4]:
                    st.write(insight)
            with col_insight3:
                for insight in insights[4:]:
                    st.write(insight)
            
            st.divider()
            
            # Sekmeler
            report_tab1, report_tab2, report_tab3 = st.tabs([
                "Genel Özet",
                "Formation Analizi",
                "Tavsiyeler"
            ])
            
            with report_tab1:
                st.markdown(narrative.generate_executive_summary())
            
            with report_tab2:
                st.markdown(narrative.explain_formation_choice())
                st.divider()
                st.markdown(narrative.identify_key_players(top_n=4))
            
            with report_tab3:
                st.markdown(narrative.analyze_strengths_weaknesses())
                st.divider()
                st.markdown(narrative.generate_recommendations())
            
            st.divider()
            
            # Tam raporu indir
            if st.button("📥 Tam Raporu İndir (Markdown)", use_container_width=True):
                full_report = narrative.generate_full_report()
                st.download_button(
                    label="Raporu İndir",
                    data=full_report,
                    file_name=f"kadro_raporu_{current_team}_{current_formation}.md",
                    mime="text/markdown"
                )
        
        # -----------------------------------------------------------------
        # TAB 10: BENCH VE YEDEKLER
        # -----------------------------------------------------------------
        with tab10:
            st.markdown(f"### {get_icon('subs')} Bench Kadrası & Yedek Oyuncular", unsafe_allow_html=True)
            
            bench_analyzer = BenchAnalyzer(selected_df, df)
            
            # Bench kadrası özeti
            st.subheader("📋 Bench Kadrası Özeti")
            st.markdown(bench_analyzer.get_bench_squad_summary())
            
            st.divider()
            
            # Sekmeler
            bench_tab1, bench_tab2, bench_tab3 = st.tabs([
                "Pozisyon Yedekleri",
                "Squad Derinliği",
                "Yaralanma Senaryoları"
            ])
            
            with bench_tab1:
                st.subheader("🔄 Pozisyon Başına En İyi Yedekler")
                
                pos_col = 'Alt_Pozisyon' if 'Alt_Pozisyon' in selected_df.columns else 'Atanan_Pozisyon'
                positions = sorted(selected_df[pos_col].unique().tolist())
                
                selected_position = st.selectbox(
                    "Pozisyon seçin:",
                    options=positions
                )
                
                backups = bench_analyzer.find_position_backups(selected_position, top_n=5)
                
                if backups.empty:
                    st.warning(f"⚠️ {selected_position} pozisyonunda yedek oyuncu yok!")
                else:
                    st.dataframe(backups, hide_index=True, use_container_width=True)
            
            with bench_tab2:
                st.subheader("📊 Squad Derinliği Analizi")
                
                depth_analysis = bench_analyzer.analyze_squad_depth()
                
                depth_df = pd.DataFrame([
                    {
                        'Pozisyon': pos,
                        'Starter': data['starter'],
                        'Yedek': data['backup'],
                        'Toplam': data['total'],
                        'Derinlik': data['derinlik']
                    }
                    for pos, data in depth_analysis.items()
                ])
                
                st.dataframe(depth_df, hide_index=True, use_container_width=True)
                
                st.markdown("""
                **Derinlik Açıklaması:**
                - 🟢 İyi: 3+ oyuncu (Starter + 2 Yedek)
                - 🟠 Zayıf: 2 oyuncu (Starter + 1 Yedek)
                - 🔴 Kritik: 1 oyuncu (Yedek yok!)
                """)
            
            with bench_tab3:
                st.subheader("🤕 Yaralanma Senaryoları")
                
                col_scenario1, col_scenario2 = st.columns(2)
                
                with col_scenario1:
                    st.markdown("**Sakatlık Simülasyonu:**")
                    
                    name_cols = [c for c in ['Oyuncu_Adi', 'Oyuncu'] if c in selected_df.columns]

                    if not name_cols:
                        st.warning("⚠️ Oyuncu isim kolonu bulunamadı.")
                    else:
                        name_col = name_cols[0]

                        injured_name = st.selectbox(
                            "Hangi oyuncu sakat olursa?",
                            options=selected_df[name_col].tolist()
                        )
                        
                        # Oyuncu ID'sini bul (tek kolon üzerinden, fallback ile)
                        injured_player = selected_df[selected_df[name_col] == injured_name]
                        
                        if not injured_player.empty:
                            player_id = injured_player.iloc[0].get('ID', injured_player.index[0])
                            scenario = bench_analyzer.analyze_injury_scenarios(player_id, df)
                            
                            if 'error' not in scenario:
                                st.write(f"**Sakat Oyuncu:** {scenario['sakat_oyuncu']}")
                                st.write(f"**Pozisyon:** {scenario['pozisyon']}")
                                
                                # Yedek oyuncu varsa göster
                                if 'yedek' in scenario:
                                    st.write(f"**Yedek:** {scenario['yedek']}")
                                    st.write(f"**Rating Farkı:** {scenario['rating_farkı']} puan")
                                
                                st.write(f"**Tavsiye:** {scenario['recommendation']}")
                                
                                if 'impact' in scenario and scenario['impact']['toplam_etki'] != 0:
                                    st.write(f"\n**Kadro Etkisi:**")
                                    st.write(f"- Ofans kaybı: {scenario['impact']['ofans_kaybı']:.1f}")
                                    st.write(f"- Defans kaybı: {scenario['impact']['defans_kaybı']:.1f}")
                                    st.write(f"- Toplam: {scenario['impact']['toplam_etki']:.1f} puan")

    
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
