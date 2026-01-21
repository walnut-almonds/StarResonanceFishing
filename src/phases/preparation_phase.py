"""
拋竿前的準備
"""

import logging
import time

from ..config_manager import ConfigManager
from ..image_detector import ImageDetector
from ..input_controller_winapi import WinAPIInputController
from ..utils import get_resource_path
from ..window_manager import WindowManager


class PreparationPhase:
    def __init__(
        self,
        config: ConfigManager,
        window_manager: WindowManager,
        input_controller: WinAPIInputController,
        image_detector: ImageDetector,
    ):
        """
        初始化準備階段處理器

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
        self.logger = logging.getLogger("FishingBot.PreparationPhase")

    def check_and_replace_rod(self):
        """檢查魚竿耐久度是否耗盡，如果耗盡則點擊更換"""
        self.logger.debug("檢查魚竿耐久度")

        # 取得配置
        rod_config = self.config.get("detection.rod_durability", {})
        wait_time = rod_config.get("wait_time", 0.1)
        search_timeout = rod_config.get("search_timeout", 0.4)
        template_path = get_resource_path(
            rod_config.get("template", "templates/rod_depleted.png")
        )
        click_delay = rod_config.get("click_delay", 0.5)
        response_delay = rod_config.get("response_delay", 0.1)
        check_interval = rod_config.get("check_interval", 0.1)

        # 等待提示出現
        time.sleep(wait_time)

        # 取得視窗資訊
        window_rect = self.window_manager.get_window_rect()
        if not window_rect:
            self.logger.warning("無法取得視窗位置，跳過耐久度檢查")
            return

        x, y, w, h = window_rect
        region_config = rod_config.get(
            "region", {"x": 0.0, "y": 0.0, "width": 1.0, "height": 1.0}
        )

        region = (
            int(x + w * region_config["x"]),
            int(y + h * region_config["y"]),
            int(w * region_config["width"]),
            int(h * region_config["height"]),
        )

        # 嘗試查找耐久度耗盡提示
        start_time = time.time()
        found = False

        while time.time() - start_time < search_timeout:
            try:
                screen = self.image_detector.capture_screen(region)
                if screen is None:
                    time.sleep(check_interval)
                    continue

                position = self.image_detector.find_template(
                    screen, template_path, 0.87
                )
                if position is not None:
                    self.logger.info("檢測到魚竿耐久度耗盡！")
                    found = True
                    break
            except Exception as e:
                self.logger.debug(f"搜尋耐久度提示失敗: {e}")

            time.sleep(check_interval)

        if found:
            # 取得點擊位置配置
            first_click_pos = rod_config.get(
                "first_click_pos", {"x": 0.5, "y": 0.5}
            )
            first_click_x = int(x + w * first_click_pos["x"])
            first_click_y = int(y + h * first_click_pos["y"])

            second_click_pos = rod_config.get(
                "second_click_pos", {"x": 0.5, "y": 0.6}
            )
            second_click_x = int(x + w * second_click_pos["x"])
            second_click_y = int(y + h * second_click_pos["y"])

            self.logger.info("開始更換魚竿")

            try:
                # 讀取滑鼠移動時間配置
                move_duration = self.config.get(
                    "anti_detection.mouse_move_duration", 0.0
                )

                # 按下 Alt 鍵
                self.logger.debug("按下 Alt 鍵")
                self.input_controller.key_down("alt")

                # 第一次點擊
                self.logger.info(
                    f"第一次點擊位置: ({first_click_x}, {first_click_y})"
                )
                self.input_controller.click(
                    first_click_x,
                    first_click_y,
                    button="left",
                    move_duration=move_duration,
                )
                self.logger.debug("第一次點擊完成")

                time.sleep(click_delay)

                # 第二次點擊
                self.logger.info(
                    f"第二次點擊位置: ({second_click_x}, {second_click_y})"
                )
                self.input_controller.click(
                    second_click_x,
                    second_click_y,
                    button="left",
                    move_duration=move_duration,
                )
                self.logger.debug("第二次點擊完成")
            finally:
                # 確保釋放 Alt 鍵
                self.input_controller.key_up("alt")
                self.logger.debug("釋放 Alt 鍵")
                self.logger.info("魚竿已更換")

            # 等待界面響應
            time.sleep(response_delay)
        else:
            self.logger.debug("魚竿耐久度正常")
