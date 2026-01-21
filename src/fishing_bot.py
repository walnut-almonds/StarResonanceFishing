"""
釣魚機器人主邏輯
"""

import logging
import random
import time
from enum import Enum

from src.config_manager import ConfigManager
from src.image_detector import ImageDetector
from src.input_controller_winapi import WinAPIInputController
from src.phases import (
    CastingPhase,
    CompletionPhase,
    PreparationPhase,
    TensionPhase,
    WaitingPhase,
)
from src.window_manager import WindowManager


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

        # 讀取滑鼠移動時間配置
        self.mouse_move_duration = config.get(
            "anti_detection.mouse_move_duration", 0.0
        )

        # 初始化各個模組
        self.window_manager = WindowManager(config.get("game.window_title"))
        self.input_controller = WinAPIInputController(
            config.get("anti_detection.random_delay_min", 0.1),
            config.get("anti_detection.random_delay_max", 0.5),
        )
        self.image_detector = ImageDetector(
            config.get("detection.threshold", 0.8)
        )

        # 初始化各階段處理器
        self.casting_phase = CastingPhase(
            config, self.window_manager, self.input_controller
        )
        self.waiting_phase = WaitingPhase(
            config, self.window_manager, self.image_detector
        )
        self.tension_phase = TensionPhase(
            config,
            self.window_manager,
            self.input_controller,
            self.image_detector,
        )
        self.completion_phase = CompletionPhase(
            config,
            self.window_manager,
            self.input_controller,
            self.image_detector,
        )
        self.preparation_phase = PreparationPhase(
            config,
            self.window_manager,
            self.input_controller,
            self.image_detector,
        )

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
                    self.config.get("anti_detection.rest_time_min", 1),
                    self.config.get("anti_detection.rest_time_max", 3),
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
        self.preparation_phase.check_and_replace_rod()

        # 1. 拋竿
        self.state = FishingState.CASTING
        self.casting_phase.execute()

        # 2. 等待咬鉤
        self.state = FishingState.WAITING
        count = 0
        while count < 2:
            if self.waiting_phase.wait_for_bite():
                self.logger.info("上鉤了！")

                # 3. 收竿
                self.state = FishingState.REELING
                self.waiting_phase.reel_in(self.input_controller)

                # 檢測是否出現拉力計
                if self.tension_phase.detect_tension_bar():
                    self.logger.info("檢測到拉力計，進入魚追蹤階段")
                    self.tension_phase.handle_tension_phase()
                else:
                    self.logger.debug("未檢測到拉力計，直接完成收竿")

                # 統計釣魚次數
                self.fishing_count += 1
                self.logger.info(f"成功釣魚 #{self.fishing_count}")
                break
            else:
                self.logger.warning("等待咬鉤逾時，重新開始")
                count += 1

        # 4. 重置狀態 - 點擊"再來一次"按鈕
        self.state = FishingState.IDLE
        self.completion_phase.reset_and_continue()

    def get_statistics(self) -> dict:
        """
        取得統計資訊

        Returns:
            統計資料字典
        """
        return {
            "fishing_count": self.fishing_count,
            "current_state": self.state.value,
        }
