"""
拋竿階段處理
"""

import logging
import time

from ..config_manager import ConfigManager
from ..input_controller_winapi import WinAPIInputController
from ..window_manager import WindowManager


class CastingPhase:
    """拋竿階段處理器"""

    def __init__(
        self,
        config: ConfigManager,
        window_manager: WindowManager,
        input_controller: WinAPIInputController,
    ):
        """
        初始化拋竿階段處理器

        Args:
            config: 配置管理器
            window_manager: 視窗管理器
            input_controller: 輸入控制器
        """
        self.config = config
        self.window_manager = window_manager
        self.input_controller = input_controller
        self.logger = logging.getLogger("FishingBot.CastingPhase")

    def execute(self):
        """執行拋竿操作"""
        self.logger.debug("開始拋竿")

        # 執行拋竿操作
        cast_type = self.config.get("fishing.cast_type", "key")
        if cast_type == "click":
            self._cast_by_click()
        else:
            self._cast_by_key()

        # 等待拋竿動畫
        cast_delay = self.config.get("fishing.cast_delay", 2)
        time.sleep(cast_delay)

        self.logger.debug("拋竿完成")

    def _cast_by_click(self):
        """滑鼠點擊拋竿"""
        window_rect = self.window_manager.get_window_rect()
        if not window_rect:
            self.logger.error("無法取得視窗位置，拋竿失敗")
            return

        x, y, w, h = window_rect
        click_pos = self.config.get(
            "fishing.cast_click_pos", {"x": 0.5, "y": 0.5}
        )
        click_x = int(x + w * click_pos["x"])
        click_y = int(y + h * click_pos["y"])

        # 讀取滑鼠移動時間配置
        move_duration = self.config.get(
            "anti_detection.mouse_move_duration", 0.0
        )

        self.logger.info(
            f"執行點擊拋竿: 視窗({x},{y},{w}x{h}), 點擊位置({click_x},{click_y})"
        )
        self.input_controller.click(
            click_x, click_y, button="left", move_duration=move_duration
        )

    def _cast_by_key(self):
        """鍵盤按鍵拋竿"""
        cast_key = self.config.get("fishing.cast_key", "e")
        self.input_controller.press_key(cast_key)
