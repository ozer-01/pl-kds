# ⚽ Premier League Kadro Optimizasyonu - Karar Destek Sistemi

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![PuLP](https://img.shields.io/badge/PuLP-2.7+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 📋 Proje Hakkında

Bu proje, **Karar Destek Sistemleri (Decision Support Systems)** dersi için hazırlanmış bir final projesidir. Uygulama, kullanıcının belirlediği taktik ve bütçe kısıtlarına göre **Doğrusal Programlama (Linear Programming)** kullanarak en optimum futbol kadrosunu (İlk 11) oluşturur.

## 🎯 Özellikler

- **Matematiksel Optimizasyon**: PuLP kütüphanesi ile Binary Integer Programming
- **İnteraktif Arayüz**: Streamlit tabanlı modern web dashboard
- **Görselleştirme**: Plotly ile interaktif futbol sahası
- **Esneklik**: 6 farklı formasyon, 3 farklı strateji

## 🧮 Matematiksel Model

### Karar Değişkenleri
```
x_i ∈ {0, 1} : i. oyuncu seçilirse 1, seçilmezse 0 (Binary)
```

### Amaç Fonksiyonu
```
Maximize Σ (w_off × Ofans_i + w_def × Defans_i + w_form × Form_i) × x_i
```

### Kısıtlar
1. `Σ x_i = 11` (Toplam 11 oyuncu)
2. `Σ x_i (GK) = 1` (Tam 1 kaleci)
3. `Σ x_i (DEF) = formation_def` (Taktik gereği defans sayısı)
4. `Σ x_i (MID) = formation_mid` (Taktik gereği orta saha sayısı)
5. `Σ x_i (FWD) = formation_fwd` (Taktik gereği forvet sayısı)
6. `Σ (Fiyat_i × x_i) ≤ Budget` (Bütçe kısıtı)
7. `x_i = 0 if Sakatlik_i = 1` (Sakat oyuncular seçilemez)

## 📁 Proje Yapısı

```
premier_league_kds/
│
├── main.py                  # Uygulamanın giriş noktası
├── requirements.txt         # Kütüphane bağımlılıkları
├── README.md                # Proje dokümantasyonu
│
└── src/                     # Kaynak kodların ana paketi
    ├── __init__.py          # Paket başlatma
    ├── config.py            # Sabitler (Taktikler, Renkler, Ayarlar)
    ├── data_handler.py      # Veri üretimi ve normalizasyon işlemleri
    ├── optimizer.py         # PuLP modelleme mantığı (Core Engine)
    ├── visualizer.py        # Plotly grafik ve tablo fonksiyonları
    └── ui_components.py     # CSS ve Streamlit arayüz bileşenleri
```

## 🚀 Kurulum ve Çalıştırma

### 1. Gereksinimleri Yükleyin

```bash
# Virtual environment oluştur (önerilir)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate     # Windows

# Bağımlılıkları yükle
pip install -r requirements.txt
```

### 2. Uygulamayı Başlatın

```bash
streamlit run main.py
```

### 3. Tarayıcıda Açın

```
http://localhost:8501
```

## 📦 Bağımlılıklar

| Kütüphane | Versiyon | Açıklama |
|-----------|----------|----------|
| streamlit | ≥1.28.0 | Web arayüzü framework'ü |
| pandas | ≥2.0.0 | Veri manipülasyonu |
| numpy | ≥1.24.0 | Sayısal hesaplamalar |
| pulp | ≥2.7.0 | Doğrusal programlama çözücü |
| plotly | ≥5.18.0 | İnteraktif görselleştirme |

## 🎮 Kullanım

### Kontrol Paneli (Sidebar)

1. **Taktik Dizilişi**: 4-4-2, 4-3-3, 3-5-2, 5-3-2, 4-2-3-1, 3-4-3
2. **Bütçe Limiti**: Slider ile maksimum harcama belirleme
3. **Oyun Stratejisi**: 
   - Ofansif (Ofans: 50%, Defans: 20%, Form: 30%)
   - Defansif (Ofans: 20%, Defans: 50%, Form: 30%)
   - Dengeli (Ofans: 35%, Defans: 35%, Form: 30%)

### Çıktılar

- **Saha Görünümü**: Oyuncuların pozisyonlarını interaktif sahada görüntüleme
- **Kadro Listesi**: Seçilen 11 oyuncunun detaylı tablosu
- **Tüm Oyuncular**: Filtrelenebilir oyuncu havuzu

## 🔧 Gerçek Veri Kullanımı

Dummy veri yerine gerçek CSV verisi kullanmak için `main.py` dosyasında:

```python
# Değiştir:
df_raw = create_dummy_dataset(n_players=60)

# Şununla:
import pandas as pd
df_raw = pd.read_csv("oyuncular.csv")
```

### CSV Formatı

```csv
Oyuncu,Mevki,Takim,Fiyat_M,Form,Ofans_Gucu,Defans_Gucu,Sakatlik
Erling Haaland,FWD,Manchester City,35.0,95,98,25,0
Virgil Van Dijk,DEF,Liverpool,18.0,88,45,95,0
...
```

## 📊 Teknik Detaylar

### Min-Max Normalizasyon
```
X_norm = (X - X_min) / (X_max - X_min)
```

### Çözüm Yöntemi
- **Solver**: CBC (Coin-or Branch and Cut)
- **Problem Tipi**: Binary Integer Programming (BIP)
- **Karmaşıklık**: NP-Hard (Branch & Bound ile çözülür)

## 👨‍💻 Geliştirici

**Karar Destek Sistemleri - Final Projesi**

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

---

⚽ *"En iyi kadro, matematiksel olarak optimal olandır."*

