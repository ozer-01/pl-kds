df_raw = pd.read_csv("oyuncular.csv")
# ⚽ Premier League Kadro Optimizasyonu - Karar Destek Sistemi

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![PuLP](https://img.shields.io/badge/PuLP-2.7+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

Tamamı Streamlit üzerinde çalışan bu uygulama, Premier League oyuncu verisi ile **binary integer programming** kullanarak optimal 11'i kurar, senaryo ve duyarlılık analizleri yapar, uyumluluk skorları üretir, Pareto sınırı çizer ve bench/yedek analizleri sunar. Bu doküman, uygulamayı ilk kez açan birinin tüm sekmeleri ve veri beklentilerini anlaması için hazırlandı.

## 🚀 Hızlı Başlangıç

```bash
# 1) Sanal ortam (önerilir)
python -m venv venv
venv\Scripts\activate   # Windows

# 2) Bağımlılıklar
pip install -r requirements.txt

# 3) Uygulamayı başlat
streamlit run main.py
```

Tarayıcıdan `http://localhost:8501` adresine gidin.

## 📂 Veri ve Yapı

- `data/playerstats_2025.csv`: Ana oyuncu istatistikleri (rating, ofans, defans, form, fiyat, sakatlık, alt pozisyon).
- `data/premier_league_players_tf.csv`: Pozisyon/flex bilgisini destekler (Alt_Pozisyon vs. Atanan_Pozisyon).
- `data/Player-positions.csv`: Ek pozisyon detayları.
- Kaynak kod: `src/` altındaki modüller (optimizer, visualizer, decision_analyzer, sensitivity_analyzer, alternative_solutions, explainability, compatibility, pareto_analysis, narrative_builder, bench_analyzer).

## 🧭 Arayüz Rehberi (Sekmeler)

**Kontrol Paneli (sol sidebar)**
- Takım seçimi: Veriyi kulüp bazında filtreler.
- Formasyon: 4-4-2, 4-3-3, 3-5-2, 5-3-2, 4-2-3-1, 3-4-3.
- Bütçe slider’ı: Maksimum toplam maliyet.
- Strateji: Dengeli, Ofansif, Defansif (ağırlık setlerini etkiler).

**Tab 1 – Optimal 11**
- LP çözümüyle seçilen ilk 11; saha yerleşimi (Plotly pitch) ve detaylı tablo.
- Kadro skorları ve metrik kartları.

**Tab 2 – Karar Destek Raporu**
- `decision_analyzer`: Ağırlıklı skor, risk uyarıları, seçilen/alternatif oyuncular, pozisyon bazlı özetler.

**Tab 3 – Tüm Kadro**
- Pozisyon filtreleri, sakatlık filtresi, sıralama; takımın tüm oyuncu havuzu.

**Tab 4 – Duyarlılık Analizi**
- `sensitivity_analyzer`: Tornado (parametre etki sıralaması) ve seçili parametre için yüzde değişim vs skor tablosu ve çizgi grafiği.

**Tab 5 – What-If Senaryoları**
- Bütçe değişimi, minimum rating seviyesi, formasyon değişikliği senaryoları (`alternative_solutions`).

**Tab 6 – Oyuncu Uyumluluğu**
- `compatibility`: Kimya/uyum skorları, pozisyon eşleşmeleri ve öneriler.

**Tab 7 – Pareto Analizi**
- `pareto_analysis`: Ofans/defans (veya maliyet) için Pareto frontier; grafik ve tablo.

**Tab 8 – Kadro Raporu (Narrative)**
- `narrative_builder`: Yönetici özeti, formasyon seçimi açıklaması, güçlü/zayıf yönler ve öneriler. Markdown indirme butonu.

**Tab 9 – Bench & Yedekler**
- `bench_analyzer`: Pozisyon başına yedekler, kadro derinliği, sakatlık senaryosu simülasyonu.

## 🔢 Optimizasyon Modeli (özet)

Karar değişkeni: $x_i \in \{0,1\}$ oyuncu i seçildiyse 1.

Amaç fonksiyonu (örnek):
$$\max \sum_i (w_{rating} r_i + w_{form} f_i + w_{off} o_i + w_{def} d_i - w_{cost} c_i) x_i$$

Ana kısıtlar:
- Pozisyona göre gerekli oyuncu sayıları (formasyon). 
- Toplam 11 oyuncu.
- Bütçe üst limiti.
- Sakat oyuncu seçilmez.
- Esnek pozisyonlar `config.POSITION_CAN_BE_FILLED_BY` ile kontrol edilir.

Solver: PuLP CBC (varsayılan).

## ⚙️ Konfigürasyon

- `src/config.py`: Formasyonlar, pozisyon esneklikleri, renkler, ikonlar, varsayılan ağırlıklar.
- `src/data_handler.py`: Veri yükleme ve normalizasyon.
- `src/optimizer.py`: PuLP modeli ve skor hesaplama.

## 📦 Bağımlılıklar

| Kütüphane | Versiyon | Not |
|-----------|----------|-----|
| streamlit | ≥1.28.0 | UI |
| pandas | ≥2.0.0 | Veri işleme |
| numpy | ≥1.24.0 | Sayısal işlemler |
| pulp | ≥2.7.0 | BIP çözücü |
| plotly | ≥5.18.0 | Grafik |

## 🛠️ Geliştirici Notları

- Yeni veri kaynağı eklerken `data_handler.py` içindeki kolon adlarıyla uyumlu hale getirin (Oyuncu_Adi/Oyuncu, Alt_Pozisyon, Fiyat_M, Form, Ofans_Gucu, Defans_Gucu, Sakatlik).
- Bench sekmesi isim kolonu fallback’i destekler (Oyuncu_Adi yoksa Oyuncu). 
- İkonlar HTML olarak `DISPLAY_ICONS` sözlüğünde; selectbox’larda ham HTML görünmemesi için `format_position_display` sade metin döndürür.

## 📄 Lisans

MIT Lisansı.

---

⚽ *"En iyi kadro, matematiksel olarak optimal olandır."*

## 🏗️ Proje Mimarisi ve Dosya Yapısı

Bu proje, **Premier League Kadro Optimizasyonu** için geliştirilmiş kapsamlı bir **Karar Destek Sistemidir (DSS)**. Proje, matematiksel optimizasyon (Doğrusal Programlama) tekniklerini modern veri analitiği ve kullanıcı dostu bir web arayüzü ile birleştirir.

Projenin mimarisi **Modüler Katmanlı Mimari** prensibine dayanır. Veri işleme, optimizasyon motoru, analiz modülleri ve kullanıcı arayüzü birbirinden ayrılmıştır.

### 1. Ana Uygulama ve Konfigürasyon

*   **`main.py`** (Giriş Noktası)
    *   **Ne İşe Yarar:** Uygulamanın beynidir. Streamlit web arayüzünü başlatır, kullanıcıdan girdileri (bütçe, taktik vb.) alır ve diğer tüm modülleri koordine eder.
    *   **Kilit Fonksiyonlar:**
        *   `main()`: Tüm uygulama akışını yöneten ana fonksiyon.
        *   Sidebar ve sayfa düzeni oluşturma işlemleri burada yapılır.

*   **`src/config.py`** (Ayarlar)
    *   **Ne İşe Yarar:** Projenin "sabitler" dosyasıdır. Taktik dizilişleri, pozisyon kuralları, renk kodları ve ağırlık katsayıları burada tutulur.
    *   **Kilit Değişkenler:**
        *   `FORMATIONS`: 4-4-2, 4-3-3 gibi dizilişlerin hangi pozisyondan kaç oyuncu gerektirdiğini tanımlar.
        *   `POSITION_CAN_BE_FILLED_BY`: Hangi pozisyonda hangi alternatif oyuncuların oynayabileceğini belirler (Örn: ST pozisyonunda LW oynayabilir mi?).

### 2. Veri Katmanı (Data Layer)

*   **`src/data_handler.py`**
    *   **Ne İşe Yarar:** Ham veriyi (CSV) okur, temizler ve analize hazır hale getirir. Oyuncu fiyatlarını ve istatistiklerini işler.
    *   **Kilit Fonksiyonlar:**
        *   `load_fc26_data()`: Oyuncu verilerini yükler.
        *   `normalize_data()`: Farklı ölçekteki verileri (0-100 arası) normalize eder.
        *   `merge_market_values()`: Oyun verisi ile gerçek piyasa değerlerini birleştirir.

### 3. Çekirdek Mantık ve Optimizasyon (Core Logic)

*   **`src/optimizer.py`** (Motor)
    *   **Ne İşe Yarar:** Projenin kalbidir. **PuLP** kütüphanesini kullanarak matematiksel modeli kurar ve en iyi kadroyu çözer.
    *   **Kilit Fonksiyonlar:**
        *   `solve_optimal_lineup()`: Bütçe ve taktik kısıtlarına göre en yüksek puanlı 11'i seçen optimizasyon fonksiyonu.
        *   `calculate_position_score()`: Bir oyuncunun belirli bir pozisyondaki verimliliğini hesaplar (Rating + İstatistik hibrit puanı).

### 4. Analiz Modülleri (Analysis Modules)

Bu modüller, oluşturulan kadroyu farklı açılardan analiz ederek karar vericiye destek olur.

*   **`src/decision_analyzer.py`**
    *   **Ne İşe Yarar:** Çok kriterli karar verme (MCDM) tekniklerini uygular.
    *   **Kilit Fonksiyonlar:**
        *   `calculate_weighted_score()`: Kadroyu rating, form, ofans ve maliyet gibi kriterlere göre puanlar (TOPSIS benzeri).
        *   `generate_decision_report()`: Kadro hakkında genel bir sağlık raporu üretir.

*   **`src/sensitivity_analyzer.py`**
    *   **Ne İşe Yarar:** "Duyarlılık Analizi" yapar. Parametreler (örneğin bütçe veya form ağırlığı) değişirse sonucun ne kadar değişeceğini ölçer.
    *   **Kilit Fonksiyonlar:**
        *   `analyze_weight_sensitivity()`: Ağırlık değişimlerinin kadro puanına etkisini analiz eder.

*   **`src/pareto_analysis.py`**
    *   **Ne İşe Yarar:** Çok amaçlı optimizasyon yapar. Maliyet ve Performans arasındaki dengeyi (trade-off) gösteren Pareto Eğrisini çizer.
    *   **Kilit Fonksiyonlar:**
        *   `generate_pareto_frontier()`: Farklı bütçe/performans dengesindeki optimal kadro alternatiflerini bulur.

*   **`src/compatibility.py`**
    *   **Ne İşe Yarar:** Oyuncular arasındaki uyumu (Kimya) analiz eder.
    *   **Kilit Fonksiyonlar:**
        *   `_build_compatibility_matrix()`: Aynı takımdan olma veya birbirini tamamlayan pozisyonlara göre uyum puanı hesaplar.

*   **`src/bench_analyzer.py`**
    *   **Ne İşe Yarar:** Sadece ilk 11'i değil, yedek kulübesini de analiz eder.
    *   **Kilit Fonksiyonlar:**
        *   `find_position_backups()`: Her mevkii için en iyi alternatif/yedek oyuncuları önerir.

*   **`src/alternative_solutions.py`**
    *   **Ne İşe Yarar:** "What-If" (Ya şöyle olursa?) senaryolarını çalıştırır.
    *   **Kilit Fonksiyonlar:**
        *   `generate_alternative_squads()`: Kullanıcıya tek bir çözüm yerine alternatif kadro önerileri sunar.

### 5. Sunum ve Görselleştirme (Presentation Layer)

*   **`src/visualizer.py`**
    *   **Ne İşe Yarar:** **Plotly** kullanarak interaktif futbol sahası ve grafikleri çizer.
    *   **Kilit Fonksiyonlar:**
        *   `create_football_pitch()`: Seçilen 11'i taktik dizilişine göre (4-4-2 vb.) saha üzerine yerleştirir.

*   **`src/ui_components.py`**
    *   **Ne İşe Yarar:** Arayüzün makyajıdır. CSS stilleri, kart tasarımları ve ikonlar burada tanımlıdır.
    *   **Kilit Fonksiyonlar:**
        *   `apply_custom_css()`: Uygulamanın renk temasını ve stilini ayarlar.
        *   `render_metric_card()`: İstatistikleri şık kartlar halinde gösterir.

*   **`src/narrative_builder.py`** & **`src/explainability.py`**
    *   **Ne İşe Yarar:** Yapay zekanın kararlarını insan diline çevirir (Explainable AI).
    *   **Kilit Fonksiyonlar:**
        *   `generate_executive_summary()`: Kadro hakkında yönetici özeti metni yazar.
        *   `explain_player_selection()`: "Neden bu oyuncuyu seçtim?" sorusunu cevaplar.

