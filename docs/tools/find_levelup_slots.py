# find_levelup_slots.py
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

print("--- LEVEL UP SEÇENEK BULUCU ---")
print("1, 2, 3 : Hangi kutuyu düzenleyeceğini seç.")
print("W/A/S/D : Kutuyu Hareket Ettir (Yukarı/Sol/Aşağı/Sağ)")
print("I/J/K/L : Kutuyu Büyüt/Küçült (Genişlik/Yükseklik)")
print("Q       : Kaydet ve Çık")

region = get_game_window_region()
if not region:
    exit()

# Varsayılan Başlangıç Değerleri (Tahmini)
# Bunları ekrandaki yerlerine göre kaydıracaksınız.
slots = [
    {"x": 800, "y": 400, "w": 300, "h": 80},  # 1. Seçenek
    {"x": 800, "y": 550, "w": 300, "h": 80},  # 2. Seçenek
    {"x": 800, "y": 700, "w": 300, "h": 80},  # 3. Seçenek
    # İsterseniz 4. seçeneği de buraya ekleyebilirsiniz.
]

current_slot_idx = 0  # Şu an düzenlediğimiz kutu (0 = 1. kutu)
move_speed = 5

cv2.namedWindow("LevelUp Ayari", cv2.WINDOW_NORMAL)
cv2.setWindowProperty("LevelUp Ayari", cv2.WND_PROP_TOPMOST, 1)

with mss.mss() as sct:
    while True:
        # Ekranı al
        screen_raw = sct.grab(region)
        full_img = np.array(screen_raw)[:, :, :3]

        display = full_img.copy()

        # Kutuları Çiz
        for i, s in enumerate(slots):
            color = (0, 255, 0) if i == current_slot_idx else (0, 0, 255)
            thickness = 3 if i == current_slot_idx else 1

            x, y, w, h = s["x"], s["y"], s["w"], s["h"]

            cv2.rectangle(display, (x, y), (x + w, y + h), color, thickness)
            cv2.putText(
                display,
                f"SECENEK {i+1}",
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                color,
                2,
            )

        # Bilgi Yazısı
        info = f"DUZENLENEN: SECENEK {current_slot_idx+1}"
        cv2.putText(
            display, info, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2
        )

        # Göster (Biraz küçültelim ki ekrana sığsın)
        h_scr, w_scr = display.shape[:2]
        display_small = cv2.resize(display, (w_scr // 2, h_scr // 2))
        cv2.imshow("LevelUp Ayari", display_small)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            print("\n--- KAYDEDİLECEK KOORDİNATLAR ---")
            print("Lütfen bu listeyi kopyalayıp get_infos.py dosyasına yapıştırın:")
            print("-" * 30)
            print("LEVELUP_OPTIONS = [")
            for s in slots:
                print(f"    ({s['x']}, {s['y']}, {s['w']}, {s['h']}),")
            print("]")
            print("-" * 30)
            break

        # Kutu Seçimi
        elif key == ord("1"):
            current_slot_idx = 0
        elif key == ord("2"):
            current_slot_idx = 1
        elif key == ord("3"):
            current_slot_idx = 2

        # Hareket
        elif key == ord("w"):
            slots[current_slot_idx]["y"] -= move_speed
        elif key == ord("s"):
            slots[current_slot_idx]["y"] += move_speed
        elif key == ord("a"):
            slots[current_slot_idx]["x"] -= move_speed
        elif key == ord("d"):
            slots[current_slot_idx]["x"] += move_speed

        # Boyutlandırma
        elif key == ord("l"):
            slots[current_slot_idx]["w"] += move_speed  # Genişlet
        elif key == ord("j"):
            slots[current_slot_idx]["w"] -= move_speed  # Daralt
        elif key == ord("k"):
            slots[current_slot_idx]["h"] += move_speed  # Uzat
        elif key == ord("i"):
            slots[current_slot_idx]["h"] -= move_speed  # Kısalt

cv2.destroyAllWindows()
