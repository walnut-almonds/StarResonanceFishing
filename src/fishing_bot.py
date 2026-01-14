"""
釣魚機器人主邏輯
"""
import time
import random
import logging
from enum import Enum
from .config_manager import ConfigManager
from .window_manager import WindowManager
from .input_controller_winapi import WinAPIInputController
from .image_detector import ImageDetector


class FishingState(Enum):
    """釣魚狀態"""
    IDLE = "空閒"
    CASTING = "拋竿"
    WAITING = "等待咬鉤"
    BITING = "咬鉤"
    REELING = "收竿"


class FishingBot:
    """釣魚自動化機器人"""
    
    def __init__(self, config: ConfigManager):
        """
        初始化釣魚機器人
        
        Args:
            config: 設定管理器
        """
        self.config = config
        self.logger = logging.getLogger("FishingBot")
        
        # 初始化各個模組
        self.window_manager = WindowManager(config.get('game.window_title'))
        self.input_controller = WinAPIInputController(
            config.get('anti_detection.random_delay_min', 0.1),
            config.get('anti_detection.random_delay_max', 0.5)
        )
        self.image_detector = ImageDetector(config.get('detection.threshold', 0.8))
        
        # 釣魚狀態
        self.state = FishingState.IDLE
        self.fishing_count = 0
        self.running = False
    
    def find_game_window(self) -> bool:
        """
        尋找遊戲視窗
        
        Returns:
            是否找到視窗
        """
        return self.window_manager.find_window()
    
    def start(self):
        """開始釣魚循環"""
        self.running = True
        self.logger.info("開始自動釣魚...")

        # 確保視窗啟動
        self.window_manager.activate_window()
        time.sleep(0.5)
        
        while self.running:
            try:
                # 執行一次完整的釣魚流程
                self._fishing_cycle()
                
                # 釣魚後休息
                rest_time = random.uniform(
                    self.config.get('anti_detection.rest_time_min', 1),
                    self.config.get('anti_detection.rest_time_max', 3)
                )
                self.logger.debug(f"休息 {rest_time:.2f} 秒")
                time.sleep(rest_time)
                
            except KeyboardInterrupt:
                self.logger.info("檢測到中斷信號，停止釣魚")
                break
            except Exception as e:
                self.logger.error(f"釣魚循環出錯: {e}", exc_info=True)
                time.sleep(5)
    
    def stop(self):
        """停止釣魚"""
        self.running = False
        self.logger.info("停止自動釣魚")
    
    def _fishing_cycle(self):
        """執行一次完整的釣魚流程"""

        # 檢查魚竿是否耐久度耗盡
        self._check_and_replace_rod()

        # 1. 拋竿
        self._cast_rod()
        
        # 2. 等待咬鉤
        count = 0
        while count < 3:
            if self._wait_for_bite():
                self.logger.info("上鉤了！")

                # 3. 收竿
                self._reel_in()

                # 統計釣魚次數
                self.fishing_count += 1
                self.logger.info(f"成功釣魚 #{self.fishing_count}")
                break
            else:
                self.logger.warning("等待咬鉤逾時，重新開始")
                count += 1

        # 4. 重置狀態 - 點擊"再來一次"按鈕
        self._reset_and_continue()
        
    def _cast_rod(self):
        """拋竿"""
        self.state = FishingState.CASTING
        self.logger.debug("開始拋竿")
        
        # 執行拋竿操作
        cast_type = self.config.get('fishing.cast_type', 'key')
        if cast_type == 'click':
            # 滑鼠點擊
            window_rect = self.window_manager.get_window_rect()
            if window_rect:
                x, y, w, h = window_rect
                click_pos = self.config.get('fishing.cast_click_pos', {'x': 0.5, 'y': 0.5})
                click_x = int(x + w * click_pos['x'])
                click_y = int(y + h * click_pos['y'])
                self.logger.info(f"執行點擊拋竿: 視窗({x},{y},{w}x{h}), 點擊位置({click_x},{click_y})")
                self.input_controller.click(click_x, click_y, button='left')
            else:
                self.logger.error("無法取得視窗位置，拋竿失敗")
        else:
            # 鍵盤按鍵
            cast_key = self.config.get('fishing.cast_key', 'e')
            self.input_controller.press_key(cast_key)
        
        # 等待拋竿動畫
        cast_delay = self.config.get('fishing.cast_delay', 2)
        time.sleep(cast_delay)
        
        self.state = FishingState.WAITING
        self.logger.debug("拋竿完成，等待咬鉤")
    
    def _wait_for_bite(self) -> bool:
        """
        等待咬鉤
        
        Returns:
            是否檢測到咬鉤
        """
        self.logger.debug("等待魚兒咬鉤...")
        timeout = self.config.get('fishing.bite_timeout', 30)
        check_interval = self.config.get('detection.check_interval', 0.1)
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            
            if self._detect_bite_indicator():
                return True
            
            time.sleep(check_interval)
        
        return False
    
    def _detect_bite_indicator(self) -> bool:
        """
        檢測咬鉤指示器
        
        Returns:
            是否檢測到咬鉤
        """
        # 取得檢測區域
        window_rect = self.window_manager.get_window_rect()
        if not window_rect:
            return False
        
        x, y, w, h = window_rect
        region_config = self.config.get('detection.region')
        
        region = (
            int(x + w * region_config['x']),
            int(y + h * region_config['y']),
            int(w * region_config['width']),
            int(h * region_config['height'])
        )
        
        # 截取檢測區域
        screen = self.image_detector.capture_screen(region)
        
        template_path = "templates/bite_indicator.png"
        screen = self.image_detector.capture_screen(region)
        position = self.image_detector.find_template(screen, template_path)
        return position is not None
    
    def _reel_in(self):
        """收竿"""
        self.state = FishingState.REELING
        self.logger.debug("開始收竿")

        # 執行收竿操作
        reel_type = self.config.get('fishing.reel_type', 'key')
        if reel_type == 'click':
            # 滑鼠點擊
            window_rect = self.window_manager.get_window_rect()
            if window_rect:
                x, y, w, h = window_rect
                click_pos = self.config.get('fishing.reel_click_pos', {'x': 0.5, 'y': 0.5})
                click_x = int(x + w * click_pos['x'])
                click_y = int(y + h * click_pos['y'])
                self.input_controller.click(click_x, click_y, button='left')
        else:
            # 鍵盤按鍵
            reel_key = self.config.get('fishing.reel_key', 'e')
            self.input_controller.press_key(reel_key)
        
        # 等待收竿動畫
        reel_delay = self.config.get('fishing.reel_delay', 1)
        time.sleep(reel_delay)
        
        # 檢測是否出現拉力計（tension bar）
        if self._detect_tension_bar():
            self.logger.info("檢測到拉力計，進入魚追蹤階段")
            self._handle_tension_phase()
        else:
            self.logger.debug("未檢測到拉力計，直接完成收竿")
        
        self.state = FishingState.IDLE
        self.logger.debug("收竿完成")
    
    def _detect_tension_bar(self) -> bool:
        """
        檢測是否出現拉力計（tension bar）
        
        Returns:
            是否檢測到拉力計
        """
        # 取得檢測區域
        window_rect = self.window_manager.get_window_rect()
        if not window_rect:
            return False
        
        x, y, w, h = window_rect
        
        tension_config = self.config.get('detection.tension_bar', {})
        region_config = tension_config.get('region', {'x': 0.25, 'y': 0.7, 'width': 0.4, 'height': 0.2})
        
        region = (
            int(x + w * region_config['x']),
            int(y + h * region_config['y']),
            int(w * region_config['width']),
            int(h * region_config['height'])
        )
        
        # 使用模板匹配
        template_path = tension_config.get('template', 'templates/tension_bar.png')
        try:
            screen = self.image_detector.capture_screen(region)
            position = self.image_detector.find_template(screen, template_path)
            if position is not None:
                self.logger.debug(f"在 {position} 檢測到拉力計")
                return True
        except Exception as e:
            self.logger.debug(f"拉力計模板匹配失敗: {e}")
        
        return False
    
    def _handle_tension_phase(self):
        """
        處理拉力計階段（收竿後的魚追蹤和QTE）
        拉力計出現後：
        - 如果紅色區域變多（超過閾值），釋放左鍵
        - 如果紅色區域不多，按住左鍵
        - 同時根據魚的位置按住 A/D 鍵
        """
        self.logger.info("開始處理拉力計階段")
        
        # 取得拉力計階段的配置
        tension_duration = self.config.get('fishing.tension_phase.duration', 10)
        check_interval = self.config.get('fishing.tension_phase.check_interval', 0.1)
        tracking_enabled = self.config.get('fishing.fish_tracking.enabled', True)
        red_detection_mode = self.config.get('fishing.tension_phase.red_detection_mode', 'color')
        red_threshold = self.config.get('fishing.tension_phase.red_threshold', 0.3)  # 紅色比例閾值
        release_hold_duration = self.config.get('fishing.tension_phase.release_hold_duration', 0.5)
        
        self.logger.info(f"紅色張力檢測模式: {red_detection_mode}")
        
        start_time = time.time()
        is_holding_mouse = False  # 記錄是否正在按住左鍵
        is_holding_left = False   # 記錄是否正在按住 A 鍵
        is_holding_right = False  # 記錄是否正在按住 D 鍵
        last_fish_position = None  # 記錄最後一次檢測到的魚位置
        no_detection_count = 0     # 連續未檢測到魚的次數
        max_no_detection = 20       # 最多允許多少次檢測失敗
        release_time = None        # 記錄釋放左鍵的時間
        
        left_key = self.config.get('fishing.fish_tracking.left_key', 'a')
        right_key = self.config.get('fishing.fish_tracking.right_key', 'd')
        
        # 開始時先按住左鍵
        self.input_controller.mouse_down('left')
        is_holding_mouse = True
        self.logger.info("開始按住滑鼠左鍵")
        
        try:
            while time.time() - start_time < tension_duration:
                # 檢查拉力計是否還存在（判斷是否結束）
                if not self._detect_tension_bar():
                    self.logger.info("拉力計消失，結束追蹤階段")
                    break
                
                # 檢測紅色張力狀態
                current_time = time.time()
                is_red_high = False
                
                if red_detection_mode == 'template':
                    # 使用模板匹配檢測
                    is_red_high = self._detect_red_tension_template()
                    if is_red_high:
                        self.logger.debug("檢測到紅色張力模板")
                else:
                    # 使用顏色比例檢測
                    red_ratio = self._get_red_ratio_in_tension_bar()
                    self.logger.debug(f"當前紅色比例: {red_ratio:.2%}")
                    is_red_high = red_ratio > red_threshold
                
                # 檢查是否在釋放保持期內
                if release_time is not None:
                    elapsed_since_release = current_time - release_time
                    if elapsed_since_release < release_hold_duration:
                        # 仍在釋放保持期內，保持釋放狀態
                        if is_holding_mouse:
                            self.input_controller.mouse_up('left')
                            is_holding_mouse = False
                        self.logger.debug(f"保持釋放狀態 ({elapsed_since_release:.1f}/{release_hold_duration}秒)")
                    else:
                        # 釋放保持期結束，重置釋放時間
                        release_time = None
                        self.logger.info("釋放保持期結束")
                
                # 如果不在釋放保持期內，根據檢測結果判斷
                if release_time is None:
                    if is_red_high:
                        # 紅色張力過高，釋放左鍵並記錄釋放時間
                        if is_holding_mouse:
                            self.input_controller.mouse_up('left')
                            is_holding_mouse = False
                            release_time = current_time
                            self.logger.info(f"拉力過高！釋放滑鼠左鍵並保持{release_hold_duration}秒")
                    else:
                        # 張力正常，按住左鍵
                        if not is_holding_mouse:
                            self.input_controller.mouse_down('left')
                            is_holding_mouse = True
                            self.logger.info("拉力正常，按住滑鼠左鍵")
                
                # 執行魚追蹤（如果啟用）
                if tracking_enabled:
                    fish_position = self._get_fish_position()
                    
                    # 如果檢測到魚，更新位置並重置計數器
                    if fish_position is not None:
                        last_fish_position = fish_position
                        no_detection_count = 0
                    else:
                        # 沒有檢測到魚，增加計數器
                        no_detection_count += 1
                        
                        # 如果連續失敗次數未超過閾值，使用上次的位置
                        if no_detection_count <= max_no_detection and last_fish_position is not None:
                            fish_position = last_fish_position
                            self.logger.debug(f"未檢測到魚 ({no_detection_count}/{max_no_detection})，保持原動作: {fish_position}")
                        else:
                            # 超過閾值，重置為中心
                            if no_detection_count == max_no_detection + 1:  # 只在剛超過時記錄一次
                                self.logger.warning(f"連續{max_no_detection}次未檢測到魚，重置按鍵")
                            fish_position = 'center'
                    
                    if fish_position == 'left':
                        # 魚在左邊，按住 A 鍵
                        if not is_holding_left:
                            if is_holding_right:
                                self.input_controller.key_up(right_key)
                                is_holding_right = False
                            self.input_controller.key_down(left_key)
                            is_holding_left = True
                            self.logger.debug(f"魚在左側，按住 {left_key} 鍵")
                    elif fish_position == 'right':
                        # 魚在右邊，按住 D 鍵
                        if not is_holding_right:
                            if is_holding_left:
                                self.input_controller.key_up(left_key)
                                is_holding_left = False
                            self.input_controller.key_down(right_key)
                            is_holding_right = True
                            self.logger.debug(f"魚在右側，按住 {right_key} 鍵")
                    else:  # fish_position == 'center'
                        # 魚在中心，釋放所有方向鍵
                        if is_holding_left:
                            self.input_controller.key_up(left_key)
                            is_holding_left = False
                            self.logger.debug(f"魚在中心，釋放 {left_key} 鍵")
                        if is_holding_right:
                            self.input_controller.key_up(right_key)
                            is_holding_right = False
                            self.logger.debug(f"魚在中心，釋放 {right_key} 鍵")
                
                time.sleep(check_interval)
        
        finally:
            # 確保釋放所有按鍵
            if is_holding_mouse:
                self.input_controller.mouse_up('left')
                self.logger.info("釋放滑鼠左鍵")
            if is_holding_left:
                self.input_controller.key_up(left_key)
                self.logger.info(f"釋放 {left_key} 鍵")
            if is_holding_right:
                self.input_controller.key_up(right_key)
                self.logger.info(f"釋放 {right_key} 鍵")
        
        self.logger.info("拉力計階段完成")
    
    def _get_red_ratio_in_tension_bar(self) -> float:
        """
        取得拉力計中紅色區域的比例
        
        Returns:
            紅色像素占拉力計區域的比例 (0.0 - 1.0)
        """
        # 取得檢測區域
        window_rect = self.window_manager.get_window_rect()
        if not window_rect:
            return 0.0
        
        x, y, w, h = window_rect
        
        # 取得拉力計區域配置
        tension_config = self.config.get('detection.tension_bar', {})
        region_config = tension_config.get('region', {'x': 0.25, 'y': 0.7, 'width': 0.4, 'height': 0.2})
        
        region = (
            int(x + w * region_config['x']),
            int(y + h * region_config['y']),
            int(w * region_config['width']),
            int(h * region_config['height'])
        )
        
        # 截取拉力計區域
        screen = self.image_detector.capture_screen(region)
        if screen is None:
            return 0.0
        
        # 檢測紅色比例
        red_ratio = self.image_detector.detect_red_ratio(screen)
        return red_ratio
    
    def _detect_red_tension_template(self) -> bool:
        """
        使用模板匹配檢測紅色張力狀態
        
        Returns:
            是否檢測到紅色張力模板
        """
        # 取得檢測區域
        window_rect = self.window_manager.get_window_rect()
        if not window_rect:
            return False
        
        x, y, w, h = window_rect
        
        # 取得紅色張力區域配置（獨立配置）
        red_tension_config = self.config.get('detection.red_tension', {})
        region_config = red_tension_config.get('region', {'x': 0.33, 'y': 0.8, 'width': 0.34, 'height': 0.06})
        
        region = (
            int(x + w * region_config['x']),
            int(y + h * region_config['y']),
            int(w * region_config['width']),
            int(h * region_config['height'])
        )
        
        # 取得紅色張力模板配置
        red_template_path = self.config.get('fishing.tension_phase.red_template', 'templates/red_tension.png')
        red_template_threshold = self.config.get('fishing.tension_phase.red_template_threshold', 0.8)
        
        try:
            # 截取檢測區域
            screen = self.image_detector.capture_screen(region)
            if screen is None:
                return False
            
            # 使用模板匹配
            position = self.image_detector.find_template(screen, red_template_path, red_template_threshold)
            return position is not None
            
        except Exception as e:
            self.logger.debug(f"紅色張力模板檢測失敗: {e}")
            return False
    
    def _get_fish_position(self) -> str:
        """
        取得魚的位置狀態
        
        Returns:
            'left' - 魚在左側，超過閾值
            'right' - 魚在右側，超過閾值
            'center' - 魚在中心區域
            None - 未檢測到魚
        """
        # 取得視窗資訊
        window_rect = self.window_manager.get_window_rect()
        if not window_rect:
            return None
        
        x, y, w, h = window_rect
        
        # 取得追蹤區域配置
        splash_config = self.config.get('detection.fish_splash', {})
        region_config = splash_config.get('region', {'x': 0.2, 'y': 0.3, 'width': 0.6, 'height': 0.3})
        
        # 計算檢測區域
        region = (
            int(x + w * region_config['x']),
            int(y + h * region_config['y']),
            int(w * region_config['width']),
            int(h * region_config['height'])
        )
        
        # 檢測白色水花位置
        white_threshold = splash_config.get('white_threshold', 200)
        min_area = splash_config.get('min_area', 50)
        splash_pos = self.image_detector.find_white_splash(region, white_threshold, min_area)
        
        if not splash_pos:
            return None
        
        # 計算水花相對於視窗中心的位置
        splash_x, splash_y = splash_pos
        window_center_x = x + w / 2 - 40  # 調整中心點偏移
        
        # 取得中心閾值（相對於視窗寬度）
        center_threshold = self.config.get('fishing.fish_tracking.center_threshold', 0.1)
        threshold_pixels = w * center_threshold
        
        # 判斷位置
        offset = splash_x - window_center_x
        
        if offset < -threshold_pixels:
            return 'left'
        elif offset > threshold_pixels:
            return 'right'
        else:
            return 'center'
    
    def _reset_and_continue(self):
        """
        重置狀態，點擊"再來一次"按鈕繼續釣魚
        """
        self.logger.debug("開始尋找'再來一次'按鈕")
        
        # 獲取配置
        retry_config = self.config.get('detection.retry_button', {})
        wait_time = retry_config.get('wait_time', 2)  # 等待按鈕出现的時間
        search_timeout = retry_config.get('search_timeout', 5)  # 搜索超時時間
        template_path = retry_config.get('template', 'templates/retry_button.png')
        
        # 等待按鈕出现
        time.sleep(wait_time)
        
        # 獲取視窗信息
        window_rect = self.window_manager.get_window_rect()
        if not window_rect:
            self.logger.warning("無法獲取視窗位置，跳过重置")
            return
        
        x, y, w, h = window_rect
        
        # 獲取搜索區域配置（如果没有配置，使用整個視窗）
        region_config = retry_config.get('region', {'x': 0.0, 'y': 0.0, 'width': 1.0, 'height': 1.0})
        
        region = (
            int(x + w * region_config['x']),
            int(y + h * region_config['y']),
            int(w * region_config['width']),
            int(h * region_config['height'])
        )
        
        # 嘗試查找按鈕
        start_time = time.time()
        found = False
        
        while time.time() - start_time < search_timeout:
            try:
                # 截取螢幕
                screen = self.image_detector.capture_screen(region)
                if screen is None:
                    time.sleep(0.5)
                    continue
                
                # 查找按鈕
                position = self.image_detector.find_template(screen, template_path)
                
                if position is not None:
                    # 計算實際點擊位置（相對於視窗）
                    click_x = region[0] + position[0]
                    click_y = region[1] + position[1]
                    
                    self.logger.info(f"找到'再來一次'按鈕，位置: ({click_x}, {click_y})")

                    time.sleep(0.5)

                    # 點擊按鈕
                    self.input_controller.click(click_x, click_y, button='left')
                    self.logger.info("已點擊'再來一次'按鈕")
                    found = True
                    break
                
            except Exception as e:
                self.logger.debug(f"搜尋按鈕失敗: {e}")
            
            time.sleep(0.5)
        
        if not found:
            self.logger.warning("未找到'再來一次'按鈕，可能需要手動操作")
            self.logger.info("提示: 請確保已截取按鈕圖片並儲存為 templates/retry_button.png")
            time.sleep(1)
        else:
            # 等待界面響應
            response_delay = retry_config.get('response_delay', 1)
            time.sleep(response_delay)
    
    def _check_and_replace_rod(self):
        """
        檢查魚竿耐久度是否耗盡，如果耗盡則點擊更換
        """
        self.logger.debug("檢查魚竿耐久度")
        
        # 取得配置
        rod_config = self.config.get('detection.rod_durability', {})
        wait_time = rod_config.get('wait_time', 0.2)  # 等待提示出現的時間
        search_timeout = rod_config.get('search_timeout', 0.9)  # 搜尋逾時時間
        template_path = rod_config.get('template', 'templates/rod_depleted.png')
        click_delay = rod_config.get('click_delay', 0.5)  # 兩次點擊之間的延遲
        response_delay = rod_config.get('response_delay', 1)  # 點擊後等待時間
        
        # 等待提示出現
        time.sleep(wait_time)
        
        # 取得視窗資訊
        window_rect = self.window_manager.get_window_rect()
        if not window_rect:
            self.logger.warning("無法取得視窗位置，跳過耐久度檢查")
            return
        
        x, y, w, h = window_rect
        
        # 取得搜尋區域配置（如果沒有配置，使用整個視窗）
        region_config = rod_config.get('region', {'x': 0.0, 'y': 0.0, 'width': 1.0, 'height': 1.0})
        
        region = (
            int(x + w * region_config['x']),
            int(y + h * region_config['y']),
            int(w * region_config['width']),
            int(h * region_config['height'])
        )
        
        # 嘗試查找耐久度耗盡提示
        start_time = time.time()
        found = False
        
        while time.time() - start_time < search_timeout:
            try:
                # 截取螢幕
                screen = self.image_detector.capture_screen(region)
                if screen is None:
                    time.sleep(0.3)
                    continue
                
                # 查找耐久度耗盡提示
                position = self.image_detector.find_template(screen, template_path, 0.87)
                
                if position is not None:
                    self.logger.info("檢測到魚竿耐久度耗盡！")
                    found = True
                    break
                
            except Exception as e:
                self.logger.debug(f"搜尋耐久度提示失敗: {e}")
            
            time.sleep(0.3)
        
        if found:
            # 取得第一次點擊位置配置
            first_click_pos = rod_config.get('first_click_pos', {'x': 0.5, 'y': 0.5})
            first_click_x = int(x + w * first_click_pos['x'])
            first_click_y = int(y + h * first_click_pos['y'])
            
            # 取得第二次點擊位置配置
            second_click_pos = rod_config.get('second_click_pos', {'x': 0.5, 'y': 0.6})
            second_click_x = int(x + w * second_click_pos['x'])
            second_click_y = int(y + h * second_click_pos['y'])
            
            self.logger.info(f"開始更換魚竿")
            
            try:
                # 按下 Alt 鍵
                self.logger.debug("按下 Alt 鍵")
                self.input_controller.key_down('alt')

                # 第一次點擊
                self.logger.info(f"第一次點擊位置: ({first_click_x}, {first_click_y})")
                self.input_controller.click(first_click_x, first_click_y, button='left')
                self.logger.debug("第一次點擊完成")
                
                time.sleep(click_delay)
                
                # 第二次點擊（保持按住 Alt）
                self.logger.info(f"第二次點擊位置: ({second_click_x}, {second_click_y})")
                self.input_controller.click(second_click_x, second_click_y, button='left')
                self.logger.info("第二次點擊完成")
                
            finally:
                # 確保釋放 Alt 鍵
                self.input_controller.key_up('alt')
                self.logger.debug("釋放 Alt 鍵")
                self.logger.info("魚竿已更換")
            
            # 等待界面響應
            time.sleep(response_delay)
        else:
            self.logger.debug("魚竿耐久度正常")
    
    def get_statistics(self) -> dict:
        """
        取得統計資訊
        
        Returns:
            統計資料字典
        """
        return {
            'fishing_count': self.fishing_count,
            'current_state': self.state.value
        }
