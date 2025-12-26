
"""
HP Bar BW Debug Tool
- Grabs the game window continuously
- Visualizes the HP region, the exact scanline used, and the counted area
- Reads HP as black/white (grayscale + threshold), with a configurable LEFT_PADDING (bar is not flush-left)

Controls:
- Trackbars in the "hp_debug_full" window:
  * standard_offset: base y offset inside HP_SEARCH_REGION
  * blue_shift: extra y shift if blue bar is detected on the check line
  * blue_ratio_thr%: blue ratio threshold (percent) to decide "shift"
  * slice_height: scanline thickness (px)
  * left_padding: pixels to skip from the left side (bar start offset)
  * bw_thresh: grayscale threshold (0..255)
- Keys:
  * q : quit
  * s : save screenshots + print current params

Run:
  python debug_hp_bw.py
"""
import os
import time
import datetime

import cv2
import mss
import numpy as np

from utils import get_game_window_region
from get_infos import HP_SEARCH_REGION, BLUE_COLOR_LOW, BLUE_COLOR_HIGH


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def compute_hp_bw(
    raw_bgr_image: np.ndarray,
    standard_offset: int,
    blue_shift: int,
    blue_ratio_thr: float,
    slice_height: int,
    left_padding: int,
    bw_thresh: int,
):
    """
    Returns:
      hp_percent (float)
      debug dict with: read_y, check_y, blue_ratio, roi_rect, slice_bin
    """
    x_s, y_s, w_s, _h_s = HP_SEARCH_REGION

    slice_height = max(1, int(slice_height))
    standard_offset = int(standard_offset)
    blue_shift = int(blue_shift)
    left_padding = max(0, int(left_padding))
    bw_thresh = int(bw_thresh)

    # 1) Check line for blue bar
    check_y = y_s + standard_offset
    if check_y + slice_height > raw_bgr_image.shape[0]:
        return -1.0, {"reason": "check_y_oob"}

    check_slice = raw_bgr_image[check_y : check_y + slice_height, x_s : x_s + w_s]
    hsv_check = cv2.cvtColor(check_slice, cv2.COLOR_BGR2HSV)
    mask_blue = cv2.inRange(hsv_check, BLUE_COLOR_LOW, BLUE_COLOR_HIGH)

    total_check = float(w_s * slice_height)
    blue_ratio = (cv2.countNonZero(mask_blue) / total_check) if total_check > 0 else 0.0

    # 2) Determine read line
    current_offset = standard_offset + (blue_shift if blue_ratio > blue_ratio_thr else 0)
    read_y = y_s + current_offset
    if read_y + slice_height > raw_bgr_image.shape[0]:
        return 0.0, {"reason": "read_y_oob", "read_y": read_y, "check_y": check_y}

    # 3) Read slice (BW)
    x0 = x_s + left_padding
    x0 = min(x0, x_s + w_s)  # clamp
    eff_w = (x_s + w_s) - x0

    if eff_w <= 0:
        return 0.0, {
            "reason": "effective_width_zero",
            "read_y": read_y,
            "check_y": check_y,
            "blue_ratio": blue_ratio,
        }

    read_slice = raw_bgr_image[read_y : read_y + slice_height, x0 : x_s + w_s]
    gray = cv2.cvtColor(read_slice, cv2.COLOR_BGR2GRAY)

    # Simple global threshold (invert if needed later; here we assume filled HP is brighter)
    _, bin_img = cv2.threshold(gray, bw_thresh, 255, cv2.THRESH_BINARY)

    white_pixels = cv2.countNonZero(bin_img)
    total_area = float(eff_w * slice_height)
    hp_percentage = (white_pixels / total_area) * 100.0 if total_area > 0 else 0.0

    # Small noise gate
    if hp_percentage < 1.0:
        hp_percentage = 0.0
    if hp_percentage > 100.0:
        hp_percentage = 100.0

    debug = {
        "read_y": read_y,
        "check_y": check_y,
        "blue_ratio": blue_ratio,
        "roi_rect": (x0, read_y, eff_w, slice_height),
        "slice_bin": bin_img,
        "slice_gray": gray,
    }
    return float(hp_percentage), debug


