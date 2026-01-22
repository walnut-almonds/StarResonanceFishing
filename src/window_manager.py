"""
視窗管理模組
"""

import logging

import pygetwindow as gw


class WindowManager:
    """遊戲視窗管理器"""

    def __init__(self, window_title: str):
        """
        初始化視窗管理器

        Args:
            window_title: 視窗標題
        """
        self.window_title = window_title
        self.window = None
        self.logger = logging.getLogger("FishingBot.WindowManager")

    def find_window(self) -> bool:
        """
        查找遊戲視窗

        Returns:
            是否找到視窗
        """
        try:
            windows = gw.getWindowsWithTitle(self.window_title)
            if windows:
                self.window = windows[0]
                self.logger.info(f"找到視窗: {self.window.title}")
                return True
            else:
                self.logger.warning(
                    f"未找到標題包含 '{self.window_title}' 的視窗"
                )
                return False
        except Exception as e:
            self.logger.error(f"查找視窗時出錯: {e}")
            return False

    def activate_window(self) -> bool:
        """
        激活遊戲視窗

        Returns:
            是否成功激活
        """
        if not self.window:
            self.logger.warning("視窗未初始化")
            return False

        try:
            if self.window.isMinimized:
                self.window.restore()
            self.window.activate()
            self.logger.debug("視窗已激活")
            return True
        except Exception as e:
            self.logger.error(f"激活視窗時出錯: {e}")
            return False

    def get_window_rect(self) -> tuple[int, int, int, int] | None:
        """
        獲取視窗位置和大小

        Returns:
            (x, y, width, height) 或 None
        """
        if not self.window:
            return None

        try:
            return (
                self.window.left,
                self.window.top,
                self.window.width,
                self.window.height,
            )
        except Exception as e:
            self.logger.error(f"獲取視窗位置時出錯: {e}")
            return None

    def is_window_active(self) -> bool:
        """
        檢查視窗是否處於活動狀態

        Returns:
            是否活動
        """
        if not self.window:
            return False

        try:
            return self.window.isActive
        except Exception:
            return False
