# ⚽ Premier League Kadro Optimizasyonu - Teknik Dokümantasyon

## 📋 İçindekiler
1. [Proje Genel Bakış](#1-proje-genel-bakış)
2. [Sistem Mimarisi](#2-sistem-mimarisi)
3. [Matematiksel Model](#3-matematiksel-model)
4. [Modül Detayları](#4-modül-detayları)
5. [Veri Akışı](#5-veri-akışı)
6. [Karar Destek Sistemleri Teorisi](#6-karar-destek-sistemleri-teorisi)
7. [Kullanılan Algoritmalar](#7-kullanılan-algoritmalar)

---

## 1. Proje Genel Bakış

### 1.1 Amaç
Bu proje, **Doğrusal Programlama (Linear Programming)** ve **Çok Kriterli Karar Verme (MCDM)** tekniklerini kullanarak Premier League futbol takımları için optimal kadro oluşturan bir **Karar Destek Sistemi (DSS)**'dir.

### 1.2 Problem Tanımı
**Girdi:**
- N adet oyuncu (Rating, Form, Ofans, Defans, Fiyat, Pozisyon)
- Bütçe kısıtı (£M)
- Formasyon seçimi (4-4-2, 4-3-3, vb.)
- Strateji tercihi (Ofansif, Defansif, Dengeli)

**Çıktı:**
- Optimal 11 kişilik kadro
- Toplam skor ve maliyet
- Risk analizi ve öneriler

### 1.3 DSS Katmanları (Simon'ın Modeli)
```
┌─────────────────────────────────────────────────────────────┐
│                    KULLANICI ARAYÜZÜ                        │
│                  (Streamlit + Plotly)                       │
├─────────────────────────────────────────────────────────────┤
│                     MODEL YÖNETİMİ                          │
│    optimizer.py | pareto_analysis.py | sensitivity.py      │
├─────────────────────────────────────────────────────────────┤
│                    VERİ YÖNETİMİ                            │
│           data_handler.py | config.py                      │
├─────────────────────────────────────────────────────────────┤
│                     VERİ TABANI                             │
│                   CSV Dosyaları                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Sistem Mimarisi

### 2.1 Dosya Yapısı
```
pl-kds/
├── main.py                 # Ana uygulama (Streamlit UI)
├── requirements.txt        # Bağımlılıklar
│
├── data/                   # Veri Katmanı
│   ├── Player-positions.csv      # Oyuncu pozisyonları
│   ├── playerstats_2025.csv      # Sezon istatistikleri
│   └── premier_league_players_tf.csv  # Piyasa değerleri
│
└── src/                    # Kaynak Kod
    ├── config.py           # Sabitler ve konfigürasyon
    ├── data_handler.py     # Veri işleme
    ├── optimizer.py        # LP Optimizasyon motoru
    ├── decision_analyzer.py    # TOPSIS analizi
    ├── sensitivity_analyzer.py # Duyarlılık analizi
    ├── alternative_solutions.py # What-If senaryoları
    ├── pareto_analysis.py      # Pareto frontier
    ├── compatibility.py        # Oyuncu uyumluluğu
    ├── bench_analyzer.py       # Yedek analizi
    ├── visualizer.py           # Görselleştirme
    ├── ui_components.py        # UI bileşenleri
    ├── narrative_builder.py    # Rapor oluşturma
    └── explainability.py       # XAI - Açıklanabilirlik
```

### 2.2 Teknoloji Yığını
| Katman | Teknoloji | Amaç |
|--------|-----------|------|
| Frontend | Streamlit | Web arayüzü |
| Görselleştirme | Plotly | İnteraktif grafikler |
| Optimizasyon | PuLP (CBC Solver) | Doğrusal programlama |
| Veri İşleme | Pandas, NumPy | Veri manipülasyonu |
| ML/İstatistik | SciPy, Scikit-learn | İstatistiksel analiz |

---

## 3. Matematiksel Model

### 3.1 Karar Değişkenleri
```
y[i,p] ∈ {0, 1}

Burada:
- i: Oyuncu indeksi (1, 2, ..., N)
- p: Pozisyon (GK, CB, LB, RB, DM, CM, CAM, LM, RM, LW, RW, ST)
- y[i,p] = 1 → Oyuncu i, pozisyon p'ye atandı
- y[i,p] = 0 → Oyuncu i, pozisyon p'ye atanmadı
```

### 3.2 Amaç Fonksiyonu (Maksimizasyon)
```
maximize Z = Σᵢ Σₚ Score(i,p) × y[i,p]

Burada Score(i,p):
  Score = 0.3 × Base_Score + 0.7 × Data_Score

  Base_Score = w_off × Ofans + w_def × Defans + 0.1 × Form
  Data_Score = Σ (Pozisyonel_Ağırlık × İstatistik)
```

### 3.3 Kısıtlar

**Kısıt 1: Her oyuncu en fazla 1 pozisyona atanabilir**
```
Σₚ y[i,p] ≤ 1    ∀i ∈ Oyuncular
```

**Kısıt 2: Her pozisyon için tam gereken sayıda oyuncu**
```
Σᵢ y[i,p] = Required[p]    ∀p ∈ Pozisyonlar

Örnek (4-3-3):
  GK=1, CB=2, LB=1, RB=1, DM=1, CM=2, LW=1, RW=1, ST=1
```

**Kısıt 3: Toplam 11 oyuncu**
```
Σᵢ Σₚ y[i,p] = 11
```

**Kısıt 4: Bütçe kısıtı**
```
Σᵢ (Fiyat[i] × Σₚ y[i,p]) ≤ Budget
```

**Kısıt 5: Pozisyon uyumluluğu**
```
y[i,p] = 0    eğer Oyuncu[i].Pozisyon ∉ Uyumlu[p]

Örnek: LB pozisyonuna sadece LB oyuncusu atanabilir
       ST pozisyonuna ST, LW, RW, CAM atanabilir
```

### 3.4 Çözücü
- **PuLP CBC (COIN-OR Branch and Cut)**
- Tam sayılı programlama için Branch & Bound algoritması
- Optimal çözümü garanti eder

---

## 4. Modül Detayları

### 4.1 optimizer.py - Optimizasyon Motoru

#### Temel Fonksiyonlar:

```python
def calculate_position_score(row: pd.Series, position: str) -> float:
    """
    Hibrit skor hesaplama:
    - %30 Base Score (Rating bazlı)
    - %70 Data Score (İstatistik bazlı)
    
    Eğer istatistik yoksa sadece Base Score × 0.3 (ceza)
    """
```

```python
def solve_optimal_lineup(
    df: pd.DataFrame,
    formation: str,      # '4-4-2', '4-3-3', vb.
    budget: float,       # Maksimum bütçe (£M)
    strategy: str,       # 'Ofansif', 'Defansif', 'Dengeli'
    use_flexible_positions: bool = True
) -> Tuple[Optional[pd.DataFrame], float, float, str]:
    """
    PuLP ile Binary Integer Programming çözer.
    
    Returns:
        - selected_df: Seçilen 11 oyuncu
        - total_score: Toplam kadro skoru
        - total_cost: Toplam maliyet
        - status: 'Optimal', 'Infeasible', vb.
    """
```

### 4.2 decision_analyzer.py - TOPSIS Analizi

#### TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)
En iyi ve en kötü çözüme benzerliğe göre alternatifleri sıralar.

```python
def calculate_weighted_score(squad_df, weights) -> float:
    """
    Ağırlıklı skor hesaplama:
    
    score = (
        rating_component × w_rating +
        form_component × w_form +
        offense_component × w_offense +
        defense_component × w_defense
    ) × cost_factor
    
    Returns: 0-100 arası skor
    """
```

```python
def generate_decision_report(squad_df, total_score, budget, formation, weights) -> Dict:
    """
    Detaylı karar raporu:
    - Kadro metrikleri
    - Güçlü/zayıf yönler
    - Risk uyarıları
    - Öneriler
    """
```

### 4.3 sensitivity_analyzer.py - Duyarlılık Analizi

#### Tornado Analizi
Her parametrenin karar üzerindeki etkisini ölçer.

```python
class SensitivityAnalyzer:
    def tornado_analysis(self) -> pd.DataFrame:
        """
        Her parametre için:
        1. %50 azalt → Skor hesapla
        2. %50 artır → Skor hesapla
        3. Etki büyüklüğü = Yüksek - Düşük
        
        En etkili parametreden en az etkiliye sırala.
        """
    
    def analyze_weight_sensitivity(self, parameter: str) -> pd.DataFrame:
        """
        Tek parametreli analiz:
        -50% ile +50% arasında her %5'te skor değişimini ölç.
        """
```

### 4.4 pareto_analysis.py - Pareto Frontier

#### Çok Amaçlı Optimizasyon
İki çelişen hedef: **Performans ↑** vs **Maliyet ↓**

```python
class ParetoAnalyzer:
    def generate_pareto_frontier(self, num_solutions: int = 20) -> pd.DataFrame:
        """
        Pareto optimal çözümleri bulur.
        
        Bir çözüm Pareto optimal'dir eğer:
        - Başka hiçbir çözüm hem daha yüksek rating'e
        - Hem de daha düşük maliyete sahip değilse
        
        Karar vericiye trade-off'ları gösterir.
        """
    
    def calculate_efficiency_score(self, squad_df) -> Dict:
        """
        Verimlilik = Rating / Maliyet
        
        Yüksek verimlilik = Az parayla çok performans
        """
```

### 4.5 alternative_solutions.py - What-If Analizi

#### Senaryo Planlama
"Ya şöyle olursa?" sorularını cevaplar.

```python
def what_if_budget_analysis(squad_df, all_players, base_budget, budget_changes):
    """
    Bütçe değişiminin etkisi:
    - Bütçe %10 artarsa kaç oyuncu iyileştirilebilir?
    - Bütçe %20 azalırsa kadro kurulabilir mi?
    """

def what_if_rating_minimum(squad_df, all_players, budget, rating_thresholds):
    """
    Minimum rating kısıtının etkisi:
    - Rating ≥ 75 istesek kaç oyuncu uygun?
    - Rating ≥ 85 istesek bütçe yeter mi?
    """

def what_if_formation_change(squad_df, all_players, budget, formations):
    """
    Formasyon değişiminin etkisi:
    - 4-4-2'den 4-3-3'e geçsek ne değişir?
    - Hangi formasyon bu kadro için optimal?
    """
```

### 4.6 visualizer.py - Görselleştirme

```python
def create_football_pitch(selected_df, formation) -> go.Figure:
    """
    Plotly ile interaktif futbol sahası:
    - Oyuncular pozisyonlarına göre yerleştirilir
    - Hover ile detaylı bilgi
    - Pozisyon bazlı renk kodlaması
    """

def create_player_comparison_radar(player1, player2) -> go.Figure:
    """
    İki oyuncuyu karşılaştıran radar chart:
    - Form, Ofans, Defans, Rating, xG, xA vb.
    - Görsel karşılaştırma
    """
```

---

## 5. Veri Akışı

```
┌──────────────────┐
│   CSV Dosyaları  │
│  (Ham Veri)      │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  data_handler.py │
│  - Yükleme       │
│  - Temizleme     │
│  - Normalizasyon │
│  - Fuzzy Match   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   optimizer.py   │
│  - LP Model      │
│  - Kısıtlar      │
│  - Çözüm         │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Analiz Modülleri│
│  - TOPSIS        │
│  - Sensitivity   │
│  - Pareto        │
│  - What-If       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   Görselleştirme │
│  - Saha          │
│  - Grafikler     │
│  - Tablolar      │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Kullanıcı       │
│  (Streamlit UI)  │
└──────────────────┘
```

---

## 6. Karar Destek Sistemleri Teorisi

### 6.1 DSS Tipleri (Alter'ın Sınıflandırması)

| Tip | Açıklama | Projede Kullanım |
|-----|----------|------------------|
| **Model-Driven** | Matematiksel modeller | LP Optimizasyonu |
| **Data-Driven** | Veri analizi | İstatistik entegrasyonu |
| **Knowledge-Driven** | Kural tabanlı | Pozisyon uyumluluğu |

### 6.2 Analitik Hiyerarşi (Gartner)

```
Descriptive     → "Ne oldu?"     → Kadro istatistikleri
     ↓
Diagnostic      → "Neden oldu?"  → Explainability modülü
     ↓
Predictive      → "Ne olacak?"   → Sensitivity analizi
     ↓
Prescriptive    → "Ne yapmalı?"  → LP Optimizasyonu
```

### 6.3 Simon'ın Karar Verme Modeli

1. **Intelligence (Anlama)**: Veri toplama ve analiz
2. **Design (Tasarım)**: Model oluşturma, alternatif üretme
3. **Choice (Seçim)**: Optimal çözüm seçimi
4. **Implementation (Uygulama)**: Sonuçların sunumu

---

## 7. Kullanılan Algoritmalar

### 7.1 Binary Integer Programming (BIP)
- **Problem Tipi**: NP-Hard (Assignment Problem)
- **Çözüm Yöntemi**: Branch & Bound
- **Solver**: PuLP CBC
- **Karmaşıklık**: O(2^n) worst case, pratikte çok daha hızlı

### 7.2 TOPSIS
```
1. Normalize et: r_ij = x_ij / √(Σ x_ij²)
2. Ağırlıkla: v_ij = w_j × r_ij
3. İdeal çözüm: A⁺ = (max v_ij)
4. Anti-ideal: A⁻ = (min v_ij)
5. Uzaklık: D⁺ = √(Σ(v_ij - v_j⁺)²)
6. Skor: C = D⁻ / (D⁺ + D⁻)
```

### 7.3 Pareto Optimality
```
Çözüm X, Y'yi domine eder eğer:
- X en az bir hedefte Y'den iyiyse
- X hiçbir hedefte Y'den kötü değilse

Pareto Frontier = Domine edilmeyen çözümler kümesi
```

### 7.4 Sensitivity Analysis
```
ΔOutput / ΔInput = Duyarlılık

Yüksek duyarlılık → Parametre kritik
Düşük duyarlılık → Parametre önemsiz
```

### 7.5 Fuzzy String Matching
```
Levenshtein Distance kullanılarak:
- "Salah" ↔ "M. Salah" = %85 benzerlik
- Eşik değer: %70+

Takım doğrulaması ile yanlış eşleşme önlenir.
```

---

## 📊 Örnek Çıktılar

### Optimal Kadro Çıktısı
```
┌────────────────┬─────────┬────────┬───────┬───────┬────────┐
│ Oyuncu         │ Pozisyon│ Rating │ Form  │ Ofans │ Maliyet│
├────────────────┼─────────┼────────┼───────┼───────┼────────┤
│ David Raya     │ GK      │ 87     │ 7.5   │ 45    │ £25M   │
│ William Saliba │ CB      │ 88     │ 8.2   │ 52    │ £65M   │
│ ...            │ ...     │ ...    │ ...   │ ...   │ ...    │
└────────────────┴─────────┴────────┴───────┴───────┴────────┘

Toplam Skor: 847.32
Toplam Maliyet: £285.5M
Bütçe Kullanımı: %95.2
```

### Tornado Analizi Çıktısı
```
┌───────────────┬──────────────────┬─────────────┐
│ Parametre     │ Etki Büyüklüğü   │ Önem        │
├───────────────┼──────────────────┼─────────────┤
│ Rating        │ 15.4             │ 🔴 Kritik   │
│ Form          │ 8.7              │ 🟠 Yüksek   │
│ Ofans         │ 5.2              │ 🟡 Orta     │
│ Defans        │ 4.8              │ 🟡 Orta     │
│ Cost_Penalty  │ 2.1              │ 🟢 Düşük    │
└───────────────┴──────────────────┴─────────────┘
```

---

## 📚 Referanslar

1. **Doğrusal Programlama**: Hillier & Lieberman, "Introduction to Operations Research"
2. **TOPSIS**: Hwang & Yoon (1981), "Multiple Attribute Decision Making"
3. **Pareto Optimality**: Vilfredo Pareto, "Manual of Political Economy"
4. **DSS Teorisi**: Turban et al., "Decision Support Systems and Intelligent Systems"

---

*Bu dokümantasyon, Premier League Kadro Optimizasyonu - Karar Destek Sistemi projesi için hazırlanmıştır.*

**Versiyon**: 1.0  
**Tarih**: 2025

