"""
=============================================================================
VISUALIZER.PY - GÖRSELLEŞTİRME FONKSİYONLARI
=============================================================================

Bu modül, Plotly kütüphanesi ile interaktif görselleştirmeler oluşturur:
- Futbol sahası görseli (ALT POZİSYON bazlı oyuncu yerleşimi)
- Kadro tabloları
- İstatistik grafikleri

ALT POZİSYON DESTEĞİ:
- Van Dijk (CB) sahada stoper pozisyonunda gösterilir
- Her oyuncu 'Atanan_Pozisyon' sütununa göre yerleştirilir
=============================================================================
"""

import pandas as pd
import plotly.graph_objects as go
from typing import List, Tuple

from .config import (
    FORMATION_POSITIONS, POSITION_COLORS, SUB_POS_TO_GROUP,
    PITCH_LENGTH, PITCH_WIDTH, PITCH_MARGIN,
    PITCH_FIGURE_SIZE, COLORS
)


def create_football_pitch(selected_df: pd.DataFrame, formation: str) -> go.Figure:
    """
    Plotly ile interaktif futbol sahası görseli oluşturur.
    Seçilen oyuncuları ALT POZİSYONLARA göre saha üzerinde konumlandırır.
    
    Args:
        selected_df: Seçilen oyuncuların DataFrame'i ('Atanan_Pozisyon' sütunu olmalı)
        formation: Taktik dizilişi ('4-4-2', '4-3-3', vb.)
        
    Returns:
        go.Figure: Plotly figure nesnesi
        
    Features:
        - İnteraktif hover bilgisi (Alt pozisyon gösterilir)
        - Alt pozisyon bazlı renkler (CB, RB, LB, DM, CM, CAM, LM, RM, LW, RW, ST)
        - Glow efekti
        - Saha çizgileri ve işaretleri
    """
    
    positions = FORMATION_POSITIONS[formation]
    
    # Figure oluştur
    fig = go.Figure()
    
    # =========================================================================
    # SAHA ÇİZİMLERİ
    # =========================================================================
    
    shapes = _create_pitch_shapes()
    
    # =========================================================================
    # OYUNCULARI YERLEŞTİRME (ALT POZİSYONLARA GÖRE)
    # =========================================================================
    
    all_x, all_y, all_colors, all_names, all_hover, all_pos_labels = _prepare_player_data(
        selected_df, positions
    )
    
    # Dış glow efekti
    fig.add_trace(go.Scatter(
        x=all_x,
        y=all_y,
        mode='markers',
        marker=dict(
            size=55,
            color=all_colors,
            opacity=0.4
        ),
        hoverinfo='skip',
        showlegend=False
    ))
    
    # Ana oyuncu noktaları
    fig.add_trace(go.Scatter(
        x=all_x,
        y=all_y,
        mode='markers+text',
        marker=dict(
            size=42,
            color=all_colors,
            line=dict(color='white', width=4),
            symbol='circle'
        ),
        text=all_names,
        textposition='bottom center',
        textfont=dict(size=11, color='white', family='Arial Black'),
        hovertemplate='%{customdata}<extra></extra>',
        customdata=all_hover,
        showlegend=False
    ))
    
    # Pozisyon etiketleri (oyuncu noktasının üstünde)
    fig.add_trace(go.Scatter(
        x=all_x,
        y=[y + 2 for y in all_y],  # Biraz yukarıda göster
        mode='text',
        text=all_pos_labels,
        textfont=dict(size=9, color='white', family='Arial'),
        hoverinfo='skip',
        showlegend=False
    ))
    
    # =========================================================================
    # LAYOUT AYARLARI
    # =========================================================================
    
    fig.update_layout(
        title=dict(
            text=f"<b>⚽ Optimal Kadro - {formation}</b>",
            font=dict(size=22, color='white', family='Georgia'),
            x=0.5,
            y=0.97
        ),
        xaxis=dict(
            showgrid=False,
            showticklabels=False,
            zeroline=False,
            range=[0, PITCH_LENGTH],
            fixedrange=True,
            showline=False,
            visible=False # Tamamen gizle (cerceve sorununu cozer)
        ),
        yaxis=dict(
            showgrid=False,
            showticklabels=False,
            zeroline=False,
            range=[0, PITCH_WIDTH],
            # scaleanchor='x',  # Kuculme sorununa neden oluyor
            # scaleratio=1,     # Kuculme sorununa neden oluyor
            fixedrange=True,
            showline=False,
            visible=False # Tamamen gizle
        ),
        shapes=shapes,
        plot_bgcolor='rgba(0,0,0,0)', # Tamamen seffaf
        paper_bgcolor='rgba(0,0,0,0)', # Tamamen seffaf
        # Genislik ve Yuksekligi sabitleyelim (4:3 veya 3:2 oranini korumak icin)
        # Bu sayede ne cok dar ne cok genis olur.
        width=900,  
        height=600, 
        dragmode='lasso', # Varsayilan arac lasso olsun
        margin=dict(l=10, r=10, t=40, b=10), # Kenar bosluklarini azalt
        # autosize=True, # BU SATIR SILINDI: Resize loop sebebi olabilir
        hoverlabel=dict(
            bgcolor=COLORS['primary_green'],
            font_size=13,
            font_family="Arial",
            font_color="white",
            bordercolor=COLORS['accent_gold']
        )
    )
    
    return fig


