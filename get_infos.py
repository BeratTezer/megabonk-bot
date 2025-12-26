import cv2
import numpy as np
import os
import glob
from config import (
    HP_SEARCH_REGION,
    BLUE_COLOR_LOW,
    BLUE_COLOR_HIGH,
    HP_COLOR_LOW,
    HP_COLOR_HIGH,
    TEMPLATE_THRESHOLD,
    STANDARD_OFFSET,
    BLUE_SHIFT,
    SLICE_HEIGHT,
    LEVELUP_OPTIONS,
    LEVELUP_REGION,
    GAMEOVER_REGION,
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


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

            check_y = y_s + STANDARD_OFFSET

            if check_y + SLICE_HEIGHT > raw_bgr_image.shape[0]:
                return -1.0

            check_slice = raw_bgr_image[
                check_y : check_y + SLICE_HEIGHT, x_s : x_s + w_s
            ]
            hsv_check = cv2.cvtColor(check_slice, cv2.COLOR_BGR2HSV)

            mask_blue = cv2.inRange(hsv_check, BLUE_COLOR_LOW, BLUE_COLOR_HIGH)
            blue_ratio = cv2.countNonZero(mask_blue) / (w_s * SLICE_HEIGHT)

            current_offset = STANDARD_OFFSET

            if blue_ratio > 0.40:
                current_offset = STANDARD_OFFSET + BLUE_SHIFT

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

            return hp_percentage if hp_percentage > 2 else 0.0

        except Exception:
            return -1.0

    def scan_levelup_screen(self, raw_bgr_image):
        gray_screen = cv2.cvtColor(raw_bgr_image, cv2.COLOR_BGR2GRAY)
        results = []

        for i, (x, y, w, h) in enumerate(LEVELUP_OPTIONS):
            if y + h > gray_screen.shape[0] or x + w > gray_screen.shape[1]:
                results.append(None)
                continue

            slot_crop = gray_screen[y : y + h, x : x + w]

            found_item_name = None
            best_score = 0.0

            for name, data in self.item_templates.items():
                template = data["img"]
                mask = data["mask"]

                try:
                    if (
                        template.shape[0] > slot_crop.shape[0]
                        or template.shape[1] > slot_crop.shape[1]
                    ):
                        continue

                    if mask is not None:
                        res = cv2.matchTemplate(
                            slot_crop, template, cv2.TM_CCOEFF_NORMED, mask=mask
                        )
                    else:
                        res = cv2.matchTemplate(
                            slot_crop, template, cv2.TM_CCOEFF_NORMED
                        )

                    _, max_val, _, _ = cv2.minMaxLoc(res)

                    if max_val > 0.75 and max_val > best_score:
                        best_score = max_val
                        found_item_name = name
                except Exception:
                    pass

            results.append(found_item_name)

        return results

    def extract_game_state(self, raw_bgr_image):
        current_hp = self._get_current_hp(raw_bgr_image)

        try:
            x, y, w, h = LEVELUP_REGION
            lvl_crop = raw_bgr_image[y : y + h, x : x + w]
            lvl_gray = cv2.cvtColor(lvl_crop, cv2.COLOR_BGR2GRAY)
        except:
            lvl_gray = cv2.cvtColor(raw_bgr_image, cv2.COLOR_BGR2GRAY)

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
