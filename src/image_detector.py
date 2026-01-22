"""
圖像檢測模組
"""

import logging
from pathlib import Path

import cv2
import numpy as np
import pyautogui
import pytesseract


class ImageDetector:
    """圖像檢測器"""

    def __init__(self, threshold: float = 0.8):
        """
        初始化圖像檢測器

        Args:
            threshold: 匹配閾值
        """
        self.threshold = threshold
        self.logger = logging.getLogger("FishingBot.ImageDetector")

    def capture_screen(
        self, region: tuple[int, int, int, int] | None = None
    ) -> np.ndarray | None:
        """
        截取螢幕

        Args:
            region: 截取區域 (x, y, width, height)

        Returns:
            截圖的 numpy 陣列，失敗時返回 None
        """
        try:
            screenshot = pyautogui.screenshot(region=region)
            return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        except Exception as e:
            self.logger.error(f"截屏失敗: {e}")
            return None

    def find_template(
        self,
        screen: np.ndarray | None,
        template_path: str,
        threshold: float | None = None,
    ) -> tuple[int, int] | None:
        """
        在螢幕截圖中查找模板圖像

        Args:
            screen: 螢幕截圖
            template_path: 模板圖像路徑
            threshold: 匹配閾值（可選，預設使用初始化時的閾值）

        Returns:
            匹配位置的中心座標 (x, y)，未找到返回 None
        """
        if screen is None:
            return None

        # 使用傳入的閾值，如果沒有則使用預設閾值
        match_threshold = (
            threshold if threshold is not None else self.threshold
        )

        template_file = Path(template_path)
        if not template_file.exists():
            self.logger.warning(f"模板檔案不存在: {template_path}")
            return None

        try:
            template = cv2.imread(str(template_file))
            if template is None:
                self.logger.error(f"無法加載模板圖像: {template_path}")
                return None

            # 檢查尺寸：搜索區域必須 >= 模板圖片
            screen_h, screen_w = screen.shape[:2]
            template_h, template_w = template.shape[:2]

            if screen_h < template_h or screen_w < template_w:
                self.logger.warning(
                    f"搜索區域 ({screen_w}x{screen_h}) 小於模板 ({template_w}x{template_h})，"
                    f"請調整遊戲窗口大小或使用更小的模板圖片"
                )
                return None

            result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            if max_val >= match_threshold:
                # 返回匹配區域的中心點
                h, w = template.shape[:2]
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                self.logger.debug(
                    f"找到模板，匹配度: {max_val:.2f}，位置: ({center_x}, {center_y})"
                )
                return (center_x, center_y)
            else:
                self.logger.debug(f"未找到模板，最高匹配度: {max_val:.2f}")
                return None

        except Exception as e:
            self.logger.error(f"模板匹配失敗: {e}")
            return None

    def detect_red_ratio(
        self,
        screen: np.ndarray,
    ) -> int:
        """
        檢測圖像中特定顏色範圍的像素，判定張力狀態

        顏色範圍定義（BGR 格式）：
        - 張力較高 (50): RGB 246,113,13 ~ 229,13,13 (BGR: 13,113,246 ~ 13,13,229)
        - 張力過高 (100): RGB 229,13,13 ~ 255,255,255 (BGR: 13,13,229 ~ 255,255,255)

        Args:
            screen: 輸入圖像（BGR格式）

        Returns:
            張力值：
            - 0: 無張力
            - 50: 張力較高（需要間歇點擊）
            - 100: 張力過高（需要釋放）
        """
        if screen is None:
            return 0

        try:
            total_pixels = screen.shape[0] * screen.shape[1]

            # 定義張力過高的顏色範圍 (BGR: 13,13,229 ~ 255,255,255)
            # RGB 229,13,13 ~ 255,255,255
            lower_critical = np.array([13, 13, 229], dtype=np.uint8)
            upper_critical = np.array([255, 255, 255], dtype=np.uint8)
            mask_critical = cv2.inRange(screen, lower_critical, upper_critical)
            critical_pixels = cv2.countNonZero(mask_critical)
            critical_ratio = (
                critical_pixels / total_pixels if total_pixels > 0 else 0.0
            )

            if critical_ratio > 0.95:
                self.logger.debug(
                    f"檢測到張力過高，像素比例: {critical_ratio:.3f}"
                )
                return 100
            if critical_ratio > 0.6:
                self.logger.debug(
                    f"檢測到張力較高，像素比例: {critical_ratio:.3f}"
                )
                return 50

            return 0
        except Exception as e:
            self.logger.error(f"張力顏色檢測失敗: {e}")
            return 0

    def detect_color_change(
        self,
        region: tuple[int, int, int, int],
        target_color: tuple[int, int, int],
        tolerance: int = 30,
    ) -> bool:
        """
        檢測指定區域的顏色變化

        Args:
            region: 檢測區域 (x, y, width, height)
            target_color: 目標顏色 (B, G, R)
            tolerance: 顏色容差

        Returns:
            是否檢測到目標顏色
        """
        screen = self.capture_screen(region)
        if screen is None:
            return False

        try:
            # 計算平均顏色
            avg_color = cv2.mean(screen)[:3]

            # 檢查顏色是否在容差範圍内
            color_diff = sum(
                abs(avg_color[i] - target_color[i]) for i in range(3)
            )

            if color_diff <= tolerance * 3:
                self.logger.debug(f"檢測到顏色變化，平均顏色: {avg_color}")
                return True
            return False

        except Exception as e:
            self.logger.error(f"顏色檢測失敗: {e}")
            return False

    def detect_color_in_range(
        self,
        region: tuple[int, int, int, int],
        color_min: tuple[int, int, int],
        color_max: tuple[int, int, int],
        min_pixel_ratio: float = 0.01,
    ) -> bool:
        """
        檢測指定區域是否存在特定顏色範圍的像素

        Args:
            region: 檢測區域 (x, y, width, height)
            color_min: 最小顏色值 (B, G, R)
            color_max: 最大顏色值 (B, G, R)
            min_pixel_ratio: 最小像素比例（0.0-1.0），超過此比例才判定為存在該顏色

        Returns:
            是否檢測到目標顏色範圍
        """
        screen = self.capture_screen(region)
        if screen is None:
            return False

        try:
            # 創建顏色範圍遮罩
            lower = np.array(color_min, dtype=np.uint8)
            upper = np.array(color_max, dtype=np.uint8)

            # 使用 inRange 檢測顏色範圍
            mask = cv2.inRange(screen, lower, upper)

            # 計算符合顏色範圍的像素數量
            matched_pixels = cv2.countNonZero(mask)
            total_pixels = screen.shape[0] * screen.shape[1]

            ratio = matched_pixels / total_pixels if total_pixels > 0 else 0.0

            if ratio >= min_pixel_ratio:
                self.logger.debug(f"檢測到目標顏色範圍，像素比例: {ratio:.3f}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"顏色範圍檢測失敗: {e}")
            return False

    def save_screenshot(
        self, filename: str, region: tuple[int, int, int, int] | None = None
    ):
        """
        保存截圖（用於測試）

        Args:
            filename: 保存的檔案名稱
            region: 截取區域
        """
        screen = self.capture_screen(region)
        if screen is not None:
            cv2.imwrite(filename, screen)
            self.logger.info(f"截圖已保存: {filename}")

    def find_white_splash(
        self,
        region: tuple[int, int, int, int],
        white_threshold: int = 200,
        min_area: int = 50,
    ) -> tuple[int, int] | None:
        """
        檢測白色水花的位置

        Args:
            region: 檢測區域 (x, y, width, height)
            white_threshold: 白色閾值 (0-255)
            min_area: 最小面積（過濾噪点）

        Returns:
            白色水花的中心位置 (x, y)，相對於整個螢幕，未找到返回 None
        """
        screen = self.capture_screen(region)
        if screen is None:
            return None

        try:
            # 轉換為灰度圖
            gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)

            # 二值化：提取白色區域
            _, binary = cv2.threshold(
                gray, white_threshold, 255, cv2.THRESH_BINARY
            )

            # 查找輪廓
            contours, _ = cv2.findContours(
                binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            if not contours:
                return None

            # 找到面積最大的輪廓（假設為水花）
            valid_contours = [
                c for c in contours if cv2.contourArea(c) >= min_area
            ]
            if not valid_contours:
                return None

            largest_contour = max(
                valid_contours, key=lambda c: cv2.contourArea(c)
            )

            # 計算輪廓的中心點
            M = cv2.moments(largest_contour)
            if M["m00"] == 0:
                return None

            # 相對於檢測區域的座標
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])

            # 轉換為絕對螢幕座標
            abs_x = region[0] + cx
            abs_y = region[1] + cy

            self.logger.debug(
                f"檢測到白色水花: ({abs_x}, {abs_y}), 面積: {cv2.contourArea(largest_contour):.0f}"
            )
            return (abs_x, abs_y)

        except Exception as e:
            self.logger.error(f"白色水花檢測失敗: {e}")
            return None

    def _detect_tension_by_ocr(
        self, region: tuple[int, int, int, int]
    ) -> int | None:
        """
        使用 OCR 識別張力表上的數字（0-100）

        Returns:
            張力數字，識別失敗返回 None
        """

        try:
            screen = self.capture_screen(region)
            if screen is None:
                return None

            # 轉換為灰度圖
            gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)

            # 二值化處理，增強數字對比度
            _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

            # 使用 pytesseract 識別數字
            # 配置為只識別數字
            custom_config = (
                r"--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789"
            )
            text = pytesseract.image_to_string(binary, config=custom_config)

            # 提取數字
            text = text.strip()
            if text.isdigit():
                value = int(text)
                if 0 <= value <= 100:
                    return value

            return None
        except Exception as e:
            self.logger.debug(f"OCR 識別失敗: {e}")
            return None
