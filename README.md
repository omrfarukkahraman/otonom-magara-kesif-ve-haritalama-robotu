# Otonom Mağara Keşif ve Haritalama Robotu Simülasyonu

Bu proje, **Necmettin Erbakan Üniversitesi Bilgisayar Mühendisliği Bölümü - Robotik Dersi** kapsamında geliştirilmiş bir otonom keşif ve haritalama (SLAM - Eşzamanlı Konumlandırma ve Haritalama) robotu simülasyonudur.

* **Öğrenci Adı:** Ömer Faruk Kahraman
* **Öğrenci Numarası:** 21370031058

---

## 🌟 Proje Özellikleri

1. **Hücresel Otomat (Cellular Automata) ile Organik Mağara Üretimi:** 
   Simülasyon her başlatıldığında veya sıfırlandığında, gerçek mağara yapılarına benzer dar geçitler, geniş odalar ve doğal engeller içeren tamamen rastgele ve organik bir mağara haritası üretilir. Bağlantısız (erişilemeyen) odacıklar otomatik olarak tespit edilir ve doldurulur; böylece robotun kapalı küçük alanlarda sıkışması önlenir.

2. **Gelişmiş LiDAR Sensör Simülasyonu:**
   Robotun üzerinde 360 derecelik alanı tarayan **36 adet bağımsız LiDAR (lazer ışını)** bulunur. Her ışın, mağaranın gerçek sınırlarını tarayarak mesafe ölçümü gerçekleştirir.

3. **Eşzamanlı Haritalama (SLAM Grid):**
   Robot, LiDAR sensöründen aldığı verileri kullanarak kendi zihnindeki haritayı gerçek zamanlı olarak oluşturur. Robotun görüş hattındaki boş alanlar haritada beyaz olarak işaretlenirken, çarpan lazer uç noktaları kırmızı renkte birer engel/duvar olarak robotun harita belleğine kaydedilir (SLAM Izgarası).

4. **Otonom Yönlenme ve Keşif Algoritması:**
   Robot, önünde bir engel algıladığında en geniş boş alana doğru (sağ veya sol sensör ortalamasına göre) otonom olarak yön değiştirir. Robot, bir odada kısır döngüye girmemek için **keşfedilmemiş alanları (siyah/lacivert sis bulutunu) analiz eder** ve lazer tarama doğrultusundaki keşfedilmemiş hücrelerin en yoğun olduğu yöne doğru hafif bir yönelim kuvveti uygular.

5. **Sıkışma Algılama ve Geri Çekilme (Recovery):**
   Robot dar geçitlerde veya köşelerde hareket edemez hale gelirse (sıkışma dedektörü), otomatik olarak `"GERI CEKILME"` moduna geçer; geriye doğru gidip kendi etrafında dönerek çıkış yolunu arar.

6. **İnteraktif Kontrol ve Veri Gösterge Paneli:**
   Simülasyonun sağ tarafında robotun anlık hızı, açısı, pil seviyesi, koordinatları ve mağaranın yüzde kaçının başarıyla keşfedildiğini gösteren bir **dashboard** yer alır.

---

## 🛠️ Gereksinimler ve Kurulum

Simülasyonu çalıştırmak için sisteminizde **Python 3** ve **Pygame** kütüphanesinin kurulu olması gerekmektedir.

### Pygame Kurulumu:
Konsol veya terminal üzerinden aşağıdaki komutla gerekli kütüphaneyi kurun:
```bash
pip install pygame
```

---

## 🚀 Simülasyonu Çalıştırma

Proje klasörünün içerisindeyken aşağıdaki komutu çalıştırarak simülasyonu başlatabilirsiniz:
```bash
python otonom_magara_robotu.py
```

---

## ⌨️ Simülasyon Kontrolleri (Klavye Kılavuzu)

| Tuş | Açıklama |
|---|---|
| **`[SPACE]`** | Simülasyonu Duraklatır veya kaldığı yerden devam ettirir. |
| **`[M]`** | **Otonom** ve **Manuel** sürüş modları arasında geçiş yapar. |
| **`[V]`** | Haritadaki kırmızı çizgiyle gösterilen **Gerçek Mağara Sınırlarını** gösterir veya gizler. |
| **`[R]`** | Mağara haritasını tamamen sıfırdan üretir, robotu başlangıç konumuna alır ve harita hafızasını temizler. |
| **`[C]`** | Robotun bataryasını anında doldurur (%100). |
| **`[YÖN / WASD]`** | **Manuel Moddayken** robotu manuel olarak sürmenizi sağlar. (İleri, geri, sağa/sola dönüş). |

---

## 🎥 Tanıtım ve Demo Videosu

Simülasyonun çalışmasını gösteren örnek ekran kaydına, proje klasöründeki şu video dosyasından ulaşabilirsiniz:
* `NEÜ Robotik - Otonom Mağara Robotu Simülasyonu (21370031058) 2026-06-01 15-36-12.mp4`

---
*Bu proje akademik değerlendirme amacıyla hazırlanmıştır.*
