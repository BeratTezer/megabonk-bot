import pyautogui
from config import OYUN_PENCERE_ADI


def get_game_window_region():
    try:
        pencere = pyautogui.getWindowsWithTitle(OYUN_PENCERE_ADI)[0]
        if not pencere:
            print(f"HATA: '{OYUN_PENCERE_ADI}' başlıklı pencere bulunamadı.")
            return None

        pencere.activate()

        return {
            "top": pencere.top,
            "left": pencere.left,
            "width": pencere.width,
            "height": pencere.height,
        }

    except IndexError:
        print(f"HATA: '{OYUN_PENCERE_ADI}' başlıklı pencere bulunamadı.")
        return None
    except Exception as e:
        print(f"Pencere bulunurken hata: {e}")
        return None
