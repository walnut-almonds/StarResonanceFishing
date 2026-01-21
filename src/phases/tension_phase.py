"""
拉力計階段處理（魚追蹤和QTE）
"""

import logging
import threading
import time

from ..config_manager import ConfigManager
from ..image_detector import ImageDetector
from ..input_controller_winapi import WinAPIInputController
from ..utils import get_resource_path
from ..window_manager import WindowManager


class TensionPhase:
    """拉力計階段處理器"""

    def __init__(
        self,
        config: ConfigManager,
        window_manager: WindowManager,
        input_controller: WinAPIInputController,
        image_detector: ImageDetector,
    ):
        """
        初始化拉力計階段處理器

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
        self.logger = logging.getLogger("FishingBot.TensionPhase")

    def detect_tension_bar(self) -> bool:
        """
        檢測是否出現拉力計

        Returns:
            是否檢測到拉力計
        """
        window_rect = self.window_manager.get_window_rect()
        if not window_rect:
            return False

        x, y, w, h = window_rect
        tension_config = self.config.get("detection.tension_bar", {})
        region_config = tension_config.get(
            "region", {"x": 0.25, "y": 0.7, "width": 0.4, "height": 0.2}
        )

        region = (
            int(x + w * region_config["x"]),
            int(y + h * region_config["y"]),
            int(w * region_config["width"]),
            int(h * region_config["height"]),
        )

        template_path = get_resource_path(
            tension_config.get("template", "templates/tension_bar.png")
        )
        try:
            screen = self.image_detector.capture_screen(region)
            position = self.image_detector.find_template(screen, template_path)
            if position is not None:
                self.logger.debug(f"在 {position} 檢測到拉力計")
                return True
        except Exception as e:
            self.logger.debug(f"拉力計模板匹配失敗: {e}")

        return False

    def handle_tension_phase(self):
        """處理拉力計階段（收竿後的魚追蹤和QTE）"""
        self.logger.info("開始處理拉力計階段")

        # 取得配置
        tension_duration = self.config.get(
            "fishing.tension_phase.duration", 180
        )

        # 共享狀態變量
        self.stop_threads = False
        self.start_time = time.time()

        # 創建並啟動兩個獨立線程
        mouse_thread = threading.Thread(
            target=self._mouse_control_thread, name="MouseControlThread"
        )
        movement_thread = threading.Thread(
            target=self._movement_control_thread, name="MovementControlThread"
        )

        # 啟動線程
        mouse_thread.start()
        movement_thread.start()

        try:
            # 主循環：監控拉力計是否還存在
            while time.time() - self.start_time < tension_duration:
                if not self.detect_tension_bar():
                    self.logger.info("拉力計消失，結束追蹤階段")
                    break
                time.sleep(0.5)
        finally:
            # 通知線程停止
            self.stop_threads = True

            # 等待線程結束
            mouse_thread.join(timeout=1.0)
            movement_thread.join(timeout=1.0)

            self.logger.info("拉力計階段完成")

    def _mouse_control_thread(self):
        """左鍵控制線程"""
        # 取得配置
        red_tension_intermittent_hold_threshold = self.config.get(
            "fishing.tension_phase.red_tension_intermittent_hold_threshold", 50
        )
        intermittent_hold_duration = self.config.get(
            "fishing.tension_phase.intermittent_hold_duration", 0.2
        )
        intermittent_release_duration = self.config.get(
            "fishing.tension_phase.intermittent_release_duration", 0.2
        )
        red_tension_max_threshold = self.config.get(
            "fishing.tension_phase.red_tension_max_threshold", 100
        )
        max_tension_release_duration = self.config.get(
            "fishing.tension_phase.max_tension_release_duration", 0.3
        )
        check_interval = self.config.get(
            "fishing.tension_phase.check_interval", 0.05
        )

        is_holding_mouse = False
        click_hold_release_time = None

        # 開始時先按住左鍵
        self.input_controller.mouse_down("left")
        is_holding_mouse = True
        self.logger.info("開始按住滑鼠左鍵")

        try:
            while not self.stop_threads:
                # 檢測紅色張力狀態
                tension_value = self._detect_red_tension_color()
                if tension_value is not None:
                    self.logger.debug(f"張力值: {tension_value}")
                else:
                    self.logger.debug("張力值識別失敗")
                    is_red_high = self._detect_red_tension_template()
                    if is_red_high:
                        self.logger.debug("檢測到紅色張力模板")
                        tension_value = 101  # 強制視為過高
                    else:
                        tension_value = 0

                # 控制左鍵
                current_time = time.time()
                elapsed_since_time = None
                if click_hold_release_time is not None:
                    elapsed_since_time = current_time - click_hold_release_time

                if tension_value >= red_tension_max_threshold:
                    if (
                        elapsed_since_time is None
                        or elapsed_since_time >= max_tension_release_duration
                    ):
                        # 張力過高，釋放滑鼠左鍵
                        if is_holding_mouse:
                            self.input_controller.mouse_up("left")
                            is_holding_mouse = False
                            click_hold_release_time = current_time
                            self.logger.info(
                                f"拉力過高！釋放滑鼠左鍵並保持{max_tension_release_duration}秒"
                            )
                elif tension_value >= red_tension_intermittent_hold_threshold:
                    # 張力較高，間歇點擊滑鼠左鍵
                    if is_holding_mouse:
                        if (
                            elapsed_since_time is None
                            or elapsed_since_time >= intermittent_hold_duration
                        ):
                            self.input_controller.mouse_up("left")
                            is_holding_mouse = False
                            click_hold_release_time = current_time
                    else:
                        if (
                            elapsed_since_time is None
                            or elapsed_since_time
                            >= intermittent_release_duration
                        ):
                            self.input_controller.mouse_down("left")
                            is_holding_mouse = True
                            click_hold_release_time = current_time
                else:
                    if not is_holding_mouse:
                        self.input_controller.mouse_down("left")
                        is_holding_mouse = True

                time.sleep(check_interval)

        finally:
            # 確保釋放滑鼠左鍵
            if is_holding_mouse:
                self.input_controller.mouse_up("left")
                self.logger.info("釋放滑鼠左鍵")

    def _movement_control_thread(self):
        """AD 方向鍵控制線程"""
        tracking_enabled = self.config.get(
            "fishing.fish_tracking.enabled", True
        )

        if not tracking_enabled:
            self.logger.info("魚追蹤已禁用，移動控制線程退出")
            return

        # 取得配置
        check_interval = self.config.get(
            "fishing.fish_tracking.check_interval", 0.05
        )
        hold_rate = (
            2.8  # 因為左右魚桿比放開還慢N倍，這個參數用來補償這個時間差
        )
        fish_speed_rate = (
            1.7  # 因為左右魚桿和魚的速度不同，這個參數用來調整追蹤速度
        )
        max_no_detection = 100

        left_key = self.config.get("fishing.fish_tracking.left_key", "a")
        right_key = self.config.get("fishing.fish_tracking.right_key", "d")
        center_threshold_max = self.config.get(
            "fishing.fish_tracking.center_threshold_max", 0.10
        )

        is_holding_left = False
        is_holding_right = False
        last_fish_position = None
        pre_fish_position = ("center", 0.0)
        no_detection_count = 0

        try:
            while not self.stop_threads:
                # 魚追蹤
                fish_direction, offset_ratio = self._get_fish_position()

                if fish_direction is not None:
                    last_fish_position = (fish_direction, offset_ratio)
                    no_detection_count = 0
                else:
                    no_detection_count += 1
                    if (
                        no_detection_count <= max_no_detection
                        and last_fish_position is not None
                    ):
                        fish_direction, offset_ratio = last_fish_position
                        self.logger.debug(
                            f"未檢測到魚 ({no_detection_count}/{max_no_detection})，保持原動作: {fish_direction} ({offset_ratio:.3f})"
                        )
                    else:
                        if no_detection_count == max_no_detection + 1:
                            self.logger.warning(
                                f"連續{max_no_detection}次未檢測到魚，重置按鍵"
                            )
                        fish_direction = "center"
                        offset_ratio = 0.0

                # 控制方向鍵
                if fish_direction == "center":
                    # 魚在中心區域，釋放所有方向鍵
                    if is_holding_left:
                        self.input_controller.key_up(left_key)
                        is_holding_left = False
                        self.logger.debug(f"魚在中心，釋放 {left_key} 鍵")
                    if is_holding_right:
                        self.input_controller.key_up(right_key)
                        is_holding_right = False
                        self.logger.debug(f"魚在中心，釋放 {right_key} 鍵")
                    time.sleep(check_interval)
                elif offset_ratio >= center_threshold_max:
                    # 偏移量超過最大閾值，完全壓住按鍵
                    if fish_direction == "left":
                        if not is_holding_left:
                            if is_holding_right:
                                self.input_controller.key_up(right_key)
                                is_holding_right = False
                            self.input_controller.key_down(left_key)
                            is_holding_left = True
                            self.logger.debug(
                                f"魚在左側(完全)，按住 {left_key} 鍵"
                            )
                    else:  # right
                        if not is_holding_right:
                            if is_holding_left:
                                self.input_controller.key_up(left_key)
                                is_holding_left = False
                            self.input_controller.key_down(right_key)
                            is_holding_right = True
                            self.logger.debug(
                                f"魚在右側(完全)，按住 {right_key} 鍵"
                            )
                    time.sleep(check_interval)
                else:
                    pre_fish_direction, pre_offset_ratio = pre_fish_position

                    if fish_direction == "left":
                        if is_holding_right:
                            self.input_controller.key_up(right_key)
                            is_holding_right = False

                        if pre_fish_direction == fish_direction:
                            ratio_diff = offset_ratio - pre_offset_ratio
                            if ratio_diff > 0:
                                if not is_holding_left:
                                    self.input_controller.key_down(left_key)
                                    is_holding_left = True
                            elif ratio_diff < 0:
                                if is_holding_left:
                                    self.input_controller.key_up(left_key)
                                    is_holding_left = False
                            else:  # ratio_diff == 0
                                if is_holding_left:
                                    self.input_controller.key_up(left_key)
                                    is_holding_left = False
                                else:
                                    self.input_controller.key_down(left_key)
                                    is_holding_left = True
                            if is_holding_left:
                                press_duration = (
                                    abs(ratio_diff)
                                    * fish_speed_rate
                                    * hold_rate
                                )
                            else:
                                press_duration = (
                                    abs(ratio_diff) * fish_speed_rate
                                )
                            time.sleep(
                                min(check_interval * 10, press_duration)
                            )
                        else:
                            if not is_holding_left:
                                self.input_controller.key_down(left_key)
                                is_holding_left = True
                                time.sleep(check_interval * hold_rate)

                    else:  # right
                        if is_holding_left:
                            self.input_controller.key_up(left_key)
                            is_holding_left = False
                        if pre_fish_direction == fish_direction:
                            ratio_diff = offset_ratio - pre_offset_ratio
                            if ratio_diff > 0:
                                if not is_holding_right:
                                    self.input_controller.key_down(right_key)
                                    is_holding_right = True
                            elif ratio_diff < 0:
                                if is_holding_right:
                                    self.input_controller.key_up(right_key)
                                    is_holding_right = False
                            else:  # ratio_diff == 0
                                if is_holding_right:
                                    self.input_controller.key_up(right_key)
                                    is_holding_right = False
                                else:
                                    self.input_controller.key_down(right_key)
                                    is_holding_right = True
                            if is_holding_right:
                                press_duration = (
                                    abs(ratio_diff)
                                    * fish_speed_rate
                                    * hold_rate
                                )
                            else:
                                press_duration = (
                                    abs(ratio_diff) * fish_speed_rate
                                )
                            time.sleep(
                                min(check_interval * 10, press_duration)
                            )
                        else:
                            if not is_holding_right:
                                self.input_controller.key_down(right_key)
                                is_holding_right = True
                                time.sleep(check_interval * hold_rate)

                pre_fish_position = (fish_direction, offset_ratio)

        finally:
            # 確保釋放所有方向鍵
            if is_holding_left:
                self.input_controller.key_up(left_key)
                self.logger.info(f"釋放 {left_key} 鍵")
            if is_holding_right:
                self.input_controller.key_up(right_key)
                self.logger.info(f"釋放 {right_key} 鍵")

    def _detect_red_tension_color(self) -> int:
        """取得拉力計中紅色區域的比例"""
        window_rect = self.window_manager.get_window_rect()
        if not window_rect:
            return None

        x, y, w, h = window_rect
        tension_config = self.config.get("detection.red_tension", {})
        region_config = tension_config.get(
            "region", {"x": 0.25, "y": 0.7, "width": 0.4, "height": 0.2}
        )

        region = (
            int(x + w * region_config["x"]),
            int(y + h * region_config["y"]),
            int(w * region_config["width"]),
            int(h * region_config["height"]),
        )

        screen = self.image_detector.capture_screen(region)
        if screen is None:
            return None

        return self.image_detector.detect_red_ratio(screen)

    def _detect_red_tension_template(self) -> bool:
        """使用模板匹配檢測紅色張力狀態"""
        window_rect = self.window_manager.get_window_rect()
        if not window_rect:
            return False

        x, y, w, h = window_rect
        red_tension_config = self.config.get(
            "detection.red_tension_template", {}
        )
        region_config = red_tension_config.get(
            "region", {"x": 0.33, "y": 0.8, "width": 0.34, "height": 0.06}
        )

        region = (
            int(x + w * region_config["x"]),
            int(y + h * region_config["y"]),
            int(w * region_config["width"]),
            int(h * region_config["height"]),
        )

        red_template_path = get_resource_path(
            self.config.get(
                "fishing.tension_phase.red_template",
                "templates/red_tension.png",
            )
        )
        red_template_threshold = self.config.get(
            "fishing.tension_phase.red_template_threshold", 0.8
        )

        try:
            screen = self.image_detector.capture_screen(region)
            if screen is None:
                return False

            position = self.image_detector.find_template(
                screen, red_template_path, red_template_threshold
            )
            return position is not None
        except Exception as e:
            self.logger.debug(f"紅色張力模板檢測失敗: {e}")
            return False

    def _get_fish_position(self):
        """
        取得魚的位置狀態

        Returns:
            tuple: (direction, offset_ratio) 其中 direction 是 'left', 'right', 'center' 或 None
                   offset_ratio 是偏移量佔視窗寬度的比例（絕對值）
        """
        window_rect = self.window_manager.get_window_rect()
        if not window_rect:
            return None, 0.0

        x, y, w, h = window_rect
        splash_config = self.config.get("detection.fish_splash", {})
        region_config = splash_config.get(
            "region", {"x": 0.2, "y": 0.3, "width": 0.6, "height": 0.3}
        )

        region = (
            int(x + w * region_config["x"]),
            int(y + h * region_config["y"]),
            int(w * region_config["width"]),
            int(h * region_config["height"]),
        )

        white_threshold = splash_config.get("white_threshold", 200)
        min_area = splash_config.get("min_area", 50)
        splash_pos = self.image_detector.find_white_splash(
            region, white_threshold, min_area
        )

        if not splash_pos:
            return None, 0.0

        splash_x, splash_y = splash_pos

        # 讀取中心點偏移配置
        center_offset = self.config.get(
            "fishing.fish_tracking.center_offset", 0
        )
        window_center_x = x + w / 2 + center_offset

        center_threshold_min = self.config.get(
            "fishing.fish_tracking.center_threshold_min", 0.05
        )

        offset = splash_x - window_center_x
        offset_ratio = abs(offset) / w  # 偏移量佔視窗寬度的比例

        if offset_ratio < center_threshold_min:
            return "center", offset_ratio
        elif offset < 0:
            return "left", offset_ratio
        else:
            return "right", offset_ratio
