import gymnasium as gym
from gymnasium import spaces
import numpy as np
import mss
import pyautogui
import time
import cv2
import datetime
import threading

from utils import get_game_window_region
from config import (
    ACTION_SPACE_SIZE,
    ACTION_MAP,
    OYUN_PENCERE_ADI,
)

from get_infos import InfoExtractor

PRIORITY_LIST = [
    "katana",
    "dexecutioner",
    "frostwalker",
    "chaos_tome",
    "precision_tome",
    "xp_tome",
    "cursed_tome",
]


class ScreenMonitor(threading.Thread):
    def __init__(self, game_region):
        super().__init__()
        self.game_region = game_region
        self.extractor = InfoExtractor()
        self.running = True
        self.latest_game_state = {
            "current_hp": 100.0,
            "is_level_up": False,
            "is_game_over": False,
        }
        self.latest_raw_obs = None
        self.daemon = True

    def run(self):
        with mss.mss() as sct:
            while self.running:
                try:
                    screen_raw = sct.grab(self.game_region)
                    raw_obs = np.array(screen_raw)[:, :, :3]
                    state = self.extractor.extract_game_state(raw_obs)
                    self.latest_game_state = state
                    self.latest_raw_obs = raw_obs
                    time.sleep(0.01)
                except Exception as e:
                    print(f"Monitor Hatasi: {e}")

    def stop(self):
        self.running = False


