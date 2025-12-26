# calibrate_hp_v3.py
import cv2
import mss
import numpy as np
import sys
import time

sys.path.append(".")
try:
    from utils import get_game_window_region
except ImportError:
    print("utils.py bulunamadı.")
    exit()

# --- BAŞLANGIÇ AYARLARI ---
# Botun şu an baktığı yer (Bunu değiştireceğiz)
CURRENT_OFFSET = 18

# Mavi bar gelince ne kadar kaydığı (Bunu da test edebiliriz)
BLUE_SHIFT_AMOUNT = 20

# Renkler
HP_COLOR_LOW = np.array([0, 50, 50])
HP_COLOR_HIGH = np.array([10, 255, 255])
BLUE_LOW = np.array([100, 150, 50])
BLUE_HIGH = np.array([140, 255, 255])
# --------------------------

print("--- HP KALİBRASYON MODU ---")
print("W / S : Yeşil çizgiyi (Kırmızı Bar Yeri) Yukarı/Aşağı taşır.")
print("A / D : Mavi çizgiyi (Kayma Miktarı) Artırır/Azaltır.")
print("Q     : Kaydet ve Çık.")

region = get_game_window_region()
if not region:
    exit()

# Arama bölgesini geniş tutuyoruz
SEARCH_X = 27
SEARCH_Y = 140
SEARCH_W = 331
SEARCH_H = 100

cv2.namedWindow("KALIBRASYON", cv2.WINDOW_NORMAL)
cv2.setWindowProperty("KALIBRASYON", cv2.WND_PROP_TOPMOST, 1)

with mss.mss() as sct:
    while True:
        # Görüntü al
        screen_raw = sct.grab(region)
        full_img = np.array(screen_raw)[:, :, :3]

        # Çalışma alanı
        crop = full_img[SEARCH_Y : SEARCH_Y + SEARCH_H, SEARCH_X : SEARCH_X + SEARCH_W]
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)

        # 1. KIRMIZI BAR (NORMAL) HESABI
        # Yeşil çizginin olduğu yerden 3 piksel al
        y1 = CURRENT_OFFSET
        y2 = CURRENT_OFFSET + 1

        # Taşma kontrolü
        if y2 > SEARCH_H:
            y2 = SEARCH_H

        slice_red = crop[y1:y2, :]
        mask_red = cv2.inRange(
            cv2.cvtColor(slice_red, cv2.COLOR_BGR2HSV), HP_COLOR_LOW, HP_COLOR_HIGH
        )
        red_val = (
            (cv2.countNonZero(mask_red) / (SEARCH_W * 3)) * 100
            if slice_red.size > 0
            else 0
        )

        # 2. MAVİ BAR KONTROLÜ
        # Aynı yerin mavi değerine bak
        mask_blue = cv2.inRange(
            cv2.cvtColor(slice_red, cv2.COLOR_BGR2HSV), BLUE_LOW, BLUE_HIGH
        )
        blue_val = (
            (cv2.countNonZero(mask_blue) / (SEARCH_W * 3)) * 100
            if slice_red.size > 0
            else 0
        )

        # 3. KAYDIRILMIŞ KIRMIZI (Shifted)
        sy1 = CURRENT_OFFSET + BLUE_SHIFT_AMOUNT
        sy2 = sy1 + 3
        shifted_red_val = 0
        if sy2 < SEARCH_H:
            slice_shift = crop[sy1:sy2, :]
            mask_shift = cv2.inRange(
                cv2.cvtColor(slice_shift, cv2.COLOR_BGR2HSV),
                HP_COLOR_LOW,
                HP_COLOR_HIGH,
            )
            shifted_red_val = (cv2.countNonZero(mask_shift) / (SEARCH_W * 3)) * 100

        # --- GÖRSELLEŞTİRME ---
        disp = crop.copy()

        # A) Yeşil Çizgi (Normalde okunan yer)
        cv2.rectangle(disp, (0, y1), (SEARCH_W, y2), (0, 255, 0), 2)

        # B) Sarı Çizgi (Mavi gelirse okunacak yer)
        if sy2 < SEARCH_H:
            cv2.rectangle(disp, (0, sy1), (SEARCH_W, sy2), (0, 255, 255), 2)
            # Ok işareti
            cv2.arrowedLine(
                disp, (SEARCH_W // 2, y2), (SEARCH_W // 2, sy1), (255, 0, 0), 1
            )

        # Yazılar
        info1 = f"NORMAL OKUMA (Yesil): %{red_val:.1f} (Mavi Orani: %{blue_val:.1f})"
        info2 = f"KAYDIRILMIS (Sari)  : %{shifted_red_val:.1f}"
        info3 = f"OFFSET: {CURRENT_OFFSET} | SHIFT: {BLUE_SHIFT_AMOUNT}"

        # Resmi Büyüt
        big_disp = cv2.resize(
            disp, (SEARCH_W * 2, SEARCH_H * 2), interpolation=cv2.INTER_NEAREST
        )

        # Bilgileri ekrana yaz
        cv2.putText(
            big_disp, info1, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2
        )
        cv2.putText(
            big_disp, info2, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2
        )
        cv2.putText(
            big_disp,
            info3,
            (10, 180),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )
        cv2.putText(
            big_disp,
            "W/S: Yesil Cizgiyi Tasi | Q: Kaydet",
            (10, 200),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (200, 200, 200),
            1,
        )

        cv2.imshow("KALIBRASYON", big_disp)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            print(
                f"\n>>> KAYDEDİLECEK DEĞERLER: OFFSET={CURRENT_OFFSET}, SHIFT={BLUE_SHIFT_AMOUNT}"
            )
            break
        elif key == ord("w"):
            CURRENT_OFFSET = max(0, CURRENT_OFFSET - 1)
        elif key == ord("s"):
            CURRENT_OFFSET = min(SEARCH_H - 10, CURRENT_OFFSET + 1)
        elif key == ord("a"):
            BLUE_SHIFT_AMOUNT = max(5, BLUE_SHIFT_AMOUNT - 1)
        elif key == ord("d"):
            BLUE_SHIFT_AMOUNT = min(50, BLUE_SHIFT_AMOUNT + 1)

cv2.destroyAllWindows()