def _create_pitch_shapes() -> List[dict]:
    """
    Futbol sahası çizgilerini oluşturur.
    
    Returns:
        List[dict]: Plotly shape nesneleri listesi
    """
    margin_x = PITCH_MARGIN
    margin_y = PITCH_MARGIN
    
    shapes = [
        # Saha dış çizgisi
        dict(type="rect", x0=margin_x, y0=margin_y, 
             x1=PITCH_LENGTH-margin_x, y1=PITCH_WIDTH-margin_y,
             fillcolor=COLORS['pitch_green'], 
             line=dict(color="white", width=3), layer='below'),
        
        # Orta saha çizgisi
        dict(type="line", x0=PITCH_LENGTH/2, y0=margin_y, 
             x1=PITCH_LENGTH/2, y1=PITCH_WIDTH-margin_y,
             line=dict(color="white", width=2), layer='below'),
        
        # Orta daire
        dict(type="circle", x0=PITCH_LENGTH/2-10, y0=PITCH_WIDTH/2-10,
             x1=PITCH_LENGTH/2+10, y1=PITCH_WIDTH/2+10,
             line=dict(color="white", width=2), layer='below'),
        
        # Orta nokta
        dict(type="circle", x0=PITCH_LENGTH/2-1, y0=PITCH_WIDTH/2-1,
             x1=PITCH_LENGTH/2+1, y1=PITCH_WIDTH/2+1,
             fillcolor="white", line=dict(color="white", width=1), layer='below'),
        
        # Sol ceza sahası
        dict(type="rect", x0=margin_x, y0=PITCH_WIDTH/2-18, 
             x1=20, y1=PITCH_WIDTH/2+18,
             line=dict(color="white", width=2), layer='below'),
        
        # Sol kale alanı
        dict(type="rect", x0=margin_x, y0=PITCH_WIDTH/2-9, 
             x1=10, y1=PITCH_WIDTH/2+9,
             line=dict(color="white", width=2), layer='below'),
        
        # Sağ ceza sahası
        dict(type="rect", x0=PITCH_LENGTH-20, y0=PITCH_WIDTH/2-18,
             x1=PITCH_LENGTH-margin_x, y1=PITCH_WIDTH/2+18,
             line=dict(color="white", width=2), layer='below'),
        
        # Sağ kale alanı
        dict(type="rect", x0=PITCH_LENGTH-10, y0=PITCH_WIDTH/2-9,
             x1=PITCH_LENGTH-margin_x, y1=PITCH_WIDTH/2+9,
             line=dict(color="white", width=2), layer='below'),
        
        # Sol kale
        dict(type="rect", x0=0, y0=PITCH_WIDTH/2-6,
             x1=margin_x, y1=PITCH_WIDTH/2+6,
             fillcolor="white", line=dict(color="white", width=1), layer='below'),
        
        # Sağ kale
        dict(type="rect", x0=PITCH_LENGTH-margin_x, y0=PITCH_WIDTH/2-6,
             x1=PITCH_LENGTH, y1=PITCH_WIDTH/2+6,
             fillcolor="white", line=dict(color="white", width=1), layer='below'),
    ]
    
    return shapes


