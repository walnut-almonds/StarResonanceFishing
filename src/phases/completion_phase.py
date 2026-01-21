"""
釣魚完成與重置階段處理
"""

import logging
import time

from ..config_manager import ConfigManager
from ..image_detector import ImageDetector
from ..input_controller_winapi import WinAPIInputController
from ..utils import get_resource_path
from ..window_manager import WindowManager


class CompletionPhase:
    """釣魚完成與重置階段處理器"""

    def __init__(
        self,
        config: ConfigManager,
        window_manager: WindowManager,
        input_controller: WinAPIInputController,
        image_detector: ImageDetector,
    ):
        """
        初始化完成階段處理器

        Args:
            config: 配置管理器
            window_manager: 視窗管理器
            input_controller: 輸入控制器
            image_detector: 圖像檢測器
        """
        self.config = config
        self.window_manager = window_manager
        self.input_controller = input_controller
        self.image_detector = image_detector
        self.logger = logging.getLogger("FishingBot.CompletionPhase")

    def reset_and_continue(self):
        """重置狀態，點擊"再來一次"按鈕繼續釣魚"""
        self.logger.debug("開始尋找'再來一次'按鈕")

        # 獲取配置
        retry_config = self.config.get("detection.retry_button", {})
        wait_time = retry_config.get("wait_time", 2)
        search_timeout = retry_config.get("search_timeout", 5)
        check_interval = retry_config.get("check_interval", 0.5)
        template_path = get_resource_path(
            retry_config.get("template", "templates/retry_button.png")
        )

        # 等待按鈕出現
        time.sleep(wait_time)

        # 獲取視窗信息
        window_rect = self.window_manager.get_window_rect()
        if not window_rect:
            self.logger.warning("無法獲取視窗位置，跳過重置")
            return

        x, y, w, h = window_rect
        region_config = retry_config.get(
            "region", {"x": 0.0, "y": 0.0, "width": 1.0, "height": 1.0}
        )

        region = (
            int(x + w * region_config["x"]),
            int(y + h * region_config["y"]),
            int(w * region_config["width"]),
            int(h * region_config["height"]),
        )

        # 嘗試查找按鈕
        start_time = time.time()
        found = False

        while time.time() - start_time < search_timeout:
            try:
                screen = self.image_detector.capture_screen(region)
                if screen is None:
                    time.sleep(check_interval)
                    continue

                position = self.image_detector.find_template(
                    screen, template_path
                )

                if position is not None:
                    click_x = region[0] + position[0]
                    click_y = region[1] + position[1]

                    self.logger.info(
                        f"找到'再來一次'按鈕，位置: ({click_x}, {click_y})"
                    )

                    # 讀取滑鼠移動時間配置
                    move_duration = self.config.get(
                        "anti_detection.mouse_move_duration", 0.0
                    )
                    time.sleep(0.5)

                    self.input_controller.click(
                        click_x,
                        click_y,
                        button="left",
                        move_duration=move_duration,
                    )

                    self.logger.info("已點擊'再來一次'按鈕")
                    found = True
                    break
            except Exception as e:
                self.logger.debug(f"搜尋按鈕失敗: {e}")

            time.sleep(check_interval)

        if not found:
            self.logger.warning("未找到'再來一次'按鈕，可能需要手動操作")
            time.sleep(1)
        else:
            response_delay = retry_config.get("response_delay", 1)
            time.sleep(response_delay)
