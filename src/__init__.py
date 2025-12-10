"""
Premier League Kadro Optimizasyonu - Kaynak Kod Paketi
======================================================

Bu paket, Karar Destek Sistemi uygulamasının temel modüllerini içerir.

Modüller:
- config: Sabitler ve yapılandırma ayarları
- data_handler: Veri üretimi ve normalizasyon işlemleri
- optimizer: PuLP ile doğrusal programlama modeli
- visualizer: Plotly grafik ve görselleştirme fonksiyonları
- ui_components: Streamlit CSS ve arayüz bileşenleri
"""

from .config import *
from .data_handler import load_premier_league_data, normalize_data, create_dummy_dataset
from .optimizer import solve_optimal_lineup
from .visualizer import create_football_pitch, create_team_table
from .ui_components import apply_custom_css, render_metric_card, render_info_box

__version__ = "1.0.0"
__author__ = "KDS Final Projesi"

