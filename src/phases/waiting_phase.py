"""
等待咬鉤階段處理
"""

import logging
import time

from src.config_manager import ConfigManager
from src.image_detector import ImageDetector
from src.utils import get_resource_path
from src.window_manager import WindowManager


class WaitingPhase:
    """等待咬鉤階段處理器"""

    def __init__(
        self,
        config: ConfigManager,
        window_manager: WindowManager,
        image_detector: ImageDetector,
    ):
        """
        初始化等待咬鉤階段處理器

        Args:
            config: 配置管理器
            window_manager: 視窗管理器
            image_detector: 圖像檢測器
        """
        self.config = config
        self.window_manager = window_manager
        self.image_detector = image_detector
        self.logger = logging.getLogger("FishingBot.WaitingPhase")

    def wait_for_bite(self) -> bool:
        """
        等待咬鉤

        Returns:
            是否檢測到咬鉤
        """
        self.logger.debug("等待魚兒咬鉤...")
        timeout = self.config.get("fishing.bite_timeout", 30)
        check_interval = self.config.get("detection.check_interval", 0.1)
        start_time = time.time()

        while time.time() - start_time < timeout:
            if self._detect_bite_indicator():
                return True
            time.sleep(check_interval)

        self.logger.warning(f"等待咬鉤超時 ({timeout}秒)")
        return False

    def _detect_bite_indicator(self) -> bool:
        """
        檢測咬鉤指示器

        Returns:
            是否檢測到咬鉤
        """
        window_rect = self.window_manager.get_window_rect()
        if not window_rect:
            return False

        x, y, w, h = window_rect
        region_config = self.config.get("detection.region")

        region = (
            int(x + w * region_config["x"]),
            int(y + h * region_config["y"]),
            int(w * region_config["width"]),
            int(h * region_config["height"]),
        )

        # 優先使用顏色檢測
        # 咬鉤指示器的橙色範圍
        color_detected = self.image_detector.detect_color_in_range(
            region,
            color_min=(1, 70, 246),
            color_max=(29, 195, 254),
            min_pixel_ratio=0.03,  # 至少 3% 的像素符合顏色範圍
        )

        if color_detected:
            self.logger.info("檢測到咬鉤（顏色檢測）！")
            return True

        # 如果顏色檢測失敗，使用模板匹配作為備用
        screen = self.image_detector.capture_screen(region)
        if screen is None:
            return False

        template_path = get_resource_path("templates/bite_indicator.png")
        position = self.image_detector.find_template(screen, template_path)

        if position is not None:
            self.logger.info("檢測到咬鉤（模板匹配）！")
            return True

        return False

    def reel_in(self, input_controller):
        """
        收竿操作

        Args:
            input_controller: 輸入控制器
        """
        self.logger.debug("開始收竿")

        reel_type = self.config.get("fishing.reel_type", "key")
        if reel_type == "click":
            self._reel_by_click(input_controller)
        else:
            self._reel_by_key(input_controller)

        # 等待收竿動畫
        reel_delay = self.config.get("fishing.reel_delay", 0.1)
        time.sleep(reel_delay)

        self.logger.debug("收竿完成")

    def _reel_by_click(self, input_controller):
        """滑鼠點擊收竿"""
        window_rect = self.window_manager.get_window_rect()
        if not window_rect:
            self.logger.error("無法取得視窗位置，收竿失敗")
            return

        x, y, w, h = window_rect
        click_pos = self.config.get(
            "fishing.reel_click_pos", {"x": 0.5, "y": 0.5}
        )
        click_x = int(x + w * click_pos["x"])
        click_y = int(y + h * click_pos["y"])

        # 讀取滑鼠移動時間配置
        move_duration = self.config.get(
            "anti_detection.mouse_move_duration", 0.0
        )

        input_controller.click(
            click_x, click_y, button="left", move_duration=move_duration
        )

    def _reel_by_key(self, input_controller):
        """鍵盤按鍵收竿"""
        reel_key = self.config.get("fishing.reel_key", "e")
        input_controller.press_key(reel_key)