def _prepare_player_data(
    selected_df: pd.DataFrame, 
    positions: dict
) -> Tuple[list, list, list, list, list, list]:
    """
    Oyuncu verilerini ALT POZİSYONLARA GÖRE görselleştirme için hazırlar.
    
    'Atanan_Pozisyon' sütununu kullanarak her oyuncuyu doğru koordinata yerleştirir.
    Bu sayede Van Dijk (CB) asla RB pozisyonunda gösterilmez!
    
    Args:
        selected_df: Seçilen oyuncuların DataFrame'i
        positions: Formasyon pozisyon koordinatları (alt pozisyon bazlı)
        
    Returns:
        tuple: (x_coords, y_coords, colors, names, hover_texts, pos_labels)
    """
    all_x = []
    all_y = []
    all_colors = []
    all_names = []
    all_hover = []
    all_pos_labels = []
    
    # Tüm alt pozisyonları işle
    all_sub_positions = list(positions.keys())
    
    for sub_pos in all_sub_positions:
        if sub_pos not in positions:
            continue
            
        pos_coords = positions[sub_pos]
        
        # Bu alt pozisyona atanmış oyuncuları bul
        # Önce 'Atanan_Pozisyon' varsa onu kullan, yoksa 'Alt_Pozisyon'
        if 'Atanan_Pozisyon' in selected_df.columns:
            pos_players = selected_df[selected_df['Atanan_Pozisyon'] == sub_pos].reset_index(drop=True)
        else:
            pos_players = selected_df[selected_df['Alt_Pozisyon'] == sub_pos].reset_index(drop=True)
        
        for idx in range(len(pos_players)):
            if idx < len(pos_coords):
                px, py = pos_coords[idx]
                player = pos_players.iloc[idx]
                
                all_x.append(px)
                all_y.append(py)
                
                # Alt pozisyona göre renk
                color = POSITION_COLORS.get(sub_pos, '#ffffff')
                all_colors.append(color)
                
                # Oyuncu ismini kısalt (sadece soyisim)
                name_parts = player['Oyuncu'].split()
                short_name = name_parts[-1] if len(name_parts) > 1 else name_parts[0]
                all_names.append(short_name[:10])
                
                # Pozisyon etiketi
                all_pos_labels.append(sub_pos)
                
                # Rating bilgisi varsa ekle
                rating_info = f"Rating: {player['Rating']}<br>" if 'Rating' in player else ""
                
                # Hover text - Alt pozisyon bilgisi dahil
                hover_text = (
                    f"<b>{player['Oyuncu']}</b><br>"
                    f"Pozisyon: {sub_pos}<br>"
                    f"Takım: {player['Takim']}<br>"
                    f"{rating_info}"
                    f"Fiyat: £{player['Fiyat_M']}M<br>"
                    f"Form: {player['Form']}<br>"
                    f"Ofans: {player['Ofans_Gucu']}<br>"
                    f"Defans: {player['Defans_Gucu']}"
                )
                all_hover.append(hover_text)
    
    return all_x, all_y, all_colors, all_names, all_hover, all_pos_labels