class GameEnv(gym.Env):
    metadata = {"render_modes": ["human"]}

    def __init__(self):
        super(GameEnv, self).__init__()

        self.action_space = spaces.Discrete(ACTION_SPACE_SIZE)
        low = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        high = np.array([100.0, 1.0, 1.0], dtype=np.float32)
        self.observation_space = spaces.Box(low, high, dtype=np.float32)

        self.game_region = get_game_window_region()
        if not self.game_region:
            raise ValueError("Oyun penceresi bulunamadı.")

        self.monitor = ScreenMonitor(self.game_region)
        self.monitor.start()
        time.sleep(1.0)

        self.render_window_name = "AI Bot Log Penceresi"
        self.current_action_str = "NOP"
        self.last_hp = 100.0
        self.current_level = 1
        self.on_levelup_screen = False

        self.last_reward = 0.0
        self.last_game_state = self.monitor.latest_game_state
        self.window_initialized = False
        self.LOG_BOX_WIDTH = 400
        self.LOG_BOX_HEIGHT = 250
        self.screen_width, self.screen_height = pyautogui.size()

        cv2.namedWindow(self.render_window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(
            self.render_window_name, self.LOG_BOX_WIDTH, self.LOG_BOX_HEIGHT
        )

        self.is_resetting = False
        self.pressed_movement_keys = set()

    def _create_observation_vector(self):
        hp = self.last_hp
        level_up = 1.0 if self.last_game_state.get("is_level_up", False) else 0.0
        game_over = 1.0 if self.last_game_state.get("is_game_over", False) else 0.0
        return np.array([hp, level_up, game_over], dtype=np.float32)

    def _calculate_reward(self, new_game_state):
        reward = -0.01
        current_hp = new_game_state["current_hp"]

        if current_hp == -1.0:
            current_hp = self.last_hp

        if current_hp < self.last_hp:
            reward -= 50
        elif current_hp > self.last_hp:
            reward += 10
        self.last_hp = current_hp

        is_level_up = new_game_state["is_level_up"]

        if is_level_up and not self.on_levelup_screen:
            reward += 200
            self.current_level += 1
            self.on_levelup_screen = True
        elif not is_level_up:
            self.on_levelup_screen = False

        return reward

    def _get_terminated(self, new_game_state):
        if new_game_state["is_game_over"]:
            return True
        return False

    def _release_all_movement_keys(self):
        try:
            if self.pressed_movement_keys:
                for key in self.pressed_movement_keys:
                    pyautogui.keyUp(key)
                self.pressed_movement_keys.clear()
        except:
            pass

    def _wait_and_check(self, duration):
        start_time = time.time()
        while time.time() - start_time < duration:
            if self.monitor.latest_game_state.get("is_level_up", False):
                return True
            time.sleep(0.005)
        return False

    def _choose_best_levelup_action(self):
        raw_obs = self.monitor.latest_raw_obs
        if raw_obs is None:
            return 7

        found_items = self.monitor.extractor.scan_levelup_screen(raw_obs)

        best_slot_index = 0
        best_priority_idx = 999

        for i, item_name in enumerate(found_items):
            if item_name in PRIORITY_LIST:
                p_idx = PRIORITY_LIST.index(item_name)
                if p_idx < best_priority_idx:
                    best_priority_idx = p_idx
                    best_slot_index = i

        return 7 + best_slot_index

    def step(self, action):
        self.last_game_state = self.monitor.latest_game_state
        is_level_up_visible = self.last_game_state.get("is_level_up", False)

        if is_level_up_visible:
            forced_action = self._choose_best_levelup_action()
            action = forced_action
            self.current_action_str = f"AUTO-PICK: {ACTION_MAP[action]}"
            self._release_all_movement_keys()

        # OYUN AKIŞI
        if self.is_resetting:
            if not self.last_game_state.get("is_game_over", False):
                try:
                    pyautogui.keyUp("r")
                except:
                    pass
                self.is_resetting = False
            else:
                self.current_action_str = "RESETTING..."
                return self._create_observation_vector(), 0, False, False, {}

        active_window = pyautogui.getActiveWindow()
        is_game_active = (
            active_window is not None and active_window.title == OYUN_PENCERE_ADI
        )

        command_type, command_value = ACTION_MAP[action]

        if not is_level_up_visible:
            self.current_action_str = str(ACTION_MAP[action])

        movement_actions = [0, 1, 2, 3, 4, 5]
        upgrade_actions = [7, 8, 9, 10, 11, 12]
        interaction_action = 6
        is_invalid_action = False

        if is_level_up_visible:
            if action in movement_actions or action == interaction_action:
                command_type = "nop"
                is_invalid_action = True
        else:
            if action in upgrade_actions or action == interaction_action:
                command_type = "nop"
                is_invalid_action = True

        if not is_game_active:
            self.current_action_str = "Oyun Pasif"
            command_type = "nop"

        if is_game_active:
            if action in movement_actions:
                try:
                    pyautogui.keyDown(command_value)
                    self.pressed_movement_keys.add(command_value)
                except:
                    pass
            else:
                self._release_all_movement_keys()
                if command_type == "key":
                    try:
                        pyautogui.press(command_value)
                    except:
                        pass
                elif command_type == "sequence":
                    try:
                        for key in command_value:
                            pyautogui.press(key)
                            time.sleep(0.05)
                    except:
                        pass

        was_interrupted = self._wait_and_check(0.1)
        if was_interrupted:
            self._release_all_movement_keys()
            self.last_game_state = self.monitor.latest_game_state

        reward = self._calculate_reward(self.last_game_state)
        if is_invalid_action:
            reward -= 10
        self.last_reward = reward

        terminated = self._get_terminated(self.last_game_state)
        if terminated:
            self._release_all_movement_keys()

        return self._create_observation_vector(), reward, terminated, False, {}

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        print("Resetleniyor...")
        self._release_all_movement_keys()

        try:
            if pyautogui.getActiveWindow().title == OYUN_PENCERE_ADI:
                pyautogui.keyDown("r")
                self.is_resetting = True
        except:
            pass

        self.current_level = 1
        self.last_game_state = self.monitor.latest_game_state
        self.last_hp = self.last_game_state.get("current_hp", 100.0)

        if self.last_hp < 1:
            self.last_hp = 100.0

        self.on_levelup_screen = False
        return self._create_observation_vector(), {}

    def render(self):
        display_img = np.zeros(
            (self.LOG_BOX_HEIGHT, self.LOG_BOX_WIDTH, 3), dtype=np.uint8
        )
        now = datetime.datetime.now().strftime("%H:%M:%S")

        logs = [
            f"ZAMAN: {now}",
            f"EYLEM: {self.current_action_str}",
            f"ODUL: {self.last_reward:.1f}",
            f"HP: {self.last_hp:.1f}% | LVL: {self.current_level}",
            f"LVL: {self.last_game_state.get('is_level_up', False)}",
            f"OYUN: {self.last_game_state.get('is_game_over', False)}",
        ]

        for i, line in enumerate(logs):
            cv2.putText(
                display_img,
                line,
                (10, 30 + (i * 30)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                1,
            )

        cv2.imshow(self.render_window_name, display_img)

        if not self.window_initialized:
            try:
                cv2.moveWindow(
                    self.render_window_name,
                    self.screen_width - 420,
                    self.screen_height - 350,
                )
                cv2.setWindowProperty(self.render_window_name, cv2.WND_PROP_TOPMOST, 1)
                self.window_initialized = True
            except:
                pass
        cv2.waitKey(1)

    def close(self):
        if hasattr(self, "monitor"):
            self.monitor.stop()
            self.monitor.join()
        self._release_all_movement_keys()
        if self.is_resetting:
            try:
                pyautogui.keyUp("r")
            except:
                pass
        cv2.destroyAllWindows()
