import cv2
import mss
import numpy as np
import sys
import time

sys.path.append(".")
try:
    from utils import get_game_window_region
except ImportError:
    print("HATA: utils.py bulunamadı.")
    exit()

# --- AYARLANACAK DEĞERLER (Bunlarla oynayacağız) ---
OFFSET_TOP = 5  # Barın tepesinden kaç piksel aşağı inilsin?
SLICE_HEIGHT = 3  # Şerit kaç piksel kalınlığında olsun?
# ---------------------------------------------------

# Daha önceki genişletilmiş bölge ayarı
TEST_REGION = (27, 150, 331, 40)
HP_COLOR_LOW = np.array([0, 50, 50])
HP_COLOR_HIGH = np.array([10, 255, 255])

print("--- SLICE (ŞERİT) AYAR MODU ---")
region = get_game_window_region()
if not region:
    exit()

cv2.namedWindow("Slice Debug", cv2.WINDOW_NORMAL)
cv2.setWindowProperty("Slice Debug", cv2.WND_PROP_TOPMOST, 1)

with mss.mss() as sct:
    while True:
        screen_raw = sct.grab(region)
        full_img = np.array(screen_raw)[:, :, :3]

        # 1. Ana HP Bölgesini Kes
        x, y, w, h = TEST_REGION
        hp_area = full_img[y : y + h, x : x + w]

        if hp_area.size == 0:
            continue

        # 2. Slice (Şerit) Hesapla
        # Şeridin Y koordinatlarını hesapla (hp_area içindeki yerel koordinat)
        slice_y1 = OFFSET_TOP
        slice_y2 = OFFSET_TOP + SLICE_HEIGHT

        # Şeridi kes
        the_slice = hp_area[slice_y1:slice_y2, :]

        # 3. Hesaplama Yap (Botun gördüğü değer)
        hsv = cv2.cvtColor(the_slice, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, HP_COLOR_LOW, HP_COLOR_HIGH)
        white_pixels = cv2.countNonZero(mask)
        total_area = w * SLICE_HEIGHT
        hp_percent = (white_pixels / total_area) * 100 if total_area > 0 else 0

        # 4. GÖRSELLEŞTİRME
        # A) Şeridin yerini SARI ÇİZGİ ile göster
        # Çizgiyi hp_area üzerine çiziyoruz
        debug_img = hp_area.copy()
        cv2.rectangle(debug_img, (0, slice_y1), (w, slice_y2), (0, 255, 255), 1)

        # B) Görüntüyü büyüt ki rahat gör
        debug_img_big = cv2.resize(
            debug_img, (w * 3, h * 3), interpolation=cv2.INTER_NEAREST
        )

        # C) Bilgileri Yaz
        info_text = f"HP: %{hp_percent:.1f}"
        cv2.putText(
            debug_img_big,
            info_text,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )
        cv2.putText(
            debug_img_big,
            f"Offset: {OFFSET_TOP}px",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2,
        )

        cv2.imshow("Slice Debug", debug_img_big)
        cv2.imshow(
            "Maske (Botun Gordugu)",
            cv2.resize(
                mask, (w * 3, SLICE_HEIGHT * 10), interpolation=cv2.INTER_NEAREST
            ),
        )

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

        # KLAVYE İLE AYAR YAPMA:
        # 'w' tuşu şeridi YUKARI taşır (Offset azaltır)
        # 's' tuşu şeridi AŞAĞI taşır (Offset artırır)
        elif key == ord("w"):
            OFFSET_TOP = max(0, OFFSET_TOP - 1)
        elif key == ord("s"):
            OFFSET_TOP = min(h - SLICE_HEIGHT, OFFSET_TOP + 1)

cv2.destroyAllWindows()
print(f"EN SON AYARLANAN OFFSET DEĞERİ: {OFFSET_TOP}")
