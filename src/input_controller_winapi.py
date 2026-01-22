"""
Windows API 輸入控制器
"""

import ctypes
import logging
import random
import time
from ctypes import (
    POINTER,
    Structure,
    Union,
    c_long,
    c_short,
    c_ulong,
    c_ushort,
    sizeof,
    windll,
    wintypes,
)

# Windows API 常量
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_ABSOLUTE = 0x8000

KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008

# 虛擬鍵碼
VK_CODE = {
    "a": 0x41,
    "d": 0x44,
    "e": 0x45,
    "w": 0x57,
    "s": 0x53,
    "space": 0x20,
    "enter": 0x0D,
    "esc": 0x1B,
    "alt": 0x12,  # VK_MENU
}

# 掃描碼
SCAN_CODE = {
    "a": 0x1E,
    "d": 0x20,
    "e": 0x12,
    "w": 0x11,
    "s": 0x1F,
    "space": 0x39,
    "enter": 0x1C,
    "esc": 0x01,
    "alt": 0x38,  # Alt 鍵的掃描碼
}


class MOUSEINPUT(Structure):
    _fields_ = [
        ("dx", c_long),
        ("dy", c_long),
        ("mouseData", c_ulong),
        ("dwFlags", c_ulong),
        ("time", c_ulong),
        ("dwExtraInfo", POINTER(c_ulong)),
    ]


class KEYBDINPUT(Structure):
    _fields_ = [
        ("wVk", c_ushort),
        ("wScan", c_ushort),
        ("dwFlags", c_ulong),
        ("time", c_ulong),
        ("dwExtraInfo", POINTER(c_ulong)),
    ]


class HARDWAREINPUT(Structure):
    _fields_ = [("uMsg", c_ulong), ("wParamL", c_short), ("wParamH", c_ushort)]


class INPUT_UNION(Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]


class INPUT(Structure):
    _fields_ = [("type", c_ulong), ("union", INPUT_UNION)]


