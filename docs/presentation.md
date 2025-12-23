# 20 Dakikalık Sunum Metni

Aşağıdaki akış, 20 dakikalık bir sunum için konuşma rehberidir. Süre önerileri toplam 20 dakikaya göredir; gerektiğinde kısaltılabilir.

## 0:00–1:00 | Açılış ve Amaç
- Premier League kadro optimizasyonu için geliştirilmiş karar destek sistemi.
- Amaç: bütçe, formasyon ve strateji kısıtları altında optimal 11’i kurmak; yedek ve risk analizleriyle kararı güçlendirmek.

## 1:00–3:00 | Problemin Çerçevesi
- Analistlerin üç zorluğu: (1) Bütçe kısıtı, (2) Pozisyon uyumluluğu ve esneklik, (3) Sakatlık/senaryo riskleri.
- Başarı kriterleri: skor maksimize, bütçe ≤ limit, pozisyon gereksinimleri sağlanmış, sakat oyuncu seçilmez.

## 3:00–5:00 | Veri ve Model Özet
- Veri: 2025 oyuncu istatistikleri (rating, form, ofans, defans, fiyat, sakatlık, alt pozisyon).
- Model: Binary Integer Programming (PuLP/CBC). Karar değişkeni: oyuncu seçimi (0/1).
- Amaç fonksiyonu: ağırlıklı performans – maliyet. Kısıtlar: formasyon pozisyon sayıları, toplam 11, bütçe, sakatlık filtresi, pozisyon esnekliği.
- Ağırlıklar stratejiye göre dinamik (Dengeli, Ofansif, Defansif).

## 5:00–7:00 | Uygulama Mimarisi (Kısa)
- Streamlit UI; modüller: optimizer, decision_analyzer, sensitivity_analyzer, alternative_solutions, compatibility, pareto_analysis, narrative_builder, bench_analyzer.
- Plotly sahası ve Pareto grafikleri; pandas veri işleme; PuLP CBC çözücü.

## 7:00–12:00 | Canlı Demo Akışı (Sekmeler)
1) Kontrol Paneli: Takım, formasyon, bütçe, strateji seçimi.
2) Optimal 11: Pitch yerleşimi, metrik kartları, tablo.
3) Karar Destek Raporu: Ağırlıklı skor, risk uyarıları, alternatif oyuncular, pozisyon özetleri.
4) Tüm Kadro: Pozisyon/sakatlık filtresi, sıralama; oyuncu havuzu.
5) Duyarlılık Analizi: Tornado (parametre etki sıralaması), seçili parametre için yüzde değişimi grafiği.
6) What-If Senaryoları: Bütçe +/-%, minimum rating eşikleri, formasyon değişikliği.
7) Uyumluluk: Kimya/uyum skorları ve öneriler.
8) Pareto Analizi: Ofans/defans-maliyet Pareto frontier, frontier oyuncuları.
9) Narrative Rapor: Yönetici özeti, formasyon gerekçesi, güçlü/zayıf yönler, öneriler; Markdown indirme.
10) Bench & Yedekler: Pozisyon yedekleri, kadro derinliği, sakatlık senaryosu simülasyonu.

## 12:00–14:00 | Sonuçlar ve Değer Önerisi
- Hızlı optimal kadro üretimi; risklerin görünür kılınması.
- Duyarlılık ve senaryo modülleriyle “neden bu kadro?” sorusuna kanıta dayalı cevap.
- Pareto ve uyumluluk analizleriyle denge ve kimya optimizasyonu.

## 14:00–16:00 | Kısıtlar ve Öğrenilenler
- Veriye bağımlılık: kolon adlarının tutarlılığı (Oyuncu_Adi/Oyuncu, Alt_Pozisyon, vb.).
- Solver performansı: CBC küçük/orta veri setinde hızlı; büyük ligler için HiGHS/Gurobi opsiyonları.
- UI sağlamlığı: selectbox ikon sadeleştirmeleri, bench isim fallback’leri, hata önleyici kontroller.

## 16:00–18:00 | Gelecek Çalışmalar
- Canlı form/sakatlık güncellemeleri (API entegrasyonu).
- Monte Carlo sakatlık simülasyonları, sezon projeksiyonları.
- Maaş tavanı ve transfer bütçesi kısıtları.
- PDF/HTML rapor export, çoklu dil desteği.

## 18:00–20:00 | Kapanış ve Soru-Cevap
- Araç, analistlerin kararını hızlandırıp şeffaflaştırıyor. Soru ve demo taleplerini alın.

## Sunucu Notları (Kısa İpuçları)
- Demo sırasında en az iki senaryo gösterin: bir bütçe artışı ve bir sakatlık simülasyonu.
- Pareto grafiğinde frontier oyuncularını vurgulayın; “niçin frontier?” sorusunu cevaplayın.
- Narrative sekmesinden kısa bir yönetici özeti okuyun; iş değeri vurgusu yapın.
- Zaman yönetimi: Sekme demosu ~5 dk, Q&A için ~2 dk bırakın.
