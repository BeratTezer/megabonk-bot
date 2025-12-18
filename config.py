OYUN_PENCERE_ADI = "Megabonk"

ACTION_MAP = {
    0: ("key", "w"),  # Hareket: İleri
    1: ("key", "a"),  # Hareket: Sol
    2: ("key", "s"),  # Hareket: Geri
    3: ("key", "d"),  # Hareket: Sağ
    4: ("key", "space"),  # Hareket: Space
    5: ("key", "ctrl"),  # Hareket: Ctrl
    6: ("key", "e"),  # Etkileşim / Seçim
    7: ("sequence", ["up", "up", "up", "1"]),  # Seçenek 1
    8: ("sequence", ["up", "up", "up", "2"]),  # Seçenek 2
    9: ("sequence", ["up", "up", "up", "3"]),  # Seçenek 3
    10: (
        "sequence",
        ["up", "up", "up", "down", "down", "down", "enter"],
    ),  # Seçenek: Refresh
    11: (
        "sequence",
        ["up", "up", "up", "down", "down", "down", "left", "enter"],
    ),  # Seçenek: Skip
    12: (
        "sequence",
        ["up", "up", "up", "down", "down", "down", "left", "left", "enter"],
    ),  # Seçenek: Banish
    13: ("nop", None),  # No Operation
}
ACTION_SPACE_SIZE = len(ACTION_MAP)

NOP_ACTION_ID = 13
