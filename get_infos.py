import cv2
import numpy as np
import os
import glob  # <-- Klasör taramak için eklendi

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# --- SİZİN DÜZENLEMENİZ GEREKEN AYARLAR ---
# 1. Sağlık Çubuğu Bölgesi
HP_SEARCH_REGION = (27, 140, 331, 100)

# 2. Renk Ayarları
HP_COLOR_LOW = np.array([0, 50, 50])  # Kırmızı (Can)
HP_COLOR_HIGH = np.array([10, 255, 255])

BLUE_COLOR_LOW = np.array([100, 150, 50])  # Mavi (Mana/Kalkan)
BLUE_COLOR_HIGH = np.array([140, 255, 255])

# --- BÖLGESEL ARAMA AYARLARI ---
LEVELUP_REGION = (823, 313, 373, 50)
GAMEOVER_REGION = (1123, 176, 310, 94)

# SİZİN BULDUĞUNUZ KOORDİNATLAR
LEVELUP_OPTIONS = [
    (885, 490, 140, 140),  # 1. Seçenek
    (900, 720, 135, 130),  # 2. Seçenek
    (900, 945, 135, 135),  # 3. Seçenek
]

# Şablon Eşleştirme Eşiği
TEMPLATE_THRESHOLD = 0.6


class InfoExtractor:
    def __init__(self):
        # 1. Normal Şablonları Yükle
        levelup_path = os.path.join(SCRIPT_DIR, "assets/levelup_template.png")
        gameover_path = os.path.join(SCRIPT_DIR, "assets/gameover_template.png")

        self.levelup_template = self._load_template(levelup_path)
        self.gameover_template = self._load_template(gameover_path)

        # 2. İTEM ŞABLONLARINI YÜKLE (Maskeli Yükleme)
        self.item_templates = {}
        items_dir = os.path.join(SCRIPT_DIR, "assets/good_items")

        # Klasördeki tüm PNG'leri bul
        for file_path in glob.glob(os.path.join(items_dir, "*.png")):
            filename = os.path.basename(file_path)
            item_name = os.path.splitext(filename)[0]  # "katana.png" -> "katana"

            # Şeffaflık (Alpha) kanalıyla birlikte yükle
            img_bgra = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)

            if img_bgra is not None:
                # Eğer resim 4 kanallıysa (Şeffaflık varsa) maske oluştur
                if img_bgra.shape[2] == 4:
                    bgr = img_bgra[:, :, :3]
                    mask = img_bgra[:, :, 3]  # Alpha kanalı
                    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

                    self.item_templates[item_name] = {"img": gray, "mask": mask}
                    print(f"İtem Yüklendi (Maskeli): {item_name}")
                else:
                    # Maske yoksa düz yükle
                    gray = cv2.cvtColor(img_bgra, cv2.COLOR_BGR2GRAY)
                    self.item_templates[item_name] = {"img": gray, "mask": None}
                    print(f"İtem Yüklendi (Normal): {item_name}")
            else:
                print(f"UYARI: {filename} okunamadı!")

    def _load_template(self, path):
        template = cv2.imread(path, 0)
        if template is None:
            print(f"UYARI (InfoExtractor): '{path}' şablonu bulunamadı.")
        return template

    def _check_template(self, gray_image_region, template):
        if template is None:
            return False
        try:
            res = cv2.matchTemplate(gray_image_region, template, cv2.TM_CCOEFF_NORMED)
            _, maxVal, _, _ = cv2.minMaxLoc(res)
            return maxVal >= TEMPLATE_THRESHOLD
        except:
            return False

    def _get_current_hp(self, raw_bgr_image):
        try:
            x_s, y_s, w_s, h_s = HP_SEARCH_REGION

            # --- KULLANICI AYARLARI ---
            STANDARD_OFFSET = 1
            BLUE_SHIFT = 37
            SLICE_HEIGHT = 3
            # --------------------------

            # 1. ADIM: Standart konumu kontrol et (Mavi var mı?)
            check_y = y_s + STANDARD_OFFSET

            if check_y + SLICE_HEIGHT > raw_bgr_image.shape[0]:
                return -1.0

            check_slice = raw_bgr_image[
                check_y : check_y + SLICE_HEIGHT, x_s : x_s + w_s
            ]
            hsv_check = cv2.cvtColor(check_slice, cv2.COLOR_BGR2HSV)

            mask_blue = cv2.inRange(hsv_check, BLUE_COLOR_LOW, BLUE_COLOR_HIGH)
            blue_ratio = cv2.countNonZero(mask_blue) / (w_s * SLICE_HEIGHT)

            # 2. ADIM: Ofseti Belirle
            current_offset = STANDARD_OFFSET

            # Eğer şeridin %40'ından fazlası maviyse, bar kaymıştır.
            if blue_ratio > 0.40:
                current_offset = STANDARD_OFFSET + BLUE_SHIFT

            # 3. ADIM: Kırmızı Canı Oku
            read_y = y_s + current_offset

            if read_y + SLICE_HEIGHT > raw_bgr_image.shape[0]:
                return 0.0

            read_slice = raw_bgr_image[read_y : read_y + SLICE_HEIGHT, x_s : x_s + w_s]
            hsv_read = cv2.cvtColor(read_slice, cv2.COLOR_BGR2HSV)

            mask_red = cv2.inRange(hsv_read, HP_COLOR_LOW, HP_COLOR_HIGH)
            white_pixels = cv2.countNonZero(mask_red)
            total_area = w_s * SLICE_HEIGHT

            if total_area == 0:
                return 0.0

            hp_percentage = (white_pixels / total_area) * 100

            # Gürültü filtresi
            return hp_percentage if hp_percentage > 2 else 0.0

        except Exception:
            return -1.0

    # --- YENİ: LEVEL UP EKRANINI TARA ---
    def scan_levelup_screen(self, raw_bgr_image):
        """
        Level Up ekranındaki 3 kutuyu tarar.
        Dönüş Örneği: ['katana', None, 'xp_tome'] (None = Tanınmayan item)
        """
        gray_screen = cv2.cvtColor(raw_bgr_image, cv2.COLOR_BGR2GRAY)
        results = []

        # Her bir kutu için (Koordinatları LEVELUP_OPTIONS'dan al)
        for i, (x, y, w, h) in enumerate(LEVELUP_OPTIONS):
            # Güvenlik: Resim sınırlarını aşma
            if y + h > gray_screen.shape[0] or x + w > gray_screen.shape[1]:
                results.append(None)
                continue

            # Kutuyu Kes
            slot_crop = gray_screen[y : y + h, x : x + w]

            found_item_name = None
            best_score = 0.0

            # Bu kutuda bildiğimiz itemlerden biri var mı?
            for name, data in self.item_templates.items():
                template = data["img"]
                mask = data["mask"]

                try:
                    # Şablon kutudan büyükse atla
                    if (
                        template.shape[0] > slot_crop.shape[0]
                        or template.shape[1] > slot_crop.shape[1]
                    ):
                        continue

                    # Maskeli Eşleştirme Yap
                    if mask is not None:
                        res = cv2.matchTemplate(
                            slot_crop, template, cv2.TM_CCOEFF_NORMED, mask=mask
                        )
                    else:
                        res = cv2.matchTemplate(
                            slot_crop, template, cv2.TM_CCOEFF_NORMED
                        )

                    _, max_val, _, _ = cv2.minMaxLoc(res)

                    # Eşik değerini geçen en yüksek skoru kaydet
                    if max_val > 0.75 and max_val > best_score:
                        best_score = max_val
                        found_item_name = name
                except Exception:
                    pass

            results.append(found_item_name)

        return results

    def extract_game_state(self, raw_bgr_image):
        current_hp = self._get_current_hp(raw_bgr_image)

        # Optimize edilmiş Level Up Kontrolü
        try:
            x, y, w, h = LEVELUP_REGION
            lvl_crop = raw_bgr_image[y : y + h, x : x + w]
            lvl_gray = cv2.cvtColor(lvl_crop, cv2.COLOR_BGR2GRAY)
        except:
            lvl_gray = cv2.cvtColor(raw_bgr_image, cv2.COLOR_BGR2GRAY)

        # Optimize edilmiş Game Over Kontrolü
        try:
            x, y, w, h = GAMEOVER_REGION
            go_crop = raw_bgr_image[y : y + h, x : x + w]
            go_gray = cv2.cvtColor(go_crop, cv2.COLOR_BGR2GRAY)
        except:
            go_gray = cv2.cvtColor(raw_bgr_image, cv2.COLOR_BGR2GRAY)

        return {
            "current_hp": current_hp,
            "is_level_up": self._check_template(lvl_gray, self.levelup_template),
            "is_game_over": self._check_template(go_gray, self.gameover_template),
        }