def create_team_table(selected_df: pd.DataFrame) -> pd.DataFrame:
    """
    Seçilen kadro için görsel tablo oluşturur.
    ALT POZİSYONLARI gösterir.
    
    Args:
        selected_df: Seçilen oyuncuların DataFrame'i
        
    Returns:
        pd.DataFrame: Görüntüleme için hazırlanmış DataFrame
    """
    # Gerekli sütunları seç
    columns_to_show = ['Oyuncu', 'Fiyat_M', 'Form', 'Ofans_Gucu', 'Defans_Gucu']
    
    # Alt pozisyon sütunu - Atanan veya orijinal
    if 'Atanan_Pozisyon' in selected_df.columns:
        pos_col = 'Atanan_Pozisyon'
    else:
        pos_col = 'Alt_Pozisyon'
    
    display_df = selected_df[columns_to_show].copy()
    display_df.insert(1, 'Pozisyon', selected_df[pos_col])
    
    # Rating varsa ekle
    if 'Rating' in selected_df.columns:
        display_df.insert(2, 'Rating', selected_df['Rating'])
    
    # Sütun isimlerini Türkçeleştir
    col_rename = {
        'Oyuncu': '⚽ Oyuncu',
        'Pozisyon': '📍 Poz',
        'Rating': '⭐ OVR',
        'Fiyat_M': '💰 Fiyat',
        'Form': '📊 Form',
        'Ofans_Gucu': '⚔️ Ofans',
        'Defans_Gucu': '🛡️ Defans'
    }
    display_df = display_df.rename(columns=col_rename)
    
    # Pozisyona göre sırala (GK -> DEF -> MID -> FWD)
    position_order = {
        'GK': 0, 
        'CB': 1, 'RB': 2, 'LB': 3,
        'DM': 4, 'CM': 5, 'CAM': 6, 'RM': 7, 'LM': 8,
        'RW': 9, 'LW': 10, 'ST': 11
    }
    
    display_df['_sort'] = selected_df[pos_col].map(position_order)
    display_df = display_df.sort_values('_sort').drop('_sort', axis=1)
    
    return display_df.reset_index(drop=True)


def create_position_stats_table(selected_df: pd.DataFrame) -> pd.DataFrame:
    """
    Alt pozisyon bazlı istatistik tablosu oluşturur.
    
    Args:
        selected_df: Seçilen oyuncuların DataFrame'i
        
    Returns:
        pd.DataFrame: Pozisyon istatistikleri
    """
    # Pozisyon sütunu - Atanan veya orijinal
    if 'Atanan_Pozisyon' in selected_df.columns:
        pos_col = 'Atanan_Pozisyon'
    else:
        pos_col = 'Alt_Pozisyon'
    
    # İstatistikler
    agg_dict = {
        'Oyuncu': 'count',
        'Fiyat_M': 'sum',
        'Ofans_Gucu': 'mean',
        'Defans_Gucu': 'mean',
        'Form': 'mean'
    }
    
    if 'Rating' in selected_df.columns:
        agg_dict['Rating'] = 'mean'
    
    pos_stats = selected_df.groupby(pos_col).agg(agg_dict).round(1)
    
    # Sütun isimleri
    col_names = ['Sayı', 'Toplam £M', 'Ort. Ofans', 'Ort. Defans', 'Ort. Form']
    if 'Rating' in selected_df.columns:
        col_names.append('Ort. OVR')
    
    pos_stats.columns = col_names
    
    # Sıralama (GK -> DEF -> MID -> FWD)
    order = ['GK', 'CB', 'RB', 'LB', 'DM', 'CM', 'CAM', 'RM', 'LM', 'RW', 'LW', 'ST']
    existing_positions = [p for p in order if p in pos_stats.index]
    pos_stats = pos_stats.reindex(existing_positions)
    
    return pos_stats


def create_squad_summary(selected_df: pd.DataFrame, formation: str) -> dict:
    """
    Kadro özeti oluşturur.
    
    Args:
        selected_df: Seçilen oyuncuların DataFrame'i
        formation: Kullanılan formasyon
        
    Returns:
        dict: Kadro özet bilgileri
    """
    # Pozisyon sütunu
    pos_col = 'Atanan_Pozisyon' if 'Atanan_Pozisyon' in selected_df.columns else 'Alt_Pozisyon'
    
    summary = {
        'formasyon': formation,
        'toplam_oyuncu': len(selected_df),
        'toplam_deger': selected_df['Fiyat_M'].sum(),
        'ortalama_form': selected_df['Form'].mean(),
        'ortalama_ofans': selected_df['Ofans_Gucu'].mean(),
        'ortalama_defans': selected_df['Defans_Gucu'].mean(),
        'pozisyon_dagilimi': selected_df[pos_col].value_counts().to_dict()
    }
    
    if 'Rating' in selected_df.columns:
        summary['ortalama_rating'] = selected_df['Rating'].mean()
    
    return summary
