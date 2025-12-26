import numpy as np

OYUN_PENCERE_ADI = "Megabonk"

# 1. Sağlık Çubuğu Bölgesi
HP_SEARCH_REGION = (32, 140, 331, 105)

# 2. Renk Ayarları
HP_COLOR_LOW = np.array([0, 50, 50])  # Kırmızı (Can)
HP_COLOR_HIGH = np.array([10, 255, 255])

BLUE_COLOR_LOW = np.array([100, 150, 50])  # Mavi (Kalkan)
BLUE_COLOR_HIGH = np.array([140, 255, 255])

STANDARD_OFFSET = 16
BLUE_SHIFT = 37
SLICE_HEIGHT = 3
BW_THRESH = 65

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

# Eşya listesi
PRIORITY_LIST = [
    "katana",
    "dexecutioner",
    "frostwalker",
    "chaos_tome",
    "precision_tome",
    "xp_tome",
    "cursed_tome",
]

ACTION_MAP = {
    0: ("key", "w"),  # Hareket: İleri
    1: ("key", "a"),  # Hareket: Sol
    2: ("key", "s"),  # Hareket: Geri
    3: ("key", "d"),  # Hareket: Sağ
    4: ("key", "space"),  # Hareket: Space
    5: ("key", "ctrl"),  # Hareket: Ctrl
    6: ("key", "e"),  # Etkileşim / Seçim
    7: ("Key", "1"),  # Seçenek 1
    8: ("Key", "2"),  # Seçenek 2
    9: ("Key", "3"),  # Seçenek 3
    10: (
        "sequence",
        ["down", "down", "down", "enter"],
    ),  # Seçenek: Refresh
    11: (
        "sequence",
        ["down", "down", "down", "left", "enter"],
    ),  # Seçenek: Skip
    12: (
        "sequence",
        ["down", "down", "down", "left", "left", "enter"],
    ),  # Seçenek: Banish
    13: ("nop", None),  # No Operation
}
ACTION_SPACE_SIZE = len(ACTION_MAP)

NOP_ACTION_ID = 13

MOVEMENT_ACTIONS = [0, 1, 2, 3, 4, 5]
INTERACTION_ACTIONS = [6]
MENU_ACTIONS = [7, 8, 9, 10, 11, 12]
