"""
輸入控制模組
"""

import logging
import random
import time

import pyautogui


class InputController:
    """輸入控制器"""

    def __init__(
        self, random_delay_min: float = 0.1, random_delay_max: float = 0.5
    ):
        """
        初始化輸入控制器

        Args:
            random_delay_min: 最小隨機延遲
            random_delay_max: 最大隨機延遲
        """
        self.random_delay_min = random_delay_min
        self.random_delay_max = random_delay_max
        # 計算高斯分佈參數：平均值和標準差
        self.delay_mean = (random_delay_min + random_delay_max) / 2
        self.delay_std = (
            random_delay_max - random_delay_min
        ) / 6  # 3倍標準差涵萹8.7%範圍
        self.logger = logging.getLogger("FishingBot.InputController")

        # 設定 PyAutoGUI 的安全特性
        pyautogui.FAILSAFE = True  # 移動滑鼠到左上角可以中止
        pyautogui.PAUSE = 0.1  # 每次操作後的暫停時間

    def _random_delay(self):
        """添加隨機延遲，使用高斯分佈模擬人類行為"""
        # 使用高斯分佈生成延遲時間，68%落在平均值±1個標準差
        delay = random.gauss(self.delay_mean, self.delay_std)
        # 限制在合理範圍內，避免極端值
        delay = max(self.random_delay_min, min(self.random_delay_max, delay))
        time.sleep(delay)

    def press_key(self, key: str, duration: float = 0.1):
        """
        按下按鍵

        Args:
            key: 按鍵名稱
            duration: 按鍵持續時間
        """
        try:
            self._random_delay()
            pyautogui.press(key, interval=duration)
            self.logger.debug(f"按下按鍵: {key}")
        except Exception as e:
            self.logger.error(f"按鍵操作失敗: {e}")

    def click(
        self, x: int, y: int, button: str = "left", move_duration: float = 0.0
    ):
        """
        點擊指定位置

        Args:
            x: X 座標
            y: Y 座標
            button: 滑鼠按鈕 ('left', 'right', 'middle')
            move_duration: 滑鼠移動持續時間（秒），0 表示使用預設（瞬間移動）
        """
        try:
            self._random_delay()
            # 使用高斯分佈添加隨機偏移，模擬人類行為
            # 68%的偏移落在±1像素內，99.7%落在±3像素內
            offset_x = int(random.gauss(0, 1))
            offset_y = int(random.gauss(0, 1))
            # 限制最大偏移量，避免點擊錯誤位置
            offset_x = max(-3, min(3, offset_x))
            offset_y = max(-3, min(3, offset_y))

            target_x = x + offset_x
            target_y = y + offset_y

            if move_duration > 0:
                # 先移動到目標位置，再點擊
                duration_variation = random.gauss(
                    move_duration, move_duration * 0.1
                )
                duration_variation = max(
                    0.1, min(move_duration * 2, duration_variation)
                )
                pyautogui.moveTo(
                    target_x, target_y, duration=duration_variation
                )
                pyautogui.click(button=button)
            else:
                # 直接點擊（PyAutoGUI 預設行為）
                pyautogui.click(target_x, target_y, button=button)

            self.logger.debug(
                f"點擊位置: ({x}, {y}), 偏移: ({offset_x}, {offset_y})"
            )
        except Exception as e:
            self.logger.error(f"點擊操作失敗: {e}")

    def move_to(self, x: int, y: int, duration: float = 0.5):
        """
        移動滑鼠到指定位置
        （也使用高斯分佈添加隨機性）
        """
        try:
            self._random_delay()
            # 給移動時長添加輕微的高斯隨機性
            duration_variation = random.gauss(duration, duration * 0.1)
            duration_variation = max(
                0.1, min(duration * 2, duration_variation)
            )
            pyautogui.moveTo(x, y, duration=duration_variation)
            self.logger.debug(
                f"移動滑鼠到: ({x}, {y}), 用時: {duration_variation:.2f}秒"
            )
        except Exception as e:
            self.logger.error(f"滑鼠移動失敗: {e}")

    def get_mouse_position(self) -> tuple[int, int]:
        """
        取得當前滑鼠位置

        Returns:
            (x, y) 座標
        """
        return pyautogui.position()