class WinAPIInputController:
    """使用 Windows API 的輸入控制器"""

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
        self.delay_mean = (random_delay_min + random_delay_max) / 2
        self.delay_std = (random_delay_max - random_delay_min) / 6
        self.logger = logging.getLogger("FishingBot.WinAPIInputController")

        # Windows API 函式
        self.SendInput = windll.user32.SendInput
        self.SetCursorPos = windll.user32.SetCursorPos
        self.GetCursorPos = windll.user32.GetCursorPos

        self.logger.info("Windows API 輸入控制器已初始化")

    def _random_delay(self):
        """添加隨機延遲"""
        delay = random.gauss(self.delay_mean, self.delay_std)
        delay = max(self.random_delay_min, min(self.random_delay_max, delay))
        time.sleep(delay)

    def _send_input(self, *inputs):
        """發送輸入事件"""
        nInputs = len(inputs)
        LPINPUT = INPUT * nInputs
        pInputs = LPINPUT(*inputs)
        cbSize = sizeof(INPUT)
        return self.SendInput(nInputs, pInputs, cbSize)

    def move_to(self, x: int, y: int, duration: float = 0.5):
        """
        移動滑鼠到指定位置

        Args:
            x: X 座標（螢幕座標）
            y: Y 座標（螢幕座標）
            duration: 移動持續時間（秒）
        """
        try:
            self._random_delay()

            # 獲取當前位置
            current_pos = self.get_mouse_position()

            # 計算移動步数
            steps = max(10, int(duration * 100))
            dx = (x - current_pos[0]) / steps
            dy = (y - current_pos[1]) / steps

            # 逐步移動
            for i in range(steps):
                new_x = int(current_pos[0] + dx * (i + 1))
                new_y = int(current_pos[1] + dy * (i + 1))
                self.SetCursorPos(new_x, new_y)
                time.sleep(duration / steps)

            # 確保到达目標位置
            self.SetCursorPos(x, y)
            self.logger.debug(f"移動滑鼠到: ({x}, {y})")
        except Exception as e:
            self.logger.error(f"滑鼠移動失敗: {e}")

    def click(
        self, x: int, y: int, button: str = "left", move_duration: float = 0.0
    ):
        """
        點擊指定位置

        Args:
            x: X 座標（螢幕座標）
            y: Y 座標（螢幕座標）
            button: 滑鼠按鈕 ('left', 'right', 'middle')
            move_duration: 滑鼠移動持續時間（秒），0 表示瞬間移動
        """
        try:
            self._random_delay()

            # 添加隨機偏移
            offset_x = int(random.gauss(0, 1))
            offset_y = int(random.gauss(0, 1))
            offset_x = max(-3, min(3, offset_x))
            offset_y = max(-3, min(3, offset_y))

            target_x = x + offset_x
            target_y = y + offset_y

            # 移動到目標位置
            if move_duration > 0:
                # 使用平滑移動
                current_pos = self.get_mouse_position()
                steps = max(10, int(move_duration * 100))
                dx = (target_x - current_pos[0]) / steps
                dy = (target_y - current_pos[1]) / steps

                for i in range(steps):
                    new_x = int(current_pos[0] + dx * (i + 1))
                    new_y = int(current_pos[1] + dy * (i + 1))
                    self.SetCursorPos(new_x, new_y)
                    time.sleep(move_duration / steps)

                # 確保到達目標位置
                # self.SetCursorPos(target_x, target_y)
            else:
                # 瞬間移動
                self.SetCursorPos(target_x, target_y)
                time.sleep(0.01)

            # 確定按鈕標誌
            if button == "left":
                down_flag = MOUSEEVENTF_LEFTDOWN
                up_flag = MOUSEEVENTF_LEFTUP
            elif button == "right":
                down_flag = MOUSEEVENTF_RIGHTDOWN
                up_flag = MOUSEEVENTF_RIGHTUP
            elif button == "middle":
                down_flag = MOUSEEVENTF_MIDDLEDOWN
                up_flag = MOUSEEVENTF_MIDDLEUP
            else:
                raise ValueError(f"不支援的按鈕: {button}")

            # 創建按下事件
            down_input = INPUT()
            down_input.type = INPUT_MOUSE
            down_input.union.mi = MOUSEINPUT()
            down_input.union.mi.dx = 0
            down_input.union.mi.dy = 0
            down_input.union.mi.mouseData = 0
            down_input.union.mi.dwFlags = down_flag
            down_input.union.mi.time = 0
            down_input.union.mi.dwExtraInfo = None

            # 創建釋放事件
            up_input = INPUT()
            up_input.type = INPUT_MOUSE
            up_input.union.mi = MOUSEINPUT()
            up_input.union.mi.dx = 0
            up_input.union.mi.dy = 0
            up_input.union.mi.mouseData = 0
            up_input.union.mi.dwFlags = up_flag
            up_input.union.mi.time = 0
            up_input.union.mi.dwExtraInfo = None

            # 發送事件
            self._send_input(down_input)
            time.sleep(random.uniform(0.08, 0.12))
            self._send_input(up_input)

            self.logger.debug(
                f"點擊位置: ({x}, {y}), 偏移: ({offset_x}, {offset_y}), 按鈕: {button}"
            )
        except Exception as e:
            self.logger.error(f"點擊操作失敗: {e}")
            import traceback

            traceback.print_exc()

    def press_key(self, key: str, duration: float = 0.1):
        """
        按下按鍵

        Args:
            key: 按鍵名稱
            duration: 按鍵持續時間
        """
        try:
            self._random_delay()

            key = key.lower()
            if key not in VK_CODE:
                self.logger.error(f"不支持的按鍵: {key}")
                return

            vk_code = VK_CODE[key]
            scan_code = SCAN_CODE.get(key, 0)

            # 創建按下事件
            down_input = INPUT()
            down_input.type = INPUT_KEYBOARD
            down_input.union.ki = KEYBDINPUT()
            down_input.union.ki.wVk = vk_code
            down_input.union.ki.wScan = scan_code
            down_input.union.ki.dwFlags = 0
            down_input.union.ki.time = 0
            down_input.union.ki.dwExtraInfo = None

            # 創建釋放事件
            up_input = INPUT()
            up_input.type = INPUT_KEYBOARD
            up_input.union.ki = KEYBDINPUT()
            up_input.union.ki.wVk = vk_code
            up_input.union.ki.wScan = scan_code
            up_input.union.ki.dwFlags = KEYEVENTF_KEYUP
            up_input.union.ki.time = 0
            up_input.union.ki.dwExtraInfo = None

            # 發送事件
            self._send_input(down_input)
            time.sleep(duration)
            self._send_input(up_input)

            self.logger.debug(f"按下按鍵: {key}")
        except Exception as e:
            self.logger.error(f"按鍵操作失敗: {e}")

    def key_down(self, key: str):
        """
        按下按鍵（不釋放）

        Args:
            key: 按鍵名稱
        """
        try:
            key = key.lower()
            if key not in VK_CODE:
                self.logger.error(f"不支持的按鍵: {key}")
                return

            vk_code = VK_CODE[key]
            scan_code = SCAN_CODE.get(key, 0)

            # 創建按下事件
            down_input = INPUT()
            down_input.type = INPUT_KEYBOARD
            down_input.union.ki = KEYBDINPUT()
            down_input.union.ki.wVk = vk_code
            down_input.union.ki.wScan = scan_code
            down_input.union.ki.dwFlags = 0
            down_input.union.ki.time = 0
            down_input.union.ki.dwExtraInfo = None

            # 發送事件
            self._send_input(down_input)
            self.logger.debug(f"按下按鍵: {key} (不釋放)")
        except Exception as e:
            self.logger.error(f"按鍵按下失敗: {e}")

    def key_up(self, key: str):
        """
        釋放按鍵

        Args:
            key: 按鍵名稱
        """
        try:
            key = key.lower()
            if key not in VK_CODE:
                self.logger.error(f"不支持的按鍵: {key}")
                return

            vk_code = VK_CODE[key]
            scan_code = SCAN_CODE.get(key, 0)

            # 創建釋放事件
            up_input = INPUT()
            up_input.type = INPUT_KEYBOARD
            up_input.union.ki = KEYBDINPUT()
            up_input.union.ki.wVk = vk_code
            up_input.union.ki.wScan = scan_code
            up_input.union.ki.dwFlags = KEYEVENTF_KEYUP
            up_input.union.ki.time = 0
            up_input.union.ki.dwExtraInfo = None

            # 發送事件
            self._send_input(up_input)
            self.logger.debug(f"釋放按鍵: {key}")
        except Exception as e:
            self.logger.error(f"按鍵釋放失敗: {e}")

    def mouse_down(self, button: str = "left"):
        """
        按下滑鼠按鈕（不釋放）

        Args:
            button: 滑鼠按鈕 ('left', 'right', 'middle')
        """
        try:
            # 確定按鈕標誌
            if button == "left":
                down_flag = MOUSEEVENTF_LEFTDOWN
            elif button == "right":
                down_flag = MOUSEEVENTF_RIGHTDOWN
            elif button == "middle":
                down_flag = MOUSEEVENTF_MIDDLEDOWN
            else:
                raise ValueError(f"不支援的按鈕: {button}")

            # 創建按下事件
            down_input = INPUT()
            down_input.type = INPUT_MOUSE
            down_input.union.mi = MOUSEINPUT()
            down_input.union.mi.dx = 0
            down_input.union.mi.dy = 0
            down_input.union.mi.mouseData = 0
            down_input.union.mi.dwFlags = down_flag
            down_input.union.mi.time = 0
            down_input.union.mi.dwExtraInfo = None

            # 發送事件
            self._send_input(down_input)
            self.logger.debug(f"按下滑鼠 {button} 鍵")
        except Exception as e:
            self.logger.error(f"滑鼠按下失敗: {e}")

    def mouse_up(self, button: str = "left"):
        """
        釋放滑鼠按鈕

        Args:
            button: 滑鼠按鈕 ('left', 'right', 'middle')
        """
        try:
            # 確定按鈕標誌
            if button == "left":
                up_flag = MOUSEEVENTF_LEFTUP
            elif button == "right":
                up_flag = MOUSEEVENTF_RIGHTUP
            elif button == "middle":
                up_flag = MOUSEEVENTF_MIDDLEUP
            else:
                raise ValueError(f"不支援的按鈕: {button}")

            # 創建釋放事件
            up_input = INPUT()
            up_input.type = INPUT_MOUSE
            up_input.union.mi = MOUSEINPUT()
            up_input.union.mi.dx = 0
            up_input.union.mi.dy = 0
            up_input.union.mi.mouseData = 0
            up_input.union.mi.dwFlags = up_flag
            up_input.union.mi.time = 0
            up_input.union.mi.dwExtraInfo = None

            # 發送事件
            self._send_input(up_input)
            self.logger.debug(f"釋放滑鼠 {button} 鍵")
        except Exception as e:
            self.logger.error(f"滑鼠釋放失敗: {e}")

    def get_mouse_position(self) -> tuple[int, int]:
        """
        獲取當前滑鼠位置

        Returns:
            (x, y) 座標
        """
        point = wintypes.POINT()
        self.GetCursorPos(ctypes.byref(point))
        return point.x, point.y
