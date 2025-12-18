import cv2
import numpy as np
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# --- SİZİN DÜZENLEMENİZ GEREKEN AYARLAR ---
# 1. Sağlık Çubuğu Bölgesi (x, y, w, h)
HP_SEARCH_REGION = (27, 162, 331, 1)

# 2. Sağlık Çubuğu Rengi (HSV formatında)
HP_COLOR_LOW = np.array([0, 120, 70])
HP_COLOR_HIGH = np.array([10, 255, 255])

# 3. HP Barının minimum genişliği (piksel olarak)
MIN_HP_BAR_WIDTH = 1

# 4. OKUMA DİLİMİ
HP_SLICE_OFFSET_Y = 2
HP_SLICE_HEIGHT = 5

# --- BÖLGESEL ARAMA AYARLARI ---
LEVELUP_REGION = (823, 313, 373, 50)
GAMEOVER_REGION = (1123, 176, 310, 94)

# "time": current_time
GAMEPLAYTIME_REGION = (69, 52, 168, 64)
# "gold": current_gold
GOLD_REGION = (497, 57, 172, 51)
# "kills": current_kills
KILLSCORE_REGION = (711, 57, 242, 51)
# "current_box_cost": current_box_cost
BOXPRICE_REGION = (2145, 61, 219, 51)
# "level": current_level
LEVEL_REGION = (2318, 57, 210, 63)
# "current_guns": current_guns
GUNS_REGION = (23, 179, 351, 87)
# "current_tomes": current_tomes
TOMES_REGION = (23, 270, 351, 87)
# "map": map_data
MAP_KEY = "TAB"
MAP_REGION = (0, 319, 1089, 1096)
# ---

# 3. Şablon Eşleştirme Eşiği
TEMPLATE_THRESHOLD = 0.6


class InfoExtractor:
    def __init__(self):
        levelup_path = os.path.join(SCRIPT_DIR, "assets/levelup_template.png")
        gameover_path = os.path.join(SCRIPT_DIR, "assets/gameover_template.png")

        self.levelup_template = self._load_template(levelup_path)
        self.gameover_template = self._load_template(gameover_path)

    def _load_template(self, path):
        template = cv2.imread(path, 0)
        if template is None:
            print(f"UYARI (InfoExtractor): '{path}' şablonu bulunamadı veya okunamadı.")
        return template

    def _check_template(self, gray_image_region, template):
        if template is None:
            return False
        try:
            if (
                template.shape[0] > gray_image_region.shape[0]
                or template.shape[1] > gray_image_region.shape[1]
            ):
                return False
        except Exception:
            return False

        try:
            res = cv2.matchTemplate(gray_image_region, template, cv2.TM_CCOEFF_NORMED)
            _minVal, maxVal, _minLoc, _maxLoc = cv2.minMaxLoc(res)

            if maxVal >= TEMPLATE_THRESHOLD:
                return True
        except cv2.error:
            return False

        return False

    def _get_current_hp(self, raw_bgr_image):
        try:
            x_s, y_s, w_s, h_s = HP_SEARCH_REGION
            search_crop = raw_bgr_image[y_s : y_s + h_s, x_s : x_s + w_s]

            hsv_crop = cv2.cvtColor(search_crop, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv_crop, HP_COLOR_LOW, HP_COLOR_HIGH)

            bar_y = -1
            for y in range(h_s):
                row = mask[y, :]
                red_pixel_count = cv2.countNonZero(row)

                if red_pixel_count > MIN_HP_BAR_WIDTH:
                    bar_y = y
                    break

            if bar_y == -1:
                return -1.0

            slice_y_start = bar_y + HP_SLICE_OFFSET_Y
            slice_y_end = slice_y_start + HP_SLICE_HEIGHT

            bar_full_slice_bgr = search_crop[slice_y_start:slice_y_end, :]

            bar_slice_hsv = cv2.cvtColor(bar_full_slice_bgr, cv2.COLOR_BGR2HSV)
            hp_mask = cv2.inRange(bar_slice_hsv, HP_COLOR_LOW, HP_COLOR_HIGH)
            hp_pixels = cv2.countNonZero(hp_mask)

            total_pixels_in_slice = (
                bar_full_slice_bgr.shape[0] * bar_full_slice_bgr.shape[1]
            )

            if total_pixels_in_slice == 0:
                return 0.0

            EMPTY_BAR_LOW = np.array([0, 0, 20])
            EMPTY_BAR_HIGH = np.array([180, 50, 80])

            empty_mask = cv2.inRange(bar_slice_hsv, EMPTY_BAR_LOW, EMPTY_BAR_HIGH)
            empty_pixels = cv2.countNonZero(empty_mask)

            total_bar_pixels = hp_pixels + empty_pixels

            if total_bar_pixels < hp_pixels:
                total_bar_pixels = total_pixels_in_slice

            if total_bar_pixels == 0:
                return 0.0

            hp_percentage = (hp_pixels / total_bar_pixels) * 100

            return hp_percentage

        except Exception as e:
            return -1.0

    def extract_game_state(self, raw_bgr_image):
        gray_image = cv2.cvtColor(raw_bgr_image, cv2.COLOR_BGR2GRAY)
        current_hp = self._get_current_hp(raw_bgr_image)

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

        is_level_up = self._check_template(levelup_search_area, self.levelup_template)
        is_game_over = self._check_template(
            gameover_search_area, self.gameover_template
        )

        game_state = {
            "current_hp": current_hp,
            "is_level_up": is_level_up,
            "is_game_over": is_game_over,
        }

        return game_state