def main():
    game_region = get_game_window_region()
    if not game_region:
        raise SystemExit("Game window not found. Check OYUN_PENCERE_ADI in config.py")

    cv2.namedWindow("hp_debug_full", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("hp_debug_full", 1100, 650)

    # Trackbars
    cv2.createTrackbar("standard_offset", "hp_debug_full", 1, 150, lambda _v: None)
    cv2.createTrackbar("blue_shift", "hp_debug_full", 37, 200, lambda _v: None)
    cv2.createTrackbar("blue_ratio_thr%", "hp_debug_full", 40, 100, lambda _v: None)
    cv2.createTrackbar("slice_height", "hp_debug_full", 3, 20, lambda _v: None)
    cv2.createTrackbar("left_padding", "hp_debug_full", 0, 200, lambda _v: None)
    cv2.createTrackbar("bw_thresh", "hp_debug_full", 160, 255, lambda _v: None)

    out_dir = os.path.join("docs", "screenshots")
    _ensure_dir(out_dir)

    x_s, y_s, w_s, h_s = HP_SEARCH_REGION

    with mss.mss() as sct:
        while True:
            frame = np.array(sct.grab(game_region))[:, :, :3]  # BGR

            standard_offset = cv2.getTrackbarPos("standard_offset", "hp_debug_full")
            blue_shift = cv2.getTrackbarPos("blue_shift", "hp_debug_full")
            blue_ratio_thr = cv2.getTrackbarPos("blue_ratio_thr%", "hp_debug_full") / 100.0
            slice_height = cv2.getTrackbarPos("slice_height", "hp_debug_full")
            left_padding = cv2.getTrackbarPos("left_padding", "hp_debug_full")
            bw_thresh = cv2.getTrackbarPos("bw_thresh", "hp_debug_full")

            hp, dbg = compute_hp_bw(
                frame,
                standard_offset=standard_offset,
                blue_shift=blue_shift,
                blue_ratio_thr=blue_ratio_thr,
                slice_height=slice_height,
                left_padding=left_padding,
                bw_thresh=bw_thresh,
            )

            vis = frame.copy()

            # Draw HP search region
            cv2.rectangle(vis, (x_s, y_s), (x_s + w_s, y_s + h_s), (0, 255, 0), 2)

            # Draw check and read lines
            if "check_y" in dbg:
                cy = int(dbg["check_y"])
                cv2.line(vis, (x_s, cy), (x_s + w_s, cy), (255, 255, 0), 1)
            if "read_y" in dbg:
                ry = int(dbg["read_y"])
                cv2.line(vis, (x_s, ry), (x_s + w_s, ry), (0, 255, 255), 1)

            # Draw counted ROI
            if "roi_rect" in dbg:
                rx, ry, rw, rh = dbg["roi_rect"]
                cv2.rectangle(vis, (rx, ry), (rx + rw, ry + rh), (0, 0, 255), 2)

            # Text overlay
            blue_ratio = dbg.get("blue_ratio", 0.0)
            cv2.putText(
                vis,
                f"HP(BW): {hp:5.1f}% | blue_ratio: {blue_ratio:.2f} | thr: {bw_thresh} | left_pad: {left_padding}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (255, 255, 255),
                2,
            )

            cv2.imshow("hp_debug_full", vis)

            # Show ROI bin enlarged
            if "slice_bin" in dbg and dbg["slice_bin"] is not None:
                bin_img = dbg["slice_bin"]
                scale = 12
                bin_big = cv2.resize(
                    bin_img, (bin_img.shape[1] * scale, bin_img.shape[0] * scale), interpolation=cv2.INTER_NEAREST
                )
                cv2.imshow("hp_debug_roi_bw", bin_big)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key == ord("s"):
                ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                full_path = os.path.join(out_dir, f"hp_bw_full_{ts}.png")
                roi_path = os.path.join(out_dir, f"hp_bw_roi_{ts}.png")
                cv2.imwrite(full_path, vis)
                if "slice_bin" in dbg and dbg["slice_bin"] is not None:
                    cv2.imwrite(roi_path, dbg["slice_bin"])

                print("\n[SAVED]")
                print(" full:", full_path)
                print(" roi :", roi_path)
                print(
                    f" params: standard_offset={standard_offset}, blue_shift={blue_shift}, blue_ratio_thr={blue_ratio_thr:.2f}, "
                    f"slice_height={slice_height}, left_padding={left_padding}, bw_thresh={bw_thresh}"
                )

            time.sleep(0.01)

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
