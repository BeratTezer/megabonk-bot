# debug_live_regions.py
import cv2
import mss
import numpy as np
import time
import pyautogui  # Ekran boyutunu almak için

# Ayarları ve araçları import et
from utils import get_game_window_region
from get_infos import (
    InfoExtractor,
    HP_SEARCH_REGION,
    LEVELUP_REGION,
    GAMEOVER_REGION,
)

print("Canlı Hata Ayıklama Aracı Başlatılıyor...")
print("Lütfen oyun penceresinin ekranda olduğundan emin olun.")
print("Kapatmak için 'q' tuşuna basın.")
time.sleep(3)

# --- DEĞİŞİKLİK: Pencereyi döngüden ÖNCE bir kez bul ---
region = get_game_window_region()
if not region:
    print(
        "HATA: Oyun penceresi bulunamadı. Lütfen config.py dosyasını ve oyunun açık olduğunu kontrol edin."
    )
    exit()  # Döngüye hiç girme
# ---

# Gözleri (Extractor) başlat
extractor = InfoExtractor()

# Pencereyi oluştur ve konumlandır
cv2.namedWindow("Canli Hata Ayiklama (DEBUG)", cv2.WINDOW_NORMAL)
try:
    screen_width, screen_height = pyautogui.size()
    cv2.moveWindow(
        "Canli Hata Ayiklama (DEBUG)", screen_width - 650, screen_height - 420
    )
    cv2.resizeWindow("Canli Hata Ayiklama (DEBUG)", 640, 360)
    cv2.setWindowProperty("Canli Hata Ayiklama (DEBUG)", cv2.WND_PROP_TOPMOST, 1)
except Exception:
    pass

# Canlı döngüyü başlat
with mss.mss() as sct:
    while True:
        # --- DEĞİŞİKLİK: 'region = ...' komutu buradan kaldırıldı ---
        # Artık döngü içinde sürekli pencere aramıyoruz.

        # 1. Oyun penceresini yakala (Artık bulunan 'region'ı kullan)
        screen_raw = sct.grab(region)
        img = np.array(screen_raw)[:, :, :3].copy()

        # 2. Görüntüyü analiz et (HIZLI ANALİZ)
        gray_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        try:
            x, y, w, h = LEVELUP_REGION
            levelup_search_area = gray_image[y : y + h, x : x + w]
        except Exception:
            levelup_search_area = gray_image

        try:
            x, y, w, h = GAMEOVER_REGION
            gameover_search_area = gray_image[y : y + h, x : x + w]
        except Exception:
            gameover_search_area = gray_image

        # 3. Eşleşme skorlarını CANLI olarak hesapla
        try:
            res = cv2.matchTemplate(
                levelup_search_area, extractor.levelup_template, cv2.TM_CCOEFF_NORMED
            )
            _minVal, lvl_maxVal, _minLoc, _maxLoc = cv2.minMaxLoc(res)
        except Exception:
            lvl_maxVal = 0.0

        try:
            res = cv2.matchTemplate(
                gameover_search_area, extractor.gameover_template, cv2.TM_CCOEFF_NORMED
            )
            _minVal, go_maxVal, _minLoc, _maxLoc = cv2.minMaxLoc(res)
        except Exception:
            go_maxVal = 0.0

        # 4. Bölgeleri ve Skorları Çiz
        color_box = (0, 0, 255)  # Kırmızı

        # Level Up Bölgesi
        x, y, w, h = LEVELUP_REGION
        cv2.rectangle(img, (x, y), (x + w, y + h), color_box, 2)
        lvl_text = f"LevelUp Eslesme: {lvl_maxVal:.2f}"
        cv2.putText(
            img, lvl_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2
        )

        # Game Over Bölgesi
        x, y, w, h = GAMEOVER_REGION
        cv2.rectangle(img, (x, y), (x + w, y + h), color_box, 2)
        go_text = f"GameOver Eslesme: {go_maxVal:.2f}"
        cv2.putText(
            img, go_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2
        )

        # HP Bölgesi (Sadece çizim)
        x, y, w, h = HP_SEARCH_REGION
        cv2.rectangle(img, (x, y), (x + w, y + h), color_box, 2)

        # 5. Görüntüyü küçült ve göster
        display_img_resized = cv2.resize(img, (640, 360))
        cv2.imshow("Canli Hata Ayiklama (DEBUG)", display_img_resized)

        # Çıkış için 'q' tuşu
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

cv2.destroyAllWindows()
