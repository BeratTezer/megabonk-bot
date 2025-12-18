# fine_tune_regions.py
import cv2
import mss
import numpy as np
import os
import time

# Oyun penceresi bulucu
from utils import get_game_window_region

# --- AYARLAR ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Aranacak Şablonlar Listesi
TARGETS = [
    {
        "var_name": "LEVELUP_REGION",
        "file": "assets/levelup_template.png",
        "color": (0, 255, 0),  # Yeşil
    },
    {
        "var_name": "GAMEOVER_REGION",
        "file": "assets/gameover_template.png",
        "color": (0, 0, 255),  # Kırmızı
    },
    {
        "var_name": "MAP_REGION",
        "file": "assets/map_template.png",
        "color": (0, 0, 0),  # Siyah
    },
]
# ---------------


def load_templates():
    loaded = []
    print("Şablonlar yükleniyor...")
    for target in TARGETS:
        path = os.path.join(SCRIPT_DIR, target["file"])
        img = cv2.imread(path, 0)  # Gri tonlamalı yükle

        if img is None:
            print(f"UYARI: '{target['file']}' bulunamadı! Bu şablon atlanacak.")
            continue

        h, w = img.shape
        loaded.append({"info": target, "image": img, "w": w, "h": h})
        print(f"OK: {target['file']} yüklendi ({w}x{h})")
    return loaded


# Şablonları hafızaya al
active_targets = load_templates()

if not active_targets:
    print("HATA: Hiçbir şablon yüklenemedi. Dosya adlarını kontrol edin.")
    exit()

print("\n--- FINE TUNE ARACI BAŞLATILIYOR ---")
print("1. Oyunu açın.")
print("2. İlgili ekranları (Level Up, Game Over vb.) açın.")
print("3. Terminale düşen koordinat satırını kopyalayıp 'get_infos.py'ye yapıştırın.")
print("--------------------------------------")
time.sleep(2)

region = get_game_window_region()
if not region:
    print("HATA: Oyun penceresi bulunamadı!")
    exit()

cv2.namedWindow("Fine Tune (Kapatmak icin 'q')", cv2.WINDOW_NORMAL)

# --- YENİ: Mükemmel bulunanları takip etmek için küme ---
found_targets = set()
# -------------------------------------------------------

with mss.mss() as sct:
    while True:
        # 1. Ekranı al
        screen_raw = sct.grab(region)
        screen_bgr = np.array(screen_raw)[:, :, :3].copy()
        screen_gray = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2GRAY)

        # 2. TÜM ŞABLONLARI DÖNGÜYLE ARA
        for target in active_targets:
            template_img = target["image"]
            w, h = target["w"], target["h"]
            var_name = target["info"]["var_name"]
            color = target["info"]["color"]

            # Eşleştirme yap
            res = cv2.matchTemplate(screen_gray, template_img, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

            # Eşik Değeri (Ekrana çizmek için %80 yeterli)
            if max_val > 0.80:

                top_left = max_loc
                bottom_right = (top_left[0] + w, top_left[1] + h)

                # Çizim yap (Her zaman çizmeye devam et ki yerini gör)
                cv2.rectangle(screen_bgr, top_left, bottom_right, color, 2)

                # Mükemmel Koordinatları Hesapla
                margin = 10
                safe_x = max(0, top_left[0] - margin)
                safe_y = max(0, top_left[1] - margin)
                safe_w = w + (margin * 2)
                safe_h = h + (margin * 2)

                # Ekrana Bilgi Yaz
                label = f"{var_name} ({max_val:.2f})"
                cv2.putText(
                    screen_bgr,
                    label,
                    (safe_x, safe_y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    color,
                    2,
                )

                # --- DEĞİŞİKLİK: Sadece daha önce bulunmamışsa yazdır ---
                if var_name not in found_targets:

                    # Eğer skor %99 üzerindeyse "Mükemmel" kabul et ve kilitle
                    if max_val >= 0.99:
                        print(
                            f">> {var_name} = ({safe_x}, {safe_y}, {safe_w}, {safe_h})  [Skor: {max_val:.4f}]  <-- TAM EŞLEŞME (Print Kilitlendi)"
                        )
                        found_targets.add(var_name)  # Listeye ekle, bir daha yazdırma

                    # Henüz mükemmel değilse (%90-%99 arası) yazdırmaya devam et (ayar yapıyorsun demektir)
                    elif max_val > 0.90:
                        print(
                            f">> {var_name} = ({safe_x}, {safe_y}, {safe_w}, {safe_h})  [Skor: {max_val:.3f}]"
                        )
                # -------------------------------------------------------

        # Görüntüle
        cv2.imshow("Fine Tune (Kapatmak icin 'q')", screen_bgr)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

cv2.destroyAllWindows()
