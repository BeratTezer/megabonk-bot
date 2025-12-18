# debug_regions.py
import cv2
import mss
import numpy as np
import time

# Ayarları ve araçları import et
from utils import get_game_window_region

# --- DEĞİŞİKLİK: MAP_REGION eklendi ---
from get_infos import (
    InfoExtractor,
    HP_SEARCH_REGION,
    LEVELUP_REGION,
    GAMEOVER_REGION,
    MAP_REGION,
)

# ---

print("Hata Ayıklama Aracı Başlatılıyor...")
print("5 saniye içinde oyun pencerenizin ekran görüntüsü alınacak.")
print("Lütfen oyun penceresinin ekranda olduğundan emin olun.")
time.sleep(3)

# 1. Oyun penceresinin koordinatlarını al
region = get_game_window_region()
if not region:
    print("HATA: Oyun penceresi bulunamadı. config.py dosyasını kontrol edin.")
    exit()

# 2. Ekran görüntüsü al
with mss.mss() as sct:
    screen_raw = sct.grab(region)
    # Görüntüyü OpenCV formatına çevir (BGRA -> BGR) ve kopyala
    img = np.array(screen_raw)[:, :, :3].copy()

print("Ekran görüntüsü alındı. Bölgeler analiz ediliyor ve çiziliyor...")

# --- InfoExtractor'ı çalıştır ---
try:
    extractor = InfoExtractor()
    game_state = extractor.extract_game_state(img)

    # Okunan değerleri al
    hp_value = game_state.get("current_hp")
    levelup_value = game_state.get("is_level_up")
    gameover_value = game_state.get("is_game_over")

    print(f"--- OKUNAN DEGERLER ---")
    print(f"HP: {hp_value}")
    print(f"Level Up: {levelup_value}")
    print(f"Game Over: {gameover_value}")
    print(f"-------------------------")

except Exception as e:
    print(f"HATA: InfoExtractor çalışırken bir hata oluştu: {e}")
    hp_value = "HATA"
    levelup_value = "HATA"
    gameover_value = "HATA"


# 3. Bölgeleri Kırmızı Karelerle Çiz ve Değerleri Yaz
color_box = (0, 0, 255)  # Kırmızı (Kare)
color_text = (0, 255, 0)  # Yeşil (Metin)
thickness = 2

# --- HP ARAMA BÖLGESİ ---
try:
    x, y, w, h = HP_SEARCH_REGION
    cv2.rectangle(img, (x, y), (x + w, y + h), color_box, thickness)

    if hp_value == -1.0:
        hp_text = "HP: Bulunamadi"
    elif isinstance(hp_value, float):
        hp_text = f"HP: {hp_value:.1f}%"
    else:
        hp_text = f"HP: {hp_value}"

    cv2.putText(img, hp_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_text, 2)
    cv2.putText(
        img,
        "(HP Arama Alani)",
        (x, y + h + 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 255),
        1,
    )
except Exception as e:
    print(f"HP_SEARCH_REGION çizilemedi: {e}")

# --- Level Up Bölgesi ---
try:
    x, y, w, h = LEVELUP_REGION
    cv2.rectangle(img, (x, y), (x + w, y + h), color_box, thickness)
    levelup_text = f"LevelUp: {levelup_value}"
    cv2.putText(
        img, levelup_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_text, 2
    )
except Exception as e:
    print(f"LEVELUP_REGION çizilemedi: {e}")

# --- Game Over Bölgesi ---
try:
    x, y, w, h = GAMEOVER_REGION
    cv2.rectangle(img, (x, y), (x + w, y + h), color_box, thickness)
    gameover_text = f"GameOver: {gameover_value}"
    cv2.putText(
        img, gameover_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_text, 2
    )
except Exception as e:
    print(f"GAMEOVER_REGION çizilemedi: {e}")

# --- YENİ EKLENEN: MAP Bölgesi ---
try:
    x, y, w, h = MAP_REGION
    # Harita için farklı bir renk kullanalım (Camgöbeği/Cyan)
    map_color = (255, 255, 0)
    cv2.rectangle(img, (x, y), (x + w, y + h), map_color, thickness)
    cv2.putText(
        img, "MAP Bolgesi", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, map_color, 2
    )
except Exception as e:
    print(f"MAP_REGION çizilemedi: {e}")
# ---------------------------------

# 4. Sonucu göster
print("Çizim tamamlandı. Görüntü gösteriliyor. Kapatmak için bir tuşa basın.")
cv2.imshow("Bolge Hata Ayiklama (DEBUG)", img)
cv2.waitKey(0)  # Bir tuşa basana kadar bekle
cv2.destroyAllWindows()
